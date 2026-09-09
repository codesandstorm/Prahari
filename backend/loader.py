from __future__ import annotations
import csv, hashlib, json, logging, math, uuid
from datetime import date, datetime, timezone
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import IngestionRun, Project, ProjectSnapshot, SourceReport

LOG = logging.getLogger("prahari.loader")
VALID_COVERAGE = {"PROJECT_LEVEL", "AGGREGATE_ONLY", "MISSING_SOURCE"}


class DataValidationError(ValueError): pass


def _rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def _none(value):
    return None if value is None or value.strip() in {"", "-", "NA", "N/A", "nan"} else value.strip()


def _number(value, kind=float):
    value = _none(value)
    if value is None: return None
    try: result = kind(float(value))
    except ValueError as exc: raise DataValidationError(f"invalid numeric value: {value}") from exc
    if isinstance(result, float) and not math.isfinite(result): raise DataValidationError(f"non-finite numeric value: {value}")
    return result


def _reported_number(value):
    """Parse a source-reported numeric cell without imputing missing values."""
    value = _none(value)
    if value is None: return None
    return _number(value.replace(",", "").replace("%", "").strip(), float)


def _month(value: str) -> date:
    try: return date.fromisoformat(value[:7] + "-01")
    except (TypeError, ValueError) as exc: raise DataValidationError(f"invalid reporting month: {value}") from exc


def dataset_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


def load_canonical_dataset(db: Session, data_dir: Path, manifest_path: Path | None = None) -> dict:
    master, months, reports = data_dir / "project_master.csv", data_dir / "project_month.csv", data_dir / "report_month.csv"
    paths = [master, months, reports]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing: raise DataValidationError(f"missing approved input(s): {missing}")
    fingerprint = dataset_hash(paths)
    prior = db.scalar(select(IngestionRun).where(IngestionRun.dataset_hash == fingerprint, IngestionRun.status == "COMPLETED"))
    if prior: return {"status": "ALREADY_LOADED", "run_id": prior.run_id, "projects": prior.projects_loaded, "snapshots": prior.snapshots_loaded, "dataset_hash": fingerprint}
    run_id = f"ING-{uuid.uuid4().hex[:16]}"
    project_rows, month_rows, report_rows = list(_rows(master)), list(_rows(months)), list(_rows(reports))
    project_ids = [r.get("canonical_project_id", "").strip() for r in project_rows]
    if any(not x for x in project_ids) or len(project_ids) != len(set(project_ids)): raise DataValidationError("project master has missing or duplicate canonical_project_id")
    report_keys = {_month(r.get("reporting_month", "")) for r in report_rows}
    coverage_by_month = {_month(r.get("reporting_month", "")): r.get("coverage_class") for r in report_rows}
    coverage = {r.get("coverage_class") for r in report_rows}
    if not coverage <= VALID_COVERAGE: raise DataValidationError(f"unsupported coverage class: {coverage - VALID_COVERAGE}")
    snapshot_keys = [(r.get("canonical_project_id", "").strip(), _month(r.get("reporting_month", ""))) for r in month_rows]
    if len(snapshot_keys) != len(set(snapshot_keys)): raise DataValidationError("duplicate canonical project-month key")
    for pid, month in snapshot_keys:
        if pid not in set(project_ids): raise DataValidationError(f"snapshot references unknown project: {pid}")
        if month not in report_keys: raise DataValidationError(f"snapshot month absent from report calendar: {month}")
        if coverage_by_month[month] != "PROJECT_LEVEL": raise DataValidationError(f"project snapshot exists for unavailable project-level month: {month}")
    for row in month_rows:
        progress = _reported_number(row.get("reported_physical_progress"))
        if progress is not None and not 0 <= progress <= 100: raise DataValidationError(f"progress_current outside [0,100]: {progress}")
    hashes = {}
    if manifest_path and manifest_path.is_file():
        for row in _rows(manifest_path): hashes[row.get("source_id")] = _none(row.get("sha256"))
    db.rollback()  # close the validation/read transaction before the atomic write
    with db.begin():
        run = IngestionRun(run_id=run_id, dataset_hash=fingerprint, status="RUNNING")
        db.add(run)
        for row in report_rows:
            month = _month(row["reporting_month"]); item = db.get(SourceReport, month) or SourceReport(reporting_month=month)
            item.source_id=_none(row.get("source_id")); item.coverage_class=row["coverage_class"]; item.source_present=row.get("source_present", "").upper()=="TRUE"
            item.project_level_usable=row.get("project_level_usable", "").upper()=="TRUE"; item.official_project_count=_number(row.get("official_project_count"), int)
            item.schema_family=_none(row.get("schema_family")); item.source_quality_status=_none(row.get("source_quality_status")); item.sha256=hashes.get(item.source_id)
            db.add(item)
        for row in project_rows:
            pid=row["canonical_project_id"].strip(); item=db.get(Project,pid) or Project(canonical_project_id=pid)
            for target, source in (("project_code","project_code"),("canonical_name","canonical_name"),("agency","agency"),("ministry","ministry"),("sector","sector"),("state","state"),("identity_method","identity_method"),("identity_status","identity_status")):
                setattr(item,target,_none(row.get(source)) or ("UNKNOWN" if target in {"canonical_name","identity_method","identity_status"} else None))
            db.add(item)
        db.flush()
        for row in month_rows:
            pid, month=row["canonical_project_id"].strip(),_month(row["reporting_month"])
            item=db.scalar(select(ProjectSnapshot).where(ProjectSnapshot.canonical_project_id==pid,ProjectSnapshot.reporting_month==month)) or ProjectSnapshot(canonical_project_id=pid,reporting_month=month)
            # Only contemporaneous source-reported state enters operations.
            item.project_observation_count=None;item.months_since_first_observation=None
            item.progress_current=_reported_number(row.get("reported_physical_progress"));item.progress_velocity=None
            item.expenditure_current=_reported_number(row.get("reported_cumulative_expenditure"));item.expenditure_velocity=None;item.cost_ratio=None
            item.agency=_none(row.get("reported_agency"));item.state=_none(row.get("reported_state"));item.sector=_none(row.get("sector_raw"));item.raw_features={}
            db.add(item)
        run.status="COMPLETED";run.projects_loaded=len(project_rows);run.snapshots_loaded=len(month_rows);run.completed_at=datetime.now(timezone.utc)
    LOG.info("canonical_dataset_loaded run_id=%s projects=%d snapshots=%d",run_id,len(project_rows),len(month_rows))
    return {"status":"LOADED","run_id":run_id,"projects":len(project_rows),"snapshots":len(month_rows),"dataset_hash":fingerprint}
