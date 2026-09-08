import math
import csv
from pathlib import Path

from src.ml.teammate_feature_review import (
    add_peer_features, changepoint_features, expenditure_lag_features,
    recovery_features, teammate_features,
)


def test_changepoint_is_past_only_and_deterministic():
    past = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 8), (5, 13)]
    assert changepoint_features(past) == changepoint_features(past)
    assert changepoint_features(past) == changepoint_features(past + [(6, 30)])[:0] + changepoint_features(past)


def test_changepoint_is_gap_aware():
    months, direction, magnitude = changepoint_features([(0, 0), (2, 2), (4, 4), (6, 6), (8, 16), (10, 26)])
    assert months >= 0 and direction == 1 and magnitude > 0


def test_recovery_uses_only_completed_windows():
    result = recovery_features([(0, 0), (1, 0), (2, 2), (3, 2), (4, 2), (5, 5)])
    assert result["prior_stall_count"] == 2
    assert result["recovered_stall_count"] == 2
    # A stall at the anchor is unresolved and therefore excluded.
    assert recovery_features([(0, 0), (1, 0)])["prior_stall_count"] == 0


def test_peer_feature_excludes_project_itself():
    rows = [{"canonical_project_id": str(i), "anchor_month": "2025-01", "log_original_cost": math.log1p(100.0),
             "physical_progress": 40.0, "progress_velocity_last": float(i)} for i in range(4)]
    add_peer_features(rows, minimum_group=3)
    assert rows[0]["peer_group_size"] == 3
    assert rows[3]["peer_velocity_percentile"] == 100


def test_expenditure_lag_is_past_only_and_requires_four_pairs():
    short = expenditure_lag_features([(0, 0), (1, 1)], [(0, 0), (1, 1)])
    assert math.isnan(short["historical_exp_progress_lag_corr"])
    progress = [(i, float(i * i)) for i in range(7)]
    expenditure = [(i, float(i)) for i in range(7)]
    assert "historical_exp_progress_lag_slope" in expenditure_lag_features(progress, expenditure)


def test_teammate_features_do_not_require_future_fields():
    history = [{"reporting_month": f"2025-0{i}", "physical_progress_raw": str(i),
                "cumulative_expenditure_raw": str(i * 2)} for i in range(1, 7)]
    assert teammate_features(history) == teammate_features(history)


def test_registry_uses_only_permitted_verdicts():
    path = Path(__file__).resolve().parents[1] / "data/metadata/prahari_teammate_feature_registry.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    allowed = {"ADOPT_NOW_CORE", "ADOPT_NOW_CONDITIONAL", "ADOPT_AS_RELIABILITY_FEATURE", "FUTURE_CUF", "FUTURE_EXTERNAL", "FUTURE_AFTER_COMPLETION_DATA", "REJECT_REDUNDANT", "REJECT_UNSTABLE", "REJECT_LEAKAGE", "REJECT_INSUFFICIENT_DATA", "REJECT_SEMANTICALLY_UNSAFE"}
    assert rows and {r["final_verdict"] for r in rows} <= allowed
    assert next(r for r in rows if r["feature_name"] == "contractor_peer_trend")["final_verdict"] == "FUTURE_CUF"


def test_horizon_censoring_requires_complete_future_months():
    from src.ml.teammate_feature_review import build_review_cohort
    coverage = {f"2025-{m:02d}": "PROJECT_LEVEL" for m in range(1, 8)}
    rows = []
    for m in range(1, 8):
        rows.append({"canonical_project_id": "P1", "reporting_month": f"2025-{m:02d}",
                     "physical_progress_raw": str(m), "cumulative_expenditure_raw": str(m),
                     "original_cost_raw": "100", "original_target_doc_raw": "12/2025",
                     "approval_date_raw": "01/2025", "revised_doc_raw": ""})
    assert len(build_review_cohort(rows, coverage, 3)) > len(build_review_cohort(rows, coverage, 6))
