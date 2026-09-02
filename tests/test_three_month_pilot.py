from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from src.pipeline.build_longitudinal_pilot import to_project_month
from src.pipeline.build_three_month_pilot import (
    DATASET_VERSION,
    MONTHS,
    SEED,
    _sample,
    canonical_id,
    pair_flags,
    presence_pattern,
)
from src.validation.provenance import validate_provenance_record

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed/pilot_2026_04_06"
IDENTITY = ROOT / "validation/identity_continuity"
LONGITUDINAL = ROOT / "validation/longitudinal"
EXPECTED_INPUT_HASHES = {
    "2026-04": "55d84996925b4d5d0f2bb3bc9367a685c2ad49a14c009acddc7662b0b9ee11dd",
    "2026-05": "f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e",
    "2026-06": "bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9",
}


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_presence_patterns_and_exact_code_mapping():
    assert canonical_id("618814") == "PRH-618814"
    assert presence_pattern(set(MONTHS)) == "APR_MAY_JUN"
    assert presence_pattern({"2026-04", "2026-06"}) == "APR_JUN_ONLY"
    assert presence_pattern({"2026-05"}) == "MAY_ONLY"


def test_three_month_union_keys_and_row_reconciliation():
    master, month = read(PROCESSED / "project_master.csv"), read(PROCESSED / "project_month.csv")
    assert len(master) == 2038
    assert len(month) == 1981 + 1987 + 1847
    assert len({row["canonical_project_id"] for row in master}) == len(master)
    assert len({(row["canonical_project_id"], row["reporting_month"]) for row in month}) == len(month)
    assert Counter(row["presence_pattern"] for row in master) == {
        "APR_MAY_JUN": 1790, "APR_MAY_ONLY": 161, "MAY_JUN_ONLY": 35,
        "APR_JUN_ONLY": 1, "APR_ONLY": 29, "MAY_ONLY": 1, "JUN_ONLY": 21,
    }


def test_monthly_history_is_a_lossless_mapping():
    raw = []
    for month in MONTHS:
        raw.extend(read(ROOT / f"data/extracted/ongoing/ongoing_{month.replace('-', '_')}.csv"))
    actual = {row["observation_id"]: row for row in read(PROCESSED / "project_month.csv")}
    assert set(actual) == {row["observation_id"] for row in raw}
    for source in raw:
        assert actual[source["observation_id"]] == to_project_month(source)


def test_master_current_fields_come_from_latest_observation():
    month = read(PROCESSED / "project_month.csv")
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in month:
        grouped.setdefault(row["canonical_project_id"], []).append(row)
    for master in read(PROCESSED / "project_master.csv"):
        latest = max(grouped[master["canonical_project_id"]], key=lambda row: row["reporting_month"])
        assert master["latest_observed_month"] == latest["reporting_month"]
        assert master["current_project_name"] == latest["reported_project_name"]
        assert master["current_observation_id"] == latest["observation_id"]
        assert master["current_raw_row_locator"] == latest["raw_row_locator"]


def test_both_boundaries_and_trajectory_outputs_are_present():
    transitions = read(LONGITUDINAL / "april_may_june_2026_transitions.csv")
    assert Counter(row["boundary"] for row in transitions) == {"APR_TO_MAY": 1951, "MAY_TO_JUN": 1825}
    assert any("PHYSICAL_PROGRESS_DECREASED" in row["primary_flags"] for row in transitions if row["boundary"] == "APR_TO_MAY")
    assert any("PHYSICAL_PROGRESS_DECREASED" in row["primary_flags"] for row in transitions if row["boundary"] == "MAY_TO_JUN")
    trajectories = read(LONGITUDINAL / "april_may_june_2026_trajectories.csv")
    assert len(trajectories) == 1790
    assert all(row["progress_trajectory"].count("→") == 2 for row in trajectories)


