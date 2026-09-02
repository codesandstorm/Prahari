"""Prepare an exhaustive, source-faithful May-June temporal review."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from src.identity.continuity_audit import normalize_for_comparison

MAY_EXTRACTED_SHA256 = "f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e"
JUNE_EXTRACTED_SHA256 = "bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9"
MATCHED_PROJECTS = 1825

PRIMARY_FLAGS = (
    "PROJECT_NAME_CHANGED",
    "APPROVAL_DATE_CHANGED",
    "START_DATE_CHANGED",
    "ORIGINAL_COST_CHANGED",
    "PHYSICAL_PROGRESS_DECREASED",
    "CUMULATIVE_EXPENDITURE_DECREASED",
)
OPTIONAL_FLAGS = (
    "ORIGINAL_TARGET_DOC_CHANGED", "REVISED_COST_CHANGED", "REVISED_DOC_CHANGED",
    "AGENCY_CHANGED", "STATE_CHANGED",
)
MANUAL_FIELDS = (
    "manual_source_values_confirmed",
    "manual_longitudinal_mapping_correct",
    "manual_change_is_source_reported",
    "manual_issue_type",
    "reviewer",
    "review_notes",
)

SOURCE_TO_MONTH = {
    "observation_id": "observation_id",
    "project_code_raw": "project_code",
    "reporting_month": "reporting_month",
    "project_name_raw": "reported_project_name",
    "agency_raw": "reported_agency",
    "state_raw": "reported_state",
    "approval_date_raw": "reported_approval_date",
    "start_date_raw": "reported_start_date",
    "original_target_doc_raw": "reported_original_target_doc",
    "revised_doc_raw": "reported_revised_doc",
    "original_cost_raw": "reported_original_cost",
    "revised_cost_raw": "reported_revised_cost",
    "cumulative_expenditure_raw": "reported_cumulative_expenditure",
    "physical_progress_raw": "reported_physical_progress",
    "legacy_ocms_code_raw": "legacy_ocms_code_raw",
    "pmgid_raw": "pmgid_raw",
    "source_id": "source_id",
    "source_sha256": "source_sha256",
    "pdf_page_index": "pdf_page_index",
    "printed_page_number": "printed_page_number",
    "source_table": "source_table",
    "source_table_number": "source_table_number",
    "extraction_method": "extraction_method",
    "extractor_version": "extractor_version",
    "raw_row_locator": "raw_row_locator",
}
PROVENANCE_FIELDS = (
    "source_id", "source_sha256", "pdf_page_index", "printed_page_number",
    "source_table", "source_table_number", "raw_row_locator",
)
IDENTITY_FIELDS = ("observation_id", "project_code_raw", "project_name_raw", "agency_raw", "state_raw")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = fields or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=selected, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def decimal_or_none(value: str) -> Decimal | None:
    cleaned = value.strip().replace(",", "")
    if cleaned in {"", "-", "NA"}:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Non-numeric temporal value: {value!r}") from exc


def numeric_changed(left: str, right: str) -> bool:
    return decimal_or_none(left) != decimal_or_none(right)


def decreased(left: str, right: str) -> bool:
    before, after = decimal_or_none(left), decimal_or_none(right)
    return before is not None and after is not None and after < before


def numeric_delta(left: str, right: str) -> Decimal | None:
    before, after = decimal_or_none(left), decimal_or_none(right)
    return None if before is None or after is None else after - before


def reconstruct_flags(may: dict[str, str], june: dict[str, str]) -> tuple[list[str], list[str]]:
    primary: list[str] = []
    optional: list[str] = []
    if normalize_for_comparison(may["reported_project_name"]) != normalize_for_comparison(june["reported_project_name"]):
        primary.append("PROJECT_NAME_CHANGED")
    if may["reported_approval_date"].strip() != june["reported_approval_date"].strip():
        primary.append("APPROVAL_DATE_CHANGED")
    if may["reported_start_date"].strip() != june["reported_start_date"].strip():
        primary.append("START_DATE_CHANGED")
    if numeric_changed(may["reported_original_cost"], june["reported_original_cost"]):
        primary.append("ORIGINAL_COST_CHANGED")
    if decreased(may["reported_physical_progress"], june["reported_physical_progress"]):
        primary.append("PHYSICAL_PROGRESS_DECREASED")
    if decreased(may["reported_cumulative_expenditure"], june["reported_cumulative_expenditure"]):
        primary.append("CUMULATIVE_EXPENDITURE_DECREASED")
    if numeric_changed(may["reported_revised_cost"], june["reported_revised_cost"]):
        optional.append("REVISED_COST_CHANGED")
    if may["reported_original_target_doc"].strip() != june["reported_original_target_doc"].strip():
        optional.append("ORIGINAL_TARGET_DOC_CHANGED")
    if may["reported_revised_doc"].strip() != june["reported_revised_doc"].strip():
        optional.append("REVISED_DOC_CHANGED")
    if normalize_for_comparison(may["reported_agency"]) != normalize_for_comparison(june["reported_agency"]):
        optional.append("AGENCY_CHANGED")
    if normalize_for_comparison(may["reported_state"]) != normalize_for_comparison(june["reported_state"]):
        optional.append("STATE_CHANGED")
    return primary, optional


def review_priority(flags: list[str]) -> str:
    if "PROJECT_NAME_CHANGED" in flags and len(flags) > 1:
        return "PRIORITY_1"
    if "APPROVAL_DATE_CHANGED" in flags or "ORIGINAL_COST_CHANGED" in flags:
        return "PRIORITY_2"
    if "START_DATE_CHANGED" in flags:
        return "PRIORITY_3"
    if set(flags) <= {"PHYSICAL_PROGRESS_DECREASED", "CUMULATIVE_EXPENDITURE_DECREASED"}:
        return "PRIORITY_4"
    return "PRIORITY_5"


def build_review_rows(project_month: list[dict[str, str]]) -> tuple[list[dict[str, str]], Counter[str]]:
    by_code_month = {(row["project_code"], row["reporting_month"]): row for row in project_month}
    if len(by_code_month) != len(project_month):
        raise RuntimeError("Duplicate project-month key in validated pilot")
    codes = sorted(
        {code for code, month in by_code_month if month == "2026-05"}
        & {code for code, month in by_code_month if month == "2026-06"},
        key=int,
    )
    counts: Counter[str] = Counter()
    result: list[dict[str, str]] = []
    for code in codes:
        may = by_code_month[(code, "2026-05")]
        june = by_code_month[(code, "2026-06")]
        flags, optional = reconstruct_flags(may, june)
        counts.update(flags + optional)
        if not flags:
            continue
        progress_delta = numeric_delta(may["reported_physical_progress"], june["reported_physical_progress"])
        expenditure_delta = numeric_delta(may["reported_cumulative_expenditure"], june["reported_cumulative_expenditure"])
        revised_cost_delta = numeric_delta(may["reported_revised_cost"], june["reported_revised_cost"])
        row = {
            "canonical_project_id": may["canonical_project_id"], "project_code": code,
            "flag_count": str(len(flags)), "flag_reasons": "|".join(flags),
            "other_diagnostic_reasons": "|".join(optional), "review_priority": review_priority(flags),
            "may_project_name": may["reported_project_name"], "may_agency": may["reported_agency"], "may_state": may["reported_state"],
            "june_project_name": june["reported_project_name"], "june_agency": june["reported_agency"], "june_state": june["reported_state"],
            "may_approval_date": may["reported_approval_date"], "may_start_date": may["reported_start_date"],
            "may_original_target_doc": may["reported_original_target_doc"], "may_revised_doc": may["reported_revised_doc"],
            "june_approval_date": june["reported_approval_date"], "june_start_date": june["reported_start_date"],
            "june_original_target_doc": june["reported_original_target_doc"], "june_revised_doc": june["reported_revised_doc"],
            "may_original_cost": may["reported_original_cost"], "may_revised_cost": may["reported_revised_cost"],
            "may_cumulative_expenditure": may["reported_cumulative_expenditure"], "may_physical_progress": may["reported_physical_progress"],
            "june_original_cost": june["reported_original_cost"], "june_revised_cost": june["reported_revised_cost"],
            "june_cumulative_expenditure": june["reported_cumulative_expenditure"], "june_physical_progress": june["reported_physical_progress"],
            "progress_delta": "" if progress_delta is None else str(progress_delta),
            "expenditure_delta": "" if expenditure_delta is None else str(expenditure_delta),
            "revised_cost_delta": "" if revised_cost_delta is None else str(revised_cost_delta),
            "may_source_id": may["source_id"], "may_pdf_page_index": may["pdf_page_index"],
            "may_printed_page_number": may["printed_page_number"], "may_raw_row_locator": may["raw_row_locator"],
            "june_source_id": june["source_id"], "june_pdf_page_index": june["pdf_page_index"],
            "june_printed_page_number": june["printed_page_number"], "june_raw_row_locator": june["raw_row_locator"],
            **{field: "" for field in MANUAL_FIELDS},
        }
        result.append(row)
    return result, counts


def compare_to_source(month: dict[str, str], source: dict[str, str]) -> tuple[bool, bool, bool, list[str]]:
    mismatches = [month_field for source_field, month_field in SOURCE_TO_MONTH.items() if month[month_field] != source[source_field]]
    provenance_ok = all(month[field] == source[field] for field in PROVENANCE_FIELDS)
    identity_ok = all(month[SOURCE_TO_MONTH[field]] == source[field] for field in IDENTITY_FIELDS)
    return not mismatches, provenance_ok, identity_ok, mismatches


def automated_checks(
    review: list[dict[str, str]], project_month: list[dict[str, str]],
    may_source: list[dict[str, str]], june_source: list[dict[str, str]],
) -> list[dict[str, str]]:
    month_index = {(row["project_code"], row["reporting_month"]): row for row in project_month}
    may_index = {row["project_code_raw"]: row for row in may_source}
    june_index = {row["project_code_raw"]: row for row in june_source}
    results = []
    for review_row in review:
        code = review_row["project_code"]
        may_equal, may_prov, may_identity, may_mismatch = compare_to_source(month_index[(code, "2026-05")], may_index[code])
        june_equal, june_prov, june_identity, june_mismatch = compare_to_source(month_index[(code, "2026-06")], june_index[code])
        provenance = may_prov and june_prov
        identity = may_identity and june_identity
        passed = may_equal and june_equal and provenance and identity
        results.append({
            "canonical_project_id": review_row["canonical_project_id"], "project_code": code,
            "may_values_equal_source": "YES" if may_equal else "NO",
            "june_values_equal_source": "YES" if june_equal else "NO",
            "provenance_equal_source": "YES" if provenance else "NO",
            "identity_equal_source": "YES" if identity else "NO",
            "may_mismatched_fields": "|".join(may_mismatch),
            "june_mismatched_fields": "|".join(june_mismatch),
            "automated_result": "PASS" if passed else "FAIL",
        })
    return results


def flag_summary(review: list[dict[str, str]]) -> list[dict[str, str]]:
    numeric = {
        "ORIGINAL_COST_CHANGED": "original_cost",
        "PHYSICAL_PROGRESS_DECREASED": "progress",
        "CUMULATIVE_EXPENDITURE_DECREASED": "expenditure",
    }
    result = []
    for flag in PRIMARY_FLAGS:
        rows = [row for row in review if flag in row["flag_reasons"].split("|")]
        deltas: list[Decimal] = []
        if flag in numeric:
            prefix = numeric[flag]
            for row in rows:
                if prefix == "original_cost":
                    delta = numeric_delta(row["may_original_cost"], row["june_original_cost"])
                else:
                    delta = decimal_or_none(row[f"{prefix}_delta"])
                if delta is not None:
                    deltas.append(delta)
        result.append({
            "flag_reason": flag, "count": str(len(rows)),
            "percentage_of_matched_projects": f"{len(rows) / MATCHED_PROJECTS * 100:.4f}",
            "minimum_change": "" if not deltas else str(min(deltas)),
            "maximum_change": "" if not deltas else str(max(deltas)),
            "median_change": "" if not deltas else str(statistics.median(deltas)),
            "also_carries_another_primary_flag": str(sum(int(int(row["flag_count"]) > 1) for row in rows)),
        })
    return result


def render_report(summary: dict[str, Any], flag_rows: list[dict[str, str]], hashes: dict[str, str]) -> str:
    flags = "\n".join(
        f"| {row['flag_reason']} | {row['count']} | {row['percentage_of_matched_projects']}% | {row['minimum_change'] or 'n/a'} | {row['maximum_change'] or 'n/a'} | {row['median_change'] or 'n/a'} | {row['also_carries_another_primary_flag']} |"
        for row in flag_rows
    )
    priorities = "\n".join(f"- {key}: {value}" for key, value in sorted(summary["priority_counts"].items()))
    return f"""# May–June 2026 Exhaustive Temporal Review Report

