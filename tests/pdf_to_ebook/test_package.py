import unittest

from tools.pdf_to_ebook.model import Provenance, SemanticBlock
from tools.pdf_to_ebook.package import build_reader_package


def block(kind, data, page, order, confidence=0.98):
    return SemanticBlock(
        kind=kind,
        data=data,
        provenance=[Provenance(page=page, bbox=(10, 20, 300, 40), reading_order=order)],
        confidence=confidence,
        evidence=["synthetic-test"],
    )


class ReaderPackageTests(unittest.TestCase):
    def build(self, blocks, page_count=2):
        return build_reader_package(
            blocks,
            page_count,
            {"sha256": "a" * 64, "metadata": {"Title": "Book"}},
            {},
        )

    def test_level_one_heading_becomes_provenance_bearing_chapter_title_only(self):
        package = self.build([
            block("heading", {"text": "Opening", "level": 1}, 1, 0, 0.96),
            block("paragraph", {"text": "Body"}, 1, 1),
        ])

        chapter = package["chapters"][0]
        self.assertEqual(chapter["title"], "Opening")
        self.assertEqual(chapter["titleProvenance"], [{"page": 1, "bbox": [10, 20, 300, 40], "reading_order": 0}])
        self.assertEqual(chapter["titleConfidence"], 0.96)
        self.assertEqual(chapter["titleEvidence"], ["synthetic-test"])
        self.assertEqual([entry["kind"] for entry in chapter["blocks"]], ["paragraph"])
        self.assertEqual([entry["kind"] for entry in package["blocks"]], ["heading", "paragraph"])

    def test_level_one_heading_links_are_resolved_on_the_chapter_title(self):
        package = self.build([
            block("heading", {"text": "Opening", "level": 1, "links": [{"target_page": 2}]}, 1, 0),
            block("heading", {"text": "Appendix", "level": 1}, 2, 0),
        ])

        self.assertEqual(package["chapters"][0]["titleLinks"], [{"target_page": 2, "target": "section-2"}])

    def test_every_ordinary_link_target_is_resolved_in_the_reader_package(self):
        package = self.build([
            block("heading", {"text": "Opening", "level": 1}, 1, 0),
            block("paragraph", {"text": "Compare", "links": [{"target_page": 1}, {"target_page": 2}]}, 1, 1),
            block("heading", {"text": "Appendix", "level": 1}, 2, 0),
        ])

        links = package["chapters"][0]["blocks"][0]["data"]["links"]
        self.assertEqual([link["target"] for link in links], ["section-1", "section-2"])

    def test_unresolved_ordinary_link_blocks_package_construction(self):
        with self.assertRaisesRegex(ValueError, "Ordinary link target page 3"):
            self.build([
                block("heading", {"text": "Opening", "level": 1}, 1, 0),
                block("paragraph", {"text": "Missing", "links": [{"target_page": 3}]}, 1, 1),
            ])


if __name__ == "__main__":
    unittest.main()
