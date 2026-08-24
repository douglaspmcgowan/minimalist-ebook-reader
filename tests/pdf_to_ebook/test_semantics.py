import json
import unittest
from pathlib import Path

from tools.pdf_to_ebook.model import ExtractionRecord, stable_json_bytes
from tools.pdf_to_ebook.semantics import classify_records


FIXTURE = Path(__file__).parent / "fixtures" / "semantic-layout.json"


class SemanticClassificationTests(unittest.TestCase):
    def setUp(self):
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.records = [ExtractionRecord.from_dict(item) for item in raw["records"]]

    def test_classifies_all_required_structures(self):
        blocks = classify_records(self.records)
        kinds = [block.kind for block in blocks]
        for expected in ("contents", "list", "table", "form", "figure", "index"):
            self.assertIn(expected, kinds)

    def test_contents_entries_preserve_links_and_subtitles(self):
        contents = next(block for block in classify_records(self.records) if block.kind == "contents")
        self.assertEqual(contents.data["entries"][0]["title"], "1  Starting Well")
        self.assertEqual(contents.data["entries"][0]["subtitle"], "A practical beginning")
        self.assertEqual(contents.data["entries"][0]["target_page"], 2)

    def test_internal_link_can_classify_contents_without_profile_hint(self):
        linked = ExtractionRecord(
            page=1,
            bbox=(72, 100, 500, 120),
            reading_order=0,
            text="Opening chapter",
            links=[{"target_page": 3}],
        )
        blocks = classify_records([linked])
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "contents")
        self.assertEqual(blocks[0].data["entries"][0]["target_page"], 3)

    def test_list_table_form_figure_and_index_are_structured(self):
        by_kind = {block.kind: block for block in classify_records(self.records)}
        self.assertEqual(by_kind["list"].data["items"], ["First step", "Second step"])
        self.assertEqual(by_kind["table"].data["headers"], ["Quarter", "Amount"])
        self.assertEqual(by_kind["form"].data["fields"][0]["label"], "Income")
        self.assertEqual(by_kind["figure"].data["alt"], "A rising line chart")
        self.assertEqual(by_kind["index"].data["entries"][0]["locators"], ["12", "30"])

    def test_output_is_byte_stable_regardless_of_input_order(self):
        first = stable_json_bytes([b.to_dict() for b in classify_records(self.records)])
        second = stable_json_bytes([b.to_dict() for b in classify_records(list(reversed(self.records)))])
        self.assertEqual(first, second)

    def test_every_block_has_complete_provenance_and_evidence(self):
        for block in classify_records(self.records):
            self.assertGreaterEqual(block.confidence, 0)
            self.assertLessEqual(block.confidence, 1)
            self.assertTrue(block.evidence)
            self.assertTrue(block.provenance)
            for source in block.provenance:
                self.assertGreater(source.page, 0)
                self.assertEqual(len(source.bbox), 4)
                self.assertGreaterEqual(source.reading_order, 0)


if __name__ == "__main__":
    unittest.main()
