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

    def test_joins_wrapped_lines_on_the_same_page(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 100, 540, 120), reading_order=0, text="A wrapped paragraph continues"),
            ExtractionRecord(page=1, bbox=(72, 124, 540, 144), reading_order=1, text="on its second visual line."),
        ]

        blocks = classify_records(records)

        self.assertEqual([(block.kind, block.data["text"]) for block in blocks], [("paragraph", "A wrapped paragraph continues on its second visual line.")])

    def test_preserves_paragraphs_separated_by_vertical_space(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 100, 540, 120), reading_order=0, text="The first paragraph ends here."),
            ExtractionRecord(page=1, bbox=(72, 148, 540, 168), reading_order=1, text="The next paragraph starts after space."),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["The first paragraph ends here.", "The next paragraph starts after space."])

    def test_joins_an_unfinished_paragraph_across_sequential_pages(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="A paragraph carries over"),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=0, text="to the next page without a break."),
        ]

        blocks = classify_records(records)

        self.assertEqual(blocks[0].data["text"], "A paragraph carries over to the next page without a break.")
        self.assertEqual([source.page for source in blocks[0].provenance], [1, 2])

    def test_continues_lists_and_wrapped_items_across_pages(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 680, 540, 700), reading_order=3, text="1. First item wraps"),
            ExtractionRecord(page=1, bbox=(96, 704, 540, 724), reading_order=4, text="onto another visual line."),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=0, text="2. Second item"),
            ExtractionRecord(page=2, bbox=(96, 96, 540, 116), reading_order=1, text="continues on this page."),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "list")
        self.assertEqual(blocks[0].data, {"ordered": True, "items": ["First item wraps onto another visual line.", "Second item continues on this page."]})
        self.assertEqual([source.page for source in blocks[0].provenance], [1, 1, 2, 2])

    def test_joined_paragraph_unions_source_provenance(self):
        records = [
            ExtractionRecord(page=4, bbox=(72, 100, 540, 120), reading_order=0, text="Provenance begins"),
            ExtractionRecord(page=4, bbox=(72, 124, 540, 144), reading_order=1, text="with every contributing line."),
        ]

        block = classify_records(records)[0]

        self.assertEqual([(source.page, source.reading_order) for source in block.provenance], [(4, 0), (4, 1)])

    def test_does_not_fuse_repeated_furniture_at_page_edges(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="Monthly Community Bulletin"),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=0, text="Monthly Community Bulletin"),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["Monthly Community Bulletin", "Monthly Community Bulletin"])

    def test_preserves_complete_adjacent_paragraphs_with_initial_capitals(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 100, 540, 120), reading_order=0, text="Complete sentence."),
            ExtractionRecord(page=1, bbox=(72, 124, 540, 144), reading_order=1, text="New paragraph."),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["Complete sentence.", "New paragraph."])

    def test_preserves_compound_hyphens_and_joins_marked_discretionary_hyphens(self):
        compound = classify_records([
            ExtractionRecord(page=1, bbox=(72, 100, 540, 120), reading_order=0, text="A long-"),
            ExtractionRecord(page=1, bbox=(72, 124, 540, 144), reading_order=1, text="term plan."),
        ])
        discretionary = classify_records([
            ExtractionRecord(page=1, bbox=(72, 100, 540, 120), reading_order=0, text="An inter-", metadata={"discretionary_hyphen": True}),
            ExtractionRecord(page=1, bbox=(72, 124, 540, 144), reading_order=1, text="national agreement."),
        ])

        self.assertEqual(compound[0].data["text"], "A long-term plan.")
        self.assertEqual(discretionary[0].data["text"], "An international agreement.")

    def test_does_not_continue_ordered_list_when_numbering_restarts_on_next_page(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="1. First list item"),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=0, text="1. Restarted list item"),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["items"] for block in blocks], [["First list item"], ["Restarted list item"]])


if __name__ == "__main__":
    unittest.main()
