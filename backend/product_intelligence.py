"""Backend adapters for real and synthetic Unified Project Intelligence V1."""
from __future__ import annotations

import math
from datetime import date
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from sqlalchemy import func, select

from src.benchmarking import BenchmarkMode, BenchmarkRecord, PeerBenchmarkService, cost_band, lifecycle_band
from src.decision.governance import ModelReleaseStatus, assess_prediction_eligibility, decide_review
from src.implementation_watch import ImplementationWatchEngine
from src.implementation_watch.contracts import Availability
from src.intelligence import IntelligenceMode, build_project_intelligence
from src.ml.final_prediction import approved_doc, build_compact_v2
from src.ml.provisional_research import month_date, number, value
from src.sandbox import SyntheticSandboxRepository
from src.trust.data_trust import DataTrustResult, Dimension

from .data_trust import database_trust
from .implementation_watch import database_implementation_watch
from .models import Project, ProjectSnapshot, SourceReport
from .repository import ProjectRepository, prediction_dict


def _finite(value) -> bool:
    return isinstance(value,(int,float)) and math.isfinite(float(value))


def _real_row(snapshot, source=None) -> dict:
    raw=dict(snapshot.raw_features or {})
    return raw|{"canonical_project_id":snapshot.canonical_project_id,"reporting_month":snapshot.reporting_month.strftime("%Y-%m"),"reported_physical_progress":snapshot.progress_current,"reported_cumulative_expenditure":snapshot.expenditure_current,"source_id":source.source_id if source else "","source_sha256":source.sha256 if source else "","schema_family":source.schema_family if source else ""}


def _record(project, history, watch, origin="HISTORICAL_FLASH_REPORT") -> BenchmarkRecord:
    rows=[_real_row(x) for x in history] if origin=="HISTORICAL_FLASH_REPORT" else history
    latest=rows[-1]; features={}
    if origin=="HISTORICAL_FLASH_REPORT":
        try: features=build_compact_v2(rows)
        except (ValueError,KeyError,AssertionError): features={}
        original=number(value(latest,"original_cost_raw","reported_original_cost")); revised=number(value(latest,"revised_cost_raw","reported_revised_cost")); expenditure=number(value(latest,"cumulative_expenditure_raw","reported_cumulative_expenditure")); progress=number(value(latest,"physical_progress_raw","reported_physical_progress")); approval=month_date(value(latest,"approval_date_raw","reported_approval_date")); completion=approved_doc(latest)
        sector=project.sector or getattr(history[-1],"sector",None)
    else:
        original=float(latest["original_cost"]); revised=float(latest["current_cost"]); expenditure=float(latest["cumulative_expenditure"]); progress=float(latest["actual_physical_progress"]) if latest["actual_physical_progress"] else math.nan; approval=date.fromisoformat(latest["approval_date"]); completion=date.fromisoformat(latest["revised_completion_date"]); sector=project["sector"]
        as_of_date=date.fromisoformat(latest["reporting_month"]+"-01")
        months_elapsed=max(0,(as_of_date.year-approval.year)*12+as_of_date.month-approval.month)
        features={"project_age_months":months_elapsed,"remaining_schedule_months":float(latest["remaining_schedule_months"]),"required_future_velocity":float(latest["required_future_velocity"]) if latest["required_future_velocity"] else math.nan,"progress_vs_elapsed_gap":math.nan,"expenditure_velocity":float(latest["cumulative_expenditure"])-float(rows[-2]["cumulative_expenditure"]) if len(rows)>1 else math.nan}
    current=revised if _finite(revised) else original
    signal_values={x["code"]:x.get("value") for x in watch.get("signals",[]) if x.get("status")=="DETECTED"}
    metrics={"original_cost":original,"current_cost":current,"cost_revision_pct":100*(current-original)/original if _finite(current) and _finite(original) and original>0 else math.nan,"cumulative_expenditure_ratio":expenditure/current if _finite(expenditure) and _finite(current) and current>0 else math.nan,"physical_progress":progress,"project_age_months":features.get("project_age_months"),"remaining_schedule_months":features.get("remaining_schedule_months"),"required_future_velocity":features.get("required_future_velocity"),"progress_vs_elapsed_gap":features.get("progress_vs_elapsed_gap"),"expenditure_velocity":features.get("expenditure_velocity"),"watch_signal_count":sum(x.get("status")=="DETECTED" and x.get("family") not in {"REPORTING","DATA_QUALITY"} for x in watch.get("signals",[])),"milestone_slippage_days":signal_values.get("SEVERE_MILESTONE_SLIPPAGE"),"land_remaining_pct":signal_values.get("HIGH_LAND_REMAINING"),"pending_clearances":signal_values.get("MULTIPLE_CLEARANCES_PENDING",signal_values.get("CLEARANCE_PENDING")),"tender_cycle_days":signal_values.get("TENDER_CYCLE_PROLONGED")}
    as_of=date.fromisoformat(latest["reporting_month"]+"-01")
    return BenchmarkRecord(str(project.canonical_project_id if origin=="HISTORICAL_FLASH_REPORT" else project["canonical_project_id"]),latest["reporting_month"],origin,sector or "UNKNOWN",cost_band(original),lifecycle_band(approval,completion,as_of),metrics)


