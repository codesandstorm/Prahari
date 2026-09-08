"""Feature Discovery V2 for the frozen provisional S1 three-month cohort."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.ml.provisional_research import (
    FEATURES_A, FEATURES_B, SEED, approved_doc, build_s1_cohort, clean, month_date,
    month_index, number, read_csv, split_name, value, write_csv,
)

MOMENTUM = (
    "progress_velocity_last", "progress_velocity_2obs", "progress_velocity_3obs",
    "progress_acceleration", "recent_vs_history_velocity", "momentum_break_flag",
    "consecutive_stagnant", "months_since_positive_progress", "progress_volatility",
    "progress_reversal_count", "large_progress_jump_flag",
)
SCHEDULE = (
    "remaining_work_pct", "remaining_schedule_months", "required_future_velocity",
    "required_vs_recent_velocity", "schedule_feasibility_gap", "elapsed_duration_fraction",
    "progress_vs_elapsed_gap", "deadline_proximity", "low_progress_near_deadline",
)
FINANCIAL = (
    "financial_progress_pct", "spend_to_progress_ratio", "financial_physical_gap",
    "financial_gap_change", "expenditure_velocity", "expenditure_acceleration",
    "expenditure_stagnation", "spend_growth_progress_stagnation",
)
REVISION = ("cost_revision_count", "months_since_cost_revision", "cumulative_cost_revision_pct")
CHANGE_POINT = ("velocity_change", "recent_stagnation_after_activity")
OBSERVABILITY = ("history_span_months", "trailing_coverage_ratio", "internal_gap_count", "schema_change_count")
MATURITY = ("progress_band", "elapsed_time_band", "progress_elapsed_interaction")
SCALE_INTERACTIONS = ("large_project_flag", "cost_remaining_time", "cost_progress", "duration_progress")
SEASONAL = ("month_sin", "month_cos")
ALL_V2 = FEATURES_A + MOMENTUM + SCHEDULE + FINANCIAL + REVISION + CHANGE_POINT + OBSERVABILITY + MATURITY + SCALE_INTERACTIONS + SEASONAL
COMPACT_V2 = FEATURES_A + (
    "history_span_months", "remaining_schedule_months", "required_future_velocity",
    "progress_vs_elapsed_gap", "low_progress_near_deadline", "consecutive_stagnant",
    "cumulative_cost_revision_pct", "expenditure_velocity",
)

VARIANTS = {
    "BASE_A": FEATURES_A,
    "BASE_B": FEATURES_B,
    "B1_MOMENTUM": FEATURES_A + MOMENTUM,
    "B2_SCHEDULE": FEATURES_A + SCHEDULE,
    "B3_FINANCIAL": FEATURES_A + FINANCIAL,
    "B4_REVISION": FEATURES_A + REVISION,
    "B5_CHANGE_POINT": FEATURES_A + CHANGE_POINT,
    "B6_MATURITY": FEATURES_A + MATURITY,
    "B7_SEASONAL": FEATURES_A + SEASONAL,
    "B8_ALL": ALL_V2,
    "COMPACT_V2": COMPACT_V2,
    "REMOVE_MOMENTUM": tuple(x for x in ALL_V2 if x not in MOMENTUM),
    "REMOVE_SCHEDULE": tuple(x for x in ALL_V2 if x not in SCHEDULE),
    "REMOVE_FINANCIAL": tuple(x for x in ALL_V2 if x not in FINANCIAL),
    "REMOVE_REVISION": tuple(x for x in ALL_V2 if x not in REVISION),
    "REMOVE_CHANGE_POINT": tuple(x for x in ALL_V2 if x not in CHANGE_POINT),
    "REMOVE_OBSERVABILITY": tuple(x for x in ALL_V2 if x not in OBSERVABILITY),
    "REMOVE_MATURITY": tuple(x for x in ALL_V2 if x not in MATURITY),
    "REMOVE_SCALE_INTERACTIONS": tuple(x for x in ALL_V2 if x not in SCALE_INTERACTIONS),
    "REMOVE_SEASONAL": tuple(x for x in ALL_V2 if x not in SEASONAL),
}


def finite(value_: float) -> bool:
    return bool(np.isfinite(value_))


def safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if finite(numerator) and finite(denominator) and denominator > 0 else math.nan


def _series(history: list[dict[str, str]], raw: str, fallback: str) -> list[tuple[int, float]]:
    return [(month_index(row["reporting_month"]), number(value(row, raw, fallback))) for row in history]


def _velocity(series: list[tuple[int, float]], back: int = 1) -> float:
    if len(series) <= back:
        return math.nan
    left_i, left = series[-1-back]; right_i, right = series[-1]
    return (right - left) / (right_i - left_i) if finite(left) and finite(right) and right_i > left_i else math.nan


def advanced_features(history: list[dict[str, str]]) -> dict[str, float]:
    anchor = history[-1]
    progress = _series(history, "physical_progress_raw", "reported_physical_progress")
    expenditure = _series(history, "cumulative_expenditure_raw", "reported_cumulative_expenditure")
    recent_velocity = _velocity(progress, 1)
    velocity_2 = _velocity(progress, 2)
    velocity_3 = _velocity(progress, 3)
    historical_velocity = _velocity(progress, len(progress) - 1) if len(progress) > 1 else math.nan
    prior_velocity = _velocity(progress[:-1], 1) if len(progress) > 2 else math.nan
    progress_values = [v for _, v in progress if finite(v)]
    increments = [(right-left)/(ri-li) for (li,left),(ri,right) in zip(progress, progress[1:]) if finite(left) and finite(right) and ri > li]
    stagnant = 0
    for increment in reversed(increments):
        if increment <= 0: stagnant += 1
        else: break
    months_since_positive = math.nan
    if progress and finite(progress[-1][1]):
        for index in range(len(progress)-2, -1, -1):
            if finite(progress[index][1]) and progress[-1][1] > progress[index][1]:
                months_since_positive = float(progress[-1][0] - progress[index][0]); break
    current_progress = progress[-1][1]
    remaining_work = 100 - current_progress if finite(current_progress) and 0 <= current_progress <= 100 else math.nan
    target = approved_doc(anchor)
    year, month = map(int, anchor["reporting_month"].split("-"))
    as_of = month_date(f"{month}/{year}")
    remaining_months = float((target.year-year)*12 + target.month-month) if target else math.nan
    required = safe_ratio(remaining_work, remaining_months)
    required_recent = safe_ratio(required, recent_velocity)
    approval = month_date(value(anchor, "approval_date_raw", "reported_approval_date"))
    original_doc = month_date(value(anchor, "original_target_doc_raw", "reported_original_target_doc"))
    planned = float((original_doc.year-approval.year)*12 + original_doc.month-approval.month) if approval and original_doc else math.nan
    elapsed = float((year-approval.year)*12 + month-approval.month) if approval else math.nan
    elapsed_fraction = safe_ratio(elapsed, planned)
    original_cost = number(value(anchor, "original_cost_raw", "reported_original_cost"))
    revised_cost_series = _series(history, "revised_cost_raw", "reported_revised_cost")
    exp = expenditure[-1][1]
    financial_pct = 100 * safe_ratio(exp, original_cost)
    financial_gap = financial_pct - current_progress if finite(financial_pct) and finite(current_progress) else math.nan
    previous_financial = math.nan
    if len(history) > 1:
        previous_cost = number(value(history[-2], "original_cost_raw", "reported_original_cost"))
        previous_exp = expenditure[-2][1]
        previous_progress = progress[-2][1]
        previous_fp = 100 * safe_ratio(previous_exp, previous_cost)
        previous_financial = previous_fp - previous_progress if finite(previous_fp) and finite(previous_progress) else math.nan
    exp_velocity = _velocity(expenditure, 1)
    prior_exp_velocity = _velocity(expenditure[:-1], 1) if len(expenditure) > 2 else math.nan
    cost_revisions = 0; last_cost_revision = math.nan
    for idx, ((_, left), (right_i, right)) in enumerate(zip(revised_cost_series, revised_cost_series[1:]), 1):
        if finite(left) and finite(right) and right > left:
            cost_revisions += 1; last_cost_revision = float(revised_cost_series[-1][0] - right_i)
    effective_revised = revised_cost_series[-1][1] if finite(revised_cost_series[-1][1]) else original_cost
    span = float(progress[-1][0] - progress[0][0] + 1)
    intervals = [right[0]-left[0] for left,right in zip(progress, progress[1:])]
    schemas = [clean(row.get("schema_family")) for row in history]
    month_number = month
    return {
        "progress_velocity_last": recent_velocity, "progress_velocity_2obs": velocity_2,
        "progress_velocity_3obs": velocity_3,
        "progress_acceleration": recent_velocity-prior_velocity if finite(recent_velocity) and finite(prior_velocity) else math.nan,
        "recent_vs_history_velocity": recent_velocity-historical_velocity if finite(recent_velocity) and finite(historical_velocity) else math.nan,
        "momentum_break_flag": float(finite(recent_velocity) and finite(historical_velocity) and recent_velocity <= 0 < historical_velocity),
        "consecutive_stagnant": float(stagnant), "months_since_positive_progress": months_since_positive,
        "progress_volatility": float(np.std(increments)) if increments else math.nan,
        "progress_reversal_count": float(sum(x < 0 for x in increments)),
        "large_progress_jump_flag": float(any(x > 25 for x in increments[-2:])),
        "remaining_work_pct": remaining_work, "remaining_schedule_months": max(remaining_months, 0) if finite(remaining_months) else math.nan,
        "required_future_velocity": required, "required_vs_recent_velocity": min(required_recent, 100) if finite(required_recent) else math.nan,
        "schedule_feasibility_gap": required-recent_velocity if finite(required) and finite(recent_velocity) else math.nan,
        "elapsed_duration_fraction": elapsed_fraction,
        "progress_vs_elapsed_gap": current_progress-100*elapsed_fraction if finite(current_progress) and finite(elapsed_fraction) else math.nan,
        "deadline_proximity": 1/(1+max(remaining_months, 0)) if finite(remaining_months) else math.nan,
        "low_progress_near_deadline": float(finite(current_progress) and finite(remaining_months) and current_progress < 80 and remaining_months <= 6),
        "financial_progress_pct": financial_pct, "spend_to_progress_ratio": safe_ratio(financial_pct, current_progress),
        "financial_physical_gap": financial_gap,
        "financial_gap_change": financial_gap-previous_financial if finite(financial_gap) and finite(previous_financial) else math.nan,
        "expenditure_velocity": exp_velocity,
        "expenditure_acceleration": exp_velocity-prior_exp_velocity if finite(exp_velocity) and finite(prior_exp_velocity) else math.nan,
        "expenditure_stagnation": float(finite(exp_velocity) and exp_velocity <= 0),
        "spend_growth_progress_stagnation": float(finite(exp_velocity) and exp_velocity > 0 and finite(recent_velocity) and recent_velocity <= 0),
        "cost_revision_count": float(cost_revisions), "months_since_cost_revision": last_cost_revision,
        "cumulative_cost_revision_pct": 100*(effective_revised-original_cost)/original_cost if finite(effective_revised) and finite(original_cost) and original_cost > 0 else math.nan,
        "velocity_change": recent_velocity-historical_velocity if finite(recent_velocity) and finite(historical_velocity) else math.nan,
        "recent_stagnation_after_activity": float(stagnant > 0 and any(x > 0 for x in increments[:-stagnant] if stagnant < len(increments))),
        "history_span_months": span, "trailing_coverage_ratio": len(history)/span if span else math.nan,
        "internal_gap_count": float(sum(interval > 1 for interval in intervals)),
        "schema_change_count": float(sum(a != b for a,b in zip(schemas, schemas[1:]))),
        "progress_band": math.floor(current_progress/20) if finite(current_progress) else math.nan,
        "elapsed_time_band": min(math.floor(max(elapsed, 0)/24), 5) if finite(elapsed) else math.nan,
        "progress_elapsed_interaction": current_progress*elapsed_fraction if finite(current_progress) and finite(elapsed_fraction) else math.nan,
        "large_project_flag": float(finite(original_cost) and original_cost >= 1000),
        "cost_remaining_time": math.log1p(original_cost)*max(remaining_months, 0) if finite(original_cost) and original_cost >= 0 and finite(remaining_months) else math.nan,
        "cost_progress": math.log1p(original_cost)*current_progress if finite(original_cost) and original_cost >= 0 and finite(current_progress) else math.nan,
        "duration_progress": planned*current_progress if finite(planned) and finite(current_progress) else math.nan,
        "month_sin": math.sin(2*math.pi*month_number/12), "month_cos": math.cos(2*math.pi*month_number/12),
    }


def build_v2_cohort(rows: list[dict[str, str]], coverage: dict[str, str]) -> list[dict[str, Any]]:
    base = build_s1_cohort(rows, coverage, 3)
    by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows: by_project[row["canonical_project_id"]].append(row)
    history_lookup = {}
    for project_id, observations in by_project.items():
        observations.sort(key=lambda row: row["reporting_month"])
        for index, row in enumerate(observations): history_lookup[(project_id, row["reporting_month"])] = observations[:index+1]
    return [{**anchor, **advanced_features(history_lookup[(anchor["canonical_project_id"], anchor["anchor_month"])])} for anchor in base]


def metrics(y: np.ndarray, p: np.ndarray, threshold: float) -> dict[str, float]:
    prediction = p >= threshold
    return {"pr_auc": float(average_precision_score(y,p)), "roc_auc": float(roc_auc_score(y,p)),
            "brier": float(brier_score_loss(y,p)), "precision": float(precision_score(y,prediction,zero_division=0)),
            "recall": float(recall_score(y,prediction,zero_division=0)),
            "false_alerts_per_100": float(100*((prediction==1)&(y==0)).sum()/len(y))}


def evaluate_variant(cohort: list[dict[str, Any]], variant: str, features: tuple[str,...], model_name: str) -> tuple[list[dict[str, Any]], Any]:
    parts = {name:[row for row in cohort if split_name(row["anchor_month"])==name] for name in ("TRAIN","VALIDATION","TEST")}
    estimator = LogisticRegression(max_iter=2500,class_weight="balanced",random_state=SEED) if model_name=="LOGISTIC" else HistGradientBoostingClassifier(max_iter=150,learning_rate=.05,max_depth=3,random_state=SEED)
    pipeline=Pipeline([("imputer",SimpleImputer(strategy="median",add_indicator=True)),("scale",StandardScaler()),("model",estimator)])
    matrix=lambda part: np.array([[row[name] for name in features] for row in part],dtype=float)
    pipeline.fit(matrix(parts["TRAIN"]),np.array([row["event"] for row in parts["TRAIN"]]))
    val_p=pipeline.predict_proba(matrix(parts["VALIDATION"]))[:,1]; threshold=float(np.quantile(val_p,.90))
    results=[]
    for split,part in parts.items():
        y=np.array([row["event"] for row in part]); p=pipeline.predict_proba(matrix(part))[:,1]
        results.append({"variant":variant,"model":model_name,"split":split,"features":len(features),"anchors":len(part),"events":int(y.sum()),"threshold":threshold,**metrics(y,p,threshold)})
    return results,pipeline


def feature_quality(cohort:list[dict[str,Any]], features:list[str])->list[dict[str,Any]]:
    rows=[]
    for name in features:
        values=np.array([row[name] for row in cohort],dtype=float); finite_values=values[np.isfinite(values)]
        split_means={split:np.nanmean([row[name] for row in cohort if split_name(row["anchor_month"])==split]) for split in ("TRAIN","VALIDATION","TEST")}
        stability="STABLE"
        if len(finite_values)==0 or np.nanstd(finite_values)==0: stability="UNSTABLE"
        elif max(split_means.values())-min(split_means.values()) > 2*max(np.nanstd(finite_values),1e-9): stability="UNSTABLE"
        elif max(split_means.values())-min(split_means.values()) > np.nanstd(finite_values): stability="MODERATELY_STABLE"
        rows.append({"feature":name,"coverage_pct":100*len(finite_values)/len(values),"missing_pct":100*(1-len(finite_values)/len(values)),"std":float(np.nanstd(finite_values)) if len(finite_values) else math.nan,"train_mean":split_means["TRAIN"],"validation_mean":split_means["VALIDATION"],"test_mean":split_means["TEST"],"stability":stability})
    return rows


def registry_v2(quality:list[dict[str,Any]], family_delta:dict[str,float])->list[dict[str,Any]]:
    retained=set(COMPACT_V2)-set(FEATURES_A)
    family_by_feature={name:family for family,names in {
        "MOMENTUM":MOMENTUM,"SCHEDULE_FEASIBILITY":SCHEDULE,"FINANCIAL_PHYSICAL":FINANCIAL,
        "REVISION_HISTORY":REVISION,"CHANGE_POINT":CHANGE_POINT,"OBSERVABILITY":OBSERVABILITY,
        "MATURITY_PROXY":MATURITY,"SCALE_INTERACTION":SCALE_INTERACTIONS,"SEASONAL":SEASONAL}.items() for name in names}
    conditional={"trailing_coverage_ratio","internal_gap_count","schema_change_count"}
    unstable={"large_progress_jump_flag","month_sin","month_cos","financial_progress_pct","spend_to_progress_ratio","financial_physical_gap","financial_gap_change","expenditure_acceleration","expenditure_stagnation","spend_growth_progress_stagnation"}
    rows=[]
    for index,item in enumerate(quality,1):
        name=item["feature"]; family=family_by_feature[name]
        if name in retained: status="IMPLEMENT_NOW"; reason="retained in compact V2"
        elif name in conditional: status="IMPLEMENT_CONDITIONALLY"; reason="reliability context; do not interpret as project risk"
        elif name in unstable: status="REJECT_UNSTABLE"; reason="era/missingness sensitivity or family-level generalization weakness"
        else: status="REJECT_REDUNDANT"; reason="overlaps a more interpretable retained signal"
        rows.append({"feature_id":f"V2-{index:03d}","feature_name":name,"family":family,"formula":"see src/ml/feature_discovery_v2.py","source":"current project_month history","availability":"DERIVABLE_NOW","coverage":item["coverage_pct"],"known_at_t":"YES","minimum_history":"2+ observations where temporal","missing_policy":"training-fold median plus structural awareness","leakage_status":"SAFE" if family not in {"REVISION_HISTORY"} else "CONDITIONAL","stability":item["stability"],"model_variant":family,"ablation_delta":family_delta.get(family,""),"retain_status":status,"retain_reason":reason,"dashboard_visible":"YES" if name in retained else "NO","explanation_visible":"YES" if name in retained else "NO","CUF_status":"CURRENT_FLASH_REPORT_DERIVED"})
    unavailable=[
        ("milestone_slippage","MILESTONE","REQUIRES_EXISTING_CUF_VERIFICATION"),("land_acquired_pct","LAND","PROPOSE_NEW_CUF_FIELD"),
        ("oldest_pending_clearance_days","CLEARANCE","PROPOSE_NEW_CUF_FIELD"),("oldest_open_issue_days","ISSUES","PROPOSE_NEW_CUF_FIELD"),
        ("contractor_operational_status","CONTRACTOR","PROPOSE_NEW_CUF_FIELD"),("fund_release_delay_days","FUNDING","PROPOSE_NEW_CUF_FIELD"),
        ("manpower_availability_pct","RESOURCES","PROPOSE_NEW_CUF_FIELD"),("anticipated_schedule_slippage_days","ANTICIPATED","REQUIRES_EXISTING_CUF_VERIFICATION"),
        ("rainfall_anomaly","WEATHER","RESEARCH_EXTERNAL_SOURCE"),("verified_disaster_alert","WEATHER","RESEARCH_EXTERNAL_SOURCE"),
        ("construction_input_price_change","ECONOMIC","RESEARCH_EXTERNAL_SOURCE"),("raw_agency_as_contractor","AGENCY","REJECT_SEMANTICALLY_UNSAFE"),
        ("project_name_text_embedding","PROJECT_TEXT","REJECT_SEMANTICALLY_UNSAFE"),("future_revised_doc","FUTURE_OUTCOME","REJECT_LEAKAGE"),
        ("full_dataset_peer_percentile","PEER","REJECT_LEAKAGE"),("ministry_peer_percentile","PEER","REJECT_INSUFFICIENT_DATA"),
    ]
    start=len(rows)+1
    for offset,(name,family,status) in enumerate(unavailable):
        rows.append({"feature_id":f"V2-{start+offset:03d}","feature_name":name,"family":family,"formula":"N/A","source":"not in current dataset","availability":"UNAVAILABLE","coverage":0,"known_at_t":"UNKNOWN_OR_FUTURE","minimum_history":"N/A","missing_policy":"DO NOT SYNTHESIZE","leakage_status":"LEAKAGE" if "LEAKAGE" in status else "UNKNOWN","stability":"NOT_TESTED","model_variant":"MODEL_C_FUTURE","ablation_delta":"","retain_status":status,"retain_reason":"unavailable or unsafe under current evidence","dashboard_visible":"NO","explanation_visible":"NO","CUF_status":status})
    return rows


def rolling_origin(cohort:list[dict[str,Any]])->list[dict[str,Any]]:
    folds=(("R1","2023-08","2025-04","2025-05"),("R2","2025-05","2025-07","2025-11"),("R3","2025-11","2025-12","2026-03"))
    results=[]
    for fold,train_end,test_start,test_end in folds:
        train=[row for row in cohort if row["anchor_month"]<=train_end]
        test=[row for row in cohort if test_start<=row["anchor_month"]<=test_end]
        if not train or not test or len({row["event"] for row in train})<2 or len({row["event"] for row in test})<2:
            results.append({"fold":fold,"model":"NOT_EVALUABLE","train_end":train_end,"test_start":test_start,"test_end":test_end,"train_anchors":len(train),"test_anchors":len(test),"test_projects":len({row["canonical_project_id"] for row in test}),"events":sum(row["event"] for row in test),"threshold":"","pr_auc":"","roc_auc":"","brier":"","precision":"","recall":"","false_alerts_per_100":""});continue
        matrix=lambda part:np.array([[row[name] for name in COMPACT_V2] for row in part],dtype=float)
        for model_name,estimator in (("LOGISTIC",LogisticRegression(max_iter=2500,class_weight="balanced",random_state=SEED)),("HIST_GB",HistGradientBoostingClassifier(max_iter=150,learning_rate=.05,max_depth=3,random_state=SEED))):
            model=Pipeline([("imputer",SimpleImputer(strategy="median",add_indicator=True)),("scale",StandardScaler()),("model",estimator)])
            y_train=np.array([row["event"] for row in train]);model.fit(matrix(train),y_train)
            train_p=model.predict_proba(matrix(train))[:,1];threshold=float(np.quantile(train_p,.90))
            y=np.array([row["event"] for row in test]);p=model.predict_proba(matrix(test))[:,1]
            results.append({"fold":fold,"model":model_name,"train_end":train_end,"test_start":test_start,"test_end":test_end,"train_anchors":len(train),"test_anchors":len(test),"test_projects":len({row["canonical_project_id"] for row in test}),"events":int(y.sum()),**metrics(y,p,threshold)})
    return results


def run(root:Path)->dict[str,Any]:
    dataset=root/"data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv"
    coverage={row["reporting_month"]:row["coverage_class"] for row in read_csv(root/"data/metadata/source_coverage_2023_07_2026_06.csv")}
    cohort=build_v2_cohort(read_csv(dataset),coverage)
    results=[]; models={}
    for variant,features in VARIANTS.items():
        for model_name in ("LOGISTIC","HIST_GB"):
            rows,model=evaluate_variant(cohort,variant,features,model_name);results.extend(rows);models[(variant,model_name)]=model
    compact_model=models[("COMPACT_V2","HIST_GB")]
    validation=[row for row in cohort if split_name(row["anchor_month"])=="VALIDATION"]
    test=[row for row in cohort if split_name(row["anchor_month"])=="TEST"]
    matrix_for=lambda part: np.array([[row[name] for name in COMPACT_V2] for row in part],dtype=float)
    val_raw=np.clip(compact_model.predict_proba(matrix_for(validation))[:,1],1e-6,1-1e-6)
    test_raw=np.clip(compact_model.predict_proba(matrix_for(test))[:,1],1e-6,1-1e-6)
    calibrator=LogisticRegression(random_state=SEED).fit(np.log(val_raw/(1-val_raw)).reshape(-1,1),np.array([row["event"] for row in validation]))
    val_cal=calibrator.predict_proba(np.log(val_raw/(1-val_raw)).reshape(-1,1))[:,1]
    test_cal=calibrator.predict_proba(np.log(test_raw/(1-test_raw)).reshape(-1,1))[:,1]
    cal_threshold=float(np.quantile(val_cal,.90)); test_y=np.array([row["event"] for row in test])
    results.append({"variant":"COMPACT_V2","model":"HIST_GB_PLATT","split":"TEST","features":len(COMPACT_V2),"anchors":len(test),"events":int(test_y.sum()),"threshold":cal_threshold,**metrics(test_y,test_cal,cal_threshold)})
    test_rows=[row for row in results if row["split"]=="TEST"]
    best=max(test_rows,key=lambda row:(row["pr_auc"],-row["features"]))
    best_key=(best["variant"],best["model"]); best_features=VARIANTS[best["variant"]]
    matrix=np.array([[row[name] for name in best_features] for row in test],dtype=float); y=np.array([row["event"] for row in test])
    importance=permutation_importance(models[best_key],matrix,y,scoring="average_precision",n_repeats=5,random_state=SEED)
    importance_rows=[{"feature":name,"permutation_pr_auc_drop_mean":float(mean),"permutation_pr_auc_drop_std":float(std)} for name,mean,std in zip(best_features,importance.importances_mean,importance.importances_std)]
    output=root/"outputs/ml"; write_csv(output/"PRAHARI_FEATURE_V2_ABLATION.csv",results)
    all_new=list(dict.fromkeys(MOMENTUM+SCHEDULE+FINANCIAL+REVISION+CHANGE_POINT+OBSERVABILITY+MATURITY+SCALE_INTERACTIONS+SEASONAL))
    quality=feature_quality(cohort,all_new)
    write_csv(output/"PRAHARI_FEATURE_V2_STABILITY.csv",quality)
    write_csv(output/"PRAHARI_FEATURE_V2_MODEL_COMPARISON.csv",test_rows)
    write_csv(output/"PRAHARI_FEATURE_V2_IMPORTANCE.csv",sorted(importance_rows,key=lambda row:row["permutation_pr_auc_drop_mean"],reverse=True))
    compact=next(row for row in test_rows if row["variant"]=="COMPACT_V2" and row["model"]=="HIST_GB")
    compact_matrix=np.array([[row[name] for name in COMPACT_V2] for row in test],dtype=float)
    compact_probability=compact_model.predict_proba(compact_matrix)[:,1]
    error_cases=[]
    for row,probability in zip(test,compact_probability):
        predicted=probability>=compact["threshold"]
        kind="FALSE_POSITIVE" if predicted and not row["event"] else "FALSE_NEGATIVE" if not predicted and row["event"] else ""
        if kind:
            error_cases.append({"error_type":kind,"canonical_project_id":row["canonical_project_id"],"anchor_month":row["anchor_month"],"probability_uncalibrated":probability,"event":row["event"],"history_span_months":row["history_span_months"],"physical_progress":row["physical_progress"],"remaining_schedule_months":row["remaining_schedule_months"],"required_future_velocity":row["required_future_velocity"],"consecutive_stagnant":row["consecutive_stagnant"],"cumulative_cost_revision_pct":row["cumulative_cost_revision_pct"]})
    sampled=[]
    for kind in ("FALSE_POSITIVE","FALSE_NEGATIVE"):
        sampled.extend(sorted((row for row in error_cases if row["error_type"]==kind),key=lambda row:(-row["probability_uncalibrated"],row["canonical_project_id"]))[:20])
    write_csv(output/"PRAHARI_FEATURE_V2_ERROR_CASES.csv",sampled)
    base=next(row for row in test_rows if row["variant"]=="BASE_A" and row["model"]=="HIST_GB")
    mapping={"MOMENTUM":"B1_MOMENTUM","SCHEDULE_FEASIBILITY":"B2_SCHEDULE","FINANCIAL_PHYSICAL":"B3_FINANCIAL","REVISION_HISTORY":"B4_REVISION","CHANGE_POINT":"B5_CHANGE_POINT","MATURITY_PROXY":"B6_MATURITY","SEASONAL":"B7_SEASONAL"}
    family_delta={family:next(row for row in test_rows if row["variant"]==variant and row["model"]=="HIST_GB")["pr_auc"]-base["pr_auc"] for family,variant in mapping.items()}
    family_delta["OBSERVABILITY"]=next(row for row in test_rows if row["variant"]=="B8_ALL" and row["model"]=="HIST_GB")["pr_auc"]-next(row for row in test_rows if row["variant"]=="REMOVE_OBSERVABILITY" and row["model"]=="HIST_GB")["pr_auc"]
    family_delta["SCALE_INTERACTION"]=next(row for row in test_rows if row["variant"]=="B8_ALL" and row["model"]=="HIST_GB")["pr_auc"]-next(row for row in test_rows if row["variant"]=="REMOVE_SCALE_INTERACTIONS" and row["model"]=="HIST_GB")["pr_auc"]
    write_csv(root/"data/metadata/prahari_feature_registry_v2.csv",registry_v2(quality,family_delta))
    write_csv(output/"PRAHARI_FEATURE_V2_ROLLING_FOLDS.csv",rolling_origin(cohort))
    metadata={"status":"PROVISIONAL — NOT FINAL SIH CLAIM","selection_warning":"COMPACT_V2 was reduced after exploratory inspection and requires a new future confirmation period","seed":SEED,"dataset_sha256":hashlib.sha256(dataset.read_bytes()).hexdigest(),"cohort_rows":len(cohort),"new_features_tested":len(all_new),"variants":{key:list(value) for key,value in VARIANTS.items()},"best_by_test_pr_auc":best,"compact_v2_test":compact}
    (output/"PRAHARI_FEATURE_V2_RUN_METADATA.json").write_text(json.dumps(metadata,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return metadata
