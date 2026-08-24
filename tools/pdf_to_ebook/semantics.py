from __future__ import annotations

import re
from collections.abc import Iterable

from .model import ExtractionRecord, SemanticBlock


_LIST = re.compile(r"^\s*(?P<marker>(?:\d+[.)]|[-*•]))\s+(?P<text>.+)$")
_INDEX = re.compile(r"^\s*(?P<term>[^,]+),\s*(?P<locators>\d+(?:\s*,\s*\d+)*)\s*$")
_OPENING_PUNCTUATION = "\"'“‘«‹([{"


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
        if not isinstance(link, dict):
            continue
        target = link.get("target_page")
        if target is not None:
            try:
                return int(target)
            except (TypeError, ValueError):
                continue
    return None


def _link_signature(record: ExtractionRecord) -> tuple[int | None, tuple[float, ...]]:
    link = next((item for item in record.links if isinstance(item, dict)), {})
    bbox = link.get("bbox")
    try:
        geometry = tuple(float(value) for value in bbox) if isinstance(bbox, (list, tuple)) and len(bbox) == 4 else ()
    except (TypeError, ValueError):
        geometry = ()
    return _target_page(record), geometry


def _aligned_contents_entry(first: ExtractionRecord, previous: ExtractionRecord, candidate: ExtractionRecord) -> bool:
    height = max(
        1.0,
        first.bbox[3] - first.bbox[1],
        previous.bbox[3] - previous.bbox[1],
        candidate.bbox[3] - candidate.bbox[1],
    )
    vertical_gap = candidate.bbox[1] - previous.bbox[3]
    return (
        candidate.page == first.page
        and _target_page(candidate) is not None
        and abs(candidate.bbox[0] - first.bbox[0]) <= 12
        and -height <= vertical_gap <= max(36.0, 2.5 * height)
    )


def _linked_contents_cluster(records: list[ExtractionRecord], start: int) -> bool:
    first = records[start]
    if _target_page(first) is None:
        return False
    aligned = 0
    signatures: set[tuple[int | None, tuple[float, ...]]] = set()
    targets: set[int | None] = set()
    previous = first
    for record in records[start:]:
        if aligned and not _aligned_contents_entry(first, previous, record):
            break
        if not aligned and (record.page != first.page or _target_page(record) is None):
            break
        aligned += 1
        signatures.add(_link_signature(record))
        targets.add(_target_page(record))
        previous = record
    return aligned >= 2 and len(signatures) >= 2 and len(targets) >= 2


def _links_data(records: list[ExtractionRecord]) -> list[dict]:
    return [dict(link) for record in records for link in record.links if isinstance(link, dict)]


def _text_data(records: list[ExtractionRecord]) -> dict:
    data = {"text": _join_records(records)}
    links = _links_data(records)
    if links:
        data["links"] = links
    return data


def _list_data(records: list[ExtractionRecord]) -> dict:
    parsed = [_LIST.match(record.text) for record in records]
    markers = [match for match in parsed if match]
    ordered = bool(markers and all(match.group("marker")[0].isdigit() for match in markers))
    items: list[str] = []
    previous = None
    for record, match in zip(records, parsed):
        if match or record.role_hint == "list_item":
            items.append(match.group("text").strip() if match else record.text.strip())
        elif items:
            items[-1] = _join_text(items[-1], record.text, bool(previous and previous.metadata.get("discretionary_hyphen")))
        previous = record
    return {"ordered": ordered, "items": items}


def _index_entry(record: ExtractionRecord) -> dict:
    match = _INDEX.match(record.text)
    if match:
        return {"term": match.group("term").strip(), "locators": [item.strip() for item in match.group("locators").split(",")]}
    return {"term": record.text.strip(), "locators": []}


def _join_text(first: str, second: str, discretionary_hyphen: bool = False) -> str:
    first = first.strip()
    second = second.strip()
    if first.endswith("-") and second:
        return (first[:-1] if discretionary_hyphen else first) + second
    return f"{first} {second}".strip()


def _join_records(records: list[ExtractionRecord]) -> str:
    text = ""
    previous = None
    for record in records:
        text = record.text.strip() if not text else _join_text(text, record.text, bool(previous and previous.metadata.get("discretionary_hyphen")))
        previous = record
    return text


def _is_plain_text(record: ExtractionRecord) -> bool:
    return (record.role_hint or "") in {"", "paragraph"} and not any((record.links, record.table, record.form, record.asset)) and not _LIST.match(record.text) and not _INDEX.match(record.text)


