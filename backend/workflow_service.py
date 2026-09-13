"""Transactional alert episodes, officer reviews, and append-only audit history."""
from __future__ import annotations
import hashlib,json,math,uuid
from datetime import date,datetime,timezone
from statistics import median

from sqlalchemy import func,select
from sqlalchemy.exc import IntegrityError

from src.workflow.alert_policy import POLICY,AlertCandidate,deduplication_key,evaluate_alert_candidate
from src.workflow.lifecycle import REVIEW_POLICY,REVIEW_POLICY_VERSION,transition_alert,transition_review
from .models import Alert,AlertHistory,OfficerReview,Project,ReviewAction,ReviewNote

ACTIVE_ALERT_STATES={'NEW','ACKNOWLEDGED','IN_REVIEW','MONITORING','PERSISTENT','ESCALATED','REOPENED'}
SEVERITY_RANK={'INFO':0,'ATTENTION':1,'HIGH':2}
SYSTEM_ACTOR='SYSTEM'


def _now():return datetime.now(timezone.utc)
def _id(prefix):return f'{prefix}-{uuid.uuid4().hex}'
def _as_dict(value):return value.model_dump(mode='json') if hasattr(value,'model_dump') else dict(value)
def _fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def _validate_actor(actor_type,actor_id):
    if actor_type!='SYSTEM' and not actor_id:raise ValueError('actor_id is required for officer/reviewer mutations')


def evidence_snapshot(intelligence:dict)->dict:
    benchmark=intelligence.get('peer_benchmark') or {}
    return {'contract_version':intelligence.get('contract_version'),'mode':intelligence.get('mode'),'data_origin':intelligence.get('data_origin'),'as_of_month':(intelligence.get('current_state') or {}).get('as_of_month'),'current_state':intelligence.get('current_state') or {},'implementation_watch':intelligence.get('implementation_watch') or {},'data_trust':intelligence.get('data_trust') or {},'officer_decision':intelligence.get('officer_decision') or {},'benchmark_summary':{'benchmark_status':benchmark.get('benchmark_status'),'peer_count':benchmark.get('peer_count'),'peer_group':benchmark.get('peer_group'),'policy_version':benchmark.get('policy_version')},'evidence_summary':intelligence.get('evidence_summary') or [],'alert_policy_version':POLICY['policy_version']}


def evidence_difference(opening:dict,current:dict)->dict:
    old=set((opening.get('implementation_watch') or {}).get('reason_codes',[]));new=set((current.get('implementation_watch') or {}).get('reason_codes',[]))
    return {'changed_reason_codes':sorted(old^new),'new_reason_codes':sorted(new-old),'resolved_reason_codes':sorted(old-new),'old_watch_status':(opening.get('implementation_watch') or {}).get('status'),'new_watch_status':(current.get('implementation_watch') or {}).get('status')}


def _history(db,alert,event_type,reason,actor_type=SYSTEM_ACTOR,actor_id=None,old_state=None,new_state=None,metadata=None,evidence_reference=None):
    event=AlertHistory(event_id=_id('EVT'),alert_id=alert.alert_id,canonical_project_id=alert.canonical_project_id,event_type=event_type,timestamp=_now(),actor_type=actor_type,actor_id=actor_id,old_state=old_state,new_state=new_state,reason=reason,event_metadata=metadata or {},evidence_reference=evidence_reference);db.add(event);return event


def _ensure_project(db,intelligence):
    identity=intelligence['identity'];pid=identity['canonical_project_id'];project=db.get(Project,pid)
    if project:return project
    if intelligence['data_origin']!='SYNTHETIC_CUF_PROTOTYPE':raise LookupError(pid)
    project=Project(canonical_project_id=pid,project_code=None,canonical_name=identity.get('project_name') or pid,agency=identity.get('agency'),ministry=identity.get('ministry'),sector=identity.get('sector'),state=identity.get('location'),identity_method='SYNTHETIC_FIXTURE',identity_status='SYNTHETIC',data_origin='SYNTHETIC_CUF_PROTOTYPE');db.add(project);db.flush();return project


def _priority(candidate:AlertCandidate)->str:
    return 'HIGH' if candidate.severity=='HIGH' else 'NORMAL' if candidate.eligible else 'LOW'