_REAL_CACHE={"key":None,"bundle":None}


def _real_bundle(db, repo):
    state=(db.scalar(select(func.count()).select_from(Project)) or 0,db.scalar(select(func.count()).select_from(ProjectSnapshot)) or 0,db.scalar(select(func.max(ProjectSnapshot.reporting_month))))
    key=(db.bind.url.render_as_string(hide_password=True),state)
    if _REAL_CACHE["key"]==key:return _REAL_CACHE["bundle"]
    sources=repo.all_sources(); source_by_month={x.reporting_month:x for x in sources}; all_projects=repo.all_projects(); histories=defaultdict(list)
    for item in db.scalars(select(ProjectSnapshot).order_by(ProjectSnapshot.canonical_project_id,ProjectSnapshot.reporting_month)): histories[item.canonical_project_id].append(item)
    records=[]; assessments={}
    for candidate in all_projects:
        history=histories[candidate.canonical_project_id]
        if not history: continue
        result,trust,view,release,eligibility=database_trust(db,repo,candidate,history_override=history,sources_override=sources); cwatch=database_implementation_watch(repo,candidate,result,history_override=history,source_override=source_by_month.get(history[-1].reporting_month)).model_dump(mode="json");assessments[candidate.canonical_project_id]=(result,trust,view,release,eligibility,cwatch)
        records.append(_record(candidate,history,cwatch))
    bundle=(sources,source_by_month,{p.canonical_project_id:p for p in all_projects},histories,records,assessments)
    _REAL_CACHE.update(key=key,bundle=bundle);return bundle


def real_project_intelligence(db, project_id: str):
    repo=ProjectRepository(db); sources,source_by_month,projects,histories,records,assessments=_real_bundle(db,repo);project=projects.get(project_id)
    if project is None: raise LookupError(project_id)
    trust_result,trust,trust_view,release,eligibility,watch=assessments[project_id]
    prediction=prediction_dict(repo,repo.latest_prediction(project_id)); decision=decide_review(trust=trust_result,eligibility=eligibility,prediction=prediction,implementation_watch=watch).to_dict()
    subject=next(x for x in records if x.canonical_project_id==project_id); benchmark=PeerBenchmarkService(records).benchmark(subject,BenchmarkMode.REAL_CURRENT).model_dump(mode="json")
    latest=histories[project_id][-1] if histories[project_id] else None; source=source_by_month.get(latest.reporting_month) if latest else None; raw=_real_row(latest,source) if latest else {}
    original=number(value(raw,"original_cost_raw","reported_original_cost")); revised=number(value(raw,"revised_cost_raw","reported_revised_cost")); current=revised if _finite(revised) else original; expenditure=latest.expenditure_current if latest else math.nan
    state={"as_of_month":latest.reporting_month.strftime("%Y-%m") if latest else None,"original_cost":original if _finite(original) else None,"current_cost":current if _finite(current) else None,"cost_escalation_pct":100*(current-original)/original if _finite(current) and _finite(original) and original>0 else None,"cumulative_expenditure":expenditure if _finite(expenditure) else None,"physical_progress":latest.progress_current if latest else None,"approval_date":value(raw,"approval_date_raw","reported_approval_date") or None,"original_completion_date":value(raw,"original_target_doc_raw","reported_original_target_doc") or None,"current_approved_completion_date":value(raw,"revised_doc_raw","reported_revised_doc") or value(raw,"original_target_doc_raw","reported_original_target_doc") or None,"project_status":raw.get("project_status_raw"),"availability":{"source_backed":True if latest else False}}
    evidence=[]
    if source: evidence=[{"data_origin":"HISTORICAL_FLASH_REPORT","source_id":source.source_id,"reporting_month":source.reporting_month.strftime("%Y-%m"),"sha256":source.sha256,"page":raw.get("pdf_page_index"),"table":raw.get("source_table"),"signal_codes":watch.get("reason_codes",[])}]
    identity={"canonical_project_id":project_id,"project_name":project.canonical_name,"sector":project.sector or (latest.sector if latest else None) or "UNKNOWN","ministry":project.ministry,"agency":project.agency,"location":project.state,"project_status":state["project_status"],"as_of_month":state["as_of_month"],"agency_is_contractor":False}
    return build_project_intelligence(mode=IntelligenceMode.REAL_HISTORICAL,identity=identity,current_state=state,watch=watch,trust=trust_view|{"dimensions":trust},benchmark=benchmark,officer_decision=decision,evidence=evidence,provenance={"canonical_source":"project_month.csv","source_report":source.source_id if source else None,"source_sha256":source.sha256 if source else None,"interpolated":False})


