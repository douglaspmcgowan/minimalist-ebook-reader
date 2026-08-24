import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.pdf_to_ebook.model import ExtractionRecord, Provenance, ReviewItem, SemanticBlock
from tools.pdf_to_ebook.validate import validate_release


def block(page=1):
    return SemanticBlock(
        kind="paragraph",
        data={"text": "Synthetic prose."},
        provenance=[Provenance(page=page, bbox=(1, 2, 3, 4), reading_order=0)],
        confidence=0.98,
        evidence=["synthetic-test"],
    )


class ValidationTests(unittest.TestCase):
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
