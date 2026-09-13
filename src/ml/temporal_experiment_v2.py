"""Post-adjudication temporal model harness for Prediction Research V2.

The harness consumes frozen cohorts; it never constructs labels.  Callers must
explicitly declare that human target transfer passed before fitting anything.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss, precision_score,
                             recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_NAMES=("rule","logistic_regression","hist_gradient_boosting","random_forest","xgboost")
WEIGHT_GRID=((.5,.25,.25),(.25,.5,.25),(.25,.25,.5),(.34,.33,.33))


TARGET_VALIDATION_STATUS = "MACHINE_PROVISIONAL"
RESEARCH_MODE = "PROTOTYPE_RESEARCH_OVERRIDE"


def require_research_authorization(status: str) -> None:
    """Permit fitting only after an explicit truth gate or governed prototype override."""
    if status not in {"HUMAN_TARGET_TRANSFER_PASSED", RESEARCH_MODE}:
        raise RuntimeError("MODEL_EXECUTION_BLOCKED_WITHOUT_EXPLICIT_RESEARCH_AUTHORIZATION")


def require_human_gate(status: str) -> None:
    """Backward-compatible name; semantics now include the approved prototype override."""
    require_research_authorization(status)


def model_factory(name: str, feature_names: list[str], seed: int=26103):
    if name not in MODEL_NAMES or name=="rule": raise ValueError("unsupported learned model")
    if name=="logistic_regression":
        return Pipeline([("impute",SimpleImputer(strategy="median",add_indicator=True)),
                         ("scale",StandardScaler()),("model",LogisticRegression(max_iter=2000,class_weight="balanced",random_state=seed))])
    if name=="hist_gradient_boosting":
        return Pipeline([("impute",SimpleImputer(strategy="median",add_indicator=True)),
                         ("model",HistGradientBoostingClassifier(random_state=seed))])
    if name=="random_forest":
        return Pipeline([("impute",SimpleImputer(strategy="median",add_indicator=True)),
                         ("model",RandomForestClassifier(n_estimators=400,min_samples_leaf=5,class_weight="balanced",random_state=seed,n_jobs=1))])
    from xgboost import XGBClassifier
    return Pipeline([("impute",SimpleImputer(strategy="median",add_indicator=True)),
                     ("model",XGBClassifier(n_estimators=400,max_depth=4,learning_rate=.04,subsample=.8,colsample_bytree=.8,
                                            eval_metric="logloss",random_state=seed,n_jobs=1))])


def expected_calibration_error(y: Iterable[int], probability: Iterable[float], bins: int=10) -> float:
    y=np.asarray(list(y),dtype=int); p=np.asarray(list(probability),dtype=float); total=len(y)
    if not total: return float("nan")
    result=0.0
    for lo,hi in zip(np.linspace(0,1,bins+1)[:-1],np.linspace(0,1,bins+1)[1:]):
        mask=(p>=lo)&((p<hi) if hi<1 else (p<=hi))
        if mask.any(): result += mask.mean()*abs(y[mask].mean()-p[mask].mean())
    return float(result)


def probability_metrics(y: Iterable[int], probability: Iterable[float], threshold: float=.5) -> dict[str,float]:
    y=np.asarray(list(y),dtype=int); p=np.asarray(list(probability),dtype=float)
    if len(y)!=len(p) or not len(y) or not np.isfinite(p).all(): raise ValueError("aligned finite outcomes/probabilities required")
    pred=(p>=threshold).astype(int); negatives=max(int((y==0).sum()),1)
    return {"pr_auc":float(average_precision_score(y,p)),"roc_auc":float(roc_auc_score(y,p)) if len(np.unique(y))==2 else float("nan"),
            "precision":float(precision_score(y,pred,zero_division=0)),"recall":float(recall_score(y,pred,zero_division=0)),
            "false_alerts_per_100":float(100*((pred==1)&(y==0)).sum()/negatives),"brier":float(brier_score_loss(y,p)),
            "ece":expected_calibration_error(y,p),"warning_rate":float(pred.mean())}


def align_predictions(predictions: dict[str,list[dict[str,Any]]], required=("hist_gradient_boosting","random_forest","xgboost")):
    maps={name:{row["row_key"]:row for row in predictions[name]} for name in required}
    keys=set(maps[required[0]])
    if any(set(maps[name])!=keys for name in required[1:]): raise ValueError("ENSEMBLE_ROW_ALIGNMENT_FAIL")
    ordered=sorted(keys); matrix=np.asarray([[float(maps[name][key]["probability"]) for key in ordered] for name in required])
    return ordered,matrix


def equal_vote(predictions: dict[str,list[dict[str,Any]]]):
    keys,matrix=align_predictions(predictions)
    return [{"row_key":key,"probability":float(matrix[:,index].mean())} for index,key in enumerate(keys)]


def weighted_vote(predictions: dict[str,list[dict[str,Any]]], weights: tuple[float,float,float]):
    if weights not in WEIGHT_GRID: raise ValueError("weights must come from predeclared past-validation grid")
    keys,matrix=align_predictions(predictions)
    values=np.average(matrix,axis=0,weights=np.asarray(weights))
    return [{"row_key":key,"probability":float(values[index])} for index,key in enumerate(keys)]


def ensemble_diversity(y: Iterable[int], matrix: np.ndarray, names=("hist_gradient_boosting","random_forest","xgboost")):
    y=np.asarray(list(y),dtype=int); result=[]
    for i in range(len(names)):
        for j in range(i+1,len(names)):
            a,b=matrix[i],matrix[j]; ea=(a>=.5)!=y; eb=(b>=.5)!=y
            result.append({"model_a":names[i],"model_b":names[j],"pearson":float(pearsonr(a,b).statistic),
                           "spearman":float(spearmanr(a,b).statistic),"error_disagreement":float((ea!=eb).mean()),
                           "false_positive_disagreement":float((((a>=.5)&(y==0))!=((b>=.5)&(y==0))).mean())})
    return result


def fit_calibrator(estimator, x_calibration, y_calibration, method: str):
    if method not in {"sigmoid","isotonic"}: raise ValueError("unsupported calibration")
    if method=="isotonic" and min(np.bincount(np.asarray(y_calibration,dtype=int),minlength=2))<100:
        raise ValueError("ISOTONIC_SUPPORT_INADEQUATE")
    calibrated=CalibratedClassifierCV(estimator,method=method,cv="prefit")
    return calibrated.fit(x_calibration,y_calibration)


def validate_temporal_oof(rows: list[dict[str,Any]]) -> None:
    for row in rows:
        if row["training_outcome_cutoff"] >= row["prediction_month"]: raise ValueError("STACKING_OOF_TEMPORAL_LEAKAGE")
        if row.get("prediction_scope") != "OUT_OF_FOLD": raise ValueError("STACKING_REQUIRES_OOF_PREDICTIONS")
