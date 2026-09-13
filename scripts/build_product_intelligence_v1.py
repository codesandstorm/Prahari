#!/usr/bin/env python3
"""Reproducibly build sandbox evidence and sample intelligence payloads."""
from __future__ import annotations
import hashlib,json,tempfile,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from sqlalchemy.orm import sessionmaker

from backend.database import Base,make_engine
from backend.loader import load_canonical_dataset
from backend.product_intelligence import _REAL_CACHE,_real_bundle,real_project_intelligence,synthetic_project_intelligence
from backend.repository import ProjectRepository
from src.sandbox.generator import OUTPUT,generate_sandbox

CANONICAL=ROOT/'data'/'processed'/'longitudinal_2023_07_2026_06_mixed'
OUT=ROOT/'outputs'/'product_intelligence_v1'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,payload):
    path=OUT/name;path.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8');return path


def main():
    OUT.mkdir(parents=True,exist_ok=True);canonical_before={x.name:sha(x) for x in (CANONICAL/'project_master.csv',CANONICAL/'report_month.csv',CANONICAL/'project_month.csv')}
    metadata=generate_sandbox();samples={
        'synthetic_clear.json':synthetic_project_intelligence('SYN-CUF-0001').model_dump(mode='json'),
        'synthetic_watch.json':synthetic_project_intelligence('SYN-CUF-0005').model_dump(mode='json'),
        'synthetic_elevated.json':synthetic_project_intelligence('SYN-CUF-0022').model_dump(mode='json'),
        'synthetic_data_insufficient.json':synthetic_project_intelligence('SYN-CUF-0023').model_dump(mode='json'),
    }
    with tempfile.TemporaryDirectory(prefix='prahari-intelligence-') as folder:
        engine=make_engine(f"sqlite:///{(Path(folder)/'sample.db').as_posix()}");Base.metadata.create_all(engine);Session=sessionmaker(engine,expire_on_commit=False)
        with Session() as db:load_canonical_dataset(db,CANONICAL,ROOT/'data'/'metadata'/'source_manifest.csv')
        with Session() as db:
            repo=ProjectRepository(db);_REAL_CACHE.update(key=None,bundle=None);bundle=_real_bundle(db,repo);assessments=bundle[-1]
            usable=next((pid for pid,(result,_,_,_,_,watch) in assessments.items() if result.data_usable and watch['status']!='DATA_INSUFFICIENT'),None)
            verification=next((pid for pid,(result,*_) in assessments.items() if not result.data_usable),None)
            if usable:samples['real_current.json']=real_project_intelligence(db,usable).model_dump(mode='json')
            if verification:samples['real_data_verification_required.json']=real_project_intelligence(db,verification).model_dump(mode='json')
        _REAL_CACHE.update(key=None,bundle=None);engine.dispose()
    paths=[write(name,payload) for name,payload in samples.items()]
    canonical_after={x.name:sha(x) for x in (CANONICAL/'project_master.csv',CANONICAL/'report_month.csv',CANONICAL/'project_month.csv')}
    if canonical_before!=canonical_after:raise RuntimeError('canonical real artifacts changed')
    evidence={'status':'PASS','synthetic_metadata':metadata,'canonical_real_hashes_unchanged':canonical_after,'samples':{p.name:sha(p) for p in paths},'synthetic_ml_experiment':'NOT_IMPLEMENTED','synthetic_ml_disclaimer':'No synthetic ML metrics or production artifacts were created.'}
    write('build_evidence.json',evidence);print(json.dumps(evidence,indent=2))

if __name__=='__main__':main()
