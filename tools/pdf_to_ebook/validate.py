from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .model import ExtractionRecord, ReviewItem, SemanticBlock


_READER_ASSET_PATH = re.compile(r"^(?:content-private|assets|images)/[A-Za-z0-9][A-Za-z0-9._/-]*(?:[?#][^\s]*)?$")
_READER_TARGET = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")


@dataclass
class ValidationReport:
    releasable: bool
    page_count: int
    covered_pages: list[int]
    missing_pages: list[int]
    unresolved_high_severity: int
    block_inventory: dict[str, int]
    unresolved_contents_targets: int = 0
    missing_text_tokens: list[str] = field(default_factory=list)
    items: list[ReviewItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "block_inventory": dict(sorted(self.block_inventory.items())),
            "covered_pages": self.covered_pages,
            "items": [item.to_dict() for item in self.items],
            "missing_pages": self.missing_pages,
            "missing_text_tokens": self.missing_text_tokens,
            "page_count": self.page_count,
            "releasable": self.releasable,
            "unresolved_contents_targets": self.unresolved_contents_targets,
            "unresolved_high_severity": self.unresolved_high_severity,
        }


def validate_release(
    blocks: Iterable[SemanticBlock],
    page_count: int,
    review_items: Iterable[ReviewItem] = (),
    intentionally_excluded_pages: Iterable[int] = (),
    reader_targets: Iterable[str] = (),
    page_targets: dict[int, str] | None = None,
    non_text_objects: Iterable[dict] = (),
    asset_root: str | Path | None = None,
    expected_source_tokens: Iterable[str] = (),
    extraction_records: Iterable[ExtractionRecord] = (),
) -> ValidationReport:
    materialized = list(blocks)
    extracted = list(extraction_records)
    supplied_items = list(review_items)
    generated_items = _extraction_review_items(extracted)
    extraction_approvals = [item for item in supplied_items if _is_extraction_approval(item)]
    items = [item for item in supplied_items if not _is_extraction_approval(item)]
    for approval in extraction_approvals:
        if not any(_approval_matches_finding(approval, finding) for finding in generated_items):
            items.append(ReviewItem(
                "invalid-extraction-approval",
                "high",
                approval.page,
                "Approved extraction finding does not match the generated finding scope.",
                details={
                    "disposition": approval.message,
                    "finding_id": approval.details.get("finding_id"),
                },
            ))
    for finding in generated_items:
        approval = next(
            (item for item in extraction_approvals if _approval_matches_finding(item, finding)),
            None,
        )
        if approval is None:
            items.append(finding)
            continue
        items.append(ReviewItem(
            finding.code,
            finding.severity,
            finding.page,
            finding.message,
            approved=True,
            details={**finding.details, "disposition": approval.message},
        ))
    covered: set[int] = set(int(page) for page in intentionally_excluded_pages)
    inventory: dict[str, int] = {}
    targets = {str(target) for target in reader_targets}
    page_target_map = {int(page): str(target) for page, target in (page_targets or {}).items()}
    prior_order: dict[int, int] = {}
    unresolved_contents_targets = 0
    assets: list[tuple[int | None, dict]] = []

    for position, block in enumerate(materialized):
        inventory[block.kind] = inventory.get(block.kind, 0) + 1
        if not block.provenance:
            items.append(ReviewItem("missing-provenance", "high", None, f"Block {position} has no source provenance."))
        if not block.evidence:
            items.append(ReviewItem("missing-evidence", "high", block.provenance[0].page if block.provenance else None, f"Block {position} has no classification evidence."))
        if not 0 <= block.confidence <= 1:
            items.append(ReviewItem("invalid-confidence", "high", block.provenance[0].page if block.provenance else None, f"Block {position} confidence is outside 0..1."))
        elif block.confidence < 0.7:
            review_code = (
                "ambiguous-table-continuation"
                if "ambiguous-table-continuation" in block.evidence
                else "conflicting-table-continuation"
                if "conflicting-table-continuation" in block.evidence
                else "low-confidence-structure"
            )
            items.append(ReviewItem(review_code, "high", block.provenance[0].page if block.provenance else None, f"Block {position} requires semantic review."))
        if block.kind == "table":
            headers = block.data.get("headers", [])
            rows = block.data.get("rows", [])
            column_count = len(headers) or (len(rows[0]) if rows else 0)
            if column_count == 0 or any(len(row) != column_count for row in rows):
                items.append(ReviewItem("invalid-table-shape", "high", block.provenance[0].page if block.provenance else None, f"Table block {position} has inconsistent columns."))
        if block.kind == "figure" and not str(block.data.get("alt") or "").strip():
            items.append(ReviewItem("missing-figure-alt", "high", block.provenance[0].page if block.provenance else None, f"Figure block {position} needs alternative text."))
        if block.kind == "figure":
            assets.append((block.provenance[0].page if block.provenance else None, block.data))
        if block.kind == "contents":
            for entry in block.data.get("entries", []):
                if not isinstance(entry, dict):
                    unresolved_contents_targets += 1
                    items.append(ReviewItem("unresolved-contents-target", "high", block.provenance[0].page if block.provenance else None, f"Contents block {position} has an invalid entry."))
                    continue
                target = entry.get("target")
                if not target:
                    try:
                        target = page_target_map.get(int(entry.get("target_page")))
                    except (TypeError, ValueError):
                        target = None
                if target and not _READER_TARGET.fullmatch(str(target)):
                    items.append(ReviewItem("invalid-reader-target", "high", block.provenance[0].page if block.provenance else None, f"Contents entry {entry.get('title')!r} has an unsafe reader target."))
                if not target or str(target) not in targets:
                    unresolved_contents_targets += 1
                    items.append(ReviewItem("unresolved-contents-target", "high", block.provenance[0].page if block.provenance else None, f"Contents entry {entry.get('title')!r} does not resolve to a reader target."))
        else:
            _validate_block_links(items, block, position, targets, page_target_map)
        if block.kind == "form":
            page = block.provenance[0].page if block.provenance else None
            fields = block.data.get("fields")
            rows = block.data.get("rows")
            worksheet = block.data.get("worksheet")
            if not str(block.data.get("title") or "").strip():
                items.append(ReviewItem("missing-form-title", "high", page, f"Form block {position} has no reader-visible title."))
            if isinstance(worksheet, dict) and isinstance(worksheet.get("rows"), list):
                items.append(ReviewItem("unsupported-nested-form-rows", "high", page, f"Form block {position} stores rows outside the reader's root-level schema."))
            valid_fields = [field for field in fields if isinstance(field, dict) and str(field.get("label") or "").strip()] if isinstance(fields, list) else []
            valid_rows = [row for row in rows if isinstance(row, dict) and str(row.get("label") or "").strip()] if isinstance(rows, list) else []
            if not valid_fields and not valid_rows:
                items.append(ReviewItem("missing-form-inventory", "high", page, f"Form block {position} has no valid root-level fields or worksheet rows."))
            for field in fields if isinstance(fields, list) else []:
                if not isinstance(field, dict) or not str(field.get("label") or "").strip():
                    items.append(ReviewItem("missing-form-field-label", "high", page, f"Form block {position} has an unlabelled field."))
            for row in rows if isinstance(rows, list) else []:
                if not isinstance(row, dict) or not str(row.get("label") or "").strip():
                    items.append(ReviewItem("missing-form-row-label", "high", page, f"Form block {position} has an unlabelled worksheet row."))
        for source in block.provenance:
            if source.page < 1 or source.page > page_count:
                items.append(ReviewItem("invalid-source-page", "high", source.page, f"Block {position} points outside the source."))
            else:
                covered.add(source.page)
            if len(source.bbox) != 4:
                items.append(ReviewItem("invalid-bbox", "high", source.page, f"Block {position} has an invalid source box."))
            previous = prior_order.get(source.page)
            if previous is not None and source.reading_order <= previous:
                items.append(ReviewItem("inconsistent-provenance-order", "high", source.page, f"Block {position} regresses or repeats reading order on source page {source.page}."))
            prior_order[source.page] = source.reading_order

    automatic_objects = [
        {
            "id": record.metadata.get("object_id"),
            "object_kind": record.metadata.get("object_kind"),
            "page": record.page,
            "bbox": list(record.bbox),
        }
        for record in extracted
        if record.role_hint == "non_text_object" or record.metadata.get("non_text_object")
    ]
    _validate_non_text_objects(items, materialized, [*automatic_objects, *list(non_text_objects)])
    _validate_assets(items, assets, asset_root)
    missing_text_tokens = _validate_text_coverage(items, materialized, expected_source_tokens)

    missing = [page for page in range(1, page_count + 1) if page not in covered]
    items.extend(ReviewItem("missing-page-coverage", "high", page, "Source page has no semantic or approved exclusion coverage.") for page in missing)
    unresolved = sum(1 for item in items if item.severity == "high" and not item.approved)
    return ValidationReport(
        releasable=unresolved == 0,
        page_count=page_count,
        covered_pages=sorted(covered),
        missing_pages=missing,
        unresolved_high_severity=unresolved,
        block_inventory=inventory,
        unresolved_contents_targets=unresolved_contents_targets,
        missing_text_tokens=missing_text_tokens,
        items=items,
    )


