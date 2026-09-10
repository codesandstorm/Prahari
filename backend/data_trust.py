"""Database adapter for the canonical model-independent Data Trust evaluator."""
from __future__ import annotations
from src.trust.data_trust import DataTrustEvaluator,frontend_view

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
    result=DataTrustEvaluator(coverage,manifest,human_validation_complete=False,calibration_confirmed=False).evaluate(rows,requested)
    return result.to_dict(),frontend_view(result)
