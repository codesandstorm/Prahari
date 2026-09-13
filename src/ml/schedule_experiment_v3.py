"""Leakage-safe schedule experiments over frozen Prediction Research V2 cohorts."""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support

from src.ml.final_prediction import add_month
from src.ml.prediction_research_v2 import PLANNED_FOLDS, cluster_bootstrap_indices
from src.ml.temporal_experiment_v2 import (
    RESEARCH_MODE, TARGET_VALIDATION_STATUS, ensemble_diversity, model_factory,
    probability_metrics,
)

MINIMUMS = (1000, 300, 30)
MODELS = ("rule", "logistic_regression", "hist_gradient_boosting", "random_forest", "xgboost")


def matrix(rows: list[dict[str, Any]], features: tuple[str, ...]) -> np.ndarray:
    return np.asarray([[float(row.get(name, math.nan)) for name in features] for row in rows], dtype=float)


def schedule_rule_probability(row: dict[str, Any]) -> float:
    """Frozen transparent schedule-pressure rule using only values known at T."""
    remaining = float(row.get("remaining_schedule_months", math.nan))
    age = float(row.get("project_age_months", math.nan))
    planned = float(row.get("planned_duration_months", math.nan))
    progress = float(row.get("physical_progress", math.nan))
    stagnant = float(row.get("consecutive_stagnant", math.nan))
    late = math.isfinite(age) and math.isfinite(planned) and planned > 0 and age >= .8 * planned
    low_progress = math.isfinite(progress) and progress < 50
    near_deadline = math.isfinite(remaining) and remaining <= 6
    flagged = (math.isfinite(stagnant) and stagnant >= 2) or (late and (low_progress or near_deadline))
    return .75 if flagged else .25