## 1. Purpose

This review independently reconstructs the defined May–June temporal flags, creates a reviewer-friendly side-by-side artifact, and checks every flagged longitudinal observation against the frozen validated monthly extraction. It does not correct source values or interpret changes as errors, outcomes, features, or risk.

## 2. Input hashes

- May extracted CSV: `{hashes['may_extracted']}`
- June extracted CSV: `{hashes['june_extracted']}`
- May source PDF: `{hashes['may_pdf']}`
- June source PDF: `{hashes['june_pdf']}`
- Frozen `project_master.csv`: `{hashes['project_master']}`
- Frozen `project_month.csv`: `{hashes['project_month']}`

## 3. Independent reconstruction and prior-set comparison

- Existing review rows / unique Project Codes: {summary['existing_rows']} / {summary['existing_unique']}
- Recomputed review rows / unique Project Codes: {summary['recomputed_rows']} / {summary['recomputed_unique']}
- Intersection: {summary['intersection']}
- Existing-only: {summary['existing_only']}
- Recomputed-only: {summary['recomputed_only']}
- Exact Project Code set match: {summary['exact_set_match']}

The reconstruction reads `project_month.csv` and independently applies the documented primary policy. Agency, revised-cost, and revised-DoC changes are retained as secondary diagnostics and do not expand the primary review set.

