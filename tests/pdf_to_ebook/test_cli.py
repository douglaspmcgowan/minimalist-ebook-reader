import json
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
from reportlab.pdfgen import canvas

from tools.pdf_to_ebook.cli import convert
from tools.pdf_to_ebook.model import ExtractionRecord, Provenance, SemanticBlock


def semantic_block(kind, data, page, order):
    return SemanticBlock(
        kind=kind,
        data=data,
        provenance=[Provenance(page=page, bbox=(10, 20, 300, 40), reading_order=order)],
        confidence=0.98,
        evidence=["synthetic-test"],
    )


class ConvertPackageTests(unittest.TestCase):
    def _figure_pdf(self, directory: Path, alt: str | None = "A blue rectangle") -> Path:
        image = directory / "figure-source.png"
        Image.new("RGB", (40, 30), color=(20, 80, 140)).save(image)
        raw = directory / "raw-source.pdf"
        pdf = canvas.Canvas(str(raw), pagesize=(612, 792))
        pdf.drawImage(str(image), 72, 430, width=40, height=30)
        pdf.save()
        reader = PdfReader(raw)
        writer = PdfWriter()
        writer.clone_document_from_reader(reader)
        xobjects = writer.pages[0]["/Resources"]["/XObject"].get_object()
        image_object = next(value.get_object() for value in xobjects.values() if value.get_object().get("/Subtype") == "/Image")
        if alt is not None:
            image_object[NameObject("/Alt")] = TextStringObject(alt)
        source = directory / "source.pdf"
        with source.open("wb") as handle:
            writer.write(handle)
        return source

    def test_convert_writes_reader_package_with_resolvable_contents_targets(self):
        preflight = {
            "source": {"sha256": "synthetic", "page_count": 2, "metadata": {"Title": "Reader package", "Author": "Test Author"}},
            "pages": [{"page": 1}, {"page": 2}],
        }
        blocks = [
            semantic_block("heading", {"text": "Contents", "level": 1}, 1, 0),
            semantic_block("contents", {"entries": [{"title": "Opening", "target_page": 2}]}, 1, 1),
            semantic_block("paragraph", {"text": "See opening", "links": [{"target_page": 2}]}, 1, 2),
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
        self.assertEqual(package["chapters"][0]["blocks"][2]["data"]["links"][0]["target"], "section-2")
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
            output = root / "book.json"

            def materialize_asset(_source, asset_output_dir=None):
                asset = Path(asset_output_dir, "assets", "chart.png")
                asset.parent.mkdir()
                asset.write_bytes(b"chart")
                return preflight, []

            with patch("tools.pdf_to_ebook.cli.extract_pdf", side_effect=materialize_asset), patch(
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

    def test_convert_blocks_and_reports_every_extraction_review_finding(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        records = [
            ExtractionRecord(
                page=1,
                bbox=(10, 20, 300, 40),
                reading_order=0,
                text="Synthetic prose.",
                metadata={"review": [
                    {"code": "uncertain-reading-order", "severity": "high", "message": "Order requires review."},
                    {"code": "missing-figure-materialization", "severity": "high", "message": "Figure requires review."},
                ]},
            ),
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "book.json"
            report_path = root / "report.json"
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, records)):
                status = convert(root / "source.pdf", output, report_path)
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(status, 2)
        self.assertFalse(output.exists())
        self.assertEqual(report["unresolved_high_severity"], 2)
        self.assertEqual([item["code"] for item in report["items"]], ["uncertain-reading-order", "missing-figure-materialization"])

    def test_real_pdf_conversion_materializes_hashes_and_packages_figure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._figure_pdf(root)
            output = root / "book.json"

            status = convert(source, output, asset_root=root)

            package = json.loads(output.read_text(encoding="utf-8"))
            figure = next(block for block in package["blocks"] if block["kind"] == "figure")
            asset = root / figure["data"]["asset"]
            self.assertEqual(status, 0)
            self.assertTrue(asset.is_file())
            self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(), figure["data"]["sha256"])
            self.assertEqual(package["chapters"][0]["blocks"][0]["data"]["asset"], "assets/page-0001-figure-01.png")

    def test_failed_conversion_preserves_existing_package_and_figure_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._figure_pdf(root, alt=None)
            output = root / "book.json"
            output.write_text('{"title":"existing"}\n', encoding="utf-8")
            existing_asset = root / "assets" / "page-0001-figure-01.png"
            existing_asset.parent.mkdir()
            existing_asset.write_bytes(b"existing-figure")

            status = convert(source, output, asset_root=root)

            self.assertEqual(status, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), '{"title":"existing"}\n')
            self.assertEqual(existing_asset.read_bytes(), b"existing-figure")

    def test_package_promotion_failure_rolls_back_existing_figure_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._figure_pdf(root)
            output = root / "book.json"
            output.write_text('{"title":"existing"}\n', encoding="utf-8")
            existing_asset = root / "assets" / "page-0001-figure-01.png"
            existing_asset.parent.mkdir()
            existing_asset.write_bytes(b"existing-figure")
            real_replace = os.replace

            def fail_package_replace(source_path, destination_path):
                if Path(destination_path) == output:
                    raise OSError("synthetic package promotion failure")
                return real_replace(source_path, destination_path)

            with patch("tools.pdf_to_ebook.cli.os.replace", side_effect=fail_package_replace):
                with self.assertRaisesRegex(OSError, "synthetic package"):
                    convert(source, output, asset_root=root)

            self.assertEqual(output.read_text(encoding="utf-8"), '{"title":"existing"}\n')
            self.assertEqual(existing_asset.read_bytes(), b"existing-figure")

    def test_convert_blocks_missing_or_mismatched_materialized_figure(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        blocks = [semantic_block("figure", {"asset": "assets/chart.png", "alt": "Chart", "sha256": "0" * 64}, 1, 0)]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "book.json"

            def materialize_mismatch(_source, asset_output_dir=None):
                asset = Path(asset_output_dir, "assets", "chart.png")
                asset.parent.mkdir()
                asset.write_bytes(b"chart")
                return preflight, []

            with patch("tools.pdf_to_ebook.cli.extract_pdf", side_effect=materialize_mismatch), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ):
                mismatch = convert(root / "source.pdf", output, asset_root=root)
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, [])), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ):
                missing = convert(root / "source.pdf", output, asset_root=root)

        self.assertEqual((mismatch, missing), (2, 2))
        self.assertFalse(output.exists())

    def test_rejects_source_output_and_managed_asset_aliases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)
            with source.open("wb") as handle:
                writer.write(handle)
            with self.assertRaisesRegex(ValueError, "source"):
                convert(source, source)
            with self.assertRaisesRegex(ValueError, "asset root"):
                convert(source, root / "book.json", asset_root=root / "book.json")
            asset_file = root / "asset-file"
            asset_file.write_bytes(b"unsafe")
            with self.assertRaisesRegex(ValueError, "directory"):
                convert(source, root / "book.json", asset_root=asset_file)
            with self.assertRaisesRegex(ValueError, "filesystem root"):
                convert(source, root / "book.json", asset_root=Path(source.anchor))
            with self.assertRaisesRegex(ValueError, "managed asset"):
                convert(source, root / "assets" / "book.json", asset_root=root)


if __name__ == "__main__":
    unittest.main()
