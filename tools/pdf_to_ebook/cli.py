from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .extract import extract_pdf
from .model import stable_json_bytes
from .package import build_reader_package
from .semantics import classify_records
from .validate import validate_release


def convert(source: Path, output: Path, report_path: Path | None = None) -> int:
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
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(stable_json_bytes(package))
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_bytes(stable_json_bytes(report.to_dict()))
    return 0 if report.releasable else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a PDF to provenance-bearing semantic ebook JSON.")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        return convert(args.source, args.output, args.report)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 1


if __name__ == "__main__":
    sys.exit(main())
