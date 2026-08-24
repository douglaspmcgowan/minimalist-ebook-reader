from __future__ import annotations

import math
import re
from collections.abc import Iterable

from .model import ExtractionRecord, SemanticBlock


_LIST = re.compile(r"^\s*(?P<marker>(?:\d+[.)]|[-*•]))\s+(?P<text>.+)$")
_INDEX = re.compile(r"^\s*(?P<term>[^,]+),\s*(?P<locators>\d+(?:\s*,\s*\d+)*)\s*$")
_OPENING_PUNCTUATION = "\"'“‘«‹([{"
_TERMINAL_SENTENCE = re.compile(r"[.!?…:;][\"'”’»›)\]}]*$")
_HEADING_CONNECTORS = frozenset({"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with", "without"})


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


def _link_source_key(link: dict) -> tuple | None:
    annotation_id = link.get("annotation_id")
    if isinstance(annotation_id, str) and annotation_id.strip():
        return ("annotation", annotation_id.strip())
    bbox = link.get("bbox")
    try:
        geometry = tuple(float(value) for value in bbox) if isinstance(bbox, (list, tuple)) and len(bbox) == 4 else ()
        target_page = int(link.get("target_page"))
    except (TypeError, ValueError):
        return None
    return ("geometry", target_page, geometry) if geometry else None


def _links_data(records: list[ExtractionRecord]) -> list[dict]:
    links: list[dict] = []
    seen: set[tuple] = set()
    for record in records:
        for source in record.links:
            if not isinstance(source, dict):
                continue
            link = dict(source)
            key = _link_source_key(link)
            if key is not None and key in seen:
                continue
            if key is not None:
                seen.add(key)
            links.append(link)
    return links


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
    links_are_joinable = not record.links or all(
        isinstance(link, dict) and _link_source_key(link) is not None
        for link in record.links
    )
    return (record.role_hint or "") in {"", "paragraph"} and links_are_joinable and not any((record.table, record.form, record.asset)) and not _LIST.match(record.text) and not _INDEX.match(record.text)


_LETTER_WIDTH = 612.0
_LETTER_HEIGHT = 792.0
_COLUMN_TOLERANCE_RATIO = 12.0 / _LETTER_WIDTH
_BOTTOM_EDGE_RATIO = 600.0 / _LETTER_HEIGHT
_TOP_EDGE_RATIO = 144.0 / _LETTER_HEIGHT
_LAYOUT_METADATA_KEYS = frozenset({"page_width", "page_height", "page_bbox"})


def _page_dimension(record: ExtractionRecord, key: str) -> float | None:
    value = record.metadata.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0:
        return float(value)
    return None


def _page_bounds(record: ExtractionRecord) -> tuple[float, float, float, float] | None:
    value = record.metadata.get("page_bbox")
    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            bounds = tuple(float(number) for number in value)
        except (TypeError, ValueError):
            bounds = ()
        if len(bounds) == 4 and all(math.isfinite(number) for number in bounds) and bounds[2] > bounds[0] and bounds[3] > bounds[1]:
            return bounds
    width = _page_dimension(record, "page_width")
    height = _page_dimension(record, "page_height")
    return (0.0, 0.0, width, height) if width is not None and height is not None else None


def _inferred_page_height(record: ExtractionRecord) -> float:
    line_height = max(1.0, record.bbox[3] - record.bbox[1])
    inferred_width = max(1.0, record.bbox[2] + max(0.0, record.bbox[0]))
    return max(
        _LETTER_HEIGHT,
        inferred_width * (_LETTER_HEIGHT / _LETTER_WIDTH),
        record.bbox[3] + max(line_height, record.bbox[0]),
    )


