"""Build and evaluate PRAHARI Cost Prediction V3 research."""
from __future__ import annotations

import argparse,hashlib,json,math,subprocess,sys
from collections import Counter,defaultdict
from pathlib import Path

import joblib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from src.ml.cost_experiment_v3 import aggregate_metrics,bootstrap_metrics,cost_folds,lead_time,run_temporal_models
from src.ml.cost_prediction_v2 import (COST_BASIC_C1,COST_BASIC_C2,COST_COMPACT_EXTRA,RESEARCH_MODE,TARGET_VALIDATION_STATUS,
    build_cost_target,cohort_fingerprint,cost_feature_registry,normalize_cost,peer_benchmark)
from src.ml.prediction_research_v2 import dataset_fingerprint,population_stability_index,read_csv,rolling_folds,write_csv
from src.ml.temporal_experiment_v2 import ensemble_diversity,model_factory

DATA=ROOT/"data/processed/longitudinal_2018_01_2026_06_cost_research_v3"
OUT=ROOT/"outputs/ml/cost_prediction_v3"
MODEL_ROOT=ROOT/"models/research/cost_prediction_v3"
DATASET_FINGERPRINT=""


def json_safe(obj):
    if isinstance(obj,float) and not math.isfinite(obj):return None
    if isinstance(obj,dict):return {str(key):json_safe(value_) for key,value_ in obj.items()}
    if isinstance(obj,(list,tuple)):return [json_safe(value_) for value_ in obj]
    return obj


def json_write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(json_safe(obj),indent=2,default=str,allow_nan=False)+"\n",encoding="utf-8")


def apply_serialized_member(member,x):
    model,calibrator,_=member
    raw=model.predict_proba(x)[:,1]
    if calibrator is None:return np.asarray(raw,dtype=float)
    clipped=np.clip(np.asarray(raw,dtype=float),1e-6,1-1e-6)
    return calibrator.predict_proba(np.log(clipped/(1-clipped)).reshape(-1,1))[:,1]


def model_configuration(features):
    result={"rule":{"threshold_concepts":["expenditure ratio","remaining schedule","project age"],"probabilities":[.25,.75]}}
    for name in ("logistic_regression","hist_gradient_boosting","random_forest","xgboost"):
        pipeline=model_factory(name,list(features));estimator=pipeline.named_steps["model"]
        result[name]={"estimator":type(estimator).__name__,"hyperparameters":estimator.get_params(deep=False),"imputation":"TRAINING_FOLD_MEDIAN_WITH_MISSING_INDICATORS","scaling":"StandardScaler" if name=="logistic_regression" else "NONE"}
    result["equal_soft_vote"]={"members":["hist_gradient_boosting","random_forest","xgboost"],"weights":[1/3,1/3,1/3]}
    return result


