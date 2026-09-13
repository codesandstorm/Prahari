from __future__ import annotations
import math
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import Prediction, PredictionContributor, Project, ProjectSnapshot, SourceReport


class ProjectRepository:
    def __init__(self, db: Session): self.db = db

    def get(self, project_id: str):
        return self.db.get(Project, project_id)

    def latest_snapshot(self, project_id: str):
        return self.db.scalar(select(ProjectSnapshot).where(ProjectSnapshot.canonical_project_id == project_id).order_by(ProjectSnapshot.reporting_month.desc()).limit(1))

    def latest_prediction(self, project_id: str):
        return self.db.scalar(select(Prediction).where(Prediction.canonical_project_id == project_id).order_by(Prediction.as_of_month.desc(), Prediction.created_at.desc()).limit(1))

    def contributors(self, prediction_id: str):
        return list(self.db.scalars(select(PredictionContributor).where(PredictionContributor.prediction_id == prediction_id).order_by(PredictionContributor.rank)))

    def history(self, project_id: str):
        return list(self.db.scalars(select(ProjectSnapshot).where(ProjectSnapshot.canonical_project_id == project_id).order_by(ProjectSnapshot.reporting_month)))

    def unavailable_months(self):
        return list(self.db.scalars(select(SourceReport).where(SourceReport.coverage_class != "PROJECT_LEVEL").order_by(SourceReport.reporting_month)))

    def all_sources(self):
        return list(self.db.scalars(select(SourceReport).order_by(SourceReport.reporting_month)))

    def all_projects(self, data_origin="HISTORICAL_FLASH_REPORT"):
        q=select(Project)
        if data_origin:q=q.where(Project.data_origin==data_origin)
        return list(self.db.scalars(q.order_by(Project.canonical_project_id)))

    def list(self, page: int, page_size: int, search: str | None, sector: str | None, ministry: str | None, sort: str, order: str):
        q = select(Project).where(Project.data_origin=="HISTORICAL_FLASH_REPORT")
        if search: q = q.where(Project.canonical_name.ilike(f"%{search}%"))
        if sector: q = q.where(Project.sector == sector)
        if ministry: q = q.where(Project.ministry == ministry)
        total = self.db.scalar(select(func.count()).select_from(q.subquery())) or 0
        columns = {"canonical_project_id": Project.canonical_project_id, "name": Project.canonical_name, "agency": Project.agency, "sector": Project.sector}
        col = columns[sort]
        q = q.order_by(col.desc() if order == "desc" else col.asc()).offset((page - 1) * page_size).limit(page_size)
        return list(self.db.scalars(q)), total, math.ceil(total / page_size) if total else 0


def prediction_dict(repo: ProjectRepository, item: Prediction | None):
    if item is None: return None
    return {c.name: getattr(item, c.name) for c in item.__table__.columns} | {"contributors": [
        {"rank": c.rank, "feature_name": c.feature_name, "contribution": c.contribution, "direction": c.direction}
        for c in repo.contributors(item.prediction_id)
    ]}
