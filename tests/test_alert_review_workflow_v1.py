from __future__ import annotations
import copy
from datetime import date,timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func,select
from sqlalchemy.orm import sessionmaker

from backend.database import Base,get_db,make_engine
from backend.main import create_app
from backend.models import Alert,AlertHistory,OfficerReview,Project,ReviewAction,ReviewNote
from backend.workflow_service import AlertWorkflowService,workflow_metrics
from src.workflow.alert_policy import evaluate_alert_candidate
from src.workflow.lifecycle import InvalidTransition,transition_alert,transition_review


def intelligence(pid='P1',origin='HISTORICAL_FLASH_REPORT',month='2026-06',decision='REVIEW_RECOMMENDED',watch='ELEVATED',trust='USABLE',reasons=None):
    reasons=reasons or (['HIGH_REQUIRED_FUTURE_PACE'] if decision=='REVIEW_RECOMMENDED' else ['SOURCE_GAP'])
    mode='REAL_HISTORICAL' if origin=='HISTORICAL_FLASH_REPORT' else 'SYNTHETIC_SANDBOX'
    return {'contract_version':'unified-project-intelligence-v1.0','mode':mode,'data_origin':origin,'identity':{'canonical_project_id':pid,'project_name':'Fixture project','sector':'ROAD','agency':'Agency','ministry':None,'location':None},'current_state':{'as_of_month':month,'physical_progress':50},'schedule_intelligence':{'prediction_status':'WITHHELD','probability':None,'risk_band':None},'cost_intelligence':{'prediction_status':'WITHHELD','probability':None,'risk_band':None},'implementation_watch':{'status':watch,'reason_codes':reasons,'signals':[],'policy_version':'implementation-watch-v1.0'},'data_trust':{'data_status':trust},'peer_benchmark':{'benchmark_status':'BENCHMARK_AVAILABLE','peer_count':30,'peer_group':{},'policy_version':'peer-benchmark-v1.0','metrics':[]},'officer_decision':{'review_state':decision,'reason_codes':reasons,'decision_policy_version':'officer-decision-v1'},'evidence_summary':[{'data_origin':origin,'source_id':'FIXTURE'}]}


@pytest.fixture
def Session(tmp_path):
    engine=make_engine(f"sqlite:///{(tmp_path/'workflow.db').as_posix()}");Base.metadata.create_all(engine);maker=sessionmaker(engine,expire_on_commit=False)
    with maker.begin() as db:db.add(Project(canonical_project_id='P1',project_code=None,canonical_name='Real fixture',agency='Agency',ministry=None,sector='ROAD',state=None,identity_method='EXACT',identity_status='RESOLVED_EXACT',data_origin='HISTORICAL_FLASH_REPORT'))
    yield maker;engine.dispose()


def test_alert_policy_requires_officer_decision_not_raw_inputs():
    good=evaluate_alert_candidate(intelligence());assert good.eligible and good.alert_type=='IMPLEMENTATION_PRESSURE' and good.severity=='HIGH'
    raw=intelligence(decision='PREDICTION_WITHHELD');raw['schedule_intelligence']={'prediction_status':'AVAILABLE','probability':.99,'risk_band':'HIGH'};raw['peer_benchmark']['metrics']=[{'percentile':99}]
    assert not evaluate_alert_candidate(raw).eligible
    assert not evaluate_alert_candidate(intelligence(decision='PREDICTION_WITHHELD',watch='CLEAR')).eligible


def test_data_verification_is_not_project_deterioration():
    candidate=evaluate_alert_candidate(intelligence(decision='DATA_VERIFICATION_REQUIRED',watch='DATA_INSUFFICIENT',trust='NOT_USABLE'))
    assert candidate.eligible and candidate.alert_type=='REPORTING_GAP' and candidate.reason_family=='DATA_VERIFICATION'
    assert 'deterior' not in candidate.explanation.lower()


