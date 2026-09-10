from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.ml.adjudication import HUMAN_FIELDS,build_master,choose_sample,enrich_sample_excerpts,negative_controls,render_html,write_csv
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw-root',type=Path,default=ROOT.parent/'PRAHARI'/'data/raw');args=ap.parse_args()
    master,audit=build_master(ROOT,args.raw_root);out=ROOT/'validation/target_adjudication_v1';write_csv(out/'master_machine_event_ledger.csv',master);write_csv(out/'source_availability_audit.csv',audit)
    samples=[]
    for t in ('S1','S2'):
        sample=choose_sample(master,t)[:54]+negative_controls(ROOT,args.raw_root,t,6)
        for i,r in enumerate(sample,1):r['review_row_id']=f'{t}-VAL-{i:04d}'
        sample=enrich_sample_excerpts(ROOT,args.raw_root,sample);samples+=sample;dest=ROOT/'validation'/t.lower()/f'{t.lower()}_human_validation_v1.csv';write_csv(dest,sample)
        with dest.with_suffix('.jsonl').open('w',encoding='utf-8') as f:
            for r in sample:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    suspicious=[r for r in master if r['target_family']=='S1' and r['correction_like_flag'].lower()=='true'];sampled={r['canonical_project_id']+'|'+r['anchor_month'] for r in samples}
    follow=[]
    for i,r in enumerate((r for r in suspicious if r['canonical_project_id']+'|'+r['anchor_month'] not in sampled),1):
        x=r.copy();x['review_row_id']=f'S1-FOLLOWUP-{i:04d}';x['review_stratum']='CORRECTION_LIKE_PRIORITY';[x.__setitem__(h,'') for h in HUMAN_FIELDS];follow.append(x)
    write_csv(ROOT/'validation/s1/s1_priority_followup_cases.csv',follow);render_html(samples,out/'prahari_target_adjudication_v1.html')
    print(json.dumps({'S1_sample':60,'S2_sample':60,'master_events':len(master),'source_reports':len(audit),'followup':len(follow)},indent=2))
if __name__=='__main__':main()
