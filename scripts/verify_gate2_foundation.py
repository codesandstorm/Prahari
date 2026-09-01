"""Read-only production verification for the Gate 2 foundation."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.extraction.pdf_inspector import compute_sha256, inspect_pdf
from src.extraction.schema_detector import detect_schema
from src.pipeline.source_registry import (
    SourceRegistryError, load_manifest, multipart_overlap_warnings, resolve_source, validate_manifest,
)
from src.utils.safe_io import UnsafeWritePathError, safe_destination
from src.validation.provenance import (
    validate_empty_provenance_registry,
    validate_provenance_record,
    validate_provenance_registry,
)


def schema_config() -> dict:
    """Schema rules mirrored from config.yaml for dependency-minimal verification."""
    return {"schema_versions": {
        "PAIMANA_V2": {"rules": [{
            "name": "paimana_v2_dual_identity",
            "all_of": ["Legacy OCMS Code", "PMGID"],
            "confidence": "HIGH",
        }]},
        "PAIMANA_V1": {"rules": [{
            "name": "paimana_v1_project_code_column",
            "all_of": ["Project Code"],
            "any_of": ["Project Assessment, Infrastructure Monitoring", "PAIMANA"],
            "confidence": "HIGH",
        }]},
        "OCMS": {"rules": [{
            "name": "ocms_primary_rule", "all_of": ["OCMS"],
            "any_of": ["Online Computerised Monitoring System", "Original Cost", "Anticipated Cost", "Date of Commissioning"],
            "confidence": "HIGH",
        }]},
        "LEGACY": {"rules": [{
            "name": "legacy_doa_doc_pair", "all_of": ["DOA", "DOC"], "confidence": "HIGH",
        }]},
    }}


def main() -> int:
    checks = 0
    manifest_path = REPO_ROOT / "data/metadata/source_manifest.csv"
    rows = load_manifest(manifest_path)
    manifest_errors = validate_manifest(rows)
    if manifest_errors:
        raise AssertionError(manifest_errors)
    checks += 1
    source = resolve_source("SRC-2026-06", manifest_path, REPO_ROOT)
    for rejected in ("SRC-2026-07-DUP", "SRC-2026-07-MISSING"):
        try:
            resolve_source(rejected, manifest_path, REPO_ROOT)
        except SourceRegistryError:
            pass
        else:
            raise AssertionError(f"ineligible source resolved: {rejected}")
    checks += 3

    for unsafe in ("data/raw/x", "outputs/../data/raw/x", "DATA/RAW/x", REPO_ROOT / "data/raw/x"):
        try:
            safe_destination(unsafe, REPO_ROOT)
        except UnsafeWritePathError:
            checks += 1
        else:
            raise AssertionError(f"raw destination accepted: {unsafe}")
    safe_destination(REPO_ROOT / "data/raw_material/x", REPO_ROOT)
    checks += 1

    partial = detect_schema(
        Path("unused.pdf"), schema_config(),
        _extract_fn=lambda path, limit: [(1, "All Ongoing Projects Project Name Sl.No PMGID")],
    )
    assert partial.detected_schema == "UNKNOWN_SCHEMA" and partial.candidate_schema == "PAIMANA_V2"
    conflict_text = (
        "All Ongoing Projects Project Name Sl.No Project Code PAIMANA "
        "Legacy OCMS Code PMGID OCMS Original Cost"
    )
    conflict = detect_schema(
        Path("unused.pdf"), schema_config(), _extract_fn=lambda path, limit: [(1, conflict_text)]
    )
    assert conflict.detected_schema == "CONFLICTING_SCHEMA"
    checks += 2

    schema = detect_schema(source.path, schema_config())
    data_pages = [c for c in schema.table_contexts if c["context_type"] == "TABLE_DATA"]
    representatives = [c for c in data_pages if c.get("representative")]
    assert schema.detected_schema == "PAIMANA_V2", schema.to_dict()
    assert [c["pdf_page_index"] for c in representatives] == [59, 109, 159]
    checks += 2

    inspection = inspect_pdf(source.path, repo_root=REPO_ROOT, known_table_pages=[59, 109, 159])
    assert inspection.document_text_extractable == "YES"
    assert inspection.table_text_extractable == "YES"
    assert inspection.table_page_text_status in {"STRUCTURED_TEXT", "TEXT_ONLY"}
    assert not inspection.page_errors
    assert compute_sha256(source.path) == source.sha256
    provenance_path = REPO_ROOT / "data/metadata/provenance.csv"
    extracted_paths = sorted((REPO_ROOT / "data/extracted/ongoing").glob("ongoing_*.csv"))
    if extracted_paths:
        import csv
        provenance_rows = 0
        for extracted_path in extracted_paths:
            with extracted_path.open(encoding="utf-8", newline="") as handle:
                provenance_rows += sum(1 for _ in csv.DictReader(handle))
        assert validate_provenance_registry(
            provenance_path, manifest_path, expected_rows=provenance_rows
        ) == []
    else:
        provenance_rows = 0
        assert validate_empty_provenance_registry(provenance_path) == []
    checks += 6

    valid_record = {
        "source_id": source.source_id, "source_sha256": source.sha256,
        "pdf_page_index": 59, "source_table": "Table 6: All Ongoing Projects",
        "extraction_method": "pdfplumber_table", "extractor_version": "verification:1",
        "raw_row_locator": "pdf_page_index=59,row_index=1",
    }
    assert validate_provenance_record(valid_record, manifest_path) == []
    bad_hash = dict(valid_record, source_sha256="0" * 64)
    assert any("does not match" in e for e in validate_provenance_record(bad_hash, manifest_path))
    unknown = dict(valid_record, source_id="UNKNOWN")
    assert any("unknown" in e for e in validate_provenance_record(unknown, manifest_path))
    checks += 3

    duplicate = deepcopy(rows[4])
    duplicate.update(source_id="DUP-PART", source_part="02")
    assert any("duplicate hash within multipart group" in e for e in validate_manifest(rows + [duplicate]))
    assert multipart_overlap_warnings([
        {"source_group_id": "G", "source_id": "P1", "raw_observation_identity": "K"},
        {"source_group_id": "G", "source_id": "P2", "raw_observation_identity": "K"},
    ])
    checks += 2

    print(json.dumps({
        "source_id": source.source_id,
        "filename": source.filename,
        "sha256": source.sha256,
        "report_month": f"{source.report_year:04d}-{source.report_month:02d}",
        "schema": schema.detected_schema,
        "schema_confidence": schema.confidence,
        "table_heading_pdf_page_index": 58,
        "table_data_pdf_page_indices": [data_pages[0]["pdf_page_index"], data_pages[-1]["pdf_page_index"]],
        "representative_pdf_page_indices": [c["pdf_page_index"] for c in representatives],
        "representative_printed_page_numbers": [c["printed_page_number"] for c in representatives],
        "table_page_text_status": inspection.table_page_text_status,
        "provenance_rows": provenance_rows,
        "manifest_rows": len(rows),
        "production_checks_passed": checks,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