def fold_support(cohort: list[dict[str, Any]], horizon: int) -> list[dict[str, Any]]:
    result = []
    for fold_id, (start, end) in PLANNED_FOLDS.items():
        test = [row for row in cohort if start <= row["anchor_month"] <= end]
        pool = [row for row in cohort if add_month(row["anchor_month"], horizon) < start]
        months = sorted({row["anchor_month"] for row in pool})
        validation_months = months[-max(2, min(4, len(months)//4)):] if len(months) >= 3 else []
        validation_start = validation_months[0] if validation_months else ""
        train = [row for row in pool if validation_start and add_month(row["anchor_month"], horizon) < validation_start]
        validation = [row for row in pool if row["anchor_month"] in validation_months]
        events = sum(int(row["event"]) for row in test)
        projects = len({row["canonical_project_id"] for row in test})
        inner_support = min(
            sum(int(r["event"]) for r in train), sum(1-int(r["event"]) for r in train),
            sum(int(r["event"]) for r in validation), sum(1-int(r["event"]) for r in validation),
        ) if validation else 0
        admitted = len(test) >= MINIMUMS[0] and projects >= MINIMUMS[1] and events >= MINIMUMS[2]
        admitted = admitted and len(train) >= 500 and inner_support >= 5
        result.append({"fold_id": fold_id, "test_start": start, "test_end": end,
                       "outcome_realization_end": add_month(end, horizon),
                       "train_rows": len(train), "validation_rows": len(validation),
                       "test_rows": len(test), "test_events": events, "test_projects": projects,
                       "validation_months": "|".join(validation_months),
                       "latest_training_outcome": add_month(max((r["anchor_month"] for r in train), default="1900-01"), horizon),
                       "status": "ADMITTED" if admitted else "DESCRIPTIVE_ONLY",
                       "reason": "" if admitted else "PREDECLARED_SUPPORT_MINIMUM_NOT_MET"})
    return result


def choose_threshold(y: np.ndarray, probability: np.ndarray) -> tuple[float, float]:
    candidates = sorted(set(float(x) for x in np.quantile(probability, np.linspace(.5, .98, 25))))
    best = (.5, -1.0)
    for threshold in candidates:
        f1 = precision_recall_fscore_support(y, probability >= threshold, average="binary", zero_division=0)[2]
        if f1 > best[1]: best = (threshold, float(f1))
    capacity = float(np.quantile(probability, .9))
    return best[0], capacity


def platt_fit(y: np.ndarray, probability: np.ndarray):
    if len(np.unique(y)) < 2: return None
    p = np.clip(probability, 1e-6, 1-1e-6)
    return LogisticRegression(random_state=26103).fit(np.log(p/(1-p)).reshape(-1, 1), y)


def platt_apply(calibrator, probability: np.ndarray) -> np.ndarray:
    if calibrator is None: return probability
    p = np.clip(probability, 1e-6, 1-1e-6)
    return calibrator.predict_proba(np.log(p/(1-p)).reshape(-1, 1))[:, 1]


def calibration_regression(y: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    if len(np.unique(y)) < 2: return {"calibration_intercept": math.nan, "calibration_slope": math.nan}
    p = np.clip(probability, 1e-6, 1-1e-6)
    fit = LogisticRegression(C=1e6, random_state=26103).fit(np.log(p/(1-p)).reshape(-1, 1), y)
    return {"calibration_intercept": float(fit.intercept_[0]), "calibration_slope": float(fit.coef_[0][0])}


def run_models(cohort: list[dict[str, Any]], features: tuple[str, ...], target: str,
               horizon: int, feature_contract: str):
    metrics=[]; predictions=[]; calibrations=[]; diversity=[]; fitted={}; splits=fold_support(cohort,horizon)
    support = {row["fold_id"]: row for row in splits}
    for fold_id, (test_start, test_end) in PLANNED_FOLDS.items():
        pool=[r for r in cohort if add_month(r["anchor_month"],horizon)<test_start]
        months=sorted({r["anchor_month"] for r in pool})
        if len(months)<3: continue
        val_months=months[-max(2,min(4,len(months)//4)):]; val_start=val_months[0]
        train=[r for r in pool if add_month(r["anchor_month"],horizon)<val_start]
        val=[r for r in pool if r["anchor_month"] in val_months]
        test=[r for r in cohort if test_start<=r["anchor_month"]<=test_end]
        if not train or not val or not test: continue
        y_train=np.asarray([int(r["event"]) for r in train]); y_val=np.asarray([int(r["event"]) for r in val]); y_test=np.asarray([int(r["event"]) for r in test])
        if min(y_train.sum(),len(y_train)-y_train.sum(),y_val.sum(),len(y_val)-y_val.sum(),y_test.sum(),len(y_test)-y_test.sum())<2: continue
        x_train,x_val,x_test=matrix(train,features),matrix(val,features),matrix(test,features)
        fold_test={}; fold_val={}
        for name in MODELS:
            if name=="rule": raw_val=np.asarray([schedule_rule_probability(r) for r in val]);raw_test=np.asarray([schedule_rule_probability(r) for r in test]);model=calibrator=None
            else:
                model=model_factory(name,list(features)); model.fit(x_train,y_train)
                raw_val=model.predict_proba(x_val)[:,1]; raw_test=model.predict_proba(x_test)[:,1]; calibrator=platt_fit(y_val,raw_val)
            val_p=platt_apply(calibrator,raw_val); test_p=platt_apply(calibrator,raw_test); threshold,capacity=choose_threshold(y_val,val_p)
            values=probability_metrics(y_test,test_p,threshold)
            common={"target":target,"horizon_months":horizon,"feature_contract":feature_contract,"fold_id":fold_id,"model":name,
                    "threshold":threshold,"capacity_threshold":capacity,"fold_claim_status":support[fold_id]["status"],
                    "research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS}
            metrics.append({**common,**values,"test_rows":len(test),"test_events":int(y_test.sum())})
            calibrations.append({**common,"raw_brier":probability_metrics(y_test,raw_test,.5)["brier"],"calibrated_brier":values["brier"],
                                 **calibration_regression(y_test,test_p),"method":"PLATT_ON_PAST_VALIDATION" if calibrator else "NONE"})
            fold_test[name]=test_p;fold_val[name]=val_p;fitted[(fold_id,name)]=(model,calibrator,threshold)
            for row,p in zip(test,test_p): predictions.append({"row_key":f'{row["canonical_project_id"]}|{row["anchor_month"]}',"canonical_project_id":row["canonical_project_id"],"anchor_month":row["anchor_month"],"event":row["event"],"event_month":row.get("event_month","") ,**common,"probability":float(p),"prediction_scope":"OUT_OF_SAMPLE_BACKTEST"})
        names=("hist_gradient_boosting","random_forest","xgboost")
        val_p=np.mean([fold_val[n] for n in names],axis=0); test_p=np.mean([fold_test[n] for n in names],axis=0);threshold,capacity=choose_threshold(y_val,val_p)
        values=probability_metrics(y_test,test_p,threshold);common={"target":target,"horizon_months":horizon,"feature_contract":feature_contract,"fold_id":fold_id,"model":"equal_soft_vote","threshold":threshold,"capacity_threshold":capacity,"fold_claim_status":support[fold_id]["status"],"research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS}
        metrics.append({**common,**values,"test_rows":len(test),"test_events":int(y_test.sum())})
        for row,p in zip(test,test_p):predictions.append({"row_key":f'{row["canonical_project_id"]}|{row["anchor_month"]}',"canonical_project_id":row["canonical_project_id"],"anchor_month":row["anchor_month"],"event":row["event"],"event_month":row.get("event_month","") ,**common,"probability":float(p),"prediction_scope":"OUT_OF_SAMPLE_BACKTEST"})
        diversity.extend({"target":target,"horizon_months":horizon,"feature_contract":feature_contract,"fold_id":fold_id,**r} for r in ensemble_diversity(y_test,np.asarray([fold_test[n] for n in names])))
    return metrics,predictions,calibrations,diversity,fitted,splits


def aggregate_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped=defaultdict(list); result=[]
    for row in rows: grouped[(row["target"],row["horizon_months"],row["feature_contract"],row["model"])].append(row)
    for key,items in grouped.items():
        admitted=[r for r in items if r["fold_claim_status"]=="ADMITTED"]; scored=admitted or items
        result.append({"target":key[0],"horizon_months":key[1],"feature_contract":key[2],"model":key[3],"folds":len(items),"admitted_folds":len(admitted),"claim_status":"ADMITTED_FOLDS" if admitted else "DESCRIPTIVE_ONLY",
                       **{f"{label}_{metric}":float(function([r[metric] for r in scored])) for metric in ("pr_auc","precision","recall","false_alerts_per_100","brier","ece") for label,function in (("mean",np.mean),("median",np.median),("worst",np.min),("std",np.std))}})
    return result


def bootstrap_metrics(predictions: list[dict[str, Any]], replicates: int=2000) -> list[dict[str, Any]]:
    y=np.asarray([int(r["event"]) for r in predictions]);p=np.asarray([float(r["probability"]) for r in predictions]);ids=[r["canonical_project_id"] for r in predictions];threshold=float(np.median([float(r["threshold"]) for r in predictions]));values=defaultdict(list)
    for indices in cluster_bootstrap_indices(ids,replicates=replicates):
        if len(np.unique(y[indices]))<2:continue
        for key,value in probability_metrics(y[indices],p[indices],threshold).items():values[key].append(value)
    point=probability_metrics(y,p,threshold)
    return [{"metric":key,"estimate":point[key],"ci_low":float(np.quantile(vals,.025)),"ci_high":float(np.quantile(vals,.975)),"replicates":len(vals)} for key,vals in values.items()]


def lead_time(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    all_events=defaultdict(list)
    for row in predictions:
        if int(row["event"]) and row.get("event_month"):all_events[(row["canonical_project_id"],row["event_month"])].append(row)
    leads=[]
    for rows in all_events.values():
        warned=[(int(r["event_month"][:4])-int(r["anchor_month"][:4]))*12+int(r["event_month"][5:])-int(r["anchor_month"][5:]) for r in rows if float(r["probability"])>=float(r["threshold"])]
        if warned: leads.append(max(warned))
    return {"event_count":len(all_events),"events_warned":len(leads),"warning_coverage":len(leads)/len(all_events) if all_events else 0,"median_lead_months":float(np.median(leads)) if leads else math.nan,"p25":float(np.quantile(leads,.25)) if leads else math.nan,"p75":float(np.quantile(leads,.75)) if leads else math.nan,**{f"at_least_{n}m":sum(x>=n for x in leads)/len(leads) if leads else 0 for n in range(1,7)}}
