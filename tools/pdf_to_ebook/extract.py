from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pdfplumber
from pypdf import PdfReader

from .model import ExtractionRecord


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _outline_count(reader: PdfReader) -> int:
    def count(items: list[Any]) -> int:
        return sum(count(item) if isinstance(item, list) else 1 for item in items)
    try:
        return count(reader.outline)
    except Exception:
        return 0


def preflight_pdf(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    reader = PdfReader(source)
    pages = []
    with pdfplumber.open(source) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.find_tables()
            table_boxes = [tuple(float(value) for value in table.bbox) for table in tables]
            pages.append({
                "page": number,
                "width": round(float(page.width), 3),
                "height": round(float(page.height), 3),
                "characters": len(text),
                "images": len(page.images),
                "tables": len(tables),
                "vector_regions": len(_vector_regions(page, table_boxes)),
                "annotations": len(page.annots or []),
            })
    metadata = {str(key).lstrip("/"): str(value) for key, value in (reader.metadata or {}).items() if value is not None}
    return {
        "schema_version": 1,
        "source": {"sha256": _sha256(source), "page_count": len(reader.pages), "metadata": metadata, "outline_items": _outline_count(reader)},
        "pages": pages,
    }


def _group_words(words: list[dict[str, Any]], tolerance: float = 4.0) -> list[list[dict[str, Any]]]:
    lines: list[list[dict[str, Any]]] = []
    for word in sorted(words, key=lambda item: (round(float(item["top"]) / tolerance), float(item["x0"]))):
        if not lines or abs(float(word["top"]) - float(lines[-1][0]["top"])) > tolerance:
            lines.append([word])
        else:
            lines[-1].append(word)
    return lines


def _line_segments(line: list[dict[str, Any]], column_gap: float = 72.0) -> list[list[dict[str, Any]]]:
    """Split a visual line at a wide horizontal gap that indicates columns."""
    segments: list[list[dict[str, Any]]] = []
    for word in sorted(line, key=lambda item: float(item["x0"])):
        if segments and float(word["x0"]) - float(segments[-1][-1]["x1"]) > column_gap:
            segments.append([])
        elif not segments:
            segments.append([])
        segments[-1].append(word)
    return segments


def _intersection(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> bool:
    return first[0] < second[2] and second[0] < first[2] and first[1] < second[3] and second[1] < first[3]


def _contains(outer: tuple[float, float, float, float], inner: tuple[float, float, float, float]) -> bool:
    return inner[0] >= outer[0] and inner[1] >= outer[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def _near_or_intersecting(first: tuple[float, float, float, float], second: tuple[float, float, float, float], gap: float = 2.0) -> bool:
    return not (
        first[2] + gap < second[0]
        or second[2] + gap < first[0]
        or first[3] + gap < second[1]
        or second[3] + gap < first[1]
    )


def _vector_bbox(item: dict[str, Any]) -> tuple[float, float, float, float] | None:
    try:
        bbox = tuple(float(item[key]) for key in ("x0", "top", "x1", "bottom"))
    except (KeyError, TypeError, ValueError):
        return None
    if bbox[0] > bbox[2] or bbox[1] > bbox[3]:
        return None
    return bbox


def _vector_regions(page: Any, table_boxes: list[tuple[float, float, float, float]]) -> list[tuple[float, float, float, float]]:
    primitives = []
    for item in [*page.curves, *page.rects, *page.lines]:
        bbox = _vector_bbox(item)
        if bbox is not None and not any(_contains(table, bbox) for table in table_boxes):
            primitives.append(bbox)
    regions: list[tuple[float, float, float, float]] = []
    for bbox in sorted(set(primitives)):
        matches = [index for index, region in enumerate(regions) if _near_or_intersecting(region, bbox)]
        if not matches:
            regions.append(bbox)
            continue
        merged = bbox
        for index in reversed(matches):
            region = regions.pop(index)
            merged = (
                min(merged[0], region[0]),
                min(merged[1], region[1]),
                max(merged[2], region[2]),
                max(merged[3], region[3]),
            )
        regions.append(merged)
    return sorted(regions, key=lambda bbox: (bbox[1], bbox[0], bbox[3], bbox[2]))


def _character_gap(previous: dict[str, Any], character: dict[str, Any], rotation: int) -> float:
    if rotation == 90:
        return float(character["top"]) - float(previous["bottom"])
    if rotation == 270:
        return float(previous["top"]) - float(character["bottom"])
    if rotation == 180:
        return float(previous["x0"]) - float(character["x1"])
    return float(character["x0"]) - float(previous["x1"])


def _character_lines(characters: list[dict[str, Any]], rotation: int) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    anchors: list[float] = []
    for character in characters:
        anchor = float(character["x0"] if rotation in {90, 270} else character["top"])
        match = next((index for index, value in enumerate(anchors) if abs(anchor - value) <= 4.0), None)
        if match is None:
            anchors.append(anchor)
            groups.append([])
            match = len(groups) - 1
        groups[match].append(character)
    if rotation == 90:
        for group in groups:
            group.sort(key=lambda item: float(item["top"]))
        groups.sort(key=lambda group: -float(group[0]["x0"]))
    elif rotation == 270:
        for group in groups:
            group.sort(key=lambda item: -float(item["top"]))
        groups.sort(key=lambda group: float(group[0]["x0"]))
    elif rotation == 180:
        for group in groups:
            group.sort(key=lambda item: -float(item["x0"]))
        groups.sort(key=lambda group: -float(group[0]["top"]))
    else:
        for group in groups:
            group.sort(key=lambda item: float(item["x0"]))
        groups.sort(key=lambda group: float(group[0]["top"]))
    return groups


def _character_text(characters: list[dict[str, Any]], rotation: int) -> str:
    pieces: list[str] = []
    previous = None
    for character in characters:
        if previous is not None and _character_gap(previous, character, rotation) > 1.0 and pieces and not pieces[-1].endswith(" "):
            pieces.append(" ")
        pieces.append(str(character.get("text") or ""))
        previous = character
    return re.sub(r"\s+", " ", "".join(pieces)).strip()


def _logical_rotated_spans(page: Any) -> list[dict[str, Any]]:
    rotation = int(getattr(page, "rotation", 0) or 0) % 360
    if rotation == 0:
        return page.extract_words(extra_attrs=["fontname", "size"], keep_blank_chars=False)
    spans = []
    for line in _character_lines(page.chars, rotation):
        runs: list[list[dict[str, Any]]] = [[]]
        previous = None
        for character in line:
            if previous is not None and _character_gap(previous, character, rotation) > 72.0:
                runs.append([])
            runs[-1].append(character)
            previous = character
        for group in runs:
            text = _character_text(group, rotation)
            if not text:
                continue
            spans.append({
                "text": text,
                "x0": min(float(item["x0"]) for item in group),
                "x1": max(float(item["x1"]) for item in group),
                "top": min(float(item["top"]) for item in group),
                "bottom": max(float(item["bottom"]) for item in group),
                "fontname": str(group[0].get("fontname") or ""),
                "size": sum(
                    float(item["x1"] - item["x0"] if rotation in {90, 270} else item["bottom"] - item["top"])
                    for item in group
                ) / len(group),
            })
    return spans


def _anchor_text(page: Any, bbox: tuple[float, float, float, float]) -> str:
    characters = [
        character
        for character in page.chars
        if _intersection(
            (float(character["x0"]), float(character["top"]), float(character["x1"]), float(character["bottom"])),
            bbox,
        )
    ]
    rotation = int(getattr(page, "rotation", 0) or 0) % 360
    return " ".join(filter(None, (_character_text(line, rotation) for line in _character_lines(characters, rotation))))


def _annotation_bbox(annotation: Any, page: Any) -> tuple[float, float, float, float] | None:
    rectangle = annotation.get("/Rect")
    if not rectangle or len(rectangle) != 4:
        return None
    left, bottom, right, top = (float(value) for value in rectangle)
    crop = page.cropbox
    crop_left, crop_bottom, crop_right, crop_top = (float(value) for value in crop)
    left, bottom, right, top = max(min(left, right), crop_left), max(min(bottom, top), crop_bottom), min(max(left, right), crop_right), min(max(bottom, top), crop_top)
    if left >= right or bottom >= top:
        return None
    media_left, media_bottom, media_right, media_top = (float(value) for value in page.mediabox)
    width, height = media_right - media_left, media_top - media_bottom
    rotation = int(page.get("/Rotate") or 0) % 360

    def transform(x: float, y: float) -> tuple[float, float]:
        x, y = x - media_left, y - media_bottom
        if rotation == 90:
            return y, x
        if rotation == 180:
            return width - x, y
        if rotation == 270:
            return height - y, width - x
        return x, height - y

    points = [transform(x, y) for x in (left, right) for y in (bottom, top)]
    return (min(x for x, _ in points), min(y for _, y in points), max(x for x, _ in points), max(y for _, y in points))


def _inherited_annotation_value(annotation: Any, key: str) -> Any:
    current = annotation
    seen: set[tuple[int | None, int | None]] = set()
    while current is not None:
        reference = getattr(current, "indirect_reference", None)
        identity = (getattr(reference, "idnum", None), getattr(reference, "generation", None))
        if identity in seen:
            return None
        seen.add(identity)
        if key in current:
            return current[key]
        parent = current.get("/Parent")
        current = parent.get_object() if parent is not None else None
    return None


def _annotation_group_id(annotation: Any) -> str:
    current = annotation
    identity = ""
    seen: set[tuple[int | None, int | None]] = set()
    while current is not None:
        reference = getattr(current, "indirect_reference", None)
        key = (getattr(reference, "idnum", None), getattr(reference, "generation", None))
        if key in seen:
            break
        seen.add(key)
        if key[0] is not None:
            identity = f"{key[0]}:{key[1] or 0}"
        parent = current.get("/Parent")
        current = parent.get_object() if parent is not None else None
    return identity or str(_inherited_annotation_value(annotation, "/T") or "anonymous")


def _widget_options(annotation: Any, field_type: str, field_flags: int) -> list[str]:
    options: list[str] = []

    def append(value: Any) -> None:
        text = str(value or "").lstrip("/").strip()
        if text and text not in options:
            options.append(text)

    inherited = _inherited_annotation_value(annotation, "/Opt")
    if isinstance(inherited, (list, tuple)):
        for option in inherited:
            value = option[1] if isinstance(option, (list, tuple)) and len(option) >= 2 else option[0] if isinstance(option, (list, tuple)) and option else option
            append(value)
    if field_type == "button" and not field_flags & (1 << 16):
        appearance = annotation.get("/AP") or {}
        normal = appearance.get("/N") if hasattr(appearance, "get") else None
        normal = normal.get_object() if hasattr(normal, "get_object") else normal
        if hasattr(normal, "keys") and not hasattr(normal, "get_data"):
            for value in normal.keys():
                if str(value) != "/Off":
                    append(value)
    return options


def _widget_value(annotation: Any) -> str | list[str]:
    raw = _inherited_annotation_value(annotation, "/V")
    mapping: dict[str, str] = {}
    inherited = _inherited_annotation_value(annotation, "/Opt")
    if isinstance(inherited, (list, tuple)):
        for option in inherited:
            if isinstance(option, (list, tuple)) and len(option) >= 2:
                mapping[str(option[0]).lstrip("/")] = str(option[1])

    def normalize(value: Any) -> str:
        text = str(value or "").lstrip("/")
        return mapping.get(text, text)

    if isinstance(raw, (list, tuple)):
        return [normalize(value) for value in raw]
    return normalize(raw)


def _destination_page(reader: PdfReader, destination: Any) -> int | None:
    if destination is None:
        return None
    if isinstance(destination, (str, bytes)):
        named = reader.named_destinations.get(str(destination))
        if named is None:
            return None
        destination = named
    try:
        return int(reader.get_destination_page_number(destination)) + 1
    except Exception:
        pass
    try:
        target = destination[0]
        target_id = getattr(target, "idnum", None)
        for number, page in enumerate(reader.pages, start=1):
            if getattr(page.indirect_reference, "idnum", None) == target_id:
                return number
    except (IndexError, KeyError, TypeError):
        pass
    return None


def _page_annotations(reader: PdfReader, page_number: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    links: list[dict[str, Any]] = []
    widgets: list[dict[str, Any]] = []
    page = reader.pages[page_number - 1]
    for reference in page.get("/Annots", []):
        annotation = reference.get_object()
        bbox = _annotation_bbox(annotation, page)
        subtype = str(annotation.get("/Subtype") or "")
        if subtype == "/Link" and bbox is not None:
            action = annotation.get("/A") or {}
            target_page = _destination_page(reader, annotation.get("/Dest") or action.get("/D"))
            if target_page is not None:
                links.append({"bbox": bbox, "target_page": target_page})
        elif subtype == "/Widget" and bbox is not None:
            name = str(_inherited_annotation_value(annotation, "/T") or "")
            tooltip = str(_inherited_annotation_value(annotation, "/TU") or "").strip()
            label = tooltip or name
            field_type = {"/Tx": "text", "/Btn": "button", "/Ch": "choice", "/Sig": "signature"}.get(str(_inherited_annotation_value(annotation, "/FT") or ""), "unknown")
            field_flags = int(_inherited_annotation_value(annotation, "/Ff") or 0)
            widget = {
                "bbox": bbox,
                "group_id": _annotation_group_id(annotation),
                "name": name,
                "label": label,
                "field": {
                    "name": name,
                    "label": label,
                    "type": field_type,
                    "value": _widget_value(annotation),
                    "required": bool(field_flags & 2),
                },
                "options": _widget_options(annotation, field_type, field_flags),
            }
            if not tooltip:
                widget["review"] = {
                    "code": "widget-label-name-fallback",
                    "severity": "high",
                    "message": "Widget label falls back to /T because inherited /TU is absent.",
                    "field_name": name,
                }
            widgets.append(widget)
    return links, widgets


def _ambiguous_reading_order(candidates: list[dict[str, Any]], page_width: float, rotation: int = 0) -> bool:
    text = [candidate for candidate in candidates if candidate["text"]]
    if len(text) >= 4:
        column_axis = 1 if rotation in {90, 270} else 0
        flow_start, flow_end = ((0, 2) if rotation in {90, 270} else (1, 3))
        ordered = sorted(text, key=lambda item: item["bbox"][column_axis])
        gaps = [(ordered[index + 1]["bbox"][column_axis] - item["bbox"][column_axis], index) for index, item in enumerate(ordered[:-1])]
        gap, index = max(gaps, default=(0.0, -1))
        if gap >= max(72.0, page_width * 0.15):
            left, right = ordered[:index + 1], ordered[index + 1:]
            if len(left) >= 2 and len(right) >= 2:
                left_top, left_bottom = min(item["bbox"][flow_start] for item in left), max(item["bbox"][flow_end] for item in left)
                right_top, right_bottom = min(item["bbox"][flow_start] for item in right), max(item["bbox"][flow_end] for item in right)
                if max(left_top, right_top) < min(left_bottom, right_bottom):
                    return True
    return any(
        _intersection(first["bbox"], second["bbox"])
        for index, first in enumerate(candidates)
        for second in candidates[index + 1:]
    )


def _reading_order_key(candidate: dict[str, Any], rotation: int) -> tuple[Any, ...]:
    left, top, right, bottom = candidate["bbox"]
    role = candidate.get("role_hint") or ""
    if rotation == 90:
        return (-right, top, -left, bottom, role)
    if rotation == 180:
        return (-bottom, -right, -top, -left, role)
    if rotation == 270:
        return (left, -bottom, right, -top, role)
    return (top, left, bottom, right, role)


def _figure_asset(page: Any, bbox: tuple[float, float, float, float], output_dir: Path | None, page_number: int, figure_number: int) -> tuple[str | None, dict[str, Any]]:
    filename = Path("assets") / f"page-{page_number:04d}-figure-{figure_number:02d}.png"
    metadata: dict[str, Any] = {}
    if output_dir is None:
        metadata["review"] = [{"code": "figure-asset-unmaterialized", "severity": "high", "message": "Figure requires an explicit asset output directory."}]
        return None, metadata
    try:
        root = output_dir.resolve()
        if root.exists() and not root.is_dir():
            raise ValueError("Asset output root must be a directory.")
        destination = (root / filename).resolve()
        destination.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        page.crop(bbox).to_image(resolution=144).save(destination, format="PNG")
        metadata["asset_sha256"] = _sha256(destination)
        return filename.as_posix(), metadata
    except (OSError, ValueError) as error:
        metadata["review"] = [{"code": "figure-asset-unmaterialized", "severity": "high", "message": str(error)}]
        return None, metadata


def _image_alt(image: dict[str, Any]) -> str | None:
    stream = image.get("stream")
    attributes = getattr(stream, "attrs", {})
    for key, value in attributes.items():
        if str(key).lstrip("/") not in {"Alt", "ActualText"}:
            continue
        text = bytes(value).decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
        if text.strip():
            return text.strip()
    return None


def _add_review(metadata: dict[str, Any], review: dict[str, Any]) -> None:
    existing = metadata.get("review", [])
    items = [existing] if isinstance(existing, dict) else list(existing)
    items.append(review)
    metadata["review"] = sorted(items, key=lambda item: (str(item.get("code") or ""), str(item.get("severity") or ""), str(item.get("message") or "")))


def extract_pdf(
    path: str | Path,
    page_numbers: list[int] | tuple[int, ...] | None = None,
    include_preflight: bool = True,
    asset_output_dir: str | Path | None = None,
) -> tuple[dict[str, Any], list[ExtractionRecord]]:
    """Extract positioned lines, tables, and image regions from a PDF."""
    requested = sorted(set(int(page) for page in page_numbers)) if page_numbers is not None else None
    preflight = preflight_pdf(path) if include_preflight else {
        "schema_version": 1,
        "requested_pages": requested or [],
    }
    source = Path(path)
    assets = Path(asset_output_dir) if asset_output_dir is not None else None
    reader = PdfReader(source)
    records: list[ExtractionRecord] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            if requested is not None and page_number not in requested:
                continue
            candidates: list[dict[str, Any]] = []
            tables = page.find_tables()
            table_boxes = [tuple(float(value) for value in table.bbox) for table in tables]
            links, widgets = _page_annotations(reader, page_number)
            for table, bbox in zip(tables, table_boxes):
                rows = table.extract() or []
                headers = [str(cell or "").strip() for cell in rows[0]] if rows else []
                body = [[str(cell or "").strip() for cell in row] for row in rows[1:]]
                candidates.append({"bbox": bbox, "role_hint": "table", "table": {"caption": None, "headers": headers, "rows": body}, "text": ""})

            words = _logical_rotated_spans(page)
            line_groups = [[word] for word in words] if int(getattr(page, "rotation", 0) or 0) % 360 else _group_words(words)
            for line in line_groups:
                for segment in _line_segments(line):
                    x0 = min(float(word["x0"]) for word in segment)
                    top = min(float(word["top"]) for word in segment)
                    x1 = max(float(word["x1"]) for word in segment)
                    bottom = max(float(word["bottom"]) for word in segment)
                    bbox = (x0, top, x1, bottom)
                    if any(x0 >= box[0] and top >= box[1] and x1 <= box[2] and bottom <= box[3] for box in table_boxes):
                        continue
                    sizes = [float(word.get("size") or 0) for word in segment]
                    fonts = [str(word.get("fontname") or "") for word in segment]
                    text = " ".join(str(word["text"]) for word in segment).strip()
                    if text:
                        candidates.append({
                            "bbox": bbox,
                            "text": text,
                            "font_size": round(sum(sizes) / len(sizes), 3),
                            "bold": any("bold" in font.lower() for font in fonts),
                            "links": [
                                {
                                    "target_page": link["target_page"],
                                    "bbox": list(link["bbox"]),
                                    "text": _anchor_text(page, link["bbox"]) or text,
                                }
                                for link in links
                                if _intersection(bbox, link["bbox"])
                            ],
                        })

            for image_number, image in enumerate(page.images, start=1):
                bbox = (float(image["x0"]), float(image["top"]), float(image["x1"]), float(image["bottom"]))
                asset, metadata = _figure_asset(page, bbox, assets, page_number, image_number)
                metadata["object_name"] = image.get("name")
                candidates.append({"bbox": bbox, "text": "", "role_hint": "figure", "asset": asset, "alt": _image_alt(image), "metadata": metadata})

            for vector_number, bbox in enumerate(_vector_regions(page, table_boxes), start=1):
                candidates.append({
                    "bbox": bbox,
                    "text": "",
                    "role_hint": "non_text_object",
                    "metadata": {
                        "object_id": f"page-{page_number:04d}-vector-{vector_number:03d}",
                        "object_kind": "vector",
                    },
                })

            widget_groups: dict[str, list[dict[str, Any]]] = {}
            for widget in widgets:
                widget_groups.setdefault(widget["group_id"], []).append(widget)
            for group in widget_groups.values():
                first = group[0]
                bbox = (
                    min(widget["bbox"][0] for widget in group),
                    min(widget["bbox"][1] for widget in group),
                    max(widget["bbox"][2] for widget in group),
                    max(widget["bbox"][3] for widget in group),
                )
                metadata = {"widget_name": first["name"], "widget_count": len(group)}
                for widget in group:
                    if widget.get("review"):
                        _add_review(metadata, widget["review"])
                fields_by_name: dict[str, dict[str, Any]] = {}
                for widget in group:
                    field = dict(widget["field"])
                    key = str(field.get("name") or field.get("label") or len(fields_by_name))
                    existing = fields_by_name.setdefault(key, field)
                    options = list(existing.get("options", []))
                    options.extend(option for option in widget.get("options", []) if option not in options)
                    if options:
                        existing["options"] = options
                candidates.append({
                    "bbox": bbox,
                    "text": "",
                    "role_hint": "form",
                    "form": {"title": first["label"], "instructions": "", "fields": list(fields_by_name.values())},
                    "metadata": metadata,
                })

            reading_order_candidates = [candidate for candidate in candidates if candidate.get("role_hint") != "non_text_object"]
            rotation = int(getattr(page, "rotation", 0) or 0) % 360
            column_axis_extent = float(page.height if rotation in {90, 270} else page.width)
            ambiguous = _ambiguous_reading_order(reading_order_candidates, column_axis_extent, rotation)
            for order, candidate in enumerate(sorted(candidates, key=lambda item: _reading_order_key(item, rotation))):
                metadata = dict(candidate.get("metadata") or {})
                if ambiguous:
                    metadata["reading_order_ambiguous"] = True
                    _add_review(metadata, {
                        "code": "uncertain-reading-order",
                        "severity": "high",
                        "message": "Overlapping or multi-column geometry requires review before release.",
                    })
                records.append(ExtractionRecord(
                    page_number,
                    candidate["bbox"],
                    order,
                    text=candidate.get("text", ""),
                    font_size=candidate.get("font_size", 0.0),
                    bold=candidate.get("bold", False),
                    role_hint=candidate.get("role_hint"),
                    links=candidate.get("links", []),
                    table=candidate.get("table"),
                    form=candidate.get("form"),
                    asset=candidate.get("asset"),
                    alt=candidate.get("alt"),
                    metadata=metadata,
                ))

    records.sort(key=lambda item: (item.page, item.reading_order, item.bbox, item.text))
    # Record repeated normalized margin strings for book-profile furniture rules.
    margin_text = Counter(record.text for record in records if record.text and (record.bbox[1] < 72 or record.bbox[3] > 720))
    preflight["repeated_margin_candidates"] = sorted(text for text, count in margin_text.items() if count >= 3)
    return preflight, records
