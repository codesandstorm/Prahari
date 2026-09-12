import math
import os
from pathlib import Path

import numpy as np
import pytest

from src.ml.prediction_research_v2 import (
    BASIC_LONG_HISTORY_V1, build_basic_long_history, cluster_bootstrap_indices,
    equal_soft_vote, expanding_folds, population_stability_index, rolling_folds, validate_transfer_rows,
)
from src.pipeline.build_mixed_coverage_dataset import _recover_ocms_footer_serial,discover_table,extract_project_month
from src.ml.temporal_experiment_v2 import equal_vote,probability_metrics,require_human_gate,validate_temporal_oof,weighted_vote


def row(month, expenditure="10"):
    return {"reporting_month":month,"original_cost_raw":"100","cumulative_expenditure_raw":expenditure,
            "approval_date_raw":"01/2020","original_target_doc_raw":"12/2025","revised_doc_raw":"",
            "reported_original_cost":"","reported_cumulative_expenditure":"","reported_approval_date":"",
            "reported_original_target_doc":"","reported_revised_doc":""}


def test_october_footer_recovery_is_narrow():
    assert _recover_ocms_footer_serial("F 5") == "5"
    assert _recover_ocms_footer_serial("166 F") == "166"
    assert _recover_ocms_footer_serial("42") == "42"
    assert _recover_ocms_footer_serial("F42") == "F42"
    assert _recover_ocms_footer_serial("TOTAL 42") == "TOTAL 42"


@pytest.mark.integration
def test_october_2022_actual_source_has_complete_row_accounting():
    raw=os.environ.get("PRAHARI_RAW_ROOT")
    if not raw: pytest.skip("PRAHARI_RAW_ROOT not configured")
    path=Path(raw)/"2022/FlashReport_2022_10.pdf"
    rows,summary=extract_project_month(path,"2022-10",discover_table(path))
    assert len(rows)==1521
    assert summary["ocms_footer_serials_recovered"]==99
    assert summary["missing_serials"]==[] and summary["duplicate_serials"]==0
    assert summary["unresolved_rows"]==[] and summary["row_accounting_valid"]


def test_basic_long_history_exact_contract_and_calendar_velocity():
    features=build_basic_long_history([row("2023-01","10"),row("2023-02","14")])
    assert tuple(features)==BASIC_LONG_HISTORY_V1
    assert features["expenditure_velocity"]==4
    assert features["history_span_months"]==2
    assert "physical_progress" not in features


def test_equal_soft_vote_and_validation():
    assert np.allclose(equal_soft_vote([[.2,.8],[.4,.6]]),[.3,.7])
    with pytest.raises(ValueError): equal_soft_vote([[1.2]])


def test_expanding_fold_uses_only_mature_training_outcomes():
    cohort=[]
    for month in ("2022-12","2023-01","2023-04"):
        cohort.append({"canonical_project_id":"P1","anchor_month":month,"event":1})
    f1=expanding_folds(cohort,3,minimums=(0,0,0))[0]
    assert f1["latest_train_anchor"]=="2022-12"


def test_cluster_bootstrap_keeps_project_rows_together():
    samples=cluster_bootstrap_indices(["A","A","B"],replicates=3,seed=1)
    for sample in samples:
        assert list(sample).count(0)==list(sample).count(1)


def test_drift_and_rolling_helpers_are_deterministic():
    assert population_stability_index([1,2,3,4],[1,2,3,4])==pytest.approx(0)
    cohort=[{"canonical_project_id":"P","anchor_month":"2022-12","event":0}]
    assert rolling_folds(cohort,3)[0]["analysis_role"]=="SECONDARY_SENSITIVITY_ONLY"


def test_transfer_validator_detects_tampering_and_partial_review():
    import hashlib
    evidence=["review_id","machine_label"]
    row={"review_id":"R1","machine_label":"1","reviewer":"","manual_label":"","confidence":"","evidence_verified":"",
         "source_page_verified":"","identity_verified":"","review_notes":"","review_timestamp":""}
    digest=hashlib.sha256("R1|1".encode()).hexdigest(); manifest={"evidence_fields":evidence,"evidence_hashes":{"R1":digest}}
    assert validate_transfer_rows([row],manifest)==[]
    row["machine_label"]="0"
    assert "EVIDENCE_TAMPERED" in validate_transfer_rows([row],manifest)[0]


def test_model_harness_is_fail_closed_until_human_transfer():
    with pytest.raises(RuntimeError): require_human_gate("PENDING")
    require_human_gate("HUMAN_TARGET_TRANSFER_PASSED")


def test_ensemble_requires_identical_rows_and_predeclared_weights():
    predictions={name:[{"row_key":"A","probability":p}] for name,p in
                 (("hist_gradient_boosting",.2),("random_forest",.4),("xgboost",.6))}
    assert equal_vote(predictions)[0]["probability"]==pytest.approx(.4)
    assert weighted_vote(predictions,(.34,.33,.33))[0]["probability"]==pytest.approx(.398)
    predictions["xgboost"][0]["row_key"]="B"
    with pytest.raises(ValueError): equal_vote(predictions)


def test_metrics_and_stacking_oof_temporal_guard():
    assert probability_metrics([0,1],[.1,.9])["pr_auc"]==1
    validate_temporal_oof([{"training_outcome_cutoff":"2023-01","prediction_month":"2023-02","prediction_scope":"OUT_OF_FOLD"}])
    with pytest.raises(ValueError): validate_temporal_oof([{"training_outcome_cutoff":"2023-02","prediction_month":"2023-02","prediction_scope":"OUT_OF_FOLD"}])
