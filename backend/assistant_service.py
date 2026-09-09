from __future__ import annotations
from dataclasses import asdict
from datetime import date
from sqlalchemy.orm import Session
from llm.rag.assistant import UnifiedPrahariAssistant
from .repository import ProjectRepository, prediction_dict


def build_authoritative_evidence(db: Session, project_id: str) -> dict:
    repo=ProjectRepository(db); project=repo.get(project_id)
    if project is None: raise LookupError(project_id)
    snapshot=repo.latest_snapshot(project_id); prediction=repo.latest_prediction(project_id)
    provenance=[]
    if snapshot:
        source=db.get(__import__("backend.models",fromlist=["SourceReport"]).SourceReport,snapshot.reporting_month)
        if source: provenance=[{"source_id":source.source_id,"reporting_month":source.reporting_month.strftime("%Y-%m"),"sha256":source.sha256,"coverage_class":source.coverage_class}]
    if prediction:
        p=prediction_dict(repo,prediction)
        contributors=[x["feature_name"] for x in p.pop("contributors")]
        return {"canonical_project_id":project_id,"project_name":project.canonical_name,"as_of_month":prediction.as_of_month.strftime("%Y-%m"),"target":prediction.target,"horizon_months":prediction.horizon_months,"prediction_status":prediction.prediction_status,"calibrated_probability":prediction.probability,"risk_band":prediction.risk_band,"reliability_band":prediction.reliability_band,"reliability_reasons":prediction.reliability_reasons,"data_quality_status":prediction.data_quality_status,"review_priority":prediction.review_priority,"contributors":contributors,"source_provenance":provenance,"model_version":prediction.model_version,"feature_version":prediction.feature_version,"target_version":prediction.target_version,"abstention_reason":prediction.abstention_reason,"agency":project.agency}
    return {"canonical_project_id":project_id,"project_name":project.canonical_name,"as_of_month":snapshot.reporting_month.strftime("%Y-%m") if snapshot else date.today().strftime("%Y-%m"),"target":"S1","horizon_months":3,"prediction_status":"WITHHELD","calibrated_probability":None,"risk_band":None,"reliability_band":"ABSTAIN","reliability_reasons":["No approved versioned prediction is loaded"],"data_quality_status":"UNKNOWN","review_priority":None,"contributors":[],"source_provenance":provenance,"model_version":"UNAVAILABLE","feature_version":"Compact-V2-contract","target_version":"S1-v0.1-provisional","abstention_reason":"No scientifically approved prediction artifact is available","agency":project.agency}


class AssistantAdapter:
    def __init__(self, assistant: UnifiedPrahariAssistant): self.assistant=assistant
    def answer(self, db: Session, request_id: str, question: str, project_id: str | None):
        evidence=build_authoritative_evidence(db,project_id) if project_id else None
        return asdict(self.assistant.answer(question=question,project_evidence=evidence,request_id=request_id))
