"""Leakage-safe expanding-origin experiments for Cost Prediction V3."""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,precision_recall_fscore_support

from src.ml.cost_prediction_v2 import MIN_EVENT_COUNT,RESEARCH_MODE,TARGET_VALIDATION_STATUS,cost_rule_probability
from src.ml.prediction_research_v2 import add_month,cluster_bootstrap_indices
from src.ml.temporal_experiment_v2 import model_factory,probability_metrics


def cost_folds(cohort: list[dict[str,Any]],horizon: int) -> list[dict[str,Any]]:
    result=[]
    for fold_id,(start,end) in COST_V3_FOLDS.items():
        test=[r for r in cohort if start<=r["anchor_month"]<=end]
        train=[r for r in cohort if add_month(r["anchor_month"],horizon)<start]
        events=sum(int(r["event"]) for r in test); projects=len({r["canonical_project_id"] for r in test});train_events=sum(int(r["event"]) for r in train)
        months=sorted({r["anchor_month"] for r in train});val_months=months[-max(2,min(4,len(months)//4)):] if len(months)>=3 else []
        val_start=val_months[0] if val_months else "";inner_train=[r for r in train if val_start and add_month(r["anchor_month"],horizon)<val_start];validation=[r for r in train if r["anchor_month"] in val_months]
        inner_support=min(sum(int(r["event"]) for r in inner_train),sum(1-int(r["event"]) for r in inner_train),sum(int(r["event"]) for r in validation),sum(1-int(r["event"]) for r in validation)) if val_months else 0
        admitted=len(test)>=1000 and projects>=300 and events>=MIN_EVENT_COUNT and len(train)>=500 and train_events>=20 and inner_support>=5
        schemas=defaultdict(int)
        for row in test: schemas[row.get("schema_family","UNKNOWN")]+=1
        result.append({"fold_id":fold_id,"test_start":start,"test_end":end,"outcome_realization_end":add_month(end,horizon),
                       "train_start":min((r["anchor_month"] for r in train),default=""),"train_end":max((r["anchor_month"] for r in train),default=""),"train_rows":len(train),"train_events":train_events,
                       "eligible_anchors":len(test),"events":events,"non_events":len(test)-events,"projects":projects,
                       "prevalence":events/len(test) if test else 0,"schema_mix":"|".join(f"{k}:{v}" for k,v in sorted(schemas.items())),
                       "inner_train_rows":len(inner_train),"validation_rows":len(validation),"validation_events":sum(int(r["event"]) for r in validation),
                       "status":"ADMITTED" if admitted else "DESCRIPTIVE_ONLY","reason":"" if admitted else "TRAIN_VALIDATION_OR_TEST_SUPPORT_MINIMUM_NOT_MET"})
    return result


def matrix(rows,features): return np.asarray([[float(r.get(f,math.nan)) for f in features] for r in rows],dtype=float)


def choose_threshold(y,p):
    best=(.5,-1.0)
    for threshold in np.linspace(.1,.9,17):
        score=precision_recall_fscore_support(y,np.asarray(p)>=threshold,average="binary",zero_division=0)[2]
        if score>best[1]: best=(float(threshold),float(score))
    return best[0]


def platt_fit(y,p):
    p=np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6); x=np.log(p/(1-p)).reshape(-1,1)
    if len(np.unique(y))<2: return None
    return LogisticRegression(random_state=26103).fit(x,y)


def platt_apply(calibrator,p):
    if calibrator is None:return np.asarray(p,dtype=float)
    p=np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6);return calibrator.predict_proba(np.log(p/(1-p)).reshape(-1,1))[:,1]


def calibration_slope_intercept(y,p):
    """Descriptive calibration regression; never used to refit test probabilities."""
    y=np.asarray(y,dtype=int);p=np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6)
    if len(np.unique(y))<2:return {"calibration_intercept":math.nan,"calibration_slope":math.nan}
    fitted=LogisticRegression(C=1e6,solver="lbfgs",random_state=26103).fit(np.log(p/(1-p)).reshape(-1,1),y)
    return {"calibration_intercept":float(fitted.intercept_[0]),"calibration_slope":float(fitted.coef_[0][0])}


