from __future__ import annotations
from typing import Protocol
from sqlalchemy.orm import Session
from .repository import ProjectRepository


class PredictionProvider(Protocol):
    def latest(self, db: Session, canonical_project_id: str): ...


class StoredPredictionProvider:
    """Reads auditable predictions loaded by a separately approved model pipeline."""
    def latest(self, db: Session, canonical_project_id: str):
        return ProjectRepository(db).latest_prediction(canonical_project_id)
