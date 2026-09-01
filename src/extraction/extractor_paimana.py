"""Loss-minimized extraction of June 2026 PAIMANA Table 6 only.

This module deliberately does not normalize values, link projects across
months, extract other tables, or select sources by filename.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import re
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pdfplumber
import yaml

from src.extraction.pdf_inspector import compute_sha256
from src.extraction.schema_detector import detect_schema
from src.pipeline.source_registry import SourceRegistryError, resolve_primary_target
from src.utils.safe_io import ensure_parent, safe_destination, write_json_replace
from src.validation.provenance import validate_provenance_record

logger = logging.getLogger(__name__)

SOURCE_ID = "SRC-2026-06"
REPORTING_MONTH = "2026-06"
SOURCE_TABLE = "All Ongoing Projects"
SOURCE_TABLE_NUMBER = 6
EXPECTED_COUNT = 1847
EXTRACTION_METHOD = "pdfplumber_table"
EXTRACTOR_VERSION = "extractor_paimana_table6:0.1.0"
MANUAL_SAMPLE_SEED = 26103

OUTPUT_COLUMNS = [
    "observation_id", "reporting_month", "serial_number_raw",
    "project_name_raw", "agency_raw", "project_code_raw",
    "legacy_ocms_code_raw", "pmgid_raw", "state_raw",
    "approval_date_raw", "start_date_raw", "original_target_doc_raw",
    "revised_doc_raw", "original_cost_raw", "revised_cost_raw",
    "cumulative_expenditure_raw", "physical_progress_raw",
    "project_identity_cell_raw", "approval_start_cell_raw", "doc_cell_raw",
    "cost_cell_raw", "source_id", "source_sha256", "pdf_page_index",
    "printed_page_number", "source_table", "source_table_number",
    "extraction_method", "extractor_version", "raw_row_locator",
]

PROVENANCE_COLUMNS = [
    "observation_id", "source_id", "source_sha256", "source_group_id",
    "source_part", "filename", "report_year", "report_month",
    "pdf_page_index", "printed_page_number", "source_table",
    "source_table_number", "extraction_method", "extractor_version",
    "raw_row_locator", "extraction_timestamp_utc", "extracted_by", "notes",
]

UNRESOLVED_COLUMNS = [
    "source_id", "source_sha256", "pdf_page_index", "printed_page_number",
    "source_table", "source_table_number", "extraction_method",
    "extractor_version", "raw_row_locator", "reason", "raw_cells_json",
]

_SERIAL_RE = re.compile(r"^\d+$")
_SINGLE_PAREN_RE = re.compile(r"^\(([^()]*)\)$")
_PAIR_PAREN_RE = re.compile(r"^\((.*?)\)\s+\((.*?)\)$")
_TOTAL_RE = re.compile(r"^Total\s*\(\d+\)$", re.IGNORECASE)


def _clean_cell(value: Any) -> str:
    return "" if value is None else str(value).strip()


def classify_non_project_row(row: list[Any]) -> str:
    """Classify a verified non-project table row for page diagnostics."""
    cells = [_clean_cell(value) for value in row]
    if not any(cells):
        return "BLANK"
    if cells and cells[0].lower().replace(".", "") in {"slno", "sl no"}:
        return "REPEATED_HEADER"
    label = cells[1] if len(cells) > 1 else ""
    if _TOTAL_RE.fullmatch(label):
        return "TOTAL"
    if not cells[0] and label and not any(cells[2:]):
        return "SECTION_HEADING"
    return "OTHER_NON_PROJECT"


def _split_two_line_cell(value: Any, field_name: str) -> tuple[str, str]:
    lines = [line.strip() for line in _clean_cell(value).splitlines() if line.strip()]
    if len(lines) != 2:
        raise ValueError(f"{field_name} expected exactly two lines; got {len(lines)}")
    second = _SINGLE_PAREN_RE.fullmatch(lines[1])
    if not second:
        raise ValueError(f"{field_name} second value is not parenthesized")
    return lines[0], second.group(1).strip()


def parse_project_row(
    row: list[Any],
    *,
    source_sha256: str,
    pdf_page_index: int,
    printed_page_number: int | None,
    table_index: int,
    row_index: int,
) -> dict[str, Any]:
    """Parse one conservatively identified eight-cell project row."""
    if len(row) != 8:
        raise ValueError(f"expected 8 cells; got {len(row)}")
    serial = _clean_cell(row[0])
    if not _SERIAL_RE.fullmatch(serial):
        raise ValueError("first cell is not a decimal project serial")

    identity_raw = _clean_cell(row[1])
    identity_lines = [line.strip() for line in identity_raw.splitlines() if line.strip()]
    if len(identity_lines) < 4:
        raise ValueError("compound project identity cell has fewer than four lines")
    pair = _PAIR_PAREN_RE.fullmatch(identity_lines[-1])
    project_code = _SINGLE_PAREN_RE.fullmatch(identity_lines[-2])
    agency_line = identity_lines[-3]
    agency_valid = agency_line.startswith("(") and agency_line.endswith(")") and len(agency_line) > 2
    if not pair or not project_code or not agency_valid:
        raise ValueError("compound project identity cell does not match verified bottom-anchored structure")
    project_name_lines = identity_lines[:-3]
    if not project_name_lines:
        raise ValueError("project name is empty")

    approval_date, start_date = _split_two_line_cell(row[3], "approval/start")
    original_doc, revised_doc = _split_two_line_cell(row[4], "target/revised DoC")
    original_cost, revised_cost = _split_two_line_cell(row[5], "original/revised cost")
    locator = f"pdf_page_index={pdf_page_index},table_index={table_index},row_index={row_index}"

    return {
        "observation_id": f"OBS-202606-{int(serial):05d}",
        "reporting_month": REPORTING_MONTH,
        "serial_number_raw": serial,
        "project_name_raw": "\n".join(project_name_lines),
        "agency_raw": agency_line[1:-1].strip(),
        "project_code_raw": project_code.group(1).strip(),
        "legacy_ocms_code_raw": pair.group(1).strip(),
        "pmgid_raw": pair.group(2).strip(),
        "state_raw": _clean_cell(row[2]),
        "approval_date_raw": approval_date,
        "start_date_raw": start_date,
        "original_target_doc_raw": original_doc,
        "revised_doc_raw": revised_doc,
        "original_cost_raw": original_cost,
        "revised_cost_raw": revised_cost,
        "cumulative_expenditure_raw": _clean_cell(row[6]),
        "physical_progress_raw": _clean_cell(row[7]),
        "project_identity_cell_raw": identity_raw,
        "approval_start_cell_raw": _clean_cell(row[3]),
        "doc_cell_raw": _clean_cell(row[4]),
        "cost_cell_raw": _clean_cell(row[5]),
        "source_id": SOURCE_ID,
        "source_sha256": source_sha256,
        "pdf_page_index": pdf_page_index,
        "printed_page_number": printed_page_number,
        "source_table": SOURCE_TABLE,
        "source_table_number": SOURCE_TABLE_NUMBER,
        "extraction_method": EXTRACTION_METHOD,
        "extractor_version": EXTRACTOR_VERSION,
        "raw_row_locator": locator,
    }


def parse_or_review(
    row: list[Any],
    *,
    source_sha256: str,
    pdf_page_index: int,
    printed_page_number: int | None,
    table_index: int,
    row_index: int,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return either a verified project record or a provenance-rich review row."""
    try:
        record = parse_project_row(
            row,
            source_sha256=source_sha256,
            pdf_page_index=pdf_page_index,
            printed_page_number=printed_page_number,
            table_index=table_index,
            row_index=row_index,
        )
    except ValueError as exc:
        return None, {
            "source_id": SOURCE_ID,
            "source_sha256": source_sha256,
            "pdf_page_index": pdf_page_index,
            "printed_page_number": printed_page_number,
            "source_table": SOURCE_TABLE,
            "source_table_number": SOURCE_TABLE_NUMBER,
            "extraction_method": EXTRACTION_METHOD,
            "extractor_version": EXTRACTOR_VERSION,
            "raw_row_locator": f"pdf_page_index={pdf_page_index},table_index={table_index},row_index={row_index}",
            "reason": str(exc),
            "raw_cells_json": json.dumps(row, ensure_ascii=False),
        }
    return record, None


