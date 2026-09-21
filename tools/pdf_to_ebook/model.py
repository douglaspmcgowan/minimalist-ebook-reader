from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


def _canonical(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return _canonical(value.to_dict())
    if isinstance(value, dict):
        return {key: _canonical(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    return value


def stable_json_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically for byte-stable conversion output."""
    return (json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


@dataclass(frozen=True)
class Provenance:
    page: int
    bbox: tuple[float, float, float, float]
    reading_order: int

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Provenance":
        return cls(
            page=int(value["page"]),
            bbox=tuple(float(number) for number in value["bbox"]),
            reading_order=int(value["reading_order"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"page": self.page, "bbox": list(self.bbox), "reading_order": self.reading_order}


@dataclass(frozen=True)
class ExtractionRecord:
    page: int
    bbox: tuple[float, float, float, float]
    reading_order: int
    text: str = ""
    font_size: float = 0.0
    bold: bool = False
    role_hint: str | None = None
    links: list[dict[str, Any]] = field(default_factory=list)
    table: dict[str, Any] | None = None
    form: dict[str, Any] | None = None
    asset: str | None = None
    alt: str | None = None
    caption: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ExtractionRecord":
        allowed = {item.name for item in cls.__dataclass_fields__.values()}
        clean = {key: value[key] for key in value if key in allowed}
        clean["page"] = int(clean["page"])
        clean["reading_order"] = int(clean["reading_order"])
        clean["bbox"] = tuple(float(number) for number in clean["bbox"])
        clean["font_size"] = float(clean.get("font_size", 0))
        return cls(**clean)

    def provenance(self) -> Provenance:
        return Provenance(self.page, self.bbox, self.reading_order)

    def to_dict(self) -> dict[str, Any]:
        return _canonical(asdict(self))


@dataclass
class SemanticBlock:
    kind: str
    data: dict[str, Any]
    provenance: list[Provenance]
    confidence: float
    evidence: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": round(float(self.confidence), 4),
            "data": _canonical(self.data),
            "evidence": list(self.evidence),
            "kind": self.kind,
            "provenance": [source.to_dict() for source in self.provenance],
        }


@dataclass(frozen=True)
class ReviewItem:
    code: str
    severity: str
    page: int | None
    message: str
    approved: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _canonical(asdict(self))