class AlertWorkflowService:
    def __init__(self,db):self.db=db

    def evaluate(self,intelligence,*,reopen_actor_type=SYSTEM_ACTOR,reopen_actor_id=None,reopen_reason=None)->dict:
        payload=_as_dict(intelligence);_ensure_project(self.db,payload);candidate=evaluate_alert_candidate(payload);snapshot=evidence_snapshot(payload);pid=payload['identity']['canonical_project_id'];origin=payload['data_origin'];as_of=snapshot['as_of_month'];created=False;changed=False
        if not candidate.eligible:
            evaluable=(payload.get('data_trust') or {}).get('data_status')=='USABLE' and (payload.get('implementation_watch') or {}).get('status')=='CLEAR'
            resolved=[]
            if evaluable:
                for alert in self.db.scalars(select(Alert).where(Alert.canonical_project_id==pid,Alert.data_origin==origin,Alert.status.in_(ACTIVE_ALERT_STATES))):
                    old=alert.status;transition_alert(old,'RESOLVED');alert.status='RESOLVED';alert.resolved_at=_now();alert.last_updated_at=_now();alert.latest_evidence_snapshot=snapshot;alert.decision_state_current=(snapshot['officer_decision'] or {}).get('review_state');alert.data_trust_current=snapshot['data_trust'];alert.last_seen_month=as_of;_history(self.db,alert,'ALERT_RESOLVED','Current evidence is evaluable and the governed alert condition is no longer present.',old_state=old,new_state='RESOLVED',metadata=evidence_difference(alert.initial_evidence_snapshot,snapshot),evidence_reference=_fingerprint(snapshot));resolved.append(alert.alert_id)
            return {'eligible':False,'created':False,'changed':bool(resolved),'alert_ids':resolved,'explanation':candidate.explanation}
        key=deduplication_key(pid,origin,candidate.alert_type,candidate.reason_family);alert=self.db.scalar(select(Alert).where(Alert.deduplication_key==key))
        if alert is None:
            alert=Alert(alert_id='ALT-'+key[:24],canonical_project_id=pid,prediction_id=None,status='NEW',policy_version=POLICY['policy_version'],reason=candidate.explanation,alert_type=candidate.alert_type,severity=candidate.severity,data_origin=origin,deduplication_key=key,reason_family=candidate.reason_family,trigger_reason_codes=list(candidate.trigger_reason_codes),current_reason_codes=list(candidate.trigger_reason_codes),initial_evidence_snapshot=snapshot,latest_evidence_snapshot=snapshot,decision_state_at_open=(snapshot['officer_decision'] or {}).get('review_state'),decision_state_current=(snapshot['officer_decision'] or {}).get('review_state'),data_trust_at_open=snapshot['data_trust'],data_trust_current=snapshot['data_trust'],opened_at=_now(),last_updated_at=_now(),first_seen_month=as_of,last_seen_month=as_of,consecutive_valid_cycles=1,watch_policy_version=(snapshot['implementation_watch'] or {}).get('policy_version'),decision_policy_version=(snapshot['officer_decision'] or {}).get('decision_policy_version'),review_policy_version=REVIEW_POLICY_VERSION)
            try:
                with self.db.begin_nested():self.db.add(alert);self.db.flush()
            except IntegrityError:
                alert=self.db.scalar(select(Alert).where(Alert.deduplication_key==key));return {'eligible':True,'created':False,'changed':False,'alert_ids':[alert.alert_id],'explanation':'Concurrent equivalent evaluation reused the governed alert episode.'}
            created=True;changed=True;_history(self.db,alert,'ALERT_CREATED',candidate.explanation,new_state='NEW',metadata={'candidate':candidate.__dict__},evidence_reference=_fingerprint(snapshot));self._ensure_review(alert,candidate)
        else:
            prior_fp=_fingerprint(alert.latest_evidence_snapshot or {});current_fp=_fingerprint(snapshot)
            if alert.last_seen_month==as_of and prior_fp==current_fp:return {'eligible':True,'created':False,'changed':False,'alert_ids':[alert.alert_id],'explanation':'Unchanged evaluation reused the existing alert episode.'}
            old=alert.status
            if old in {'RESOLVED','DISMISSED'}:
                if not as_of or (alert.last_seen_month and as_of<=alert.last_seen_month):return {'eligible':True,'created':False,'changed':False,'alert_ids':[alert.alert_id],'explanation':'Reopen requires newer equivalent evidence.'}
                _validate_actor(reopen_actor_type,reopen_actor_id)
                transition_alert(old,'REOPENED');alert.status='REOPENED';alert.reopened_at=_now();alert.resolved_at=None;alert.consecutive_valid_cycles=1
                review=self.db.scalar(select(OfficerReview).where(OfficerReview.alert_id==alert.alert_id))
                if review and review.review_status in {'COMPLETE','CLOSED_NO_ACTION'}:
                    review.review_status='NOT_STARTED';review.review_started_at=None;review.review_completed_at=None;review.outcome=None;review.last_updated_at=_now()
                _history(self.db,alert,'ALERT_REOPENED',reopen_reason or 'Equivalent governed evidence recurred after closure.',reopen_actor_type,reopen_actor_id,old_state=old,new_state='REOPENED',evidence_reference=current_fp);changed=True
            elif as_of and as_of!=alert.last_seen_month:
                alert.consecutive_valid_cycles+=1
                if SEVERITY_RANK[candidate.severity]>SEVERITY_RANK.get(alert.severity,0):
                    transition_alert(alert.status,'ESCALATED');prior=alert.status;alert.status='ESCALATED';_history(self.db,alert,'ALERT_ESCALATED','Governed alert severity increased.',old_state=prior,new_state='ESCALATED',metadata={'old_severity':alert.severity,'new_severity':candidate.severity});changed=True
                elif alert.consecutive_valid_cycles>=POLICY['persistence_valid_cycles'] and alert.status in {'NEW','ACKNOWLEDGED','MONITORING','REOPENED'}:
                    prior=alert.status;transition_alert(prior,'PERSISTENT');alert.status='PERSISTENT';_history(self.db,alert,'STATUS_CHANGED','Equivalent evidence persisted across governed valid cycles.',old_state=prior,new_state='PERSISTENT');changed=True
            if SEVERITY_RANK[candidate.severity]<SEVERITY_RANK.get(alert.severity,0):
                _history(self.db,alert,'SEVERITY_CHANGED','Governed evidence reduced the alert severity without proving resolution.',old_state=alert.status,new_state=alert.status,metadata={'old_severity':alert.severity,'new_severity':candidate.severity},evidence_reference=current_fp)
            alert.severity=candidate.severity;alert.current_reason_codes=list(candidate.trigger_reason_codes);alert.latest_evidence_snapshot=snapshot;alert.decision_state_current=(snapshot['officer_decision'] or {}).get('review_state');alert.data_trust_current=snapshot['data_trust'];alert.last_seen_month=as_of;alert.last_updated_at=_now();_history(self.db,alert,'EVIDENCE_UPDATED','Governed project intelligence evidence was refreshed.',old_state=old,new_state=alert.status,metadata=evidence_difference(alert.initial_evidence_snapshot,snapshot),evidence_reference=current_fp);changed=True
        return {'eligible':True,'created':created,'changed':changed,'alert_ids':[alert.alert_id],'explanation':candidate.explanation}

    def _ensure_review(self,alert,candidate):
        existing=self.db.scalar(select(OfficerReview).where(OfficerReview.alert_id==alert.alert_id))
        if existing:return existing
        review=OfficerReview(review_id='REV-'+alert.alert_id[4:],canonical_project_id=alert.canonical_project_id,alert_id=alert.alert_id,data_origin=alert.data_origin,review_status='NOT_STARTED',priority=_priority(candidate),review_reason_codes=list(candidate.trigger_reason_codes),review_policy_version=REVIEW_POLICY_VERSION,verification_status='UNRESOLVED' if candidate.reason_family=='DATA_VERIFICATION' else None);self.db.add(review);self.db.flush();return review

    def transition(self,alert_id,new_state,*,actor_type,actor_id=None,reason):
        _validate_actor(actor_type,actor_id);alert=self.get_alert(alert_id);old=alert.status;transition_alert(old,new_state)
        if new_state=='REOPENED':raise ValueError('reopen requires newer equivalent evidence through project re-evaluation')
        if new_state=='DISMISSED' and reason not in REVIEW_POLICY['dismissal_reasons'] and not reason.startswith('OTHER:'):raise ValueError('governed dismissal reason is required')
        if new_state=='RESOLVED':
            if not reason.strip():raise ValueError('resolution reason is required')
            evidence=alert.latest_evidence_snapshot or {};trust=evidence.get('data_trust') or {};watch=evidence.get('implementation_watch') or {};cleared=trust.get('data_status')=='USABLE' and watch.get('status')=='CLEAR';review=self.db.scalar(select(OfficerReview).where(OfficerReview.alert_id==alert_id));verified=alert.alert_type in {'DATA_VERIFICATION','REPORTING_GAP','SOURCE_QUALITY'} and review and review.verification_status in {'VERIFIED','CORRECTED'}
            if not cleared and not verified:raise ValueError('resolution requires valid clear evidence or a verified data correction')
        alert.status=new_state;alert.last_updated_at=_now()
        if new_state=='RESOLVED':alert.resolved_at=_now()
        event={'ACKNOWLEDGED':'ALERT_ACKNOWLEDGED','IN_REVIEW':'REVIEW_STARTED','MONITORING':'STATUS_CHANGED','RESOLVED':'ALERT_RESOLVED','DISMISSED':'ALERT_DISMISSED','REOPENED':'ALERT_REOPENED','ESCALATED':'ALERT_ESCALATED','PERSISTENT':'STATUS_CHANGED'}[new_state]
        _history(self.db,alert,event,reason,actor_type,actor_id,old,new_state);return alert

    def get_alert(self,alert_id):
        alert=self.db.get(Alert,alert_id)
        if alert is None:raise LookupError(alert_id)
        return alert

    def get_review(self,review_id):
        review=self.db.get(OfficerReview,review_id)
        if review is None:raise LookupError(review_id)
        return review

    def assign(self,review_id,assigned_to,actor_type,actor_id=None):
        _validate_actor(actor_type,actor_id);review=self.get_review(review_id);old=review.assigned_to;review.assigned_to=assigned_to;review.last_updated_at=_now();alert=self.get_alert(review.alert_id);_history(self.db,alert,'ASSIGNEE_CHANGED','Review assignment changed.',actor_type,actor_id,metadata={'old_assignee':old,'new_assignee':assigned_to});return review

    def update_review(self,review_id,new_status,*,actor_type,actor_id=None,outcome=None,next_review_date=None,recommended_follow_up=None,verification_status=None):
        _validate_actor(actor_type,actor_id);review=self.get_review(review_id);old=review.review_status
        if old!=new_status:transition_review(old,new_status)
        if next_review_date and next_review_date<date.today():raise ValueError('next_review_date cannot be in the past')
        if outcome and outcome not in REVIEW_POLICY['outcomes']:raise ValueError('unsupported review outcome')
        if new_status in {'COMPLETE','CLOSED_NO_ACTION'} and outcome is None:raise ValueError('closure requires a structured outcome')
        if new_status=='CLOSED_NO_ACTION' and outcome!='NO_ACTION_REQUIRED':raise ValueError('CLOSED_NO_ACTION requires NO_ACTION_REQUIRED outcome')
        if verification_status and verification_status not in {'VERIFIED','CORRECTED','SOURCE_PENDING','UNRESOLVED'}:raise ValueError('unsupported verification status')
        review.review_status=new_status;review.outcome=outcome;review.next_review_date=next_review_date;review.recommended_follow_up=recommended_follow_up;review.verification_status=verification_status or review.verification_status;review.last_updated_at=_now()
        if new_status=='IN_PROGRESS' and review.review_started_at is None:review.review_started_at=_now()
        if new_status in {'COMPLETE','CLOSED_NO_ACTION'}:review.review_completed_at=_now()
        alert=self.get_alert(review.alert_id);_history(self.db,alert,'STATUS_CHANGED' if old!=new_status else 'REVIEW_UPDATED','Officer review status changed.' if old!=new_status else 'Officer review follow-up fields updated.',actor_type,actor_id,old,new_status,{'outcome':outcome,'next_review_date':next_review_date.isoformat() if next_review_date else None});return review

    def add_note(self,review_id,text,note_type,actor_type,actor_id=None):
        _validate_actor(actor_type,actor_id)
        if note_type not in REVIEW_POLICY['note_types']:raise ValueError('unsupported note type')
        review=self.get_review(review_id);note=ReviewNote(note_id=_id('NOTE'),review_id=review_id,actor_type=actor_type,actor_id=actor_id,text=text,note_type=note_type);self.db.add(note);alert=self.get_alert(review.alert_id);_history(self.db,alert,'NOTE_ADDED','Officer review note added.',actor_type,actor_id,metadata={'note_id':note.note_id,'note_type':note_type});return note

    def add_action(self,review_id,action_type,detail,actor_type,actor_id=None):
        _validate_actor(actor_type,actor_id)
        if action_type not in REVIEW_POLICY['actions']:raise ValueError('unsupported review action')
        review=self.get_review(review_id);action=ReviewAction(action_id=_id('ACT'),review_id=review_id,actor_type=actor_type,actor_id=actor_id,action_type=action_type,detail=detail);self.db.add(action);alert=self.get_alert(review.alert_id);_history(self.db,alert,'ACTION_RECORDED','Bounded officer review action recorded.',actor_type,actor_id,metadata={'action_id':action.action_id,'action_type':action_type});return action