def run_temporal_models(cohort,features,target,horizon,feature_contract,history_window_months=None):
    metrics=[];predictions=[];calibration=[];models={};fold_records=[]
    folds={r["fold_id"]:r for r in cost_folds(cohort,horizon)}
    for fold_id,(test_start,test_end) in COST_V3_FOLDS.items():
        pool=[r for r in cohort if add_month(r["anchor_month"],horizon)<test_start]
        if history_window_months is not None:
            earliest = add_month(test_start, -int(history_window_months))
            pool = [r for r in pool if r["anchor_month"] >= earliest]
        months=sorted({r["anchor_month"] for r in pool})
        if len(months)<3:continue
        val_months=months[-max(2,min(4,len(months)//4)):]
        val_start=val_months[0]; train=[r for r in pool if add_month(r["anchor_month"],horizon)<val_start]; val=[r for r in pool if r["anchor_month"] in val_months]
        test=[r for r in cohort if test_start<=r["anchor_month"]<=test_end]
        if len(test)<1 or sum(int(r["event"]) for r in test)<5 or min(sum(int(r["event"]) for r in train),sum(1-int(r["event"]) for r in train),sum(int(r["event"]) for r in val),sum(1-int(r["event"]) for r in val))<5:continue
        y_train=np.asarray([int(r["event"]) for r in train]);y_val=np.asarray([int(r["event"]) for r in val]);y_test=np.asarray([int(r["event"]) for r in test])
        X_train,X_val,X_test=matrix(train,features),matrix(val,features),matrix(test,features)
        fold_probs={};fold_val={}
        for name in ("rule","logistic_regression","hist_gradient_boosting","random_forest","xgboost"):
            if name=="rule": raw_val=np.asarray([cost_rule_probability(r,target) for r in val]);raw_test=np.asarray([cost_rule_probability(r,target) for r in test]);calibrator=None;model=None
            else:
                model=model_factory(name,list(features));model.fit(X_train,y_train);raw_val=model.predict_proba(X_val)[:,1];raw_test=model.predict_proba(X_test)[:,1];calibrator=platt_fit(y_val,raw_val)
            calibrated_val=platt_apply(calibrator,raw_val); calibrated_test=platt_apply(calibrator,raw_test);threshold=choose_threshold(y_val,calibrated_val)
            values=probability_metrics(y_test,calibrated_test,threshold)
            metrics.append({"target":target,"horizon_months":horizon,"feature_contract":feature_contract,"fold_id":fold_id,"model":name,"threshold":threshold,**values,
                            "test_rows":len(test),"test_events":int(y_test.sum()),"fold_claim_status":folds[fold_id]["status"],"research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS})
            calibration.append({"target":target,"horizon_months":horizon,"feature_contract":feature_contract,"fold_id":fold_id,"model":name,
                                "raw_brier":probability_metrics(y_test,raw_test,.5)["brier"],"calibrated_brier":values["brier"],
                                **calibration_slope_intercept(y_test,calibrated_test),
                                "method":"PLATT_ON_PAST_VALIDATION" if calibrator else "NONE","fit_data":"PAST_VALIDATION_ONLY","test_use":"EVALUATION_ONLY"})
            fold_probs[name]=calibrated_test;fold_val[name]=calibrated_val
            for row,prob in zip(test,calibrated_test): predictions.append({"row_key":row["row_key"],"canonical_project_id":row["canonical_project_id"],"anchor_month":row["anchor_month"],"event":row["event"],"event_month":row.get("event_month",""),"target":target,"horizon_months":horizon,"feature_contract":feature_contract,"fold_id":fold_id,"model":name,"probability":float(prob),"threshold":threshold,"prediction_scope":"OUT_OF_SAMPLE_BACKTEST"})
            models[(fold_id,name)]=(model,calibrator,threshold)
        for ensemble_name,weights in (("equal_soft_vote",(1/3,1/3,1/3)),):
            names=("hist_gradient_boosting","random_forest","xgboost");val_prob=sum(w*fold_val[n] for w,n in zip(weights,names));test_prob=sum(w*fold_probs[n] for w,n in zip(weights,names));threshold=choose_threshold(y_val,val_prob);values=probability_metrics(y_test,test_prob,threshold)
            metrics.append({"target":target,"horizon_months":horizon,"feature_contract":feature_contract,"fold_id":fold_id,"model":ensemble_name,"threshold":threshold,**values,"test_rows":len(test),"test_events":int(y_test.sum()),"fold_claim_status":folds[fold_id]["status"],"research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS})
            for row,prob in zip(test,test_prob):predictions.append({"row_key":row["row_key"],"canonical_project_id":row["canonical_project_id"],"anchor_month":row["anchor_month"],"event":row["event"],"event_month":row.get("event_month",""),"target":target,"horizon_months":horizon,"feature_contract":feature_contract,"fold_id":fold_id,"model":ensemble_name,"probability":float(prob),"threshold":threshold,"prediction_scope":"OUT_OF_SAMPLE_BACKTEST"})
        fold_records.append({"fold_id":fold_id,"train_rows":len(train),"validation_rows":len(val),"test_rows":len(test),"validation_months":"|".join(val_months),"latest_training_outcome":add_month(max(r["anchor_month"] for r in train),horizon),"test_start":test_start})
    return metrics,predictions,calibration,models,fold_records


def aggregate_metrics(rows):
    grouped=defaultdict(list);result=[]
    for row in rows:grouped[(row["target"],row["horizon_months"],row["feature_contract"],row["model"])].append(row)
    for key,items in grouped.items():
        admitted=[r for r in items if r.get("fold_claim_status")=="ADMITTED"];scored=admitted or items
        result.append({"target":key[0],"horizon_months":key[1],"feature_contract":key[2],"model":key[3],"folds":len(items),"admitted_folds":len(admitted),"claim_status":"ADMITTED_FOLDS" if admitted else "DESCRIPTIVE_ONLY",
                       "mean_pr_auc":float(np.mean([r["pr_auc"] for r in scored])),"median_pr_auc":float(np.median([r["pr_auc"] for r in scored])),"worst_pr_auc":float(np.min([r["pr_auc"] for r in scored])),"std_pr_auc":float(np.std([r["pr_auc"] for r in scored])),
                       "mean_precision":float(np.mean([r["precision"] for r in scored])),"mean_recall":float(np.mean([r["recall"] for r in scored])),"mean_false_alerts_per_100":float(np.mean([r["false_alerts_per_100"] for r in scored])),"mean_brier":float(np.mean([r["brier"] for r in scored])),"mean_ece":float(np.mean([r["ece"] for r in scored]))})
    return result


def bootstrap_metrics(predictions,replicates=2000):
    y=np.asarray([int(r["event"]) for r in predictions]);p=np.asarray([float(r["probability"]) for r in predictions]);ids=[r["canonical_project_id"] for r in predictions];threshold=float(np.median([float(r["threshold"]) for r in predictions]));values=defaultdict(list)
    for indices in cluster_bootstrap_indices(ids,replicates=replicates):
        if len(np.unique(y[indices]))<2:continue
        for key,val in probability_metrics(y[indices],p[indices],threshold).items():values[key].append(val)
    return [{"metric":key,"estimate":probability_metrics(y,p,threshold)[key],"ci_low":float(np.quantile(vals,.025)),"ci_high":float(np.quantile(vals,.975)),"replicates":len(vals)} for key,vals in values.items()]


def lead_time(predictions):
    by_event=defaultdict(list)
    for row in predictions:
        if int(row["event"]) and row.get("event_month"):by_event[(row["canonical_project_id"],row["event_month"])].append(row)
    leads=[]
    for items in by_event.values():
        warned=[month_distance(r["anchor_month"],r["event_month"]) for r in items if float(r["probability"])>=float(r["threshold"])]
        if warned:leads.append(max(warned))
    if not leads:return {"events_warned":0,"median_lead_months":math.nan,"p25":math.nan,"p75":math.nan}
    return {"events_warned":len(leads),"median_lead_months":float(np.median(leads)),"p25":float(np.quantile(leads,.25)),"p75":float(np.quantile(leads,.75)),**{f"at_least_{n}m":sum(x>=n for x in leads)/len(leads) for n in range(1,7)}}


def month_distance(left,right):
    return (int(right[:4])-int(left[:4]))*12+int(right[5:])-int(left[5:])
CostFold = tuple[str, str]
COST_V3_FOLDS: dict[str, CostFold] = {
    "V3-F01-PRE_COVID": ("2019-07", "2019-12"),
    "V3-F02-COVID_ONSET": ("2020-01", "2020-06"),
    "V3-F03-COVID_LATE": ("2020-07", "2020-12"),
    "V3-F04-COVID_2021_H1": ("2021-01", "2021-06"),
    "V3-F05-COVID_2021_H2": ("2021-07", "2021-12"),
    "V3-F06-LATE_OCMS": ("2022-01", "2022-05"),
    "V3-F07-OCMS_RESTART": ("2023-01", "2023-06"),
    "V3-F08-PAIMANA_TRANSITION": ("2024-06", "2024-10"),
    "V3-F09-RECENT_2025": ("2025-03", "2025-09"),
    "V3-F10-RECENT_2026": ("2025-10", "2026-03"),
}
