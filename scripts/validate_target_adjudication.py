from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.ml.adjudication import read_csv,validate_review
def load(path,target):
    if path.suffix.lower()=='.json':
        rows=json.loads(path.read_text(encoding='utf-8'))
    elif path.suffix.lower()=='.jsonl':
        rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    else:rows=read_csv(path)
    return [r for r in rows if r.get('target_family')==target]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--s1',type=Path);ap.add_argument('--s2',type=Path);args=ap.parse_args();overall=True
    for target,given in [('S1',args.s1),('S2',args.s2)]:
        canonical=read_csv(ROOT/'validation'/target.lower()/f'{target.lower()}_human_validation_v1.csv');submitted=load(given,target) if given else canonical;result=validate_review(canonical,submitted);overall&=result['valid'];print(target,json.dumps(result,indent=2))
    raise SystemExit(0 if overall else 1)
if __name__=='__main__':main()