def alert_dict(alert):
    return {c.name:getattr(alert,c.name) for c in alert.__table__.columns}|{'evidence_difference':evidence_difference(alert.initial_evidence_snapshot or {},alert.latest_evidence_snapshot or {})}
def event_dict(event):
    return {'event_id':event.event_id,'alert_id':event.alert_id,'canonical_project_id':event.canonical_project_id,'event_type':event.event_type,'timestamp':event.timestamp,'actor_type':event.actor_type,'actor_id':event.actor_id,'old_state':event.old_state,'new_state':event.new_state,'reason':event.reason,'metadata':event.event_metadata,'evidence_reference':event.evidence_reference}
def review_dict(db,review,include_children=True):
    result={c.name:getattr(review,c.name) for c in review.__table__.columns}
    if include_children:result|={'notes':[ {c.name:getattr(x,c.name) for c in x.__table__.columns} for x in db.scalars(select(ReviewNote).where(ReviewNote.review_id==review.review_id).order_by(ReviewNote.created_at))], 'actions':[ {c.name:getattr(x,c.name) for c in x.__table__.columns} for x in db.scalars(select(ReviewAction).where(ReviewAction.review_id==review.review_id).order_by(ReviewAction.created_at))]}
    return result


def workflow_metrics(db,data_origin):
    alerts=list(db.scalars(select(Alert).where(Alert.data_origin==data_origin)));events=list(db.scalars(select(AlertHistory).join(Alert).where(Alert.data_origin==data_origin)));reviews=list(db.scalars(select(OfficerReview).where(OfficerReview.data_origin==data_origin)))
    ack=[];dur=[]
    for alert in alerts:
        a=next((x for x in events if x.alert_id==alert.alert_id and x.event_type=='ALERT_ACKNOWLEDGED'),None)
        if a and alert.opened_at:ack.append((a.timestamp-alert.opened_at).total_seconds())
    for review in reviews:
        if review.review_started_at and review.review_completed_at:dur.append((review.review_completed_at-review.review_started_at).total_seconds())
    recent=lambda value:bool(value and (_now().replace(tzinfo=None)-value.replace(tzinfo=None)).days<=30)
    return {'data_origin':data_origin,'alerts_opened':len(alerts),'new_alerts':sum(x.status=='NEW' for x in alerts),'unacknowledged_alerts':sum(x.status in {'NEW','REOPENED'} for x in alerts),'alerts_acknowledged':sum(x.event_type=='ALERT_ACKNOWLEDGED' for x in events),'in_review':sum(x.review_status in {'IN_PROGRESS','ACTION_REQUIRED'} for x in reviews),'monitoring':sum(x.review_status=='MONITORING' for x in reviews),'data_verification':sum(x.alert_type in {'DATA_VERIFICATION','REPORTING_GAP','SOURCE_QUALITY'} and x.status in ACTIVE_ALERT_STATES for x in alerts),'alerts_resolved':sum(x.status=='RESOLVED' for x in alerts),'resolved_recently':sum(x.status=='RESOLVED' and recent(x.resolved_at) for x in alerts),'alerts_persistent':sum(x.status=='PERSISTENT' for x in alerts),'alerts_escalated':sum(x.status=='ESCALATED' for x in alerts),'reopen_count':sum(x.event_type=='ALERT_REOPENED' for x in events),'median_acknowledgement_seconds':median(ack) if ack else None,'median_review_duration_seconds':median(dur) if dur else None,'metric_type':'WORKFLOW_OPERATIONAL_NOT_ML'}
