"""Create deterministic blank S1/S2 human-adjudication worksheets."""
from __future__ import annotations
import csv,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SEED=26103
LABELS='CONFIRMED_FIRST_SCHEDULE_DETERIORATION|CONFIRMED_FURTHER_DETERIORATION|CORRECTION_NOT_EVENT|DATE_NORMALIZATION_ARTIFACT|IDENTITY_UNCERTAIN|SOURCE_INCONSISTENCY|INSUFFICIENT_EVIDENCE|OTHER'
def main():
    for target in ('s1','s2'):
        src=ROOT/'outputs/ml/final_prediction_v1'/f'{target}_event_ledger.csv'
        rows=list(csv.DictReader(src.open(encoding='utf-8'))); random.Random(SEED).shuffle(rows);rows=rows[:60]
        for r in rows:r.update({'allowed_labels':LABELS,'manual_label':'','manual_identity_confirmed':'','manual_date_change_confirmed':'','manual_approval_evidence':'','reviewer':'','review_notes':''})
        dest=ROOT/'validation/prediction_v1'/f'{target}_human_adjudication.csv';dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
if __name__=='__main__':main()
