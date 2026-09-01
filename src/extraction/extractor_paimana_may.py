"""Controlled extraction of May 2026 PAIMANA Table 6 only."""

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

from src.extraction.extractor_paimana import (
    OUTPUT_COLUMNS,
    PROVENANCE_COLUMNS,
    UNRESOLVED_COLUMNS,
    classify_non_project_row,
)
from src.extraction.pdf_inspector import compute_sha256
from src.extraction.schema_detector import detect_schema
from src.pipeline.source_registry import SourceRegistryError, resolve_source
from src.utils.safe_io import ensure_parent, safe_destination, write_json_replace
from src.validation.provenance import validate_provenance_record

logger = logging.getLogger(__name__)

SOURCE_ID = "SRC-2026-05"
REPORTING_MONTH = "2026-05"
SOURCE_TABLE = "All Ongoing Projects"
SOURCE_TABLE_NUMBER = 6
EXPECTED_COUNT = 1987
EXPECTED_DATA_PAGES = list(range(54, 163))
EXTRACTION_METHOD = "pdfplumber_table"
EXTRACTOR_VERSION = "extractor_paimana_may_table6:0.1.0"
MANUAL_SAMPLE_SEED = 26103

_SERIAL_RE = re.compile(r"^\d+$")
_SINGLE_PAREN_RE = re.compile(r"^\(([^()]*)\)$")
_PAIR_PAREN_RE = re.compile(r"^\((.*?)\)\s+\((.*?)\)$")


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _split_two_line(value: Any, field: str) -> tuple[str, str]:
    lines = [line.strip() for line in _clean(value).splitlines() if line.strip()]
    if len(lines) != 2:
        raise ValueError(f"{field} expected exactly two lines; got {len(lines)}")
    second = _SINGLE_PAREN_RE.fullmatch(lines[1])
    if not second:
        raise ValueError(f"{field} second value is not parenthesized")
    return lines[0], second.group(1).strip()


def _split_may_doc(value: Any) -> tuple[str, str]:
    """Parse May's verified DoC forms without changing the frozen June rule."""
    raw = _clean(value)
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) == 1 and lines[0] == "(-)":
        return "", "-"
    return _split_two_line(raw, "target/revised DoC")


