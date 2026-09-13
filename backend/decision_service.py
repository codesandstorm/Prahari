"""Backend adapter for deterministic Officer Decision Layer V1."""
from __future__ import annotations
from collections import Counter
import math
from collections import defaultdict
from sqlalchemy import func,select
from .models import IngestionRun,Prediction,Project,ProjectSnapshot,SourceReport
from .data_trust import database_trust
from .repository import ProjectRepository,prediction_dict
from src.decision.governance import DECISION_POLICY_VERSION,decide_review
from .implementation_watch import database_implementation_watch
from src.implementation_watch.contracts import POLICY_VERSION as WATCH_POLICY_VERSION

_CACHE={'key':None,'items':None}

def _cache_key(db):
    run=db.scalar(select(IngestionRun).where(IngestionRun.status=='COMPLETED').order_by(IngestionRun.completed_at.desc()).limit(1));url=db.bind.url.render_as_string(hide_password=True)
    prediction_state=db.execute(select(func.count(Prediction.prediction_id),func.max(Prediction.created_at))).one()
    return (url,run.dataset_hash if run else 'unversioned',prediction_state,DECISION_POLICY_VERSION,WATCH_POLICY_VERSION)

def _build_items(db):
    repo=ProjectRepository(db);items=[];projects=list(db.scalars(select(Project).order_by(Project.canonical_project_id)));sources=list(db.scalars(select(SourceReport).order_by(SourceReport.reporting_month)));histories=defaultdict(list)
    for snapshot in db.scalars(select(ProjectSnapshot).order_by(ProjectSnapshot.canonical_project_id,ProjectSnapshot.reporting_month)):histories[snapshot.canonical_project_id].append(snapshot)
    predictions={}
    for prediction in db.scalars(select(Prediction).order_by(Prediction.canonical_project_id,Prediction.as_of_month.desc(),Prediction.created_at.desc())):predictions.setdefault(prediction.canonical_project_id,prediction)
    source_by_month={source.reporting_month:source for source in sources}
    for project in projects:
        project_history=histories[project.canonical_project_id];trust,_,view,release,eligibility=database_trust(db,repo,project,history_override=project_history,sources_override=sources);stored=predictions.get(project.canonical_project_id);prediction=prediction_dict(repo,stored) if stored else None;latest=project_history[-1] if project_history else None;watch=database_implementation_watch(repo,project,trust,history_override=project_history,source_override=source_by_month.get(latest.reporting_month) if latest else None);decision=decide_review(trust=trust,eligibility=eligibility,prediction=prediction,implementation_watch=watch.model_dump(mode='json'))
        if decision.review_state!='NO_REVIEW_SIGNAL':items.append(decision.to_dict()|{'project_name':project.canonical_name,'data_trust':view,'model_release':release.to_dict(),'prediction_eligibility':eligibility.to_dict(),'implementation_watch':watch.model_dump(mode='json'),'source_provenance_link':None,'project_intelligence_endpoint':f'/api/v1/projects/{project.canonical_project_id}/intelligence','prioritization_basis':['OFFICER_DECISION','IMPLEMENTATION_WATCH','DATA_VERIFICATION','DETERMINISTIC_SCHEDULE_PRESSURE']})
    return items

def review_queue(db,page=1,page_size=25,review_state=None,reason_code=None,model_release_state=None):
    key=_cache_key(db)
    if _CACHE['key']!=key:_CACHE.update(key=key,items=_build_items(db))
    items=list(_CACHE['items'])
    if review_state:items=[x for x in items if x['review_state']==review_state]
    if reason_code:items=[x for x in items if reason_code in x['reason_codes']]
    if model_release_state:items=[x for x in items if x['model_release']['status']==model_release_state]
    counts=Counter(x['review_state'] for x in items);total=len(items);start=(page-1)*page_size
    return {'items':items[start:start+page_size],'status':'ACTIVE_WITH_PREDICTIONS_WITHHELD','policy_version':DECISION_POLICY_VERSION,'counts':dict(counts),'page':page,'page_size':page_size,'total':total,'pages':math.ceil(total/page_size) if total else 0}
