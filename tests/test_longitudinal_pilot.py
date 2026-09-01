from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from src.pipeline.build_longitudinal_pilot import (
    DATASET_VERSION,
    MAY_CSV_SHA256,
    JUNE_CSV_SHA256,
    build_master,
    canonical_project_id,
    to_project_month,
)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed/pilot_2026_05_06"
MAY_PDF_SHA = "480d98632cd1b1d4fe70b58a5a753924b2735b0135e7c8507c1ec05ff2ddf005"
JUNE_PDF_SHA = "d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15"


def read(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_canonical_ids_are_deterministic_and_distinct_from_project_code():
    assert canonical_project_id("618702") == "PRH-618702"
    assert canonical_project_id("618702") == canonical_project_id("618702")
    assert canonical_project_id("618702") != "618702"


def test_master_and_month_reconcile_without_duplicate_keys():
    master = read(PROCESSED / "project_master.csv")
    month = read(PROCESSED / "project_month.csv")
    assert len(master) == 2009
    assert len(month) == 3834
    assert len({row["canonical_project_id"] for row in master}) == 2009
    assert len({(row["canonical_project_id"], row["reporting_month"]) for row in month}) == 3834
    assert Counter(row["presence_status"] for row in master) == {
        "MAY_ONLY": 162, "MAY_AND_JUNE": 1825, "JUNE_ONLY": 22,
    }
    assert set(row["observation_count"] for row in master) <= {"1", "2"}


def test_project_month_is_lossless_mapping_with_full_provenance():
    raw = read(ROOT / "data/extracted/ongoing/ongoing_2026_05.csv") + read(
        ROOT / "data/extracted/ongoing/ongoing_2026_06.csv"
    )
    transformed = {row["observation_id"]: row for row in read(PROCESSED / "project_month.csv")}
    assert set(transformed) == {row["observation_id"] for row in raw}
    for source in raw:
        expected = to_project_month(source)
        assert transformed[source["observation_id"]] == expected


def test_historical_may_values_are_not_overwritten_by_june():
    month = read(PROCESSED / "project_month.csv")
    by_key = {(row["project_code"], row["reporting_month"]): row for row in month}
    raw_may = read(ROOT / "data/extracted/ongoing/ongoing_2026_05.csv")
    for source in raw_may:
        pilot = by_key[(source["project_code_raw"], "2026-05")]
        assert pilot["reported_project_name"] == source["project_name_raw"]
        assert pilot["reported_agency"] == source["agency_raw"]
        assert pilot["reported_revised_cost"] == source["revised_cost_raw"]
        assert pilot["reported_physical_progress"] == source["physical_progress_raw"]


def test_master_current_value_comes_from_latest_available_observation():
    month = read(PROCESSED / "project_month.csv")
    master = read(PROCESSED / "project_master.csv")
    by_project = {}
    for row in month:
        by_project.setdefault(row["canonical_project_id"], []).append(row)
    for row in master:
        latest = max(by_project[row["canonical_project_id"]], key=lambda item: item["reporting_month"])
        assert row["current_observation_id"] == latest["observation_id"]
        assert row["current_project_name"] == latest["reported_project_name"]
        assert row["current_raw_row_locator"] == latest["raw_row_locator"]


def test_unmatched_observations_are_retained():
    master = read(PROCESSED / "project_master.csv")
    assert sum(row["presence_status"] == "MAY_ONLY" for row in master) == 162
    assert sum(row["presence_status"] == "JUNE_ONLY" for row in master) == 22


def test_no_completion_or_ml_fields_are_created():
    forbidden = {"completed", "completion_event", "new_project", "ml_label", "outcome", "risk_score", "feature"}
    for filename in ("project_master.csv", "project_month.csv"):
        with (PROCESSED / filename).open(encoding="utf-8", newline="") as handle:
            fields = csv.DictReader(handle).fieldnames or []
        assert not any(any(term in field.casefold() for term in forbidden) for field in fields)


def test_input_and_source_hashes_are_unchanged():
    assert sha(ROOT / "data/extracted/ongoing/ongoing_2026_05.csv") == MAY_CSV_SHA256
    assert sha(ROOT / "data/extracted/ongoing/ongoing_2026_06.csv") == JUNE_CSV_SHA256
    assert sha(ROOT / "data/raw/2026/FlashReport_2026_05.pdf") == MAY_PDF_SHA
    assert sha(ROOT / "data/raw/2026/FlashReport_2026_06.pdf") == JUNE_PDF_SHA


def test_dataset_metadata_and_manual_sample_contract():
    metadata = json.loads((PROCESSED / "dataset_metadata.json").read_text(encoding="utf-8"))
    assert metadata["dataset_version"] == DATASET_VERSION
    sample = read(ROOT / "validation/longitudinal/may_june_2026_manual_longitudinal_sample_30.csv")
    assert len(sample) == 30
    for row in sample:
        assert row["manual_history_correct"] == ""
        assert row["manual_temporal_values_correct"] == ""
        assert row["manual_provenance_correct"] == ""
        assert row["reviewer"] == ""
        assert row["review_notes"] == ""
