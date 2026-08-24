import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.pdf_to_ebook.cli import convert
from tools.pdf_to_ebook.model import Provenance, SemanticBlock


def semantic_block(kind, data, page, order):
    return SemanticBlock(
        kind=kind,
        data=data,
        provenance=[Provenance(page=page, bbox=(10, 20, 300, 40), reading_order=order)],
        confidence=0.98,
        evidence=["synthetic-test"],
    )


class ConvertPackageTests(unittest.TestCase):
    def test_convert_writes_reader_package_with_resolvable_contents_targets(self):
        preflight = {
            "source": {"sha256": "synthetic", "page_count": 2, "metadata": {"Title": "Reader package", "Author": "Test Author"}},
            "pages": [{"page": 1}, {"page": 2}],
        }
        blocks = [
            semantic_block("heading", {"text": "Contents", "level": 1}, 1, 0),
            semantic_block("contents", {"entries": [{"title": "Opening", "target_page": 2}]}, 1, 1),
            semantic_block("heading", {"text": "Opening", "level": 1}, 2, 0),
            semantic_block("paragraph", {"text": "A reader can open this chapter."}, 2, 1),
        ]
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp, "book.json")
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, [])), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ):
                self.assertEqual(convert(Path(temp, "source.pdf"), output), 0)
            package = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(package["reader"]["schema_version"], 1)
        self.assertEqual(package["title"], "Reader package")
        self.assertEqual(package["author"], "Test Author")
        self.assertEqual([entry["page"] for entry in package["sourceCoverage"]], [1, 2])
        self.assertEqual([chapter["target"] for chapter in package["chapters"]], ["section-1", "section-2"])
        self.assertTrue(all(chapter["blocks"] for chapter in package["chapters"]))
        contents = package["chapters"][0]["blocks"][1]
        self.assertEqual(contents["data"]["entries"][0]["target"], "section-2")
        self.assertTrue(all(block["provenance"] for chapter in package["chapters"] for block in chapter["blocks"]))


if __name__ == "__main__":
    unittest.main()
