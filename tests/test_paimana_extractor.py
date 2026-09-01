from __future__ import annotations

import inspect
from pathlib import Path

import pdfplumber
import pytest

from src.extraction.extractor_paimana import (
    SOURCE_ID,
    classify_non_project_row,
    parse_or_review,
    parse_project_row,
)
from src.pipeline.source_registry import resolve_source

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/metadata/source_manifest.csv"
SHA = "d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15"


def valid_row():
    return [
        "1",
        "Wrapped project name line one\nline two\n(Agency Name)\n(612786)\n(-) (-)",
        "Andhra Pradesh",
        "03/2023\n(01/2024)",
        "01/2026\n(07/2026)",
        "265.91\n(265.91)",
        "153.62",
        "75",
    ]


def parse(row=None, row_index=3):
    return parse_project_row(
        row or valid_row(), source_sha256=SHA, pdf_page_index=59,
        printed_page_number=58, table_index=0, row_index=row_index,
    )


def test_valid_wrapped_project_row_accepted_with_provenance():
    record = parse()
    assert record["project_name_raw"] == "Wrapped project name line one\nline two"
    assert record["agency_raw"] == "Agency Name"
    assert record["source_id"] == SOURCE_ID
    assert record["source_sha256"] == SHA
    assert record["pdf_page_index"] == 59
    assert record["printed_page_number"] == 58


def test_agency_with_nested_parentheses_is_preserved():
    row = valid_row()
    row[1] = "Project\n(Bharat Coking Coal Limited (BCCL))\n(611864)\n(-) (-)"
    assert parse(row)["agency_raw"] == "Bharat Coking Coal Limited (BCCL)"


@pytest.mark.parametrize(("row", "classification"), [
    (["Sl.No", "Project Name", "", "", "", "", "", ""], "REPEATED_HEADER"),
    (["", "Total (25)", "", "", "", "", "", ""], "TOTAL"),
    (["", "", "", "", "", "", "", ""], "BLANK"),
])
def test_non_project_rows_rejected(row, classification):
    assert classify_non_project_row(row) == classification


def test_missing_business_value_does_not_shift_columns():
    row = valid_row()
    row[7] = ""
    record = parse(row)
    assert record["physical_progress_raw"] == ""
    assert record["cumulative_expenditure_raw"] == "153.62"


def test_malformed_numeric_record_is_sent_to_review():
    row = valid_row()
    row[1] = "Cannot reconstruct identity"
    record, review = parse_or_review(
        row, source_sha256=SHA, pdf_page_index=59,
        printed_page_number=58, table_index=0, row_index=9,
    )
    assert record is None
    assert review is not None
    assert review["raw_row_locator"].endswith("row_index=9")
    assert review["raw_cells_json"]


def test_raw_row_locator_is_deterministic_and_unique_by_row():
    assert parse(row_index=3)["raw_row_locator"] != parse(row_index=4)["raw_row_locator"]


def test_extractor_does_not_accept_arbitrary_source_id_parameter():
    from src.extraction.extractor_paimana import extract_june_2026_table6
    assert "source_id" not in inspect.signature(extract_june_2026_table6).parameters
    with pytest.raises(Exception):
        resolve_source("SRC-2026-07-DUP", MANIFEST, ROOT)


@pytest.mark.integration
def test_real_june_representative_page_yields_provenance_rows():
    source = resolve_source(SOURCE_ID, MANIFEST, ROOT)
    with pdfplumber.open(str(source.path)) as pdf:
        table = pdf.pages[58].extract_tables()[0]  # physical PDF page 59
    numeric = next(row for row in table if row[0] and row[0].strip().isdigit())
    record = parse_project_row(
        numeric, source_sha256=source.sha256, pdf_page_index=59,
        printed_page_number=58, table_index=0, row_index=3,
    )
    assert record["project_code_raw"]
    assert record["source_id"] == SOURCE_ID
    assert record["raw_row_locator"]