def _same_column(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    return abs(first.bbox[0] - second.bbox[0]) <= 12


def _nearby_line(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    first_height = max(1.0, first.bbox[3] - first.bbox[1])
    second_height = max(1.0, second.bbox[3] - second.bbox[1])
    gap = second.bbox[1] - first.bbox[3]
    return -max(first_height, second_height) <= gap <= 0.75 * max(first_height, second_height)


def _same_page_flow(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    return _same_column(first, second) and _nearby_line(first, second)


def _initial_text_character(text: str) -> str:
    return text.lstrip().lstrip(_OPENING_PUNCTUATION).lstrip()[:1]


def _cross_page_flow(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    return (
        second.page == first.page + 1
        and first.bbox[3] >= 600
        and second.bbox[1] <= 144
    )


def _can_join_paragraph_line(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    if not _is_plain_text(second):
        return False
    if second.page == first.page:
        return _same_page_flow(first, second) and not (
            re.search(r"[.!?…:;][\"')\]]*$", first.text.strip())
            and _initial_text_character(second.text).isupper()
        )
    return (
        _same_column(first, second)
        and _cross_page_flow(first, second)
        and second.text[:1].islower()
        and not re.search(r"[.!?…:;][\"')\]]*$", first.text.strip())
    )


def _list_marker_family(record: ExtractionRecord) -> str | None:
    match = _LIST.match(record.text)
    if not match:
        return "hint" if record.role_hint == "list_item" else None
    return "ordered" if match.group("marker")[0].isdigit() else "unordered"


def _ordered_marker_value(record: ExtractionRecord) -> int | None:
    match = _LIST.match(record.text)
    if not match or not match.group("marker")[0].isdigit():
        return None
    return int(match.group("marker").rstrip(".)"))


def _explicit_list_continuation(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    return bool(first.metadata.get("list_continuation") or second.metadata.get("list_continuation"))


def _continues_list_across_page(last_marker: ExtractionRecord, candidate: ExtractionRecord) -> bool:
    if _explicit_list_continuation(last_marker, candidate):
        return True
    previous_number = _ordered_marker_value(last_marker)
    candidate_number = _ordered_marker_value(candidate)
    return previous_number is not None and candidate_number == previous_number + 1


def _can_continue_list(group: list[ExtractionRecord], candidate: ExtractionRecord) -> bool:
    first_marker = next((record for record in group if _list_marker_family(record)), None)
    last_marker = next((record for record in reversed(group) if _list_marker_family(record)), None)
    if first_marker is None or last_marker is None:
        return False
    candidate_family = _list_marker_family(candidate)
    if candidate_family:
        if candidate_family == "hint":
            return _same_page_flow(group[-1], candidate) if candidate.page == group[-1].page else _same_column(group[-1], candidate) and _cross_page_flow(group[-1], candidate) and _continues_list_across_page(last_marker, candidate)
        if candidate_family != _list_marker_family(first_marker):
            return False
        return _same_page_flow(group[-1], candidate) if candidate.page == group[-1].page else _same_column(last_marker, candidate) and _cross_page_flow(group[-1], candidate) and _continues_list_across_page(last_marker, candidate)
    if candidate.role_hint == "list_continuation":
        return _nearby_line(group[-1], candidate) if candidate.page == group[-1].page else _cross_page_flow(group[-1], candidate) and _explicit_list_continuation(last_marker, candidate)
    return (
        candidate.page == group[-1].page
        and _nearby_line(group[-1], candidate)
        and candidate.bbox[0] >= last_marker.bbox[0] + 8
        and candidate.text[:1].islower()
    )


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

        if hint == "non_text_object":
            index += 1
            continue

        if hint == "contents" or _linked_contents_cluster(source, index):
            explicit_contents = hint == "contents"
            group: list[ExtractionRecord] = []
            entries: list[dict] = []
            previous_contents_entry = record
            while index < len(source):
                item = source[index]
                is_linked_entry = bool(item.links and _target_page(item) is not None)
                if explicit_contents:
                    if item.role_hint not in {"contents", "contents_subtitle"} and not is_linked_entry:
                        break
                elif (
                    not is_linked_entry
                    or (group and not _aligned_contents_entry(record, previous_contents_entry, item))
                ):
                    break
                group.append(item)
                if item.role_hint == "contents_subtitle":
                    if entries:
                        entries[-1]["subtitle"] = item.text.strip()
                else:
                    entries.append({"title": item.text.strip(), "subtitle": None, "target_page": _target_page(item)})
                    previous_contents_entry = item
                index += 1
            blocks.append(_block("contents", {"entries": entries}, group, 0.98, "role-hint", "internal-link-target"))
            continue

        list_match = _LIST.match(record.text)
        if hint == "list_item" or list_match:
            group = [record]
            index += 1
            while index < len(source) and _can_continue_list(group, source[index]):
                group.append(source[index])
                index += 1
            evidence = ["list-marker", "aligned-reading-order"]
            if len({item.page for item in group}) > 1:
                evidence.append("cross-page-continuation")
            blocks.append(_block("list", _list_data(group), group, 0.96, *evidence))
            continue

        if hint == "table" or record.table:
            table = dict(record.table or {"caption": record.text, "headers": [], "rows": []})
            blocks.append(_block("table", table, [record], 0.98 if record.table else 0.65, "table-grid", "role-hint"))
        elif hint == "form" or record.form:
            form = dict(record.form or {"title": record.text, "instructions": "", "fields": []})
            blocks.append(_block("form", form, [record], 0.98 if record.form else 0.65, "label-field-relationships", "role-hint"))
        elif hint == "figure" or record.asset:
            figure = {"asset": record.asset, "alt": record.alt or "", "caption": record.caption}
            if record.metadata.get("asset_sha256"):
                figure["sha256"] = record.metadata["asset_sha256"]
            if record.metadata.get("object_name"):
                figure["object_name"] = record.metadata["object_name"]
            blocks.append(_block("figure", figure, [record], 0.95 if record.asset and record.alt else 0.6, "non-text-object", "figure-caption-pair"))
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
            heading = {"text": record.text.strip(), "level": level, "target": record.metadata.get("target")}
            if record.links:
                heading["links"] = _links_data([record])
            blocks.append(_block("heading", heading, [record], 0.92, "typography", "role-hint" if hint else "font-size"))
        else:
            group = [record]
            index += 1
            while index < len(source) and _can_join_paragraph_line(group[-1], source[index]):
                group.append(source[index])
                index += 1
            evidence = ["reading-order", "text-block"]
            if len(group) > 1:
                evidence.append("geometry-line-flow")
            if len({item.page for item in group}) > 1:
                evidence.append("cross-page-continuation")
            blocks.append(_block("paragraph", _text_data(group), group, 0.8, *evidence))
            continue
        index += 1
    return blocks