def _validate_non_text_objects(items: list[ReviewItem], blocks: list[SemanticBlock], objects: Iterable[dict]) -> None:
    materialized = list(objects)
    identifiers = Counter(
        identifier
        for obj in materialized
        if isinstance(obj, dict)
        for identifier in [_non_text_object_id(obj)]
        if identifier
    )
    for identifier, count in sorted(identifiers.items()):
        if count > 1:
            items.append(ReviewItem("duplicate-non-text-object-id", "high", None, f"Non-text object ID {identifier!r} appears {count} times."))
    for position, obj in enumerate(materialized):
        if not isinstance(obj, dict):
            items.append(ReviewItem("missing-non-text-object-disposition", "high", None, f"Non-text object {position} has no usable disposition."))
            continue
        page = obj.get("page")
        object_id = _non_text_object_id(obj)
        page = page if isinstance(page, int) and not isinstance(page, bool) else None
        bbox = obj.get("bbox")
        try:
            normalized_bbox = tuple(float(value) for value in bbox) if isinstance(bbox, (list, tuple)) and len(bbox) == 4 else None
            if normalized_bbox is not None and not all(math.isfinite(value) for value in normalized_bbox):
                normalized_bbox = None
        except (TypeError, ValueError):
            normalized_bbox = None
        if not object_id and (page is None or normalized_bbox is None):
            items.append(ReviewItem("missing-non-text-object-disposition", "high", page, f"Non-text object {position} lacks a stable ID or finite page geometry."))
            continue
        matched = any(
            block.kind in {"divider", "figure"}
            and (page is None or any(source.page == page for source in block.provenance))
            and (
                (
                    bool(object_id)
                    and object_id in tuple(
                        _normalize_non_text_object_id(block.data.get(key))
                        for key in ("id", "object_id", "object_name")
                    )
                )
                or (
                    normalized_bbox is not None
                    and any(source.page == page and tuple(source.bbox) == normalized_bbox for source in block.provenance)
                )
            )
            for block in blocks
        )
        approved = any(
            item.approved
            and item.code == "non-text-object-disposition"
            and (
                _normalize_non_text_object_id(item.details.get("object_id")) == object_id and (item.page is None or item.page == page)
                if object_id
                else item.page == page and _normalized_bbox(item.details.get("bbox")) == normalized_bbox
            )
            for item in items
        )
        if not matched and not approved:
            items.append(ReviewItem("missing-non-text-object-disposition", "high", page if isinstance(page, int) else None, f"Non-text object {object_id or position} lacks a semantic block or approved disposition."))


