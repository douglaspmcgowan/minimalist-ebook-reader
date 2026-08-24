from __future__ import annotations

import argparse
import errno
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import replace
from pathlib import Path
from typing import Any

from .extract import extract_pdf
from .model import ExtractionRecord, ReviewItem, stable_json_bytes
from .package import build_reader_package
from .semantics import classify_records
from .validate import extraction_finding_id, validate_release


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
def _conversion_locks(output: Path, asset_root: Path | None, report_path: Path | None = None):
    resources = {os.path.normcase(str(output.resolve()))}
    if asset_root is not None:
        resources.add(os.path.normcase(str(asset_root.resolve())))
    if report_path is not None:
        resources.add(os.path.normcase(str(report_path.resolve())))
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


def _referenced_asset_paths(value: object) -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"asset", "src"} and isinstance(item, str) and item.startswith("assets/"):
                paths.add(re.split(r"[?#]", item, maxsplit=1)[0].removeprefix("assets/"))
            else:
                paths.update(_referenced_asset_paths(item))
    elif isinstance(value, list):
        for item in value:
            paths.update(_referenced_asset_paths(item))
    return paths


def _asset_generation(staging_root: Path | None, package: object) -> tuple[str | None, Path | None]:
    staged_assets = staging_root / "assets" if staging_root is not None else None
    referenced = sorted(_referenced_asset_paths(package))
    if not referenced:
        return None, None
    if staged_assets is None:
        raise ValueError("Reader package assets require an explicit staged asset root.")
    publication_assets = staging_root / "publication-assets"
    files: list[Path] = []
    for relative in referenced:
        source = (staged_assets / Path(relative)).resolve()
        try:
            source.relative_to(staged_assets.resolve())
        except ValueError:
            raise ValueError(f"Reader package asset {relative!r} escapes the staged asset root.") from None
        if not source.is_file():
            raise ValueError(f"Reader package asset {relative!r} is absent from the staged release.")
        destination = publication_assets / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        files.append(destination)
    inventory = [
        {"path": path.relative_to(publication_assets).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in files
    ]
    return hashlib.sha256(stable_json_bytes(inventory)).hexdigest(), publication_assets


def _rewrite_generation_assets(value: Any, generation: str | None) -> Any:
    if isinstance(value, dict):
        rewritten = {key: _rewrite_generation_assets(item, generation) for key, item in value.items()}
        if generation is not None:
            for key in ("asset", "src"):
                asset = rewritten.get(key)
                if isinstance(asset, str) and asset.startswith("assets/") and not asset.startswith("assets/generations/"):
                    rewritten[key] = f"assets/generations/{generation}/{asset.removeprefix('assets/')}"
        return rewritten
    if isinstance(value, list):
        return [_rewrite_generation_assets(item, generation) for item in value]
    return value


def _same_tree(left: Path, right: Path) -> bool:
    def inventory(root: Path) -> dict[str, str]:
        return {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*")
            if path.is_file()
        }

    return inventory(left) == inventory(right)


def _cleanup_managed_assets(asset_root: Path, current_generation: str | None) -> None:
    assets = asset_root / "assets"
    if not assets.exists():
        return
    generations = assets / "generations"
    for child in list(assets.iterdir()):
        if child == generations:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    if generations.exists():
        for child in list(generations.iterdir()):
            if current_generation is not None and child.name == current_generation:
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        if current_generation is None and not any(generations.iterdir()):
            generations.rmdir()


def _output_staging_directory(path: Path) -> Path:
    identity = hashlib.sha256(os.path.normcase(str(path.resolve())).encode("utf-8")).hexdigest()
    return path.parent / ".pdf-to-ebook-staging" / identity


def _remove_staging_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _recover_staging(output: Path, report_path: Path | None, asset_root: Path | None) -> None:
    _remove_staging_directory(_output_staging_directory(output))
    if report_path is not None:
        _remove_staging_directory(_output_staging_directory(report_path))
    if asset_root is not None:
        staging = asset_root / "assets" / ".pdf-to-ebook-staging"
        if staging.exists():
            shutil.rmtree(staging)


def _published_asset_generation(package: object) -> tuple[bool, str | None]:
    paths: list[str] = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"asset", "src"} and isinstance(item, str) and item.startswith("assets/"):
                    paths.append(item)
                else:
                    collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    collect(package)
    if not paths:
        return True, None
    generations = {
        match.group(1)
        for path in paths
        for match in [re.match(r"^assets/generations/([0-9a-f]{64})/", path)]
        if match
    }
    if len(generations) != 1:
        return False, None
    generation = next(iter(generations))
    prefix = f"assets/generations/{generation}/"
    return all(path.startswith(prefix) for path in paths), generation


