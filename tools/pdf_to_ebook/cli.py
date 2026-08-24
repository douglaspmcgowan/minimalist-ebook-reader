from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .extract import extract_pdf
from .model import stable_json_bytes
from .package import build_reader_package
from .semantics import classify_records
from .validate import validate_release


def convert(
    source: Path,
    output: Path,
    report_path: Path | None = None,
    non_text_objects: list[dict] | None = None,
    asset_root: Path | None = None,
    expected_source_tokens: list[str] | None = None,
) -> int:
    if report_path is not None and output.resolve() == report_path.resolve():
        raise ValueError("Output and report paths must be different.")
    preflight, records = extract_pdf(source)
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
        asset_root=asset_root,
        expected_source_tokens=expected_source_tokens or (),
    )
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_bytes(stable_json_bytes(report.to_dict()))
    if not report.releasable:
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(stable_json_bytes(package))
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
