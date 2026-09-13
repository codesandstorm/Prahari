"""Execute and freeze PRAHARI Schedule Prediction Final V3 research evidence."""
from __future__ import annotations

import argparse, hashlib, json, math, subprocess, sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from src.ml.prediction_research_v2 import BASIC_LONG_HISTORY_V1, build_basic_long_history, build_research_target, read_csv, restrict_feature_anchors, write_csv
from src.ml.final_prediction import COMPACT_V2, build_compact_v2
from src.ml.schedule_experiment_v3 import aggregate_metrics, bootstrap_metrics, lead_time, matrix, run_models
from src.ml.temporal_experiment_v2 import RESEARCH_MODE, TARGET_VALIDATION_STATUS, require_research_authorization

DATA=ROOT/"data/processed/longitudinal_2022_08_2026_06_research_v2"
SOURCE=ROOT/"outputs/ml/prediction_research_v2"
OUT=ROOT/"outputs/ml/schedule_prediction_final_v3"
MODEL_ROOT=ROOT/"models/research/schedule_prediction_final_v3"


def fingerprint(rows):
    payload="\n".join(sorted(f'{r["canonical_project_id"]}|{r["anchor_month"]}|{r["event"]}' for r in rows))
    return hashlib.sha256(payload.encode()).hexdigest()


def json_write(path,obj):
    def safe(x):
        if isinstance(x,float) and not math.isfinite(x):return None
        if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)):return [safe(v) for v in x]
        return x
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(safe(obj),indent=2,default=str,allow_nan=False)+"\n",encoding="utf-8")


def selected_candidate(summary,target,contract="basic-long-history-v1"):
    rows=[r for r in summary if r["target"]==target and int(r["horizon_months"])==3 and r["feature_contract"]==contract and int(r["admitted_folds"])>=2]
    rule=next((r for r in rows if r["model"]=="rule"),None)
    learned=[r for r in rows if r["model"]!="rule" and r["mean_recall"]>=.20 and r["mean_false_alerts_per_100"]<=15]
    learned=[r for r in learned if rule and r["mean_pr_auc"]>rule["mean_pr_auc"] and r["worst_pr_auc"]>=.05]
    return max(learned,key=lambda r:(r["worst_pr_auc"],r["mean_pr_auc"],-r["mean_brier"])) if learned else None


def apply_member(member,x):
    model,calibrator,_=member;raw=model.predict_proba(x)[:,1]
    if calibrator is None:return raw
    clipped=np.clip(raw,1e-6,1-1e-6);return calibrator.predict_proba(np.log(clipped/(1-clipped)).reshape(-1,1))[:,1]


