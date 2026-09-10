from __future__ import annotations
import csv,json,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.trust.data_trust import DataTrustEvaluator,frontend_view
from src.decision.governance import ModelReleaseStatus,assess_prediction_eligibility
from src.ml.final_prediction import _completed
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
    rows=read(ROOT/'data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv');coverage={r['reporting_month']:r['coverage_class'] for r in read(ROOT/'data/metadata/source_coverage_2023_07_2026_06.csv')};manifest={r['source_id']:r for r in read(ROOT/'data/metadata/source_manifest.csv')};by=defaultdict(list)
    for r in rows:by[r['canonical_project_id']].append(r)
    evaluator=DataTrustEvaluator(coverage,manifest);results=[];reasons=Counter()
    for pid,history in sorted(by.items()):
        result=evaluator.evaluate(history,'2026-06');d=result.to_dict();eligibility=assess_prediction_eligibility(result,ModelReleaseStatus(),project_completed=bool(history and _completed(sorted(history,key=lambda x:x['reporting_month'])[-1])));results.append({**frontend_view(result),'canonical_project_id':pid,'observed_history_months':d['observed_history_months'],'history_span_months':d['history_span_months'],'contiguous_recent_history':d['contiguous_recent_history'],'prediction':'ELIGIBLE' if eligibility.prediction_eligible else 'WITHHELD','eligibility_reason_codes':'|'.join(eligibility.reason_codes)});reasons.update(eligibility.reason_codes)
    out=ROOT/'outputs/trust';out.mkdir(parents=True,exist_ok=True)
    with (out/'data_trust_latest_population.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    release_only={'HUMAN_TARGET_VALIDATION_PENDING','CALIBRATION_NOT_CONFIRMED','MODEL_NOT_RELEASED'}
    summary={'as_of_month':'2026-06','total_projects':len(results),'eligible':sum(r['prediction']=='ELIGIBLE' for r in results),'withheld':sum(r['prediction']=='WITHHELD' for r in results),'technically_ready_except_scientific_release':sum(set(filter(None,r['eligibility_reason_codes'].split('|')))<=release_only for r in results),'reason_counts':dict(reasons),'operational_probabilities_created':0,'trust_contract_version':'data-trust-v1'}
    (out/'data_trust_latest_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    demos=[]
    predicates=[('STRONG_DATA_PENDING_RELEASE',lambda r:set(filter(None,r['eligibility_reason_codes'].split('|')))<=release_only),('INSUFFICIENT_HISTORY',lambda r:r['history']=='INSUFFICIENT_HISTORY'),('SOURCE_GAP',lambda r:int(r['source_gap_count'])>0),('PROVENANCE_RICH',lambda r:r['source']=='VERIFIED_SOURCE'),('COMPLETED_OR_INELIGIBLE',lambda r:'PROJECT_COMPLETED' in r['eligibility_reason_codes'])]
    used=set()
    for label,p in predicates:
        found=next((r for r in results if r['canonical_project_id'] not in used and p(r)),None)
        if found:used.add(found['canonical_project_id']);demos.append({'demo_type':label,**found})
    with (out/'data_trust_demo_cases.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(demos[0]));w.writeheader();w.writerows(demos)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
