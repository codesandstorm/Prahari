"""Read-only repository for the physically isolated synthetic sandbox."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from src.implementation_watch.contracts import Availability, Clearance, CufProjectSnapshot, LandStatus, Milestone, RowStatus, Tender
from .generator import DATA_ORIGIN, OUTPUT


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle))


def _bool(value: str | None) -> bool | None:
    if value in (None, ""): return None
    return value.upper() == "TRUE"


def _float(value: str | None) -> float | None:
    return None if value in (None, "") else float(value)


def _date(value: str | None) -> date | None:
    return None if value in (None, "") else date.fromisoformat(value)


class SyntheticSandboxRepository:
    def __init__(self, root: Path = OUTPUT):
        if "data/synthetic" not in root.as_posix().lower(): raise ValueError("synthetic repository must remain under data/synthetic")
        self.root=root; self.projects=_rows(root/"project_master.csv"); self.months=_rows(root/"project_month.csv")
        self._tables={name:_rows(root/f"{name}.csv") for name in ("milestones","land","row","clearances","tenders","funding")}
        if any(r.get("data_origin") != DATA_ORIGIN for r in self.projects+self.months): raise ValueError("synthetic origin marker missing or mixed")

    def list_projects(self, curated_only=False) -> list[dict[str,str]]:
        return [r for r in self.projects if not curated_only or r["curated_fixture"]=="TRUE"]

    def project(self, project_id: str) -> dict[str,str] | None:
        return next((r for r in self.projects if r["canonical_project_id"]==project_id),None)

    def history(self, project_id: str) -> list[dict[str,str]]:
        return sorted((r for r in self.months if r["canonical_project_id"]==project_id),key=lambda r:r["reporting_month"])

    def snapshot(self, project_id: str, month: str | None = None) -> CufProjectSnapshot:
        history=self.history(project_id)
        if not history: raise LookupError(project_id)
        row=next((r for r in history if r["reporting_month"]==month),None) if month else history[-1]
        if row is None: raise LookupError(f"{project_id}:{month}")
        key=lambda name:[x for x in self._tables[name] if x["canonical_project_id"]==project_id and x["reporting_month"]==row["reporting_month"]]
        ms=[Milestone(label=x["label"],family=x["family"],applicable=_bool(x["applicable"]),planned_date=_date(x["planned_date"]),actual_date=_date(x["actual_date"])) for x in key("milestones")]
        land_row=next(iter(key("land")),None); land=LandStatus(applicable=_bool(land_row["applicable"]),required=_float(land_row["required"]),acquired=_float(land_row["acquired"]),remaining_pct=_float(land_row["remaining_pct"]),acquisition_complete=_bool(land_row["acquisition_complete"]),expected_completion_date=_date(land_row["expected_completion_date"])) if land_row else None
        row_row=next(iter(key("row")),None); right_of_way=RowStatus(applicable=_bool(row_row["applicable"]),pending=_bool(row_row["pending"]),availability_pct=_float(row_row["availability_pct"])) if row_row else None
        clearance=[Clearance(category=x["category"],applicable=_bool(x["applicable"]),status=x["status"],due_date=_date(x["due_date"])) for x in key("clearances")]
        tender=[Tender(tender_id=x["tender_id"],applicable=_bool(x["applicable"]),publish_date=_date(x["publish_date"]),award_date=_date(x["award_date"]),expected_award_date=_date(x["expected_award_date"])) for x in key("tenders")]
        return CufProjectSnapshot(canonical_project_id=project_id,as_of=date.fromisoformat(row["reporting_month"]+"-01"),data_origin=DATA_ORIGIN,source_refs=[x for x in row["source_ref"].split("|") if x],source_availability=Availability(row["source_availability"]),provenance_complete=_bool(row["provenance_complete"]),report_stale=_bool(row["report_stale"]),report_month_missing=row["source_availability"]=="SOURCE_GAP",scheduled_physical_progress=_float(row["scheduled_physical_progress"]),actual_physical_progress=_float(row["actual_physical_progress"]),scheduled_financial_progress=_float(row["scheduled_financial_progress"]),actual_financial_progress=_float(row["actual_financial_progress"]),financial_progress_semantics_compatible=True,remaining_schedule_months=_float(row["remaining_schedule_months"]),required_future_velocity=_float(row["required_future_velocity"]),milestones=ms,land=land,right_of_way=right_of_way,clearances=clearance,tenders=tender,has_active_tenders=any(x.award_date is None for x in tender) if tender else False)
