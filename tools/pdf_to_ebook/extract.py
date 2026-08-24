from __future__ import annotations

import hashlib
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
            pages.append({
                "page": number,
                "width": round(float(page.width), 3),
                "height": round(float(page.height), 3),
                "characters": len(text),
                "images": len(page.images),
                "tables": len(tables),
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
            field_type = {"/Tx": "text", "/Btn": "button", "/Ch": "choice", "/Sig": "signature"}.get(str(_inherited_annotation_value(annotation, "/FT") or ""), "unknown")
            widgets.append({
                "bbox": bbox,
                "name": name,
                "field": {
                    "name": name,
                    "type": field_type,
                    "value": str(_inherited_annotation_value(annotation, "/V") or ""),
                    "required": bool(int(_inherited_annotation_value(annotation, "/Ff") or 0) & 2),
                },
            })
    return links, widgets


def _ambiguous_reading_order(candidates: list[dict[str, Any]], page_width: float) -> bool:
    text = [candidate for candidate in candidates if candidate["text"]]
    if len(text) >= 4:
        ordered = sorted(text, key=lambda item: item["bbox"][0])
        gaps = [(ordered[index + 1]["bbox"][0] - item["bbox"][0], index) for index, item in enumerate(ordered[:-1])]
        gap, index = max(gaps, default=(0.0, -1))
        if gap >= max(72.0, page_width * 0.15):
            left, right = ordered[:index + 1], ordered[index + 1:]
            if len(left) >= 2 and len(right) >= 2:
                left_top, left_bottom = min(item["bbox"][1] for item in left), max(item["bbox"][3] for item in left)
                right_top, right_bottom = min(item["bbox"][1] for item in right), max(item["bbox"][3] for item in right)
                if max(left_top, right_top) < min(left_bottom, right_bottom):
                    return True
    return any(
        _intersection(first["bbox"], second["bbox"])
        for index, first in enumerate(candidates)
        for second in candidates[index + 1:]
    )


def _figure_asset(page: Any, bbox: tuple[float, float, float, float], output_dir: Path | None, page_number: int, figure_number: int) -> tuple[str | None, dict[str, Any]]:
    filename = Path("assets") / f"page-{page_number:04d}-figure-{figure_number:02d}.png"
    metadata: dict[str, Any] = {}
    if output_dir is None:
        metadata["review"] = [{"code": "figure-asset-unmaterialized", "severity": "high", "message": "Figure requires an explicit asset output directory."}]
        return None, metadata
    try:
        destination = output_dir / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        page.crop(bbox).to_image(resolution=144).save(destination, format="PNG")
        metadata["asset_sha256"] = _sha256(destination)
        return filename.as_posix(), metadata
    except (OSError, ValueError) as error:
        metadata["review"] = [{"code": "figure-asset-unmaterialized", "severity": "high", "message": str(error)}]
        return None, metadata


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

            words = page.extract_words(extra_attrs=["fontname", "size"], keep_blank_chars=False)
            for line in _group_words(words):
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
                            "links": [{"target_page": link["target_page"]} for link in links if _intersection(bbox, link["bbox"])],
                        })

            for image_number, image in enumerate(page.images, start=1):
                bbox = (float(image["x0"]), float(image["top"]), float(image["x1"]), float(image["bottom"]))
                asset, metadata = _figure_asset(page, bbox, assets, page_number, image_number)
                metadata["object_name"] = image.get("name")
                candidates.append({"bbox": bbox, "text": "", "role_hint": "figure", "asset": asset, "metadata": metadata})

            for widget in widgets:
                candidates.append({
                    "bbox": widget["bbox"],
                    "text": "",
                    "role_hint": "form",
                    "form": {"title": widget["name"], "instructions": "", "fields": [widget["field"]]},
                    "metadata": {"widget_name": widget["name"]},
                })

            ambiguous = _ambiguous_reading_order(candidates, float(page.width))
            for order, candidate in enumerate(sorted(candidates, key=lambda item: (item["bbox"][1], item["bbox"][0], item["bbox"][3], item["bbox"][2], item.get("role_hint") or ""))):
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
                    metadata=metadata,
                ))

    records.sort(key=lambda item: (item.page, item.reading_order, item.bbox, item.text))
    # Record repeated normalized margin strings for book-profile furniture rules.
    margin_text = Counter(record.text for record in records if record.text and (record.bbox[1] < 72 or record.bbox[3] > 720))
    preflight["repeated_margin_candidates"] = sorted(text for text, count in margin_text.items() if count >= 3)
    return preflight, records
