from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from src.pipeline.build_twelve_month_dataset import (
    DATASET_STATUS,
    DATASET_VERSION,
    FROZEN_EXTRACTION_HASHES,
    MONTHS,
    NEW_MONTHS,
    SAMPLE_SEED,
    detect_adapter,
)
from src.pipeline.source_registry import resolve_source
from src.validation.provenance import validate_provenance_record

ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "data" / "extracted" / "ongoing"
PROCESSED = ROOT / "data" / "processed" / "pilot_2025_07_2026_06"
LONGITUDINAL = ROOT / "validation" / "longitudinal" / "twelve_month"
MANIFEST = ROOT / "data" / "metadata" / "source_manifest.csv"
EXPECTED_COUNTS = {
    "2025-07": 791, "2025-08": 800, "2025-09": 794, "2025-10": 820,
    "2025-11": 823, "2025-12": 1392, "2026-01": 1702,
    "2026-02": 1948, "2026-03": 1941, "2026-04": 1981,
    "2026-05": 1987, "2026-06": 1847,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extraction(month: str) -> Path:
    return EXTRACTED / f"ongoing_{month.replace('-', '_')}.csv"


def test_source_inventory_has_twelve_distinct_hashes_and_resolves():
    hashes = []
    for month in MONTHS:
        source_id = "SRC-2025-07-P01" if month == "2025-07" else f"SRC-{month}"
        source = resolve_source(source_id, MANIFEST, ROOT)
        assert source.path.is_file()
        assert source.file_status == "CANONICAL"
        assert source.sha256 == digest(source.path)
        hashes.append(source.sha256)
    assert len(hashes) == len(set(hashes)) == 12


def test_schema_adapter_routing_uses_structure_and_unknown_fails_closed():
    assert detect_adapter(["Project Code", "Approval Date"]) == "PAIMANA_V1_APPROVAL_ONLY"
    assert detect_adapter(["Project Code", "Approval Date / Start Date"]) == "PAIMANA_V1_INLINE_CODE"
    assert detect_adapter(["Project Code", "Legacy OCMS Code", "Start Date"]) == "PAIMANA_V1_WITH_LEGACY"
    assert detect_adapter(["Project Code", "Legacy OCMS Code", "PMGID", "Start Date"]) == "PAIMANA_V2"
    with pytest.raises(ValueError, match="UNKNOWN schema"):
        detect_adapter(["Project Name", "Cost"])


def test_monthly_counts_serials_codes_and_structural_reconciliation():
    for month in MONTHS:
        rows = read_csv(extraction(month))
        assert len(rows) == EXPECTED_COUNTS[month]
        serials = [int(row["serial_number_raw"]) for row in rows]
        codes = [row["project_code_raw"] for row in rows]
        assert serials == list(range(1, EXPECTED_COUNTS[month] + 1))
        assert all(code == code.strip() and code.isdigit() for code in codes)
        assert len(codes) == len(set(codes))
        if month in NEW_MONTHS:
            path = ROOT / "validation" / "extraction_validation" / month / f"{month.replace('-', '_')}_extraction_summary.json"
            summary = json.loads(path.read_text(encoding="utf-8"))
            assert summary["accepted_project_rows"] + sum(summary["structural_counts"].values()) + summary["unresolved_rows"] == summary["total_raw_table_rows"]
            assert summary["quality_gate"] == "PASS_AUTOMATED"
            assert summary["unresolved_rows"] == 0
            assert "required_field_audit" in summary["field_quality"]


def test_every_project_month_has_unique_key_and_valid_provenance():
    rows = read_csv(PROCESSED / "project_month.csv")
    keys = {(row["canonical_project_id"], row["reporting_month"]) for row in rows}
    assert len(rows) == sum(EXPECTED_COUNTS.values()) == len(keys) == 16826
    assert not [error for row in rows for error in validate_provenance_record(row, MANIFEST)]
    assert len({(row["source_id"], row["raw_row_locator"]) for row in rows}) == len(rows)


def test_canonical_union_and_history_bounds_are_exact():
    master = read_csv(PROCESSED / "project_master.csv")
    month = read_csv(PROCESSED / "project_month.csv")
    assert len(master) == len({row["canonical_project_id"] for row in master}) == 2207
    observations = Counter(row["canonical_project_id"] for row in month)
    for row in master:
        assert row["canonical_project_id"] == f"PRH-{row['project_code']}"
        assert int(row["observation_count"]) == observations[row["canonical_project_id"]]


def test_all_eleven_pairwise_boundaries_have_no_conflicts():
    rows = read_csv(LONGITUDINAL / "pairwise_identity_continuity.csv")
    assert len(rows) == 11
    assert all(row["left_duplicates"] == row["right_duplicates"] == row["identity_conflicts"] == "0" for row in rows)
    assert sum(int(row["exact_matches"]) for row in rows) == 14583


def test_presence_gaps_are_review_only_and_not_synthesized():
    gaps = read_csv(LONGITUDINAL / "internal_presence_gap_review.csv")
    month = read_csv(PROCESSED / "project_month.csv")
    assert len(gaps) == 36
    keys = {(row["canonical_project_id"], row["reporting_month"]) for row in month}
    for gap in gaps:
        for missing_month in gap["internal_missing_months"].split("|"):
            assert (gap["canonical_project_id"], missing_month) not in keys


def test_frozen_extractions_and_prior_pilot_hashes_are_immutable():
    for month, expected in FROZEN_EXTRACTION_HASHES.items():
        assert digest(extraction(month)) == expected
    expected = {
        "data/processed/pilot_2026_04_06/project_master.csv": "b282da6e8d28dc615903195d3fb29183a53215b51d99f663dd19ef1108169c5d",
        "data/processed/pilot_2026_04_06/project_month.csv": "2b6cd7d2b97369bfaad3d6721407eb6596ccd042622d41fe95f972dd07207aff",
        "data/processed/pilot_2026_05_06/project_master.csv": "f760d5ac9fcf62fb52a6ddd029719f6a0653fd22fcfb58663d350224ae9c8d86",
        "data/processed/pilot_2026_05_06/project_month.csv": "188189b03a8fcb8f1e431840ef96ab466b1414eb686c08fda994d276c7cf8761",
    }
    for path, expected_hash in expected.items():
        assert digest(ROOT / path) == expected_hash


def test_dataset_manifest_is_provisional_and_hash_complete():
    metadata = json.loads((PROCESSED / "dataset_metadata.json").read_text(encoding="utf-8"))
    assert metadata["dataset_version"] == DATASET_VERSION
    assert metadata["status"] == DATASET_STATUS
    assert metadata["automated_validation_status"] == "PASS"
    assert metadata["human_validation_status"] == "PENDING_FOR_NINE_NEW_MONTHS"
    assert metadata["monthly_row_counts"] == EXPECTED_COUNTS
    assert set(metadata["source_hashes"]) == set(metadata["extraction_hashes"]) == set(MONTHS)
    for month, expected_hash in metadata["extraction_hashes"].items():
        assert digest(extraction(month)) == expected_hash


def test_manual_samples_are_deterministic_sized_and_unreviewed():
    assert SAMPLE_SEED == 26103
    manual = ("manual_row_confirmed", "manual_identity_confirmed", "manual_fields_confirmed", "manual_provenance_confirmed", "reviewer", "review_notes")
    for month in NEW_MONTHS:
        path = ROOT / "validation" / "extraction_validation" / month / f"{month.replace('-', '_')}_manual_sample.csv"
        rows = read_csv(path)
        assert len(rows) == 20
        assert {"FIRST", "LAST", "EARLY_PAGE", "MIDDLE_PAGE", "LATE_PAGE"} <= {row["sample_category"] for row in rows}
        assert all(all(row[field] == "" for field in manual) for row in rows)


def test_no_forbidden_gate_two_outputs_or_completion_inference():
    forbidden_exact = {
        "risk_score", "risk_class", "prediction", "target", "label",
        "training_dataset", "shap_value", "alert_priority", "confidence_score",
        "completion_status", "is_completed", "is_new", "is_cancelled",
    }
    for path in (PROCESSED / "project_master.csv", PROCESSED / "project_month.csv"):
        with path.open(encoding="utf-8", newline="") as handle:
            fields = {field.casefold() for field in (csv.DictReader(handle).fieldnames or [])}
        assert fields.isdisjoint(forbidden_exact)
