from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from .database import get_db
from .models import Alert, Prediction, Project, ProjectSnapshot, SourceReport
from .repository import ProjectRepository, prediction_dict
from .schemas import AssistantOut, AssistantRequest, HistoryOut, PageOut, PredictionOut, ProjectDetail, ReviewQueueOut
from .data_trust import database_trust,guard_prediction_output
from .decision_service import review_queue as build_review_queue
from src.decision.governance import decide_review
from .implementation_watch import database_implementation_watch
from .product_intelligence import intelligence_dashboard_summary, list_sandbox_projects, real_project_intelligence, synthetic_project_intelligence
from src.intelligence.contracts import ProjectIntelligence

router=APIRouter()


def _source(db,snapshot):
    if not snapshot:return None
    source=db.get(SourceReport,snapshot.reporting_month)
    return {"reporting_month":source.reporting_month,"source_id":source.source_id,"coverage_class":source.coverage_class,"sha256":source.sha256,"schema_family":source.schema_family} if source else None


def _snapshot(db,item):
    if not item:return None
    fields=("reporting_month","agency","state","sector","project_observation_count","months_since_first_observation","progress_current","progress_velocity","expenditure_current","expenditure_velocity","cost_ratio")
    return {x:getattr(item,x) for x in fields}|{"source":_source(db,item)}


@router.get("/health")
def health(request:Request,db:Session=Depends(get_db)):
    try: db.execute(text("SELECT 1")); database="available"
    except Exception: database="unavailable"
    return {"status":"ok" if database=="available" else "degraded","database":database,"assistant":"enabled" if getattr(request.app.state,"assistant",None) else "degraded"}


@router.get("/projects",response_model=PageOut)
def projects(page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),search:str|None=Query(None,max_length=200),sector:str|None=Query(None,max_length=200),ministry:str|None=Query(None,max_length=200),sort:str=Query("canonical_project_id",pattern="^(canonical_project_id|name|agency|sector)$"),order:str=Query("asc",pattern="^(asc|desc)$"),db:Session=Depends(get_db)):
    repo=ProjectRepository(db);items,total,pages=repo.list(page,page_size,search,sector,ministry,sort,order);out=[]
    for p in items:
        snap=repo.latest_snapshot(p.canonical_project_id); pred=repo.latest_prediction(p.canonical_project_id)
        _,_,_,_,eligibility=database_trust(db,repo,p)
        out.append({"canonical_project_id":p.canonical_project_id,"project_code":p.project_code,"canonical_name":p.canonical_name,"agency":p.agency,"ministry":p.ministry,"sector":p.sector,"state":p.state,"latest_reporting_month":snap.reporting_month if snap else None,"prediction":guard_prediction_output(prediction_dict(repo,pred),eligibility)})
    return {"items":out,"page":page,"page_size":page_size,"total":total,"pages":pages}


@router.get("/projects/{project_id}",response_model=ProjectDetail)
def project_detail(project_id:str,db:Session=Depends(get_db)):
    repo=ProjectRepository(db);p=repo.get(project_id)
    if not p:raise HTTPException(404,detail={"code":"PROJECT_NOT_FOUND","message":"Project not found"})
    snap=repo.latest_snapshot(project_id);pred=repo.latest_prediction(project_id)
    trust_result,trust,_,release,eligibility=database_trust(db,repo,p);governed_prediction=guard_prediction_output(prediction_dict(repo,pred),eligibility);watch=database_implementation_watch(repo,p,trust_result);decision=decide_review(trust=trust_result,eligibility=eligibility,prediction=governed_prediction,implementation_watch=watch.model_dump(mode='json'))
    return {"canonical_project_id":p.canonical_project_id,"project_code":p.project_code,"canonical_name":p.canonical_name,"agency":p.agency,"ministry":p.ministry,"sector":p.sector,"state":p.state,"identity_method":p.identity_method,"identity_status":p.identity_status,"latest_reporting_month":snap.reporting_month if snap else None,"latest_snapshot":_snapshot(db,snap),"prediction":governed_prediction,"data_trust":trust,"model_release":release.to_dict(),"prediction_eligibility":eligibility.to_dict(),"officer_decision":decision.to_dict(),"implementation_watch":watch.model_dump(mode='json')}


