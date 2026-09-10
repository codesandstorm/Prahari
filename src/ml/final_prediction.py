"""Canonical PRAHARI S1/S2 prediction research and inference primitives.

All features are computed as-of the anchor month. Outcome construction is kept
separate and is never called by inference. Machine-derived outcomes remain
provisional until source-level human adjudication is complete.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Iterable

import numpy as np

from src.ml.feature_discovery_v2 import COMPACT_V2
from src.ml.provisional_research import approved_doc, clean, month_date, month_index, number, value

HORIZON_MONTHS = 3
TARGET_VERSION = {"S1": "S1-v1-machine-provisional", "S2": "S2-v1-machine-provisional"}
FEATURE_VERSION = "compact-v2.1-calendar-safe"
EXACT_IDENTITY = "RESOLVED_EXACT"
COMPLETED_VALUES = {"COMPLETED", "COMMISSIONED", "CLOSED"}


def add_month(month: str, offset: int) -> str:
    idx = month_index(month) + offset
    return f"{(idx - 1)//12:04d}-{(idx - 1)%12 + 1:02d}"


def exact_value(history: list[dict[str, str]], months_back: int, raw: str, fallback: str) -> float:
    wanted = add_month(history[-1]["reporting_month"], -months_back)
    row = next((r for r in history if r["reporting_month"] == wanted), None)
    return number(value(row or {}, raw, fallback)) if row else math.nan


def _finite(v: float) -> bool:
    return bool(np.isfinite(v))


def _ratio(a: float, b: float) -> float:
    return a / b if _finite(a) and _finite(b) and b > 0 else math.nan


def build_compact_v2(history: list[dict[str, str]]) -> dict[str, float]:
    """Build the exact ordered Compact V2 values using calendar-safe history."""
    if not history:
        raise ValueError("history is required")
    history = sorted(history, key=lambda r: r["reporting_month"])
    a = history[-1]
    original_cost = number(value(a, "original_cost_raw", "reported_original_cost"))
    expenditure = number(value(a, "cumulative_expenditure_raw", "reported_cumulative_expenditure"))
    progress = number(value(a, "physical_progress_raw", "reported_physical_progress"))
    approval = month_date(value(a, "approval_date_raw", "reported_approval_date"))
    original_doc = month_date(value(a, "original_target_doc_raw", "reported_original_target_doc"))
    approved = approved_doc(a)
    year, mon = map(int, a["reporting_month"].split("-")); as_of = date(year, mon, 1)
    planned = float((original_doc.year-approval.year)*12 + original_doc.month-approval.month) if approval and original_doc else math.nan
    age = float((as_of.year-approval.year)*12 + as_of.month-approval.month) if approval else math.nan
    remaining = float((approved.year-as_of.year)*12 + approved.month-as_of.month) if approved else math.nan
    remaining = max(remaining, 0.0) if _finite(remaining) else math.nan
    remaining_work = 100-progress if _finite(progress) and 0 <= progress <= 100 else math.nan
    required_velocity = _ratio(remaining_work, remaining)
    elapsed_fraction = _ratio(age, planned)

    prev_progress = exact_value(history, 1, "physical_progress_raw", "reported_physical_progress")
    prev_exp = exact_value(history, 1, "cumulative_expenditure_raw", "reported_cumulative_expenditure")
    progress_delta = progress-prev_progress if _finite(progress) and _finite(prev_progress) else math.nan
    exp_velocity = expenditure-prev_exp if _finite(expenditure) and _finite(prev_exp) else math.nan

    stagnant = 0
    cursor = progress
    for back in range(1, len(history)):
        prior = exact_value(history, back, "physical_progress_raw", "reported_physical_progress")
        if not (_finite(cursor) and _finite(prior)):
            break
        if cursor-prior <= 0:
            stagnant += 1; cursor = prior
        else:
            break

    revised_cost = number(value(a, "revised_cost_raw", "reported_revised_cost"))
    effective_cost = revised_cost if _finite(revised_cost) else original_cost
    values = {
        "log_original_cost": math.log1p(original_cost) if _finite(original_cost) and original_cost >= 0 else math.nan,
        "planned_duration_months": planned,
        "project_age_months": age,
        "expenditure_to_cost": _ratio(expenditure, original_cost),
        "physical_progress": progress,
        "physical_progress_missing": float(not _finite(progress)),
        "history_span_months": float(month_index(a["reporting_month"])-month_index(history[0]["reporting_month"])+1),
        "remaining_schedule_months": remaining,
        "required_future_velocity": required_velocity,
        "progress_vs_elapsed_gap": progress-100*elapsed_fraction if _finite(progress) and _finite(elapsed_fraction) else math.nan,
        "low_progress_near_deadline": float(_finite(progress) and _finite(remaining) and progress < 80 and remaining <= 6),
        "consecutive_stagnant": float(stagnant),
        "cumulative_cost_revision_pct": 100*(effective_cost-original_cost)/original_cost if _finite(effective_cost) and _finite(original_cost) and original_cost > 0 else math.nan,
        "expenditure_velocity": exp_velocity,
    }
    assert tuple(values) == COMPACT_V2
    return values


def _deteriorated(row: dict[str, str]) -> bool:
    original = month_date(value(row, "original_target_doc_raw", "reported_original_target_doc"))
    revised = month_date(value(row, "revised_doc_raw", "reported_revised_doc"))
    return bool(original and revised and revised > original)


def _completed(row: dict[str, str]) -> bool:
    status = clean(row.get("project_status_raw")).upper()
    progress = number(value(row, "physical_progress_raw", "reported_physical_progress"))
    return status in COMPLETED_VALUES or (_finite(progress) and progress >= 100)


@dataclass
class Candidate:
    canonical_project_id: str
    anchor_month: str
    target: str
    status: str
    primary_reason: str
    reasons: str
    baseline_approved_date: str | None
    event: int | None
    event_month: str | None
    event_approved_date: str | None
    date_change_months: int | None


def build_target(rows: list[dict[str, str]], coverage: dict[str, str], target: str, horizon: int = 3):
    """Return eligible feature cohort, complete candidate ledger, and event ledger."""
    if target not in {"S1", "S2"}: raise ValueError("target must be S1 or S2")
    by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows: by_project[row["canonical_project_id"]].append(row)
    cohort: list[dict[str, Any]]=[]; ledger: list[dict[str, Any]]=[]; events=[]
    for pid, obs in sorted(by_project.items()):
        obs.sort(key=lambda r:r["reporting_month"]); lookup={r["reporting_month"]:r for r in obs}
        for i, anchor in enumerate(obs):
            history=obs[:i+1]; future_months=[add_month(anchor["reporting_month"],j) for j in range(1,horizon+1)]
            reasons=[]
            if anchor.get("identity_status") != EXACT_IDENTITY: reasons.append("IDENTITY_NOT_EXACT")
            if approved_doc(anchor) is None: reasons.append("APPROVED_DATE_UNAVAILABLE")
            if _completed(anchor): reasons.append("COMPLETED_AT_T")
            prior=any(_deteriorated(r) for r in history)
            if target=="S1" and prior: reasons.append("PRIOR_DETERIORATION")
            if target=="S2" and not _deteriorated(anchor): reasons.append("NOT_DETERIORATED_AT_T")
            if any(coverage.get(m)!="PROJECT_LEVEL" for m in future_months): reasons.append("FUTURE_SOURCE_COVERAGE_GAP")
            if any(m not in lookup for m in future_months): reasons.append("FUTURE_PROJECT_OBSERVATION_MISSING")
            if len(history)<2: reasons.append("INSUFFICIENT_HISTORY")
            elif add_month(history[-2]["reporting_month"],1)!=anchor["reporting_month"]: reasons.append("PRIOR_MONTH_GAP")
            baseline=(month_date(value(anchor,"original_target_doc_raw","reported_original_target_doc")) if target=="S1" else approved_doc(anchor)); event_month=None; event_date=None
            if not reasons and baseline:
                for m in future_months:
                    candidate=approved_doc(lookup[m])
                    if candidate and candidate > baseline:
                        event_month=m; event_date=candidate; break
            event=int(event_month is not None) if not reasons else None
            change=((event_date.year-baseline.year)*12+event_date.month-baseline.month) if event_date and baseline else None
            status="ELIGIBLE" if not reasons else ("CENSORED" if any(r.startswith("FUTURE_") for r in reasons) else "EXCLUDED")
            item=asdict(Candidate(pid,anchor["reporting_month"],target,status,reasons[0] if reasons else "", "|".join(reasons),baseline.isoformat() if baseline else None,event,event_month,event_date.isoformat() if event_date else None,change))
            ledger.append(item)
            if not reasons:
                feature=build_compact_v2(history)
                cohort.append({"canonical_project_id":pid,"anchor_month":anchor["reporting_month"],"target":target,"event":event,"event_month":event_month,**feature})
                if event:
                    future_row=lookup[event_month]
                    anchor_original=month_date(value(anchor,"original_target_doc_raw","reported_original_target_doc"))
                    future_original=month_date(value(future_row,"original_target_doc_raw","reported_original_target_doc"))
                    suspicious=bool(change is not None and change>60) or (anchor_original and future_original and anchor_original!=future_original)
                    events.append({**item,"anchor_source_id":anchor.get("source_id"),"anchor_page":anchor.get("pdf_page_index"),"anchor_table":anchor.get("source_table"),"anchor_schema":anchor.get("schema_family"),"future_source_id":future_row.get("source_id"),"future_page":future_row.get("pdf_page_index"),"future_table":future_row.get("source_table"),"future_schema":future_row.get("schema_family"),"source_schema_transition":anchor.get("schema_family")!=future_row.get("schema_family"),"original_date_changed":bool(anchor_original and future_original and anchor_original!=future_original),"possible_correction_flag":suspicious})
    return cohort,ledger,events


def ledger_counts(ledger: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows=list(ledger)
    return {"status":dict(Counter(r["status"] for r in rows)),"primary_reason":dict(Counter(r["primary_reason"] for r in rows if r["primary_reason"]))}


def reliability(features: dict[str,float], identity_status: str, source_ok: bool, calibrated_confirmed: bool=False):
    reasons=[]
    if identity_status != EXACT_IDENTITY: return "WITHHELD",["IDENTITY_NOT_EXACT"]
    if not source_ok: return "WITHHELD",["SOURCE_COVERAGE_UNAVAILABLE"]
    span=features.get("history_span_months",math.nan)
    temporal=(features.get("consecutive_stagnant",math.nan),features.get("expenditure_velocity",math.nan))
    if not _finite(span) or span < 13: return "WITHHELD",["OUTSIDE_VALIDATED_HISTORY_REGIME"]
    if all(not _finite(v) for v in temporal): return "WITHHELD",["TEMPORAL_FEATURES_UNAVAILABLE"]
    missing=sum(not _finite(features[n]) for n in COMPACT_V2)
    if not calibrated_confirmed: reasons.append("CALIBRATION_NOT_INDEPENDENTLY_CONFIRMED")
    if missing > 4: reasons.append("HIGH_FEATURE_MISSINGNESS")
    if reasons: return "LOW",reasons
    return ("HIGH" if span>12 else "MODERATE"),[]
