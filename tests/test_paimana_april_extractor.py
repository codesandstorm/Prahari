from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pdfplumber
import pytest
import yaml

from src.extraction.extractor_paimana import classify_non_project_row
from src.extraction.extractor_paimana_april import (
    EXPECTED_DATA_PAGES, EXTRACTOR_VERSION, MANUAL_FIELDS, SOURCE_ID,
    _stratified_sample, parse_april_project_row,
)
from src.extraction.schema_detector import detect_schema
from src.pipeline.source_registry import resolve_source
from src.validation.provenance import validate_provenance_record

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/metadata/source_manifest.csv"
APRIL_SHA = "90a6959e976da6928440efdea9c68847d1178356e4c0ebd078c51026ddb118d5"
FROZEN = {
    "data/extracted/ongoing/ongoing_2026_05.csv": "f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e",
    "data/extracted/ongoing/ongoing_2026_06.csv": "bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9",
}


def fixture_row() -> list[str]:
    return ["1", "April Project\n(Agency [Unit])\n(612786)\n(N04000106) (-)", "State", "03/2023\n(01/2024)", "01/2026\n(07/2026)", "265.91\n(265.91)", "142.62", "70"]


def parse(row=None):
    return parse_april_project_row(row or fixture_row(), source_sha256=APRIL_SHA, pdf_page_index=55, printed_page_number=54, table_index=0, row_index=3)


@pytest.mark.integration
def test_april_source_recognition():
    source = resolve_source(SOURCE_ID, MANIFEST, ROOT)
    assert (source.report_year, source.report_month) == (2026, 4)
    assert source.sha256 == APRIL_SHA


def test_april_project_row_and_compound_identity():
    record = parse()
    assert record["observation_id"] == "OBS-202604-00001"
    assert record["reporting_month"] == "2026-04"
    assert record["project_code_raw"] == "612786"
    assert record["agency_raw"] == "Agency [Unit]"
    assert record["legacy_ocms_code_raw"] == "N04000106"
    assert record["pmgid_raw"] == "-"
    assert record["extractor_version"] == EXTRACTOR_VERSION


def test_missing_markers_dates_costs_expenditure_progress_are_preserved():
    row = fixture_row(); row[4] = "01/2026\n(-)"; row[6] = "0"; row[7] = "0"
    record = parse(row)
    assert record["revised_doc_raw"] == "-"
    assert record["original_cost_raw"] == "265.91"
    assert record["cumulative_expenditure_raw"] == "0"
    assert record["physical_progress_raw"] == "0"


@pytest.mark.parametrize(("row", "kind"), [
    (["Sl.No", "Project Name", "", "", "", "", "", ""], "REPEATED_HEADER"),
    (["", "Sector", "", "", "", "", "", ""], "SECTION_HEADING"),
    (["", "Total (3)", "", "", "", "", "", ""], "TOTAL"),
])
def test_structural_classification(row, kind):
    assert classify_non_project_row(row) == kind


def test_real_output_serial_code_and_provenance_contract():
    with (ROOT / "data/extracted/ongoing/ongoing_2026_04.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1981
    assert [int(row["serial_number_raw"]) for row in rows] == list(range(1, 1982))
    assert len({row["project_code_raw"] for row in rows}) == 1981
    assert not [error for row in rows for error in validate_provenance_record(row, MANIFEST)]


def test_stratified_sample_is_deterministic_and_manual_fields_empty():
    with (ROOT / "data/extracted/ongoing/ongoing_2026_04.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    first, _ = _stratified_sample(rows); second, _ = _stratified_sample(rows)
    assert first == second and len(first) == 30
    assert all(row[field] == "" for row in first for field in MANUAL_FIELDS)
    assert {"first_row", "last_row", "final_table_page"} <= {category for row in first for category in row["sample_categories"].split("|")}


@pytest.mark.integration
def test_april_schema_and_table_range():
    source = resolve_source(SOURCE_ID, MANIFEST, ROOT)
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    result = detect_schema(source.path, config)
    pages = [item["pdf_page_index"] for item in result.table_contexts if item["context_type"] == "TABLE_DATA"]
    assert result.detected_schema == "PAIMANA_V2" and result.confidence == "HIGH"
    assert pages == EXPECTED_DATA_PAGES
    with pdfplumber.open(str(source.path)) as pdf:
        assert len(pdf.pages[54].extract_tables()) == 1


def test_april_work_did_not_overwrite_may_or_june():
    for relative, expected in FROZEN.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
