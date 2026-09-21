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

    def test_single_internal_link_remains_prose_with_link_metadata(self):
        linked = ExtractionRecord(
            page=1,
            bbox=(72, 100, 500, 120),
            reading_order=0,
            text="See appendix",
            links=[{"target_page": 3}],
        )
        blocks = classify_records([linked])
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "paragraph")
        self.assertEqual(blocks[0].data, {"text": "See appendix", "links": [{"target_page": 3}]})

    def test_aligned_internal_link_cluster_classifies_as_contents(self):
        linked = [
            ExtractionRecord(page=1, bbox=(72, 100, 500, 120), reading_order=0, text="Opening", links=[{"target_page": 2}]),
            ExtractionRecord(page=1, bbox=(72, 124, 500, 144), reading_order=1, text="Appendix", links=[{"target_page": 3}]),
        ]

        blocks = classify_records(linked)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "contents")
        self.assertEqual([entry["target_page"] for entry in blocks[0].data["entries"]], [2, 3])

    def test_fragments_from_one_anchor_do_not_become_contents(self):
        shared_link = {"target_page": 2, "bbox": [72, 100, 180, 120]}
        records = [
            ExtractionRecord(page=1, bbox=(72, 100, 100, 120), reading_order=0, text="Chap", links=[shared_link]),
            ExtractionRecord(page=1, bbox=(72, 124, 100, 144), reading_order=1, text="ter", links=[shared_link]),
        ]

        blocks = classify_records(records)

        self.assertNotIn("contents", [block.kind for block in blocks])

    def test_joins_multiline_anchor_prose_and_deduplicates_its_annotation(self):
        shared_link = {"target_page": 2, "bbox": [72, 100, 180, 144], "text": "wrapped appendix"}
        records = [
            ExtractionRecord(page=1, bbox=(72, 100, 180, 120), reading_order=0, text="See the wrapped", links=[shared_link]),
            ExtractionRecord(page=1, bbox=(72, 124, 180, 144), reading_order=1, text="appendix for details.", links=[shared_link]),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "paragraph")
        self.assertEqual(blocks[0].data["text"], "See the wrapped appendix for details.")
        self.assertEqual(blocks[0].data["links"], [shared_link])
        self.assertEqual([(source.page, source.reading_order) for source in blocks[0].provenance], [(1, 0), (1, 1)])

    def test_joined_link_prose_preserves_distinct_source_annotations(self):
        records = [
            ExtractionRecord(
                page=1,
                bbox=(72, 100, 300, 120),
                reading_order=0,
                text="The appendix reference wraps",
                links=[{"target_page": 2, "bbox": [72, 100, 220, 120], "text": "appendix reference"}],
            ),
            ExtractionRecord(
                page=1,
                bbox=(72, 124, 300, 144),
                reading_order=1,
                text="beside a separate note.",
                links=[{"target_page": 2, "bbox": [190, 124, 280, 144], "text": "separate note"}],
            ),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "paragraph")
        self.assertEqual([link["text"] for link in blocks[0].data["links"]], ["appendix reference", "separate note"])

    def test_malformed_anchor_geometry_does_not_abort_classification(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 100, 100, 120), reading_order=0, text="Chap", links=[{"target_page": 2, "bbox": ["bad", 1, 2, 3]}]),
            ExtractionRecord(page=1, bbox=(72, 124, 100, 144), reading_order=1, text="ter", links=[{"target_page": 2, "bbox": ["bad", 1, 2, 3]}]),
        ]

        blocks = classify_records(records)

        self.assertNotIn("contents", [block.kind for block in blocks])

    def test_malformed_link_entries_and_targets_do_not_abort_classification(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 100, 100, 120), reading_order=0, text="Bad entry", links=["bad"]),
            ExtractionRecord(page=1, bbox=(72, 124, 100, 144), reading_order=1, text="Bad target", links=[{"target_page": "wrong"}]),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.kind for block in blocks], ["paragraph", "paragraph"])

    def test_distant_internal_links_remain_separate_paragraphs(self):
        linked = [
            ExtractionRecord(page=1, bbox=(72, 100, 500, 120), reading_order=0, text="See chapter", links=[{"target_page": 2}]),
            ExtractionRecord(page=1, bbox=(72, 700, 500, 720), reading_order=1, text="See appendix", links=[{"target_page": 3}]),
        ]

        blocks = classify_records(linked)

        self.assertEqual([block.kind for block in blocks], ["paragraph", "paragraph"])
        self.assertEqual([block.data["links"][0]["target_page"] for block in blocks], [2, 3])

    def test_single_linked_heading_preserves_link_metadata(self):
        linked = ExtractionRecord(
            page=1,
            bbox=(72, 100, 500, 124),
            reading_order=0,
            text="See appendix",
            font_size=18,
            bold=True,
            links=[{"target_page": 3}],
        )

        block = classify_records([linked])[0]

        self.assertEqual(block.kind, "heading")
        self.assertEqual(block.data["links"], [{"target_page": 3}])

    def test_list_table_form_figure_and_index_are_structured(self):
        by_kind = {block.kind: block for block in classify_records(self.records)}
        self.assertEqual(by_kind["list"].data["items"], ["First step", "Second step"])
        self.assertEqual(by_kind["table"].data["headers"], ["Quarter", "Amount"])
        self.assertEqual(by_kind["form"].data["fields"][0]["label"], "Income")
        self.assertEqual(by_kind["figure"].data["alt"], "A rising line chart")
        self.assertEqual(by_kind["index"].data["entries"][0]["locators"], ["12", "30"])

    def test_figure_retains_materialized_asset_sha256(self):
        figure = ExtractionRecord(
            page=1,
            bbox=(72, 100, 172, 200),
            reading_order=0,
            role_hint="figure",
            asset="assets/figure.png",
            alt="Blue square",
            metadata={"asset_sha256": "a" * 64, "object_name": "figure-1"},
        )

        block = classify_records([figure])[0]

        self.assertEqual(block.data["asset"], "assets/figure.png")
        self.assertEqual(block.data["sha256"], "a" * 64)
        self.assertEqual(block.data["object_name"], "figure-1")

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

    def test_excluded_page_furniture_is_invisible_to_cross_page_structure_adjacency(self):
        furniture = ExtractionRecord(
            page=2,
            bbox=(240, 20, 372, 40),
            reading_order=0,
            text="Monthly Community Bulletin",
            role_hint="furniture",
        )
        cases = {
            "paragraph": (
                ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="A paragraph carries over"),
                ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=1, text="to the next page."),
                "paragraph",
            ),
            "heading": (
                ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="A Guide", bold=True, font_size=18),
                ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=1, text="to Saving", bold=True, font_size=18),
                "heading",
            ),
            "quotation": (
                ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="A quotation carries", role_hint="quotation"),
                ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=1, text="across the page", role_hint="quotation"),
                "quotation",
            ),
            "list": (
                ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="1. First item"),
                ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=1, text="2. Second item"),
                "list",
            ),
            "table": (
                ExtractionRecord(
                    page=1,
                    bbox=(72, 620, 540, 720),
                    reading_order=4,
                    role_hint="table",
                    table={"caption": "Totals", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]},
                ),
                ExtractionRecord(
                    page=2,
                    bbox=(72, 72, 540, 160),
                    reading_order=1,
                    role_hint="table",
                    table={"caption": None, "headers": ["Quarter", "Amount"], "rows": [["Q2", "$12"]]},
                ),
                "table",
            ),
        }

        for label, (first, second, expected_kind) in cases.items():
            with self.subTest(label=label):
                blocks = classify_records([first, furniture, second])
                self.assertEqual([block.kind for block in blocks], [expected_kind])
                self.assertEqual([source.page for source in blocks[0].provenance], [1, 2])

    def test_reviewed_non_text_exclusion_is_invisible_to_semantic_adjacency(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="A paragraph carries over"),
            ExtractionRecord(
                page=2,
                bbox=(240, 20, 372, 40),
                reading_order=0,
                text="",
                role_hint="non_text_object",
                metadata={"object_id": "vector-1", "semantic_exclusion": True},
            ),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=1, text="to the next page."),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["A paragraph carries over to the next page."])
        self.assertEqual([source.page for source in blocks[0].provenance], [1, 2])

    def test_unreviewed_non_text_object_remains_a_semantic_adjacency_barrier(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="A paragraph carries over"),
            ExtractionRecord(
                page=2,
                bbox=(240, 20, 372, 40),
                reading_order=0,
                text="",
                role_hint="non_text_object",
                metadata={"object_id": "vector-1"},
            ),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=1, text="to the next page."),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["A paragraph carries over", "to the next page."])

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

    def test_continues_list_across_proportionally_aligned_mixed_page_sizes(self):
        records = [
            ExtractionRecord(page=1, bbox=(36, 330, 264, 370), reading_order=4, text="1. First item", metadata={"page_width": 300, "page_height": 400}),
            ExtractionRecord(page=2, bbox=(72, 64, 528, 104), reading_order=0, text="2. Second item", metadata={"page_width": 600, "page_height": 800}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["items"] for block in blocks], [["First item", "Second item"]])

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

    def test_list_continuation_approval_applies_only_to_the_incoming_page_pair(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="1. First list item", metadata={"page_width": 612, "page_height": 792}),
            ExtractionRecord(
                page=2,
                bbox=(72, 72, 540, 720),
                reading_order=0,
                text="2. Approved continuation",
                metadata={"page_width": 612, "page_height": 792, "list_continuation": True},
            ),
            ExtractionRecord(page=3, bbox=(72, 72, 540, 92), reading_order=0, text="1. Restarted list item", metadata={"page_width": 612, "page_height": 792}),
        ]

        blocks = classify_records(records)

        self.assertEqual(
            [block.data["items"] for block in blocks],
            [["First list item", "Approved continuation"], ["Restarted list item"]],
        )

    def test_preserves_complete_paragraphs_before_opening_quotes(self):
        for opening_quote in ('“', '"', '‘', "'"):
            with self.subTest(opening_quote=opening_quote):
                records = [
                    ExtractionRecord(page=1, bbox=(72, 100, 540, 120), reading_order=0, text="Complete sentence."),
                    ExtractionRecord(page=1, bbox=(72, 124, 540, 144), reading_order=1, text=f"{opening_quote}New paragraph."),
                ]

                blocks = classify_records(records)

                self.assertEqual([block.data["text"] for block in blocks], ["Complete sentence.", f"{opening_quote}New paragraph."])

    def test_joins_split_table_across_sequential_page_edges(self):
        records = [
            ExtractionRecord(
                page=1,
                bbox=(72, 620, 540, 720),
                reading_order=4,
                role_hint="table",
                table={"caption": "Quarterly totals", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]},
            ),
            ExtractionRecord(
                page=2,
                bbox=(72, 72, 540, 160),
                reading_order=0,
                role_hint="table",
                table={"caption": None, "headers": ["Quarter", "Amount"], "rows": [["Q2", "$12"]]},
            ),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].kind, "table")
        self.assertEqual(blocks[0].data, {"caption": "Quarterly totals", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"], ["Q2", "$12"]]})
        self.assertEqual([source.page for source in blocks[0].provenance], [1, 2])
        self.assertIn("cross-page-continuation", blocks[0].evidence)

    def test_approved_headerless_table_continuation_promotes_inferred_first_row_to_data(self):
        records = [
            ExtractionRecord(
                page=1,
                bbox=(72, 620, 540, 720),
                reading_order=4,
                role_hint="table",
                table={"caption": "Quarterly totals", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]},
                metadata={"table_header_source": "inferred-first-row"},
            ),
            ExtractionRecord(
                page=2,
                bbox=(72, 72, 540, 160),
                reading_order=0,
                role_hint="table",
                table={"caption": None, "headers": ["Q2", "$12"], "rows": [["Q3", "$14"]]},
                metadata={"table_header_source": "inferred-first-row", "table_continuation": True},
            ),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].data, {
            "caption": "Quarterly totals",
            "headers": ["Quarter", "Amount"],
            "rows": [["Q1", "$10"], ["Q2", "$12"], ["Q3", "$14"]],
        })
        self.assertIn("approved-headerless-continuation", blocks[0].evidence)

    def test_table_continuation_approval_applies_only_to_the_incoming_page_pair(self):
        records = [
            ExtractionRecord(
                page=1,
                bbox=(72, 620, 540, 720),
                reading_order=4,
                role_hint="table",
                table={"caption": "Quarterly totals", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]},
                metadata={"page_width": 612, "page_height": 792, "table_header_source": "inferred-first-row"},
            ),
            ExtractionRecord(
                page=2,
                bbox=(72, 72, 540, 720),
                reading_order=0,
                role_hint="table",
                table={"caption": None, "headers": ["Q2", "$12"], "rows": [["Q3", "$14"]]},
                metadata={"page_width": 612, "page_height": 792, "table_header_source": "inferred-first-row", "table_continuation": True},
            ),
            ExtractionRecord(
                page=3,
                bbox=(72, 72, 540, 160),
                reading_order=0,
                role_hint="table",
                table={"caption": None, "headers": ["Alice", "Editor"], "rows": [["Bob", "Writer"]]},
                metadata={"page_width": 612, "page_height": 792, "table_header_source": "inferred-first-row"},
            ),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].data["rows"], [["Q1", "$10"], ["Q2", "$12"], ["Q3", "$14"]])
        self.assertEqual(blocks[1].data["headers"], ["Alice", "Editor"])
        self.assertIn("ambiguous-table-continuation", blocks[1].evidence)

    def test_heading_continuation_approval_applies_only_to_the_incoming_page_pair(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 680, 540, 720), reading_order=4, text="Terms", font_size=20, bold=True, role_hint="heading", metadata={"page_width": 612, "page_height": 792}),
            ExtractionRecord(
                page=2,
                bbox=(72, 72, 540, 720),
                reading_order=0,
                text="Conditions",
                font_size=20,
                bold=True,
                role_hint="heading",
                metadata={"page_width": 612, "page_height": 792, "heading_continuation": True},
            ),
            ExtractionRecord(page=3, bbox=(72, 72, 540, 112), reading_order=0, text="Appendix", font_size=20, bold=True, role_hint="heading", metadata={"page_width": 612, "page_height": 792}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["Terms Conditions", "Appendix"])

    def test_quotation_continuation_approval_applies_only_to_the_incoming_page_pair(self):
        records = [
            ExtractionRecord(page=1, bbox=(90, 680, 520, 720), reading_order=4, text="“A quotation", role_hint="quotation", metadata={"page_width": 612, "page_height": 792}),
            ExtractionRecord(
                page=2,
                bbox=(90, 72, 520, 720),
                reading_order=0,
                text="continues",
                role_hint="quotation",
                metadata={"page_width": 612, "page_height": 792, "quotation_continuation": True},
            ),
            ExtractionRecord(page=3, bbox=(90, 72, 520, 112), reading_order=0, text="Another quotation begins.", role_hint="quotation", metadata={"page_width": 612, "page_height": 792}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["“A quotation continues", "Another quotation begins."])

    def test_uncertain_headerless_table_continuation_is_preserved_for_review(self):
        records = [
            ExtractionRecord(
                page=1,
                bbox=(72, 620, 540, 720),
                reading_order=4,
                role_hint="table",
                table={"caption": "Quarterly totals", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]},
                metadata={"table_header_source": "inferred-first-row"},
            ),
            ExtractionRecord(
                page=2,
                bbox=(72, 72, 540, 160),
                reading_order=0,
                role_hint="table",
                table={"caption": None, "headers": ["Q2", "$12"], "rows": [["Q3", "$14"]]},
                metadata={"table_header_source": "inferred-first-row"},
            ),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[1].data["headers"], ["Q2", "$12"])
        self.assertLess(blocks[1].confidence, 0.7)
        self.assertIn("ambiguous-table-continuation", blocks[1].evidence)

    def test_explicit_continuation_does_not_merge_a_new_captioned_table(self):
        records = [
            ExtractionRecord(
                page=1,
                bbox=(72, 620, 540, 720),
                reading_order=4,
                role_hint="table",
                table={"caption": "Revenue", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]},
                metadata={"table_header_source": "inferred-first-row"},
            ),
            ExtractionRecord(
                page=2,
                bbox=(72, 72, 540, 160),
                reading_order=0,
                role_hint="table",
                table={"caption": "People", "headers": ["Name", "Role"], "rows": [["A", "Editor"]]},
                metadata={"table_header_source": "inferred-first-row", "table_continuation": True},
            ),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["caption"] for block in blocks], ["Revenue", "People"])
        self.assertLess(blocks[1].confidence, 0.7)
        self.assertIn("conflicting-table-continuation", blocks[1].evidence)

    def test_joins_table_across_proportionally_aligned_mixed_page_sizes(self):
        records = [
            ExtractionRecord(
                page=1,
                bbox=(36, 320, 264, 370),
                reading_order=4,
                role_hint="table",
                table={"caption": "Totals", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]},
                metadata={"page_width": 300, "page_height": 400},
            ),
            ExtractionRecord(
                page=2,
                bbox=(72, 64, 528, 144),
                reading_order=0,
                role_hint="table",
                table={"caption": None, "headers": ["Quarter", "Amount"], "rows": [["Q2", "$12"]]},
                metadata={"page_width": 600, "page_height": 800},
            ),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].data["rows"], [["Q1", "$10"], ["Q2", "$12"]])

    def test_joins_paragraph_across_proportionally_aligned_mixed_page_sizes(self):
        records = [
            ExtractionRecord(page=1, bbox=(36, 330, 264, 370), reading_order=4, text="A paragraph carries", metadata={"page_width": 300, "page_height": 400}),
            ExtractionRecord(page=2, bbox=(72, 64, 528, 104), reading_order=0, text="across differently sized pages.", metadata={"page_width": 600, "page_height": 800}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["A paragraph carries across differently sized pages."])

    def test_joins_paragraph_across_asymmetrically_cropped_page_edges(self):
        records = [
            ExtractionRecord(page=1, bbox=(75, 440, 525, 480), reading_order=4, text="A paragraph carries", metadata={"page_width": 600, "page_height": 800, "page_bbox": [50, 100, 550, 500]}),
            ExtractionRecord(page=2, bbox=(75, 220, 525, 260), reading_order=0, text="across cropped page boundaries.", metadata={"page_width": 600, "page_height": 800, "page_bbox": [50, 200, 550, 600]}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["A paragraph carries across cropped page boundaries."])

    def test_preserves_paragraph_when_small_page_source_is_away_from_bottom_edge(self):
        records = [
            ExtractionRecord(page=1, bbox=(36, 160, 264, 200), reading_order=4, text="A paragraph carries", metadata={"page_width": 300, "page_height": 400}),
            ExtractionRecord(page=2, bbox=(36, 36, 264, 76), reading_order=0, text="into unrelated lower-page text.", metadata={"page_width": 300, "page_height": 400}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["A paragraph carries", "into unrelated lower-page text."])

    def test_preserves_paragraph_when_small_page_candidate_is_away_from_top_edge(self):
        records = [
            ExtractionRecord(page=1, bbox=(36, 330, 264, 370), reading_order=4, text="A paragraph carries", metadata={"page_width": 300, "page_height": 400}),
            ExtractionRecord(page=2, bbox=(36, 100, 264, 140), reading_order=0, text="into unrelated lower-page text.", metadata={"page_width": 300, "page_height": 400}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["A paragraph carries", "into unrelated lower-page text."])

    def test_invalid_page_dimensions_use_geometry_fallback(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 700, 540, 720), reading_order=4, text="A paragraph carries", metadata={"page_width": True, "page_height": True}),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 92), reading_order=0, text="across legacy synthetic records.", metadata={"page_width": True, "page_height": True}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["A paragraph carries across legacy synthetic records."])

    def test_geometry_fallback_preserves_legacy_edge_threshold_for_narrow_records(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 500, 300, 520), reading_order=4, text="A paragraph carries"),
            ExtractionRecord(page=2, bbox=(72, 72, 300, 92), reading_order=0, text="into unrelated lower-page text."),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["A paragraph carries", "into unrelated lower-page text."])

    def test_preserves_distinct_tables_at_page_boundary_when_headers_differ(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 620, 540, 720), reading_order=4, role_hint="table", table={"caption": "Revenue", "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]}),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 160), reading_order=0, role_hint="table", table={"caption": "People", "headers": ["Name", "Role"], "rows": [["A", "Editor"]]}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["caption"] for block in blocks], ["Revenue", "People"])

    def test_preserves_malformed_table_fragments_for_release_validation(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 620, 540, 720), reading_order=4, role_hint="table", table={"caption": None, "headers": ["Quarter", "Amount"], "rows": [["Q1", "$10"]]}),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 160), reading_order=0, role_hint="table", table={"caption": None, "headers": ["Quarter", "Amount"], "rows": ["Q2, $12"]}),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[1].data["rows"], ["Q2, $12"])

    def test_joins_unfinished_quotation_across_sequential_page_edges(self):
        records = [
            ExtractionRecord(page=1, bbox=(90, 680, 520, 720), reading_order=4, text="“A quotation carries", role_hint="quotation"),
            ExtractionRecord(page=2, bbox=(90, 72, 520, 112), reading_order=0, text="across the page boundary.”", role_hint="quotation", metadata={"attribution": "Ada"}),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].data["text"], "“A quotation carries across the page boundary.”")
        self.assertEqual(blocks[0].data["attribution"], "Ada")
        self.assertEqual([source.page for source in blocks[0].provenance], [1, 2])
        self.assertIn("cross-page-continuation", blocks[0].evidence)

    def test_joins_quotation_across_proportionally_aligned_mixed_page_sizes(self):
        records = [
            ExtractionRecord(page=1, bbox=(45, 330, 260, 370), reading_order=4, text="“A quotation carries", role_hint="quotation", metadata={"page_width": 300, "page_height": 400}),
            ExtractionRecord(page=2, bbox=(90, 64, 520, 104), reading_order=0, text="across differently sized pages.”", role_hint="quotation", metadata={"page_width": 600, "page_height": 800, "attribution": "Ada"}),
        ]

        blocks = classify_records(records)

        self.assertEqual(blocks[0].data, {"attribution": "Ada", "text": "“A quotation carries across differently sized pages.”"})

    def test_preserves_complete_quotations_across_page_boundary(self):
        records = [
            ExtractionRecord(page=1, bbox=(90, 680, 520, 720), reading_order=4, text="“One complete quotation.”", role_hint="quotation"),
            ExtractionRecord(page=2, bbox=(90, 72, 520, 112), reading_order=0, text="“Another complete quotation.”", role_hint="quotation"),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["“One complete quotation.”", "“Another complete quotation.”"])

    def test_joins_wrapped_large_font_heading_across_sequential_page_edges(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 680, 540, 720), reading_order=4, text="A Practical Guide to", font_size=20, bold=True, role_hint="heading"),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 112), reading_order=0, text="Financial Freedom", font_size=20, bold=True, role_hint="heading"),
        ]

        blocks = classify_records(records)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].data["text"], "A Practical Guide to Financial Freedom")
        self.assertEqual([source.page for source in blocks[0].provenance], [1, 2])
        self.assertIn("cross-page-continuation", blocks[0].evidence)

    def test_joins_heading_across_proportionally_aligned_mixed_page_sizes(self):
        records = [
            ExtractionRecord(page=1, bbox=(36, 330, 264, 370), reading_order=4, text="A Practical Guide to", font_size=20, bold=True, role_hint="heading", metadata={"page_width": 300, "page_height": 400}),
            ExtractionRecord(page=2, bbox=(72, 64, 528, 104), reading_order=0, text="Financial Freedom", font_size=20, bold=True, role_hint="heading", metadata={"page_width": 600, "page_height": 800}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["A Practical Guide to Financial Freedom"])

    def test_preserves_separate_complete_headings_at_page_boundary(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 680, 540, 720), reading_order=4, text="Part One", font_size=20, bold=True, role_hint="heading"),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 112), reading_order=0, text="Part Two", font_size=20, bold=True, role_hint="heading"),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["text"] for block in blocks], ["Part One", "Part Two"])

    def test_preserves_headings_with_distinct_targets_at_page_boundary(self):
        records = [
            ExtractionRecord(page=1, bbox=(72, 680, 540, 720), reading_order=4, text="Terms and", font_size=20, bold=True, role_hint="heading", metadata={"target": "terms"}),
            ExtractionRecord(page=2, bbox=(72, 72, 540, 112), reading_order=0, text="Conditions", font_size=20, bold=True, role_hint="heading", metadata={"target": "conditions"}),
        ]

        blocks = classify_records(records)

        self.assertEqual([block.data["target"] for block in blocks], ["terms", "conditions"])


if __name__ == "__main__":
    unittest.main()
