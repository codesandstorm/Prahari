from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class CoverageClass(str, enum.Enum):
    PROJECT_LEVEL = "PROJECT_LEVEL"
    AGGREGATE_ONLY = "AGGREGATE_ONLY"
    MISSING_SOURCE = "MISSING_SOURCE"


class Project(Base):
    __tablename__ = "projects"
    canonical_project_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_code: Mapped[str | None] = mapped_column(String(64))
    canonical_name: Mapped[str] = mapped_column(Text)
    agency: Mapped[str | None] = mapped_column(Text)
    ministry: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    identity_method: Mapped[str] = mapped_column(String(64))
    identity_status: Mapped[str] = mapped_column(String(64))
    data_origin: Mapped[str] = mapped_column(String(32), default="HISTORICAL_FLASH_REPORT", index=True)
    snapshots: Mapped[list["ProjectSnapshot"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class SourceReport(Base):
    __tablename__ = "source_reports"
    reporting_month: Mapped[date] = mapped_column(Date, primary_key=True)
    source_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    coverage_class: Mapped[str] = mapped_column(String(32))
    source_present: Mapped[bool] = mapped_column(Boolean)
    project_level_usable: Mapped[bool] = mapped_column(Boolean)
    official_project_count: Mapped[int | None] = mapped_column(Integer)
    schema_family: Mapped[str | None] = mapped_column(String(64))
    source_quality_status: Mapped[str | None] = mapped_column(String(32))
    sha256: Mapped[str | None] = mapped_column(String(64))
    __table_args__ = (CheckConstraint("coverage_class IN ('PROJECT_LEVEL','AGGREGATE_ONLY','MISSING_SOURCE')", name="ck_source_coverage"),)


class ProjectSnapshot(Base):
    __tablename__ = "project_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_project_id: Mapped[str] = mapped_column(ForeignKey("projects.canonical_project_id", ondelete="CASCADE"))
    reporting_month: Mapped[date] = mapped_column(ForeignKey("source_reports.reporting_month"))
    agency: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(Text)
    project_observation_count: Mapped[int | None] = mapped_column(Integer)
    months_since_first_observation: Mapped[int | None] = mapped_column(Integer)
    progress_current: Mapped[float | None] = mapped_column(Float)
    progress_velocity: Mapped[float | None] = mapped_column(Float)
    expenditure_current: Mapped[float | None] = mapped_column(Float)
    expenditure_velocity: Mapped[float | None] = mapped_column(Float)
    cost_ratio: Mapped[float | None] = mapped_column(Float)
    raw_features: Mapped[dict] = mapped_column(JSON, default=dict)
    project: Mapped[Project] = relationship(back_populates="snapshots")
    __table_args__ = (
        UniqueConstraint("canonical_project_id", "reporting_month", name="uq_project_snapshot_month"),
        Index("ix_snapshot_month_project", "reporting_month", "canonical_project_id"),
    )


class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    canonical_project_id: Mapped[str] = mapped_column(ForeignKey("projects.canonical_project_id", ondelete="CASCADE"), index=True)
    as_of_month: Mapped[date] = mapped_column(Date, index=True)
    target: Mapped[str] = mapped_column(String(100))
    horizon_months: Mapped[int] = mapped_column(Integer)
    prediction_status: Mapped[str] = mapped_column(String(16))
    probability: Mapped[float | None] = mapped_column(Float)
    risk_band: Mapped[str | None] = mapped_column(String(16))
    reliability_band: Mapped[str] = mapped_column(String(16))
    reliability_reasons: Mapped[list] = mapped_column(JSON, default=list)
    data_quality_status: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    review_priority: Mapped[str | None] = mapped_column(String(16))
    model_version: Mapped[str] = mapped_column(String(80))
    feature_version: Mapped[str] = mapped_column(String(80))
    target_version: Mapped[str] = mapped_column(String(80))
    abstention_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        UniqueConstraint("canonical_project_id", "as_of_month", "target", "horizon_months", "model_version", name="uq_prediction_version"),
        CheckConstraint("probability IS NULL OR (probability >= 0 AND probability <= 1)", name="ck_probability_range"),
        CheckConstraint("prediction_status NOT IN ('ABSTAIN','WITHHELD') OR (probability IS NULL AND risk_band IS NULL)", name="ck_abstention_nulls"),
    )


class PredictionContributor(Base):
    __tablename__ = "prediction_contributors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[str] = mapped_column(ForeignKey("predictions.prediction_id", ondelete="CASCADE"), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    feature_name: Mapped[str] = mapped_column(String(100))
    contribution: Mapped[float | None] = mapped_column(Float)
    direction: Mapped[str | None] = mapped_column(String(16))


class Alert(Base):
    __tablename__ = "alerts"
    alert_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    canonical_project_id: Mapped[str] = mapped_column(ForeignKey("projects.canonical_project_id"), index=True)
    prediction_id: Mapped[str | None] = mapped_column(ForeignKey("predictions.prediction_id"))
    status: Mapped[str] = mapped_column(String(20))
    policy_version: Mapped[str] = mapped_column(String(80))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    alert_type: Mapped[str] = mapped_column(String(40), default="IMPLEMENTATION_PRESSURE")
    severity: Mapped[str] = mapped_column(String(16), default="ATTENTION")
    data_origin: Mapped[str] = mapped_column(String(32), default="HISTORICAL_FLASH_REPORT", index=True)
    deduplication_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    reason_family: Mapped[str | None] = mapped_column(String(40))
    trigger_reason_codes: Mapped[list] = mapped_column(JSON, default=list)
    current_reason_codes: Mapped[list] = mapped_column(JSON, default=list)
    initial_evidence_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    latest_evidence_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    decision_state_at_open: Mapped[str | None] = mapped_column(String(40))
    decision_state_current: Mapped[str | None] = mapped_column(String(40))
    data_trust_at_open: Mapped[dict] = mapped_column(JSON, default=dict)
    data_trust_current: Mapped[dict] = mapped_column(JSON, default=dict)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_month: Mapped[str | None] = mapped_column(String(7))
    last_seen_month: Mapped[str | None] = mapped_column(String(7))
    consecutive_valid_cycles: Mapped[int] = mapped_column(Integer, default=1)
    watch_policy_version: Mapped[str | None] = mapped_column(String(80))
    decision_policy_version: Mapped[str | None] = mapped_column(String(80))
    review_policy_version: Mapped[str] = mapped_column(String(80), default="officer-review-v1.0")
    __table_args__ = (
        CheckConstraint("status IN ('NEW','ACKNOWLEDGED','IN_REVIEW','MONITORING','PERSISTENT','ESCALATED','RESOLVED','DISMISSED','REOPENED')",name="ck_alert_workflow_status"),
        CheckConstraint("severity IN ('INFO','ATTENTION','HIGH')",name="ck_alert_severity"),
        Index("ix_alert_mode_status_updated","data_origin","status","last_updated_at"),
    )


class AlertHistory(Base):
    __tablename__="alert_history"
    event_id: Mapped[str] = mapped_column(String(80),primary_key=True)
    alert_id: Mapped[str] = mapped_column(ForeignKey("alerts.alert_id",ondelete="CASCADE"),index=True)
    canonical_project_id: Mapped[str] = mapped_column(String(64),index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    actor_type: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str | None] = mapped_column(String(80))
    old_state: Mapped[str | None] = mapped_column(String(24))
    new_state: Mapped[str | None] = mapped_column(String(24))
    reason: Mapped[str] = mapped_column(Text)
    event_metadata: Mapped[dict] = mapped_column("metadata",JSON,default=dict)
    evidence_reference: Mapped[str | None] = mapped_column(String(120))
    __table_args__=(Index("ix_alert_history_timeline","alert_id","timestamp"),)


class OfficerReview(Base):
    __tablename__="officer_reviews"
    review_id: Mapped[str] = mapped_column(String(80),primary_key=True)
    canonical_project_id: Mapped[str] = mapped_column(String(64),index=True)
    alert_id: Mapped[str] = mapped_column(ForeignKey("alerts.alert_id",ondelete="CASCADE"),unique=True)
    data_origin: Mapped[str] = mapped_column(String(32),index=True)
    review_status: Mapped[str] = mapped_column(String(24),default="NOT_STARTED")
    assigned_to: Mapped[str | None] = mapped_column(String(80))
    priority: Mapped[str] = mapped_column(String(16),default="NORMAL")
    review_reason_codes: Mapped[list] = mapped_column(JSON,default=list)
    review_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    recommended_follow_up: Mapped[str | None] = mapped_column(Text)
    next_review_date: Mapped[date | None] = mapped_column(Date)
    outcome: Mapped[str | None] = mapped_column(String(40))
    verification_status: Mapped[str | None] = mapped_column(String(24))
    review_policy_version: Mapped[str] = mapped_column(String(80),default="officer-review-v1.0")
    __table_args__=(CheckConstraint("review_status IN ('NOT_STARTED','IN_PROGRESS','MONITORING','ACTION_REQUIRED','COMPLETE','CLOSED_NO_ACTION')",name="ck_review_status"),CheckConstraint("priority IN ('HIGH','NORMAL','LOW')",name="ck_review_priority"),Index("ix_review_queue","data_origin","review_status","priority"))


class ReviewNote(Base):
    __tablename__="review_notes"
    note_id: Mapped[str] = mapped_column(String(80),primary_key=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("officer_reviews.review_id",ondelete="CASCADE"),index=True)
    actor_type: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    text: Mapped[str] = mapped_column(Text)
    note_type: Mapped[str] = mapped_column(String(24))


class ReviewAction(Base):
    __tablename__="review_actions"
    action_id: Mapped[str] = mapped_column(String(80),primary_key=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("officer_reviews.review_id",ondelete="CASCADE"),index=True)
    actor_type: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    action_type: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str | None] = mapped_column(Text)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    dataset_hash: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(16))
    projects_loaded: Mapped[int] = mapped_column(Integer, default=0)
    snapshots_loaded: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