def _same_column(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    first_bounds = _page_bounds(first)
    second_bounds = _page_bounds(second)
    if first_bounds is not None and second_bounds is not None:
        first_position = (first.bbox[0] - first_bounds[0]) / (first_bounds[2] - first_bounds[0])
        second_position = (second.bbox[0] - second_bounds[0]) / (second_bounds[2] - second_bounds[0])
        return abs(first_position - second_position) <= _COLUMN_TOLERANCE_RATIO
    return abs(first.bbox[0] - second.bbox[0]) <= 12


def _same_right_edge(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    first_bounds = _page_bounds(first)
    second_bounds = _page_bounds(second)
    if first_bounds is not None and second_bounds is not None:
        first_position = (first.bbox[2] - first_bounds[0]) / (first_bounds[2] - first_bounds[0])
        second_position = (second.bbox[2] - second_bounds[0]) / (second_bounds[2] - second_bounds[0])
        return abs(first_position - second_position) <= _COLUMN_TOLERANCE_RATIO
    return abs(first.bbox[2] - second.bbox[2]) <= 12


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
    fallback_height = max(_inferred_page_height(first), _inferred_page_height(second))
    first_bounds = _page_bounds(first) or (0.0, 0.0, 1.0, fallback_height)
    second_bounds = _page_bounds(second) or (0.0, 0.0, 1.0, fallback_height)
    first_height = first_bounds[3] - first_bounds[1]
    second_height = second_bounds[3] - second_bounds[1]
    return (
        second.page == first.page + 1
        and first.bbox[3] >= first_bounds[1] + first_height * _BOTTOM_EDGE_RATIO
        and second.bbox[1] <= second_bounds[1] + second_height * _TOP_EDGE_RATIO
    )


def _explicit_continuation(candidate: ExtractionRecord, kind: str) -> bool:
    return bool(
        candidate.metadata.get("continuation")
        or candidate.metadata.get(f"{kind}_continuation")
    )


def _has_terminal_sentence(text: str) -> bool:
    return bool(_TERMINAL_SENTENCE.search(text.strip()))


def _can_join_paragraph_line(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    if not (_is_plain_text(first) and _is_plain_text(second)):
        return False
    if second.page == first.page:
        return _same_page_flow(first, second) and not (
            _has_terminal_sentence(first.text)
            and _initial_text_character(second.text).isupper()
        )
    return (
        _same_column(first, second)
        and _cross_page_flow(first, second)
        and second.text[:1].islower()
        and not _has_terminal_sentence(first.text)
    )


def _table_columns(table: dict) -> int:
    headers = table.get("headers")
    rows = table.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, list) for row in rows):
        return 0
    widths = [len(headers)] if isinstance(headers, list) and headers else []
    widths.extend(len(row) for row in rows)
    return widths[0] if widths and all(width == widths[0] for width in widths) else 0


def _table_pair_geometry(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    return _same_column(first, second) and _same_right_edge(first, second) and _cross_page_flow(first, second)


def _approved_headerless_table_continuation(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    return bool(
        _explicit_continuation(second, "table")
        and second.metadata.get("table_header_source") == "inferred-first-row"
        and first.table
        and second.table
        and first.table.get("headers") != second.table.get("headers")
    )


def _ambiguous_headerless_table_continuation(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    if not isinstance(first.table, dict) or not isinstance(second.table, dict):
        return False
    if _explicit_continuation(second, "table") or not _table_pair_geometry(first, second):
        return False
    first_headers = first.table.get("headers")
    second_headers = second.table.get("headers")
    return bool(
        isinstance(first_headers, list)
        and first_headers
        and isinstance(second_headers, list)
        and second_headers
        and first_headers != second_headers
        and second.metadata.get("table_header_source") == "inferred-first-row"
        and not second.table.get("caption")
        and _table_columns(first.table)
        and _table_columns(first.table) == _table_columns(second.table)
    )


def _can_join_table(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    if not isinstance(first.table, dict) or not isinstance(second.table, dict):
        return False
    if not _table_pair_geometry(first, second):
        return False
    first_headers = first.table.get("headers")
    second_headers = second.table.get("headers")
    if not isinstance(first_headers, list) or not first_headers or not isinstance(second_headers, list) or not second_headers:
        return False
    if not _table_columns(first.table) or _table_columns(first.table) != _table_columns(second.table):
        return False
    second_caption = second.table.get("caption")
    if second_caption and second_caption != first.table.get("caption"):
        return False
    return first_headers == second_headers or _approved_headerless_table_continuation(first, second)


def _conflicting_table_continuation(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    return bool(
        isinstance(first.table, dict)
        and isinstance(second.table, dict)
        and second.page == first.page + 1
        and _explicit_continuation(second, "table")
        and not _can_join_table(first, second)
    )


def _table_data(records: list[ExtractionRecord]) -> dict:
    table = dict(records[0].table or {})
    rows: list[list] = []
    for position, record in enumerate(records):
        record_table = record.table or {}
        if position and _approved_headerless_table_continuation(records[position - 1], record):
            rows.append(list(record_table.get("headers", [])))
        rows.extend(list(row) for row in record_table.get("rows", []) if isinstance(row, list))
    table["rows"] = rows
    return table


def _can_join_quotation(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    if second.role_hint != first.role_hint or first.role_hint not in {"quotation", "testimonial"}:
        return False
    if not (_same_column(first, second) and _cross_page_flow(first, second)):
        return False
    if first.metadata.get("attribution") or _has_terminal_sentence(first.text):
        return False
    return _explicit_continuation(second, first.role_hint) or _initial_text_character(second.text).islower()


def _quotation_data(records: list[ExtractionRecord]) -> dict:
    metadata: dict = {}
    for record in records:
        metadata.update((key, value) for key, value in record.metadata.items() if key not in _LAYOUT_METADATA_KEYS)
    return {**metadata, "text": _join_records(records)}


def _heading_level(record: ExtractionRecord) -> int:
    return int(record.metadata.get("level", 1 if record.font_size >= 18 else 2))


def _is_heading(record: ExtractionRecord) -> bool:
    return record.role_hint == "heading" or (record.bold and record.font_size >= 15)


def _can_join_heading(first: ExtractionRecord, second: ExtractionRecord) -> bool:
    if not _is_heading(second) or not (_same_column(first, second) and _cross_page_flow(first, second)):
        return False
    if not (first.bold and second.bold and first.font_size >= 15 and second.font_size >= 15):
        return False
    if _heading_level(first) != _heading_level(second) or abs(first.font_size - second.font_size) > 1:
        return False
    first_target = first.metadata.get("target")
    second_target = second.metadata.get("target")
    if first_target and second_target and first_target != second_target:
        return False
    if _explicit_continuation(second, "heading"):
        return True
    words = re.sub(r"[^\w]+$", "", first.text.strip()).casefold().rsplit(maxsplit=1)
    return bool(words and (words[-1] in _HEADING_CONNECTORS or _initial_text_character(second.text).islower()))


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


def _explicit_list_continuation(candidate: ExtractionRecord) -> bool:
    return bool(candidate.metadata.get("list_continuation"))


def _continues_list_across_page(last_marker: ExtractionRecord, candidate: ExtractionRecord) -> bool:
    if _explicit_list_continuation(candidate):
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
        return _nearby_line(group[-1], candidate) if candidate.page == group[-1].page else _cross_page_flow(group[-1], candidate) and _explicit_list_continuation(candidate)
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
    table_review_evidence: dict[int, str] = {}
    for position in range(len(source) - 1):
        first, second = source[position], source[position + 1]
        if _ambiguous_headerless_table_continuation(first, second):
            table_review_evidence[id(second)] = "ambiguous-table-continuation"
        elif _conflicting_table_continuation(first, second):
            table_review_evidence[id(second)] = "conflicting-table-continuation"
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
            group = [record]
            index += 1
            while index < len(source) and _can_join_table(group[-1], source[index]):
                group.append(source[index])
                index += 1
            table = _table_data(group) if len(group) > 1 else dict(record.table or {"caption": record.text, "headers": [], "rows": []})
            evidence = ["table-grid", "role-hint"]
            if len(group) > 1:
                evidence.append("cross-page-continuation")
            if any(
                _approved_headerless_table_continuation(group[position - 1], group[position])
                for position in range(1, len(group))
            ):
                evidence.append("approved-headerless-continuation")
            continuation_review = table_review_evidence.get(id(record))
            if continuation_review:
                evidence.append(continuation_review)
            blocks.append(_block(
                "table",
                table,
                group,
                0.65 if continuation_review or not record.table else 0.98,
                *evidence,
            ))
            continue
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
            group = [record]
            index += 1
            while index < len(source) and _can_join_quotation(group[-1], source[index]):
                group.append(source[index])
                index += 1
            evidence = ["role-hint"]
            if len(group) > 1:
                evidence.append("cross-page-continuation")
            blocks.append(_block(hint, _quotation_data(group), group, 0.9, *evidence))
            continue
        elif hint == "divider":
            blocks.append(_block("divider", {}, [record], 0.9, "role-hint"))
        elif hint == "heading" or (record.bold and record.font_size >= 15):
            group = [record]
            index += 1
            while index < len(source) and _can_join_heading(group[-1], source[index]):
                group.append(source[index])
                index += 1
            target = next((item.metadata.get("target") for item in group if item.metadata.get("target")), None)
            heading = {"text": _join_records(group), "level": _heading_level(record), "target": target}
            if any(item.links for item in group):
                heading["links"] = _links_data(group)
            evidence = ["typography", "role-hint" if hint else "font-size"]
            if len(group) > 1:
                evidence.append("cross-page-continuation")
            blocks.append(_block("heading", heading, group, 0.92, *evidence))
            continue
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
