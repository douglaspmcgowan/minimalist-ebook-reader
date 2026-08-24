import json
import hashlib
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject
from reportlab.pdfgen import canvas

from tools.pdf_to_ebook.cli import _load_book_profile, convert
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
        contents = package["chapters"][0]["blocks"][0]
        self.assertEqual(contents["data"]["entries"][0]["target"], "section-2")
        self.assertEqual(package["chapters"][0]["blocks"][1]["data"]["links"][0]["target"], "section-2")
        self.assertEqual(package["chapters"][0]["titleProvenance"][0]["page"], 1)
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
            self.assertRegex(
                package["chapters"][0]["blocks"][0]["data"]["asset"],
                r"^assets/generations/[0-9a-f]{64}/page-0001-figure-01\.png$",
            )

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

    def test_successful_figureless_conversion_replaces_prior_managed_assets(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        blocks = [semantic_block("paragraph", {"text": "A figureless replacement."}, 1, 0)]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "book.json"
            stale_asset = root / "assets" / "stale.png"
            stale_asset.parent.mkdir()
            stale_asset.write_bytes(b"stale")

            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, [])), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ):
                status = convert(root / "source.pdf", output, asset_root=root)

            self.assertEqual(status, 0)
            self.assertFalse(stale_asset.exists())
            self.assertFalse((root / "assets").exists() and any((root / "assets").iterdir()))

    def test_figureless_release_does_not_publish_unreferenced_staged_private_assets(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        blocks = [semantic_block("paragraph", {"text": "No released figure."}, 1, 0)]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def stage_unreferenced_asset(_source, asset_output_dir=None):
                asset = Path(asset_output_dir, "assets", "private-source-crop.png")
                asset.parent.mkdir()
                asset.write_bytes(b"private")
                return preflight, []

            with patch("tools.pdf_to_ebook.cli.extract_pdf", side_effect=stage_unreferenced_asset), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ):
                self.assertEqual(convert(root / "source.pdf", root / "book.json", asset_root=root), 0)

            self.assertFalse((root / "assets").exists() and any((root / "assets").iterdir()))

    def test_package_uses_content_addressed_generation_assets(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        content = b"chart"
        blocks = [semantic_block(
            "figure",
            {"asset": "assets/chart.png", "alt": "Chart", "sha256": hashlib.sha256(content).hexdigest()},
            1,
            0,
        )]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def materialize(_source, asset_output_dir=None):
                asset = Path(asset_output_dir, "assets", "chart.png")
                asset.parent.mkdir()
                asset.write_bytes(content)
                return preflight, []

            with patch("tools.pdf_to_ebook.cli.extract_pdf", side_effect=materialize), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ):
                self.assertEqual(convert(root / "source.pdf", root / "book.json", asset_root=root), 0)

            package = json.loads((root / "book.json").read_text(encoding="utf-8"))
            figure = next(block for block in package["blocks"] if block["kind"] == "figure")
            asset_path = figure["data"]["asset"]
            self.assertRegex(asset_path, r"^assets/generations/[0-9a-f]{64}/chart\.png$")
            self.assertEqual((root / asset_path).read_bytes(), content)
            self.assertEqual(package["chapters"][0]["blocks"][0]["data"]["asset"], asset_path)

    def test_package_swap_failure_keeps_old_package_assets_and_success_report_consistent(self):
        preflight = {"source": {"sha256": "new", "page_count": 1, "metadata": {}}}
        new_content = b"new"
        blocks = [semantic_block(
            "figure",
            {"asset": "assets/figure.bin", "alt": "New", "sha256": hashlib.sha256(new_content).hexdigest()},
            1,
            0,
        )]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "book.json"
            report_path = root / "report.json"
            old_asset = root / "assets" / "generations" / ("a" * 64) / "old.bin"
            old_asset.parent.mkdir(parents=True)
            old_asset.write_bytes(b"old")
            old_package = {"blocks": [{"kind": "figure", "data": {"asset": old_asset.relative_to(root).as_posix()}}]}
            output.write_bytes(json.dumps(old_package).encode("utf-8"))
            report_path.write_text(json.dumps({"releasable": True, "publication": {"package_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}}), encoding="utf-8")

            def materialize(_source, asset_output_dir=None):
                asset = Path(asset_output_dir, "assets", "figure.bin")
                asset.parent.mkdir()
                asset.write_bytes(new_content)
                return preflight, []

            real_replace = os.replace

            def fail_package_swap(source_path, destination_path):
                if Path(destination_path) == output:
                    raise OSError("synthetic package swap failure")
                return real_replace(source_path, destination_path)

            with patch("tools.pdf_to_ebook.cli.extract_pdf", side_effect=materialize), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ), patch("tools.pdf_to_ebook.cli.os.replace", side_effect=fail_package_swap):
                with self.assertRaisesRegex(OSError, "synthetic package"):
                    convert(root / "source.pdf", output, report_path=report_path, asset_root=root)

            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), old_package)
            self.assertEqual(old_asset.read_bytes(), b"old")
            self.assertFalse(report_path.exists())

    def test_success_report_is_written_after_matching_package_commit(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        blocks = [semantic_block("paragraph", {"text": "Published."}, 1, 0)]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "book.json"
            report_path = root / "report.json"
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, [])), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ):
                self.assertEqual(convert(root / "source.pdf", output, report_path=report_path, asset_root=root), 0)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["releasable"])
            self.assertEqual(report["publication"]["package_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())

    def test_completed_conversion_preserves_shared_guarded_staging_parent_for_sibling_outputs(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 1, "metadata": {}}}
        blocks = [semantic_block("paragraph", {"text": "Published."}, 1, 0)]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, [])), patch(
                "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
            ):
                self.assertEqual(convert(root / "source.pdf", root / "book.json"), 0)
            staging_parent = root / ".pdf-to-ebook-staging"
            self.assertTrue(staging_parent.is_dir())
            self.assertEqual(list(staging_parent.iterdir()), [])

    def test_book_profile_applies_record_overrides_and_release_decisions(self):
        preflight = {"source": {"sha256": "synthetic", "page_count": 2, "metadata": {}}}
        record = ExtractionRecord(page=1, bbox=(10, 20, 300, 40), reading_order=0, text="Chapter", role_hint="paragraph")
        profile = {
            "schema_version": 1,
            "record_overrides": [{"page": 1, "reading_order": 0, "set": {"role_hint": "heading", "metadata": {"level": 1}}}],
            "review_items": [],
            "intentionally_excluded_pages": [2],
            "non_text_objects": [],
            "expected_source_tokens": ["Chapter"],
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(preflight, [record])):
                self.assertEqual(convert(root / "source.pdf", root / "book.json", book_profile=profile), 0)
            package = json.loads((root / "book.json").read_text(encoding="utf-8"))

        self.assertEqual(package["chapters"][0]["title"], "Chapter")
        self.assertEqual(package["chapters"][0]["titleProvenance"][0]["page"], 1)

    def test_book_profile_schema_rejects_unsafe_or_ambiguous_values(self):
        invalid_profiles = [
            [],
            {"schema_version": 2},
            {"schema_version": 1, "unknown": []},
            {"schema_version": 1, "intentionally_excluded_pages": [True]},
            {"schema_version": 1, "review_items": [{"code": "x", "severity": "high", "approved": True}]},
            {"schema_version": 1, "record_overrides": [{"page": 1, "reading_order": 0, "set": {"asset": "private.bin"}}]},
            {"schema_version": 1, "record_overrides": [{"page": 1, "reading_order": 0, "set": {"metadata": {"review": []}}}]},
            {"schema_version": 1, "record_overrides": [{"page": 1, "reading_order": 0, "set": {"text": None}}]},
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp, "profile.json")
            for value in invalid_profiles:
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        _load_book_profile(path)

    def test_two_processes_cannot_publish_a_package_with_another_conversions_assets(self):
        worker_source = r'''
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

from tools.pdf_to_ebook.cli import convert
from tools.pdf_to_ebook.model import Provenance, SemanticBlock

root = Path(sys.argv[1])
label = sys.argv[2]
signal = Path(sys.argv[3])
asset_bytes = label.encode("utf-8")
preflight = {"source": {"sha256": label, "page_count": 1, "metadata": {"Title": label}}}
blocks = [SemanticBlock(
    kind="figure",
    data={"asset": "assets/figure.bin", "alt": label, "sha256": hashlib.sha256(asset_bytes).hexdigest()},
    provenance=[Provenance(page=1, bbox=(10, 20, 30, 40), reading_order=0)],
    confidence=0.98,
    evidence=["two-process-test"],
)]

def extract(_source, asset_output_dir=None):
    asset = Path(asset_output_dir, "assets", "figure.bin")
    asset.parent.mkdir()
    asset.write_bytes(asset_bytes)
    return preflight, []

real_replace = os.replace
def replace_with_first_writer_pause(source, destination):
    result = real_replace(source, destination)
    if label == "first" and Path(destination).parent == root / "assets" / "generations":
        signal.write_text("promoted", encoding="utf-8")
        time.sleep(1.5)
    return result

with patch("tools.pdf_to_ebook.cli.extract_pdf", side_effect=extract), patch(
    "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
), patch("tools.pdf_to_ebook.cli.os.replace", side_effect=replace_with_first_writer_pause):
    status = convert(root / f"{label}.pdf", root / "book.json", asset_root=root)
print(json.dumps({"label": label, "status": status}))
'''
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            worker = root / "worker.py"
            worker.write_text(worker_source, encoding="utf-8")
            signal = root / "first-assets-promoted"
            repository = Path(__file__).resolve().parents[2]
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(repository)
            first = subprocess.Popen(
                [sys.executable, str(worker), str(root), "first", str(signal)],
                cwd=repository,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.addCleanup(self._terminate_process, first)
            deadline = time.monotonic() + 10
            while not signal.exists() and first.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(signal.exists(), "first conversion never reached asset promotion")
            second = subprocess.Popen(
                [sys.executable, str(worker), str(root), "second", str(signal)],
                cwd=repository,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.addCleanup(self._terminate_process, second)
            first_stdout, first_stderr = first.communicate(timeout=15)
            second_stdout, second_stderr = second.communicate(timeout=15)
            self.assertEqual(first.returncode, 0, first_stderr)
            self.assertEqual(second.returncode, 0, second_stderr)
            self.assertEqual(json.loads(first_stdout)["status"], 0)
            self.assertEqual(json.loads(second_stdout)["status"], 0)

            package = json.loads((root / "book.json").read_text(encoding="utf-8"))
            figure = next(block for block in package["blocks"] if block["kind"] == "figure")
            live_asset = root / figure["data"]["asset"]
            self.assertEqual(hashlib.sha256(live_asset.read_bytes()).hexdigest(), figure["data"]["sha256"])

    def test_process_termination_after_figureless_package_swap_is_guarded_and_recovered(self):
        worker_source = r'''
import sys
import time
from pathlib import Path
from unittest.mock import patch

from tools.pdf_to_ebook.cli import _cleanup_managed_assets, convert
from tools.pdf_to_ebook.model import Provenance, SemanticBlock

root = Path(sys.argv[1])
signal = Path(sys.argv[2])
preflight = {"source": {"sha256": "new", "page_count": 1, "metadata": {}}}
blocks = [SemanticBlock(
    kind="paragraph",
    data={"text": "Figureless replacement."},
    provenance=[Provenance(page=1, bbox=(10, 20, 30, 40), reading_order=0)],
    confidence=0.98,
    evidence=["termination-test"],
)]

def extract(_source, asset_output_dir=None):
    return preflight, []

cleanup_calls = 0
def pause_cleanup(asset_root, generation):
    global cleanup_calls
    cleanup_calls += 1
    if cleanup_calls == 1:
        return _cleanup_managed_assets(asset_root, generation)
    signal.write_text("package-swapped", encoding="utf-8")
    time.sleep(30)

with patch("tools.pdf_to_ebook.cli.extract_pdf", side_effect=extract), patch(
    "tools.pdf_to_ebook.cli.classify_records", return_value=blocks
), patch("tools.pdf_to_ebook.cli._cleanup_managed_assets", side_effect=pause_cleanup):
    convert(root / "source.pdf", root / "book.json", report_path=root / "report.json", asset_root=root)
'''
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old_generation = "a" * 64
            old_asset = root / "assets" / "generations" / old_generation / "old.bin"
            old_asset.parent.mkdir(parents=True)
            old_asset.write_bytes(b"old-private")
            (root / "book.json").write_text(json.dumps({
                "schema_version": 1,
                "blocks": [{"kind": "figure", "data": {"asset": f"assets/generations/{old_generation}/old.bin"}}],
            }), encoding="utf-8")
            worker = root / "termination-worker.py"
            worker.write_text(worker_source, encoding="utf-8")
            signal = root / "package-swapped"
            repository = Path(__file__).resolve().parents[2]
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(repository)
            process = subprocess.Popen(
                [sys.executable, str(worker), str(root), str(signal)],
                cwd=repository,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.addCleanup(self._terminate_process, process)
            deadline = time.monotonic() + 10
            while not signal.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(signal.exists(), "worker never reached post-swap cleanup")
            process.kill()
            _, stderr = process.communicate(timeout=10)
            self.assertNotEqual(process.returncode, 0, stderr.decode("utf-8", errors="replace"))

            package = json.loads((root / "book.json").read_text(encoding="utf-8"))
            self.assertFalse(any(block["kind"] == "figure" for block in package["blocks"]))
            self.assertEqual(old_asset.read_bytes(), b"old-private")
            self.assertFalse((root / "report.json").exists())
            guards = [
                (repository / ".gitignore").read_text(encoding="utf-8"),
                (repository / ".vercelignore").read_text(encoding="utf-8"),
            ]
            self.assertTrue(all("**/.pdf-to-ebook-staging/" in guard for guard in guards))

            recovery_blocks = [semantic_block("paragraph", {"text": "Recovered."}, 1, 0)]
            with patch("tools.pdf_to_ebook.cli.extract_pdf", return_value=(
                {"source": {"sha256": "recovered", "page_count": 1, "metadata": {}}}, []
            )), patch("tools.pdf_to_ebook.cli.classify_records", return_value=recovery_blocks):
                self.assertEqual(convert(root / "source.pdf", root / "book.json", report_path=root / "report.json", asset_root=root), 0)
            self.assertFalse(old_asset.exists())
            self.assertFalse((root / "assets").exists() and any((root / "assets").iterdir()))

    @staticmethod
    def _terminate_process(process: subprocess.Popen) -> None:
        if process.poll() is None:
            process.kill()
            process.communicate()

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
