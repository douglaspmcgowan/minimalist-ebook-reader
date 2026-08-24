import tempfile
import unittest
import hashlib
from pathlib import Path

from PIL import Image
from pypdf import PdfWriter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from tools.pdf_to_ebook.extract import extract_pdf


class ExtractionTests(unittest.TestCase):
    def _image(self, directory: Path) -> Path:
        source = directory / "figure.png"
        Image.new("RGB", (40, 30), color=(20, 80, 140)).save(source)
        return source

    def _canvas(self, directory: Path, name: str = "fixture.pdf") -> tuple[Path, canvas.Canvas]:
        source = directory / name
        return source, canvas.Canvas(str(source), pagesize=(612, 792))

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
            self.assertEqual(linked.links, [{"target_page": 2}])

    def test_extracts_real_widget_field_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory)
            pdf.drawString(72, 700, "Email")
            pdf.acroForm.textfield(name="email", x=72, y=640, width=180, height=24, borderWidth=1)
            pdf.save()

            _, records = extract_pdf(source)

            widget = next(record for record in records if record.role_hint == "form")
            self.assertEqual(widget.form["fields"], [{"name": "email", "type": "text", "value": "", "required": False}])
            self.assertEqual(widget.metadata["widget_name"], "email")

    def test_unmaterialized_figure_has_blocking_review_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, pdf = self._canvas(directory)
            pdf.drawImage(str(self._image(directory)), 72, 430, width=40, height=30)
            pdf.save()

            _, records = extract_pdf(source)

            figure = next(record for record in records if record.role_hint == "figure")
            self.assertIsNone(figure.asset)
            self.assertEqual("high", figure.metadata["review"]["severity"])

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
            self.assertEqual("high", records[0].metadata["review"]["severity"])


if __name__ == "__main__":
    unittest.main()
