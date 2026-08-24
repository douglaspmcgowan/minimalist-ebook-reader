from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from .model import SemanticBlock


def _source_key(block: SemanticBlock) -> tuple[int, int]:
    if not block.provenance:
        return (10**9, 10**9)
    first = min(block.provenance, key=lambda source: (source.page, source.reading_order))
    return first.page, first.reading_order


def _chapter_title(block: SemanticBlock, fallback: str) -> str:
    title = block.data.get("text") if block.kind == "heading" else None
    return title.strip() if isinstance(title, str) and title.strip() else fallback


def _page_targets(chapters: list[dict[str, Any]], page_count: int) -> dict[int, str]:
    targets: dict[int, str] = {}
    for index, chapter in enumerate(chapters):
        start = chapter["sourcePages"]["start"]
        end = chapters[index + 1]["sourcePages"]["start"] - 1 if index + 1 < len(chapters) else page_count
        chapter["sourcePages"]["end"] = max(start, end)
        for page in range(start, min(end, page_count) + 1):
            targets[page] = chapter["target"]
    return targets


def _reader_block(block: SemanticBlock, page_targets: dict[int, str]) -> dict[str, Any]:
    value = deepcopy(block.to_dict())
    if block.kind != "contents":
        return value
    entries = value["data"].get("entries")
    if not isinstance(entries, list):
        return value
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("target"):
            continue
        try:
            target_page = int(entry.get("target_page"))
        except (TypeError, ValueError):
            continue
        target = page_targets.get(target_page)
        if target:
            entry["target"] = target
    return value


def build_reader_package(
    blocks: Iterable[SemanticBlock],
    page_count: int,
    source: dict[str, Any],
    preflight: dict[str, Any],
    source_name: str = "",
) -> dict[str, Any]:
    """Translate semantic IR into the reader's chapter contract deterministically."""
    ordered = sorted(blocks, key=_source_key)
    metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    title = str(metadata.get("Title") or source_name or "Untitled PDF").strip()
    author = str(metadata.get("Author") or "").strip()
    chapters: list[dict[str, Any]] = []

    for block in ordered:
        starts_section = block.kind == "heading" and int(block.data.get("level") or 2) == 1
        if not chapters or starts_section:
            start_page = _source_key(block)[0]
            chapters.append({
                "number": len(chapters) + 1,
                "title": _chapter_title(block, title),
                "target": f"section-{len(chapters) + 1}",
                "sourcePages": {"start": start_page, "end": start_page},
                "blocks": [],
            })
        chapters[-1]["blocks"].append(block)

    page_targets = _page_targets(chapters, page_count) if chapters else {}
    reader_chapters = []
    for chapter in chapters:
        reader_chapters.append({
            **{key: value for key, value in chapter.items() if key != "blocks"},
            "blocks": [_reader_block(block, page_targets) for block in chapter["blocks"]],
        })

    return {
        "schema_version": 1,
        "reader": {
            "schema_version": 1,
            "source_sha256": source.get("sha256"),
            "source_page_count": page_count,
        },
        "title": title,
        "author": author,
        "source": source,
        "preflight": preflight,
        "sourceCoverage": [{"page": page} for page in range(1, page_count + 1)],
        "blocks": [block.to_dict() for block in ordered],
        "chapters": reader_chapters,
    }
