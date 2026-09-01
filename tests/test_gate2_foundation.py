from __future__ import annotations

import csv
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from src.extraction.schema_detector import detect_schema, discover_table_contexts
from src.pipeline.source_registry import (
    SourceRegistryError,
    load_manifest,
    multipart_overlap_warnings,
    resolve_primary_target,
    resolve_source,
    validate_manifest,
)
from src.utils.safe_io import UnsafeWritePathError, safe_destination
from src.validation.provenance import (
    validate_empty_provenance_registry,
    validate_provenance_record,
    validate_provenance_registry,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "metadata" / "source_manifest.csv"


@pytest.fixture(scope="module")
def config():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def test_primary_target_resolves_canonical_june(config):
    source = resolve_primary_target(config, ROOT)
    assert source.source_id == "SRC-2026-06"
    assert source.filename == "FlashReport_2026_06.pdf"
    assert (source.report_year, source.report_month) == (2026, 6)
    assert source.file_status == "CANONICAL"


@pytest.mark.parametrize("source_id", ["SRC-2026-07-DUP", "SRC-2026-07-MISSING"])
def test_ineligible_source_resolution_fails(source_id):
    with pytest.raises(SourceRegistryError, match="not extraction-eligible"):
        resolve_source(source_id, MANIFEST, ROOT)


def test_report_content_config_period_mismatch_rejected(config):
    broken = deepcopy(config)
    broken["extraction"]["primary_target"]["report_month"] = "2026-07"
    with pytest.raises(SourceRegistryError, match="month does not match"):
        resolve_primary_target(broken, ROOT)


def test_safe_destination_allows_normal_and_similar_text(tmp_path):
    assert safe_destination("outputs/report.json", ROOT).is_absolute()
    similar = tmp_path / "data" / "raw_material" / "report.json"
    assert safe_destination(similar, ROOT) == similar.resolve()


@pytest.mark.parametrize("destination", [
    "data/raw/2026/result.json",
    "outputs/../data/raw/2026/result.json",
    "DATA/RAW/2026/result.json",
])
def test_raw_destinations_rejected(destination):
    with pytest.raises(UnsafeWritePathError):
        safe_destination(destination, ROOT)


def test_absolute_raw_destination_rejected():
    with pytest.raises(UnsafeWritePathError):
        safe_destination(ROOT / "data" / "raw" / "result.json", ROOT)


def _rules():
    return {
        "schema_versions": {
            "PAIMANA_V2": {"rules": [{
                "name": "v2", "all_of": ["Legacy OCMS Code", "PMGID"], "confidence": "HIGH"
            }]},
            "PAIMANA_V1": {"rules": [{
                "name": "v1", "all_of": ["Project Code"], "any_of": ["PAIMANA"], "confidence": "HIGH"
            }]},
            "OCMS": {"rules": [{
                "name": "ocms", "all_of": ["OCMS"], "any_of": ["Original Cost"], "confidence": "HIGH"
            }]},
            "LEGACY": {"rules": [{
                "name": "legacy", "all_of": ["DOA", "DOC"], "confidence": "HIGH"
            }]},
        }
    }


def _detect(pages):
    return detect_schema(Path("unused.pdf"), _rules(), _extract_fn=lambda path, limit: pages)


def test_isolated_pmgid_is_candidate_not_production_v2():
    result = _detect([(1, "All Ongoing Projects Project Name Sl.No PMGID")])
    assert result.detected_schema == "UNKNOWN_SCHEMA"
    assert result.candidate_schema == "PAIMANA_V2"


def test_project_code_alone_is_candidate_not_production_v1():
    result = _detect([(1, "All Ongoing Projects Project Name Sl.No Project Code")])
    assert result.detected_schema == "UNKNOWN_SCHEMA"
    assert result.candidate_schema == "PAIMANA_V1"


def test_conflicting_table_evidence_blocks_production_selection():
    text = (
        "All Ongoing Projects Project Name Sl.No Project Code PAIMANA "
        "Legacy OCMS Code PMGID OCMS Original Cost"
    )
    result = _detect([(8, text)])
    assert result.detected_schema == "CONFLICTING_SCHEMA"
    assert set(result.conflicting_schemas) == {"PAIMANA_V2", "OCMS"}


def test_toc_evidence_is_distinguished_from_table_data():
    contexts = discover_table_contexts([
        (2, "Table of Contents All Ongoing Projects ........ 57"),
        (58, "Table 6: All Ongoing Projects Page 57"),
        (59, "All Ongoing Projects Project Name Sl.No Project Code PMGID Page 58"),
    ])
    assert [item["context_type"] for item in contexts] == ["TOC", "TABLE_HEADING", "TABLE_DATA"]
    assert contexts[2]["pdf_page_index"] == 59
    assert contexts[2]["printed_page_number"] == 58


def test_provenance_registry_matches_pipeline_lifecycle():
    provenance = ROOT / "data/metadata/provenance.csv"
    extracted = ROOT / "data/extracted/ongoing/ongoing_2026_06.csv"
    if not extracted.exists():
        assert validate_empty_provenance_registry(provenance) == []
        return
    with extracted.open(encoding="utf-8", newline="") as handle:
        expected_rows = sum(1 for _ in csv.DictReader(handle))
    assert validate_provenance_registry(
        provenance, MANIFEST, expected_rows=expected_rows
    ) == []


def _valid_provenance():
    source = resolve_source("SRC-2026-06", MANIFEST, ROOT)
    return {
        "source_id": source.source_id,
        "source_sha256": source.sha256,
        "pdf_page_index": 59,
        "source_table": "Table 6: All Ongoing Projects",
        "extraction_method": "pdfplumber_table",
        "extractor_version": "future-extractor:0.1.0",
        "raw_row_locator": "pdf_page_index=59,row_index=1",
    }


def test_provenance_validator_accepts_valid_source():
    assert validate_provenance_record(_valid_provenance(), MANIFEST) == []


def test_provenance_validator_rejects_unknown_source():
    record = _valid_provenance()
    record["source_id"] = "SRC-DOES-NOT-EXIST"
    assert any("unknown" in error for error in validate_provenance_record(record, MANIFEST))


def test_provenance_validator_rejects_hash_mismatch():
    record = _valid_provenance()
    record["source_sha256"] = "0" * 64
    assert any("does not match" in error for error in validate_provenance_record(record, MANIFEST))


def test_manifest_rejects_duplicate_group_part():
    rows = load_manifest(MANIFEST)
    duplicate = deepcopy(rows[0])
    duplicate["source_id"] = "SRC-DUPLICATE-PART"
    duplicate["sha256"] = "1" * 64
    assert any("duplicate source group/part" in error for error in validate_manifest(rows + [duplicate]))


def test_manifest_rejects_mismatched_group_period():
    rows = load_manifest(MANIFEST)
    duplicate = deepcopy(rows[0])
    duplicate.update(source_id="SRC-PERIOD", source_part="02", report_month="7", sha256="2" * 64)
    assert any("mismatched reporting period" in error for error in validate_manifest(rows + [duplicate]))


def test_manifest_flags_duplicate_multipart_hash():
    rows = load_manifest(MANIFEST)
    first = deepcopy(rows[4])
    second = deepcopy(first)
    second.update(source_id="SRC-OTHER-PART", source_part="02")
    assert any("duplicate hash within multipart group" in error for error in validate_manifest(rows + [second]))


def test_overlap_warning_keeps_source_parts_traceable():
    warnings = multipart_overlap_warnings([
        {"source_group_id": "FR-X", "source_id": "SRC-P01", "raw_observation_identity": "project=7,month=2026-06"},
        {"source_group_id": "FR-X", "source_id": "SRC-P02", "raw_observation_identity": "project=7,month=2026-06"},
    ])
    assert len(warnings) == 1


@pytest.mark.integration
def test_real_june_table_discovery_and_schema(config):
    source = resolve_primary_target(config, ROOT)
    result = detect_schema(source.path, config)
    assert result.detected_schema == "PAIMANA_V2"
    assert result.confidence == "HIGH"
    data_pages = [item for item in result.table_contexts if item["context_type"] == "TABLE_DATA"]
    representatives = [item for item in data_pages if item.get("representative")]
    assert data_pages[0]["pdf_page_index"] == 59
    assert data_pages[-1]["pdf_page_index"] == 159
    assert [item["pdf_page_index"] for item in representatives] == [59, 109, 159]