def _non_text_object_id(obj: dict) -> str | None:
    for key in ("id", "object_id", "object_name"):
        if key in obj:
            identifier = _normalize_non_text_object_id(obj.get(key))
            if identifier is not None:
                return identifier
    return None


def _normalize_non_text_object_id(value: object) -> str | None:
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        return None
    identifier = str(value).strip()
    return identifier if identifier else None


def _validate_block_links(
    items: list[ReviewItem],
    block: SemanticBlock,
    position: int,
    targets: set[str],
    page_target_map: dict[int, str],
) -> None:
    links = block.data.get("links")
    if not isinstance(links, list):
        return
    page = block.provenance[0].page if block.provenance else None
    for link_position, link in enumerate(links):
        if not isinstance(link, dict):
            items.append(ReviewItem("unresolved-link-target", "high", page, f"Block {position} link {link_position} is invalid."))
            continue
        if "bbox" in link and _normalized_bbox(link.get("bbox")) is None:
            items.append(ReviewItem("invalid-link-geometry", "high", page, f"Block {position} link {link_position} has invalid source geometry."))
        target = link.get("target")
        if not target:
            try:
                target = page_target_map.get(int(link.get("target_page")))
            except (TypeError, ValueError):
                target = None
        if target and not _READER_TARGET.fullmatch(str(target)):
            items.append(ReviewItem("invalid-reader-target", "high", page, f"Block {position} link {link_position} has an unsafe reader target."))
        if not target or str(target) not in targets:
            items.append(ReviewItem("unresolved-link-target", "high", page, f"Block {position} link {link_position} does not resolve to a reader target."))


def _normalized_bbox(value: object) -> tuple[float, float, float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        bbox = tuple(float(item) for item in value)
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(item) for item in bbox):
        return None
    return bbox


