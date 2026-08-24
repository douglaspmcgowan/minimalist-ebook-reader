import unittest

from tools.pdf_to_ebook.model import Provenance, ReviewItem, SemanticBlock
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


if __name__ == "__main__":
    unittest.main()