def write_nonselected_contract(target,cohort,feature_contract,features,split_rows,experiments):
    artifact_dir=MODEL_ROOT/target.lower();artifact_dir.mkdir(parents=True,exist_ok=True)
    json_write(artifact_dir/"feature_manifest.json",{"version":feature_contract,"features":list(features),"known_at_t":True})
    json_write(artifact_dir/"target_contract.json",{"target":target,"horizon_months":3,"version":f"{target}-v1-machine-provisional","anticipated_cost_is_label":False,"expenditure_is_label":False})
    json_write(artifact_dir/"model_card.json",{"status":"NO_RESEARCH_CANDIDATE_ADMITTED","model":None,"production_release":"WITHHELD","pipeline_artifact":"NOT_CREATED","limitations":["machine-provisional targets","temporal stability/admission criteria not met","predicts approved cost deterioration, not exact final cost"]})
    json_write(artifact_dir/"training_metadata.json",{"dataset_fingerprint":DATASET_FINGERPRINT,"cohort_fingerprint":cohort_fingerprint(cohort),"research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS,"fit_status":"NOT_FIT_AS_DEPLOYABLE_ARTIFACT"})
    json_write(artifact_dir/"split_definition.json",[r for r in split_rows if r['target']==target and r['feature_contract']==feature_contract])
    json_write(artifact_dir/"calibration.json",{"status":"NOT_ADMITTED","method":"PLATT_ON_PAST_VALIDATION_IN_BACKTESTS_ONLY"})
    json_write(artifact_dir/"threshold_policy.json",{"status":"NOT_ADMITTED","method":"PAST_VALIDATION_F1_IN_BACKTESTS_ONLY","not_production_policy":True})
    json_write(artifact_dir/"dependency_metadata.json",{"python":sys.version.split()[0],"joblib":joblib.__version__})
    json_write(artifact_dir/"evaluation_summary.json",{"status":"NO_COST_MODEL_PASSED_RESEARCH_ADMISSION"})


def rolling_support(cohorts):
    rows=[]
    for target in ("C1","C2"):
        cohort=cohorts[(target,3,"cost-basic-long-history-v1")]
        for window in (12,18,24):
            for fold in rolling_folds(cohort,3,window):
                rows.append({"target":target,"horizon_months":3,"window_months":window,**fold,
                             "model_evaluation_status":"SUPPORT_ONLY_PRIMARY_MODEL_NOT_ADMITTED"})
    return rows


def drift_summary(cohorts):
    rows=[]
    for target in ("C1","C2"):
        cohort=cohorts[(target,3,"cost-basic-long-history-v1")]
        early=[r for r in cohort if r['anchor_month']<'2025-01'];late=[r for r in cohort if r['anchor_month']>='2025-01']
        for feature in ("log_original_cost","expenditure_to_original_cost","expenditure_to_current_approved_cost","project_age_months"):
            rows.append({"target":target,"feature":feature,"reference_period":"before-2025-01","current_period":"2025-01-and-later",
                         "reference_rows":len(early),"current_rows":len(late),"psi":population_stability_index((r[feature] for r in early),(r[feature] for r in late)),
                         "interpretation":"DESCRIPTIVE_NON_CAUSAL_DRIFT_DIAGNOSTIC"})
        rows.append({"target":target,"feature":"target_prevalence","reference_period":"before-2025-01","current_period":"2025-01-and-later",
                     "reference_rows":len(early),"current_rows":len(late),"psi":"","reference_value":sum(r['event'] for r in early)/len(early) if early else "",
                     "current_value":sum(r['event'] for r in late)/len(late) if late else "","interpretation":"DESCRIPTIVE_NON_CAUSAL_DRIFT_DIAGNOSTIC"})
    return rows


def demo_fixtures(ledgers):
    fixtures=[]
    choices=[("C1_EVENT",next((r for r in ledgers[("C1",3)] if r['status']=='ELIGIBLE' and r['event']==1),None)),
             ("C2_EVENT",next((r for r in ledgers[("C2",3)] if r['status']=='ELIGIBLE' and r['event']==1),None)),
             ("NO_EVENT",next((r for r in ledgers[("C1",3)] if r['status']=='ELIGIBLE' and r['event']==0),None)),
             ("PREDICTION_WITHHELD",next((r for r in ledgers[("C1",3)] if r['status']=='CENSORED'),None)),
             ("DATA_VERIFICATION_REQUIRED",next((r for r in ledgers[("C1",3)] if 'CORRECTION' in r['correction_like_flags'] or 'REVERSAL' in r['correction_like_flags']),None))]
    for fixture_type,item in choices:
        if not item:continue
        fixtures.append({"fixture_type":fixture_type,"fixture_scope":"SOURCE_BACKED_TARGET_REVIEW_NOT_MODEL_PREDICTION","canonical_project_id":item['canonical_project_id'],"project_name":item['project_name'],"anchor_month":item['anchor_month'],"target":item['target'],"observed_machine_provisional_event":item['event'],"event_month":item['event_month'],"source_id":item['source_id'],"source_page":item['source_page'],"source_table":item['source_table'],"prediction_status":"WITHHELD","cost_probability":"","withheld_reason":"NO_COST_MODEL_PASSED_RESEARCH_ADMISSION" if item['status']=='ELIGIBLE' else item['primary_reason'],"machine_provisional":"TRUE","research_override":"TRUE"})
    return fixtures


def field_semantics_and_normalization(rows):
    contracts=[
        ("original_cost_raw","Original approved/sanctioned cost","C1 frozen baseline; C2 reference","Never replaced by revised/anticipated/expenditure"),
        ("revised_cost_raw","Approved revised cost as reported","C1/C2 event state","Only approved upward state changes can label events"),
        ("anticipated_cost_raw","Anticipated/estimated cost","Evidence flag only","Never an approved-revision label"),
        ("cumulative_expenditure_raw","Cumulative expenditure to reporting date","Known-at-T feature only","Not final cost and never a label"),
    ]
    semantics=[{"field":field,"source_semantics":meaning,"model_role":role,"guardrail":guardrail,"normalized_unit":"INR_CRORE","raw_preserved":"YES"} for field,meaning,role,guardrail in contracts]
    audit=[]
    for field,_,_,_ in contracts:
        normalized=[]
        for value_ in (r.get(field,"") for r in rows):
            try:normalized.append(normalize_cost(value_))
            except ValueError:normalized.append({"method":"AMBIGUOUS","value_crore":math.nan})
        present=[v for v in normalized if v["method"]!="MISSING"]
        audit.append({"field":field,"total_rows":len(rows),"semantic_missing":sum(v["method"]=="MISSING" for v in normalized),"non_missing_raw":len(present),"finite_normalized":sum(math.isfinite(v["value_crore"]) for v in present),"invalid_or_ambiguous":sum(not math.isfinite(v["value_crore"]) for v in present),"assumed_table_unit":"INR_CRORE","normalization_method":"TABLE_HEADER_CRORE_NO_SCALING","raw_preserved":"YES"})
    return semantics,audit


def cohort_audit(cohorts,ledgers):
    rows=[]
    for (target,horizon,contract),cohort in cohorts.items():
        if contract!="cost-basic-long-history-v1":continue
        ledger=ledgers[(target,horizon)]
        for schema,count in sorted(Counter(r.get("schema_family") or "UNKNOWN" for r in cohort).items()):
            rows.append({"target":target,"horizon_months":horizon,"metric":"ELIGIBLE_SCHEMA","category":schema,"count":count})
        for bucket,count in sorted(Counter("1-5" if r["history_span_months"]<6 else "6-11" if r["history_span_months"]<12 else "12-23" if r["history_span_months"]<24 else "24+" for r in cohort).items()):
            rows.append({"target":target,"horizon_months":horizon,"metric":"HISTORY_DEPTH_MONTHS","category":bucket,"count":count})
        for reason,count in Counter(r["primary_reason"] or "ELIGIBLE" for r in ledger).most_common():
            rows.append({"target":target,"horizon_months":horizon,"metric":"PRIMARY_DISPOSITION_REASON","category":reason,"count":count})
    return rows


def event_distribution(ledgers):
    rows=[]
    for (target,horizon),ledger in ledgers.items():
        if horizon not in (3,6):continue
        events=[r for r in ledger if r["status"]=="ELIGIBLE" and int(r["event"])==1]
        groupings={
            "year":lambda r:r["event_month"][:4],
            "schema_era":lambda r:r.get("schema_family") or "UNKNOWN",
            "cost_band":lambda r:("LT_500" if float(r["frozen_approved_cost_at_t"])<500 else "500_TO_2000" if float(r["frozen_approved_cost_at_t"])<2000 else "GE_2000"),
        }
        for dimension,function in groupings.items():
            for category,count in sorted(Counter(function(row) for row in events).items()):
                rows.append({"target":target,"horizon_months":horizon,"dimension":dimension,"category":category,"events":count})
    return rows


def before_after_support(current):
    old_path=ROOT/"outputs/ml/prediction_research_v2/cost/target_support_summary.csv"
    old=read_csv(old_path) if old_path.is_file() else []
    result=[]
    for target in ("C1","C2"):
        for horizon in (3,6):
            prior=next((r for r in old if r["target"]==target and int(r["horizon_months"])==horizon and r["feature_contract"]=="cost-basic-long-history-v1"),{})
            now=next(r for r in current if r["target"]==target and int(r["horizon_months"])==horizon and r["feature_contract"]=="cost-basic-long-history-v1")
            result.append({"target":target,"horizon_months":horizon,
                           "v2_eligible":prior.get("eligible_anchors",""),"v3_eligible":now["eligible_anchors"],
                           "v2_events":prior.get("events",""),"v3_events":now["events"],
                           "v2_projects":prior.get("projects",""),"v3_projects":now["projects"],
                           "v2_admitted_folds":prior.get("admitted_folds",""),"v3_admitted_folds":now["admitted_folds"]})
    return result


def longitudinal_cost_audit(rows):
    grouped=defaultdict(list)
    for row in rows:grouped[row["canonical_project_id"]].append(row)
    original_rows=[];revised_rows=[]
    for pid,history in sorted(grouped.items()):
        history.sort(key=lambda row:row["reporting_month"])
        originals=[normalize_cost(row.get("original_cost_raw",""))["value_crore"] for row in history]
        approved=[]
        for row in history:
            original=normalize_cost(row.get("original_cost_raw",""))["value_crore"]
            revised=normalize_cost(row.get("revised_cost_raw",""))["value_crore"]
            approved.append(revised if math.isfinite(revised) else original)
        original_changes=sum(math.isfinite(a) and math.isfinite(b) and abs(a-b)>max(.01,abs(a)*1e-6) for a,b in zip(originals,originals[1:]))
        downward=sum(math.isfinite(a) and math.isfinite(b) and b<a-max(.01,abs(a)*1e-6) for a,b in zip(approved,approved[1:]))
        upward=sum(math.isfinite(a) and math.isfinite(b) and b>a+max(.01,abs(a)*1e-6) for a,b in zip(approved,approved[1:]))
        original_rows.append({"canonical_project_id":pid,"observations":len(history),"first_month":history[0]["reporting_month"],"last_month":history[-1]["reporting_month"],
                              "original_cost_change_count":original_changes,"classification":"CONSISTENT" if not original_changes else "UNRESOLVED_TARGET_CENSORED"})
        revised_rows.append({"canonical_project_id":pid,"approved_upward_state_changes":upward,"approved_downward_or_reversal_changes":downward,
                             "classification":"UNRESOLVED_REVERSAL_TARGET_CENSORED" if downward else "MONOTONIC_OR_STABLE"})
    return original_rows,revised_rows


def parser_repair_summary(rows):
    grouped=Counter()
    for row in rows:
        if row.get("serial_recovery_method"):grouped[(row["reporting_month"],row["serial_recovery_method"])]+=1
        if row.get("overlay_recovery_method"):grouped[(row["reporting_month"],row["overlay_recovery_method"])]+=1
        if row.get("extraction_method")=="pdfplumber_table" and str(row.get("serial_number_raw","")).isdigit() and row.get("source_serial_number_raw"):
            grouped[(row["reporting_month"],"SOURCE_SERIAL_PRESERVED")]+=1
    return [{"reporting_month":month,"repair_method":method,"affected_rows":count,"scope":"EXTRACTION_ONLY_RAW_SOURCE_UNCHANGED"} for (month,method),count in sorted(grouped.items())]


def select_candidate(summary,target,horizon,contract):
    rows=[r for r in summary if r["target"]==target and int(r["horizon_months"])==horizon and r["feature_contract"]==contract and int(r["admitted_folds"])>=2]
    rule=next((r for r in rows if r["model"]=="rule"),None); learned=[r for r in rows if r["model"]!="rule"]
    acceptable=[r for r in learned if rule and r["mean_pr_auc"]>=rule["mean_pr_auc"]+.01 and r["worst_pr_auc"]>=rule["worst_pr_auc"]-.02 and r["mean_recall"]>=.10 and r["mean_false_alerts_per_100"]<=20 and r["mean_ece"]<=.10]
    rule_ok=rule and rule["mean_recall"]>=.10 and rule["mean_false_alerts_per_100"]<=20 and rule["mean_ece"]<=.10
    pool=acceptable or ([rule] if rule_ok else [])
    return max(pool,key=lambda r:(r["worst_pr_auc"],r["mean_pr_auc"],-r["mean_brier"])) if pool else None


def main(override: str):
    global DATASET_FINGERPRINT
    if override!=RESEARCH_MODE:raise RuntimeError("explicit --research-mode PROTOTYPE_RESEARCH_OVERRIDE required")
    code_commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    rows=read_csv(DATA/"project_month.csv"); coverage={r["reporting_month"]:r["coverage_class"] for r in read_csv(DATA/"report_month.csv")}
    metadata=json.loads((DATA/"dataset_metadata.json").read_text(encoding="utf-8"))
    DATASET_FINGERPRINT=dataset_fingerprint(rows)
    if metadata["dataset_fingerprint"]!=DATASET_FINGERPRINT:raise RuntimeError("V3_DATASET_FINGERPRINT_MISMATCH")
    semantics,normalization=field_semantics_and_normalization(rows)
    write_csv(OUT/"cost_field_semantics.csv",semantics);write_csv(OUT/"cost_normalization_audit.csv",normalization)
    field_audit=[{"audit_type":"SEMANTICS","field":row["field"],"status":"SEPARATE_SOURCE_FIELD","details":json.dumps(row,sort_keys=True)} for row in semantics]
    field_audit += [{"audit_type":"NORMALIZATION","field":row["field"],"status":"PASS" if not row["invalid_or_ambiguous"] else "REVIEW_REQUIRED","details":json.dumps(row,sort_keys=True)} for row in normalization]
    write_csv(OUT/"cost_field_audit.csv",field_audit)
    original_audit,revised_audit=longitudinal_cost_audit(rows)
    write_csv(OUT/"original_cost_consistency.csv",original_audit)
    write_csv(OUT/"revised_cost_trajectory_audit.csv",revised_audit)
    write_csv(OUT/"parser_repairs.csv",parser_repair_summary(rows))
    support=[];fold_rows=[];cohorts={};ledgers={};all_metrics=[];all_predictions=[];all_calibration=[];model_cache={};split_rows=[]
    compatible={(r["canonical_project_id"],r["reporting_month"]) for r in rows if r.get("physical_progress_schema_available")=="TRUE"}
    for target in ("C1","C2"):
        features=COST_BASIC_C2 if target=="C2" else COST_BASIC_C1
        for horizon in (3,6,12):
            cohort,ledger,events=build_cost_target(rows,coverage,target,horizon,False);key=(target,horizon,"cost-basic-long-history-v1")
            cohorts[key]=cohort;ledgers[(target,horizon)]=ledger
            write_csv(OUT/f"{target.lower()}_{horizon}m_basic_cohort.csv",cohort);write_csv(OUT/f"{target.lower()}_{horizon}m_target_ledger.csv",ledger);write_csv(OUT/f"{target.lower()}_{horizon}m_events.csv",events)
            folds=cost_folds(cohort,horizon)
            for f in folds:fold_rows.append({"target":target,"horizon_months":horizon,"feature_contract":key[2],**f})
            counts=Counter(r["status"] for r in ledger);support.append({"target":target,"horizon_months":horizon,"feature_contract":key[2],"eligible_anchors":len(cohort),"events":len(events),"non_events":len(cohort)-len(events),"projects":len({r['canonical_project_id'] for r in cohort}),"prevalence":len(events)/len(cohort) if cohort else 0,"censored":counts['CENSORED'],"excluded":counts['EXCLUDED'],"admitted_folds":sum(f['status']=='ADMITTED' for f in folds),"target_validation_status":TARGET_VALIDATION_STATUS,"research_mode":RESEARCH_MODE})
        cohort,ledger,events=build_cost_target(rows,coverage,target,3,True);cohort=[r for r in cohort if (r["canonical_project_id"],r["anchor_month"]) in compatible]
        ledger=[r for r in ledger if (r["canonical_project_id"],r["anchor_month"]) in compatible];events=[r for r in events if (r["canonical_project_id"],r["anchor_month"]) in compatible]
        key=(target,3,"cost-compact-v2");cohorts[key]=cohort;write_csv(OUT/f"{target.lower()}_3m_compact_cohort.csv",cohort);write_csv(OUT/f"{target.lower()}_3m_compact_target_ledger.csv",ledger)
        folds=cost_folds(cohort,3)
        for f in folds:fold_rows.append({"target":target,"horizon_months":3,"feature_contract":key[2],**f})
        counts=Counter(r["status"] for r in ledger);support.append({"target":target,"horizon_months":3,"feature_contract":key[2],"eligible_anchors":len(cohort),"events":len(events),"non_events":len(cohort)-len(events),"projects":len({r['canonical_project_id'] for r in cohort}),"prevalence":len(events)/len(cohort) if cohort else 0,"censored":counts['CENSORED'],"excluded":counts['EXCLUDED'],"admitted_folds":sum(f['status']=='ADMITTED' for f in folds),"target_validation_status":TARGET_VALIDATION_STATUS,"research_mode":RESEARCH_MODE})
    write_csv(OUT/"target_support_summary.csv",support);write_csv(OUT/"target_support_v3.csv",support);write_csv(OUT/"fold_summary.csv",fold_rows)
    write_csv(OUT/"target_support_before_after.csv",before_after_support(support))
    write_csv(OUT/"event_distribution_by_year.csv",event_distribution(ledgers))
    write_csv(OUT/"cohort_audit_summary.csv",cohort_audit(cohorts,ledgers))
    write_csv(OUT/"cost_feature_registry.csv",cost_feature_registry())
    write_csv(OUT/"rolling_window_support.csv",rolling_support(cohorts))
    drift=drift_summary(cohorts);write_csv(OUT/"cost_drift_summary.csv",drift);write_csv(OUT/"drift_summary.csv",drift)
    write_csv(OUT/"demo_fixture_references.csv",demo_fixtures(ledgers))
    admitted_6={t:next(r for r in support if r['target']==t and r['horizon_months']==6 and r['feature_contract']=='cost-basic-long-history-v1')['admitted_folds']>=2 for t in ('C1','C2')}
    experiments=[]
    for key,cohort in cohorts.items():
        target,horizon,contract=key
        if horizon==12 or (horizon==6 and not admitted_6[target]):continue
        features=(COST_BASIC_C2 if target=="C2" else COST_BASIC_C1)+(COST_COMPACT_EXTRA if contract=="cost-compact-v2" else ())
        metrics,predictions,calibration,models,splits=run_temporal_models(cohort,features,target,horizon,contract)
        all_metrics.extend(metrics);all_predictions.extend(predictions);all_calibration.extend(calibration);model_cache[key]=models
        split_rows.extend({"target":target,"horizon_months":horizon,"feature_contract":contract,**r} for r in splits)
        experiments.append({"experiment_id":f"COST-{target}-{horizon}M-{contract}","target":target,"horizon":horizon,"feature_contract":contract,"dataset_fingerprint":DATASET_FINGERPRINT,"cohort_fingerprint":cohort_fingerprint(cohort),"code_commit":code_commit,"research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS,
                            "temporal_splits":[r for r in splits],"model_configuration":model_configuration(features),"calibration":"PLATT_FIT_ON_PAST_VALIDATION_ONLY","threshold_policy":"PAST_VALIDATION_F1_ONLY","weighted_ensemble":"NOT_ADMITTED","stacking":"NOT_ADMITTED"})
    history_metrics=[]
    for target in ("C1","C2"):
        cohort=cohorts[(target,3,"cost-basic-long-history-v1")]
        features=COST_BASIC_C2 if target=="C2" else COST_BASIC_C1
        for window in (24,36,48):
            contract=f"cost-basic-long-history-v1-recent-{window}m"
            metrics,predictions,calibration,_,splits=run_temporal_models(cohort,features,target,3,contract,history_window_months=window)
            history_metrics.extend(metrics);all_metrics.extend(metrics);all_predictions.extend(predictions);all_calibration.extend(calibration)
            split_rows.extend({"target":target,"horizon_months":3,"feature_contract":contract,"history_window_months":window,**r} for r in splits)
    write_csv(OUT/"history_window_metrics.csv",aggregate_metrics(history_metrics))
    compact_status=[]
    for target in ("C1","C2"):
        basic=next(r for r in support if r["target"]==target and r["horizon_months"]==3 and r["feature_contract"]=="cost-basic-long-history-v1")
        compact=next(r for r in support if r["target"]==target and r["horizon_months"]==3 and r["feature_contract"]=="cost-compact-v2")
        compact_status.append({"target":target,"basic_eligible":basic["eligible_anchors"],"compact_eligible":compact["eligible_anchors"],
                               "compact_admitted_folds":compact["admitted_folds"],"decision":"NO_SUPERIORITY_CLAIM",
                               "reason":"Compact V2 lacks multiple admitted identical-anchor temporal folds"})
    write_csv(OUT/"basic_vs_compact.csv",compact_status)
    write_csv(OUT/"model_metrics.csv",all_metrics);write_csv(OUT/"project_cost_predictions.csv",all_predictions);write_csv(OUT/"calibration_summary.csv",all_calibration);write_csv(OUT/"split_definition.csv",split_rows)
    summary=aggregate_metrics(all_metrics);write_csv(OUT/"temporal_metrics.csv",summary)
    selected={};bootstrap=[];leads=[];paired=[];contributors=[];peer_rows=[]
    for target in ("C1","C2"):
        candidates=[]
        for contract in ("cost-basic-long-history-v1","cost-compact-v2"):
            candidate=select_candidate(summary,target,3,contract)
            if candidate:candidates.append(candidate)
        winner=max(candidates,key=lambda r:(r['worst_pr_auc'],r['mean_pr_auc'],-r['mean_brier'])) if candidates else None
        if not winner:
            contract="cost-basic-long-history-v1";key=(target,3,contract)
            write_nonselected_contract(target,cohorts[key],contract,COST_BASIC_C2 if target=='C2' else COST_BASIC_C1,split_rows,experiments)
            continue
        selected[target]=winner
        relevant=[r for r in all_predictions if r['target']==target and int(r['horizon_months'])==3 and r['feature_contract']==winner['feature_contract'] and r['model']==winner['model']]
        bootstrap.extend({"target":target,"model":winner['model'],"feature_contract":winner['feature_contract'],**r} for r in bootstrap_metrics(relevant,2000))
        leads.append({"target":target,"model":winner['model'],"feature_contract":winner['feature_contract'],**lead_time(relevant)})
        rule=[r for r in all_predictions if r['target']==target and int(r['horizon_months'])==3 and r['feature_contract']==winner['feature_contract'] and r['model']=='rule']
        if len(rule)==len(relevant):
            a={r['row_key']:r for r in relevant};b={r['row_key']:r for r in rule};keys=sorted(set(a)&set(b));y=[int(a[k]['event']) for k in keys]
            paired.append({"target":target,"model_a":winner['model'],"model_b":"rule","common_rows":len(keys),"pr_auc_a":__import__('sklearn.metrics',fromlist=['average_precision_score']).average_precision_score(y,[a[k]['probability'] for k in keys]),"pr_auc_b":__import__('sklearn.metrics',fromlist=['average_precision_score']).average_precision_score(y,[b[k]['probability'] for k in keys]),"status":"POINT_COMPARISON; CLUSTER_CI_IN_BOOTSTRAP_SUMMARY"})
        contract=winner['feature_contract'];key=(target,3,contract);models=model_cache[key]
        candidate_folds=sorted({r['fold_id'] for r in relevant});latest_fold=candidate_folds[-1] if candidate_folds else None
        if latest_fold:
            feature_names=list((COST_BASIC_C2 if target=='C2' else COST_BASIC_C1)+(COST_COMPACT_EXTRA if contract=='cost-compact-v2' else ()))
            latest_predictions=[r for r in relevant if r['fold_id']==latest_fold]
            row_map={r['row_key']:r for r in cohorts[key]};x=np.asarray([[float(row_map[r['row_key']].get(name,math.nan)) for name in feature_names] for r in latest_predictions])
            if winner['model']=='equal_soft_vote':
                members={name:models[(latest_fold,name)] for name in ('hist_gradient_boosting','random_forest','xgboost')}
                threshold=float(latest_predictions[0]['threshold']);artifact={"members":members,"ensemble":"equal_soft_vote","threshold":threshold}
            else:
                model,calibrator,threshold=models[(latest_fold,winner['model'])];artifact={"model":model,"calibrator":calibrator,"threshold":threshold}
            artifact.update({"features":feature_names,"target":target,"horizon":3,"research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS})
            artifact_dir=MODEL_ROOT/target.lower();artifact_dir.mkdir(parents=True,exist_ok=True)
            joblib.dump(artifact,artifact_dir/"pipeline.joblib");reloaded=joblib.load(artifact_dir/"pipeline.joblib")
            if reloaded.get("ensemble")=='equal_soft_vote':reloaded_probability=np.mean([apply_serialized_member(member,x) for member in reloaded["members"].values()],axis=0)
            else:reloaded_probability=apply_serialized_member((reloaded["model"],reloaded["calibrator"],reloaded["threshold"]),x)
            expected_probability=np.asarray([float(r["probability"]) for r in latest_predictions])
            if not np.allclose(reloaded_probability,expected_probability,rtol=0,atol=1e-12):raise RuntimeError("V3_SERIALIZATION_RELOAD_PARITY_FAIL")
            reference_member=next(iter(reloaded["members"].values())) if reloaded.get("ensemble") else (reloaded["model"],reloaded["calibrator"],reloaded["threshold"])
            reference=np.asarray(reference_member[0].named_steps["impute"].statistics_[:len(feature_names)],dtype=float)
            impact=np.zeros((len(latest_predictions),len(feature_names)))
            for column in range(len(feature_names)):
                altered=x.copy();altered[:,column]=reference[column]
                if reloaded.get("ensemble")=='equal_soft_vote':altered_probability=np.mean([apply_serialized_member(member,altered) for member in reloaded["members"].values()],axis=0)
                else:altered_probability=apply_serialized_member((reloaded["model"],reloaded["calibrator"],reloaded["threshold"]),altered)
                impact[:,column]=reloaded_probability-altered_probability
            for row_index,prediction in enumerate(latest_predictions):
                order=np.argsort(np.abs(impact[row_index]))[::-1][:3]
                for rank,column in enumerate(order,1):
                    contributors.append({"canonical_project_id":prediction["canonical_project_id"],"anchor_month":prediction["anchor_month"],"target":target,
                                         "model":winner["model"],"feature":feature_names[column],"feature_value":x[row_index,column],
                                         "direction":"INCREASED_WARNING" if impact[row_index,column]>0 else "DECREASED_WARNING",
                                         "contribution_magnitude":abs(float(impact[row_index,column])),"rank":rank,
                                         "interpretation":"PREDICTIVE CONTRIBUTOR; COUNTERFACTUAL REFERENCE IS TRAINING-FOLD MEDIAN; NOT CAUSAL"})
            if latest_predictions:
                project=row_map[latest_predictions[0]["row_key"]];peers=[row_map[item["row_key"]] for item in latest_predictions]
                for metric in ("current_approved_cost_revision_pct","expenditure_to_original_cost","project_age_months","remaining_schedule_months","physical_progress","recent_expenditure_velocity"):
                    if metric in project:
                        peer_rows.append({"target":target,"canonical_project_id":project["canonical_project_id"],"anchor_month":project["anchor_month"],**peer_benchmark(project,peers,metric)})
            json_write(artifact_dir/"feature_manifest.json",{"version":contract,"features":artifact['features'],"known_at_t":True})
            json_write(artifact_dir/"target_contract.json",{"target":target,"horizon_months":3,"version":f"{target}-v1-machine-provisional","anticipated_cost_is_label":False,"expenditure_is_label":False})
            json_write(artifact_dir/"model_card.json",{"status":"RESEARCH_CANDIDATE_SELECTED","model":winner['model'],"production_release":"WITHHELD","limitations":["machine-provisional targets","no official MoSPI approval","predicts approved cost deterioration, not exact final cost"]})
            json_write(artifact_dir/"training_metadata.json",{"dataset_fingerprint":DATASET_FINGERPRINT,"cohort_fingerprint":next(e['cohort_fingerprint'] for e in experiments if e['target']==target and e['horizon']==3 and e['feature_contract']==contract),"fold_artifact":latest_fold,"reload_parity":"PASS_AT_1E-12","research_mode":RESEARCH_MODE})
            json_write(artifact_dir/"split_definition.json",[r for r in split_rows if r['target']==target and r['feature_contract']==contract])
            json_write(artifact_dir/"calibration.json",{"method":"PLATT_ON_PAST_VALIDATION","threshold":threshold})
            json_write(artifact_dir/"threshold_policy.json",{"method":"PAST_VALIDATION_F1","not_production_policy":True})
            json_write(artifact_dir/"dependency_metadata.json",{"python":sys.version.split()[0],"joblib":joblib.__version__})
            json_write(artifact_dir/"evaluation_summary.json",winner)
    no_candidate=[{"status":"NOT_EXECUTED","reason":"NO_COST_MODEL_PASSED_RESEARCH_ADMISSION"}]
    write_csv(OUT/"bootstrap_uncertainty.csv",bootstrap or no_candidate);write_csv(OUT/"bootstrap_summary.csv",bootstrap or no_candidate)
    write_csv(OUT/"lead_time_summary.csv",leads or no_candidate);write_csv(OUT/"paired_comparisons.csv",paired or no_candidate)
    diversity=[]
    for target in ("C1","C2"):
      for horizon in (3,6):
       for contract in ("cost-basic-long-history-v1","cost-compact-v2"):
        subset=[r for r in all_predictions if r['target']==target and int(r['horizon_months'])==horizon and r['feature_contract']==contract]
        for fold in sorted({r['fold_id'] for r in subset}):
         maps={name:{r['row_key']:r for r in subset if r['fold_id']==fold and r['model']==name} for name in ('hist_gradient_boosting','random_forest','xgboost')};keys=set.intersection(*(set(v) for v in maps.values())) if all(maps.values()) else set()
         if keys:
          keys=sorted(keys);matrix=np.asarray([[float(maps[n][k]['probability']) for k in keys] for n in maps]);y=[int(maps['hist_gradient_boosting'][k]['event']) for k in keys]
          diversity.extend({"target":target,"horizon_months":horizon,"feature_contract":contract,"fold_id":fold,**r} for r in ensemble_diversity(y,matrix))
    write_csv(OUT/"ensemble_diversity.csv",diversity)
    write_csv(OUT/"cost_contributors.csv",contributors if contributors else [{"status":"NOT_AVAILABLE","reason":"NO_COST_MODEL_PASSED_RESEARCH_ADMISSION; contributors must not be fabricated"}])
    write_csv(OUT/"feature_importance.csv",contributors if contributors else [{"status":"NOT_AVAILABLE","reason":"NO_COST_MODEL_PASSED_RESEARCH_ADMISSION; contributors must not be fabricated"}])
    write_csv(OUT/"peer_benchmark_status.csv",peer_rows if peer_rows else [{"status":"WITHHELD","reason":"NO_COST_MODEL_PASSED_RESEARCH_ADMISSION"}])
    write_csv(OUT/"driver_analysis_status.csv",[{"status":"WITHHELD","reason":"NO_COST_MODEL_PASSED_RESEARCH_ADMISSION; predictive contributors must not be presented as causes"}])
    write_csv(OUT/"backend_integration_status.csv",[{"cost_intelligence":"WITHHELD","prediction_provider":"UNCHANGED_FAIL_CLOSED","officer_decision":"NO_COST_RISK_SIGNAL_WITHOUT_AVAILABLE_RESEARCH_PREDICTION","production_release":"WITHHELD"}])
    write_csv(OUT/"weighted_vote_summary.csv",[{"status":"NOT_ADMITTED","reason":"Equal ensemble evaluated first; no independent past-validation evidence of material weighted-vote gain"}])
    write_csv(OUT/"stacking_summary.csv",[{"status":"COST_STACKING_NOT_JUSTIFIED","reason":"insufficient independent temporal OOF layers for leakage-safe meta-model selection"}])
    write_csv(OUT/"cost_cuf_matrix.csv",cost_cuf_matrix())
    json_write(OUT/"experiment_registry.json",experiments)
    selection_status="RESEARCH_CANDIDATE_SELECTED_PRODUCTION_WITHHELD" if selected else "NO_COST_MODEL_PASSED_RESEARCH_ADMISSION"
    status={"status":"COMPLETE_RESEARCH_EVALUATION" if selected else "PARTIAL","research_mode":RESEARCH_MODE,"target_validation_status":TARGET_VALIDATION_STATUS,"production_model_release":"WITHHELD","dataset_fingerprint":DATASET_FINGERPRINT,"code_commit":code_commit,"support":support,"selected_research_candidates":selected,"selection_status":selection_status,"six_month_support_admitted":admitted_6,"six_month_model_status":{target:("RESEARCH_EVALUATED" if admitted_6[target] else "INSUFFICIENT_ADMITTED_FOLDS") for target in ("C1","C2")},"twelve_month_status":"SUPPORT_CHECK_ONLY_NOT_OPERATIONAL","magnitude_forecast":"COST_MAGNITUDE_FORECAST_NOT_READY","weighted_vote":"NOT_ADMITTED_PENDING_MATERIAL_VALIDATION_GAIN","stacking":"COST_STACKING_NOT_JUSTIFIED","rolling_sensitivity":"EVALUATED_24_36_48_MONTHS","july_2026":"PROSPECTIVE_RESEARCH_ONLY_NOT_USED_OR_SCORED"}
    json_write(OUT/"cost_v3_status.json",status);print(json.dumps({"support":support,"selected":selected,"six_month":admitted_6},indent=2,default=str))


def cost_cuf_matrix():
    rows=[]
    specs=[("log_original_cost","Original Cost","NO_VERIFIED_CUF_EVIDENCE_IN_REPOSITORY","YES","YES","YES","YES","NO"),("expenditure_to_original_cost","Cumulative Expenditure + Original Cost","NO_VERIFIED_CUF_EVIDENCE_IN_REPOSITORY","YES","YES","YES","YES","NO"),("expenditure_to_current_approved_cost","Cumulative Expenditure + Revised Cost","NO_VERIFIED_CUF_EVIDENCE_IN_REPOSITORY","YES","YES","YES","YES","NO"),("current_approved_cost_revision_pct","Original + Revised Cost","NO_VERIFIED_CUF_EVIDENCE_IN_REPOSITORY","YES","NO","YES","YES","NO"),("physical_progress","Physical Progress","VERIFIED_PUBLIC_PAIMANA_FIELD","PARTIAL","YES","YES","YES","NO"),("recent_expenditure_velocity","Monthly expenditure observations","DERIVED_FROM_CURRENT_FLASH_REPORT_FIELDS","YES","YES","YES","YES","NO"),("contractor_performance","Unverified contractor history","NO","NO","NO","NO","NO","YES")]
    for feature,source,verified,historical,c1,c2,derived,proposed in specs:rows.append({"feature":feature,"source_field":source,"officially_verified_cuf_field":verified,"available_historically":historical,"used_c1":c1,"used_c2":c2,"derived":derived,"structurally_missing_older_era":"YES" if feature=='physical_progress' else "NO","proposed_future_augmentation":proposed})
    return rows


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--research-mode",required=True);args=parser.parse_args();main(args.research_mode)
