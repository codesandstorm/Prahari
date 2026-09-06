import csv
import json
from pathlib import Path

from src.pipeline.build_mixed_coverage_dataset import (
    AGGREGATE_ONLY, MISSING_SOURCE, MONTHS, PROJECT_MONTHS,
    calendar_boundaries, month_distance,
    horizon_observability,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/longitudinal_2023_07_2026_06_mixed"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_calendar_contract_is_30_5_1():
    assert len(MONTHS) == 36
    assert len(PROJECT_MONTHS) == 30
    assert AGGREGATE_ONLY == {"2023-12", "2024-04", "2024-05", "2024-08", "2024-09"}
    assert MISSING_SOURCE == {"2025-02"}


def test_report_month_has_exact_calendar_without_july_duplicate():
    data = rows(OUT / "report_month.csv")
    assert [row["reporting_month"] for row in data] == list(MONTHS)
    assert all(row["reporting_month"] != "2026-07" for row in data)
    counts = {kind: sum(row["coverage_class"] == kind for row in data) for kind in ("PROJECT_LEVEL", "AGGREGATE_ONLY", "MISSING_SOURCE")}
    assert counts == {"PROJECT_LEVEL": 30, "AGGREGATE_ONLY": 5, "MISSING_SOURCE": 1}


def test_project_month_contains_only_observed_project_months():
    data = rows(OUT / "project_month.csv")
    observed = {row["reporting_month"] for row in data}
    assert observed == set(PROJECT_MONTHS)
    assert not (observed & (AGGREGATE_ONLY | MISSING_SOURCE | {"2026-07"}))
    keys = [(row["canonical_project_id"], row["reporting_month"]) for row in data]
    assert len(keys) == len(set(keys))


def test_no_forbidden_model_or_synthetic_fields():
    forbidden = ("risk", "prediction", "label", "shap", "fraud", "corruption", "synthetic", "interpolated")
    fields = {field.lower() for field in rows(OUT / "project_month.csv")[0]}
    assert not any(token in field for field in fields for token in forbidden)


def test_gap_distances_are_calendar_aware():
    assert month_distance("2024-03", "2024-06") == 3
    coverage = rows(ROOT / "data/metadata/source_coverage_2023_07_2026_06.csv")
    boundaries = calendar_boundaries(coverage)
    assert len(boundaries) == 35
    assert any(row["boundary_class"] == "CROSSES_MISSING_MONTH" for row in boundaries)


def test_metadata_and_protected_hash_audit():
    metadata = json.loads((OUT / "dataset_metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "PROVISIONAL - MIXED COVERAGE - HUMAN VALIDATION PENDING"
    assert metadata["forbidden_transformations_applied"] == []
    protected = json.loads((OUT / "protected_hash_audit.json").read_text(encoding="utf-8"))
    assert protected["status"] == "PASS"


def test_horizon_observability_censors_gaps_and_right_edge():
    coverage = rows(ROOT / "data/metadata/source_coverage_2023_07_2026_06.csv")
    audit = horizon_observability(coverage)
    assert len(audit) == 36 * 3
    march_2024 = next(row for row in audit if row["anchor_month"] == "2024-03" and row["horizon_months"] == 3)
    assert march_2024["observability_status"] == "CENSORED_BY_GAP"
    june_2026 = next(row for row in audit if row["anchor_month"] == "2026-06" and row["horizon_months"] == 3)
    assert june_2026["observability_status"] == "RIGHT_CENSORED"
