"""FastAPI routes for governed Alert and Officer Review Workflow V1."""
from __future__ import annotations
import math
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Alert,AlertHistory,OfficerReview
from .product_intelligence import real_project_intelligence,synthetic_project_intelligence
from .schemas import ActorRequest,AssignmentRequest,DismissRequest,ReviewActionRequest,ReviewNoteRequest,ReviewUpdateRequest
from .workflow_service import ACTIVE_ALERT_STATES,AlertWorkflowService,alert_dict,event_dict,review_dict,workflow_metrics

router=APIRouter()
ORIGIN={'REAL_HISTORICAL':'HISTORICAL_FLASH_REPORT','SYNTHETIC_SANDBOX':'SYNTHETIC_CUF_PROTOTYPE'}

def _mode(mode):return ORIGIN[mode]
def _error(exc,status=409):raise HTTPException(status,detail={'code':'WORKFLOW_CONTRACT_ERROR','message':str(exc)})

@router.post('/projects/{project_id}/alerts/evaluate')
def evaluate_real_alert(project_id:str,db:Session=Depends(get_db)):
    try:result=AlertWorkflowService(db).evaluate(real_project_intelligence(db,project_id));db.commit();return result
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'PROJECT_NOT_FOUND','message':'Project not found'})
    except ValueError as exc:db.rollback();_error(exc)

@router.post('/sandbox/projects/{project_id}/alerts/evaluate')
def evaluate_synthetic_alert(project_id:str,db:Session=Depends(get_db)):
    try:result=AlertWorkflowService(db).evaluate(synthetic_project_intelligence(project_id,db));db.commit();return result
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'SYNTHETIC_PROJECT_NOT_FOUND','message':'Synthetic sandbox project not found'})
    except ValueError as exc:db.rollback();_error(exc)

@router.get('/alerts')
def list_alerts(mode:str=Query('REAL_HISTORICAL',pattern='^(REAL_HISTORICAL|SYNTHETIC_SANDBOX)$'),status:str|None=Query(None,pattern='^(NEW|ACKNOWLEDGED|IN_REVIEW|MONITORING|PERSISTENT|ESCALATED|RESOLVED|DISMISSED|REOPENED)$'),severity:str|None=Query(None,pattern='^(INFO|ATTENTION|HIGH)$'),alert_type:str|None=Query(None,pattern='^(IMPLEMENTATION_PRESSURE|DATA_VERIFICATION|REPORTING_GAP|SOURCE_QUALITY|MODEL_SCHEDULE_WARNING|MODEL_COST_WARNING)$'),page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),db:Session=Depends(get_db)):
    query=select(Alert).where(Alert.data_origin==_mode(mode)).order_by(Alert.last_updated_at.desc(),Alert.alert_id)
    if status:query=query.where(Alert.status==status)
    if severity:query=query.where(Alert.severity==severity)
    if alert_type:query=query.where(Alert.alert_type==alert_type)
    items=list(db.scalars(query));total=len(items);start=(page-1)*page_size
    return {'mode':mode,'data_origin':_mode(mode),'items':[alert_dict(x) for x in items[start:start+page_size]],'page':page,'page_size':page_size,'total':total,'pages':math.ceil(total/page_size) if total else 0}

@router.get('/alerts/{alert_id}')
def get_alert(alert_id:str,mode:str=Query('REAL_HISTORICAL',pattern='^(REAL_HISTORICAL|SYNTHETIC_SANDBOX)$'),db:Session=Depends(get_db)):
    alert=db.get(Alert,alert_id)
    if alert is None or alert.data_origin!=_mode(mode):raise HTTPException(404,detail={'code':'ALERT_NOT_FOUND','message':'Alert not found in requested mode'})
    review=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==alert_id))
    return alert_dict(alert)|{'review':review_dict(db,review) if review else None}

def _transition(db,alert_id,state,payload):
    try:alert=AlertWorkflowService(db).transition(alert_id,state,actor_type=payload.actor_type,actor_id=payload.actor_id,reason=payload.reason);db.commit();return alert_dict(alert)
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'ALERT_NOT_FOUND','message':'Alert not found'})
    except ValueError as exc:db.rollback();_error(exc)

