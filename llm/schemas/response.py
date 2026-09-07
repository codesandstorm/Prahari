"""Structured, auditable explanation response."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass(frozen=True)
class PrahariResponse:
    summary: str
    evidence_points: list[str] = field(default_factory=list)
    reliability_explanation: str = ""
    recommended_review_areas: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    source_references: list[str] = field(default_factory=list)
    unsupported_question: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrahariResponse":
        if not isinstance(data, dict):
            raise ValueError("response must be an object")
        allowed = {item.name for item in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"unknown response fields: {sorted(unknown)}")
        required = allowed
        missing = required - set(data)
        if missing:
            raise ValueError(f"missing response fields: {sorted(missing)}")
        for key in ("evidence_points", "recommended_review_areas", "limitations", "source_references"):
            if not isinstance(data[key], list) or not all(isinstance(x, str) for x in data[key]):
                raise ValueError(f"{key} must be a list of strings")
        if not isinstance(data["summary"], str) or not isinstance(data["reliability_explanation"], str) or not isinstance(data["unsupported_question"], bool):
            raise ValueError("invalid response field type")
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
