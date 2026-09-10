"""Train and freeze the canonical, machine-label-provisional S1/S2 models."""
from __future__ import annotations

import csv, hashlib, json, math, platform, subprocess, sys
from collections import defaultdict
from pathlib import Path

import joblib, numpy as np, pandas as pd, sklearn, xgboost
from sklearn.calibration import calibration_curve
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

ROOT=Path(__file__).resolve().parents[1]; SEED=26103
sys.path.insert(0, str(ROOT))
from src.ml.final_prediction import COMPACT_V2, FEATURE_VERSION, HORIZON_MONTHS, TARGET_VERSION, build_target, ledger_counts
DATA=ROOT/'data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv'
COVERAGE=ROOT/'data/metadata/source_coverage_2023_07_2026_06.csv'
OUT=ROOT/'outputs/ml/final_prediction_v1'; MODELS=ROOT/'models/prediction'

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True); rows=list(rows)
    if not rows:return
    fields=list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def split(month): return 'TRAIN' if month<='2025-05' else 'VALIDATION' if month<='2025-11' else 'TEST'
def matrix(rows): return np.asarray([[r[n] for n in COMPACT_V2] for r in rows],float)
def estimator(name):
    if name=='LOGISTIC': return Pipeline([('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),('scale',StandardScaler()),('model',LogisticRegression(max_iter=2500,class_weight='balanced',random_state=SEED))])
    if name=='HIST_GB': return Pipeline([('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),('model',HistGradientBoostingClassifier(max_iter=150,learning_rate=.05,max_depth=3,random_state=SEED))])
    if name=='RANDOM_FOREST': return Pipeline([('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),('model',RandomForestClassifier(n_estimators=500,min_samples_leaf=2,class_weight='balanced',random_state=SEED,n_jobs=-1))])
    if name=='XGBOOST': return Pipeline([('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),('model',XGBClassifier(n_estimators=300,max_depth=5,learning_rate=.05,subsample=.8,colsample_bytree=.8,min_child_weight=3,reg_lambda=1,objective='binary:logistic',eval_metric='logloss',random_state=SEED,n_jobs=-1))])
    raise ValueError(name)
def metric(y,p,threshold):
    pred=p>=threshold; tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    clipped=np.clip(p,1e-6,1-1e-6); z=np.log(clipped/(1-clipped)).reshape(-1,1)
    diagnostic=LogisticRegression(C=1e6,max_iter=2000).fit(z,y)
    return {'anchors':len(y),'events':int(y.sum()),'prevalence':float(y.mean()),'pr_auc':float(average_precision_score(y,p)),'roc_auc':float(roc_auc_score(y,p)),'brier':float(brier_score_loss(y,p)),'ece':ece(y,p),'calibration_intercept':float(diagnostic.intercept_[0]),'calibration_slope':float(diagnostic.coef_[0,0]),'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),'false_alerts_per_100':100*fp/len(y),'alert_rate':float(pred.mean()),'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp),'threshold':float(threshold)}
def ece(y,p,bins=10):
    edges=np.linspace(0,1,bins+1); total=0
    for lo,hi in zip(edges[:-1],edges[1:]):
        mask=(p>=lo)&(p<(hi if hi<1 else hi+1e-9))
        if mask.any(): total += mask.mean()*abs(p[mask].mean()-y[mask].mean())
    return float(total)
def calibrator(raw,y):
    z=np.log(np.clip(raw,1e-6,1-1e-6)/(1-np.clip(raw,1e-6,1-1e-6))).reshape(-1,1)
    return LogisticRegression(random_state=SEED).fit(z,y)
def apply_cal(cal,raw):
    p=np.clip(raw,1e-6,1-1e-6); return cal.predict_proba(np.log(p/(1-p)).reshape(-1,1))[:,1]
def rule_scores(rows):
    return np.array([float((np.isfinite(r['consecutive_stagnant']) and r['consecutive_stagnant']>=2) or (np.isfinite(r['low_progress_near_deadline']) and r['low_progress_near_deadline']==1)) for r in rows])
def fingerprint(rows):
    keys='\n'.join(sorted(f"{r['canonical_project_id']}|{r['anchor_month']}|{r.get('event','')}" for r in rows))
    return hashlib.sha256(keys.encode()).hexdigest()

def run():
    rows=read(DATA); coverage={r['reporting_month']:r['coverage_class'] for r in read(COVERAGE)}
    all_metrics=[]; rolling=[]; short=[]; lead=[]; summaries={}
    for target in ('S1','S2'):
        cohort,ledger,events=build_target(rows,coverage,target,HORIZON_MONTHS)
        parts={s:[r for r in cohort if split(r['anchor_month'])==s] for s in ('TRAIN','VALIDATION','TEST')}
        write(OUT/f'{target.lower()}_candidate_ledger.csv',ledger); write(OUT/f'{target.lower()}_event_ledger.csv',events)
        write(OUT/f'{target.lower()}_machine_label_sensitivity.csv',[{'scenario':'BASE_MACHINE_LABEL','eligible_anchors':len(cohort),'positive_anchors':sum(r['event'] for r in cohort)},{'scenario':'STRICT_EXCLUDE_CORRECTION_LIKE_EVENTS','eligible_anchors':len(cohort)-sum(str(r.get('possible_correction_flag')).lower()=='true' for r in events),'positive_anchors':sum(r['event'] for r in cohort)-sum(str(r.get('possible_correction_flag')).lower()=='true' for r in events),'excluded_suspicious_positive_anchors':sum(str(r.get('possible_correction_flag')).lower()=='true' for r in events)}])
        fitted={}; probabilities={}
        val_y=np.array([r['event'] for r in parts['VALIDATION']],int)
        for name in ('LOGISTIC','HIST_GB','RANDOM_FOREST','XGBOOST'):
            model=estimator(name); model.fit(matrix(parts['TRAIN']),np.array([r['event'] for r in parts['TRAIN']],int)); fitted[name]=model
            valp=model.predict_proba(matrix(parts['VALIDATION']))[:,1]; threshold=float(np.quantile(valp,.90))
            for s,part in parts.items():
                y=np.array([r['event'] for r in part],int); p=model.predict_proba(matrix(part))[:,1]
                all_metrics.append({'target':target,'model':name,'split':s,'calibration':'RAW',**metric(y,p,threshold)})
            probabilities[name]=model.predict_proba(matrix(parts['TEST']))[:,1]
        for s,part in parts.items():
            y=np.array([r['event'] for r in part],int);all_metrics.append({'target':target,'model':'RULE','split':s,'calibration':'NONE',**metric(y,rule_scores(part),.5)})
        # HistGB is the predeclared conservative artifact candidate. Platt is validation-fit only.
        chosen='HIST_GB'; raw_val=fitted[chosen].predict_proba(matrix(parts['VALIDATION']))[:,1]; cal=calibrator(raw_val,val_y)
        val_cal=apply_cal(cal,raw_val); threshold=float(np.quantile(val_cal,.90)); test=parts['TEST']; ytest=np.array([r['event'] for r in test],int); test_cal=apply_cal(cal,probabilities[chosen])
        all_metrics.append({'target':target,'model':'HIST_GB_PLATT','split':'TEST','calibration':'PLATT_VALIDATION_ONLY',**metric(ytest,test_cal,threshold)})
        # Month-wise rolling origin; threshold is fitted on the latest available training month predictions.
        months=sorted({r['anchor_month'] for r in cohort})
        for i in range(2,len(months)):
            train=[r for r in cohort if r['anchor_month']<months[i]]; testfold=[r for r in cohort if r['anchor_month']==months[i]]
            if len({r['event'] for r in train})<2 or len({r['event'] for r in testfold})<2: continue
            for name in ('LOGISTIC','HIST_GB','RANDOM_FOREST','XGBOOST'):
                m=estimator(name);m.fit(matrix(train),np.array([r['event'] for r in train])); tp=m.predict_proba(matrix(train))[:,1];th=float(np.quantile(tp,.90));y=np.array([r['event'] for r in testfold]);p=m.predict_proba(matrix(testfold))[:,1]
                rolling.append({'target':target,'test_month':months[i],'model':name,**metric(y,p,th)})
        # Short-history uses the fixed test partition and fixed validation threshold.
        for name,p in probabilities.items():
            th=next(r['threshold'] for r in all_metrics if r['target']==target and r['model']==name and r['split']=='TEST')
            for label,lo,hi in [('2-3',2,3),('4-6',4,6),('7-12',7,12),('>12',13,10**9)]:
                idx=[i for i,r in enumerate(test) if lo<=r['history_span_months']<=hi]
                if not idx: continue
                y=ytest[idx];pp=p[idx]; row={'target':target,'model':name,'history_band':label,**metric(y,pp,th)}
                short.append(row)
        # Event-level warning lead time for chosen raw model using its validation threshold.
        th=next(r['threshold'] for r in all_metrics if r['target']==target and r['model']==chosen and r['split']=='TEST')
        event_warn=defaultdict(list)
        for r,p in zip(test,probabilities[chosen]):
            if r['event'] and r['event_month'] and p>=th:
                leadm=(int(r['event_month'][:4])-int(r['anchor_month'][:4]))*12+int(r['event_month'][5:])-int(r['anchor_month'][5:])
                event_warn[(r['canonical_project_id'],r['event_month'])].append(leadm)
        event_keys={(r['canonical_project_id'],r['event_month']) for r in test if r['event']}
        leads=[max(event_warn[k]) for k in event_keys if k in event_warn]
        lead.append({'target':target,'model':chosen,'events':len(event_keys),'events_warned':len(leads),'warning_rate':len(leads)/len(event_keys) if event_keys else 0,'median':float(np.median(leads)) if leads else None,'p25':float(np.percentile(leads,25)) if leads else None,'p75':float(np.percentile(leads,75)) if leads else None,'minimum':min(leads) if leads else None,'maximum':max(leads) if leads else None,'ge_1':sum(x>=1 for x in leads)/len(event_keys) if event_keys else 0,'ge_2':sum(x>=2 for x in leads)/len(event_keys) if event_keys else 0,'ge_3':sum(x>=3 for x in leads)/len(event_keys) if event_keys else 0})
        artifact=MODELS/target.lower()/'v1';artifact.mkdir(parents=True,exist_ok=True)
        joblib.dump({'model':fitted[chosen],'calibrator':cal,'threshold':threshold,'features':COMPACT_V2,'target':target},artifact/'pipeline.joblib')
        dep={'python':platform.python_version(),'scikit_learn':sklearn.__version__,'xgboost':xgboost.__version__,'numpy':np.__version__,'pandas':pd.__version__,'joblib':joblib.__version__}
        meta={'status':'RESEARCH_VALIDATED_MACHINE_LABELS_HUMAN_REVIEW_PENDING','target':target,'target_version':TARGET_VERSION[target],'feature_version':FEATURE_VERSION,'horizon_months':3,'selected_candidate':chosen,'selection_basis':'predeclared conservative reproducible candidate; not selected by final test outcome','dataset_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'cohort_fingerprint':fingerprint(cohort),'code_commit_at_training':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'cohort_rows':len(cohort),'events':sum(r['event'] for r in cohort),'projects':len({r['canonical_project_id'] for r in cohort}),'splits':{s:{'months':sorted({r['anchor_month'] for r in p}),'anchors':len(p),'events':sum(r['event'] for r in p),'row_fingerprint':fingerprint(p)} for s,p in parts.items()},'ledger':ledger_counts(ledger),'probability_display':'WITHHELD_PENDING_HUMAN_ADJUDICATION_AND_INDEPENDENT_CALIBRATION_CONFIRMATION','dependencies':dep}
        for filename,payload in [('feature_manifest.json',{'version':FEATURE_VERSION,'ordered_features':list(COMPACT_V2)}),('target_contract.json',{'version':TARGET_VERSION[target],'target':target,'horizon_months':3}),('reliability_contract.json',{'bands':['HIGH','MODERATE','LOW','WITHHELD'],'probability_independent':True}),('threshold_policy.json',{'policy':'90th percentile validation review capacity','not_probability_cutoff':True}),('training_metadata.json',meta),('dependency_metadata.json',dep),('model_card.json',{'target':target,'status':meta['status'],'intended_use':'SIH research prototype after explicit availability checks','prohibited_use':['causal attribution','automated sanctions','production probability claims']})]:
            (artifact/filename).write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
        summaries[target]=meta
    write(OUT/'model_comparison.csv',all_metrics);write(OUT/'rolling_folds.csv',rolling);write(OUT/'short_history.csv',short);write(OUT/'lead_time.csv',lead)
    (OUT/'run_metadata.json').write_text(json.dumps(summaries,indent=2)+'\n',encoding='utf-8')
    return summaries
if __name__=='__main__': print(json.dumps(run(),indent=2))