@router.post('/alerts/{alert_id}/acknowledge')
def acknowledge(alert_id:str,payload:ActorRequest,db:Session=Depends(get_db)):return _transition(db,alert_id,'ACKNOWLEDGED',payload)
@router.post('/alerts/{alert_id}/start-review')
def start_review(alert_id:str,payload:ActorRequest,db:Session=Depends(get_db)):
    try:
        service=AlertWorkflowService(db);alert=service.transition(alert_id,'IN_REVIEW',actor_type=payload.actor_type,actor_id=payload.actor_id,reason=payload.reason);review=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==alert_id))
        if review and review.review_status in {'NOT_STARTED','MONITORING'}:service.update_review(review.review_id,'IN_PROGRESS',actor_type=payload.actor_type,actor_id=payload.actor_id)
        db.commit();return alert_dict(alert)
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'ALERT_NOT_FOUND','message':'Alert not found'})
    except ValueError as exc:db.rollback();_error(exc)
@router.post('/alerts/{alert_id}/monitor')
def monitor(alert_id:str,payload:ActorRequest,db:Session=Depends(get_db)):
    try:
        service=AlertWorkflowService(db);alert=service.transition(alert_id,'MONITORING',actor_type=payload.actor_type,actor_id=payload.actor_id,reason=payload.reason);review=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==alert_id))
        if review and review.review_status in {'IN_PROGRESS','ACTION_REQUIRED'}:service.update_review(review.review_id,'MONITORING',actor_type=payload.actor_type,actor_id=payload.actor_id,outcome='MONITOR_CONTINUED')
        db.commit();return alert_dict(alert)
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'ALERT_NOT_FOUND','message':'Alert not found'})
    except ValueError as exc:db.rollback();_error(exc)
@router.post('/alerts/{alert_id}/resolve')
def resolve(alert_id:str,payload:ActorRequest,db:Session=Depends(get_db)):
    try:
        service=AlertWorkflowService(db);review=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==alert_id))
        if review is None or review.review_status not in {'IN_PROGRESS','MONITORING','ACTION_REQUIRED'}:raise ValueError('resolution requires an active officer review')
        alert=service.transition(alert_id,'RESOLVED',actor_type=payload.actor_type,actor_id=payload.actor_id,reason=payload.reason);service.update_review(review.review_id,'COMPLETE',actor_type=payload.actor_type,actor_id=payload.actor_id,outcome='ISSUE_RESOLVED');db.commit();return alert_dict(alert)
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'ALERT_NOT_FOUND','message':'Alert not found'})
    except ValueError as exc:db.rollback();_error(exc)
@router.post('/alerts/{alert_id}/dismiss')
def dismiss(alert_id:str,payload:DismissRequest,db:Session=Depends(get_db)):
    try:
        service=AlertWorkflowService(db);alert=service.transition(alert_id,'DISMISSED',actor_type=payload.actor_type,actor_id=payload.actor_id,reason=payload.reason);review=db.scalar(select(OfficerReview).where(OfficerReview.alert_id==alert_id))
        if review and review.review_status in {'NOT_STARTED','IN_PROGRESS','MONITORING'}:service.update_review(review.review_id,'CLOSED_NO_ACTION',actor_type=payload.actor_type,actor_id=payload.actor_id,outcome='NO_ACTION_REQUIRED');db.commit()
        else:db.commit()
        return alert_dict(alert)
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'ALERT_NOT_FOUND','message':'Alert not found'})
    except ValueError as exc:db.rollback();_error(exc)
