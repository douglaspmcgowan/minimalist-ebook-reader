from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import sys
import tempfile
import time
from contextlib import ExitStack, contextmanager, nullcontext
from pathlib import Path

from .extract import extract_pdf
from .model import stable_json_bytes
from .package import build_reader_package
from .semantics import classify_records
from .validate import validate_release


@contextmanager
def _file_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as error:
                    if error.errno not in {errno.EACCES, errno.EDEADLK}:
                        raise
                    time.sleep(0.05)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _conversion_locks(output: Path, asset_root: Path | None):
    resources = {os.path.normcase(str(output.resolve()))}
    if asset_root is not None:
        resources.add(os.path.normcase(str(asset_root.resolve())))
    lock_root = Path(tempfile.gettempdir()) / "pdf-to-ebook-locks"
    lock_paths = [
        lock_root / f"{hashlib.sha256(resource.encode('utf-8')).hexdigest()}.lock"
        for resource in sorted(resources)
    ]
    with ExitStack() as stack:
        for lock_path in lock_paths:
            stack.enter_context(_file_lock(lock_path))
        yield


def _validate_output_paths(source: Path, output: Path, report_path: Path | None, asset_root: Path | None) -> None:
    resolved_source = source.resolve()
    resolved_output = output.resolve()
    resolved_report = report_path.resolve() if report_path is not None else None
    if resolved_output == resolved_source:
        raise ValueError("Output path must be different from the source path.")
    if resolved_report == resolved_source:
        raise ValueError("Report path must be different from the source path.")
    if resolved_report == resolved_output:
        raise ValueError("Output and report paths must be different.")
    if asset_root is None:
        return
    resolved_root = asset_root.resolve()
    if resolved_root == Path(resolved_root.anchor):
        raise ValueError("The asset root must not be a filesystem root.")
    if resolved_root.exists() and not resolved_root.is_dir():
        raise ValueError("The asset root must be a directory.")
    if resolved_root in {resolved_source, resolved_output, resolved_report}:
        raise ValueError("The asset root must not alias the source, output, or report path.")
    managed_assets = (resolved_root / "assets").resolve()
    for name, path in (("source", resolved_source), ("output", resolved_output), ("report", resolved_report)):
        if path is None:
            continue
        try:
            path.relative_to(managed_assets)
        except ValueError:
            continue
        raise ValueError(f"The {name} path must stay outside the managed asset directory.")


def _commit_release(output: Path, package_bytes: bytes, staging_root: Path | None, asset_root: Path | None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output: Path | None = None
    staged_assets = staging_root / "assets" if staging_root is not None else None
    live_assets = asset_root / "assets" if asset_root is not None else None
    previous_assets = staging_root / "previous-assets" if staging_root is not None else None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False) as handle:
            handle.write(package_bytes)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_output = Path(handle.name)
        if staged_assets is not None and live_assets is not None and previous_assets is not None:
            staged_assets.mkdir(parents=True, exist_ok=True)
            if live_assets.exists():
                os.replace(live_assets, previous_assets)
            os.replace(staged_assets, live_assets)
        os.replace(temporary_output, output)
        temporary_output = None
    except OSError:
        if staged_assets is not None and live_assets is not None and previous_assets is not None:
            if live_assets.exists() and not staged_assets.exists():
                os.replace(live_assets, staged_assets)
            if previous_assets.exists():
                os.replace(previous_assets, live_assets)
        raise
    finally:
        if temporary_output is not None:
            temporary_output.unlink(missing_ok=True)


def convert(
    source: Path,
    output: Path,
    report_path: Path | None = None,
    non_text_objects: list[dict] | None = None,
    asset_root: Path | None = None,
    expected_source_tokens: list[str] | None = None,
) -> int:
    _validate_output_paths(source, output, report_path, asset_root)
    resolved_asset_root = asset_root.resolve() if asset_root is not None else None
    with _conversion_locks(output, resolved_asset_root):
        if resolved_asset_root is not None:
            resolved_asset_root.mkdir(parents=True, exist_ok=True)
        staging_context = (
            tempfile.TemporaryDirectory(prefix=".pdf-to-ebook-", dir=resolved_asset_root)
            if resolved_asset_root is not None
            else nullcontext(None)
        )
        with staging_context as staging:
            staging_root = Path(staging) if staging is not None else None
            preflight, records = extract_pdf(source, asset_output_dir=staging_root)
            blocks = classify_records(records)
            page_count = int(preflight["source"]["page_count"])
            package = build_reader_package(
                blocks,
                page_count,
                preflight["source"],
                {key: value for key, value in preflight.items() if key not in {"source"}},
                source.stem,
            )
            page_targets = {
                page: chapter["target"]
                for chapter in package["chapters"]
                for page in range(chapter["sourcePages"]["start"], chapter["sourcePages"]["end"] + 1)
            }
            report = validate_release(
                blocks,
                page_count,
                reader_targets={chapter["target"] for chapter in package["chapters"]},
                page_targets=page_targets,
                non_text_objects=non_text_objects or (),
                asset_root=staging_root,
                expected_source_tokens=expected_source_tokens or (),
                extraction_records=records,
            )
            if report_path:
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_bytes(stable_json_bytes(report.to_dict()))
            if not report.releasable:
                return 2
            _commit_release(output, stable_json_bytes(package), staging_root, resolved_asset_root)
            return 0


def _json_list(path: Path, option: str) -> list:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"{option} must contain a JSON array.")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a PDF to provenance-bearing semantic ebook JSON.")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--non-text-objects", type=Path, metavar="JSON")
    parser.add_argument("--asset-root", type=Path)
    parser.add_argument("--expected-source-tokens", type=Path, metavar="JSON")
    args = parser.parse_args(argv)
    try:
        return convert(
            args.source,
            args.output,
            args.report,
            _json_list(args.non_text_objects, "--non-text-objects") if args.non_text_objects else None,
            args.asset_root,
            _json_list(args.expected_source_tokens, "--expected-source-tokens") if args.expected_source_tokens else None,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 1


if __name__ == "__main__":
    sys.exit(main())