def test_alert_episode_idempotency_opening_snapshot_and_review(Session):
    with Session.begin() as db:
        service=AlertWorkflowService(db);first=service.evaluate(intelligence());second=service.evaluate(intelligence())
        assert first['created'] is True and second['created'] is False and second['changed'] is False
        alert=db.get(Alert,first['alert_ids'][0]);assert alert.initial_evidence_snapshot==alert.latest_evidence_snapshot and alert.status=='NEW'
        assert db.scalar(select(func.count()).select_from(Alert))==1 and db.scalar(select(func.count()).select_from(AlertHistory))==1
        review=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==alert.alert_id));assert review.review_status=='NOT_STARTED' and review.priority=='HIGH'


def test_persistence_evidence_diff_and_escalation(Session):
    with Session.begin() as db:
        service=AlertWorkflowService(db);first=service.evaluate(intelligence(watch='WATCH'));aid=first['alert_ids'][0]
        service.evaluate(intelligence(month='2026-07',watch='WATCH'));service.evaluate(intelligence(month='2026-08',watch='WATCH'))
        assert db.get(Alert,aid).status=='PERSISTENT' and db.get(Alert,aid).consecutive_valid_cycles==3
    with Session.begin() as db:
        service=AlertWorkflowService(db);service.evaluate(intelligence(month='2026-09',watch='ELEVATED',reasons=['HIGH_REQUIRED_FUTURE_PACE','PHYSICAL_PROGRESS_STAGNANT']))
        alert=db.get(Alert,aid);assert alert.status=='ESCALATED' and alert.severity=='HIGH'
        assert set(alert.current_reason_codes)-set(alert.trigger_reason_codes)=={'PHYSICAL_PROGRESS_STAGNANT'}


def test_new_episode_can_escalate_on_next_valid_cycle(Session):
    with Session.begin() as db:
        service=AlertWorkflowService(db);aid=service.evaluate(intelligence(watch='WATCH'))['alert_ids'][0]
        service.evaluate(intelligence(month='2026-07',watch='ELEVATED'))
        assert db.get(Alert,aid).status=='ESCALATED'


def test_lower_severity_is_audited_but_does_not_imply_resolution(Session):
    with Session.begin() as db:
        service=AlertWorkflowService(db);aid=service.evaluate(intelligence(watch='ELEVATED'))['alert_ids'][0]
        service.evaluate(intelligence(month='2026-07',watch='WATCH'))
        alert=db.get(Alert,aid);assert alert.severity=='ATTENTION' and alert.status=='NEW'
        assert db.scalar(select(func.count()).select_from(AlertHistory).where(AlertHistory.event_type=='SEVERITY_CHANGED'))==1


def test_valid_clear_resolves_missing_evidence_does_not(Session):
    with Session.begin() as db:aid=AlertWorkflowService(db).evaluate(intelligence())['alert_ids'][0]
    missing=intelligence(month='2026-07',decision='DATA_VERIFICATION_REQUIRED',watch='DATA_INSUFFICIENT',trust='NOT_USABLE')
    with Session.begin() as db:
        AlertWorkflowService(db).evaluate(missing);assert db.get(Alert,aid).status=='NEW'
    clear=intelligence(month='2026-08',decision='PREDICTION_WITHHELD',watch='CLEAR',trust='USABLE',reasons=[])
    with Session.begin() as db:
        result=AlertWorkflowService(db).evaluate(clear);assert aid in result['alert_ids'] and db.get(Alert,aid).status=='RESOLVED'


def test_resolved_episode_reopens_only_on_newer_equivalent_evidence(Session):
    with Session.begin() as db:
        service=AlertWorkflowService(db);aid=service.evaluate(intelligence())['alert_ids'][0];service.evaluate(intelligence(month='2026-07',decision='PREDICTION_WITHHELD',watch='CLEAR',trust='USABLE',reasons=[]))
    with Session.begin() as db:
        result=AlertWorkflowService(db).evaluate(intelligence(month='2026-07'));assert result['changed'] is False and db.get(Alert,aid).status=='RESOLVED'
    with Session.begin() as db:
        result=AlertWorkflowService(db).evaluate(intelligence(month='2026-08'));assert result['changed'] and db.get(Alert,aid).status=='REOPENED'


