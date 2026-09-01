from __future__ import annotations

import hashlib
from pathlib import Path

from src.identity.continuity_audit import (
    MAY_CSV_SHA256,
    JUNE_CSV_SHA256,
    classify_exact_code_pair,
    classify_project_codes,
    generate_candidates,
    normalize_for_comparison,
)

ROOT = Path(__file__).resolve().parents[1]


def row(code: str, name: str = "Project A", agency: str = "Agency", state: str = "State"):
    return {
        "observation_id": f"OBS-{code}", "project_code_raw": code,
        "project_name_raw": name, "agency_raw": agency, "state_raw": state,
    }


def test_unique_exact_code_matching():
    result = classify_project_codes([row("1"), row("2")], [row("1"), row("3")])
    assert result == {"1": "EXACT_1_TO_1", "2": "MAY_ONLY", "3": "JUNE_ONLY"}


def test_duplicate_code_is_not_forced_into_match():
    result = classify_project_codes([row("1"), row("1")], [row("1")])
    assert result["1"] == "DUPLICATE_IN_MAY"
    result = classify_project_codes([row("1"), row("1")], [row("1"), row("1")])
    assert result["1"] == "CONFLICT"


def test_normalized_comparison_preserves_raw_fields():
    may = row("1", name="Road—Project", agency="Agency [A]")
    june = row("1", name="road project", agency="Agency A")
    before = dict(may)
    classification, variations = classify_exact_code_pair(may, june)
    assert classification == "CODE_MATCH_TEXT_CONSISTENT"
    assert variations == []
    assert may == before
    assert normalize_for_comparison(may["project_name_raw"]) == "road project"


def test_candidates_always_require_review():
    candidates = generate_candidates([row("1")], [row("2")])
    assert len(candidates) == 1
    assert candidates[0]["status"] == "REVIEW_REQUIRED"


def test_dissimilar_unmatched_rows_remain_unmatched():
    assert generate_candidates(
        [row("1", "Airport terminal", state="Goa")],
        [row("2", "Coal mine expansion", state="Jharkhand")],
    ) == []


def test_validated_source_csvs_are_unchanged():
    may = hashlib.sha256((ROOT / "data/extracted/ongoing/ongoing_2026_05.csv").read_bytes()).hexdigest()
    june = hashlib.sha256((ROOT / "data/extracted/ongoing/ongoing_2026_06.csv").read_bytes()).hexdigest()
    assert may == MAY_CSV_SHA256
    assert june == JUNE_CSV_SHA256
