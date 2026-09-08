from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any
from llm.schemas.evidence import PrahariEvidence
from .contracts import DocumentChunk,RagResponse

@dataclass(frozen=True)
class RagValidation:
    valid:bool;response:RagResponse|None;errors:tuple[str,...]

def validate_rag_response(payload:Any,chunks:list[DocumentChunk],project:PrahariEvidence|None)->RagValidation:
    try:response=RagResponse.from_dict(payload)
    except (ValueError,TypeError) as exc:return RagValidation(False,None,(f"schema: {exc}",))
    errors=[]; supplied={(c.document_id,c.title,c.page_start,c.chunk_id,c.source_hash) for c in chunks}
    cited={(c.document_id,c.title,c.page,c.chunk_id,c.source_hash) for c in response.citations}
    if not cited.issubset(supplied):errors.append("citation not supplied or not approved")
    if response.document_evidence_points and not cited:errors.append("document claims lack citations")
    text=" ".join([response.answer,*response.project_evidence_points,*response.document_evidence_points,*response.limitations]).lower()
    if re.search(r"\b(is corrupt|committed fraud|is negligent|guilty of|to blame|caused by|responsible for)\b",text):errors.append("unsupported causal or misconduct claim")
    if project:
        if project.calibrated_probability is None and re.search(r"\b\d+(?:\.\d+)?\s*%",text):errors.append("probability invented while null")
        if project.prediction_status in {"ABSTAIN","WITHHELD"} and not any(x in text for x in ("abstain","withheld","unavailable","not available")):errors.append("abstention not preserved")
        if project.risk_band and any(f"risk is {x.lower()}" in text for x in {"LOW","MEDIUM","HIGH"}-{project.risk_band}):errors.append("project risk overridden")
    return RagValidation(not errors,response if not errors else None,tuple(dict.fromkeys(errors)))

def validate_citations(response:RagResponse,chunks:list[DocumentChunk])->bool:
    return validate_rag_response(response.to_dict(),chunks,None).valid
