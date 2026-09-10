"""Deterministic latest-as-of prediction batch. Does not write Alert rows."""
from __future__ import annotations
import argparse,csv,json,sys
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.ml.prediction_service import FrozenPredictionService

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--as-of',default='2026-06');ap.add_argument('--output',default='outputs/ml/final_prediction_v1/latest_predictions.csv');args=ap.parse_args()
    path=ROOT/'data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv'
    with path.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    by=defaultdict(list)
    for r in rows: by[r['canonical_project_id']].append(r)
    service=FrozenPredictionService(ROOT);out=[]
    for pid,history in sorted(by.items()):
        if not any(r['reporting_month']==args.as_of for r in history): continue
        for target in ('S1','S2'): out.append(service.predict_dict(history,args.as_of,target))
    dest=ROOT/args.output;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    summary={'as_of_month':args.as_of,'records':len(out),'by_target_status':{f'{t}:{s}':n for (t,s),n in Counter((r['target'],r['prediction_status']) for r in out).items()},'database_rows_created':0,'reason':'probabilities are withheld; explicit database load was not authorized by scientific gates'}
    (dest.with_suffix('.json')).write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
