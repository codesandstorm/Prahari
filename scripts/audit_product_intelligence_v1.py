#!/usr/bin/env python3
"""Fail-closed acceptance audit for Product Intelligence V1 artifacts."""
from __future__ import annotations
import csv,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];SANDBOX=ROOT/'data'/'synthetic'/'cuf_sandbox_v1';OUT=ROOT/'outputs'/'product_intelligence_v1'

def fail(message):print(f'FAIL {message}');raise SystemExit(1)
def rows(name):
    with (SANDBOX/name).open(encoding='utf-8',newline='') as handle:return list(csv.DictReader(handle))

def main():
    metadata=json.loads((SANDBOX/'generation_metadata.json').read_text());projects=rows('project_master.csv');months=rows('project_month.csv')
    if len(projects)!=1000 or len(months)!=24000:fail('sandbox size contract')
    if any(x['data_origin']!='SYNTHETIC_CUF_PROTOTYPE' for x in projects+months):fail('synthetic origin isolation')
    if len({(x['canonical_project_id'],x['reporting_month']) for x in months})!=24000:fail('duplicate synthetic project-month key')
    real=(ROOT/'data'/'processed'/'longitudinal_2023_07_2026_06_mixed'/'project_master.csv').read_text(encoding='utf-8')
    if 'SYN-CUF-' in real:fail('synthetic contamination in canonical real master')
    required={'real_current.json','real_data_verification_required.json','synthetic_clear.json','synthetic_watch.json','synthetic_elevated.json','synthetic_data_insufficient.json'}
    if not required<={p.name for p in OUT.glob('*.json')}:fail('sample payload set')
    for path in OUT.glob('*.json'):
        payload=json.loads(path.read_text())
        if path.name.startswith('synthetic_') and payload.get('data_origin')!='SYNTHETIC_CUF_PROTOTYPE':fail(f'synthetic sample origin {path.name}')
    print(json.dumps({'status':'PASS','project_count':len(projects),'project_month_count':len(months),'dataset_fingerprint_sha256':metadata['dataset_fingerprint_sha256'],'synthetic_real_separation':'PASS','production_probabilities_created':False},indent=2))

if __name__=='__main__':main()
