"""Build the validated May-June 2026 longitudinal pilot and diagnostics."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from src.identity.continuity_audit import normalize_for_comparison
from src.pipeline.source_registry import resolve_source
from src.utils.safe_io import ensure_parent, write_json_replace

DATASET_VERSION = "gate2-pilot-2026-05-06-v1"
MAY_CSV_SHA256 = "f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e"
JUNE_CSV_SHA256 = "bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9"
MAY_ROWS = 1987
JUNE_ROWS = 1847
SAMPLE_SEED = 26103

MASTER_FIELDS = [
    "canonical_project_id", "project_code", "first_observed_month",
    "last_observed_month", "observation_count", "presence_status",
    "current_project_name", "current_agency", "current_state",
    "identity_method", "identity_status", "current_observation_id",
    "current_source_id", "current_source_sha256", "current_pdf_page_index",
    "current_printed_page_number", "current_source_table",
    "current_source_table_number", "current_raw_row_locator",
]

MONTH_FIELDS = [
    "observation_id", "canonical_project_id", "project_code", "reporting_month",
    "reported_project_name", "reported_agency", "reported_state",
    "reported_approval_date", "reported_start_date",
    "reported_original_target_doc", "reported_revised_doc",
    "reported_original_cost", "reported_revised_cost",
    "reported_cumulative_expenditure", "reported_physical_progress",
    "legacy_ocms_code_raw", "pmgid_raw", "source_id", "source_sha256",
    "pdf_page_index", "printed_page_number", "source_table",
    "source_table_number", "extraction_method", "extractor_version",
    "raw_row_locator",
]


def canonical_project_id(project_code: str) -> str:
    code = project_code.strip()
    if not code or code == "-":
        raise ValueError("Project Code is required for pilot canonical identity")
    return f"PRH-{code}"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def to_project_month(row: dict[str, str]) -> dict[str, str]:
    """Map one immutable extraction row without normalizing source facts."""
    return {
        "observation_id": row["observation_id"],
        "canonical_project_id": canonical_project_id(row["project_code_raw"]),
        "project_code": row["project_code_raw"],
        "reporting_month": row["reporting_month"],
        "reported_project_name": row["project_name_raw"],
        "reported_agency": row["agency_raw"],
        "reported_state": row["state_raw"],
        "reported_approval_date": row["approval_date_raw"],
        "reported_start_date": row["start_date_raw"],
        "reported_original_target_doc": row["original_target_doc_raw"],
        "reported_revised_doc": row["revised_doc_raw"],
        "reported_original_cost": row["original_cost_raw"],
        "reported_revised_cost": row["revised_cost_raw"],
        "reported_cumulative_expenditure": row["cumulative_expenditure_raw"],
        "reported_physical_progress": row["physical_progress_raw"],
        "legacy_ocms_code_raw": row["legacy_ocms_code_raw"],
        "pmgid_raw": row["pmgid_raw"],
        "source_id": row["source_id"],
        "source_sha256": row["source_sha256"],
        "pdf_page_index": row["pdf_page_index"],
        "printed_page_number": row["printed_page_number"],
        "source_table": row["source_table"],
        "source_table_number": row["source_table_number"],
        "extraction_method": row["extraction_method"],
        "extractor_version": row["extractor_version"],
        "raw_row_locator": row["raw_row_locator"],
    }


def build_master(month_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in month_rows:
        grouped[row["project_code"]].append(row)
    result: list[dict[str, str]] = []
    for code in sorted(grouped, key=lambda value: int(value)):
        observations = sorted(grouped[code], key=lambda row: row["reporting_month"])
        months = [row["reporting_month"] for row in observations]
        if len(months) != len(set(months)):
            raise RuntimeError(f"Duplicate monthly observation for Project Code {code}")
        current = observations[-1]
        presence = (
            "MAY_AND_JUNE" if months == ["2026-05", "2026-06"]
            else "MAY_ONLY" if months == ["2026-05"]
            else "JUNE_ONLY" if months == ["2026-06"]
            else "INVALID"
        )
        if presence == "INVALID":
            raise RuntimeError(f"Unexpected pilot month inventory for {code}: {months}")
        if len(observations) == 2:
            changed = any(
                normalize_for_comparison(observations[0][field])
                != normalize_for_comparison(observations[1][field])
                for field in ("reported_project_name", "reported_agency", "reported_state")
            )
            identity_status = (
                "EXACT_CODE_WITH_METADATA_VARIATION" if changed
                else "VERIFIED_EXACT_CODE"
            )
        else:
            identity_status = "SINGLE_MONTH_OBSERVED"
        result.append({
            "canonical_project_id": canonical_project_id(code), "project_code": code,
            "first_observed_month": months[0], "last_observed_month": months[-1],
            "observation_count": str(len(observations)), "presence_status": presence,
            "current_project_name": current["reported_project_name"],
            "current_agency": current["reported_agency"],
            "current_state": current["reported_state"],
            "identity_method": "EXACT_PROJECT_CODE", "identity_status": identity_status,
            "current_observation_id": current["observation_id"],
            "current_source_id": current["source_id"],
            "current_source_sha256": current["source_sha256"],
            "current_pdf_page_index": current["pdf_page_index"],
            "current_printed_page_number": current["printed_page_number"],
            "current_source_table": current["source_table"],
            "current_source_table_number": current["source_table_number"],
            "current_raw_row_locator": current["raw_row_locator"],
        })
    return result


def _decimal(value: str) -> Decimal | None:
    value = value.strip().replace(",", "")
    if value in {"", "-", "NA"}:
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Non-numeric temporal value: {value!r}") from exc


def _movement(may: str, june: str, prefix: str) -> str:
    left, right = _decimal(may), _decimal(june)
    if left is None or right is None:
        return f"{prefix}_NOT_COMPARABLE"
    if right > left:
        return f"{prefix}_INCREASE"
    if right < left:
        return f"{prefix}_DECREASE"
    return f"{prefix}_UNCHANGED"


def _numeric_changed(may: str, june: str) -> bool:
    return _decimal(may) != _decimal(june)


def build_temporal_diagnostics(
    may_by_code: dict[str, dict[str, str]],
    june_by_code: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], Counter[str]]:
    diagnostics: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    for code in sorted(set(may_by_code) & set(june_by_code), key=int):
        may, june = may_by_code[code], june_by_code[code]
        progress = _movement(may["physical_progress_raw"], june["physical_progress_raw"], "PROGRESS")
        expenditure = _movement(
            may["cumulative_expenditure_raw"], june["cumulative_expenditure_raw"], "EXPENDITURE"
        )
        changed = {
            "name_changed": normalize_for_comparison(may["project_name_raw"]) != normalize_for_comparison(june["project_name_raw"]),
            "agency_changed": normalize_for_comparison(may["agency_raw"]) != normalize_for_comparison(june["agency_raw"]),
            "state_changed": normalize_for_comparison(may["state_raw"]) != normalize_for_comparison(june["state_raw"]),
            "approval_date_changed": may["approval_date_raw"].strip() != june["approval_date_raw"].strip(),
            "start_date_changed": may["start_date_raw"].strip() != june["start_date_raw"].strip(),
            "original_target_doc_changed": may["original_target_doc_raw"].strip() != june["original_target_doc_raw"].strip(),
            "original_cost_changed": _numeric_changed(may["original_cost_raw"], june["original_cost_raw"]),
            "revised_cost_changed": _numeric_changed(may["revised_cost_raw"], june["revised_cost_raw"]),
            "revised_doc_changed": may["revised_doc_raw"].strip() != june["revised_doc_raw"].strip(),
        }
        counts[progress] += 1
        counts[expenditure] += 1
        for key, value in changed.items():
            counts[key] += int(value)
        row = {
            "canonical_project_id": canonical_project_id(code), "project_code": code,
            "may_observation_id": may["observation_id"], "june_observation_id": june["observation_id"],
            "progress_category": progress, "expenditure_category": expenditure,
            **{key: str(value).upper() for key, value in changed.items()},
            "may_physical_progress_raw": may["physical_progress_raw"],
            "june_physical_progress_raw": june["physical_progress_raw"],
            "may_cumulative_expenditure_raw": may["cumulative_expenditure_raw"],
            "june_cumulative_expenditure_raw": june["cumulative_expenditure_raw"],
            "may_revised_cost_raw": may["revised_cost_raw"],
            "june_revised_cost_raw": june["revised_cost_raw"],
            "may_revised_doc_raw": may["revised_doc_raw"],
            "june_revised_doc_raw": june["revised_doc_raw"],
            "may_source_id": may["source_id"], "may_source_sha256": may["source_sha256"],
            "may_pdf_page_index": may["pdf_page_index"],
            "may_printed_page_number": may["printed_page_number"],
            "may_raw_row_locator": may["raw_row_locator"],
            "june_source_id": june["source_id"], "june_source_sha256": june["source_sha256"],
            "june_pdf_page_index": june["pdf_page_index"],
            "june_printed_page_number": june["printed_page_number"],
            "june_raw_row_locator": june["raw_row_locator"],
        }
        diagnostics.append(row)
        flags = []
        if progress == "PROGRESS_DECREASE": flags.append("PHYSICAL_PROGRESS_DECREASE")
        if expenditure == "EXPENDITURE_DECREASE": flags.append("CUMULATIVE_EXPENDITURE_DECREASE")
        if changed["original_cost_changed"]: flags.append("ORIGINAL_COST_CHANGED")
        if changed["approval_date_changed"]: flags.append("APPROVAL_DATE_CHANGED")
        if changed["start_date_changed"]: flags.append("START_DATE_CHANGED")
        if changed["state_changed"]: flags.append("STATE_CHANGED")
        if changed["name_changed"]: flags.append("PROJECT_NAME_CHANGED")
        if flags:
            review.append({**row, "review_flags": "|".join(flags), "review_status": "REVIEW_REQUIRED"})
    return diagnostics, review, counts


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]], root: Path) -> None:
    path = ensure_parent(path, root)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite pilot artifact: {path}")
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _sample(
    diagnostics: list[dict[str, str]], review: list[dict[str, str]],
    master: list[dict[str, str]],
) -> list[dict[str, str]]:
    rng = random.Random(SAMPLE_SEED)
    selected: list[dict[str, str]] = []
    seen: set[str] = set()

    def choose(pool: list[dict[str, str]], count: int, category: str) -> None:
        candidates = [row for row in pool if row["canonical_project_id"] not in seen]
        for row in rng.sample(candidates, min(count, len(candidates))):
            seen.add(row["canonical_project_id"])
            selected.append({**row, "sample_category": category})

    stable = [row for row in diagnostics if row["name_changed"] == row["agency_changed"] == row["state_changed"] == "FALSE" and row["revised_cost_changed"] == row["revised_doc_changed"] == "FALSE"]
    choose(stable, 6, "ORDINARY_STABLE")
    choose([row for row in diagnostics if row["progress_category"] == "PROGRESS_INCREASE"], 4, "PROGRESS_CHANGE")
    choose([row for row in diagnostics if row["revised_cost_changed"] == "TRUE"], 4, "REVISED_COST_CHANGE")
    choose([row for row in diagnostics if row["revised_doc_changed"] == "TRUE"], 4, "REVISED_DOC_CHANGE")
    choose([row for row in diagnostics if row["name_changed"] == "TRUE" or row["agency_changed"] == "TRUE"], 3, "IDENTITY_METADATA_CHANGE")
    choose(review, 3, "SUSPICIOUS_REVIEW")
    choose([row for row in master if row["presence_status"] == "MAY_ONLY"], 3, "MAY_ONLY")
    choose([row for row in master if row["presence_status"] == "JUNE_ONLY"], 3, "JUNE_ONLY")
    if len(selected) < 30:
        choose(diagnostics, 30 - len(selected), "FILLER_VALIDATED_MATCH")
    manual = [
        "manual_history_correct", "manual_temporal_values_correct",
        "manual_provenance_correct", "reviewer", "review_notes",
    ]
    return [{**row, **{field: "" for field in manual}} for row in selected[:30]]


def build_pilot(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    may_path = root / "data/extracted/ongoing/ongoing_2026_05.csv"
    june_path = root / "data/extracted/ongoing/ongoing_2026_06.csv"
    if _sha(may_path) != MAY_CSV_SHA256 or _sha(june_path) != JUNE_CSV_SHA256:
        raise RuntimeError("Frozen input extraction hash mismatch")
    may, june = _read(may_path), _read(june_path)
    if len(may) != MAY_ROWS or len(june) != JUNE_ROWS:
        raise RuntimeError("Frozen input row count mismatch")
    manifest = root / "data/metadata/source_manifest.csv"
    may_source = resolve_source("SRC-2026-05", manifest, root)
    june_source = resolve_source("SRC-2026-06", manifest, root)
    provenance = _read(root / "data/metadata/provenance.csv")
    provenance_ids = {row["observation_id"] for row in provenance}
    if any(row["observation_id"] not in provenance_ids for row in may + june):
        raise RuntimeError("Missing source provenance for pilot observation")

    project_month = [to_project_month(row) for row in may + june]
    month_keys = [(row["canonical_project_id"], row["reporting_month"]) for row in project_month]
    if len(month_keys) != len(set(month_keys)):
        raise RuntimeError("Duplicate canonical project-month key")
    master = build_master(project_month)
    if len(master) != len({row["canonical_project_id"] for row in master}):
        raise RuntimeError("Duplicate canonical Project ID")
    if len(master) != 2009 or len(project_month) != 3834:
        raise RuntimeError("Pilot union or observation reconciliation failed")
    presence = Counter(row["presence_status"] for row in master)
    if presence != Counter({"MAY_AND_JUNE": 1825, "MAY_ONLY": 162, "JUNE_ONLY": 22}):
        raise RuntimeError(f"Presence reconciliation failed: {presence}")

    may_by_code = {row["project_code_raw"]: row for row in may}
    june_by_code = {row["project_code_raw"]: row for row in june}
    diagnostics, review, counts = build_temporal_diagnostics(may_by_code, june_by_code)
    sample = _sample(diagnostics, review, master)
    created_at = datetime.now(timezone.utc).isoformat()
    processed = root / "data/processed/pilot_2026_05_06"
    validation = root / "validation/longitudinal"
    _write_csv(processed / "project_master.csv", MASTER_FIELDS, master, root)
    _write_csv(processed / "project_month.csv", MONTH_FIELDS, project_month, root)
    _write_csv(validation / "may_june_2026_temporal_diagnostics.csv", list(diagnostics[0]), diagnostics, root)
    _write_csv(validation / "may_june_2026_temporal_review.csv", list(review[0]), review, root)
    sample_fields = sorted({field for row in sample for field in row})
    _write_csv(validation / "may_june_2026_manual_longitudinal_sample_30.csv", sample_fields, sample, root)

    summary = {
        "dataset_version": DATASET_VERSION, "may_observations": len(may),
        "june_observations": len(june), "project_union": len(master),
        "matched_projects": presence["MAY_AND_JUNE"], "may_only": presence["MAY_ONLY"],
        "june_only": presence["JUNE_ONLY"], "project_master_rows": len(master),
        "project_month_rows": len(project_month), "duplicate_master_ids": 0,
        "duplicate_project_month_keys": 0, "presence_categories": dict(presence),
        "name_changes": counts["name_changed"], "agency_changes": counts["agency_changed"],
        "state_changes": counts["state_changed"],
        "approval_date_changes": counts["approval_date_changed"],
        "start_date_changes": counts["start_date_changed"],
        "original_target_doc_changes": counts["original_target_doc_changed"],
        "original_cost_changes": counts["original_cost_changed"],
        "revised_cost_changes": counts["revised_cost_changed"],
        "revised_doc_changes": counts["revised_doc_changed"],
        "physical_progress_decreases": counts["PROGRESS_DECREASE"],
        "physical_progress_increases": counts["PROGRESS_INCREASE"],
        "physical_progress_unchanged": counts["PROGRESS_UNCHANGED"],
        "expenditure_decreases": counts["EXPENDITURE_DECREASE"],
        "expenditure_increases": counts["EXPENDITURE_INCREASE"],
        "expenditure_unchanged": counts["EXPENDITURE_UNCHANGED"],
        "temporal_review_rows": len(review), "manual_sample_rows": len(sample),
        "manual_sample_seed": SAMPLE_SEED,
    }
    write_json_replace(validation / "may_june_2026_longitudinal_summary.json", summary, repo_root=root)
    metadata = {
        "dataset_version": DATASET_VERSION, "created_at": created_at,
        "months_included": ["2026-05", "2026-06"],
        "input_file_hashes": {may_path.as_posix(): MAY_CSV_SHA256, june_path.as_posix(): JUNE_CSV_SHA256},
        "source_pdf_hashes": {may_source.source_id: may_source.sha256, june_source.source_id: june_source.sha256},
        "row_counts": {"project_master": len(master), "project_month": len(project_month)},
        "identity_method": "EXACT_PROJECT_CODE",
        "known_limitations": [
            "Identity rule validated only for May-June 2026.",
            "Presence does not establish completion, removal, or addition.",
            "Temporal movements are diagnostics, not corrected facts or ML features.",
            "Human longitudinal sample review is pending.",
        ],
    }
    write_json_replace(processed / "dataset_metadata.json", metadata, repo_root=root)
    report = ensure_parent(root / "outputs/reports/MAY_JUNE_2026_LONGITUDINAL_PILOT_REPORT.md", root)
    report.write_text(_render_report(summary, metadata), encoding="utf-8")
    return summary


def _render_report(s: dict[str, Any], metadata: dict[str, Any]) -> str:
    return f"""# May–June 2026 Longitudinal Pilot Report