def parse_may_project_row(
    row: list[Any],
    *,
    source_sha256: str,
    pdf_page_index: int,
    printed_page_number: int | None,
    table_index: int,
    row_index: int,
) -> dict[str, Any]:
    """Parse one numeric May row using only the documented May structure."""
    if len(row) != 8:
        raise ValueError(f"expected 8 cells; got {len(row)}")
    serial = _clean(row[0])
    if not _SERIAL_RE.fullmatch(serial):
        raise ValueError("first cell is not a decimal project serial")

    identity_raw = _clean(row[1])
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

    approval, start = _split_two_line(row[3], "approval/start")
    target, revised_doc = _split_may_doc(row[4])
    original_cost, revised_cost = _split_two_line(row[5], "original/revised cost")
    locator = f"pdf_page_index={pdf_page_index},table_index={table_index},row_index={row_index}"
    return {
        "observation_id": f"OBS-202605-{int(serial):05d}",
        "reporting_month": REPORTING_MONTH,
        "serial_number_raw": serial,
        "project_name_raw": "\n".join(project_name_lines),
        "agency_raw": agency_line[1:-1].strip(),
        "project_code_raw": project_code.group(1).strip(),
        "legacy_ocms_code_raw": pair.group(1).strip(),
        "pmgid_raw": pair.group(2).strip(),
        "state_raw": _clean(row[2]),
        "approval_date_raw": approval,
        "start_date_raw": start,
        "original_target_doc_raw": target,
        "revised_doc_raw": revised_doc,
        "original_cost_raw": original_cost,
        "revised_cost_raw": revised_cost,
        "cumulative_expenditure_raw": _clean(row[6]),
        "physical_progress_raw": _clean(row[7]),
        "project_identity_cell_raw": identity_raw,
        "approval_start_cell_raw": _clean(row[3]),
        "doc_cell_raw": _clean(row[4]),
        "cost_cell_raw": _clean(row[5]),
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


def parse_may_or_review(row: list[Any], **context: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        return parse_may_project_row(row, **context), None
    except ValueError as exc:
        locator = (
            f"pdf_page_index={context['pdf_page_index']},"
            f"table_index={context['table_index']},row_index={context['row_index']}"
        )
        return None, {
            "source_id": SOURCE_ID,
            "source_sha256": context["source_sha256"],
            "pdf_page_index": context["pdf_page_index"],
            "printed_page_number": context["printed_page_number"],
            "source_table": SOURCE_TABLE,
            "source_table_number": SOURCE_TABLE_NUMBER,
            "extraction_method": EXTRACTION_METHOD,
            "extractor_version": EXTRACTOR_VERSION,
            "raw_row_locator": locator,
            "reason": str(exc),
            "raw_cells_json": json.dumps(row, ensure_ascii=False),
        }


def _write_csv_exclusive(path: Path, columns: list[str], rows: list[dict[str, Any]], root: Path) -> None:
    path = ensure_parent(path, root)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite extraction artifact: {path}")
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _missingness(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for field in [column for column in OUTPUT_COLUMNS if column.endswith("_raw")]:
        missing = sum(str(row.get(field, "")).strip() in {"", "-"} for row in rows)
        result[field] = {
            "missing_count": missing,
            "missing_pct": round(100 * missing / len(rows), 2) if rows else 0.0,
        }
    return result


def extract_may_2026_table6(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    config = yaml.safe_load((repo_root / "config.yaml").read_text(encoding="utf-8"))
    manifest_path = repo_root / config["manifest"]["file"]
    source = resolve_source(SOURCE_ID, manifest_path, repo_root)
    if (source.report_year, source.report_month) != (2026, 5):
        raise SourceRegistryError("May extractor resolved the wrong reporting period")
    pre_sha = compute_sha256(source.path)
    if pre_sha != source.sha256:
        raise SourceRegistryError("Pre-extraction SHA-256 mismatch")

    schema = detect_schema(source.path, config)
    if schema.detected_schema != "PAIMANA_V2" or schema.confidence != "HIGH":
        raise RuntimeError(f"Safe May PAIMANA_V2 schema not established: {schema.to_dict()}")
    data_contexts = [c for c in schema.table_contexts if c["context_type"] == "TABLE_DATA"]
    page_indices = [int(c["pdf_page_index"]) for c in data_contexts]
    if page_indices != EXPECTED_DATA_PAGES:
        raise RuntimeError(f"May Table 6 page contract changed: {page_indices[:2]}...{page_indices[-2:]}")
    printed_by_page = {int(c["pdf_page_index"]): c["printed_page_number"] for c in data_contexts}
    if any(printed_by_page[page] != page - 1 for page in page_indices):
        raise RuntimeError("May printed/physical page mapping changed")

    accepted: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    rejection_types: Counter[str] = Counter()
    with pdfplumber.open(str(source.path)) as pdf:
        for page_index in page_indices:
            page_rejections: Counter[str] = Counter()
            page_accepted = page_unresolved = 0
            tables = pdf.pages[page_index - 1].extract_tables() or []
            if len(tables) != 1:
                raise RuntimeError(f"May page {page_index} expected one table; found {len(tables)}")
            for table_index, table in enumerate(tables):
                for row_index, row in enumerate(table):
                    first = _clean(row[0]) if row else ""
                    if not _SERIAL_RE.fullmatch(first):
                        kind = classify_non_project_row(row)
                        page_rejections[kind] += 1
                        rejection_types[kind] += 1
                        continue
                    record, review = parse_may_or_review(
                        row,
                        source_sha256=source.sha256,
                        pdf_page_index=page_index,
                        printed_page_number=printed_by_page[page_index],
                        table_index=table_index,
                        row_index=row_index,
                    )
                    if review:
                        unresolved.append(review)
                        page_unresolved += 1
                    else:
                        accepted.append(record)
                        page_accepted += 1
            diagnostics.append({
                "pdf_page_index": page_index,
                "printed_page_number": printed_by_page[page_index],
                "accepted_project_rows": page_accepted,
                "rejected_headers": page_rejections["REPEATED_HEADER"],
                "rejected_sections": page_rejections["SECTION_HEADING"],
                "rejected_totals": page_rejections["TOTAL"],
                "rejected_other": sum(page_rejections.values()) - page_rejections["REPEATED_HEADER"] - page_rejections["SECTION_HEADING"] - page_rejections["TOTAL"],
                "unresolved_rows": page_unresolved,
            })

    serials = [int(row["serial_number_raw"]) for row in accepted]
    locators = [row["raw_row_locator"] for row in accepted]
    observations = [row["observation_id"] for row in accepted]
    duplicate_serials = len(serials) - len(set(serials))
    duplicate_locators = len(locators) - len(set(locators))
    duplicate_observations = len(observations) - len(set(observations))
    serial_integrity = serials == list(range(1, EXPECTED_COUNT + 1))
    if duplicate_serials or duplicate_locators or duplicate_observations:
        raise RuntimeError("Duplicate May serial, locator, or observation detected")
    if not serial_integrity:
        raise RuntimeError("May natural serial inventory is not exactly 1-1987")

    provenance_errors = [
        f"{row['raw_row_locator']}: {error}"
        for row in accepted
        for error in validate_provenance_record(row, manifest_path)
    ]
    if provenance_errors:
        raise RuntimeError("May provenance validation failed: " + "; ".join(provenance_errors[:10]))
    post_sha = compute_sha256(source.path)
    if post_sha != pre_sha or post_sha != source.sha256:
        raise RuntimeError("Post-extraction May SHA-256 mismatch")

    counts = [row["accepted_project_rows"] for row in diagnostics]
    median = statistics.median(counts)
    anomalies = [
        {**row, "reason": "ZERO_ROWS" if row["accepted_project_rows"] == 0 else "COUNT_OUTLIER"}
        for row in diagnostics
        if row["accepted_project_rows"] == 0
        or row["accepted_project_rows"] < median * 0.5
        or row["accepted_project_rows"] > median * 1.5
    ]
    timestamp = datetime.now(timezone.utc).isoformat()
    run_id = f"extract-202605-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    output = repo_root / "data/extracted/ongoing/ongoing_2026_05.csv"
    review = repo_root / "data/extracted/review/ongoing_2026_05_unresolved_rows.csv"
    sample_path = repo_root / "validation/extraction_validation/may_2026_manual_sample_30.csv"
    summary_path = repo_root / "validation/extraction_validation/may_2026_extraction_summary.json"
    report_path = repo_root / "outputs/reports/MAY_2026_EXTRACTION_REPORT.md"

    _write_csv_exclusive(output, OUTPUT_COLUMNS, accepted, repo_root)
    _write_csv_exclusive(review, UNRESOLVED_COLUMNS, unresolved, repo_root)

    provenance_path = safe_destination(repo_root / "data/metadata/provenance.csv", repo_root)
    with provenance_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        existing = list(reader)
        if reader.fieldnames != PROVENANCE_COLUMNS:
            raise RuntimeError("Existing provenance header does not match extraction contract")
    if any(row.get("source_id") == SOURCE_ID for row in existing):
        raise RuntimeError("May provenance already exists; refusing uncontrolled append")
    provenance_rows = [{
        "observation_id": row["observation_id"], "source_id": source.source_id,
        "source_sha256": source.sha256, "source_group_id": source.source_group_id,
        "source_part": source.source_part, "filename": source.filename,
        "report_year": source.report_year, "report_month": source.report_month,
        "pdf_page_index": row["pdf_page_index"], "printed_page_number": row["printed_page_number"],
        "source_table": SOURCE_TABLE, "source_table_number": SOURCE_TABLE_NUMBER,
        "extraction_method": EXTRACTION_METHOD, "extractor_version": EXTRACTOR_VERSION,
        "raw_row_locator": row["raw_row_locator"], "extraction_timestamp_utc": timestamp,
        "extracted_by": run_id, "notes": "",
    } for row in accepted]
    with provenance_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROVENANCE_COLUMNS)
        writer.writeheader()
        writer.writerows(existing + provenance_rows)

    rng = random.Random(MANUAL_SAMPLE_SEED)
    sample = sorted(rng.sample(accepted, 30), key=lambda row: int(row["serial_number_raw"]))
    manual = [
        "manual_project_name_match", "manual_project_code_match", "manual_cost_match",
        "manual_date_match", "manual_progress_match", "manual_overall_match",
        "reviewer", "review_notes",
    ]
    _write_csv_exclusive(
        sample_path, OUTPUT_COLUMNS + manual,
        [{**row, **{field: "" for field in manual}} for row in sample], repo_root,
    )

    summary = {
        "source_id": source.source_id, "source_sha256": source.sha256,
        "reporting_month": REPORTING_MONTH, "schema": schema.detected_schema,
        "schema_confidence": schema.confidence, "source_table": SOURCE_TABLE,
        "source_table_number": SOURCE_TABLE_NUMBER, "title_pdf_page_index": 53,
        "data_pdf_page_range": [54, 162], "printed_page_range": [53, 161],
        "expected_count_from_may_report": EXPECTED_COUNT,
        "expected_count_evidence_pdf_page_index": 4,
        "expected_count_evidence_printed_page_number": 3,
        "accepted_project_rows": len(accepted), "unresolved_rows": len(unresolved),
        "difference": len(accepted) - EXPECTED_COUNT,
        "duplicate_raw_locator_count": duplicate_locators,
        "duplicate_serial_count": duplicate_serials,
        "duplicate_observation_count": duplicate_observations,
        "natural_serial_integrity": serial_integrity,
        "rejection_types": dict(rejection_types), "missingness": _missingness(accepted),
        "page_diagnostics": diagnostics, "page_anomalies": anomalies,
        "pre_extraction_sha256": pre_sha, "post_extraction_sha256": post_sha,
        "extractor_version": EXTRACTOR_VERSION, "extraction_method": EXTRACTION_METHOD,
        "may_vs_june": "COMPATIBLE_VARIATION", "run_id": run_id,
        "timestamp_utc": timestamp,
    }
    write_json_replace(summary_path, summary, repo_root=repo_root)
    report_path = ensure_parent(report_path, repo_root)
    report_path.write_text(_render_report(summary, output, review, sample_path), encoding="utf-8")
    return summary


def _render_report(summary: dict[str, Any], output: Path, review: Path, sample: Path) -> str:
    missing = "\n".join(
        f"- `{field}`: {value['missing_count']} ({value['missing_pct']}%)"
        for field, value in summary["missingness"].items()
    )
    anomalies = "\n".join(
        f"- PDF {row['pdf_page_index']}: {row['reason']} ({row['accepted_project_rows']} rows)"
        for row in summary["page_anomalies"]
    ) or "- None under the declared thresholds."
    return f"""# May 2026 Table 6 Extraction Report

## Source and schema

- Source: `SRC-2026-05` / `FlashReport_2026_05.pdf`
- SHA-256: `{summary['source_sha256']}`
- Schema: `PAIMANA_V2` / `HIGH`
- Extractor: `{summary['extractor_version']}`
- Method: `{summary['extraction_method']}`
- May versus June: `COMPATIBLE_VARIATION`

## Boundaries and reconciliation

- Physical title page: 53
- Physical data pages: 54–162
- Printed data pages: 53–161
- Expected count: 1,987, stated on physical page 4 / printed page 3
- Accepted: {summary['accepted_project_rows']}
- Unresolved: {summary['unresolved_rows']}
- Difference: {summary['difference']}
- Duplicate serials/locators/observations: {summary['duplicate_serial_count']}/{summary['duplicate_raw_locator_count']}/{summary['duplicate_observation_count']}
- Natural serial sequence 1–1987: {summary['natural_serial_integrity']}

## Structure and fields

The verified eight-column PAIMANA V2 structure was extracted as raw project,
agency, identifiers, state, dates, costs, expenditure, progress, full compound
cells, and mandatory May provenance. Ministry/sector carry-forward,
normalization, linking, features, labels, outcomes, and risk values are omitted.

The May-specific compatible variation is 11 DoC cells containing only `(-)`.
Their complete source cell is preserved; target is empty and revised DoC is `-`.

## Missingness

{missing}

## Page diagnostics

The JSON summary contains all 109 page-level diagnostic records.

{anomalies}

## Artifacts and assessment

- Raw extraction: `{output.as_posix()}`
- Unresolved review: `{review.as_posix()}`
- Deterministic manual sample: `{sample.as_posix()}`

Ready for independent human review. This does not authorize project linking,
normalization, another month, or historical expansion.
"""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract canonical May 2026 Table 6 only")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    return parser


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = _parser().parse_args()
    print(json.dumps(extract_may_2026_table6(Path(args.repo_root)), indent=2, ensure_ascii=False))