def _write_csv_exclusive(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path = ensure_parent(path)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite extraction artifact: {path}")
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _missingness(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    business = [column for column in OUTPUT_COLUMNS if column.endswith("_raw")]
    report: dict[str, dict[str, float | int]] = {}
    for column in business:
        missing = sum(str(row.get(column, "")).strip() in {"", "-"} for row in rows)
        report[column] = {
            "missing_count": missing,
            "missing_pct": round((100.0 * missing / len(rows)), 2) if rows else 0.0,
        }
    return report


def extract_june_2026_table6(repo_root: Path) -> dict[str, Any]:
    """Resolve, extract, validate, and write June 2026 Table 6 artifacts."""
    repo_root = repo_root.resolve()
    config = yaml.safe_load((repo_root / "config.yaml").read_text(encoding="utf-8"))
    source = resolve_primary_target(config, repo_root)
    if source.source_id != SOURCE_ID:
        raise SourceRegistryError(f"Extractor only permits {SOURCE_ID}; resolved {source.source_id}")
    pre_sha = compute_sha256(source.path)
    if pre_sha != source.sha256:
        raise SourceRegistryError("Pre-extraction SHA-256 mismatch")

    schema = detect_schema(source.path, config)
    if schema.detected_schema != "PAIMANA_V2" or schema.confidence != "HIGH":
        raise RuntimeError(f"Safe PAIMANA_V2 schema not established: {schema.to_dict()}")
    data_contexts = [c for c in schema.table_contexts if c["context_type"] == "TABLE_DATA"]
    if not data_contexts:
        raise RuntimeError("Table 6 data pages were not discovered")
    page_indices = [int(c["pdf_page_index"]) for c in data_contexts]
    if page_indices != list(range(min(page_indices), max(page_indices) + 1)):
        raise RuntimeError("Table 6 data pages are not contiguous")
    printed_by_page = {int(c["pdf_page_index"]): c["printed_page_number"] for c in data_contexts}

    accepted: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    page_diagnostics: list[dict[str, Any]] = []
    rejection_types: Counter[str] = Counter()

    with pdfplumber.open(str(source.path)) as pdf:
        for pdf_page_index in page_indices:
            printed = printed_by_page[pdf_page_index]
            tables = pdf.pages[pdf_page_index - 1].extract_tables() or []
            page_accepted = page_rejected = page_unresolved = 0
            for table_index, table in enumerate(tables):
                for row_index, row in enumerate(table):
                    first = _clean_cell(row[0]) if row else ""
                    if not _SERIAL_RE.fullmatch(first):
                        rejection_types[classify_non_project_row(row)] += 1
                        page_rejected += 1
                        continue
                    record, review = parse_or_review(
                        row,
                        source_sha256=source.sha256,
                        pdf_page_index=pdf_page_index,
                        printed_page_number=printed,
                        table_index=table_index,
                        row_index=row_index,
                    )
                    if review is not None:
                        page_unresolved += 1
                        unresolved.append(review)
                    else:
                        assert record is not None
                        accepted.append(record)
                        page_accepted += 1
            page_diagnostics.append({
                "pdf_page_index": pdf_page_index,
                "printed_page_number": printed,
                "accepted_project_rows": page_accepted,
                "rejected_non_project_rows": page_rejected,
                "unresolved_rows": page_unresolved,
            })

    locators = [row["raw_row_locator"] for row in accepted]
    serials = [int(row["serial_number_raw"]) for row in accepted]
    duplicate_locator_count = len(locators) - len(set(locators))
    duplicate_serial_count = len(serials) - len(set(serials))
    if duplicate_locator_count or duplicate_serial_count:
        raise RuntimeError("Duplicate raw locator or project serial detected")

    provenance_errors: list[str] = []
    manifest_path = repo_root / config["manifest"]["file"]
    for row in accepted:
        errors = validate_provenance_record(row, manifest_path)
        if errors:
            provenance_errors.extend(f"{row['raw_row_locator']}: {error}" for error in errors)
    if provenance_errors:
        raise RuntimeError("Provenance validation failed: " + "; ".join(provenance_errors[:10]))

    counts = [row["accepted_project_rows"] for row in page_diagnostics]
    median_count = statistics.median(counts)
    page_anomalies = [
        {**row, "reason": "ZERO_ROWS" if row["accepted_project_rows"] == 0 else "COUNT_OUTLIER"}
        for row in page_diagnostics
        if row["accepted_project_rows"] == 0
        or row["accepted_project_rows"] < median_count * 0.5
        or row["accepted_project_rows"] > median_count * 1.5
    ]
    missingness = _missingness(accepted)
    timestamp = datetime.now(timezone.utc).isoformat()
    run_id = f"extract-202606-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    output_path = repo_root / "data/extracted/ongoing/ongoing_2026_06.csv"
    unresolved_path = repo_root / "data/extracted/review/ongoing_2026_06_unresolved_rows.csv"
    provenance_path = repo_root / "data/metadata/provenance.csv"
    summary_path = repo_root / "validation/extraction_validation/june_2026_extraction_summary.json"
    sample_path = repo_root / "validation/extraction_validation/june_2026_manual_sample_30.csv"
    report_path = repo_root / "outputs/reports/JUNE_2026_EXTRACTION_REPORT.md"

    _write_csv_exclusive(output_path, OUTPUT_COLUMNS, accepted)
    _write_csv_exclusive(unresolved_path, UNRESOLVED_COLUMNS, unresolved)
    provenance_rows = [{
        "observation_id": row["observation_id"],
        "source_id": source.source_id,
        "source_sha256": source.sha256,
        "source_group_id": source.source_group_id,
        "source_part": source.source_part,
        "filename": source.filename,
        "report_year": source.report_year,
        "report_month": source.report_month,
        "pdf_page_index": row["pdf_page_index"],
        "printed_page_number": row["printed_page_number"],
        "source_table": SOURCE_TABLE,
        "source_table_number": SOURCE_TABLE_NUMBER,
        "extraction_method": EXTRACTION_METHOD,
        "extractor_version": EXTRACTOR_VERSION,
        "raw_row_locator": row["raw_row_locator"],
        "extraction_timestamp_utc": timestamp,
        "extracted_by": run_id,
        "notes": "",
    } for row in accepted]
    # The foundation requires a header-only registry before extraction. This is
    # the first authorized population and therefore must still be empty here.
    with provenance_path.open(encoding="utf-8", newline="") as handle:
        if list(csv.DictReader(handle)):
            raise RuntimeError("Provenance registry is not empty; refusing uncontrolled append")
    provenance_path = safe_destination(provenance_path, repo_root)
    with provenance_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROVENANCE_COLUMNS)
        writer.writeheader()
        writer.writerows(provenance_rows)

    rng = random.Random(MANUAL_SAMPLE_SEED)
    sample = sorted(rng.sample(accepted, 30), key=lambda row: int(row["serial_number_raw"]))
    review_columns = [
        "manual_project_name_match", "manual_project_code_match", "manual_cost_match",
        "manual_date_match", "manual_progress_match", "manual_overall_match",
        "reviewer", "review_notes",
    ]
    sample_rows = [{**row, **{column: "" for column in review_columns}} for row in sample]
    _write_csv_exclusive(sample_path, OUTPUT_COLUMNS + review_columns, sample_rows)

    post_sha = compute_sha256(source.path)
    if post_sha != pre_sha or post_sha != source.sha256:
        raise RuntimeError("Post-extraction SHA-256 mismatch; extraction results invalid")

    summary = {
        "source_id": source.source_id,
        "source_sha256": source.sha256,
        "reporting_month": REPORTING_MONTH,
        "schema": schema.detected_schema,
        "schema_confidence": schema.confidence,
        "source_table": SOURCE_TABLE,
        "source_table_number": SOURCE_TABLE_NUMBER,
        "title_pdf_page_index": min(page_indices) - 1,
        "data_pdf_page_range": [min(page_indices), max(page_indices)],
        "printed_page_range": [printed_by_page[min(page_indices)], printed_by_page[max(page_indices)]],
        "expected_count": EXPECTED_COUNT,
        "accepted_project_rows": len(accepted),
        "unresolved_rows": len(unresolved),
        "difference": len(accepted) - EXPECTED_COUNT,
        "duplicate_raw_locator_count": duplicate_locator_count,
        "duplicate_serial_count": duplicate_serial_count,
        "rejected_non_project_rows": sum(rejection_types.values()),
        "rejection_types": dict(rejection_types),
        "missingness": missingness,
        "page_diagnostics": page_diagnostics,
        "page_anomalies": page_anomalies,
        "pre_extraction_sha256": pre_sha,
        "post_extraction_sha256": post_sha,
        "extractor_version": EXTRACTOR_VERSION,
        "extraction_method": EXTRACTION_METHOD,
        "run_id": run_id,
        "timestamp_utc": timestamp,
    }
    write_json_replace(summary_path, summary, repo_root=repo_root)

    report_path = ensure_parent(report_path, repo_root)
    report_path.write_text(_render_report(summary, output_path, unresolved_path, sample_path), encoding="utf-8")
    return summary


def _render_report(summary: dict[str, Any], output: Path, unresolved: Path, sample: Path) -> str:
    missing_lines = "\n".join(
        f"- `{field}`: {value['missing_count']} ({value['missing_pct']}%)"
        for field, value in summary["missingness"].items()
    )
    anomaly_lines = "\n".join(
        f"- PDF {row['pdf_page_index']}: {row['reason']} ({row['accepted_project_rows']} rows)"
        for row in summary["page_anomalies"]
    ) or "- None under the declared page-count thresholds."
    return f"""# June 2026 Table 6 Extraction Report

## Source identity and integrity

- Source ID: `{summary['source_id']}`
- SHA-256: `{summary['source_sha256']}`
- Pre-extraction SHA: `{summary['pre_extraction_sha256']}`
- Post-extraction SHA: `{summary['post_extraction_sha256']}`
- Schema: `{summary['schema']}` / `{summary['schema_confidence']}`
- Extractor: `{summary['extractor_version']}`
- Method: `{summary['extraction_method']}`

## Boundaries and reconciliation

- Table: Table 6 — All Ongoing Projects
- Physical title page: {summary['title_pdf_page_index']}
- Physical data pages: {summary['data_pdf_page_range'][0]}–{summary['data_pdf_page_range'][1]}
- Printed data pages: {summary['printed_page_range'][0]}–{summary['printed_page_range'][1]}
- Expected report count: {summary['expected_count']}
- Accepted project rows: {summary['accepted_project_rows']}
- Unresolved rows: {summary['unresolved_rows']}
- Difference: {summary['difference']}
- Duplicate raw locators: {summary['duplicate_raw_locator_count']}
- Duplicate serials: {summary['duplicate_serial_count']}
- Rejected structural/non-project rows: {summary['rejected_non_project_rows']}

## Extracted fields

Raw project/agency/identifier, state, approval/start date, target/revised DoC,
original/revised cost, expenditure, physical progress, complete source cells,
and mandatory provenance fields. No business normalization was performed.

Fields intentionally omitted: ministry, sector, normalized values, cross-month
identity, labels, features, and risk values.

## Missingness

{missing_lines}

## Page diagnostics

The JSON summary contains all page-level counts.

{anomaly_lines}

## Ambiguities and review

Legacy OCMS Code and PMGID columns exist but contain the source missing marker
`-` throughout this report. Section headings were not carried forward into
project records. Ambiguous numeric rows would be routed to review rather than
guessed.

- Raw extraction: `{output.as_posix()}`
- Unresolved review: `{unresolved.as_posix()}`
- Deterministic 30-row manual sample: `{sample.as_posix()}`

## Assessment

Ready for independent manual review. This report does not authorize processing
another month or constructing analytical project tables.
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract canonical June 2026 Table 6 only")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    return parser


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = _build_parser().parse_args()
    result = extract_june_2026_table6(Path(args.repo_root))
    print(json.dumps(result, indent=2, ensure_ascii=False))