def _recover_publication(output: Path, asset_root: Path | None, report_path: Path | None) -> None:
    package_bytes: bytes | None = None
    package: object | None = None
    if output.is_file():
        try:
            package_bytes = output.read_bytes()
            package = json.loads(package_bytes)
        except (OSError, ValueError):
            package_bytes = None
    if asset_root is not None and isinstance(package, dict) and package.get("schema_version") == 1:
        recoverable, generation = _published_asset_generation(package) if package is not None else (True, None)
        if recoverable:
            _cleanup_managed_assets(asset_root, generation)
    if report_path is not None and report_path.is_file():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if report.get("releasable") is True:
            publication = report.get("publication")
            expected = publication.get("package_sha256") if isinstance(publication, dict) else None
            actual = hashlib.sha256(package_bytes).hexdigest() if package_bytes is not None else None
            if not isinstance(expected, str) or expected != actual:
                report_path.unlink(missing_ok=True)


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = _output_staging_directory(path)
    staging.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=staging, prefix="content-", suffix=".tmp", delete=False) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        _remove_staging_directory(staging)


def _commit_release(
    output: Path,
    package_bytes: bytes,
    staged_assets: Path | None,
    asset_root: Path | None,
    generation: str | None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output_staging = _output_staging_directory(output)
    output_staging.mkdir(parents=True, exist_ok=True)
    temporary_output: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=output_staging, prefix="package-", suffix=".tmp", delete=False) as handle:
            handle.write(package_bytes)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_output = Path(handle.name)
        if generation is not None and staged_assets is not None and asset_root is not None:
            live_generation = asset_root / "assets" / "generations" / generation
            live_generation.parent.mkdir(parents=True, exist_ok=True)
            if live_generation.exists():
                if not _same_tree(staged_assets, live_generation):
                    raise OSError(f"Managed asset generation {generation} has conflicting content.")
            else:
                os.replace(staged_assets, live_generation)
        os.replace(temporary_output, output)
        temporary_output = None
    finally:
        if temporary_output is not None:
            temporary_output.unlink(missing_ok=True)
        _remove_staging_directory(output_staging)


_PROFILE_KEYS = {
    "schema_version", "record_overrides", "review_items", "intentionally_excluded_pages",
    "non_text_objects", "expected_source_tokens",
}
_OVERRIDE_KEYS = {"role_hint", "text", "alt", "caption", "metadata"}
_OVERRIDE_METADATA_KEYS = {
    "attribution", "discretionary_hyphen", "level", "list_continuation", "semantic_exclusion",
    "table_continuation", "target",
}
_ROLE_HINTS = {
    "contents", "contents_subtitle", "divider", "figure", "form", "furniture", "heading", "index_entry",
    "list_continuation", "list_item", "non_text_object", "paragraph", "quotation", "table", "testimonial",
}


