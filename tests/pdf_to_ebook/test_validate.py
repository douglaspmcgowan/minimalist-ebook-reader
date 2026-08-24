import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.pdf_to_ebook.model import ExtractionRecord, Provenance, ReviewItem, SemanticBlock
from tools.pdf_to_ebook.semantics import classify_records
from tools.pdf_to_ebook.validate import extraction_finding_id, validate_release


def block(page=1):
    return SemanticBlock(
        kind="paragraph",
        data={"text": "Synthetic prose."},
        provenance=[Provenance(page=page, bbox=(1, 2, 3, 4), reading_order=0)],
        confidence=0.98,
        evidence=["synthetic-test"],
    )


class ValidationTests(unittest.TestCase):
    def test_extraction_finding_identity_distinguishes_object_and_field_scope(self):
        object_finding = extraction_finding_id(
            "ambiguous-label", 1, 2, (10, 20, 30, 40), object_id="shared-label"
        )
        field_finding = extraction_finding_id(
            "ambiguous-label", 1, 2, (10, 20, 30, 40), field_name="shared-label"
        )
        delimiter_object_finding = extraction_finding_id(
            "ambiguous-label", 1, 2, (10, 20, 30, 40), object_id="shared|field_name=tail"
        )
        delimiter_field_finding = extraction_finding_id(
            "ambiguous-label",
            1,
            2,
            (10, 20, 30, 40),
            object_id="shared",
            field_name="tail|field_name=",
        )

        self.assertNotEqual(object_finding, field_finding)
        self.assertNotEqual(delimiter_object_finding, delimiter_field_finding)

    def test_approval_with_extra_canonical_scope_cannot_cover_object_and_field_findings(self):
        common_review = {
            "code": "ambiguous-label",
            "severity": "high",
            "message": "Review required.",
        }
        records = [
            ExtractionRecord(
                page=1,
                bbox=(10, 20, 30, 40),
                reading_order=2,
                text="Object finding.",
                metadata={"review": [{**common_review, "object_id": "shared-label"}]},
            ),
            ExtractionRecord(
                page=1,
                bbox=(10, 20, 30, 40),
                reading_order=2,
                text="Field finding.",
                metadata={"review": [{**common_review, "field_name": "shared-label"}]},
            ),
        ]
        initial = validate_release([block()], page_count=1, extraction_records=records)
        finding_id = initial.items[0].details["finding_id"]
        approval = ReviewItem(
            code="ambiguous-label",
            severity="high",
            page=1,
            message="Reviewed.",
            approved=True,
            details={
                "finding_id": finding_id,
                "bbox": [10, 20, 30, 40],
                "reading_order": 2,
                "object_id": "shared-label",
                "field_name": "shared-label",
            },
        )

        report = validate_release([block()], page_count=1, extraction_records=records, review_items=[approval])
        findings = [item for item in report.items if item.code == "ambiguous-label"]

        self.assertFalse(report.releasable)
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(not finding.approved for finding in findings))
        self.assertTrue(any(item.code == "invalid-extraction-approval" for item in report.items))

    def test_missing_page_coverage_blocks_release(self):
        report = validate_release([block(page=1)], page_count=2)
        self.assertFalse(report.releasable)
        self.assertEqual(report.missing_pages, [2])
        self.assertTrue(any(item.code == "missing-page-coverage" for item in report.items))

    def test_missing_provenance_blocks_release(self):
        broken = block()
        broken.provenance = []
        report = validate_release([broken], page_count=1)
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "missing-provenance" for item in report.items))

    def test_unresolved_high_severity_item_blocks_release(self):
        unresolved = ReviewItem(code="uncertain-reading-order", severity="high", page=1, message="Review required")
        report = validate_release([block()], page_count=1, review_items=[unresolved])
        self.assertFalse(report.releasable)
        self.assertEqual(report.unresolved_high_severity, 1)

    def test_preserves_every_extraction_review_finding(self):
        records = [
            ExtractionRecord(
                page=1,
                bbox=(1, 2, 3, 4),
                reading_order=0,
                text="Synthetic prose.",
                metadata={"review": [
                    {"code": "uncertain-reading-order", "severity": "high", "message": "Order one.", "object_id": "column-1", "details": {"column": "right"}},
                    {"code": "missing-figure-materialization", "severity": "high", "message": "Figure one."},
                ]},
            ),
            ExtractionRecord(
                page=1,
                bbox=(5, 6, 7, 8),
                reading_order=1,
                text="More prose.",
                metadata={"review": [
                    {"code": "uncertain-reading-order", "severity": "high", "message": "Order two."},
                ]},
            ),
        ]

        report = validate_release([block()], page_count=1, extraction_records=records)

        self.assertFalse(report.releasable)
        self.assertEqual(report.unresolved_high_severity, 3)
        self.assertEqual(
            [(item.code, item.message, item.page, item.details["reading_order"]) for item in report.items],
            [
                ("uncertain-reading-order", "Order one.", 1, 0),
                ("missing-figure-materialization", "Figure one.", 1, 0),
                ("uncertain-reading-order", "Order two.", 1, 1),
            ],
        )
        self.assertEqual(report.items[0].details["object_id"], "column-1")
        self.assertEqual(report.items[0].details["column"], "right")

    def test_extraction_metadata_cannot_approve_or_misspell_away_a_high_review(self):
        record = ExtractionRecord(
            page=1,
            bbox=(1, 2, 3, 4),
            reading_order=0,
            text="Synthetic prose.",
            metadata={"review": [{
                "code": "uncertain-reading-order",
                "severity": "HIGH",
                "message": "Review required.",
                "approved": True,
            }]},
        )

        report = validate_release([block()], page_count=1, extraction_records=[record])

        self.assertFalse(report.releasable)
        self.assertEqual(report.unresolved_high_severity, 1)
        self.assertEqual(report.items[0].severity, "high")
        self.assertFalse(report.items[0].approved)

    def test_extraction_approval_requires_the_generated_finding_scope(self):
        record = ExtractionRecord(
            page=2,
            bbox=(10, 20, 30, 40),
            reading_order=3,
            text="Synthetic prose.",
            metadata={"review": [{
                "code": "uncertain-reading-order",
                "severity": "high",
                "message": "Review required.",
                "object_id": "column-2",
            }]},
        )
        initial = validate_release([block(page=2)], page_count=2, intentionally_excluded_pages=[1], extraction_records=[record])
        finding = initial.items[0]
        approval = ReviewItem(
            code="different-code",
            severity=finding.severity,
            page=1,
            message="Reviewed disposition.",
            approved=True,
            details={
                "finding_id": finding.details["finding_id"],
                "bbox": finding.details["bbox"],
                "reading_order": finding.details["reading_order"],
                "object_id": finding.details["object_id"],
            },
        )

        report = validate_release(
            [block(page=2)],
            page_count=2,
            intentionally_excluded_pages=[1],
            extraction_records=[record],
            review_items=[approval],
        )

        generated = next(item for item in report.items if item.code == "uncertain-reading-order")
        self.assertFalse(report.releasable)
        self.assertFalse(generated.approved)
        self.assertEqual(generated.page, 2)
        self.assertEqual(generated.message, "Review required.")

    def test_matching_extraction_approval_retains_finding_and_records_disposition(self):
        record = ExtractionRecord(
            page=1,
            bbox=(10, 20, 30, 40),
            reading_order=3,
            text="Synthetic prose.",
            metadata={"review": [{
                "code": "widget-label-name-fallback",
                "severity": "high",
                "message": "Generated finding.",
                "field_name": "email",
            }]},
        )
        finding = validate_release([block()], page_count=1, extraction_records=[record]).items[0]
        approval = ReviewItem(
            code=finding.code,
            severity=finding.severity,
            page=finding.page,
            message="The field-name fallback is accurate.",
            approved=True,
            details={
                key: finding.details[key]
                for key in ("finding_id", "bbox", "reading_order", "field_name")
            },
        )

        report = validate_release([block()], page_count=1, extraction_records=[record], review_items=[approval])

        retained = next(item for item in report.items if item.details.get("finding_id") == finding.details["finding_id"])
        self.assertTrue(report.releasable, [item.to_dict() for item in report.items])
        self.assertTrue(retained.approved)
        self.assertEqual(retained.message, "Generated finding.")
        self.assertEqual(retained.details["disposition"], "The field-name fallback is accurate.")

    def test_low_confidence_semantics_enter_blocking_review(self):
        uncertain = block()
        uncertain.confidence = 0.6
        report = validate_release([uncertain], page_count=1)
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "low-confidence-structure" for item in report.items))

    def test_invalid_table_shape_and_missing_figure_alt_block_release(self):
        source = [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)]
        table = SemanticBlock("table", {"headers": ["A", "B"], "rows": [["only one"]]}, source, 0.98, ["table-grid"])
        figure = SemanticBlock("figure", {"asset": "assets/example.png", "alt": ""}, source, 0.98, ["non-text-object"])
        report = validate_release([table, figure], page_count=1)
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "invalid-table-shape" for item in report.items))
        self.assertTrue(any(item.code == "missing-figure-alt" for item in report.items))

    def test_ambiguous_headerless_table_fragment_blocks_release(self):
        records = [
            ExtractionRecord(
                page=1,
                bbox=(72, 620, 540, 720),
                reading_order=4,
                role_hint="table",
                table={"caption": "Totals", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]},
                metadata={"table_header_source": "inferred-first-row"},
            ),
            ExtractionRecord(
                page=2,
                bbox=(72, 72, 540, 160),
                reading_order=0,
                role_hint="table",
                table={"caption": None, "headers": ["Q2", "$12"], "rows": []},
                metadata={"table_header_source": "inferred-first-row"},
            ),
        ]

        report = validate_release(classify_records(records), page_count=2)

        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "ambiguous-table-continuation" and item.page == 2 for item in report.items))

    def test_approved_or_low_severity_items_do_not_block_release(self):
        items = [
            ReviewItem(code="uncertain-reading-order", severity="high", page=1, message="Reviewed", approved=True),
            ReviewItem(code="minor-spacing", severity="low", page=1, message="Review suggested"),
        ]
        report = validate_release([block()], page_count=1, review_items=items)
        self.assertTrue(report.releasable)
        self.assertEqual(report.covered_pages, [1])

    def test_inconsistent_provenance_order_blocks_release(self):
        later = block()
        later.provenance = [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=2)]
        earlier = block()
        earlier.provenance = [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=1)]
        report = validate_release([later, earlier], page_count=1)
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "inconsistent-provenance-order" for item in report.items))

    def test_unresolved_contents_target_blocks_release(self):
        contents = SemanticBlock(
            "contents",
            {"entries": [{"title": "Missing chapter", "target": "missing-section"}]},
            [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
            0.98,
            ["internal-link-target"],
        )
        report = validate_release([contents], page_count=1, reader_targets={"section-1"})
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "unresolved-contents-target" for item in report.items))

    def test_invalid_reader_target_grammar_blocks_even_known_targets(self):
        contents = SemanticBlock(
            "contents",
            {"entries": [{"title": "Unsafe", "target": "bad target"}]},
            [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
            0.98,
            ["internal-link-target"],
        )
        report = validate_release([contents], page_count=1, reader_targets={"bad target"})
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "invalid-reader-target" for item in report.items))

    def test_form_inventory_and_field_relationships_block_release(self):
        form = SemanticBlock(
            "form",
            {"title": "Budget", "fields": [{"value": ""}]},
            [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
            0.98,
            ["label-field-relationships"],
        )
        report = validate_release([form], page_count=1)
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "missing-form-field-label" for item in report.items))

    def test_missing_form_inventory_blocks_release(self):
        form = SemanticBlock(
            "form",
            {"title": "Budget"},
            [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
            0.98,
            ["label-field-relationships"],
        )
        report = validate_release([form], page_count=1)
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "missing-form-inventory" for item in report.items))

    def test_form_requires_root_title_and_inventory_without_nested_rows(self):
        forms = [
            SemanticBlock("form", {"title": " ", "fields": [{"label": "Income"}]}, [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)], 0.98, ["label-field-relationships"]),
            SemanticBlock("form", {"title": "Budget", "fields": [], "rows": []}, [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=1)], 0.98, ["label-field-relationships"]),
            SemanticBlock("form", {"title": "Budget", "worksheet": {"rows": [{"label": "Hidden"}]}}, [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=2)], 0.98, ["label-field-relationships"]),
        ]
        report = validate_release(forms, page_count=1)
        self.assertFalse(report.releasable)
        codes = {item.code for item in report.items}
        self.assertTrue({"missing-form-title", "missing-form-inventory", "unsupported-nested-form-rows"} <= codes)

    def test_unaccounted_non_text_object_blocks_release(self):
        report = validate_release([block()], page_count=1, non_text_objects=[{"id": "chart-1", "page": 1}])
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "missing-non-text-object-disposition" for item in report.items))

    def test_automatic_extraction_vector_inventory_requires_coverage(self):
        vector = ExtractionRecord(
            page=1,
            bbox=(200, 300, 280, 360),
            reading_order=1,
            role_hint="non_text_object",
            metadata={"object_id": "page-0001-vector-001", "object_kind": "vector"},
        )

        report = validate_release([block()], page_count=1, extraction_records=[vector])

        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "missing-non-text-object-disposition" for item in report.items))

    def test_automatic_vector_inventory_accepts_matching_semantic_provenance(self):
        source = Provenance(page=1, bbox=(200, 300, 280, 360), reading_order=0)
        vector = ExtractionRecord(
            page=1,
            bbox=source.bbox,
            reading_order=0,
            role_hint="non_text_object",
            metadata={"object_id": "page-0001-vector-001", "object_kind": "vector"},
        )
        divider = SemanticBlock("divider", {"object_id": "page-0001-vector-001"}, [source], 0.98, ["vector-geometry"])

        report = validate_release([divider], page_count=1, extraction_records=[vector])

        self.assertTrue(report.releasable, [item.to_dict() for item in report.items])

    def test_vector_disposition_approval_is_scoped_to_one_object(self):
        vectors = [
            ExtractionRecord(
                page=1,
                bbox=(20 * number, 100, 20 * number + 10, 110),
                reading_order=number,
                role_hint="non_text_object",
                metadata={"object_id": f"vector-{number}", "object_kind": "vector"},
            )
            for number in (1, 2)
        ]
        approval = ReviewItem(
            "non-text-object-disposition",
            "high",
            1,
            "First vector is decorative.",
            approved=True,
            details={"object_id": "vector-1"},
        )

        report = validate_release([block()], page_count=1, extraction_records=vectors, review_items=[approval])

        missing = [item for item in report.items if item.code == "missing-non-text-object-disposition"]
        self.assertEqual(len(missing), 1)
        self.assertIn("vector-2", missing[0].message)

    def test_duplicate_non_text_object_ids_block_release_despite_approval(self):
        objects = [
            {"id": "duplicate", "page": 1, "bbox": [20, 100, 30, 110]},
            {"id": "duplicate", "page": 2, "bbox": [20, 100, 30, 110]},
        ]
        approval = ReviewItem(
            "non-text-object-disposition",
            "high",
            1,
            "First object is decorative.",
            approved=True,
            details={"object_id": "duplicate"},
        )

        report = validate_release(
            [block(page=1), block(page=2)],
            page_count=2,
            non_text_objects=objects,
            review_items=[approval],
        )

        self.assertTrue(any(item.code == "duplicate-non-text-object-id" for item in report.items))

    def test_numeric_zero_non_text_id_matches_semantic_coverage(self):
        source = Provenance(page=1, bbox=(20, 100, 30, 110), reading_order=0)
        divider = SemanticBlock("divider", {"object_id": 0}, [source], 0.98, ["vector-geometry"])

        report = validate_release(
            [divider],
            page_count=1,
            non_text_objects=[{"id": 0, "page": 1, "bbox": [200, 300, 220, 320]}],
        )

        self.assertTrue(report.releasable, [item.to_dict() for item in report.items])

    def test_non_text_semantic_coverage_must_be_on_the_inventory_page(self):
        figure = SemanticBlock(
            "figure",
            {"asset": "assets/vector.png", "alt": "Vector", "object_id": "shared-id"},
            [Provenance(page=2, bbox=(20, 100, 30, 110), reading_order=0)],
            0.98,
            ["non-text-object"],
        )

        report = validate_release(
            [figure],
            page_count=2,
            intentionally_excluded_pages=[1],
            non_text_objects=[{"id": "shared-id", "page": 1}],
        )

        self.assertTrue(any(item.code == "missing-non-text-object-disposition" for item in report.items))

    def test_malformed_non_text_bbox_becomes_blocking_disposition(self):
        divider = SemanticBlock(
            "divider",
            {},
            [Provenance(page=1, bbox=(20, 100, 30, 110), reading_order=0)],
            0.98,
            ["vector-geometry"],
        )

        report = validate_release(
            [divider],
            page_count=1,
            non_text_objects=[{"page": 1, "bbox": ["bad", 100, 30, 110]}],
        )

        self.assertTrue(any(item.code == "missing-non-text-object-disposition" for item in report.items))

    def test_anonymous_non_text_inventory_cannot_use_page_wide_coverage(self):
        divider = SemanticBlock(
            "divider",
            {},
            [Provenance(page=1, bbox=(20, 100, 30, 110), reading_order=0)],
            0.98,
            ["vector-geometry"],
        )

        report = validate_release([divider], page_count=1, non_text_objects=[{"page": 1}])

        self.assertTrue(any(item.code == "missing-non-text-object-disposition" for item in report.items))

    def test_unhashable_non_text_identifier_becomes_blocking_disposition(self):
        report = validate_release([block()], page_count=1, non_text_objects=[{"id": {"bad": "id"}, "page": 1}])

        self.assertTrue(any(item.code == "missing-non-text-object-disposition" for item in report.items))

    def test_ordinary_link_targets_must_resolve(self):
        paragraph = SemanticBlock(
            "paragraph",
            {"text": "See appendix", "links": [{"target_page": 2, "bbox": [10, 20, 80, 40], "text": "appendix"}]},
            [Provenance(page=1, bbox=(10, 20, 100, 40), reading_order=0)],
            0.98,
            ["internal-link-target"],
        )

        missing = validate_release([paragraph], page_count=2, intentionally_excluded_pages=[2])
        resolved = validate_release(
            [paragraph],
            page_count=2,
            intentionally_excluded_pages=[2],
            reader_targets={"section-2"},
            page_targets={2: "section-2"},
        )

        self.assertFalse(missing.releasable)
        self.assertTrue(any(item.code == "unresolved-link-target" for item in missing.items))
        self.assertTrue(resolved.releasable, [item.to_dict() for item in resolved.items])

    def test_malformed_ordinary_link_geometry_blocks_release(self):
        paragraph = SemanticBlock(
            "paragraph",
            {"text": "See appendix", "links": [{"target": "section-2", "bbox": ["bad", 20, 80, 40]}]},
            [Provenance(page=1, bbox=(10, 20, 100, 40), reading_order=0)],
            0.98,
            ["internal-link-target"],
        )

        report = validate_release(
            [paragraph],
            page_count=1,
            reader_targets={"section-2"},
        )

        self.assertTrue(any(item.code == "invalid-link-geometry" for item in report.items))

    def test_asset_integrity_blocks_missing_and_mismatched_assets(self):
        figure = SemanticBlock(
            "figure",
            {"asset": "assets/chart.png", "alt": "Chart", "sha256": "0" * 64},
            [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
            0.98,
            ["non-text-object"],
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "assets").mkdir()
            (root / "assets" / "chart.png").write_bytes(b"chart")
            report = validate_release([figure], page_count=1, asset_root=root)
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "asset-sha256-mismatch" for item in report.items))

    def test_figure_requires_an_asset_root_for_integrity_verification(self):
        figure = SemanticBlock(
            "figure",
            {"asset": "assets/chart.png", "alt": "Chart", "sha256": hashlib.sha256(b"chart").hexdigest()},
            [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
            0.98,
            ["non-text-object"],
        )

        report = validate_release([figure], page_count=1)

        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "missing-asset-root" for item in report.items))

    def test_asset_integrity_blocks_missing_assets(self):
        figure = SemanticBlock(
            "figure",
            {"asset": "assets/missing.png", "alt": "Chart", "sha256": "0" * 64},
            [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
            0.98,
            ["non-text-object"],
        )
        with tempfile.TemporaryDirectory() as temp:
            report = validate_release([figure], page_count=1, asset_root=Path(temp))
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "missing-asset" for item in report.items))

    def test_asset_integrity_ignores_reader_query_and_fragment_suffixes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            asset = root / "assets" / "chart.png"
            asset.parent.mkdir()
            asset.write_bytes(b"chart")
            figure = SemanticBlock(
                "figure",
                {"asset": "assets/chart.png?v=1#chart", "alt": "Chart", "sha256": hashlib.sha256(b"chart").hexdigest()},
                [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
                0.98,
                ["non-text-object"],
            )

            report = validate_release([figure], page_count=1, asset_root=root)

        self.assertTrue(report.releasable)

    def test_expected_source_text_tokens_block_coverage_gaps(self):
        report = validate_release([block()], page_count=1, expected_source_tokens=["Synthetic", "missing-token"])
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "missing-source-text-token" for item in report.items))

    def test_text_coverage_does_not_count_asset_identifiers_as_source_text(self):
        figure = SemanticBlock(
            "figure",
            {"asset": "figures/chart.png", "alt": "A diagram"},
            [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
            0.98,
            ["non-text-object"],
        )
        report = validate_release([figure], page_count=1, expected_source_tokens=["chart"])
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "missing-source-text-token" for item in report.items))

    def test_asset_path_must_match_reader_safe_asset_contract(self):
        figure = SemanticBlock(
            "figure",
            {"asset": "figures/chart.png", "alt": "Chart", "sha256": hashlib.sha256(b"chart").hexdigest()},
            [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)],
            0.98,
            ["non-text-object"],
        )
        report = validate_release([figure], page_count=1)
        self.assertFalse(report.releasable)
        self.assertTrue(any(item.code == "unsafe-reader-asset-path" for item in report.items))

    def test_valid_release_passes_extended_gates(self):
        source = [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=0)]
        contents = SemanticBlock("contents", {"entries": [{"title": "Budget", "target": "section-1"}]}, source, 0.98, ["internal-link-target"])
        form = SemanticBlock("form", {"title": "Budget", "fields": [{"label": "Income", "value": ""}]}, [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=1)], 0.98, ["label-field-relationships"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "assets").mkdir()
            asset = root / "assets" / "chart.png"
            asset.write_bytes(b"chart")
            figure = SemanticBlock(
                "figure",
                {"asset": "assets/chart.png", "alt": "Chart", "sha256": hashlib.sha256(b"chart").hexdigest(), "object_id": "chart-1"},
                [Provenance(page=1, bbox=(1, 2, 3, 4), reading_order=2)],
                0.98,
                ["non-text-object"],
            )
            report = validate_release(
                [contents, form, figure],
                page_count=1,
                reader_targets={"section-1"},
                non_text_objects=[{"id": "chart-1", "page": 1}],
                asset_root=root,
                expected_source_tokens=["Budget", "Income", "Chart"],
            )
        self.assertTrue(report.releasable)


if __name__ == "__main__":
    unittest.main()