def _synthetic_trust(pid: str, month: str, usable: bool) -> DataTrustResult:
    good=Dimension("PASS","SYNTHETIC_EVIDENCE_COMPLETE","Synthetic fixture evidence is complete"); bad=Dimension("FAIL","SOURCE_AS_OF_OBSERVATION_UNAVAILABLE","Synthetic source-gap fixture")
    chosen=good if usable else bad
    return DataTrustResult(pid,month,good,chosen,chosen,good,chosen,good,good,chosen,24,24,24 if usable else 0,13,[month] if usable else [],[],[month] if not usable else [],[],[],[],usable,[] if usable else [chosen.code])


@lru_cache(maxsize=1)
def _sandbox_bundle():
    repo=SyntheticSandboxRepository(); engine=ImplementationWatchEngine(); records=[]; watches={}
    for project in repo.list_projects():
        pid=project["canonical_project_id"]; history=repo.history(pid); snap=repo.snapshot(pid); progress=[(r["reporting_month"],float(r["actual_physical_progress"]) if r["actual_physical_progress"] else None,Availability(r["source_availability"])) for r in history]
        previous=engine.evaluate(repo.snapshot(pid,history[-2]["reporting_month"]),progress_history=progress[:-1],data_trust=_synthetic_trust(pid,history[-2]["reporting_month"],True))
        usable=history[-1]["source_availability"]=="AVAILABLE" and history[-1]["provenance_complete"]=="TRUE"
        watch=engine.evaluate(snap,progress_history=progress,data_trust=_synthetic_trust(pid,history[-1]["reporting_month"],usable),previous=previous).model_dump(mode="json"); watches[pid]=(watch,previous.model_dump(mode="json")); records.append(_record(project,history,watch,"SYNTHETIC_CUF_PROTOTYPE"))
    return repo,watches,records


