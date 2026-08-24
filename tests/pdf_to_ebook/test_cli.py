import json
import hashlib
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

    def test_failed_empty_conversion_preserves_existing_reader_package(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp, "book.json")
            output.write_text('{"title":"existing"}\n', encoding="utf-8")
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, [])), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=[]
            ):
                self.assertEqual(convert(Path(temp, "empty.pdf"), output), 2)
            self.assertEqual(output.read_text(encoding="utf-8"), '{"title":"existing"}\n')

    def test_report_alias_is_rejected_without_overwriting_existing_package(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "book.json"
            output.write_text('{"title":"existing"}\n', encoding="utf-8")
            report_alias = root / "." / "book.json"
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, [])), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=[]
            ):
                with self.assertRaisesRegex(ValueError, "different"):
                    convert(root / "empty.pdf", output, report_alias)
            self.assertEqual(output.read_text(encoding="utf-8"), '{"title":"existing"}\n')

    def test_convert_applies_optional_release_gate_inputs(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        blocks = [
            semantic_block("paragraph", {"text": "Synthetic prose."}, 1, 0),
            semantic_block(
                "figure",
                {"asset": "assets/chart.png", "alt": "Chart", "sha256": hashlib.sha256(b"chart").hexdigest(), "object_id": "chart-1"},
                1,
                1,
            ),
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "assets").mkdir()
            (root / "assets" / "chart.png").write_bytes(b"chart")
            output = root / "book.json"
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, [])), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ):
                status = convert(
                    root / "source.pdf",
                    output,
                    non_text_objects=[{"id": "chart-1", "page": 1}],
                    asset_root=root,
                    expected_source_tokens=["Synthetic", "Chart"],
                )
            self.assertEqual(status, 0)
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