## 4. Automated source equality

- Reviewed projects: {summary['recomputed_rows']}
- Automated PASS: {summary['automated_passes']}
- Automated FAIL: {summary['automated_failures']}
- Provenance failures: {summary['provenance_failures']}
- Identity failures: {summary['identity_failures']}

Every preserved May and June field was compared exactly with the Project Code-matched validated extraction row, including missing markers, dates, numerics, source identity, page information, extraction metadata, and raw row locator.

## 5. Primary flag summary

Percentages use 1,825 exact matched projects as the denominator. Numeric changes are June minus May.

| Flag | Count | Matched % | Minimum | Maximum | Median | Also has another primary flag |
|---|---:|---:|---:|---:|---:|---:|
{flags}

## 6. Secondary diagnostics

- Agency changes among all matched projects: {summary['agency_changes']}
- State changes among all matched projects: {summary['state_changes']}
- Original-target-DoC changes among all matched projects: {summary['original_target_doc_changes']}
- Revised-cost changes among all matched projects: {summary['revised_cost_changes']}
- Revised-DoC changes among all matched projects: {summary['revised_doc_changes']}

## 7. Overlap and review order

- Projects with multiple primary flags: {summary['multiple_primary_flags']}
- Primary-flag pair overlaps: `{json.dumps(summary['pair_overlaps'], sort_keys=True)}`

