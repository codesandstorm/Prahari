from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber
import pytest
import yaml

from src.extraction.extractor_paimana import classify_non_project_row
from src.extraction.extractor_paimana_may import (
    EXPECTED_DATA_PAGES,
    SOURCE_ID,
    parse_may_project_row,
)
from src.extraction.schema_detector import detect_schema
from src.pipeline.source_registry import resolve_source

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/metadata/source_manifest.csv"
MAY_SHA = "480d98632cd1b1d4fe70b58a5a753924b2735b0135e7c8507c1ec05ff2ddf005"
FROZEN_JUNE_OUTPUT_SHA = "bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9"


def valid_may_row() -> list[str]:
    return [
        "1",
        "Wrapped May project\n(Agency [Unit])\n(612786)\n(N04000106) (-)",
        "Andhra Pradesh",
        "03/2023\n(01/2024)",
        "01/2026\n(07/2026)",
        "265.91\n(265.91)",
        "142.62",
        "70",
    ]


def parse(row: list[str] | None = None):
    return parse_may_project_row(
        row or valid_may_row(), source_sha256=MAY_SHA,
        pdf_page_index=54, printed_page_number=53, table_index=0, row_index=3,
    )


def test_may_source_resolves_canonically():
    source = resolve_source(SOURCE_ID, MANIFEST, ROOT)
    assert source.filename == "FlashReport_2026_05.pdf"
    assert source.sha256 == MAY_SHA
    assert (source.report_year, source.report_month) == (2026, 5)


def test_valid_wrapped_may_row_retains_provenance():
    record = parse()
    assert record["project_name_raw"] == "Wrapped May project"
    assert record["agency_raw"] == "Agency [Unit]"
    assert record["legacy_ocms_code_raw"] == "N04000106"
    assert record["pmgid_raw"] == "-"
    assert record["source_id"] == SOURCE_ID
    assert record["pdf_page_index"] == 54
    assert record["printed_page_number"] == 53
    assert record["raw_row_locator"].endswith("row_index=3")


def test_may_single_parenthesized_doc_does_not_shift_fields():
    row = valid_may_row()
    row[4] = "(-)"
    record = parse(row)
    assert record["original_target_doc_raw"] == ""
    assert record["revised_doc_raw"] == "-"
    assert record["doc_cell_raw"] == "(-)"
    assert record["original_cost_raw"] == "265.91"


@pytest.mark.parametrize(("row", "kind"), [
    (["Sl.No", "Project Name", "", "", "", "", "", ""], "REPEATED_HEADER"),
    (["", "Total (26)", "", "", "", "", "", ""], "TOTAL"),
])
def test_may_structural_rows_are_rejected(row, kind):
    assert classify_non_project_row(row) == kind


@pytest.mark.integration
def test_real_may_table_discovery_and_project_parse():
    source = resolve_source(SOURCE_ID, MANIFEST, ROOT)
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    schema = detect_schema(source.path, config)
    pages = [
        item["pdf_page_index"] for item in schema.table_contexts
        if item["context_type"] == "TABLE_DATA"
    ]
    assert schema.detected_schema == "PAIMANA_V2"
    assert schema.confidence == "HIGH"
    assert pages == EXPECTED_DATA_PAGES
    with pdfplumber.open(str(source.path)) as pdf:
        table = pdf.pages[pages[0] - 1].extract_tables()[0]
    row_index, row = next(
        (index, row) for index, row in enumerate(table)
        if row[0] and row[0].strip().isdigit()
    )
    record = parse_may_project_row(
        row, source_sha256=source.sha256, pdf_page_index=pages[0],
        printed_page_number=pages[0] - 1, table_index=0, row_index=row_index,
    )
    assert record["source_id"] == SOURCE_ID
    assert record["project_code_raw"]


def test_rejected_and_missing_sources_cannot_resolve():
    for source_id in ("SRC-2026-07-DUP", "SRC-2026-07-MISSING"):
        with pytest.raises(Exception):
            resolve_source(source_id, MANIFEST, ROOT)


def test_frozen_june_output_is_unchanged():
    digest = hashlib.sha256(
        (ROOT / "data/extracted/ongoing/ongoing_2026_06.csv").read_bytes()
    ).hexdigest()
    assert digest == FROZEN_JUNE_OUTPUT_SHA