@router.post('/alerts/{alert_id}/reopen')
def reopen(alert_id:str,payload:ActorRequest,db:Session=Depends(get_db)):
    try:
        service=AlertWorkflowService(db);alert=service.get_alert(alert_id)
    except LookupError:
        db.rollback();raise HTTPException(404,detail={'code':'ALERT_NOT_FOUND','message':'Alert not found'})
    try:
        intelligence=synthetic_project_intelligence(alert.canonical_project_id,db) if alert.data_origin=='SYNTHETIC_CUF_PROTOTYPE' else real_project_intelligence(db,alert.canonical_project_id)
        result=service.evaluate(intelligence,reopen_actor_type=payload.actor_type,reopen_actor_id=payload.actor_id,reopen_reason=payload.reason)
        reopened=service.get_alert(alert_id)
        if reopened.status!='REOPENED':raise ValueError(result['explanation'])
        db.commit();return alert_dict(reopened)
    except LookupError as exc:db.rollback();_error(ValueError(f'newer governed project evidence is unavailable: {exc}'))
    except ValueError as exc:db.rollback();_error(exc)

@router.get('/alerts/{alert_id}/history')
def alert_history(alert_id:str,mode:str=Query('REAL_HISTORICAL',pattern='^(REAL_HISTORICAL|SYNTHETIC_SANDBOX)$'),db:Session=Depends(get_db)):
    alert=db.get(Alert,alert_id)
    if alert is None or alert.data_origin!=_mode(mode):raise HTTPException(404,detail={'code':'ALERT_NOT_FOUND','message':'Alert not found in requested mode'})
    events=list(db.scalars(select(AlertHistory).where(AlertHistory.alert_id==alert_id).order_by(AlertHistory.sequence_number)))
    return {'alert_id':alert_id,'events':[event_dict(x) for x in events],'append_only':True}

@router.get('/reviews')
def reviews(mode:str=Query('REAL_HISTORICAL',pattern='^(REAL_HISTORICAL|SYNTHETIC_SANDBOX)$'),status:str|None=Query(None,pattern='^(NOT_STARTED|IN_PROGRESS|MONITORING|ACTION_REQUIRED|COMPLETE|CLOSED_NO_ACTION)$'),priority:str|None=Query(None,pattern='^(HIGH|NORMAL|LOW)$'),decision:str|None=Query(None,pattern='^(REVIEW_RECOMMENDED|DATA_VERIFICATION_REQUIRED|MONITOR|NO_REVIEW_SIGNAL|PREDICTION_WITHHELD)$'),watch_state:str|None=Query(None,pattern='^(CLEAR|WATCH|ELEVATED|DATA_INSUFFICIENT|NOT_APPLICABLE)$'),data_trust_state:str|None=Query(None,pattern='^(USABLE|NOT_USABLE|UNKNOWN|PASS|WARN|FAIL)$'),assigned_to:str|None=Query(None,max_length=80,pattern=r'^[A-Za-z0-9_.:@-]+$'),alert_type:str|None=Query(None,pattern='^(IMPLEMENTATION_PRESSURE|DATA_VERIFICATION|REPORTING_GAP|SOURCE_QUALITY|MODEL_SCHEDULE_WARNING|MODEL_COST_WARNING)$'),sort:str=Query('priority',pattern='^(priority|oldest_unacknowledged|persistence|latest_update|decision)$'),page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),db:Session=Depends(get_db)):
    query=select(OfficerReview,Alert).join(Alert,Alert.alert_id==OfficerReview.alert_id).where(OfficerReview.data_origin==_mode(mode))
    if status:query=query.where(OfficerReview.review_status==status)
    if priority:query=query.where(OfficerReview.priority==priority)
    if assigned_to:query=query.where(OfficerReview.assigned_to==assigned_to)
    if alert_type:query=query.where(Alert.alert_type==alert_type)
    pairs=list(db.execute(query))
    if decision:pairs=[(r,a) for r,a in pairs if a.decision_state_current==decision]
    if watch_state:pairs=[(r,a) for r,a in pairs if (a.latest_evidence_snapshot.get('implementation_watch') or {}).get('status')==watch_state]
    if data_trust_state:pairs=[(r,a) for r,a in pairs if (a.data_trust_current or {}).get('data_status')==data_trust_state]
    rank={'HIGH':0,'NORMAL':1,'LOW':2};status_rank={'NEW':0,'ACKNOWLEDGED':1,'IN_REVIEW':2,'MONITORING':3,'PERSISTENT':4,'ESCALATED':5,'RESOLVED':6,'DISMISSED':7,'REOPENED':8}
    if sort=='priority':pairs.sort(key=lambda x:(rank.get(x[0].priority,9),x[0].created_at))
    elif sort=='oldest_unacknowledged':pairs.sort(key=lambda x:(x[1].status!='NEW',x[1].opened_at))
    elif sort=='persistence':pairs.sort(key=lambda x:(-x[1].consecutive_valid_cycles,x[1].opened_at))
    elif sort=='latest_update':pairs.sort(key=lambda x:x[1].last_updated_at,reverse=True)
    else:pairs.sort(key=lambda x:((x[1].decision_state_current or ''),x[0].created_at))
    total=len(pairs);start=(page-1)*page_size
    items=[review_dict(db,r,False)|{'alert_status':a.status,'alert_type':a.alert_type,'watch_state':(a.latest_evidence_snapshot.get('implementation_watch') or {}).get('status'),'decision_state':a.decision_state_current,'data_trust_state':(a.data_trust_current or {}).get('data_status')} for r,a in pairs[start:start+page_size]]
    return {'mode':mode,'data_origin':_mode(mode),'items':items,'page':page,'page_size':page_size,'total':total,'pages':math.ceil(total/page_size) if total else 0,'sorted_by':sort,'probability_sort_used':False}

