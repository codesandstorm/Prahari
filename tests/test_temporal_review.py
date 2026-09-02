"""Focused validation for the exhaustive May-June temporal review."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.validation.temporal_review import (
    MANUAL_FIELDS,
    automated_checks,
    build_review_rows,
    read_csv,
    sha256,
)

ROOT = Path(__file__).resolve().parents[1]
PROJECT_MONTH = ROOT / "data/processed/pilot_2026_05_06/project_month.csv"
MAY = ROOT / "data/extracted/ongoing/ongoing_2026_05.csv"
JUNE = ROOT / "data/extracted/ongoing/ongoing_2026_06.csv"
MASTER = ROOT / "data/processed/pilot_2026_05_06/project_master.csv"


@pytest.fixture(scope="module")
def review_context():
    before = {path: sha256(path) for path in (PROJECT_MONTH, MASTER, MAY, JUNE)}
    project_month = read_csv(PROJECT_MONTH)
    review, diagnostic_counts = build_review_rows(project_month)
    checks = automated_checks(review, project_month, read_csv(MAY), read_csv(JUNE))
    return before, project_month, review, diagnostic_counts, checks


def test_flag_reconstruction_is_deterministic(review_context):
    _, project_month, review, counts, _ = review_context
    again, again_counts = build_review_rows(project_month)
    assert review == again
    assert counts == again_counts


def test_one_review_row_per_canonical_project(review_context):
    _, _, review, _, _ = review_context
    ids = [row["canonical_project_id"] for row in review]
    assert len(review) == 88
    assert len(ids) == len(set(ids))


def test_expected_primary_flag_aggregation(review_context):
    _, _, review, _, _ = review_context
    counts = {
        flag: sum(flag in row["flag_reasons"].split("|") for row in review)
        for flag in (
            "PROJECT_NAME_CHANGED", "APPROVAL_DATE_CHANGED", "START_DATE_CHANGED",
            "ORIGINAL_COST_CHANGED", "PHYSICAL_PROGRESS_DECREASED",
            "CUMULATIVE_EXPENDITURE_DECREASED",
        )
    }
    assert counts == {
        "PROJECT_NAME_CHANGED": 6,
        "APPROVAL_DATE_CHANGED": 3,
        "START_DATE_CHANGED": 21,
        "ORIGINAL_COST_CHANGED": 6,
        "PHYSICAL_PROGRESS_DECREASED": 19,
        "CUMULATIVE_EXPENDITURE_DECREASED": 38,
    }


def test_may_and_june_values_equal_validated_sources(review_context):
    _, _, _, _, checks = review_context
    assert checks
    assert all(row["may_values_equal_source"] == "YES" for row in checks)
    assert all(row["june_values_equal_source"] == "YES" for row in checks)


def test_provenance_and_identity_equal_sources(review_context):
    _, _, _, _, checks = review_context
    assert all(row["provenance_equal_source"] == "YES" for row in checks)
    assert all(row["identity_equal_source"] == "YES" for row in checks)
    assert all(row["automated_result"] == "PASS" for row in checks)


def test_manual_fields_are_empty(review_context):
    _, _, review, _, _ = review_context
    assert all(row[field] == "" for row in review for field in MANUAL_FIELDS)


def test_no_risk_label_or_completion_fields(review_context):
    _, _, review, _, _ = review_context
    forbidden = ("risk", "label", "completion", "prediction", "feature")
    assert not any(token in field.lower() for field in review[0] for token in forbidden)


def test_validation_does_not_mutate_frozen_inputs(review_context):
    before, _, _, _, _ = review_context
    after = {path: sha256(path) for path in before}
    assert after == before
