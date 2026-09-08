import pytest

from llm.schemas import BenchmarkCase, PrahariEvidence, PrahariResponse


def valid_evidence(**updates):
    data = {"canonical_project_id":"P1","project_name":None,"as_of_month":"2026-06","target":"S1","horizon_months":3,
            "prediction_status":"AVAILABLE","calibrated_probability":.7,"risk_band":"HIGH","reliability_band":"LOW"}
    data.update(updates); return data


def test_evidence_accepts_null_probability_when_withheld():
    result = PrahariEvidence.from_dict(valid_evidence(prediction_status="WITHHELD", calibrated_probability=None, risk_band=None, abstention_reason="INSUFFICIENT_HISTORY"))
    assert result.calibrated_probability is None


def test_evidence_rejects_probability_on_abstention():
    with pytest.raises(ValueError, match="requires null"):
        PrahariEvidence.from_dict(valid_evidence(prediction_status="ABSTAIN"))


def test_evidence_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown"):
        PrahariEvidence.from_dict({**valid_evidence(), "invented": 1})


def test_response_schema_is_strict():
    data = {"summary":"Review required","evidence_points":[],"reliability_explanation":"Low reliability is distinct from risk.","recommended_review_areas":[],"limitations":[],"source_references":[],"unsupported_question":False}
    assert PrahariResponse.from_dict(data).summary == "Review required"
    with pytest.raises(ValueError): PrahariResponse.from_dict({**data, "extra":"no"})
