"""Database adapter for the canonical model-independent Data Trust evaluator."""
from __future__ import annotations
from src.trust.data_trust import DataTrustEvaluator,frontend_view
from src.decision.governance import ModelReleaseStatus,assess_prediction_eligibility
from src.ml.final_prediction import _completed

def database_trust(db,repo,project,as_of_month=None):
    history=repo.history(project.canonical_project_id)
    sources={s.source_id:s for s in repo.all_sources()}
    coverage={s.reporting_month.strftime('%Y-%m'):s.coverage_class for s in sources.values()}
    manifest={sid:{'sha256':s.sha256} for sid,s in sources.items()}
    rows=[]
    for snap in history:
        source=next((s for s in sources.values() if s.reporting_month==snap.reporting_month),None)
        raw=dict(snap.raw_features or {})
        rows.append({**raw,'canonical_project_id':project.canonical_project_id,'reporting_month':snap.reporting_month.strftime('%Y-%m'),'identity_status':project.identity_status,'identity_method':project.identity_method,'source_id':source.source_id if source else '','source_sha256':source.sha256 if source else '','schema_family':source.schema_family if source else '','reported_physical_progress':snap.progress_current,'reported_cumulative_expenditure':snap.expenditure_current})
    requested=as_of_month or (rows[-1]['reporting_month'] if rows else '')
    result=DataTrustEvaluator(coverage,manifest).evaluate(rows,requested)
    release=ModelReleaseStatus()
    eligibility=assess_prediction_eligibility(result,release,project_completed=bool(rows and _completed(rows[-1])))
    return result,result.to_dict(),frontend_view(result),release,eligibility

def guard_prediction_output(prediction,eligibility):
    if prediction is None or eligibility.prediction_eligible:return prediction
    guarded=dict(prediction);guarded.update({'prediction_status':'WITHHELD','probability':None,'risk_band':None,'reliability_band':'ABSTAIN','reliability_reasons':list(eligibility.reason_codes),'review_priority':None,'contributors':[],'abstention_reason':';'.join(eligibility.reason_codes)})
    return guarded
