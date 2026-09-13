#!/usr/bin/env python3
"""Generate deterministic summaries of governed alert/review workflow stories."""
from __future__ import annotations
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from backend.database import Base,make_engine
from backend.models import Alert,AlertHistory,OfficerReview,Project
from backend.workflow_service import AlertWorkflowService

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'/'alert_review_workflow_v1'
def intel(pid,origin,month,decision,watch,trust,reasons):
    return {'contract_version':'unified-project-intelligence-v1.0','mode':'REAL_HISTORICAL' if origin=='HISTORICAL_FLASH_REPORT' else 'SYNTHETIC_SANDBOX','data_origin':origin,'identity':{'canonical_project_id':pid,'project_name':'Workflow demonstration fixture','agency':'DEMO_AGENCY'},'current_state':{'as_of_month':month,'physical_progress':50},'schedule_intelligence':{'prediction_status':'WITHHELD','probability':None,'risk_band':None},'cost_intelligence':{'prediction_status':'WITHHELD','probability':None,'risk_band':None},'implementation_watch':{'status':watch,'reason_codes':reasons,'signals':[],'policy_version':'implementation-watch-v1.0'},'data_trust':{'data_status':trust},'peer_benchmark':{'benchmark_status':'BENCHMARK_AVAILABLE','peer_count':30,'peer_group':{},'policy_version':'peer-benchmark-v1.0'},'officer_decision':{'review_state':decision,'reason_codes':reasons,'decision_policy_version':'officer-decision-v1'},'evidence_summary':[{'data_origin':origin,'source_id':'DEMO_FIXTURE'}]}
def timeline(db,aid):return [x.event_type for x in db.scalars(select(AlertHistory).where(AlertHistory.alert_id==aid).order_by(AlertHistory.sequence_number))]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='prahari-workflow-demo-') as folder:
        engine=make_engine(f"sqlite:///{(Path(folder)/'demo.db').as_posix()}");Base.metadata.create_all(engine);Session=sessionmaker(engine,expire_on_commit=False)
        with Session.begin() as db:db.add(Project(canonical_project_id='DEMO-REAL-001',project_code=None,canonical_name='Real-mode workflow fixture',agency='DEMO_AGENCY',ministry=None,sector='ROAD',state=None,identity_method='DEMO_FIXTURE',identity_status='RESOLVED_EXACT',data_origin='HISTORICAL_FLASH_REPORT'))
        with Session.begin() as db:
            s=AlertWorkflowService(db);aid=s.evaluate(intel('DEMO-REAL-001','HISTORICAL_FLASH_REPORT','2026-06','REVIEW_RECOMMENDED','WATCH','USABLE',['PHYSICAL_PROGRESS_STAGNANT']))['alert_ids'][0];states=['NEW'];s.transition(aid,'ACKNOWLEDGED',actor_type='OFFICER',actor_id='demo-officer',reason='Demo acknowledgement');states.append('ACKNOWLEDGED');s.transition(aid,'IN_REVIEW',actor_type='OFFICER',actor_id='demo-officer',reason='Demo review');states.append('IN_REVIEW');s.transition(aid,'MONITORING',actor_type='OFFICER',actor_id='demo-officer',reason='Demo monitoring');states.append('MONITORING');s.evaluate(intel('DEMO-REAL-001','HISTORICAL_FLASH_REPORT','2026-07','PREDICTION_WITHHELD','CLEAR','USABLE',[]));states.append('RESOLVED');real={'alert_id':aid,'states':states,'timeline':timeline(db,aid)}
            watch=s.evaluate(intel('DEMO-SYN-WATCH','SYNTHETIC_CUF_PROTOTYPE','2026-06','REVIEW_RECOMMENDED','WATCH','USABLE',['PHYSICAL_PROGRESS_STAGNANT']))
            elevated=s.evaluate(intel('DEMO-SYN-ELEVATED','SYNTHETIC_CUF_PROTOTYPE','2026-06','REVIEW_RECOMMENDED','ELEVATED','USABLE',['HIGH_REQUIRED_FUTURE_PACE']))
            insufficient=s.evaluate(intel('DEMO-SYN-DATA','SYNTHETIC_CUF_PROTOTYPE','2026-06','DATA_VERIFICATION_REQUIRED','DATA_INSUFFICIENT','NOT_USABLE',['SOURCE_GAP']))
            recovery_id=s.evaluate(intel('DEMO-SYN-RECOVERY','SYNTHETIC_CUF_PROTOTYPE','2026-05','REVIEW_RECOMMENDED','WATCH','USABLE',['PHYSICAL_PROGRESS_STAGNANT']))['alert_ids'][0];s.evaluate(intel('DEMO-SYN-RECOVERY','SYNTHETIC_CUF_PROTOTYPE','2026-06','PREDICTION_WITHHELD','CLEAR','USABLE',[]));recovery_state=db.get(Alert,recovery_id).status;s.evaluate(intel('DEMO-SYN-RECOVERY','SYNTHETIC_CUF_PROTOTYPE','2026-07','REVIEW_RECOMMENDED','ELEVATED','USABLE',['HIGH_REQUIRED_FUTURE_PACE']));reopen_state=db.get(Alert,recovery_id).status
            result={'evaluation_context':'BACKEND_WORKFLOW_DEMO_FIXTURE','official_project_evidence':False,'predictions_used':False,'real_mode_workflow':real,'synthetic_watch':watch,'synthetic_elevated':elevated,'synthetic_data_insufficient':insufficient,'recovery_state':recovery_state,'reopen_state':reopen_state,'schedule_prediction_status':'WITHHELD','cost_prediction_status':'WITHHELD'}
        engine.dispose()
    path=OUT/'demo_workflows.json';path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
