"""Versioned, fail-closed primitives for PRAHARI Prediction Research V2.

This module never writes V1 artifacts and never mutates raw sources.  Machine
targets produced here remain provisional until the separate human-transfer
gate is complete.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np

from src.ml.final_prediction import Candidate, _completed, _deteriorated, _finite, _ratio, add_month, exact_value
from src.ml.provisional_research import approved_doc, month_date, month_index, number, value
from src.pipeline.build_mixed_coverage_dataset import discover_table, extract_project_month, sha256

V2_VERSION = "prediction-research-v2.0"
BASIC_LONG_HISTORY_V1 = (
    "log_original_cost", "planned_duration_months", "project_age_months",
    "expenditure_to_cost", "history_span_months", "remaining_schedule_months",
    "cumulative_cost_revision_pct", "expenditure_velocity",
)
HISTORICAL_MONTHS = tuple(f"{y:04d}-{m:02d}" for y, m in
                          [(2022, m) for m in range(8, 13)] + [(2023, m) for m in range(1, 7)])
RECOVERY = {"2024-08": "FlashReport_2024_08 (2).pdf", "2024-09": "FlashReport_2024_09 (2).pdf"}
EXPECTED_COUNTS = {"2022-08":1526,"2022-09":1529,"2022-10":1521,"2022-11":1476,"2022-12":1438,
                   "2023-01":1454,"2023-02":1418,"2023-03":1449,"2023-04":1605,"2023-05":1681,
                   "2023-06":1643,"2024-08":1783,"2024-09":1792}
PLANNED_FOLDS = {
    "F1": ("2023-04", "2023-08"), "F2": ("2024-06", "2024-10"),
    "F3": ("2025-03", "2025-09"), "F4": ("2025-10", "2026-03"),
}


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    rows = list(rows); path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fields or (rows[0].keys() if rows else ()))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore"); writer.writeheader(); writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle))


def file_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_basic_long_history(history: list[dict[str, str]]) -> dict[str, float]:
    if not history: raise ValueError("history is required")
    history = sorted(history, key=lambda row: row["reporting_month"]); anchor = history[-1]
    original_cost = number(value(anchor, "original_cost_raw", "reported_original_cost"))
    expenditure = number(value(anchor, "cumulative_expenditure_raw", "reported_cumulative_expenditure"))
    approval = month_date(value(anchor, "approval_date_raw", "reported_approval_date"))
    original_doc = month_date(value(anchor, "original_target_doc_raw", "reported_original_target_doc"))
    effective_doc = approved_doc(anchor)
    year, month = map(int, anchor["reporting_month"].split("-")); as_of = date(year, month, 1)
    planned = float((original_doc.year-approval.year)*12 + original_doc.month-approval.month) if approval and original_doc else math.nan
    age = float((as_of.year-approval.year)*12 + as_of.month-approval.month) if approval else math.nan
    remaining = float((effective_doc.year-as_of.year)*12 + effective_doc.month-as_of.month) if effective_doc else math.nan
    remaining = max(remaining, 0.0) if _finite(remaining) else math.nan
    previous_exp = exact_value(history, 1, "cumulative_expenditure_raw", "reported_cumulative_expenditure")
    revised_cost = number(value(anchor, "revised_cost_raw", "reported_revised_cost"))
    effective_cost = revised_cost if _finite(revised_cost) else original_cost
    result = {
        "log_original_cost": math.log1p(original_cost) if _finite(original_cost) and original_cost >= 0 else math.nan,
        "planned_duration_months": planned, "project_age_months": age,
        "expenditure_to_cost": _ratio(expenditure, original_cost),
        "history_span_months": float(month_index(anchor["reporting_month"])-month_index(history[0]["reporting_month"])+1),
        "remaining_schedule_months": remaining,
        "cumulative_cost_revision_pct": 100*(effective_cost-original_cost)/original_cost if _finite(effective_cost) and _finite(original_cost) and original_cost > 0 else math.nan,
        "expenditure_velocity": expenditure-previous_exp if _finite(expenditure) and _finite(previous_exp) else math.nan,
    }
    assert tuple(result) == BASIC_LONG_HISTORY_V1
    return result


def build_research_target(rows: list[dict[str, str]], coverage: dict[str, str], target: str, horizon: int,
                          feature_builder: Callable[[list[dict[str, str]]], dict[str, float]], feature_version: str):
    if target not in {"S1", "S2"} or horizon not in {3, 6, 12}: raise ValueError("unsupported target/horizon")
    by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows: by_project[row["canonical_project_id"]].append(row)
    cohort=[]; ledger=[]; events=[]
    for pid, observations in sorted(by_project.items()):
        observations.sort(key=lambda row: row["reporting_month"]); lookup={row["reporting_month"]:row for row in observations}
        for index, anchor in enumerate(observations):
            history=observations[:index+1]; future=[add_month(anchor["reporting_month"], offset) for offset in range(1,horizon+1)]
            reasons=[]
            if anchor.get("identity_status") != "RESOLVED_EXACT": reasons.append("IDENTITY_NOT_EXACT")
            if approved_doc(anchor) is None: reasons.append("APPROVED_DATE_UNAVAILABLE")
            if _completed(anchor): reasons.append("COMPLETED_AT_T")
            prior=any(_deteriorated(row) for row in history)
            if target == "S1" and prior: reasons.append("PRIOR_DETERIORATION")
            if target == "S2" and not _deteriorated(anchor): reasons.append("NOT_DETERIORATED_AT_T")
            if any(coverage.get(month) != "PROJECT_LEVEL" for month in future): reasons.append("FUTURE_SOURCE_COVERAGE_GAP")
            if any(month not in lookup for month in future): reasons.append("FUTURE_PROJECT_OBSERVATION_MISSING")
            if len(history) < 2: reasons.append("INSUFFICIENT_HISTORY")
            elif add_month(history[-2]["reporting_month"], 1) != anchor["reporting_month"]: reasons.append("PRIOR_MONTH_GAP")
            original_baseline=month_date(value(anchor,"original_target_doc_raw","reported_original_target_doc"))
            baseline=original_baseline if target=="S1" else approved_doc(anchor)
            event_month=event_date=None
            if not reasons and baseline:
                future_rows=[lookup[month] for month in future]
                future_originals=[month_date(value(row,"original_target_doc_raw","reported_original_target_doc")) for row in future_rows]
                if any(item != original_baseline for item in future_originals):
                    reasons.append("ORIGINAL_COMPLETION_BASELINE_CHANGED")
                approved_sequence=[approved_doc(anchor),*(approved_doc(row) for row in future_rows)]
                if any(left and right and right < left for left,right in zip(approved_sequence,approved_sequence[1:])):
                    reasons.append("APPROVED_DATE_REVERSAL_WITHIN_HORIZON")
            if not reasons and baseline:
                for month in future:
                    candidate=month_date(value(lookup[month],"revised_doc_raw","reported_revised_doc"))
                    if candidate and candidate > baseline: event_month,event_date=month,candidate; break
            event=int(event_month is not None) if not reasons else None
            change=((event_date.year-baseline.year)*12+event_date.month-baseline.month) if event_date and baseline else None
            status="ELIGIBLE" if not reasons else ("CENSORED" if any(reason.startswith("FUTURE_") for reason in reasons) else "EXCLUDED")
            item=asdict(Candidate(pid,anchor["reporting_month"],target,status,reasons[0] if reasons else "","|".join(reasons),baseline.isoformat() if baseline else None,event,event_month,event_date.isoformat() if event_date else None,change))
            item.update(horizon_months=horizon,target_version=f"{target}-{horizon}m-v3-explicit-revised-machine-provisional",feature_version=feature_version)
            ledger.append(item)
            if not reasons:
                cohort.append({"canonical_project_id":pid,"anchor_month":anchor["reporting_month"],"target":target,"horizon_months":horizon,"event":event,"event_month":event_month,**feature_builder(history)})
                if event:
                    future_row=lookup[event_month]
                    events.append({**item,"anchor_source_id":anchor.get("source_id"),"anchor_page":anchor.get("pdf_page_index"),"anchor_table":anchor.get("source_table"),"anchor_schema":anchor.get("schema_family"),"future_source_id":future_row.get("source_id"),"future_page":future_row.get("pdf_page_index"),"future_table":future_row.get("source_table"),"future_schema":future_row.get("schema_family")})
    return cohort,ledger,events


def restrict_feature_anchors(cohort,ledger,events,compatible: set[tuple[str,str]]):
    """Restrict feature anchors after, never before, longitudinal target truth."""
    keep=lambda row:(row["canonical_project_id"],row["anchor_month"]) in compatible
    return [r for r in cohort if keep(r)],[r for r in ledger if keep(r)],[r for r in events if keep(r)]


def expanding_folds(cohort: list[dict[str, Any]], horizon: int, minimums=(1000,300,30)) -> list[dict[str, Any]]:
    folds=[]
    for fold,(start,end) in PLANNED_FOLDS.items():
        test=[row for row in cohort if start <= row["anchor_month"] <= end]
        train=[row for row in cohort if add_month(row["anchor_month"],horizon) < start]
        projects=len({row["canonical_project_id"] for row in test}); events=sum(int(row["event"]) for row in test)
        admitted=len(test)>=minimums[0] and projects>=minimums[1] and events>=minimums[2]
        folds.append({"fold_id":fold,"test_start":start,"test_end":end,"horizon_months":horizon,
                      "train_rows":len(train),"test_rows":len(test),"test_projects":projects,"test_events":events,
                      "admission_status":"ADMITTED" if admitted else "DESCRIPTIVE_ONLY",
                      "admission_reason":"" if admitted else "PREDECLARED_MINIMUM_NOT_MET",
                      "latest_train_anchor":max((row["anchor_month"] for row in train),default="")})
    return folds


def rolling_folds(cohort: list[dict[str, Any]], horizon: int, window_months: int=12) -> list[dict[str, Any]]:
    """Secondary sensitivity folds with a fixed, mature training window."""
    folds=[]
    for row in expanding_folds(cohort,horizon):
        cutoff=add_month(row["test_start"],-horizon-1); start=add_month(cutoff,-window_months+1)
        train=[item for item in cohort if start <= item["anchor_month"] <= cutoff]
        folds.append({**row,"training_window_start":start,"training_window_end":cutoff,"train_rows":len(train),
                      "analysis_role":"SECONDARY_SENSITIVITY_ONLY"})
    return folds


def population_stability_index(reference: Iterable[float], current: Iterable[float], bins: int=10) -> float:
    """Deterministic PSI diagnostic; it is not a causal drift claim."""
    ref=np.asarray(list(reference),dtype=float); cur=np.asarray(list(current),dtype=float)
    ref=ref[np.isfinite(ref)]; cur=cur[np.isfinite(cur)]
    if len(ref)<2 or len(cur)<2: return math.nan
    edges=np.unique(np.quantile(ref,np.linspace(0,1,bins+1)))
    if len(edges)<3: return 0.0
    edges[0],edges[-1]=-np.inf,np.inf
    ref_hist=np.histogram(ref,bins=edges)[0]/len(ref); cur_hist=np.histogram(cur,bins=edges)[0]/len(cur)
    ref_hist=np.clip(ref_hist,1e-6,None); cur_hist=np.clip(cur_hist,1e-6,None)
    return float(np.sum((cur_hist-ref_hist)*np.log(cur_hist/ref_hist)))


def equal_soft_vote(probabilities: Iterable[Iterable[float]]) -> np.ndarray:
    matrix=np.asarray(list(probabilities),dtype=float)
    if matrix.ndim != 2 or not matrix.shape[0]: raise ValueError("model probability matrix required")
    if not np.isfinite(matrix).all() or ((matrix < 0) | (matrix > 1)).any(): raise ValueError("probabilities must be finite in [0,1]")
    return matrix.mean(axis=0)


def cluster_bootstrap_indices(project_ids: list[str], replicates: int=2000, seed: int=26103) -> list[np.ndarray]:
    groups=defaultdict(list)
    for index,pid in enumerate(project_ids): groups[pid].append(index)
    projects=np.asarray(sorted(groups)); rng=np.random.default_rng(seed); result=[]
    for _ in range(replicates):
        sampled=rng.choice(projects,size=len(projects),replace=True)
        result.append(np.asarray([idx for pid in sampled for idx in groups[str(pid)]],dtype=int))
    return result


def validate_transfer_rows(rows: list[dict[str, str]], manifest: dict[str, Any]) -> list[str]:
    errors=[]; expected=manifest.get("evidence_hashes",{})
    required=("reviewer","manual_label","confidence","evidence_verified","source_page_verified","identity_verified","review_timestamp")
    evidence_fields=manifest.get("evidence_fields",[])
    for row in rows:
        review_id=row.get("review_id",""); payload="|".join(str(row.get(field,"")) for field in evidence_fields)
        if hashlib.sha256(payload.encode()).hexdigest()!=expected.get(review_id): errors.append(f"{review_id}: EVIDENCE_TAMPERED")
        populated=any(row.get(field,"").strip() for field in required)
        if populated:
            for field in required:
                if not row.get(field,"").strip(): errors.append(f"{review_id}: MISSING_{field.upper()}")
            if row.get("manual_label") in {"CORRECTION","INSUFFICIENT_EVIDENCE","OTHER"} and not row.get("review_notes","").strip(): errors.append(f"{review_id}: NOTES_REQUIRED")
            if row.get("manual_label") not in set(manifest.get("allowed_manual_labels",[])): errors.append(f"{review_id}: INVALID_MANUAL_LABEL")
            if row.get("confidence") not in {"HIGH","MEDIUM","LOW"}: errors.append(f"{review_id}: INVALID_CONFIDENCE")
            for field in ("evidence_verified","source_page_verified","identity_verified"):
                if row.get(field) not in {"YES","NO"}: errors.append(f"{review_id}: INVALID_{field.upper()}")
            try: date.fromisoformat(row.get("review_timestamp","")[:10])
            except ValueError: errors.append(f"{review_id}: INVALID_REVIEW_TIMESTAMP")
    return errors


def source_path(raw_root: Path, month: str) -> Path:
    if month in RECOVERY: return raw_root / "candidate_recovery" / "2024" / RECOVERY[month]
    return raw_root / month[:4] / f"FlashReport_{month.replace('-', '_')}.pdf"


def normalize_new_rows(rows: list[dict[str, Any]], id_map: dict[str,str]) -> list[dict[str, Any]]:
    for row in rows:
        code=str(row.get("project_code_raw","")).strip(); row["canonical_project_id"]=id_map.get(code,f"PRH-{code}")
        row["project_code"]=code; row["identity_status"]="RESOLVED_EXACT"; row["identity_method"]="EXACT_AUTHORITATIVE_PROJECT_CODE"
        row["reported_project_name"]=row.get("project_name_raw",""); row["reported_agency"]=row.get("agency_raw","")
        row["reported_state"]=row.get("state_raw",""); row["reported_approval_date"]=row.get("approval_date_raw","")
        row["reported_original_target_doc"]=row.get("original_target_doc_raw",""); row["reported_revised_doc"]=row.get("revised_doc_raw","")
        row["reported_original_cost"]=row.get("original_cost_raw",""); row["reported_revised_cost"]=row.get("revised_cost_raw","")
        row["reported_cumulative_expenditure"]=row.get("cumulative_expenditure_raw",""); row["reported_physical_progress"]=row.get("physical_progress_raw","")
        row["reported_start_date"]=row.get("start_date_raw","")
    return rows


def dataset_fingerprint(rows: list[dict[str, Any]]) -> str:
    keys=sorted(f"{row['canonical_project_id']}|{row['reporting_month']}|{row.get('source_sha256','')}" for row in rows)
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()
