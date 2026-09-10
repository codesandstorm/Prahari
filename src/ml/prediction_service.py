"""Frozen prediction artifact loader and fail-closed inference service."""
from __future__ import annotations
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib, numpy as np

from src.ml.final_prediction import COMPACT_V2, EXACT_IDENTITY, FEATURE_VERSION, TARGET_VERSION, _completed, _deteriorated, build_compact_v2, reliability

@dataclass(frozen=True)
class PredictionResult:
    canonical_project_id: str
    as_of_month: str
    target: str
    horizon_months: int
    prediction_status: str
    probability: float | None
    risk_band: str | None
    reliability_band: str
    reliability_reasons: list[str]
    data_quality_status: str
    review_priority: str | None
    model_version: str
    feature_version: str
    target_version: str
    contributors: list[dict[str, Any]]
    abstention_reason: str | None
    created_at: str

class FrozenPredictionService:
    """Loads versioned artifacts; current V1 fails closed on probability display."""
    def __init__(self, root: Path):
        self.root=Path(root); self.artifacts={}
        for target in ('S1','S2'):
            path=self.root/'models/prediction'/target.lower()/'v1'/'pipeline.joblib'
            if path.exists(): self.artifacts[target]=joblib.load(path)

    def predict(self, history: list[dict[str,str]], as_of_month: str, target: str) -> PredictionResult:
        rows=sorted((r for r in history if r['reporting_month']<=as_of_month),key=lambda r:r['reporting_month'])
        anchor=next((r for r in reversed(rows) if r['reporting_month']==as_of_month),None)
        reasons=[]
        if target not in ('S1','S2'): raise ValueError('target must be S1 or S2')
        if anchor is None: reasons.append('ANCHOR_OBSERVATION_UNAVAILABLE')
        elif anchor.get('identity_status')!=EXACT_IDENTITY: reasons.append('IDENTITY_NOT_EXACT')
        elif _completed(anchor): reasons.append('COMPLETED_AT_T')
        elif target=='S1' and any(_deteriorated(r) for r in rows): reasons.append('NOT_S1_ELIGIBLE')
        elif target=='S2' and not _deteriorated(anchor): reasons.append('NOT_S2_ELIGIBLE')
        if target not in self.artifacts: reasons.append('MODEL_ARTIFACT_UNAVAILABLE')
        features=build_compact_v2(rows) if anchor else {n:math.nan for n in COMPACT_V2}
        band,rel=reliability(features,anchor.get('identity_status','') if anchor else '',anchor is not None,False)
        reasons.extend(rel)
        # Machine labels have not been human-adjudicated and calibration has no
        # untouched confirmation period. Scores are therefore deliberately hidden.
        reasons.append('HUMAN_TARGET_ADJUDICATION_PENDING')
        reasons=list(dict.fromkeys(reasons))
        return PredictionResult(
            canonical_project_id=anchor.get('canonical_project_id','') if anchor else '',as_of_month=as_of_month,target=target,horizon_months=3,
            prediction_status='WITHHELD',probability=None,risk_band=None,reliability_band='ABSTAIN',reliability_reasons=reasons,
            data_quality_status='REVIEW',review_priority=None,model_version=f'{target.lower()}-histgb-v1-research',feature_version=FEATURE_VERSION,
            target_version=TARGET_VERSION[target],contributors=[],abstention_reason=';'.join(reasons),created_at=datetime.now(timezone.utc).isoformat())

    def predict_dict(self,*args,**kwargs): return asdict(self.predict(*args,**kwargs))
