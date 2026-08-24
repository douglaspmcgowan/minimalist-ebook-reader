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


def extract_pdf(
    path: str | Path,
    page_numbers: list[int] | tuple[int, ...] | None = None,
    include_preflight: bool = True,
) -> tuple[dict[str, Any], list[ExtractionRecord]]:
    """Extract positioned lines, tables, and image regions from a PDF."""
    requested = sorted(set(int(page) for page in page_numbers)) if page_numbers is not None else None
    preflight = preflight_pdf(path) if include_preflight else {
        "schema_version": 1,
        "requested_pages": requested or [],
    }
    records: list[ExtractionRecord] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            if requested is not None and page_number not in requested:
                continue
            order = 0
            table_boxes = [tuple(float(value) for value in table.bbox) for table in page.find_tables()]
            for table, bbox in zip(page.find_tables(), table_boxes):
                rows = table.extract() or []
                headers = [str(cell or "").strip() for cell in rows[0]] if rows else []
                body = [[str(cell or "").strip() for cell in row] for row in rows[1:]]
                records.append(ExtractionRecord(page_number, bbox, order, role_hint="table", table={"caption": None, "headers": headers, "rows": body}))
                order += 1

            words = page.extract_words(extra_attrs=["fontname", "size"], keep_blank_chars=False)
            for line in _group_words(words):
                x0 = min(float(word["x0"]) for word in line)
                top = min(float(word["top"]) for word in line)
                x1 = max(float(word["x1"]) for word in line)
                bottom = max(float(word["bottom"]) for word in line)
                if any(x0 >= box[0] and top >= box[1] and x1 <= box[2] and bottom <= box[3] for box in table_boxes):
                    continue
                sizes = [float(word.get("size") or 0) for word in line]
                fonts = [str(word.get("fontname") or "") for word in line]
                text = " ".join(str(word["text"]) for word in sorted(line, key=lambda item: float(item["x0"]))).strip()
                if text:
                    records.append(ExtractionRecord(page_number, (x0, top, x1, bottom), order, text=text, font_size=round(sum(sizes) / len(sizes), 3), bold=any("bold" in font.lower() for font in fonts)))
                    order += 1

            for image_number, image in enumerate(page.images, start=1):
                bbox = (float(image["x0"]), float(image["top"]), float(image["x1"]), float(image["bottom"]))
                records.append(ExtractionRecord(page_number, bbox, order, role_hint="figure", asset=f"assets/page-{page_number:04d}-figure-{image_number:02d}.png", metadata={"object_name": image.get("name")}))
                order += 1

    records.sort(key=lambda item: (item.page, item.reading_order, item.bbox, item.text))
    # Record repeated normalized margin strings for book-profile furniture rules.
    margin_text = Counter(record.text for record in records if record.text and (record.bbox[1] < 72 or record.bbox[3] > 720))
    preflight["repeated_margin_candidates"] = sorted(text for text, count in margin_text.items() if count >= 3)
    return preflight, records
