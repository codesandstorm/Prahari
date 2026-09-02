"""Controlled extraction of April 2026 PAIMANA Table 6 only."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pdfplumber
import yaml

from src.extraction.extractor_paimana import OUTPUT_COLUMNS, PROVENANCE_COLUMNS, UNRESOLVED_COLUMNS, classify_non_project_row
from src.extraction.extractor_paimana_may import parse_may_project_row
from src.extraction.pdf_inspector import compute_sha256
from src.extraction.schema_detector import detect_schema
from src.pipeline.source_registry import resolve_source
from src.utils.safe_io import ensure_parent, safe_destination, write_json_replace
from src.validation.provenance import validate_provenance_record

SOURCE_ID = "SRC-2026-04"
SOURCE_SHA256 = "90a6959e976da6928440efdea9c68847d1178356e4c0ebd078c51026ddb118d5"
REPORTING_MONTH = "2026-04"
EXPECTED_COUNT = 1981
EXPECTED_DATA_PAGES = list(range(55, 163))
EXTRACTOR_VERSION = "extractor_paimana_april_table6:0.1.0"
EXTRACTION_METHOD = "pdfplumber_table"
SOURCE_TABLE = "All Ongoing Projects"
SOURCE_TABLE_NUMBER = 6
SAMPLE_SEED = 26103
MANUAL_FIELDS = ["manual_row_confirmed", "manual_project_identity_confirmed", "manual_fields_confirmed", "manual_provenance_confirmed", "reviewer", "review_notes"]


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def parse_april_project_row(row: list[Any], **context: Any) -> dict[str, Any]:
    """Reuse the verified row shape while replacing all month-specific identity."""
    record = parse_may_project_row(row, **context)
    serial = int(record["serial_number_raw"])
    record.update({
        "observation_id": f"OBS-202604-{serial:05d}",
        "reporting_month": REPORTING_MONTH,
        "source_id": SOURCE_ID,
        "extractor_version": EXTRACTOR_VERSION,
    })
    return record


def _decimal(value: str) -> Decimal | None:
    value = value.strip().replace(",", "")
    if value in {"", "-", "NA"}:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _write(path: Path, fields: list[str], rows: list[dict[str, Any]], root: Path) -> None:
    path = ensure_parent(path, root)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite April artifact: {path}")
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _missing(rows: list[dict[str, Any]], field: str) -> int:
    return sum(str(row[field]).strip() in {"", "-", "NA"} for row in rows)


def _date_audit(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    pattern = re.compile(r"^(0[1-9]|1[0-2])/\d{4}$")
    missing = _missing(rows, field)
    malformed = sum(str(row[field]).strip() not in {"", "-", "NA"} and not pattern.fullmatch(str(row[field]).strip()) for row in rows)
    return {"parsed": len(rows) - missing - malformed, "missing": missing, "ambiguous": 0, "malformed": malformed}


def _numeric_audit(rows: list[dict[str, Any]], field: str, progress: bool = False) -> dict[str, Any]:
    values = [_decimal(str(row[field])) for row in rows]
    parsed = [value for value in values if value is not None]
    missing = _missing(rows, field)
    malformed = len(rows) - len(parsed) - missing
    result: dict[str, Any] = {"parsed": len(parsed), "missing": missing, "malformed": malformed, "negative": sum(value < 0 for value in parsed)}
    if progress:
        result.update({"min": str(min(parsed)) if parsed else None, "max": str(max(parsed)) if parsed else None, "outside_0_100": sum(value < 0 or value > 100 for value in parsed)})
    return result


def _stratified_sample(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    rng = random.Random(SAMPLE_SEED)
    chosen: dict[str, dict[str, Any]] = {}
    coverage: dict[str, list[str]] = {}

    def pick(category: str, candidates: list[dict[str, Any]], count: int = 1) -> None:
        available = [row for row in candidates if row["observation_id"] not in chosen]
        for row in (available[:count] if category in {"first_row", "last_row"} else rng.sample(available, min(count, len(available)))):
            chosen[row["observation_id"]] = row
            coverage.setdefault(row["observation_id"], []).append(category)

    ordered = sorted(rows, key=lambda row: int(row["serial_number_raw"]))
    pick("first_row", ordered[:1]); pick("last_row", ordered[-1:])
    pick("early_pages", [r for r in rows if int(r["pdf_page_index"]) <= 70], 4)
    pick("middle_pages", [r for r in rows if 100 <= int(r["pdf_page_index"]) <= 120], 4)
    pick("late_pages", [r for r in rows if int(r["pdf_page_index"]) >= 150], 4)
    pick("missing_revised_doc", [r for r in rows if r["revised_doc_raw"] == "-"], 3)
    pick("legacy_and_pmgid_present", [r for r in rows if r["legacy_ocms_code_raw"] != "-" and r["pmgid_raw"] != "-"], 3)
    pick("legacy_or_pmgid_missing", [r for r in rows if r["legacy_ocms_code_raw"] == "-" or r["pmgid_raw"] == "-"], 3)
    pick("zero_progress", [r for r in rows if _decimal(r["physical_progress_raw"]) == 0], 2)
    pick("high_progress", [r for r in rows if (_decimal(r["physical_progress_raw"]) or Decimal(-1)) >= 95], 2)
    pick("final_table_page", [r for r in rows if int(r["pdf_page_index"]) == 162], 2)
    pick("fill_seeded", rows, 30 - len(chosen))
    sample = sorted(chosen.values(), key=lambda row: int(row["serial_number_raw"]))[:30]
    return [{**row, "sample_categories": "|".join(coverage.get(row["observation_id"], ["fill_seeded"])), **{field: "" for field in MANUAL_FIELDS}} for row in sample], coverage


def extract_april_2026_table6(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    manifest = root / config["manifest"]["file"]
    source = resolve_source(SOURCE_ID, manifest, root)
    if (source.report_year, source.report_month, source.sha256) != (2026, 4, SOURCE_SHA256):
        raise RuntimeError("April source registry contract mismatch")
    pre_sha = compute_sha256(source.path)
    if pre_sha != SOURCE_SHA256:
        raise RuntimeError("April source hash mismatch")
    schema = detect_schema(source.path, config)
    contexts = [item for item in schema.table_contexts if item["context_type"] == "TABLE_DATA"]
    pages = [int(item["pdf_page_index"]) for item in contexts]
    if schema.detected_schema != "PAIMANA_V2" or schema.confidence != "HIGH" or pages != EXPECTED_DATA_PAGES:
        raise RuntimeError("April schema or Table 6 boundary contract failed")
    printed = {int(item["pdf_page_index"]): int(item["printed_page_number"]) for item in contexts}
    accepted: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    structural: Counter[str] = Counter()
    page_diagnostics = []
    with pdfplumber.open(str(source.path)) as pdf:
        for page_index in pages:
            tables = pdf.pages[page_index - 1].extract_tables() or []
            if len(tables) != 1:
                raise RuntimeError(f"April page {page_index} expected one table; found {len(tables)}")
            page_counts: Counter[str] = Counter()
            for table_index, table in enumerate(tables):
                for row_index, row in enumerate(table):
                    locator = f"pdf_page_index={page_index},table_index={table_index},row_index={row_index}"
                    if not (_clean(row[0]) if row else "").isdigit():
                        kind = classify_non_project_row(row)
                        structural[kind] += 1; page_counts[kind] += 1
                        continue
                    try:
                        accepted.append(parse_april_project_row(row, source_sha256=source.sha256, pdf_page_index=page_index, printed_page_number=printed[page_index], table_index=table_index, row_index=row_index))
                        page_counts["PROJECT_ROW"] += 1
                    except ValueError as exc:
                        unresolved.append({"source_id": SOURCE_ID, "source_sha256": source.sha256, "pdf_page_index": page_index, "printed_page_number": printed[page_index], "source_table": SOURCE_TABLE, "source_table_number": SOURCE_TABLE_NUMBER, "extraction_method": EXTRACTION_METHOD, "extractor_version": EXTRACTOR_VERSION, "raw_row_locator": locator, "reason": str(exc), "raw_cells_json": json.dumps(row, ensure_ascii=False)})
                        page_counts["UNRESOLVED"] += 1
            page_diagnostics.append({"pdf_page_index": page_index, "printed_page_number": printed[page_index], **dict(page_counts)})
    serials = [int(row["serial_number_raw"]) for row in accepted]
    codes = [row["project_code_raw"] for row in accepted]
    locators = [row["raw_row_locator"] for row in accepted]
    legacy_present = [row["legacy_ocms_code_raw"] for row in accepted if row["legacy_ocms_code_raw"] not in {"", "-", "NA"}]
    pmgid_present = [row["pmgid_raw"] for row in accepted if row["pmgid_raw"] not in {"", "-", "NA"}]
    if unresolved or len(accepted) != EXPECTED_COUNT or serials != list(range(1, EXPECTED_COUNT + 1)):
        raise RuntimeError("April row reconciliation or serial contract failed")
    if len(codes) != len(set(codes)) or any(not code.strip() or code.strip() != code for code in codes):
        raise RuntimeError("April Project Code completeness/uniqueness contract failed")
    if len(locators) != len(set(locators)):
        raise RuntimeError("Duplicate April raw row locator")
    provenance_errors = [error for row in accepted for error in validate_provenance_record(row, manifest)]
    if provenance_errors:
        raise RuntimeError("April provenance validation failed: " + "; ".join(provenance_errors[:5]))
    output = root / "data/extracted/ongoing/ongoing_2026_04.csv"
    unresolved_path = root / "data/extracted/review/ongoing_2026_04_unresolved_rows.csv"
    validation = root / "validation/extraction_validation/april_2026"
    _write(output, OUTPUT_COLUMNS, accepted, root)
    _write(unresolved_path, UNRESOLVED_COLUMNS, unresolved, root)
    timestamp = datetime.now(timezone.utc).isoformat()
    run_id = f"extract-202604-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    provenance_path = safe_destination(root / "data/metadata/provenance.csv", root)
    with provenance_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle); existing = list(reader)
        if reader.fieldnames != PROVENANCE_COLUMNS or any(row["source_id"] == SOURCE_ID for row in existing):
            raise RuntimeError("Provenance registry header mismatch or April already present")
    new_provenance = [{"observation_id": row["observation_id"], "source_id": SOURCE_ID, "source_sha256": source.sha256, "source_group_id": source.source_group_id, "source_part": source.source_part, "filename": source.filename, "report_year": 2026, "report_month": 4, "pdf_page_index": row["pdf_page_index"], "printed_page_number": row["printed_page_number"], "source_table": SOURCE_TABLE, "source_table_number": SOURCE_TABLE_NUMBER, "extraction_method": EXTRACTION_METHOD, "extractor_version": EXTRACTOR_VERSION, "raw_row_locator": row["raw_row_locator"], "extraction_timestamp_utc": timestamp, "extracted_by": run_id, "notes": "AUTOMATED_VALIDATION_COMPLETE_HUMAN_PENDING"} for row in accepted]
    with provenance_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROVENANCE_COLUMNS); writer.writeheader(); writer.writerows(existing + new_provenance)
    sample, _ = _stratified_sample(accepted)
    _write(validation / "april_2026_manual_sample.csv", OUTPUT_COLUMNS + ["sample_categories"] + MANUAL_FIELDS, sample, root)
    date_fields = ["approval_date_raw", "start_date_raw", "original_target_doc_raw", "revised_doc_raw"]
    numeric_fields = ["original_cost_raw", "revised_cost_raw", "cumulative_expenditure_raw"]
    summary = {
        "source_id": SOURCE_ID, "source_sha256": source.sha256, "file_size_bytes": source.path.stat().st_size,
        "page_count": 163, "text_extractable": "YES", "expected_count": EXPECTED_COUNT,
        "count_evidence": {"pdf_page_index": 4, "printed_page_number": 3, "statement": "1981 Ongoing Projects"},
        "title_pdf_page_index": 54, "title_printed_page_number": 53,
        "data_pdf_page_range": [55, 162], "printed_page_range": [54, 161],
        "schema": schema.detected_schema, "schema_confidence": schema.confidence,
        "schema_comparison": "COMPATIBLE_VARIATION", "adapter_decision": "APRIL_SPECIFIC_ADAPTER_REUSING_VERIFIED_MAY_ROW_PARSER",
        "extractor_version": EXTRACTOR_VERSION, "total_raw_table_rows": len(accepted) + sum(structural.values()) + len(unresolved),
        "accepted_project_rows": len(accepted), "structural_counts": dict(structural), "unresolved_rows": len(unresolved),
        "serial_min": min(serials), "serial_max": max(serials), "missing_serials": [], "duplicate_serials": 0, "out_of_order_serials": 0,
        "project_code_missing": 0, "project_code_duplicates": 0, "project_code_malformed": sum(not re.fullmatch(r"\d+", code) for code in codes),
        "legacy_ocms": {"present": len(legacy_present), "missing": _missing(accepted,"legacy_ocms_code_raw"), "unique": len(set(legacy_present)), "duplicate_rows_among_present": len(legacy_present)-len(set(legacy_present))},
        "pmgid": {"present": len(pmgid_present), "missing": _missing(accepted,"pmgid_raw"), "unique": len(set(pmgid_present)), "duplicate_rows_among_present": len(pmgid_present)-len(set(pmgid_present))},
        "date_audit": {field: _date_audit(accepted, field) for field in date_fields},
        "numeric_audit": {field: _numeric_audit(accepted, field) for field in numeric_fields},
        "physical_progress_audit": _numeric_audit(accepted, "physical_progress_raw", True),
        "missing_token_inventory": sorted({str(row[field]).strip() for row in accepted for field in OUTPUT_COLUMNS if field.endswith("_raw") and str(row[field]).strip() in {"", "-", "NA", "()", "(-)"}}),
        "duplicate_raw_row_locators": 0, "provenance_errors": 0, "count_reconciliation": "PASS",
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "source_pre_sha256": pre_sha,
        "source_post_sha256": compute_sha256(source.path), "sample_size": len(sample), "page_diagnostics": page_diagnostics,
    }
    write_json_replace(validation / "april_2026_extraction_summary.json", summary, repo_root=root)
    return summary