@router.get("/projects/{project_id}/history",response_model=HistoryOut)
def history(project_id:str,db:Session=Depends(get_db)):
    repo=ProjectRepository(db)
    if not repo.get(project_id):raise HTTPException(404,detail={"code":"PROJECT_NOT_FOUND","message":"Project not found"})
    return {"canonical_project_id":project_id,"observations":[_snapshot(db,x) for x in repo.history(project_id)],"unavailable_months":[{"reporting_month":x.reporting_month,"source_id":x.source_id,"coverage_class":x.coverage_class,"sha256":x.sha256,"schema_family":x.schema_family} for x in repo.unavailable_months()],"interpolated":False}


@router.get("/projects/{project_id}/intelligence",response_model=ProjectIntelligence)
def project_intelligence(project_id:str,db:Session=Depends(get_db)):
    try:return real_project_intelligence(db,project_id)
    except LookupError:raise HTTPException(404,detail={"code":"PROJECT_NOT_FOUND","message":"Project not found"})


@router.get("/projects/{project_id}/benchmark")
def project_benchmark(project_id:str,db:Session=Depends(get_db)):
    try:return real_project_intelligence(db,project_id).peer_benchmark
    except LookupError:raise HTTPException(404,detail={"code":"PROJECT_NOT_FOUND","message":"Project not found"})


@router.get("/sandbox/projects")
def sandbox_projects(page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),watch_status:str|None=Query(None,pattern="^(CLEAR|WATCH|ELEVATED|DATA_INSUFFICIENT)$")):
    return list_sandbox_projects(page,page_size,watch_status)


@router.get("/sandbox/projects/{project_id}/intelligence",response_model=ProjectIntelligence)
def sandbox_project_intelligence(project_id:str):
    try:return synthetic_project_intelligence(project_id)
    except LookupError:raise HTTPException(404,detail={"code":"SYNTHETIC_PROJECT_NOT_FOUND","message":"Synthetic sandbox project not found"})


@router.get("/projects/{project_id}/prediction",response_model=PredictionOut|None)
def prediction(project_id:str,db:Session=Depends(get_db)):
    repo=ProjectRepository(db)
    if not repo.get(project_id):raise HTTPException(404,detail={"code":"PROJECT_NOT_FOUND","message":"Project not found"})
    project=repo.get(project_id);_,_,_,_,eligibility=database_trust(db,repo,project)
    return guard_prediction_output(prediction_dict(repo,repo.latest_prediction(project_id)),eligibility)


@router.get("/dashboard/summary")
def dashboard(db:Session=Depends(get_db)):
    return {"projects":db.scalar(select(func.count()).select_from(Project)) or 0,"observations":db.scalar(select(func.count()).select_from(ProjectSnapshot)) or 0,"predictions":db.scalar(select(func.count()).select_from(Prediction)) or 0,"alerts":db.scalar(select(func.count()).select_from(Alert)) or 0,"note":"Predictions and alerts are independently counted."}


@router.get("/dashboard/intelligence-summary")
def dashboard_intelligence_summary(mode:str=Query("REAL_HISTORICAL",pattern="^(REAL_HISTORICAL|SYNTHETIC_SANDBOX)$"),db:Session=Depends(get_db)):
    return intelligence_dashboard_summary(db,mode)


@router.get("/review-queue",response_model=ReviewQueueOut)
def review_queue(page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),review_state:str|None=Query(None,pattern="^(REVIEW_RECOMMENDED|DATA_VERIFICATION_REQUIRED|MONITOR|PREDICTION_WITHHELD)$"),reason_code:str|None=Query(None,max_length=80),model_release_state:str|None=Query(None,pattern="^(RELEASED|WITHHELD)$"),db:Session=Depends(get_db)):
    return build_review_queue(db,page,page_size,review_state,reason_code,model_release_state)


@router.post("/assistant/query",response_model=AssistantOut)
def assistant_query(payload:AssistantRequest,request:Request,db:Session=Depends(get_db)):
    adapter=getattr(request.app.state,"assistant",None)
    if adapter is None:raise HTTPException(503,detail={"code":"ASSISTANT_UNAVAILABLE","message":"Assistant service is disabled"})
    try:return adapter.answer(db,payload.request_id,payload.question,payload.canonical_project_id)
    except LookupError:raise HTTPException(404,detail={"code":"PROJECT_NOT_FOUND","message":"Project not found"})
