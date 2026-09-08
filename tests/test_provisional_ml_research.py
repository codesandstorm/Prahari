import copy
import csv
import math
from pathlib import Path

from src.ml.provisional_research import (
    abstention_reason, build_s1_cohort, evidence_object, has_ever_been_revised,
    month_date, normalize_agency,
)


def row(project, month, original="12/2026", revised="", progress="10", expenditure="10"):
    return {"canonical_project_id": project, "reporting_month": month,
            "original_target_doc_raw": original, "revised_doc_raw": revised,
            "approval_date_raw": "01/2024", "original_cost_raw": "100",
            "cumulative_expenditure_raw": expenditure, "physical_progress_raw": progress}


def test_month_date_accepts_month_and_full_dates():
    assert month_date("9/2027").year == 2027
    assert month_date("31/12/2027").day == 31
    assert month_date("N.A.") is None


def test_target_fails_closed_across_source_gap():
    rows = [row("P1", f"2025-0{month}") for month in range(1, 6)]
    coverage = {f"2025-0{month}": "PROJECT_LEVEL" for month in range(1, 6)}
    coverage["2025-03"] = "MISSING_SOURCE"
    assert not build_s1_cohort(rows, coverage, 3)


def test_disappearance_is_not_a_negative_label():
    rows = [row("P1", "2025-01"), row("P1", "2025-02"), row("P1", "2025-04")]
    coverage = {f"2025-0{month}": "PROJECT_LEVEL" for month in range(1, 5)}
    assert not build_s1_cohort(rows, coverage, 2)


def test_features_use_only_information_available_at_anchor():
    rows = [row("P1", "2025-01"), row("P1", "2025-02"), row("P1", "2025-03"), row("P1", "2025-04")]
    coverage = {f"2025-0{month}": "PROJECT_LEVEL" for month in range(1, 5)}
    before = build_s1_cohort(rows, coverage, 2)[0]
    changed = copy.deepcopy(rows); changed[-1]["physical_progress_raw"] = "99"
    after = build_s1_cohort(changed, coverage, 2)[0]
    for key in before:
        if key != "event":
            assert before[key] == after[key] or (isinstance(before[key], float) and math.isnan(before[key]) and math.isnan(after[key]))


def test_prior_revision_excludes_s1_anchor_even_if_later_missing():
    history = [row("P1", "2025-01", revised="01/2027"), row("P1", "2025-02", revised="")]
    assert has_ever_been_revised(history)


def test_agency_normalization_is_conservative():
    assert normalize_agency("NHAI")["agency_entity_id"] == "AG-NHAI"
    assert normalize_agency("Unresearched Builder Ltd")["agency_normalization_quality"] == "UNRESOLVED"


def test_abstention_withholds_probability():
    reason = abstention_reason(history_months=1, critical_missing=False, source_gap=True,
                               identity_resolved=True, subgroup_supported=True)
    result = evidence_object("P1", "2026-01", .8, "HIGH", reason)
    assert result["calibrated_probability"] is None
    assert result["reliability_band"] == "ABSTAIN"


def test_evidence_contract_has_no_llm_or_misconduct_output():
    result = evidence_object("P1", "2026-01", .2, "LOW")
    forbidden = {"llm_probability", "fraud_score", "corruption_score", "cause"}
    assert forbidden.isdisjoint(result)


def test_feature_registry_has_frozen_contract_columns():
    path = Path(__file__).resolve().parents[1] / "data/metadata/prahari_feature_registry.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        headers = set(next(csv.reader(handle)))
    assert {"feature_id", "known_at_prediction_t", "leakage_status", "model_A", "model_B", "model_C", "evidence_status"} <= headers
