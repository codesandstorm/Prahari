"""Strict evidence supplied to an explanation model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass(frozen=True)
class PrahariEvidence:
    canonical_project_id: str
    project_name: str | None
    as_of_month: str
    target: str
    horizon_months: int
    prediction_status: str
    calibrated_probability: float | None
    risk_band: str | None
    reliability_band: str
    reliability_reasons: list[str] = field(default_factory=list)
    data_quality_status: str = "UNKNOWN"
    review_priority: str | None = None
    contributors: list[str] = field(default_factory=list)
    trajectory_summary: str | None = None
    schedule_feasibility: str | None = None
    revision_history: str | None = None
    peer_summary: str | None = None
    rule_result: str | None = None
    source_provenance: list[dict[str, Any]] = field(default_factory=list)
    data_trust: dict[str, Any] = field(default_factory=dict)
    data_trust_reason_codes: list[str] = field(default_factory=list)
    model_release: dict[str, Any] = field(default_factory=dict)
    prediction_eligibility: dict[str, Any] = field(default_factory=dict)
    review_decision: dict[str, Any] = field(default_factory=dict)
    implementation_watch: dict[str, Any] = field(default_factory=dict)
    project_intelligence: dict[str, Any] = field(default_factory=dict)
    model_version: str = "UNKNOWN"
    feature_version: str = "UNKNOWN"
    target_version: str = "UNKNOWN"
    abstention_reason: str | None = None
    contractor: str | None = None
    agency: str | None = None
    cause: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrahariEvidence":
        if not isinstance(data, dict):
            raise ValueError("evidence must be an object")
        allowed = {item.name for item in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"unknown evidence fields: {sorted(unknown)}")
        required = {"canonical_project_id", "project_name", "as_of_month", "target", "horizon_months", "prediction_status", "calibrated_probability", "risk_band", "reliability_band"}
        missing = required - set(data)
        if missing:
            raise ValueError(f"missing evidence fields: {sorted(missing)}")
        obj = cls(**data)
        if obj.prediction_status not in {"AVAILABLE", "WITHHELD", "ABSTAIN"}:
            raise ValueError("invalid prediction_status")
        if obj.risk_band not in {None, "LOW", "MEDIUM", "HIGH"}:
            raise ValueError("invalid risk_band")
        if obj.reliability_band not in {"LOW", "MODERATE", "HIGH", "ABSTAIN"}:
            raise ValueError("invalid reliability_band")
        if obj.calibrated_probability is not None and not (0 <= obj.calibrated_probability <= 1):
            raise ValueError("calibrated_probability must be null or in [0,1]")
        if obj.prediction_status in {"WITHHELD", "ABSTAIN"} and (obj.calibrated_probability is not None or obj.risk_band is not None):
            raise ValueError("withheld/abstained prediction requires null probability and risk")
        if obj.horizon_months < 1 or len(obj.as_of_month) != 7:
            raise ValueError("invalid horizon or as_of_month")
        return obj

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
