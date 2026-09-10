from __future__ import annotations
import csv,json,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.decision.governance import ModelReleaseStatus,assess_prediction_eligibility,decide_review
from src.ml.final_prediction import _completed
from src.trust.data_trust import DataTrustEvaluator
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
    rows=read(ROOT/'data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv');coverage={r['reporting_month']:r['coverage_class'] for r in read(ROOT/'data/metadata/source_coverage_2023_07_2026_06.csv')};manifest={r['source_id']:r for r in read(ROOT/'data/metadata/source_manifest.csv')};by=defaultdict(list)
    for row in rows:by[row['canonical_project_id']].append(row)
    evaluator=DataTrustEvaluator(coverage,manifest);release=ModelReleaseStatus();items=[];counts=Counter()
    for pid,history in sorted(by.items()):
        history=sorted(history,key=lambda x:x['reporting_month']);trust=evaluator.evaluate(history,'2026-06');completed=_completed(history[-1]);eligibility=assess_prediction_eligibility(trust,release,project_completed=completed);decision=decide_review(trust=trust,eligibility=eligibility,project_completed=completed);record=decision.to_dict();items.append(record);counts[decision.review_state]+=1
    out=ROOT/'outputs/decision';out.mkdir(parents=True,exist_ok=True)
    with (out/'officer_review_queue_current.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
    completed=sum('COMPLETED_PROJECT' in x['reason_codes'] for x in items);summary={'as_of_month':'2026-06','total_projects':len(items),'risk_driven':counts['REVIEW_RECOMMENDED'],'data_verification':counts['DATA_VERIFICATION_REQUIRED'],'model_release_pending':counts['PREDICTION_WITHHELD'],'completed_or_ineligible':completed,'no_actionable_signal':counts['NO_REVIEW_SIGNAL']-completed,'monitor':counts['MONITOR'],'alerts_created':0,'counts':dict(counts)}
    (out/'officer_review_queue_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