def synthetic_project_intelligence(project_id: str):
    repo,watches,records=_sandbox_bundle(); project=repo.project(project_id)
    if project is None: raise LookupError(project_id)
    history=repo.history(project_id); latest=history[-1]; watch,previous=watches[project_id]; usable=latest["source_availability"]=="AVAILABLE" and latest["provenance_complete"]=="TRUE"; trust=_synthetic_trust(project_id,latest["reporting_month"],usable); eligibility=assess_prediction_eligibility(trust,ModelReleaseStatus()); decision=decide_review(trust=trust,eligibility=eligibility,implementation_watch=watch).to_dict()
    subject=next(x for x in records if x.canonical_project_id==project_id); benchmark=PeerBenchmarkService(records).benchmark(subject,BenchmarkMode.SYNTHETIC_SANDBOX).model_dump(mode="json")
    original=float(latest["original_cost"]); current=float(latest["current_cost"]); state={"as_of_month":latest["reporting_month"],"original_cost":original,"current_cost":current,"cost_escalation_pct":round(100*(current-original)/original,3),"cumulative_expenditure":float(latest["cumulative_expenditure"]),"physical_progress":float(latest["actual_physical_progress"]) if latest["actual_physical_progress"] else None,"approval_date":latest["approval_date"],"original_completion_date":latest["original_completion_date"],"current_approved_completion_date":latest["revised_completion_date"],"project_status":"SYNTHETIC_ACTIVE","availability":{"source_backed":False,"synthetic_fixture":True}}
    evidence=[{"data_origin":"SYNTHETIC_CUF_PROTOTYPE","source_id":latest["source_ref"] or None,"reporting_month":latest["reporting_month"],"sha256":None,"page":None,"table":"SYNTHETIC_CUF_FIXTURE","signal_codes":watch["reason_codes"]}]
    identity={"canonical_project_id":project_id,"project_name":project["project_name"],"sector":project["sector"],"ministry":project["ministry"],"agency":project["agency"],"location":project["location"],"project_status":"SYNTHETIC_ACTIVE","as_of_month":latest["reporting_month"],"scenario_id":project["scenario_id"],"agency_is_contractor":False}
    trust_view={"data_status":"USABLE" if usable else "NOT_USABLE","source":trust.source.code,"history":trust.history.code,"summary_state":"PASS" if usable else "FAIL","reasons":trust.data_reason_codes,"synthetic_evidence_only":True}
    return build_project_intelligence(mode=IntelligenceMode.SYNTHETIC_SANDBOX,identity=identity,current_state=state,watch=watch,trust=trust_view,benchmark=benchmark,officer_decision=decision,evidence=evidence,provenance={"data_origin":"SYNTHETIC_CUF_PROTOTYPE","scenario_id":project["scenario_id"],"dataset_version":latest["synthetic_dataset_version"],"official_evidence":False},previous_watch=previous)


def list_sandbox_projects(page=1,page_size=25,status=None):
    repo,watches,_=_sandbox_bundle(); rows=[]
    for project in repo.list_projects():
        watch=watches[project["canonical_project_id"]][0]
        if status and watch["status"]!=status: continue
        rows.append({"canonical_project_id":project["canonical_project_id"],"project_name":project["project_name"],"scenario_id":project["scenario_id"],"implementation_watch_status":watch["status"],"data_origin":"SYNTHETIC_CUF_PROTOTYPE","curated_fixture":project["curated_fixture"]=="TRUE"})
    start=(page-1)*page_size
    return {"mode":"SYNTHETIC_SANDBOX","data_origin":"SYNTHETIC_CUF_PROTOTYPE","items":rows[start:start+page_size],"page":page,"page_size":page_size,"total":len(rows),"pages":math.ceil(len(rows)/page_size) if rows else 0}


def intelligence_dashboard_summary(db, mode: str):
    from collections import Counter
    if mode=="SYNTHETIC_SANDBOX":
        repo,watches,_=_sandbox_bundle();projects=repo.list_projects();watch_counts=Counter(watches[x["canonical_project_id"]][0]["status"] for x in projects)
        return {"mode":mode,"data_origin":"SYNTHETIC_CUF_PROTOTYPE","total_projects":len(projects),"projects_reviewed":0,"officer_decisions":{"REVIEW_RECOMMENDED":sum(v for k,v in watch_counts.items() if k in {"WATCH","ELEVATED"}),"DATA_VERIFICATION_REQUIRED":watch_counts.get("DATA_INSUFFICIENT",0)},"implementation_watch":dict(watch_counts),"predictions_withheld":len(projects),"data_trust":{"FAIL_OR_WARNING":watch_counts.get("DATA_INSUFFICIENT",0)},"recent_alerts":0,"synthetic_portfolio":True}
    if mode!="REAL_HISTORICAL":raise ValueError("unsupported intelligence mode")
    from .decision_service import review_queue
    from .models import Alert
    queue=review_queue(db,page=1,page_size=100000);items=queue["items"]
    return {"mode":mode,"data_origin":"HISTORICAL_FLASH_REPORT","total_projects":db.scalar(select(func.count()).select_from(Project)) or 0,"projects_reviewed":0,"officer_decisions":dict(Counter(x["review_state"] for x in items)),"implementation_watch":dict(Counter(x["implementation_watch"]["status"] for x in items)),"predictions_withheld":sum(x["prediction_status"]=="WITHHELD" for x in items),"data_trust":dict(Counter(x["data_trust"]["data_status"] for x in items)),"recent_alerts":db.scalar(select(func.count()).select_from(Alert)) or 0,"synthetic_portfolio":False}
