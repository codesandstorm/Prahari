"""Validated behavioral benchmark case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .evidence import PrahariEvidence


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    category: str
    description: str
    evidence: PrahariEvidence
    question: str
    expected_behavior: list[str]
    forbidden_claims: list[str]
    required_concepts: list[str]
    optional_allowed_concepts: list[str]
    automatic_checks: list[dict[str, Any]]
    human_review_required: bool
    severity: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkCase":
        required = {"case_id", "category", "description", "evidence", "question", "expected_behavior", "forbidden_claims", "required_concepts", "optional_allowed_concepts", "automatic_checks", "human_review_required", "severity"}
        if set(data) != required:
            raise ValueError(f"case fields differ: missing={sorted(required-set(data))}, unknown={sorted(set(data)-required)}")
        if data["severity"] not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise ValueError("invalid severity")
        if not data["case_id"] or not data["automatic_checks"]:
            raise ValueError("case_id and automatic_checks are required")
        return cls(**{**data, "evidence": PrahariEvidence.from_dict(data["evidence"])})