def test_pair_flags_detect_conservative_changes():
    base = {
        "project_name_raw": "A", "agency_raw": "B", "state_raw": "C",
        "approval_date_raw": "01/2020", "start_date_raw": "02/2020",
        "original_target_doc_raw": "03/2025", "revised_doc_raw": "-",
        "original_cost_raw": "100", "revised_cost_raw": "100",
        "physical_progress_raw": "50", "cumulative_expenditure_raw": "80",
    }
    changed = {**base, "project_name_raw": "A revised", "physical_progress_raw": "49", "cumulative_expenditure_raw": "79"}
    primary, secondary = pair_flags(base, changed)
    assert primary == ["PROJECT_NAME_CHANGED", "PHYSICAL_PROGRESS_DECREASED", "CUMULATIVE_EXPENDITURE_DECREASED"]
    assert secondary == []


def test_presence_gap_is_preserved_without_a_synthetic_may_row():
    gap = read(IDENTITY / "april_may_june_2026_presence_gap_review.csv")
    assert len(gap) == 1 and gap[0]["project_code"] == "618814"
    assert gap[0]["may_absence_verified"] == "YES"
    observations = [row for row in read(PROCESSED / "project_month.csv") if row["project_code"] == "618814"]
    assert [row["reporting_month"] for row in observations] == ["2026-04", "2026-06"]


def test_every_project_month_row_has_valid_provenance_and_unique_locator():
    month = read(PROCESSED / "project_month.csv")
    manifest = ROOT / "data/metadata/source_manifest.csv"
    assert not [error for row in month for error in validate_provenance_record(row, manifest)]
    locators = {(row["source_id"], row["raw_row_locator"]) for row in month}
    assert len(locators) == len(month)


def test_manual_samples_are_deterministic_complete_and_empty():
    identity = read(IDENTITY / "april_may_june_2026_manual_identity_sample.csv")
    temporal = read(LONGITUDINAL / "april_may_june_2026_temporal_sample.csv")
    assert len(identity) == len(temporal) == 30
    assert any(row["presence_pattern"] == "APR_JUN_ONLY" for row in identity)
    assert any(row["presence_pattern"] == "APR_JUN_ONLY" for row in temporal)
    combined_flags = "|".join(row["apr_to_may_primary_flags"] + row["may_to_jun_primary_flags"] for row in temporal)
    for required in ("PROJECT_NAME_CHANGED", "APPROVAL_DATE_CHANGED", "START_DATE_CHANGED", "ORIGINAL_COST_CHANGED"):
        assert required in combined_flags
    for row in identity:
        assert all(row[field] == "" for field in ("manual_identity_confirmed", "manual_presence_pattern_confirmed", "manual_provenance_confirmed", "reviewer", "review_notes"))
    for row in temporal:
        assert all(row[field] == "" for field in ("manual_values_confirmed", "manual_flags_confirmed", "manual_provenance_confirmed", "reviewer", "review_notes"))
    synthetic = [{"canonical_project_id": f"PRH-{i}", "project_code": str(i)} for i in range(40)]
    categories = [("ALL", lambda _: True, 30)]
    assert _sample(synthetic, categories, ("manual",)) == _sample(synthetic, categories, ("manual",))
    assert SEED == 26103


def test_metadata_hashes_and_no_ml_or_completion_fields():
    metadata = json.loads((PROCESSED / "dataset_metadata.json").read_text(encoding="utf-8"))
    assert metadata["dataset_version"] == DATASET_VERSION
    assert metadata["input_hashes"] == EXPECTED_INPUT_HASHES
    for month, expected in EXPECTED_INPUT_HASHES.items():
        assert sha(ROOT / f"data/extracted/ongoing/ongoing_{month.replace('-', '_')}.csv") == expected
    forbidden = ("risk_score", "risk_class", "prediction", "ml_label", "completion_event", "new_project", "feature_")
    for filename in ("project_master.csv", "project_month.csv"):
        with (PROCESSED / filename).open(encoding="utf-8", newline="") as handle:
            fields = csv.DictReader(handle).fieldnames or []
        assert not any(term in field.casefold() for field in fields for term in forbidden)