@router.get('/reviews/{review_id}')
def get_review(review_id:str,mode:str=Query('REAL_HISTORICAL',pattern='^(REAL_HISTORICAL|SYNTHETIC_SANDBOX)$'),db:Session=Depends(get_db)):
    try:
        review=AlertWorkflowService(db).get_review(review_id)
        if review.data_origin!=_mode(mode):raise LookupError(review_id)
        return review_dict(db,review)
    except LookupError:raise HTTPException(404,detail={'code':'REVIEW_NOT_FOUND','message':'Review not found'})

@router.patch('/reviews/{review_id}')
def update_review(review_id:str,payload:ReviewUpdateRequest,db:Session=Depends(get_db)):
    try:review=AlertWorkflowService(db).update_review(review_id,payload.review_status,actor_type=payload.actor_type,actor_id=payload.actor_id,outcome=payload.outcome,next_review_date=payload.next_review_date,recommended_follow_up=payload.recommended_follow_up,verification_status=payload.verification_status);db.commit();return review_dict(db,review)
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'REVIEW_NOT_FOUND','message':'Review not found'})
    except ValueError as exc:db.rollback();_error(exc)

@router.post('/reviews/{review_id}/assign')
def assign_review(review_id:str,payload:AssignmentRequest,db:Session=Depends(get_db)):
    try:review=AlertWorkflowService(db).assign(review_id,payload.assigned_to,payload.actor_type,payload.actor_id);db.commit();return review_dict(db,review)
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'REVIEW_NOT_FOUND','message':'Review not found'})
    except ValueError as exc:db.rollback();_error(exc)

@router.post('/reviews/{review_id}/notes')
def add_note(review_id:str,payload:ReviewNoteRequest,db:Session=Depends(get_db)):
    try:item=AlertWorkflowService(db).add_note(review_id,payload.text,payload.note_type,payload.actor_type,payload.actor_id);db.commit();return {c.name:getattr(item,c.name) for c in item.__table__.columns}
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'REVIEW_NOT_FOUND','message':'Review not found'})
    except ValueError as exc:db.rollback();_error(exc)

@router.post('/reviews/{review_id}/actions')
def add_action(review_id:str,payload:ReviewActionRequest,db:Session=Depends(get_db)):
    try:item=AlertWorkflowService(db).add_action(review_id,payload.action_type,payload.detail,payload.actor_type,payload.actor_id);db.commit();return {c.name:getattr(item,c.name) for c in item.__table__.columns}
    except LookupError:db.rollback();raise HTTPException(404,detail={'code':'REVIEW_NOT_FOUND','message':'Review not found'})
    except ValueError as exc:db.rollback();_error(exc)

@router.get('/workflow/metrics')
def metrics(mode:str=Query('REAL_HISTORICAL',pattern='^(REAL_HISTORICAL|SYNTHETIC_SANDBOX)$'),db:Session=Depends(get_db)):return workflow_metrics(db,_mode(mode))
