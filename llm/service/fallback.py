"""Deterministic, model-free implementation of the frozen fallback contract."""
from __future__ import annotations

from llm.schemas.evidence import PrahariEvidence
from llm.schemas.response import PrahariResponse

def _source_labels(evidence: PrahariEvidence) -> list[str]:
    labels=[]
    for source in evidence.source_provenance:
        for key in ("source_id", "source", "document", "page", "raw_row_locator"):
            value=source.get(key)
            if value not in (None, ""):
                labels.append(str(value))
    return list(dict.fromkeys(labels))

def deterministic_fallback(evidence: PrahariEvidence, reason: str = "", officer_question: str = "") -> PrahariResponse:
    withheld=evidence.prediction_status in {"ABSTAIN", "WITHHELD"}
    if withheld:
        risk="Prediction withheld; no risk percentage or risk band is available."
    else:
        pct=f" ({evidence.calibrated_probability:.1%})" if evidence.calibrated_probability is not None else ""
        risk=f"Supplied project risk is {evidence.risk_band or 'unavailable'}{pct}."
    watch_points=[str(item.get("explanation")) for item in evidence.implementation_watch.get("signals",[]) if item.get("status","DETECTED")=="DETECTED" and item.get("explanation")]
    points=list(evidence.contributors) or watch_points or ["No validated contributors or implementation signals are available."]
    reliability=f"Reliability is {evidence.reliability_band}."
    if evidence.reliability_reasons:
        reliability += " " + " ".join(evidence.reliability_reasons)
    limitations=[]; question=officer_question.lower()
    land_supported=any(item.get("family")=="LAND" and item.get("status")=="DETECTED" for item in evidence.implementation_watch.get("signals",[]))
    unsupported=any(term in question for term in ("contractor","caused","cause","ministry","blame","corrupt","fraud","neglig")) or ("land acquisition" in question and not land_supported)
    if unsupported:
        limitations.append("The requested contractor, cause, blame or misconduct evidence is unavailable in the supplied evidence object.")
    if evidence.abstention_reason: limitations.append(evidence.abstention_reason)
    if reason: limitations.append("Generated explanation was unavailable or rejected; deterministic fallback used.")
    return PrahariResponse(
        summary=f"Project is flagged for {evidence.review_priority or 'administrative review'}. {risk}",
        evidence_points=points,
        reliability_explanation=reliability,
        recommended_review_areas=["Verify the current schedule, reported trajectory and available source evidence."],
        limitations=limitations,
        source_references=_source_labels(evidence) or ["No source reference is available in this evidence object."],
        unsupported_question=unsupported,
    )