def _json_array(value: object, label: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array.")
    return value


def _positive_pages(value: object, label: str) -> list[int]:
    pages = _json_array(value, label)
    if any(not isinstance(page, int) or isinstance(page, bool) or page < 1 for page in pages):
        raise ValueError(f"{label} must contain positive integer page numbers.")
    if len(set(pages)) != len(pages):
        raise ValueError(f"{label} must not contain duplicate pages.")
    return pages


def _review_items(value: object, label: str) -> list[ReviewItem]:
    results: list[ReviewItem] = []
    allowed = {"code", "severity", "page", "message", "approved", "details"}
    for position, item in enumerate(_json_array(value, label), start=1):
        if isinstance(item, ReviewItem):
            item = item.to_dict()
        if not isinstance(item, dict) or set(item) - allowed:
            raise ValueError(f"{label} item {position} has an invalid schema.")
        code = item.get("code")
        severity = item.get("severity")
        page = item.get("page")
        message = item.get("message")
        details = item.get("details")
        if not isinstance(code, str) or not code.strip():
            raise ValueError(f"{label} item {position} needs a code.")
        if severity not in {"high", "medium", "low"}:
            raise ValueError(f"{label} item {position} has an invalid severity.")
        if page is not None and (not isinstance(page, int) or isinstance(page, bool) or page < 1):
            raise ValueError(f"{label} item {position} has an invalid page.")
        if not isinstance(message, str) or not message.strip() or item.get("approved") is not True or not isinstance(details, dict):
            raise ValueError(f"{label} item {position} must be an explicit approved finding with details.")
        finding_id = details.get("finding_id")
        scoped_disposition = code == "non-text-object-disposition" and (
            details.get("object_id") is not None or (page is not None and details.get("bbox") is not None)
        )
        if not scoped_disposition and (not isinstance(finding_id, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", finding_id)):
            raise ValueError(f"{label} item {position} needs a stable finding_id.")
        if isinstance(finding_id, str):
            bbox = details.get("bbox")
            reading_order = details.get("reading_order")
            valid_bbox = (
                isinstance(bbox, list)
                and len(bbox) == 4
                and all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in bbox)
            )
            if page is None or not valid_bbox or not isinstance(reading_order, int) or isinstance(reading_order, bool) or reading_order < 0:
                raise ValueError(f"{label} item {position} needs page, bbox, and reading_order scope.")
            for scope_key in ("object_id", "field_name"):
                if scope_key in details and (not isinstance(details[scope_key], str) or not details[scope_key].strip()):
                    raise ValueError(f"{label} item {position} has an invalid {scope_key} scope.")
            expected_finding_id = extraction_finding_id(
                code.strip(),
                page,
                reading_order,
                bbox,
                details.get("object_id"),
                details.get("field_name"),
            )
            if finding_id.lower() != expected_finding_id:
                raise ValueError(f"{label} item {position} finding_id does not match its scope.")
        results.append(ReviewItem(code.strip(), severity, page, message.strip(), True, details))
    return results


def _validate_record_overrides(value: object) -> list[dict[str, Any]]:
    overrides: list[dict[str, Any]] = []
    for position, item in enumerate(_json_array(value, "record_overrides"), start=1):
        if not isinstance(item, dict) or set(item) != {"page", "reading_order", "set"}:
            raise ValueError(f"record_overrides item {position} has an invalid schema.")
        page, order, changes = item["page"], item["reading_order"], item["set"]
        if not isinstance(page, int) or isinstance(page, bool) or page < 1:
            raise ValueError(f"record_overrides item {position} has an invalid page.")
        if not isinstance(order, int) or isinstance(order, bool) or order < 0:
            raise ValueError(f"record_overrides item {position} has an invalid reading_order.")
        if not isinstance(changes, dict) or not changes or set(changes) - _OVERRIDE_KEYS:
            raise ValueError(f"record_overrides item {position} has unsafe override fields.")
        if "role_hint" in changes and changes["role_hint"] not in _ROLE_HINTS:
            raise ValueError(f"record_overrides item {position} has an invalid role_hint.")
        if "text" in changes and not isinstance(changes["text"], str):
            raise ValueError(f"record_overrides item {position} field text must be text.")
        for key in ("alt", "caption"):
            if key in changes and changes[key] is not None and not isinstance(changes[key], str):
                raise ValueError(f"record_overrides item {position} field {key} must be text or null.")
        if "metadata" in changes:
            metadata = changes["metadata"]
            if not isinstance(metadata, dict) or set(metadata) - _OVERRIDE_METADATA_KEYS:
                raise ValueError(f"record_overrides item {position} has unsafe metadata fields.")
            if "level" in metadata and (
                not isinstance(metadata["level"], int) or isinstance(metadata["level"], bool) or not 1 <= metadata["level"] <= 6
            ):
                raise ValueError(f"record_overrides item {position} has an invalid heading level.")
            if "target" in metadata and (
                not isinstance(metadata["target"], str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]*", metadata["target"])
            ):
                raise ValueError(f"record_overrides item {position} has an invalid reader target.")
            for key in ("discretionary_hyphen", "list_continuation", "semantic_exclusion", "table_continuation"):
                if key in metadata and not isinstance(metadata[key], bool):
                    raise ValueError(f"record_overrides item {position} metadata {key} must be boolean.")
            if "attribution" in metadata and not isinstance(metadata["attribution"], str):
                raise ValueError(f"record_overrides item {position} attribution must be text.")
        overrides.append({"page": page, "reading_order": order, "set": changes})
    selectors = [(item["page"], item["reading_order"]) for item in overrides]
    if len(set(selectors)) != len(selectors):
        raise ValueError("record_overrides must not contain duplicate selectors.")
    return overrides


def _normalize_profile(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) - _PROFILE_KEYS or value.get("schema_version") != 1:
        raise ValueError("Book profile must be a schema_version 1 JSON object with supported fields only.")
    profile = {
        "schema_version": 1,
        "record_overrides": _validate_record_overrides(value.get("record_overrides", [])),
        "review_items": _review_items(value.get("review_items", []), "review_items"),
        "intentionally_excluded_pages": _positive_pages(value.get("intentionally_excluded_pages", []), "intentionally_excluded_pages"),
        "non_text_objects": _json_array(value.get("non_text_objects", []), "non_text_objects"),
        "expected_source_tokens": _json_array(value.get("expected_source_tokens", []), "expected_source_tokens"),
    }
    if any(not isinstance(item, dict) for item in profile["non_text_objects"]):
        raise ValueError("non_text_objects must contain JSON objects.")
    if any(not isinstance(token, str) or not token.strip() for token in profile["expected_source_tokens"]):
        raise ValueError("expected_source_tokens must contain non-empty strings.")
    return profile


def _load_book_profile(path: Path) -> dict[str, Any]:
    return _normalize_profile(json.loads(path.read_text(encoding="utf-8")))


def _apply_record_overrides(records: list[ExtractionRecord], overrides: list[dict[str, Any]]) -> list[ExtractionRecord]:
    updated = list(records)
    for override in overrides:
        matches = [
            index for index, record in enumerate(updated)
            if record.page == override["page"] and record.reading_order == override["reading_order"]
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Record override page {override['page']} reading_order {override['reading_order']} matched {len(matches)} records."
            )
        index = matches[0]
        changes = dict(override["set"])
        if "metadata" in changes:
            changes["metadata"] = {**updated[index].metadata, **changes["metadata"]}
        updated[index] = replace(updated[index], **changes)
    return updated


def convert(
    source: Path,
    output: Path,
    report_path: Path | None = None,
    non_text_objects: list[dict] | None = None,
    asset_root: Path | None = None,
    expected_source_tokens: list[str] | None = None,
    review_items: list[ReviewItem] | None = None,
    intentionally_excluded_pages: list[int] | None = None,
    book_profile: dict[str, Any] | None = None,
) -> int:
    _validate_output_paths(source, output, report_path, asset_root)
    resolved_asset_root = asset_root.resolve() if asset_root is not None else None
    profile = _normalize_profile(book_profile) if book_profile is not None else _normalize_profile({"schema_version": 1})
    combined_review_items = [*profile["review_items"], *(review_items or [])]
    combined_excluded_pages = [*profile["intentionally_excluded_pages"], *(intentionally_excluded_pages or [])]
    combined_non_text_objects = [*profile["non_text_objects"], *(non_text_objects or [])]
    combined_expected_tokens = [*profile["expected_source_tokens"], *(expected_source_tokens or [])]
    with _conversion_locks(output, resolved_asset_root, report_path):
        _recover_staging(output, report_path, resolved_asset_root)
        _recover_publication(output, resolved_asset_root, report_path)
        if resolved_asset_root is not None:
            resolved_asset_root.mkdir(parents=True, exist_ok=True)
            asset_staging = resolved_asset_root / "assets" / ".pdf-to-ebook-staging"
            asset_staging.mkdir(parents=True, exist_ok=True)
        else:
            asset_staging = None
        staging_context = (
            tempfile.TemporaryDirectory(prefix="conversion-", dir=asset_staging)
            if asset_staging is not None
            else nullcontext(None)
        )
        with staging_context as staging:
            staging_root = Path(staging) if staging is not None else None
            preflight, records = extract_pdf(source, asset_output_dir=staging_root)
            records = _apply_record_overrides(list(records), profile["record_overrides"])
            blocks = classify_records(records)
            page_count = int(preflight["source"]["page_count"])
            if any(page > page_count for page in combined_excluded_pages):
                raise ValueError("Intentionally excluded pages must stay within the source page count.")
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
                review_items=combined_review_items,
                intentionally_excluded_pages=combined_excluded_pages,
                non_text_objects=combined_non_text_objects,
                asset_root=staging_root,
                expected_source_tokens=combined_expected_tokens,
                extraction_records=records,
            )
            if not report.releasable:
                if report_path:
                    _atomic_write(report_path, stable_json_bytes(report.to_dict()))
                return 2
            generation, publication_assets = _asset_generation(staging_root, package)
            package = _rewrite_generation_assets(package, generation)
            package_bytes = stable_json_bytes(package)
            if report_path:
                report_path.unlink(missing_ok=True)
            _commit_release(output, package_bytes, publication_assets, resolved_asset_root, generation)
            if resolved_asset_root is not None:
                _cleanup_managed_assets(resolved_asset_root, generation)
            if report_path:
                report_value = report.to_dict()
                report_value["publication"] = {
                    "asset_generation": generation,
                    "package_sha256": hashlib.sha256(package_bytes).hexdigest(),
                }
                _atomic_write(report_path, stable_json_bytes(report_value))
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
    parser.add_argument("--review-items", type=Path, metavar="JSON")
    parser.add_argument("--intentionally-excluded-pages", type=Path, metavar="JSON")
    parser.add_argument("--book-profile", type=Path, metavar="JSON")
    args = parser.parse_args(argv)
    try:
        return convert(
            args.source,
            args.output,
            args.report,
            _json_list(args.non_text_objects, "--non-text-objects") if args.non_text_objects else None,
            args.asset_root,
            _json_list(args.expected_source_tokens, "--expected-source-tokens") if args.expected_source_tokens else None,
            _review_items(_json_list(args.review_items, "--review-items"), "--review-items") if args.review_items else None,
            _positive_pages(_json_list(args.intentionally_excluded_pages, "--intentionally-excluded-pages"), "--intentionally-excluded-pages") if args.intentionally_excluded_pages else None,
            _load_book_profile(args.book_profile) if args.book_profile else None,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 1


if __name__ == "__main__":
    sys.exit(main())
