import math
import csv
from pathlib import Path

from src.ml.feature_discovery_v2 import COMPACT_V2, VARIANTS, advanced_features, safe_ratio


def row(month, progress="10", expenditure="10", target="12/2026", schema="PAIMANA"):
    return {"reporting_month":month,"physical_progress_raw":progress,"cumulative_expenditure_raw":expenditure,
            "original_cost_raw":"100","revised_cost_raw":"","approval_date_raw":"01/2024",
            "original_target_doc_raw":target,"revised_doc_raw":"","schema_family":schema}


def test_velocity_uses_elapsed_calendar_interval():
    result=advanced_features([row("2025-01","10"),row("2025-03","14")])
    assert result["progress_velocity_last"]==2


def test_required_future_velocity():
    result=advanced_features([row("2025-01","40"),row("2025-02","50")])
    assert result["remaining_work_pct"]==50
    assert math.isclose(result["required_future_velocity"],50/22)


def test_past_deadline_does_not_create_infinity():
    result=advanced_features([row("2025-01","90",target="12/2024"),row("2025-02","90",target="12/2024")])
    assert math.isnan(result["required_future_velocity"])
    assert result["remaining_schedule_months"]==0


def test_completed_progress_requires_zero_future_velocity():
    result=advanced_features([row("2025-01","100"),row("2025-02","100")])
    assert result["required_future_velocity"]==0


def test_financial_physical_gap_is_association_only():
    result=advanced_features([row("2025-01","20","50"),row("2025-02","25","60")])
    assert result["financial_progress_pct"]==60
    assert result["financial_physical_gap"]==35


def test_change_point_uses_past_only():
    result=advanced_features([row("2025-01","10"),row("2025-02","20"),row("2025-03","20")])
    assert result["momentum_break_flag"]==1
    assert result["recent_stagnation_after_activity"]==1


def test_safe_ratio_rejects_zero_and_missing_denominator():
    assert math.isnan(safe_ratio(1,0))
    assert math.isnan(safe_ratio(1,math.nan))


def test_compact_features_contain_no_future_or_identity_fields():
    forbidden=("future_revised_doc","project_name","project_id","contractor","actual_completion")
    assert not any(feature == token for feature in COMPACT_V2 for token in forbidden)


def test_no_variant_contains_unsupported_contractor_or_land_data():
    names={feature for features in VARIANTS.values() for feature in features}
    assert not any("contractor" in name or "land_" in name or "milestone" in name for name in names)


def test_v2_registry_is_unique_and_uses_allowed_dispositions():
    path=Path(__file__).resolve().parents[1]/"data/metadata/prahari_feature_registry_v2.csv"
    with path.open(encoding="utf-8",newline="") as handle: rows=list(csv.DictReader(handle))
    allowed={"IMPLEMENT_NOW","IMPLEMENT_CONDITIONALLY","RESEARCH_EXTERNAL_SOURCE","REQUIRES_EXISTING_CUF_VERIFICATION","PROPOSE_NEW_CUF_FIELD","REJECT_REDUNDANT","REJECT_UNSTABLE","REJECT_LEAKAGE","REJECT_SEMANTICALLY_UNSAFE","REJECT_INSUFFICIENT_DATA"}
    assert len({row["feature_id"] for row in rows})==len(rows)
    assert {row["retain_status"] for row in rows}<=allowed
    assert all(row["availability"]=="UNAVAILABLE" for row in rows if "contractor" in row["feature_name"])


def test_advanced_features_are_deterministic():
    history=[row("2025-01","10","15"),row("2025-03","14","20")]
    first=advanced_features(history);second=advanced_features(history)
    assert all(first[key]==second[key] or (isinstance(first[key],float) and math.isnan(first[key]) and math.isnan(second[key])) for key in first)