def test_automatic_reopen_resets_closed_review_and_can_become_persistent(Session):
    with Session.begin() as db:
        service=AlertWorkflowService(db);aid=service.evaluate(intelligence(watch='WATCH'))['alert_ids'][0];review=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==aid))
        service.update_review(review.review_id,'CLOSED_NO_ACTION',actor_type='OFFICER',actor_id='o1',outcome='NO_ACTION_REQUIRED')
        service.transition(aid,'DISMISSED',actor_type='OFFICER',actor_id='o1',reason='NOT_ACTIONABLE')
    with Session.begin() as db:
        service=AlertWorkflowService(db);service.evaluate(intelligence(month='2026-07',watch='WATCH'))
        review=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==aid));assert review.review_status=='NOT_STARTED' and review.outcome is None
        service.evaluate(intelligence(month='2026-08',watch='WATCH'));service.evaluate(intelligence(month='2026-09',watch='WATCH'))
        assert db.get(Alert,aid).status=='PERSISTENT'


def test_alert_and_review_transition_matrices():
    chain=['NEW','ACKNOWLEDGED','IN_REVIEW','MONITORING','RESOLVED','REOPENED']
    for old,new in zip(chain,chain[1:]):assert transition_alert(old,new)==new
    assert transition_alert('MONITORING','ESCALATED')=='ESCALATED'
    assert transition_review('NOT_STARTED','IN_PROGRESS')=='IN_PROGRESS'
    assert transition_review('IN_PROGRESS','MONITORING')=='MONITORING'
    with pytest.raises(InvalidTransition):transition_alert('RESOLVED','ACKNOWLEDGED')
    with pytest.raises(InvalidTransition):transition_review('COMPLETE','IN_PROGRESS')


def test_assignment_notes_actions_outcome_next_review_and_audit(Session):
    with Session.begin() as db:
        service=AlertWorkflowService(db);aid=service.evaluate(intelligence())['alert_ids'][0];review=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==aid))
        service.assign(review.review_id,'officer-17','OFFICER','lead-1');service.update_review(review.review_id,'IN_PROGRESS',actor_type='OFFICER',actor_id='officer-17');service.add_note(review.review_id,'Verified the latest reported progress.','VERIFICATION','OFFICER','officer-17');service.add_action(review.review_id,'MONITOR_NEXT_CYCLE','Review next reporting month.','OFFICER','officer-17');service.update_review(review.review_id,'MONITORING',actor_type='OFFICER',actor_id='officer-17',outcome='MONITOR_CONTINUED',next_review_date=date.today()+timedelta(days=7))
        assert review.assigned_to=='officer-17' and review.next_review_date>date.today()
        assert db.scalar(select(func.count()).select_from(ReviewNote))==1 and db.scalar(select(func.count()).select_from(ReviewAction))==1
        assert db.scalar(select(func.count()).select_from(AlertHistory))>=6
        sequences=list(db.scalars(select(AlertHistory.sequence_number).where(AlertHistory.alert_id==aid).order_by(AlertHistory.sequence_number)))
        assert sequences==list(range(1,len(sequences)+1))
        with pytest.raises(ValueError):service.add_action(review.review_id,'APPROVE_EXTENSION',None,'OFFICER','officer-17')


def test_dismissal_requires_governed_reason_and_actor_preserved(Session):
    with Session.begin() as db:
        service=AlertWorkflowService(db);aid=service.evaluate(intelligence())['alert_ids'][0]
        with pytest.raises(ValueError):service.transition(aid,'DISMISSED',actor_type='OFFICER',actor_id='o1',reason='because')
        service.transition(aid,'DISMISSED',actor_type='OFFICER',actor_id='o1',reason='NOT_ACTIONABLE')
        event=db.scalar(select(AlertHistory).where(AlertHistory.event_type=='ALERT_DISMISSED'));assert event.actor_id=='o1' and event.reason=='NOT_ACTIONABLE'


def test_real_synthetic_persistence_and_metrics_are_isolated(Session):
    with Session.begin() as db:
        service=AlertWorkflowService(db);service.evaluate(intelligence());service.evaluate(intelligence('SYN-1','SYNTHETIC_CUF_PROTOTYPE'))
        assert workflow_metrics(db,'HISTORICAL_FLASH_REPORT')['alerts_opened']==1
        assert workflow_metrics(db,'SYNTHETIC_CUF_PROTOTYPE')['alerts_opened']==1
        assert db.get(Project,'SYN-1').data_origin=='SYNTHETIC_CUF_PROTOTYPE'