def write_model_contract(target,cohort,features,winner,predictions,models,splits,dataset_fp,code_commit):
    directory=MODEL_ROOT/target.lower();directory.mkdir(parents=True,exist_ok=True)
    cohort_fp=fingerprint(cohort);common={"target":target,"horizon_months":3,"research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS,"production_release":"WITHHELD"}
    if not winner:
        json_write(directory/"model_card.json",{**common,"status":"WITHHELD_NO_ADMITTED_CANDIDATE","pipeline_artifact":"NOT_CREATED"})
        json_write(directory/"evaluation_summary.json",{"status":f"{target}_WITHHELD_NO_ADMITTED_CANDIDATE"})
        for name,payload in {
            "feature_manifest.json":{"version":"basic-long-history-v1","features":features,"known_at_t":True},
            "target_contract.json":{**common,"version":f"{target}-3m-v3-explicit-revised-machine-provisional"},
            "training_metadata.json":{"dataset_fingerprint":dataset_fp,"cohort_fingerprint":cohort_fp,"fit_status":"NOT_FIT_AS_DEPLOYABLE_ARTIFACT"},
            "split_definition.json":splits,"calibration.json":{"status":"NOT_ADMITTED"},
            "threshold_policy.json":{"status":"NOT_ADMITTED","probability_is_not_review_policy":True},
            "dependency_metadata.json":{"python":sys.version.split()[0],"joblib":joblib.__version__},
        }.items():json_write(directory/name,payload)
        return {"status":"WITHHELD_NO_ADMITTED_CANDIDATE"},None
    relevant=[r for r in predictions if r["target"]==target and r["feature_contract"]==winner["feature_contract"] and r["model"]==winner["model"] and r["fold_claim_status"]=="ADMITTED"]
    latest=sorted({r["fold_id"] for r in relevant})[-1];latest_predictions=[r for r in relevant if r["fold_id"]==latest]
    row_map={f'{r["canonical_project_id"]}|{r["anchor_month"]}':r for r in cohort};x=matrix([row_map[r["row_key"]] for r in latest_predictions],features)
    if winner["model"]=="equal_soft_vote": artifact={"members":{n:models[(latest,n)] for n in ("hist_gradient_boosting","random_forest","xgboost")},"ensemble":"equal_soft_vote","threshold":latest_predictions[0]["threshold"]}
    else:artifact={"member":models[(latest,winner["model"])],"threshold":latest_predictions[0]["threshold"]}
    artifact.update({"features":list(features),**common,"model_version":f'{target.lower()}-schedule-final-v3'})
    joblib.dump(artifact,directory/"pipeline.joblib");loaded=joblib.load(directory/"pipeline.joblib")
    reloaded=np.mean([apply_member(m,x) for m in loaded["members"].values()],axis=0) if loaded.get("ensemble") else apply_member(loaded["member"],x)
    expected=np.asarray([r["probability"] for r in latest_predictions]);parity=bool(np.allclose(reloaded,expected,rtol=0,atol=1e-12))
    if not parity:raise RuntimeError("SCHEDULE_SERIALIZATION_RELOAD_PARITY_FAIL")
    metadata={**common,"dataset_fingerprint":dataset_fp,"cohort_fingerprint":cohort_fp,"code_commit":code_commit,"fold_artifact":latest,"reload_parity":"PASS_AT_1E-12"}
    json_write(directory/"feature_manifest.json",{"version":winner["feature_contract"],"features":features,"known_at_t":True})
    json_write(directory/"target_contract.json",{**common,"version":f"{target}-3m-v3-explicit-revised-machine-provisional","approved_schedule_deterioration_only":True})
    json_write(directory/"model_card.json",{**common,"status":"RESEARCH_CANDIDATE_SELECTED","algorithm":winner["model"],"metrics":winner,"limitations":["machine-provisional labels","not MoSPI validated","not a causal model"]})
    json_write(directory/"training_metadata.json",metadata);json_write(directory/"split_definition.json",splits)
    json_write(directory/"calibration.json",{"method":"PLATT_ON_PAST_VALIDATION","fit_scope":"PAST_ONLY"})
    json_write(directory/"threshold_policy.json",{"method":"PAST_VALIDATION_F1","capacity_threshold_also_reported":True,"not_production_policy":True})
    json_write(directory/"dependency_metadata.json",{"python":sys.version.split()[0],"joblib":joblib.__version__})
    json_write(directory/"evaluation_summary.json",winner)
    return {"status":"SELECTED","model":winner["model"],"feature_contract":winner["feature_contract"]},relevant


def main(mode):
    require_research_authorization(mode)
    metadata=json.loads((DATA/"dataset_metadata.json").read_text(encoding="utf-8"));dataset_fp=metadata["dataset_fingerprint"]
    code_commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip()
    support=[];folds=[];metrics=[];predictions=[];calibrations=[];diversity=[];cache={};cohorts={}
    source_rows=read_csv(DATA/"project_month.csv");coverage={r["reporting_month"]:r["coverage_class"] for r in read_csv(DATA/"report_month.csv")}
    compatible={(r["canonical_project_id"],r["reporting_month"]) for r in source_rows if r.get("physical_progress_schema_available")=="TRUE"}
    specs=[]
    for target in ("S1","S2"):
        specs.extend([(target,3,"basic-long-history-v1",tuple(BASIC_LONG_HISTORY_V1)),(target,3,"compact-v2.1-calendar-safe",tuple(COMPACT_V2)),(target,6,"basic-long-history-v1",tuple(BASIC_LONG_HISTORY_V1))])
    for target,horizon,contract,features in specs:
        builder=build_basic_long_history if contract.startswith("basic") else build_compact_v2
        cohort,ledger,events=build_research_target(source_rows,coverage,target,horizon,builder,contract)
        if contract.startswith("compact"):
            cohort,ledger,events=restrict_feature_anchors(cohort,ledger,events,compatible)
        cohorts[(target,horizon,contract)]=cohort
        stem=f"{target.lower()}_{horizon}m_"+("basic" if contract.startswith("basic") else "compact_v2")
        write_csv(OUT/f"{stem}_candidate_ledger.csv",ledger);write_csv(OUT/f"{stem}_events.csv",events)
        fold=__import__('src.ml.schedule_experiment_v3',fromlist=['fold_support']).fold_support(cohort,horizon)
        counts=Counter(r["status"] for r in ledger)
        support.append({"target":target,"horizon_months":horizon,"feature_contract":contract,"eligible_anchors":len(cohort),"events":sum(int(r["event"]) for r in cohort),"non_events":sum(1-int(r["event"]) for r in cohort),"projects":len({r["canonical_project_id"] for r in cohort}),"prevalence":sum(int(r["event"]) for r in cohort)/len(cohort),"censored":counts["CENSORED"],"excluded":counts["EXCLUDED"],"admitted_folds":sum(r["status"]=="ADMITTED" for r in fold),"target_validation_status":TARGET_VALIDATION_STATUS,"research_mode":RESEARCH_MODE})
        folds.extend({"target":target,"horizon_months":horizon,"feature_contract":contract,**r} for r in fold)
        result=run_models(cohort,features,target,horizon,contract);m,p,c,d,models,_=result
        metrics.extend(m);predictions.extend(p);calibrations.extend(c);diversity.extend(d);cache[(target,horizon,contract)]=models
    summary=aggregate_metrics(metrics)
    write_csv(OUT/"target_support.csv",support);write_csv(OUT/"fold_summary.csv",folds);write_csv(OUT/"model_metrics.csv",metrics);write_csv(OUT/"temporal_metrics.csv",summary);write_csv(OUT/"calibration_summary.csv",calibrations);write_csv(OUT/"ensemble_diversity.csv",diversity)
    write_csv(OUT/"threshold_summary.csv",[{k:r[k] for k in ("target","horizon_months","feature_contract","fold_id","model","threshold","capacity_threshold","fold_claim_status")} for r in metrics])
    write_csv(OUT/"historical_oos_predictions.csv",predictions)
    selections={};bootstrap=[];leads=[];paired=[]
    for target in ("S1","S2"):
        winner=selected_candidate(summary,target);cohort=cohorts[(target,3,"basic-long-history-v1")];features=tuple(BASIC_LONG_HISTORY_V1)
        decision,relevant=write_model_contract(target,cohort,features,winner,predictions,cache[(target,3,"basic-long-history-v1")],[r for r in folds if r["target"]==target and r["horizon_months"]==3 and r["feature_contract"]=="basic-long-history-v1"],dataset_fp,code_commit);selections[target]=decision
        if relevant:
            bootstrap.extend({"target":target,"model":winner["model"],**r} for r in bootstrap_metrics(relevant,2000));leads.append({"target":target,"model":winner["model"],**lead_time(relevant)})
            for other in ("rule","logistic_regression","equal_soft_vote"):
                a={r["row_key"]:r for r in relevant};b={r["row_key"]:r for r in predictions if r["target"]==target and r["horizon_months"]==3 and r["feature_contract"]==winner["feature_contract"] and r["model"]==other and r["fold_claim_status"]=="ADMITTED"};keys=sorted(set(a)&set(b))
                if keys:
                    from sklearn.metrics import average_precision_score
                    y=[int(a[k]["event"]) for k in keys];paired.append({"target":target,"selected_model":winner["model"],"comparison_model":other,"common_rows":len(keys),"selected_pr_auc":average_precision_score(y,[a[k]["probability"] for k in keys]),"comparison_pr_auc":average_precision_score(y,[b[k]["probability"] for k in keys]),"status":"POINT_COMPARISON_BOOTSTRAP_SEPARATE"})
    no=[{"status":"NOT_EXECUTED","reason":"NO_SCHEDULE_MODEL_PASSED_RESEARCH_ADMISSION"}]
    write_csv(OUT/"bootstrap_summary.csv",bootstrap or no);write_csv(OUT/"lead_time_summary.csv",leads or no);write_csv(OUT/"paired_comparisons.csv",paired or no)
    write_csv(OUT/"model_selection.csv",[{"target":t,**d} for t,d in selections.items()])
    write_csv(OUT/"weighted_vote_summary.csv",[{"status":"WEIGHTED_VOTING_NOT_JUSTIFIED","reason":"equal voting evaluated first; no independent evidence requiring validation-selected weights"}])
    write_csv(OUT/"stacking_summary.csv",[{"status":"STACKING_NOT_JUSTIFIED","reason":"insufficient independent temporal OOF layers for leakage-safe meta-model selection"}])
    write_csv(OUT/"contributors_status.csv",[{"status":"WITHHELD","reason":"contributors require an admitted candidate and remain predictive, never causal"}])
    write_csv(OUT/"backend_integration_status.csv",[{"provider":"FrozenPredictionService","integration":"UNCHANGED_FAIL_CLOSED_NO_ADMITTED_SCHEDULE_CANDIDATE","production_release":"WITHHELD","probability_when_withheld":"NULL","risk_band_when_withheld":"NULL"}])
    status={"status":"COMPLETE_RESEARCH_EVALUATION" if any(d["status"]=="SELECTED" for d in selections.values()) else "PARTIAL","research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS,"production_release":"WITHHELD","dataset_fingerprint":dataset_fp,"code_commit":code_commit,"selection":selections,"weighted_voting":"WEIGHTED_VOTING_NOT_JUSTIFIED","stacking":"STACKING_NOT_JUSTIFIED","july_2026":"UNTOUCHED_PROSPECTIVE_HOLDOUT"}
    json_write(OUT/"schedule_final_status.json",status);print(json.dumps(status,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--research-mode",required=True);args=parser.parse_args();main(args.research_mode)
