"""Versioned typed contracts for PRAHARI Implementation Watch V1.

The input contract is deliberately wider than today's Flash Report data.  An
absent future CUF field remains absent; it is never defaulted to zero or false.
"""
from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


POLICY_VERSION = "implementation-watch-v1.0"
INPUT_CONTRACT_VERSION = "prahari-cuf-input-v1.0"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Availability(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNREPORTED = "UNREPORTED"
    STRUCTURALLY_UNAVAILABLE = "STRUCTURALLY_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SOURCE_GAP = "SOURCE_GAP"
    UNKNOWN = "UNKNOWN"


class SignalState(StrEnum):
    DETECTED = "DETECTED"
    NOT_DETECTED = "NOT_DETECTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    DATA_INSUFFICIENT = "DATA_INSUFFICIENT"
    UNRELIABLE = "UNRELIABLE"


class Milestone(StrictModel):
    label: str = Field(min_length=1)
    family: Literal["PROJECT_PLANNING", "LAND_ACQUISITION", "CLEARANCES_APPROVALS", "TENDER_PUBLISH", "TENDER_AWARD", "COMMISSIONING", "UNMAPPED"] = "UNMAPPED"
    applicable: bool | None = None
    planned_date: date | None = None
    revised_date: date | None = None
    actual_date: date | None = None
    scheduled_start_original: date | None = None
    scheduled_start_revised: date | None = None
    actual_start: date | None = None
    scheduled_finish_original: date | None = None
    scheduled_finish_revised: date | None = None
    actual_finish: date | None = None
    cost_original: float | None = Field(default=None, ge=0)
    cost_revised: float | None = Field(default=None, ge=0)
    cost_actual: float | None = Field(default=None, ge=0)


class LandStatus(StrictModel):
    applicable: bool | None = None
    required: float | None = Field(default=None, ge=0)
    acquired: float | None = Field(default=None, ge=0)
    unit: str | None = None
    remaining_pct: float | None = Field(default=None, ge=0, le=100)
    acquisition_complete: bool | None = None
    expected_completion_date: date | None = None

    @model_validator(mode="after")
    def compatible_amounts(self):
        if self.required is not None and self.acquired is not None and self.acquired > self.required:
            raise ValueError("land acquired cannot exceed land required")
        return self


class RowStatus(StrictModel):
    applicable: bool | None = None
    pending: bool | None = None
    availability_pct: float | None = Field(default=None, ge=0, le=100)


class Clearance(StrictModel):
    category: str = Field(min_length=1)
    applicable: bool | None = None
    status: Literal["PENDING", "APPROVED", "REJECTED", "UNKNOWN"] = "UNKNOWN"
    due_date: date | None = None


class Tender(StrictModel):
    tender_id: str | None = None
    applicable: bool | None = None
    publish_date: date | None = None
    award_date: date | None = None
    expected_award_date: date | None = None
    tender_name: str | None = None
    tender_type: Literal["GLOBAL", "LIMITED_RESTRICTED", "EOI", "EMPANELMENT", "OPEN", "UNKNOWN"] | None = None
    tender_portal_link: str | None = None
    bid_due_date: date | None = None

    @model_validator(mode="after")
    def chronology(self):
        if self.publish_date and self.award_date and self.award_date < self.publish_date:
            raise ValueError("tender award date precedes publication date")
        return self


class FundingContext(StrictModel):
    total_project_cost: float | None = Field(default=None, gt=0)
    total_funding: float | None = Field(default=None, gt=0)
    central_support: float | None = Field(default=None, ge=0)
    state_support: float | None = Field(default=None, ge=0)
    debt: float | None = Field(default=None, ge=0)
    internal_accruals: float | None = Field(default=None, ge=0)
    external_aid: float | None = Field(default=None, ge=0)
    ppp_equity: float | None = Field(default=None, ge=0)
    vgf_grant: float | None = Field(default=None, ge=0)
    funding_sources: list[str] | None = None
    land_cost: float | None = Field(default=None, ge=0)
    other_cost: float | None = Field(default=None, ge=0)
    capital_outlay: float | None = Field(default=None, ge=0)
    estimated_project_irr: float | None = None
    estimated_economic_irr: float | None = None


class PromoterContext(StrictModel):
    organization_type: str | None = None
    promoter_sponsor_type: str | None = None
    promoter_sponsor_name: str | None = None
    implementing_line_ministry: str | None = None
    division_department: str | None = None
    website_link: str | None = None


class CufProjectSnapshot(StrictModel):
    canonical_project_id: str = Field(min_length=1, max_length=64)
    as_of: date
    data_origin: Literal["HISTORICAL_FLASH_REPORT", "PAIMANA_CUF", "SYNTHETIC_CUF_PROTOTYPE"]
    source_refs: list[str] = Field(default_factory=list)
    source_availability: Availability = Availability.AVAILABLE
    provenance_complete: bool | None = None
    report_stale: bool | None = None
    report_month_missing: bool = False
    scheduled_physical_progress: float | None = Field(default=None, ge=0, le=100)
    actual_physical_progress: float | None = Field(default=None, ge=0, le=100)
    scheduled_financial_progress: float | None = Field(default=None, ge=0, le=100)
    actual_financial_progress: float | None = Field(default=None, ge=0, le=100)
    financial_progress_semantics_compatible: bool | None = None
    remaining_schedule_months: float | None = None
    required_future_velocity: float | None = None
    progress_vs_elapsed_gap: float | None = None
    low_progress_near_deadline: bool | None = None
    milestones: list[Milestone] | None = None
    land: LandStatus | None = None
    right_of_way: RowStatus | None = None
    clearances: list[Clearance] | None = None
    tenders: list[Tender] | None = None
    has_active_tenders: bool | None = None
    funding: FundingContext | None = None
    promoter_context: PromoterContext | None = None
    contract_version: Literal["prahari-cuf-input-v1.0"] = INPUT_CONTRACT_VERSION


class WatchSignal(StrictModel):
    code: str
    family: str
    status: SignalState
    severity: Literal["INFO", "LOW", "MEDIUM", "HIGH"]
    value: float | int | str | None = None
    unit: str | None = None
    as_of: date
    plain_language_explanation: str
    technical_explanation: dict[str, Any]
    source_available: bool
    source_refs: list[str]
    availability: Availability
    data_quality_state: str
    causal_claim: Literal[False] = False
    policy_version: str = POLICY_VERSION


class FamilyResult(StrictModel):
    family: str
    availability: Availability
    status: SignalState
    signals: list[WatchSignal]
    evidence: list[dict[str, Any]]
    limitations: list[str]


class ImplementationWatchResult(StrictModel):
    status: Literal["CLEAR", "WATCH", "ELEVATED", "DATA_INSUFFICIENT", "NOT_APPLICABLE"]
    as_of: date
    trend: Literal["NEW", "PERSISTENT", "WORSENING", "IMPROVING", "RESOLVED", "NOT_AVAILABLE"]
    reason_codes: list[str]
    signals: list[WatchSignal]
    families: list[FamilyResult]
    unavailable_families: list[str]
    data_quality_notes: list[str]
    data_origin: str
    policy_version: str = POLICY_VERSION