## Inputs and identity

- Frozen May extraction: `{MAY_CSV_SHA256}` ({s['may_observations']} observations)
- Frozen June extraction: `{JUNE_CSV_SHA256}` ({s['june_observations']} observations)
- Identity method: exact raw Project Code
- Internal ID: `PRH-<project_code>`
- Dataset version: `{DATASET_VERSION}`

## Reconciliation

- Project union / master rows: {s['project_union']}
- Project-month observations: {s['project_month_rows']}
- May only / May and June / June only: {s['may_only']} / {s['matched_projects']} / {s['june_only']}
- Duplicate master IDs / project-month keys: 0 / 0

Presence is observational. It is not a completion, addition, cancellation, or
removal label.

## Historical/static-field diagnostics

- Name changes: {s['name_changes']}
- Agency changes: {s['agency_changes']}
- State changes: {s['state_changes']}
- Approval-date changes: {s['approval_date_changes']}
- Start-date changes: {s['start_date_changes']}
- Original-cost changes: {s['original_cost_changes']}
- Revised-cost changes: {s['revised_cost_changes']}
- Revised-DoC changes: {s['revised_doc_changes']}

Historical May values remain in the May ProjectMonth rows; June values never
overwrite them. Master `current_*` values mean latest reported values in this
two-month pilot only.

## Temporal diagnostics and review

- Physical-progress decreases: {s['physical_progress_decreases']}
- Cumulative-expenditure decreases: {s['expenditure_decreases']}
- Temporal-review rows: {s['temporal_review_rows']}

Flags are review diagnostics, not corrections, features, labels, outcomes, or
risk assessments. Every matched diagnostic and review row retains both source
observation IDs, SHAs, pages, and raw locators.

## Artifacts and limitations

- Manual sample: `validation/longitudinal/may_june_2026_manual_longitudinal_sample_30.csv`
- Known limitations: {json.dumps(metadata['known_limitations'], ensure_ascii=False)}

The pilot is ready for human longitudinal validation. Expansion to another
month or construction of completion/ML artifacts is not authorized by this run.
"""


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build May-June 2026 longitudinal pilot")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args()
    print(json.dumps(build_pilot(Path(args.repo_root)), indent=2, ensure_ascii=False))
