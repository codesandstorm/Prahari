from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.ml.cost_experiment_v3 import COST_V3_FOLDS, cost_folds
from src.pipeline.build_mixed_coverage_dataset import (
    _identity_ocms,
    _remove_ocms_flash_report_overlay,
    discover_table,
    extract_project_month,
)


def test_historical_identity_accepts_evidenced_optional_post_bracket_comma():
    name, agency, state, code = _identity_ocms("PROJECT - [N02000010]NPCIL,GUJARAT ,")
    assert (name, agency, state, code) == ("PROJECT", "NPCIL", "GUJARAT", "N02000010")


def test_compound_flash_report_overlay_repair_is_exact_shape_only():
    cells = ["1F288", "WIDELNING ANDA UP-GRADATISON - [N24000865],NHIDCL,MIZORAM", "H4/2017",
             "R9/2019\n(-)\n[9/2023]", "E428P.11\n(-)\n[428.11]", "O55.86 R\n(0.00)\n[48]", "T0/4"]
    repaired, changed = _remove_ocms_flash_report_overlay(cells)
    assert changed and repaired[0] == "1288"
    assert repaired[2] == "4/2017" and repaired[4].startswith("428.11")
    ordinary = ["1", "PROJECT - [N1],A,S", "1/2020", "1/2021", "100", "50", "0/1"]
    assert _remove_ocms_flash_report_overlay(ordinary) == (ordinary, False)


def test_v3_folds_are_chronological_and_cover_distinct_eras():
    assert len(COST_V3_FOLDS) == 10
    for start, end in COST_V3_FOLDS.values():
        assert start <= end
    assert next(iter(COST_V3_FOLDS.values()))[0].startswith("2019")
    assert list(COST_V3_FOLDS.values())[-1][1] == "2026-03"


def test_fold_outcomes_mature_before_test():
    cohort = []
    for year in range(2018, 2020):
        for month in range(1, 13):
            cohort.append({"anchor_month": f"{year}-{month:02d}", "event": int(month == 2),
                           "canonical_project_id": f"P{month}", "schema_family": "OCMS"})
    for fold in cost_folds(cohort, 3):
        if fold["train_end"]:
            from src.ml.final_prediction import add_month
            assert add_month(fold["train_end"], 3) < fold["test_start"]


@pytest.mark.integration
def test_external_archive_representative_month_when_configured():
    raw = os.environ.get("PRAHARI_RAW_ROOT")
    if not raw:
        pytest.skip("PRAHARI_RAW_ROOT not configured")
    path = Path(raw) / "2018/FlashReport_2018_01.pdf"
    discovery = discover_table(path)
    rows, summary = extract_project_month(path, "2018-01", discovery)
    assert len(rows) == summary["official_project_count"] == 1304
    assert not summary["unresolved_rows"] and not summary["duplicate_serials"]


def test_v3_dataset_contract_when_built():
    root = Path(__file__).resolve().parents[1]
    data = root / "data/processed/longitudinal_2018_01_2026_06_cost_research_v3"
    if not (data / "dataset_metadata.json").is_file():
        pytest.skip("V3 dataset has not been built")
    metadata = json.loads((data / "dataset_metadata.json").read_text(encoding="utf-8"))
    assert metadata["v2_source_unchanged"] is True
    assert metadata["raw_sources_read_only"] is True
    assert metadata["july_2026_included"] is False
    assert "2022-07" in metadata["missing_months"]
