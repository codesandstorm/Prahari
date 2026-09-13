from __future__ import annotations
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ErrorBody(StrictModel):
    code: str
    message: str
    request_id: str | None = None


class SourceOut(StrictModel):
    reporting_month: date
    source_id: str | None
    coverage_class: str
    sha256: str | None
    schema_family: str | None


class SnapshotOut(StrictModel):
    reporting_month: date
    agency: str | None
    state: str | None
    sector: str | None
    project_observation_count: int | None
    months_since_first_observation: int | None
    progress_current: float | None
    progress_velocity: float | None
    expenditure_current: float | None
    expenditure_velocity: float | None
    cost_ratio: float | None
    source: SourceOut | None = None


class PredictionOut(StrictModel):
    prediction_id: str
    canonical_project_id: str
    as_of_month: date
    target: str
    horizon_months: int
    prediction_status: Literal["AVAILABLE", "ABSTAIN", "WITHHELD"]
    probability: float | None
    risk_band: Literal["LOW", "MEDIUM", "HIGH"] | None
    reliability_band: Literal["LOW", "MODERATE", "HIGH", "ABSTAIN"]
    reliability_reasons: list[str]
    data_quality_status: str
    review_priority: str | None
    contributors: list[dict]
    model_version: str
    feature_version: str
    target_version: str
    abstention_reason: str | None
    created_at: datetime


class ProjectSummary(StrictModel):
    canonical_project_id: str
    project_code: str | None
    canonical_name: str
    agency: str | None
    ministry: str | None
    sector: str | None
    state: str | None
    latest_reporting_month: date | None
    prediction: PredictionOut | None


class PageOut(StrictModel):
    items: list[ProjectSummary]
    page: int
    page_size: int
    total: int
    pages: int


class ProjectDetail(ProjectSummary):
    identity_method: str
    identity_status: str
    latest_snapshot: SnapshotOut | None
    data_trust: dict
    model_release: dict
    prediction_eligibility: dict
    officer_decision: dict
    implementation_watch: dict


class ReviewQueueOut(StrictModel):
    items: list[dict]
    status: str
    policy_version: str
    counts: dict[str, int]
    page: int
    page_size: int
    total: int
    pages: int


class HistoryOut(StrictModel):
    canonical_project_id: str
    observations: list[SnapshotOut]
    unavailable_months: list[SourceOut]
    interpolated: Literal[False] = False


class AssistantRequest(StrictModel):
    request_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.:-]+$")
    question: str = Field(min_length=3, max_length=2000)
    canonical_project_id: str | None = Field(default=None, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")

    @field_validator("question")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


class AssistantOut(StrictModel):
    request_id: str
    route: str
    answer: dict
    project_evidence_references: list[str]
    document_citations: list[dict]
    reliability_statement: str | None
    limitations: list[str]
    fallback_used: bool
    fallback_reason: str | None
    model_version: str
    rag_index_version: str | None
    latency_metadata: dict[str, float]


class ActorRequest(StrictModel):
    actor_type: Literal["SYSTEM","OFFICER","REVIEWER"] = "OFFICER"
    actor_id: str | None = Field(default=None,min_length=1,max_length=80,pattern=r"^[A-Za-z0-9_.:@-]+$")
    reason: str = Field(min_length=2,max_length=1000)

    @field_validator("reason")
    @classmethod
    def reason_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason must not be blank")
        return value.strip()


class DismissRequest(ActorRequest):
    reason: str = Field(min_length=2,max_length=1000)


class AssignmentRequest(StrictModel):
    assigned_to: str | None = Field(default=None,max_length=80,pattern=r"^[A-Za-z0-9_.:@-]+$")
    actor_type: Literal["SYSTEM","OFFICER","REVIEWER"] = "OFFICER"
    actor_id: str | None = Field(default=None,max_length=80,pattern=r"^[A-Za-z0-9_.:@-]+$")


class ReviewUpdateRequest(StrictModel):
    review_status: Literal["IN_PROGRESS","MONITORING","ACTION_REQUIRED","COMPLETE","CLOSED_NO_ACTION"]
    outcome: Literal["MONITOR_CONTINUED","DATA_VERIFIED","NO_ACTION_REQUIRED","FOLLOW_UP_REQUIRED","ISSUE_RESOLVED"] | None = None
    next_review_date: date | None = None
    recommended_follow_up: str | None = Field(default=None,max_length=1000)
    verification_status: Literal["VERIFIED","CORRECTED","SOURCE_PENDING","UNRESOLVED"] | None = None
    actor_type: Literal["SYSTEM","OFFICER","REVIEWER"] = "OFFICER"
    actor_id: str | None = Field(default=None,max_length=80,pattern=r"^[A-Za-z0-9_.:@-]+$")


class ReviewNoteRequest(StrictModel):
    text: str = Field(min_length=1,max_length=4000)
    note_type: Literal["OBSERVATION","VERIFICATION","FOLLOW_UP","RESOLUTION"]
    actor_type: Literal["SYSTEM","OFFICER","REVIEWER"] = "OFFICER"
    actor_id: str | None = Field(default=None,max_length=80,pattern=r"^[A-Za-z0-9_.:@-]+$")

    @field_validator("text")
    @classmethod
    def text_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("note text must not be blank")
        return value.strip()


class ReviewActionRequest(StrictModel):
    action_type: Literal["VERIFY_SOURCE","REVIEW_PROGRESS","REVIEW_MILESTONE","REVIEW_CLEARANCE","REVIEW_LAND_STATUS","REVIEW_TENDER_STATUS","MONITOR_NEXT_CYCLE","REQUEST_DATA_VERIFICATION","NO_ACTION_REQUIRED"]
    detail: str | None = Field(default=None,max_length=2000)
    actor_type: Literal["SYSTEM","OFFICER","REVIEWER"] = "OFFICER"
    actor_id: str | None = Field(default=None,max_length=80,pattern=r"^[A-Za-z0-9_.:@-]+$")
