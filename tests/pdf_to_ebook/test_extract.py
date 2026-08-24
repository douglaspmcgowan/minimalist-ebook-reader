import tempfile
import unittest
import hashlib
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, StreamObject, TextStringObject
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from tools.pdf_to_ebook.extract import _widget_options, _widget_value, extract_pdf
from tools.pdf_to_ebook.semantics import classify_records
from tools.pdf_to_ebook.validate import validate_release


class ExtractionTests(unittest.TestCase):
    def _image(self, directory: Path) -> Path:
        source = directory / "figure.png"
        Image.new("RGB", (40, 30), color=(20, 80, 140)).save(source)
        return source

    def _canvas(self, directory: Path, name: str = "fixture.pdf") -> tuple[Path, canvas.Canvas]:
        source = directory / name
        return source, canvas.Canvas(str(source), pagesize=(612, 792))

    def _linked_pdf(self, directory: Path, name: str, rotation: int, cropped: bool = False) -> Path:
        original, pdf = self._canvas(directory, f"raw-{name}")
        pdf.drawString(72, 700, "Rotated link")
        pdf.linkAbsolute("go", "target", Rect=(70, 696, 150, 712), thickness=0)
        pdf.showPage()
        pdf.bookmarkPage("target")
        pdf.drawString(72, 700, "Destination")
        pdf.save()
        reader = PdfReader(original)
        writer = PdfWriter()
        for page_number, page in enumerate(reader.pages):
            if page_number == 0:
                page.rotate(rotation)
                if cropped:
                    page.cropbox.lower_left = (50, 50)
                    page.cropbox.upper_right = (562, 742)
            writer.add_page(page)
        source = directory / name
        with source.open("wb") as handle:
            writer.write(handle)
        return source

    def _nested_widget_pdf(self, directory: Path) -> Path:
        source, pdf = self._canvas(directory)
        pdf.drawString(72, 700, "Nested widget")
        pdf.acroForm.textfield(name="original", x=72, y=640, width=180, height=24, borderWidth=1)
        pdf.showPage()
        pdf.save()
        reader = PdfReader(source)
        writer = PdfWriter()
        writer.clone_document_from_reader(reader)
        widget = writer.pages[0]["/Annots"][0].get_object()
        parent = DictionaryObject({
            NameObject("/FT"): NameObject("/Tx"),
            NameObject("/T"): TextStringObject("parent-name"),
            NameObject("/TU"): TextStringObject("Accessible account number"),
            NameObject("/V"): TextStringObject("parent-value"),
            NameObject("/Ff"): NumberObject(2),
        })
        widget[NameObject("/Parent")] = writer._add_object(parent)
        widget[NameObject("/T")] = TextStringObject("child-name")
        widget[NameObject("/V")] = TextStringObject("child-value")
        del widget[NameObject("/FT")]
        del widget[NameObject("/Ff")]
        with source.open("wb") as handle:
            writer.write(handle)
        return source

    def _radio_group_pdf(self, directory: Path) -> Path:
        source, pdf = self._canvas(directory, "radio-group.pdf")
        pdf.drawString(72, 700, "Choose a plan")
        pdf.acroForm.radio(name="plan", value="monthly", selected=True, x=72, y=650)
        pdf.acroForm.radio(name="plan", value="annual", selected=False, x=72, y=620)
        pdf.save()
        reader = PdfReader(source)
        writer = PdfWriter()
        writer.clone_document_from_reader(reader)
        for reference in writer.pages[0]["/Annots"]:
            widget = reference.get_object()
            widget["/Parent"].get_object()[NameObject("/TU")] = TextStringObject("Billing plan")
        with source.open("wb") as handle:
            writer.write(handle)
        return source

    def test_bounded_extraction_skips_full_document_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp, "three-pages.pdf")
            writer = PdfWriter()
            for _ in range(3):
                writer.add_blank_page(width=612, height=792)
            with source.open("wb") as handle:
                writer.write(handle)

            preflight, records = extract_pdf(source, page_numbers=[2], include_preflight=False)

            self.assertEqual([2], preflight["requested_pages"])
            self.assertEqual([], records)

    def test_records_carry_the_page_geometry_used_by_their_bounding_boxes(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "mixed-page-sizes.pdf"
            pdf = canvas.Canvas(str(source), pagesize=(300, 400))
            pdf.drawString(36, 36, "Small page")
            pdf.showPage()
            pdf.setPageSize((600, 800))
            pdf.drawString(72, 72, "Large page")
            pdf.save()

            _, records = extract_pdf(source)

            by_text = {record.text: record for record in records}
            self.assertEqual(by_text["Small page"].metadata["page_width"], 300.0)
            self.assertEqual(by_text["Small page"].metadata["page_height"], 400.0)
            self.assertEqual(by_text["Large page"].metadata["page_width"], 600.0)
            self.assertEqual(by_text["Large page"].metadata["page_height"], 800.0)

    def test_records_carry_asymmetric_crop_bounds_in_bbox_coordinates(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory, "uncropped.pdf")
            pdf.drawString(72, 400, "Cropped page")
            pdf.save()
            reader = PdfReader(source)
            page = reader.pages[0]
            page.cropbox.lower_left = (50, 50)
            page.cropbox.upper_right = (550, 650)
            cropped = directory / "cropped.pdf"
            writer = PdfWriter()
            writer.add_page(page)
            with cropped.open("wb") as handle:
                writer.write(handle)

            _, records = extract_pdf(cropped)

            self.assertEqual(records[0].metadata["page_bbox"], [50.0, 142.0, 550.0, 742.0])

    def test_orders_text_table_and_materialized_figure_by_page_geometry(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory)
            pdf.drawString(72, 700, "Before table")
            table = Table([["Left", "Right"], ["A", "B"]], colWidths=[80, 80], rowHeights=[20, 20])
            table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)]))
            table.wrapOn(pdf, 612, 792)
            table.drawOn(pdf, 72, 520)
            pdf.drawImage(str(self._image(directory)), 72, 430, width=40, height=30)
            pdf.drawString(72, 300, "After figure")
            pdf.save()

            assets = directory / "assets"
            _, records = extract_pdf(source, asset_output_dir=assets)

            sequence = [(record.role_hint, record.text) for record in records]
            self.assertEqual(
                [(None, "Before table"), ("table", ""), ("figure", ""), (None, "After figure")],
                sequence,
            )
            extracted_table = next(record for record in records if record.role_hint == "table")
            self.assertEqual(extracted_table.metadata["table_header_source"], "inferred-first-row")
            figure = next(record for record in records if record.role_hint == "figure")
            self.assertEqual(figure.asset, "assets/page-0001-figure-01.png")
            materialized = assets / figure.asset
            self.assertTrue(materialized.is_file())
            self.assertEqual(hashlib.sha256(materialized.read_bytes()).hexdigest(), figure.metadata["asset_sha256"])

    def test_extracts_internal_link_destination_from_real_pdf_annotation(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory)
            pdf.drawString(72, 700, "Chapter two")
            pdf.linkAbsolute("go", "chapter-two", Rect=(70, 696, 150, 712), thickness=0)
            pdf.showPage()
            pdf.bookmarkPage("chapter-two")
            pdf.drawString(72, 700, "Destination")
            pdf.save()

            _, records = extract_pdf(source)

            linked = next(record for record in records if record.text == "Chapter two")
            self.assertEqual(linked.links[0]["target_page"], 2)
            self.assertEqual(linked.links[0]["text"], "Chapter two")
            self.assertEqual(len(linked.links[0]["bbox"]), 4)

    def test_multiline_annotation_keeps_one_normalized_source_relationship(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory, "wrapped-link.pdf")
            pdf.drawString(72, 700, "wrapped")
            pdf.drawString(72, 680, "appendix")
            pdf.linkAbsolute("go", "appendix", Rect=(70, 676, 150, 712), thickness=0)
            pdf.showPage()
            pdf.bookmarkPage("appendix")
            pdf.drawString(72, 700, "Destination")
            pdf.save()
            reader = PdfReader(source)
            writer = PdfWriter()
            writer.clone_document_from_reader(reader)
            annotations = writer.pages[0]["/Annots"]
            annotations.append(annotations[0])
            with source.open("wb") as handle:
                writer.write(handle)

            _, records = extract_pdf(source)

            linked = [record for record in records if record.links]
            self.assertEqual([record.text for record in linked], ["wrapped", "appendix"])
            self.assertEqual(linked[0].links, linked[1].links)
            self.assertEqual(len(linked[0].links), 1)
            self.assertEqual(linked[0].links[0]["text"], "wrapped appendix")
            self.assertEqual(linked[0].links[0]["target_page"], 2)

    def test_extracts_real_widget_field_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory)
            pdf.drawString(72, 700, "Email")
            pdf.acroForm.textfield(name="email", x=72, y=640, width=180, height=24, borderWidth=1)
            pdf.save()

            _, records = extract_pdf(source)

            widget = next(record for record in records if record.role_hint == "form")
            self.assertEqual(widget.form["fields"], [{"name": "email", "label": "email", "type": "text", "value": "", "required": False}])
            self.assertEqual(widget.metadata["widget_name"], "email")
            self.assertEqual(widget.metadata["review"][0]["code"], "widget-label-name-fallback")

    def test_unmaterialized_figure_has_blocking_review_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory)
            pdf.drawImage(str(self._image(directory)), 72, 430, width=40, height=30)
            pdf.save()

            _, records = extract_pdf(source)

            figure = next(record for record in records if record.role_hint == "figure")
            self.assertIsNone(figure.asset)
            self.assertEqual(["figure-asset-unmaterialized"], [item["code"] for item in figure.metadata["review"]])

    def test_marks_two_column_layout_as_ambiguous_for_review(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory)
            for x, prefix in ((72, "Left"), (330, "Right")):
                pdf.drawString(x, 700, f"{prefix} one")
                pdf.drawString(x, 675, f"{prefix} two")
            pdf.save()

            _, records = extract_pdf(source)

            self.assertTrue(records)
            self.assertTrue(all(record.metadata.get("reading_order_ambiguous") for record in records))
            self.assertEqual(["uncertain-reading-order"], [item["code"] for item in records[0].metadata["review"]])

    def test_preserves_figure_and_reading_order_review_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory)
            pdf.drawImage(str(self._image(directory)), 72, 430, width=40, height=30)
            for x, prefix in ((72, "Left"), (330, "Right")):
                pdf.drawString(x, 700, f"{prefix} one")
                pdf.drawString(x, 675, f"{prefix} two")
            pdf.save()

            _, records = extract_pdf(source)

            figure = next(record for record in records if record.role_hint == "figure")
            self.assertEqual(
                ["figure-asset-unmaterialized", "uncertain-reading-order"],
                [item["code"] for item in figure.metadata["review"]],
            )
            self.assertTrue(all(item["severity"] == "high" for item in figure.metadata["review"]))

    def test_extracts_links_after_rotation_and_cropbox_transform(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for rotation in (0, 90, 180, 270):
                source = self._linked_pdf(directory, f"rotation-{rotation}.pdf", rotation, cropped=True)

                _, records = extract_pdf(source)

                linked = [record for record in records if record.links]
                self.assertEqual([record.text for record in linked], ["Rotated link"], f"rotation {rotation}")
                self.assertEqual(linked[0].links[0]["target_page"], 2)
                self.assertEqual(linked[0].links[0]["text"], "Rotated link")
                self.assertEqual(len(linked[0].links[0]["bbox"]), 4)
                blocks = classify_records(record for record in records if record.page == 1)
                self.assertNotIn("contents", [block.kind for block in blocks], f"rotation {rotation}")

    def test_inherits_widget_attributes_with_child_precedence(self):
        with tempfile.TemporaryDirectory() as temp:
            _, records = extract_pdf(self._nested_widget_pdf(Path(temp)))

            widget = next(record for record in records if record.role_hint == "form")
            self.assertEqual(
                [{"name": "child-name", "label": "Accessible account number", "type": "text", "value": "child-value", "required": True}],
                widget.form["fields"],
            )
            self.assertNotIn("review", widget.metadata)

    def test_groups_related_widgets_and_validates_inherited_accessible_label_end_to_end(self):
        with tempfile.TemporaryDirectory() as temp:
            _, records = extract_pdf(self._radio_group_pdf(Path(temp)))

            forms = [record for record in records if record.role_hint == "form"]
            self.assertEqual(len(forms), 1)
            self.assertEqual(forms[0].form["title"], "Billing plan")
            self.assertEqual(forms[0].form["fields"][0]["label"], "Billing plan")
            self.assertEqual(forms[0].form["fields"][0]["options"], ["monthly", "annual"])
            self.assertEqual(forms[0].form["fields"][0]["value"], "monthly")
            self.assertEqual(forms[0].metadata["widget_count"], 2)
            report = validate_release(classify_records(records), page_count=1, extraction_records=records)
            self.assertTrue(report.releasable, [item.to_dict() for item in report.items])

    def test_widget_name_fallback_can_be_approved_by_stable_finding_id(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory, "fallback-widget.pdf")
            pdf.drawString(72, 700, "Email")
            pdf.acroForm.textfield(name="email", x=72, y=640, width=180, height=24, borderWidth=1)
            pdf.save()

            _, records = extract_pdf(source)
            blocks = classify_records(records)
            first = validate_release(blocks, page_count=1, extraction_records=records)
            finding = next(item for item in first.items if item.code == "widget-label-name-fallback")
            approval = type(finding)(
                finding.code,
                finding.severity,
                finding.page,
                "Reviewed field-name fallback.",
                approved=True,
                details={"finding_id": finding.details["finding_id"]},
            )

            approved = validate_release(blocks, page_count=1, extraction_records=records, review_items=[approval])

            self.assertTrue(approved.releasable, [item.to_dict() for item in approved.items])

    def test_rotated_multiline_text_and_positioned_words_form_logical_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            raw, pdf = self._canvas(directory, "raw-multiline.pdf")
            pdf.drawString(72, 700, "Alpha")
            pdf.drawString(150, 700, "Beta")
            pdf.drawString(72, 675, "Gamma")
            pdf.drawString(150, 675, "Delta")
            pdf.save()
            for rotation in (90, 270):
                reader = PdfReader(raw)
                writer = PdfWriter()
                writer.add_page(reader.pages[0])
                writer.pages[0].rotate(rotation)
                source = directory / f"multiline-{rotation}.pdf"
                with source.open("wb") as handle:
                    writer.write(handle)

                _, records = extract_pdf(source)

                self.assertEqual([record.text for record in records], ["Alpha Beta", "Gamma Delta"], f"rotation {rotation}")

    def test_rotated_two_column_rows_preserve_spans_and_enter_ambiguity_review(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            raw, pdf = self._canvas(directory, "raw-columns.pdf")
            for y, suffix in ((700, "one"), (675, "two")):
                pdf.drawString(72, y, f"Left {suffix}")
                pdf.drawString(330, y, f"Right {suffix}")
            pdf.save()
            for rotation in (90, 270):
                reader = PdfReader(raw)
                writer = PdfWriter()
                writer.add_page(reader.pages[0])
                writer.pages[0].rotate(rotation)
                source = directory / f"columns-{rotation}.pdf"
                with source.open("wb") as handle:
                    writer.write(handle)

                _, records = extract_pdf(source)

                self.assertEqual({record.text for record in records}, {"Left one", "Left two", "Right one", "Right two"})
                self.assertTrue(all(record.metadata.get("reading_order_ambiguous") for record in records))

    def test_rotated_columns_are_geometric_when_content_stream_paints_right_first(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            raw, pdf = self._canvas(directory, "raw-reversed-columns.pdf")
            for y, suffix in ((700, "one"), (675, "two")):
                pdf.drawString(330, y, f"Right {suffix}")
                pdf.drawString(72, y, f"Left {suffix}")
            pdf.save()
            reader = PdfReader(raw)
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            writer.pages[0].rotate(90)
            source = directory / "reversed-columns.pdf"
            with source.open("wb") as handle:
                writer.write(handle)

            _, records = extract_pdf(source)

            self.assertEqual({record.text for record in records}, {"Left one", "Left two", "Right one", "Right two"})
            self.assertTrue(all(record.metadata.get("reading_order_ambiguous") for record in records))

    def test_rotated_moderate_column_gap_uses_the_column_axis_extent(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            raw, pdf = self._canvas(directory, "raw-moderate-columns.pdf")
            for y, suffix in ((700, "1"), (675, "2")):
                pdf.drawString(72, y, f"L{suffix}")
                pdf.drawString(185, y, f"R{suffix}")
            pdf.save()
            reader = PdfReader(raw)
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            writer.pages[0].rotate(90)
            source = directory / "moderate-columns.pdf"
            with source.open("wb") as handle:
                writer.write(handle)

            _, records = extract_pdf(source)

            self.assertTrue(all(record.metadata.get("reading_order_ambiguous") for record in records))

    def test_rotated_anchor_text_inserts_space_between_positioned_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            raw, pdf = self._canvas(directory, "raw-anchor-words.pdf")
            pdf.drawString(150, 700, "Beta")
            pdf.drawString(72, 700, "Alpha")
            pdf.linkAbsolute("words", "target", Rect=(70, 696, 190, 712), thickness=0)
            pdf.showPage()
            pdf.bookmarkPage("target")
            pdf.drawString(72, 700, "Target")
            pdf.save()
            reader = PdfReader(raw)
            writer = PdfWriter()
            writer.clone_document_from_reader(reader)
            writer.pages[0].rotate(90)
            source = directory / "anchor-words.pdf"
            with source.open("wb") as handle:
                writer.write(handle)

            _, records = extract_pdf(source)

            linked = next(record for record in records if record.links)
            self.assertEqual(linked.links[0]["text"], "Alpha Beta")

    def test_choice_options_use_display_labels_in_source_order(self):
        annotation = DictionaryObject({
            NameObject("/Opt"): ArrayObject([
                ArrayObject([TextStringObject("b"), TextStringObject("Beta")]),
                ArrayObject([TextStringObject("a"), TextStringObject("Alpha")]),
            ]),
        })

        self.assertEqual(_widget_options(annotation, "choice", 0), ["Beta", "Alpha"])

    def test_widget_values_match_display_options_and_preserve_multiselect(self):
        single = DictionaryObject({
            NameObject("/Opt"): ArrayObject([ArrayObject([TextStringObject("b"), TextStringObject("Beta")])]),
            NameObject("/V"): TextStringObject("b"),
        })
        multiple = DictionaryObject({
            NameObject("/Opt"): ArrayObject([
                ArrayObject([TextStringObject("b"), TextStringObject("Beta")]),
                ArrayObject([TextStringObject("a"), TextStringObject("Alpha")]),
            ]),
            NameObject("/V"): ArrayObject([TextStringObject("b"), TextStringObject("a")]),
        })

        self.assertEqual(_widget_value(single), "Beta")
        self.assertEqual(_widget_value(multiple), ["Beta", "Alpha"])

    def test_widget_selected_display_value_uses_option_label_normalization(self):
        annotation = DictionaryObject({
            NameObject("/Opt"): ArrayObject([ArrayObject([TextStringObject("b"), TextStringObject(" Beta ")])]),
            NameObject("/V"): TextStringObject(" b "),
        })

        self.assertEqual(_widget_options(annotation, "choice", 0), ["Beta"])
        self.assertEqual(_widget_value(annotation), "Beta")

    def test_pushbutton_appearance_stream_is_not_treated_as_options(self):
        normal = StreamObject()
        normal[NameObject("/Subtype")] = NameObject("/Form")
        normal[NameObject("/BBox")] = ArrayObject([NumberObject(0), NumberObject(0), NumberObject(20), NumberObject(20)])
        annotation = DictionaryObject({NameObject("/AP"): DictionaryObject({NameObject("/N"): normal})})

        self.assertEqual(_widget_options(annotation, "button", 1 << 16), [])

    def test_vector_inventory_does_not_make_enclosed_text_order_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory, "labelled-vector.pdf")
            pdf.rect(60, 670, 160, 50, stroke=1, fill=0)
            pdf.drawString(72, 700, "Labelled box")
            pdf.save()

            _, records = extract_pdf(source)

            text = next(record for record in records if record.text == "Labelled box")
            self.assertFalse(text.metadata.get("reading_order_ambiguous"))

    def test_enumerates_real_pdf_vector_region_for_mandatory_disposition(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory, "vector.pdf")
            pdf.rect(200, 400, 80, 60, stroke=1, fill=0)
            pdf.save()

            preflight, records = extract_pdf(source)

            vectors = [record for record in records if record.role_hint == "non_text_object"]
            self.assertEqual(len(vectors), 1)
            self.assertEqual(vectors[0].metadata["object_kind"], "vector")
            self.assertEqual(vectors[0].metadata["object_id"], "page-0001-vector-001")
            self.assertEqual(preflight["pages"][0]["vector_regions"], 1)

    def test_nested_unconnected_vector_regions_keep_distinct_inventory_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory, "nested-vectors.pdf")
            pdf.rect(10, 10, 592, 772, stroke=1, fill=0)
            pdf.rect(250, 300, 100, 100, stroke=1, fill=0)
            pdf.save()

            preflight, records = extract_pdf(source)

            vectors = [record for record in records if record.role_hint == "non_text_object"]
            self.assertEqual([record.metadata["object_id"] for record in vectors], ["page-0001-vector-001", "page-0001-vector-002"])
            self.assertEqual(preflight["pages"][0]["vector_regions"], 2)

    def test_real_rotated_pdf_keeps_multiple_anchor_spans_and_validates_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            raw, pdf = self._canvas(directory, "raw-anchors.pdf")
            pdf.drawString(72, 700, "First Second")
            pdf.linkAbsolute("first", "one", Rect=(70, 696, 98, 712), thickness=0)
            pdf.linkAbsolute("second", "two", Rect=(100, 696, 145, 712), thickness=0)
            pdf.showPage()
            pdf.bookmarkPage("one")
            pdf.drawString(72, 700, "One")
            pdf.showPage()
            pdf.bookmarkPage("two")
            pdf.drawString(72, 700, "Two")
            pdf.save()
            reader = PdfReader(raw)
            writer = PdfWriter()
            writer.clone_document_from_reader(reader)
            writer.pages[0].rotate(90)
            source = directory / "anchors.pdf"
            with source.open("wb") as handle:
                writer.write(handle)

            _, records = extract_pdf(source)
            linked = next(record for record in records if record.text == "First Second")
            self.assertEqual([link["target_page"] for link in linked.links], [2, 3])
            self.assertEqual([link["text"] for link in linked.links], ["First", "Second"])
            self.assertEqual(len({tuple(link["bbox"]) for link in linked.links}), 2)
            blocks = classify_records(records)
            report = validate_release(
                blocks,
                page_count=3,
                reader_targets={"section-2", "section-3"},
                page_targets={2: "section-2", 3: "section-3"},
            )
            self.assertTrue(report.releasable, [item.to_dict() for item in report.items])


if __name__ == "__main__":
    unittest.main()