{priorities}

`review_priority` is deterministic review ordering only. It is not a risk score, business priority, or model feature.

## 8. Defect findings

- Longitudinal transformation defects: {summary['automated_failures']}
- Provenance defects: {summary['provenance_failures']}
- Identity defects: {summary['identity_failures']}

## 9. Human review artifact

`validation/longitudinal/may_june_2026_temporal_review_88_MANUAL.csv`

Review each row against the cited May and June PDF pages and raw row locators. Populate only the six manual columns. Confirmation fields allow `YES`, `NO`, or `UNCERTAIN`. `manual_issue_type` allows `NONE`, `SOURCE_REPORTED_VARIATION`, `EXTRACTION_ERROR`, `LONGITUDINAL_TRANSFORMATION_ERROR`, `IDENTITY_ERROR`, `PROVENANCE_ERROR`, or `UNCERTAIN`.

Do not edit non-manual fields. If any source value, identity, mapping, or provenance is not confirmable, record `UNCERTAIN` rather than inferring a cause.

## 10. Scientific interpretation

The automated result establishes whether the longitudinal representation faithfully preserves the validated extracted rows. It does not establish that every PDF extraction is semantically correct; that requires the requested human source review. Decreases and metadata revisions remain reported observations, not errors or risk indicators.

## 11. Limitations

