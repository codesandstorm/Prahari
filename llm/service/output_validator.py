"""Fail-closed schema, grounding and safety checks for generated explanations."""
from __future__ import annotations

import json, re
from dataclasses import dataclass
from typing import Any

from llm.schemas.evidence import PrahariEvidence
from llm.schemas.response import PrahariResponse

@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    response: PrahariResponse | None
    errors: tuple[str, ...]

ACCUSATIONS=(r"\bis corrupt\b",r"\bcommitted fraud\b",r"\bis negligent\b",r"\bguilty of\b",r"\bmisconduct by\b")
CAUSES=(r"\bcaused by\b",r"\bdue to\b",r"\bresponsible for\b",r"\bto blame\b")

def _text(response:PrahariResponse)->str:
    return " ".join([response.summary,*response.evidence_points,response.reliability_explanation,
                     *response.recommended_review_areas,*response.limitations,*response.source_references])

def _provenance_tokens(evidence:PrahariEvidence)->set[str]:
    return {str(v).strip().lower() for item in evidence.source_provenance for v in item.values()
            if isinstance(v,(str,int,float)) and str(v).strip()}

def validate_output(payload:Any,evidence:PrahariEvidence)->ValidationResult:
    errors=[]
    try: response=PrahariResponse.from_dict(payload)
    except (TypeError,ValueError) as exc: return ValidationResult(False,None,(f"schema: {exc}",))
    text=_text(response); lower=text.lower()
    for pattern in ACCUSATIONS:
        if re.search(pattern,lower): errors.append("unsupported misconduct accusation")
    if evidence.cause is None:
        for pattern in CAUSES:
            if re.search(pattern,lower): errors.append("unsupported causal claim"); break
    if evidence.calibrated_probability is None:
        if re.search(r"\b\d+(?:\.\d+)?\s*%",text): errors.append("probability invented while null")
        if evidence.prediction_status in {"ABSTAIN","WITHHELD"} and not any(x in lower for x in ("withheld","abstain","unavailable","not available")):
            errors.append("abstention not respected")
    if evidence.contractor is None and evidence.agency and evidence.agency.lower() in lower and "contractor" in lower:
        errors.append("agency converted to contractor")
    allowed_sources=_provenance_tokens(evidence)
    identifying_sources={token for token in allowed_sources if len(token)>=3 and not token.replace(".","",1).isdigit()}
    numeric_sources={token for token in allowed_sources if token.replace(".","",1).isdigit()}
    no_source="no source reference is available in this evidence object."
    for source in response.source_references:
        normalized=source.strip().lower()
        supported=(normalized in allowed_sources or any(token in normalized for token in identifying_sources)
                   or any(normalized==f"page {token}" for token in numeric_sources))
        if normalized!=no_source and not supported:
            errors.append("invented source reference")
    if evidence.reliability_band.lower() not in response.reliability_explanation.lower():
        errors.append("reliability band omitted")
    return ValidationResult(not errors,response if not errors else None,tuple(dict.fromkeys(errors)))
