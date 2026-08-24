from __future__ import annotations

import re
from collections.abc import Iterable

from .model import ExtractionRecord, SemanticBlock


_LIST = re.compile(r"^\s*(?P<marker>(?:\d+[.)]|[-*•]))\s+(?P<text>.+)$")
_INDEX = re.compile(r"^\s*(?P<term>[^,]+),\s*(?P<locators>\d+(?:\s*,\s*\d+)*)\s*$")


def _block(kind: str, data: dict, records: list[ExtractionRecord], confidence: float, *evidence: str) -> SemanticBlock:
    return SemanticBlock(
        kind=kind,
        data=data,
        provenance=[record.provenance() for record in records],
        confidence=confidence,
        evidence=list(evidence),
    )


def _target_page(record: ExtractionRecord) -> int | None:
    for link in record.links:
        target = link.get("target_page")
        if target is not None:
            return int(target)
    return None


def _list_data(records: list[ExtractionRecord]) -> dict:
    parsed = [_LIST.match(record.text) for record in records]
    ordered = bool(parsed and all(match and match.group("marker")[0].isdigit() for match in parsed))
    items = [match.group("text").strip() if match else record.text.strip() for record, match in zip(records, parsed)]
    return {"ordered": ordered, "items": items}


def _index_entry(record: ExtractionRecord) -> dict:
    match = _INDEX.match(record.text)
    if match:
        return {"term": match.group("term").strip(), "locators": [item.strip() for item in match.group("locators").split(",")]}
    return {"term": record.text.strip(), "locators": []}


def classify_records(records: Iterable[ExtractionRecord]) -> list[SemanticBlock]:
    """Convert positioned extraction records to deterministic semantic blocks.

    Role hints are evidence supplied by extraction or a book profile. Conservative
    text heuristics cover ordinary headings, lists, and index entries. Ambiguous
    layout remains a paragraph for later validation/review.
    """
    source = sorted(records, key=lambda item: (item.page, item.reading_order, item.bbox, item.text))
    blocks: list[SemanticBlock] = []
    index = 0
    while index < len(source):
        record = source[index]
        hint = record.role_hint or ""

        if hint == "contents_subtitle":
            blocks.append(_block("paragraph", {"text": record.text.strip()}, [record], 0.5, "orphaned-contents-subtitle"))
            index += 1
            continue

        if hint == "contents" or (record.links and _target_page(record) is not None):
            group: list[ExtractionRecord] = []
            entries: list[dict] = []
            while index < len(source):
                item = source[index]
                is_linked_entry = bool(item.links and _target_page(item) is not None)
                if item.role_hint not in {"contents", "contents_subtitle"} and not is_linked_entry:
                    break
                group.append(item)
                if item.role_hint == "contents_subtitle":
                    if entries:
                        entries[-1]["subtitle"] = item.text.strip()
                else:
                    entries.append({"title": item.text.strip(), "subtitle": None, "target_page": _target_page(item)})
                index += 1
            blocks.append(_block("contents", {"entries": entries}, group, 0.98, "role-hint", "internal-link-target"))
            continue

        list_match = _LIST.match(record.text)
        if hint == "list_item" or list_match:
            group = []
            page = record.page
            while index < len(source):
                item = source[index]
                if item.page != page or not (item.role_hint == "list_item" or _LIST.match(item.text)):
                    break
                group.append(item)
                index += 1
            blocks.append(_block("list", _list_data(group), group, 0.96, "list-marker", "aligned-reading-order"))
            continue

        if hint == "table" or record.table:
            table = dict(record.table or {"caption": record.text, "headers": [], "rows": []})
            blocks.append(_block("table", table, [record], 0.98 if record.table else 0.65, "table-grid", "role-hint"))
        elif hint == "form" or record.form:
            form = dict(record.form or {"title": record.text, "instructions": "", "fields": []})
            blocks.append(_block("form", form, [record], 0.98 if record.form else 0.65, "label-field-relationships", "role-hint"))
        elif hint == "figure" or record.asset:
            blocks.append(_block("figure", {"asset": record.asset, "alt": record.alt or "", "caption": record.caption}, [record], 0.95 if record.asset and record.alt else 0.6, "non-text-object", "figure-caption-pair"))
        elif hint == "index_entry" or _INDEX.match(record.text):
            group = []
            while index < len(source):
                item = source[index]
                if item.role_hint != "index_entry" and not _INDEX.match(item.text):
                    break
                group.append(item)
                index += 1
            blocks.append(_block("index", {"entries": [_index_entry(item) for item in group]}, group, 0.94, "term-locator-pattern", "role-hint"))
            continue
        elif hint in {"quotation", "testimonial"}:
            blocks.append(_block(hint, {"text": record.text.strip(), **record.metadata}, [record], 0.9, "role-hint"))
        elif hint == "divider":
            blocks.append(_block("divider", {}, [record], 0.9, "role-hint"))
        elif hint == "heading" or (record.bold and record.font_size >= 15):
            level = int(record.metadata.get("level", 1 if record.font_size >= 18 else 2))
            blocks.append(_block("heading", {"text": record.text.strip(), "level": level, "target": record.metadata.get("target")}, [record], 0.92, "typography", "role-hint" if hint else "font-size"))
        else:
            blocks.append(_block("paragraph", {"text": record.text.strip()}, [record], 0.8, "reading-order", "text-block"))
        index += 1
    return blocks