def _validate_assets(items: list[ReviewItem], figures: list[tuple[int | None, dict]], asset_root: str | Path | None) -> None:
    root = Path(asset_root).resolve() if asset_root is not None else None
    if figures and root is None:
        items.append(ReviewItem("missing-asset-root", "high", None, "Figure integrity requires an explicit asset root."))
    for page, data in figures:
        asset = data.get("asset") or data.get("src")
        if not isinstance(asset, str) or not asset.strip():
            items.append(ReviewItem("missing-asset", "high", page, "Figure has no asset path."))
            continue
        if not _READER_ASSET_PATH.fullmatch(asset) or ".." in asset or "\\" in asset or "//" in asset:
            items.append(ReviewItem("unsafe-reader-asset-path", "high", page, f"Figure asset {asset!r} is outside the reader's safe asset contract."))
            continue
        if root is None:
            continue
        filesystem_asset = re.split(r"[?#]", asset, maxsplit=1)[0]
        try:
            path = (root / filesystem_asset).resolve()
            path.relative_to(root)
        except (OSError, ValueError):
            items.append(ReviewItem("invalid-asset-path", "high", page, f"Figure asset {asset!r} escapes the asset root."))
            continue
        if not path.is_file():
            items.append(ReviewItem("missing-asset", "high", page, f"Figure asset {asset!r} is absent."))
            continue
        expected = data.get("sha256") or data.get("asset_sha256")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            items.append(ReviewItem("missing-asset-sha256", "high", page, f"Figure asset {asset!r} has no SHA-256."))
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual.lower() != expected.lower():
            items.append(ReviewItem("asset-sha256-mismatch", "high", page, f"Figure asset {asset!r} does not match its SHA-256."))


def _extraction_review_items(records: Iterable[ExtractionRecord]) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    for record in records:
        findings = record.metadata.get("review", []) if isinstance(record.metadata, dict) else []
        if isinstance(findings, dict):
            findings = [findings]
        if not isinstance(findings, (list, tuple)):
            findings = []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            details = {
                key: value
                for key, value in finding.items()
                if key not in {"approved", "code", "details", "message", "severity"}
            }
            if isinstance(finding.get("details"), dict):
                details.update(finding["details"])
            details.update({"bbox": list(record.bbox), "reading_order": record.reading_order})
            details["finding_id"] = extraction_finding_id(
                str(finding.get("code") or "extraction-review"),
                record.page,
                record.reading_order,
                record.bbox,
                details.get("object_id"),
                details.get("field_name"),
            )
            items.append(ReviewItem(
                code=str(finding.get("code") or "extraction-review"),
                severity=_extraction_review_severity(finding.get("severity")),
                page=record.page,
                message=str(finding.get("message") or "Extraction requires review."),
                approved=False,
                details=details,
            ))
    return items


def extraction_finding_id(
    code: str,
    page: int,
    reading_order: int,
    bbox: Iterable[object],
    object_id: object = None,
    field_name: object = None,
) -> str:
    identity = json.dumps(
        [
            str(code),
            str(page),
            str(reading_order),
            [str(value) for value in bbox],
            None if object_id is None else str(object_id),
            None if field_name is None else str(field_name),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _is_extraction_approval(item: ReviewItem) -> bool:
    return item.approved and isinstance(item.details.get("finding_id"), str)


def _approval_matches_finding(approval: ReviewItem, finding: ReviewItem) -> bool:
    if (
        approval.code != finding.code
        or approval.severity != finding.severity
        or approval.page != finding.page
        or str(approval.details.get("finding_id", "")).lower() != str(finding.details.get("finding_id", "")).lower()
        or approval.details.get("reading_order") != finding.details.get("reading_order")
        or approval.details.get("bbox") != finding.details.get("bbox")
    ):
        return False
    for key in ("object_id", "field_name"):
        if (key in approval.details) != (key in finding.details):
            return False
        if key in finding.details and approval.details[key] != finding.details[key]:
            return False
    return True


def _extraction_review_severity(value: object) -> str:
    severity = str(value or "high").strip().lower()
    return severity if severity in {"high", "medium", "low"} else "high"


def _validate_text_coverage(items: list[ReviewItem], blocks: Iterable[SemanticBlock], expected_tokens: Iterable[str]) -> list[str]:
    present: set[str] = set()
    for block in blocks:
        present.update(_tokens(block.data))
    missing = sorted({token.lower() for value in expected_tokens for token in _tokens(value)} - present)
    for token in missing:
        items.append(ReviewItem("missing-source-text-token", "high", None, f"Expected source token {token!r} has no semantic coverage."))
    return missing


_NON_TEXT_DATA_KEYS = {
    "asset", "asset_sha256", "id", "object_id", "object_name", "page", "sha256", "src", "target", "target_page",
}


def _tokens(value: object) -> list[str]:
    if isinstance(value, str):
        return re.findall(r"[\w]+", value.lower())
    if isinstance(value, dict):
        return [token for key, item in value.items() if key not in _NON_TEXT_DATA_KEYS for token in _tokens(item)]
    if isinstance(value, (list, tuple)):
        return [token for item in value for token in _tokens(item)]
    return []
