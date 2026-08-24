from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .model import ReviewItem, SemanticBlock


@dataclass
class ValidationReport:
    releasable: bool
    page_count: int
    covered_pages: list[int]
    missing_pages: list[int]
    unresolved_high_severity: int
    block_inventory: dict[str, int]
    items: list[ReviewItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "block_inventory": dict(sorted(self.block_inventory.items())),
            "covered_pages": self.covered_pages,
            "items": [item.to_dict() for item in self.items],
            "missing_pages": self.missing_pages,
            "page_count": self.page_count,
            "releasable": self.releasable,
            "unresolved_high_severity": self.unresolved_high_severity,
        }


def validate_release(
    blocks: Iterable[SemanticBlock],
    page_count: int,
    review_items: Iterable[ReviewItem] = (),
    intentionally_excluded_pages: Iterable[int] = (),
) -> ValidationReport:
    materialized = list(blocks)
    items = list(review_items)
    covered: set[int] = set(int(page) for page in intentionally_excluded_pages)
    inventory: dict[str, int] = {}

    for position, block in enumerate(materialized):
        inventory[block.kind] = inventory.get(block.kind, 0) + 1
        if not block.provenance:
            items.append(ReviewItem("missing-provenance", "high", None, f"Block {position} has no source provenance."))
        if not block.evidence:
            items.append(ReviewItem("missing-evidence", "high", block.provenance[0].page if block.provenance else None, f"Block {position} has no classification evidence."))
        if not 0 <= block.confidence <= 1:
            items.append(ReviewItem("invalid-confidence", "high", block.provenance[0].page if block.provenance else None, f"Block {position} confidence is outside 0..1."))
        elif block.confidence < 0.7:
            items.append(ReviewItem("low-confidence-structure", "high", block.provenance[0].page if block.provenance else None, f"Block {position} requires semantic review."))
        if block.kind == "table":
            headers = block.data.get("headers", [])
            rows = block.data.get("rows", [])
            column_count = len(headers) or (len(rows[0]) if rows else 0)
            if column_count == 0 or any(len(row) != column_count for row in rows):
                items.append(ReviewItem("invalid-table-shape", "high", block.provenance[0].page if block.provenance else None, f"Table block {position} has inconsistent columns."))
        if block.kind == "figure" and not str(block.data.get("alt") or "").strip():
            items.append(ReviewItem("missing-figure-alt", "high", block.provenance[0].page if block.provenance else None, f"Figure block {position} needs alternative text."))
        for source in block.provenance:
            if source.page < 1 or source.page > page_count:
                items.append(ReviewItem("invalid-source-page", "high", source.page, f"Block {position} points outside the source."))
            else:
                covered.add(source.page)
            if len(source.bbox) != 4:
                items.append(ReviewItem("invalid-bbox", "high", source.page, f"Block {position} has an invalid source box."))

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
        items=items,
    )
