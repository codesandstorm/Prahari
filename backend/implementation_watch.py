"""Backend adapter for deterministic Implementation Watch V1."""
from __future__ import annotations

import math

from src.implementation_watch import CufProjectSnapshot, ImplementationWatchEngine
from src.implementation_watch.contracts import Availability
from src.ml.final_prediction import build_compact_v2
from .models import SourceReport


def _history_rows(snapshots):
    rows=[]
    for item in snapshots:
        row=dict(item.raw_features or {})
        row.update(canonical_project_id=item.canonical_project_id,reporting_month=item.reporting_month.strftime('%Y-%m'))
        rows.append(row)
    return rows


def database_implementation_watch(repo, project, trust_result, history_override=None, source_override=None):
    history=history_override if history_override is not None else repo.history(project.canonical_project_id);latest=history[-1] if history else None
    if latest is None:
        snapshot=CufProjectSnapshot(canonical_project_id=project.canonical_project_id,as_of=__import__('datetime').date.today(),data_origin='HISTORICAL_FLASH_REPORT',source_availability=Availability.SOURCE_GAP,report_month_missing=True,provenance_complete=False)
        return ImplementationWatchEngine().evaluate(snapshot,data_trust=trust_result)
    rows=_history_rows(history);features={}
    try:features=build_compact_v2(rows)
    except (ValueError,KeyError,AssertionError):pass
    source=source_override if source_override is not None else repo.db.get(SourceReport,latest.reporting_month)
    source_ref=source.source_id if source else None
    progress_history=[]
    for item in history:
        availability=Availability.AVAILABLE if item.progress_current is not None else Availability.UNREPORTED
        progress_history.append((item.reporting_month.strftime('%Y-%m'),item.progress_current,availability))
    finite=lambda value: value is not None and isinstance(value,(int,float)) and math.isfinite(value)
    snapshot=CufProjectSnapshot(
        canonical_project_id=project.canonical_project_id,
        as_of=latest.reporting_month,
        data_origin='HISTORICAL_FLASH_REPORT',
        source_refs=[source_ref] if source_ref else [],
        source_availability=Availability.AVAILABLE if trust_result.source.status=='PASS' else Availability.UNKNOWN,
        provenance_complete=trust_result.provenance.status=='PASS',
        actual_physical_progress=latest.progress_current,
        remaining_schedule_months=features.get('remaining_schedule_months') if finite(features.get('remaining_schedule_months')) else None,
        required_future_velocity=features.get('required_future_velocity') if finite(features.get('required_future_velocity')) else None,
        progress_vs_elapsed_gap=features.get('progress_vs_elapsed_gap') if finite(features.get('progress_vs_elapsed_gap')) else None,
        low_progress_near_deadline=bool(features.get('low_progress_near_deadline')) if finite(features.get('low_progress_near_deadline')) else None,
    )
    return ImplementationWatchEngine().evaluate(snapshot,progress_history=progress_history,data_trust=trust_result)