@pytest.fixture
def api(Session):
    with Session.begin() as db:
        result=AlertWorkflowService(db).evaluate(intelligence());aid=result['alert_ids'][0];rid=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==aid)).review_id
        AlertWorkflowService(db).evaluate(intelligence('SYN-1','SYNTHETIC_CUF_PROTOTYPE'))
    app=create_app(None)
    def override():
        with Session() as db:yield db
    app.dependency_overrides[get_db]=override
    with TestClient(app) as client:yield client,aid,rid


def test_alert_review_api_lifecycle_history_filters_and_validation(api):
    client,aid,rid=api
    assert client.get('/api/v1/alerts').json()['total']==1
    assert client.get('/api/v1/alerts?mode=SYNTHETIC_SANDBOX').json()['total']==1
    assert client.get(f'/api/v1/alerts/{aid}?mode=SYNTHETIC_SANDBOX').status_code==404
    body={'actor_type':'OFFICER','actor_id':'o1','reason':'Review accepted'}
    assert client.post(f'/api/v1/alerts/{aid}/acknowledge',json=body).json()['status']=='ACKNOWLEDGED'
    assert client.post(f'/api/v1/alerts/{aid}/start-review',json=body).json()['status']=='IN_REVIEW'
    assert client.post(f'/api/v1/alerts/{aid}/monitor',json=body).json()['status']=='MONITORING'
    assert client.post(f'/api/v1/reviews/{rid}/notes',json={'text':'Evidence checked','note_type':'OBSERVATION','actor_id':'o1'}).status_code==200
    assert client.post(f'/api/v1/reviews/{rid}/actions',json={'action_type':'REVIEW_PROGRESS','detail':'Review source values','actor_id':'o1'}).status_code==200
    assert client.patch(f'/api/v1/reviews/{rid}',json={'review_status':'MONITORING','outcome':'MONITOR_CONTINUED','next_review_date':(date.today()+timedelta(days=5)).isoformat(),'actor_id':'o1'}).status_code==200
    assert client.get('/api/v1/reviews?status=MONITORING').json()['total']==1
    assert len(client.get(f'/api/v1/alerts/{aid}/history').json()['events'])>=6
    assert client.get('/api/v1/workflow/metrics').json()['metric_type']=='WORKFLOW_OPERATIONAL_NOT_ML'
    assert client.post(f'/api/v1/reviews/{rid}/notes',json={'text':'','note_type':'OBSERVATION'}).status_code==422
    assert client.get('/api/v1/alerts?status=UNSUPPORTED').status_code==422
    synthetic_review=client.get('/api/v1/reviews?mode=SYNTHETIC_SANDBOX').json()['items'][0]
    synthetic_alert=synthetic_review['alert_id']
    assert client.get(f'/api/v1/reviews/{synthetic_review["review_id"]}').status_code==404
    assert client.get(f'/api/v1/reviews/{synthetic_review["review_id"]}?mode=SYNTHETIC_SANDBOX').status_code==200
    assert client.get(f'/api/v1/alerts/{synthetic_alert}/history').status_code==404
    assert client.get(f'/api/v1/alerts/{synthetic_alert}/history?mode=SYNTHETIC_SANDBOX').status_code==200
    synthetic_summary=client.get('/api/v1/dashboard/intelligence-summary?mode=SYNTHETIC_SANDBOX').json()
    assert synthetic_summary['recent_alerts']==1 and synthetic_summary['projects_reviewed']==1 and synthetic_summary['total_projects']==1000


def test_api_invalid_transition_and_dismissal_fail_closed(api):
    client,aid,_=api
    body={'actor_type':'OFFICER','actor_id':'o1','reason':'NOT_ACTIONABLE'}
    assert client.post(f'/api/v1/alerts/{aid}/dismiss',json=body).status_code==200
    assert client.post(f'/api/v1/alerts/{aid}/acknowledge',json=body).status_code==409
    assert client.post(f'/api/v1/alerts/{aid}/reopen',json={'actor_type':'OFFICER','actor_id':'o1','reason':'Recheck current evidence'}).status_code==409
