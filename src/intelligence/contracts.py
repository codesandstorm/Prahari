"""Canonical backend/domain payload for project intelligence consumers."""
from __future__ import annotations
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, model_validator

CONTRACT_VERSION = "unified-project-intelligence-v1.0"


class IntelligenceMode(StrEnum):
    REAL_HISTORICAL = "REAL_HISTORICAL"
    SYNTHETIC_SANDBOX = "SYNTHETIC_SANDBOX"


class ProjectIntelligence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contract_version: str = CONTRACT_VERSION
    mode: IntelligenceMode
    data_origin: str
    identity: dict
    current_state: dict
    schedule_intelligence: dict
    cost_intelligence: dict
    implementation_watch: dict
    data_trust: dict
    reliability: dict
    peer_benchmark: dict
    risk_trend: dict
    officer_decision: dict
    alerts_summary: dict
    evidence_summary: list[dict]
    assistant_context: dict
    provenance: dict

    @model_validator(mode="after")
    def enforce_boundaries(self):
        expected = "SYNTHETIC_CUF_PROTOTYPE" if self.mode == IntelligenceMode.SYNTHETIC_SANDBOX else "HISTORICAL_FLASH_REPORT"
        if self.data_origin != expected: raise ValueError("mode and data_origin disagree")
        for section in (self.schedule_intelligence, self.cost_intelligence):
            if section.get("prediction_status") == "WITHHELD" and (section.get("probability") is not None or section.get("risk_band") is not None):
                raise ValueError("withheld predictions require null probability and risk band")
        if any(item.get("data_origin") != expected for item in self.evidence_summary):
            raise ValueError("mixed-origin evidence is prohibited")
        return self