- The scope is May and June 2026 only.
- Automated equality is bounded by the already validated monthly extraction.
- PDF-level confirmation remains deliberately manual.
- No causal meaning is assigned to changes.
- No source, extraction, master, or project-month file was modified.
"""


def prepare_temporal_review(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    paths = {
        "may_extracted": root / "data/extracted/ongoing/ongoing_2026_05.csv",
        "june_extracted": root / "data/extracted/ongoing/ongoing_2026_06.csv",
        "project_master": root / "data/processed/pilot_2026_05_06/project_master.csv",
        "project_month": root / "data/processed/pilot_2026_05_06/project_month.csv",
        "may_pdf": root / "data/raw/2026/FlashReport_2026_05.pdf",
        "june_pdf": root / "data/raw/2026/FlashReport_2026_06.pdf",
        "existing": root / "validation/longitudinal/may_june_2026_temporal_review.csv",
    }
    hashes = {name: sha256(path) for name, path in paths.items() if name not in {"existing"}}
    if hashes["may_extracted"] != MAY_EXTRACTED_SHA256 or hashes["june_extracted"] != JUNE_EXTRACTED_SHA256:
        raise RuntimeError("Frozen validated extraction hash mismatch")
    project_month = read_csv(paths["project_month"])
    review, diagnostic_counts = build_review_rows(project_month)
    existing = read_csv(paths["existing"])
    existing_codes = {row["project_code"] for row in existing}
    recomputed_codes = {row["project_code"] for row in review}
    checks = automated_checks(review, project_month, read_csv(paths["may_extracted"]), read_csv(paths["june_extracted"]))
    summaries = flag_summary(review)
    pairs: Counter[str] = Counter()
    for row in review:
        flags = row["flag_reasons"].split("|")
        for index, left in enumerate(flags):
            for right in flags[index + 1:]:
                pairs[f"{left}+{right}"] += 1
    summary: dict[str, Any] = {
        "existing_rows": len(existing), "existing_unique": len(existing_codes),
        "recomputed_rows": len(review), "recomputed_unique": len(recomputed_codes),
        "intersection": len(existing_codes & recomputed_codes),
        "existing_only": sorted(existing_codes - recomputed_codes, key=int),
        "recomputed_only": sorted(recomputed_codes - existing_codes, key=int),
        "exact_set_match": "YES" if existing_codes == recomputed_codes else "NO",
        "automated_passes": sum(row["automated_result"] == "PASS" for row in checks),
        "automated_failures": sum(row["automated_result"] == "FAIL" for row in checks),
        "provenance_failures": sum(row["provenance_equal_source"] == "NO" for row in checks),
        "identity_failures": sum(row["identity_equal_source"] == "NO" for row in checks),
        "multiple_primary_flags": sum(int(row["flag_count"]) > 1 for row in review),
        "pair_overlaps": dict(pairs),
        "priority_counts": dict(Counter(row["review_priority"] for row in review)),
        "agency_changes": diagnostic_counts["AGENCY_CHANGED"],
        "state_changes": diagnostic_counts["STATE_CHANGED"],
        "original_target_doc_changes": diagnostic_counts["ORIGINAL_TARGET_DOC_CHANGED"],
        "revised_cost_changes": diagnostic_counts["REVISED_COST_CHANGED"],
        "revised_doc_changes": diagnostic_counts["REVISED_DOC_CHANGED"],
        "flag_counts": {row["flag_reason"]: int(row["count"]) for row in summaries},
        "input_hashes": hashes,
    }
    validation = root / "validation/longitudinal"
    write_csv(validation / "may_june_2026_temporal_review_88_MANUAL.csv", review)
    write_csv(validation / "may_june_2026_temporal_review_automated_check.csv", checks)
    write_csv(validation / "may_june_2026_temporal_review_flag_summary.csv", summaries)
    report = root / "outputs/reports/MAY_JUNE_2026_TEMPORAL_REVIEW_REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary, summaries, hashes), encoding="utf-8")
    return summary
