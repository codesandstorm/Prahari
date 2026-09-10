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


class FrozenModelPredictionProvider:
    """Thin adapter over the canonical ML service; database writes stay separate."""
    def __init__(self, repository_root):
        from src.ml.prediction_service import FrozenPredictionService
        self.service = FrozenPredictionService(repository_root)

    def predict(self, history, as_of_month: str, target: str):
        return self.service.predict_dict(history, as_of_month, target)
