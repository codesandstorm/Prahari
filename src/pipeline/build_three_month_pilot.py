"""Build the validated April-May-June 2026 Gate 2 longitudinal pilot."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

from src.identity.continuity_audit import normalize_for_comparison
from src.pipeline.build_longitudinal_pilot import MONTH_FIELDS, to_project_month
from src.pipeline.source_registry import resolve_source
from src.utils.safe_io import ensure_parent, write_json_replace
from src.validation.provenance import validate_provenance_record

DATASET_VERSION = "gate2-pilot-2026-04-06-v1"
SEED = 26103
MONTHS = ("2026-04", "2026-05", "2026-06")
SOURCE_IDS = {"2026-04": "SRC-2026-04", "2026-05": "SRC-2026-05", "2026-06": "SRC-2026-06"}
FROZEN_HASHES = {
    "2026-04": "55d84996925b4d5d0f2bb3bc9367a685c2ad49a14c009acddc7662b0b9ee11dd",
    "2026-05": "f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e",
    "2026-06": "bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9",
}
EXPECTED_ROWS = {"2026-04": 1981, "2026-05": 1987, "2026-06": 1847}
METADATA_FIELDS = (
    "project_name_raw", "agency_raw", "state_raw", "approval_date_raw",
    "start_date_raw", "original_target_doc_raw", "revised_doc_raw",
    "original_cost_raw", "revised_cost_raw",
)
PRIMARY_FLAGS = (
    "PROJECT_NAME_CHANGED", "APPROVAL_DATE_CHANGED", "START_DATE_CHANGED",
    "ORIGINAL_COST_CHANGED", "PHYSICAL_PROGRESS_DECREASED",
    "CUMULATIVE_EXPENDITURE_DECREASED",
)
SECONDARY_FLAGS = (
    "AGENCY_CHANGED", "STATE_CHANGED", "ORIGINAL_TARGET_DOC_CHANGED",
    "REVISED_COST_CHANGED", "REVISED_DOC_CHANGED",
)
MANUAL_IDENTITY_FIELDS = ("manual_identity_confirmed", "manual_presence_pattern_confirmed", "manual_provenance_confirmed", "reviewer", "review_notes")
MANUAL_TEMPORAL_FIELDS = ("manual_values_confirmed", "manual_flags_confirmed", "manual_provenance_confirmed", "reviewer", "review_notes")

MASTER_FIELDS = [
    "canonical_project_id", "project_code", "first_observed_month",
    "latest_observed_month", "observation_count", "presence_pattern",
    "current_project_name", "current_agency", "current_state",
    "identity_method", "identity_status", "current_observation_id",
    "current_source_id", "current_source_sha256", "current_pdf_page_index",
    "current_printed_page_number", "current_source_table",
    "current_source_table_number", "current_raw_row_locator",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, rows: list[dict[str, Any]], fields: list[str], root: Path) -> None:
    path = ensure_parent(path, root)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def _decimal(value: str) -> Decimal | None:
    cleaned = value.strip().replace(",", "")
    if cleaned in {"", "-", "NA"}:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid numeric source value {value!r}") from exc


def canonical_id(code: str) -> str:
    if not code.strip() or code.strip() != code:
        raise ValueError("Project Code is missing or whitespace-ambiguous")
    return f"PRH-{code}"


def presence_pattern(months: set[str]) -> str:
    mapping = {
        frozenset(MONTHS): "APR_MAY_JUN",
        frozenset(("2026-04", "2026-05")): "APR_MAY_ONLY",
        frozenset(("2026-05", "2026-06")): "MAY_JUN_ONLY",
        frozenset(("2026-04", "2026-06")): "APR_JUN_ONLY",
        frozenset(("2026-04",)): "APR_ONLY",
        frozenset(("2026-05",)): "MAY_ONLY",
        frozenset(("2026-06",)): "JUN_ONLY",
    }
    try:
        return mapping[frozenset(months)]
    except KeyError as exc:
        raise ValueError(f"Unsupported presence inventory: {sorted(months)}") from exc


def _different(field: str, left: str, right: str) -> bool:
    if field in {"project_name_raw", "agency_raw", "state_raw"}:
        return normalize_for_comparison(left) != normalize_for_comparison(right)
    if field in {"original_cost_raw", "revised_cost_raw"}:
        return _decimal(left) != _decimal(right)
    return left.strip() != right.strip()


def pair_flags(left: dict[str, str], right: dict[str, str]) -> tuple[list[str], list[str]]:
    primary, secondary = [], []
    checks = (
        ("PROJECT_NAME_CHANGED", "project_name_raw", primary),
        ("AGENCY_CHANGED", "agency_raw", secondary),
        ("STATE_CHANGED", "state_raw", secondary),
        ("APPROVAL_DATE_CHANGED", "approval_date_raw", primary),
        ("START_DATE_CHANGED", "start_date_raw", primary),
        ("ORIGINAL_TARGET_DOC_CHANGED", "original_target_doc_raw", secondary),
        ("REVISED_DOC_CHANGED", "revised_doc_raw", secondary),
        ("ORIGINAL_COST_CHANGED", "original_cost_raw", primary),
        ("REVISED_COST_CHANGED", "revised_cost_raw", secondary),
    )
    for flag, field, target in checks:
        if _different(field, left[field], right[field]):
            target.append(flag)
    for flag, field in (("PHYSICAL_PROGRESS_DECREASED", "physical_progress_raw"), ("CUMULATIVE_EXPENDITURE_DECREASED", "cumulative_expenditure_raw")):
        before, after = _decimal(left[field]), _decimal(right[field])
        if before is not None and after is not None and after < before:
            primary.append(flag)
    return primary, secondary


def pair_continuity(left: list[dict[str, str]], right: list[dict[str, str]]) -> dict[str, Any]:
    left_index = _unique_index(left); right_index = _unique_index(right)
    common = sorted(set(left_index) & set(right_index), key=int)
    variations = []
    for code in common:
        fields = [field for field in METADATA_FIELDS if _different(field, left_index[code][field], right_index[code][field])]
        if fields:
            variations.append({"project_code": code, "canonical_project_id": canonical_id(code), "varying_fields": "|".join(fields), "evidence_class": "EXACT_CODE_WITH_METADATA_VARIATION"})
    return {
        "matches": len(common), "left_only": len(set(left_index)-set(right_index)),
        "right_only": len(set(right_index)-set(left_index)), "variations": variations,
        "verified_exact": len(common)-len(variations), "conflicts": 0, "ambiguous": 0,
    }


def _unique_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["project_code_raw"]].append(row)
    duplicates = [code for code, values in grouped.items() if len(values) != 1]
    if duplicates:
        raise RuntimeError(f"Duplicate Project Codes: {duplicates[:10]}")
    return {code: values[0] for code, values in grouped.items()}


def _build_master(month_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in month_rows:
        grouped[row["project_code"]].append(row)
    result = []
    for code in sorted(grouped, key=int):
        observations = sorted(grouped[code], key=lambda row: row["reporting_month"])
        months = {row["reporting_month"] for row in observations}
        if len(observations) != len(months):
            raise RuntimeError(f"Duplicate project-month for {code}")
        current = observations[-1]
        identity_fields = (
            "reported_project_name", "reported_agency", "reported_state",
            "reported_approval_date", "reported_start_date",
            "reported_original_target_doc", "reported_revised_doc",
            "reported_original_cost", "reported_revised_cost",
        )
        metadata_changed = any(
            observations[0][field].strip() != row[field].strip()
            for row in observations[1:] for field in identity_fields
        )
        result.append({
            "canonical_project_id": canonical_id(code), "project_code": code,
            "first_observed_month": observations[0]["reporting_month"], "latest_observed_month": current["reporting_month"],
            "observation_count": str(len(observations)), "presence_pattern": presence_pattern(months),
            "current_project_name": current["reported_project_name"], "current_agency": current["reported_agency"], "current_state": current["reported_state"],
            "identity_method": "EXACT_PROJECT_CODE", "identity_status": "EXACT_CODE_WITH_METADATA_VARIATION" if metadata_changed else "VERIFIED_EXACT_CODE",
            "current_observation_id": current["observation_id"], "current_source_id": current["source_id"], "current_source_sha256": current["source_sha256"],
            "current_pdf_page_index": current["pdf_page_index"], "current_printed_page_number": current["printed_page_number"],
            "current_source_table": current["source_table"], "current_source_table_number": current["source_table_number"], "current_raw_row_locator": current["raw_row_locator"],
        })
    return result


def _transition_rows(boundary: str, left: list[dict[str, str]], right: list[dict[str, str]]) -> list[dict[str, str]]:
    li, ri = _unique_index(left), _unique_index(right)
    result = []
    for code in sorted(set(li)&set(ri), key=int):
        primary, secondary = pair_flags(li[code], ri[code])
        result.append({
            "boundary": boundary, "canonical_project_id": canonical_id(code), "project_code": code,
            "left_observation_id": li[code]["observation_id"], "right_observation_id": ri[code]["observation_id"],
            "primary_flags": "|".join(primary), "secondary_flags": "|".join(secondary),
            "left_progress": li[code]["physical_progress_raw"], "right_progress": ri[code]["physical_progress_raw"],
            "left_expenditure": li[code]["cumulative_expenditure_raw"], "right_expenditure": ri[code]["cumulative_expenditure_raw"],
            "left_source_id": li[code]["source_id"], "left_pdf_page_index": li[code]["pdf_page_index"], "left_raw_row_locator": li[code]["raw_row_locator"],
            "right_source_id": ri[code]["source_id"], "right_pdf_page_index": ri[code]["pdf_page_index"], "right_raw_row_locator": ri[code]["raw_row_locator"],
        })
    return result


def _trajectory(code: str, rows: list[dict[str, str]]) -> dict[str, str]:
    values = {row["reporting_month"]: row for row in rows}
    def series(field: str) -> str:
        return " → ".join(values[month][field] for month in MONTHS)
    def numeric_reversal(field: str) -> str:
        nums = [_decimal(values[month][field]) for month in MONTHS]
        if any(value is None for value in nums): return "NOT_COMPARABLE"
        first, second = nums[1]-nums[0], nums[2]-nums[1]
        if first > 0 and second < 0: return "INCREASE_THEN_DECREASE"
        if first < 0 and second > 0: return "DECREASE_THEN_INCREASE"
        return "NONE"
    def metadata_revert(field: str) -> str:
        vals = [normalize_for_comparison(values[m][field]) for m in MONTHS]
        return "CHANGED_THEN_REVERTED" if vals[0] != vals[1] and vals[0] == vals[2] else "NONE"
    return {
        "canonical_project_id": canonical_id(code), "project_code": code,
        "progress_trajectory": series("physical_progress_raw"), "expenditure_trajectory": series("cumulative_expenditure_raw"),
        "revised_cost_trajectory": series("revised_cost_raw"), "revised_doc_trajectory": series("revised_doc_raw"),
        "progress_reversal": numeric_reversal("physical_progress_raw"), "expenditure_reversal": numeric_reversal("cumulative_expenditure_raw"),
        "revised_cost_reversal": numeric_reversal("revised_cost_raw"), "project_name_reversion": metadata_revert("project_name_raw"),
        "agency_reversion": metadata_revert("agency_raw"), "state_reversion": metadata_revert("state_raw"),
    }


def _sample(rows: list[dict[str, Any]], categories: list[tuple[str, Callable[[dict[str, Any]], bool], int]], manual_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    rng = random.Random(SEED); chosen: dict[str, dict[str, Any]] = {}; labels: dict[str, list[str]] = defaultdict(list)
    for label, predicate, count in categories:
        if len(chosen) == 30:
            break
        candidates = [row for row in rows if predicate(row) and row["canonical_project_id"] not in chosen]
        for row in rng.sample(candidates, min(count, len(candidates), 30-len(chosen))):
            chosen[row["canonical_project_id"]] = row; labels[row["canonical_project_id"]].append(label)
    remaining = [row for row in rows if row["canonical_project_id"] not in chosen]
    for row in rng.sample(remaining, min(30-len(chosen), len(remaining))):
        chosen[row["canonical_project_id"]] = row; labels[row["canonical_project_id"]].append("DETERMINISTIC_FILL")
    selected = sorted(chosen.values(), key=lambda row: int(row["project_code"]))[:30]
    return [{**row, "sample_categories": "|".join(labels[row["canonical_project_id"]]), **{field: "" for field in manual_fields}} for row in selected]


def build_three_month_pilot(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve(); manifest = root / "data/metadata/source_manifest.csv"
    paths = {month: root / f"data/extracted/ongoing/ongoing_{month.replace('-', '_')}.csv" for month in MONTHS}
    for month, path in paths.items():
        if _sha(path) != FROZEN_HASHES[month]: raise RuntimeError(f"Frozen {month} extraction hash mismatch")
    raw = {month: _read(path) for month, path in paths.items()}
    for month in MONTHS:
        if len(raw[month]) != EXPECTED_ROWS[month]: raise RuntimeError(f"Frozen {month} row count mismatch")
        _unique_index(raw[month])
    april_may = pair_continuity(raw["2026-04"], raw["2026-05"])
    may_june = pair_continuity(raw["2026-05"], raw["2026-06"])
    if (may_june["matches"], may_june["left_only"], may_june["right_only"]) != (1825, 162, 22):
        raise RuntimeError("May-June recomputation differs from frozen evidence")
    month_rows = [to_project_month(row) for month in MONTHS for row in raw[month]]
    keys = [(row["canonical_project_id"], row["reporting_month"]) for row in month_rows]
    if len(keys) != len(set(keys)) or len(month_rows) != sum(len(raw[m]) for m in MONTHS):
        raise RuntimeError("Three-month row reconciliation failed")
    master = _build_master(month_rows); master_index = {row["project_code"]: row for row in master}
    pattern_counts = Counter(row["presence_pattern"] for row in master)
    transitions = _transition_rows("APR_TO_MAY", raw["2026-04"], raw["2026-05"]) + _transition_rows("MAY_TO_JUN", raw["2026-05"], raw["2026-06"])
    grouped_month: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in raw["2026-04"] + raw["2026-05"] + raw["2026-06"]: grouped_month[row["project_code_raw"]].append(row)
    three_codes = sorted(set(_unique_index(raw["2026-04"])) & set(_unique_index(raw["2026-05"])) & set(_unique_index(raw["2026-06"])), key=int)
    trajectories = [_trajectory(code, grouped_month[code]) for code in three_codes]
    transition_by_code: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in transitions: transition_by_code[row["project_code"]][row["boundary"]] = row
    flagged_codes = sorted({row["project_code"] for row in transitions if row["primary_flags"]}, key=int)
    gap_codes = {row["project_code"] for row in master if row["presence_pattern"] == "APR_JUN_ONLY"}
    exhaustive = []; temporal_candidates = []
    indexes = {m: _unique_index(raw[m]) for m in MONTHS}; trajectory_index = {r["project_code"]: r for r in trajectories}
    month_prefix = {"2026-04": "april", "2026-05": "may", "2026-06": "june"}
    for code in sorted(set(flagged_codes) | gap_codes, key=int):
        row: dict[str, str] = {"canonical_project_id": canonical_id(code), "project_code": code, "presence_pattern": master_index[code]["presence_pattern"]}
        for month in MONTHS:
            prefix = month_prefix[month]; source = indexes[month].get(code)
            for source_field, label in (("project_name_raw","project_name"),("agency_raw","agency"),("state_raw","state"),("approval_date_raw","approval_date"),("start_date_raw","start_date"),("original_target_doc_raw","original_target_doc"),("revised_doc_raw","revised_doc"),("original_cost_raw","original_cost"),("revised_cost_raw","revised_cost"),("cumulative_expenditure_raw","cumulative_expenditure"),("physical_progress_raw","physical_progress"),("source_id","source_id"),("source_sha256","source_sha256"),("pdf_page_index","pdf_page_index"),("printed_page_number","printed_page_number"),("raw_row_locator","raw_row_locator")):
                row[f"{prefix}_{label}"] = "" if source is None else source[source_field]
        for boundary in ("APR_TO_MAY", "MAY_TO_JUN"):
            transition = transition_by_code[code].get(boundary, {})
            row[f"{boundary.lower()}_primary_flags"] = transition.get("primary_flags", "")
            row[f"{boundary.lower()}_secondary_flags"] = transition.get("secondary_flags", "")
        row.update(trajectory_index.get(code, {field: "" for field in ("progress_trajectory","expenditure_trajectory","revised_cost_trajectory","revised_doc_trajectory","progress_reversal","expenditure_reversal","revised_cost_reversal","project_name_reversion","agency_reversion","state_reversion")}))
        temporal_candidates.append(row)
        if code in flagged_codes:
            exhaustive.append(row)
    gap_rows = [row for row in master if row["presence_pattern"] == "APR_JUN_ONLY"]
    gap_review = []
    for item in gap_rows:
        code=item["project_code"]; a=indexes["2026-04"][code]; j=indexes["2026-06"][code]
        gap_review.append({"canonical_project_id":canonical_id(code),"project_code":code,"presence_pattern":"APR_JUN_ONLY","may_absence_verified":"YES","april_source_id":a["source_id"],"april_source_sha256":a["source_sha256"],"april_pdf_page_index":a["pdf_page_index"],"april_raw_row_locator":a["raw_row_locator"],"june_source_id":j["source_id"],"june_source_sha256":j["source_sha256"],"june_pdf_page_index":j["pdf_page_index"],"june_raw_row_locator":j["raw_row_locator"],"manual_gap_confirmed":"","reviewer":"","review_notes":""})
    provenance_errors=[]; locators=[]
    for row in month_rows:
        provenance_errors.extend(validate_provenance_record(row, manifest))
        source=resolve_source(row["source_id"],manifest,root)
        if row["reporting_month"] != f"{source.report_year:04d}-{source.report_month:02d}": provenance_errors.append("reporting month/source mismatch")
        if row["source_table"] != "All Ongoing Projects" or row["source_table_number"] != "6": provenance_errors.append("table mismatch")
        locators.append((row["source_id"],row["raw_row_locator"]))
    if provenance_errors or len(locators)!=len(set(locators)): raise RuntimeError("Three-month provenance validation failed")
    identity_rows=[]
    for row in master:
        code=row["project_code"]; source_rows=grouped_month[code]
        changed=sum(any(_different(field, source_rows[i][field],source_rows[i+1][field]) for i in range(len(source_rows)-1)) for field in METADATA_FIELDS) if len(source_rows)>1 else 0
        identity_row={**row,"metadata_change_count":str(changed),"months":"|".join(sorted(r["reporting_month"] for r in source_rows))}
        by_month={source["reporting_month"]:source for source in source_rows}
        for month in MONTHS:
            prefix=month_prefix[month]; source=by_month.get(month)
            for source_field, label in (
                ("project_name_raw", "project_name"), ("agency_raw", "agency"),
                ("source_id", "source_id"), ("source_sha256", "source_sha256"),
                ("pdf_page_index", "pdf_page_index"),
                ("printed_page_number", "printed_page_number"),
                ("raw_row_locator", "raw_row_locator"),
            ):
                identity_row[f"{prefix}_{label}"]="" if source is None else source[source_field]
        identity_rows.append(identity_row)
    identity_sample=_sample(identity_rows,[
        ("STABLE_ALL_THREE",lambda r:r["presence_pattern"]=="APR_MAY_JUN" and r["metadata_change_count"]=="0",6),
        ("ALL_THREE_VARIATION",lambda r:r["presence_pattern"]=="APR_MAY_JUN" and int(r["metadata_change_count"])>0,6),
        ("APR_ONLY",lambda r:r["presence_pattern"]=="APR_ONLY",3),("MAY_ONLY",lambda r:r["presence_pattern"]=="MAY_ONLY",3),("JUN_ONLY",lambda r:r["presence_pattern"]=="JUN_ONLY",3),
        ("APR_MAY_ONLY",lambda r:r["presence_pattern"]=="APR_MAY_ONLY",3),("MAY_JUN_ONLY",lambda r:r["presence_pattern"]=="MAY_JUN_ONLY",3),("APR_JUN_GAP",lambda r:r["presence_pattern"]=="APR_JUN_ONLY",3),
    ],MANUAL_IDENTITY_FIELDS)
    temporal_sample=_sample(temporal_candidates,[
        ("APR_JUN_GAP",lambda r:r["presence_pattern"]=="APR_JUN_ONLY",1),
        ("PROJECT_NAME_CHANGE",lambda r:"PROJECT_NAME_CHANGED" in r["apr_to_may_primary_flags"]+r["may_to_jun_primary_flags"],1),
        ("APPROVAL_DATE_CHANGE",lambda r:"APPROVAL_DATE_CHANGED" in r["apr_to_may_primary_flags"]+r["may_to_jun_primary_flags"],1),
        ("START_DATE_CHANGE",lambda r:"START_DATE_CHANGED" in r["apr_to_may_primary_flags"]+r["may_to_jun_primary_flags"],1),
        ("ORIGINAL_COST_CHANGE",lambda r:"ORIGINAL_COST_CHANGED" in r["apr_to_may_primary_flags"]+r["may_to_jun_primary_flags"],2),
        ("APR_TO_MAY_FLAG",lambda r:bool(r["apr_to_may_primary_flags"]),6),("MAY_TO_JUN_FLAG",lambda r:bool(r["may_to_jun_primary_flags"]),6),
        ("REVERSAL",lambda r:any(r.get(f) not in {"","NONE","NOT_COMPARABLE"} for f in ("progress_reversal","expenditure_reversal","revised_cost_reversal","project_name_reversion","agency_reversion","state_reversion")),5),
        ("PROGRESS_DECREASE",lambda r:"PHYSICAL_PROGRESS_DECREASED" in r["apr_to_may_primary_flags"]+r["may_to_jun_primary_flags"],3),
        ("EXPENDITURE_DECREASE",lambda r:"CUMULATIVE_EXPENDITURE_DECREASED" in r["apr_to_may_primary_flags"]+r["may_to_jun_primary_flags"],3),
    ],MANUAL_TEMPORAL_FIELDS)
    processed=root/"data/processed/pilot_2026_04_06"; identity_dir=root/"validation/identity_continuity"; long_dir=root/"validation/longitudinal"
    _write(processed/"project_master.csv",master,MASTER_FIELDS,root); _write(processed/"project_month.csv",month_rows,MONTH_FIELDS,root)
    _write(identity_dir/"april_may_2026_metadata_variations.csv",april_may["variations"],list(april_may["variations"][0]) if april_may["variations"] else ["project_code","canonical_project_id","varying_fields","evidence_class"],root)
    _write(identity_dir/"april_may_june_2026_identity_chains.csv",identity_rows,list(identity_rows[0]),root)
    _write(identity_dir/"april_may_june_2026_presence_gap_review.csv",gap_review,list(gap_review[0]) if gap_review else ["canonical_project_id","project_code","presence_pattern"],root)
    _write(identity_dir/"april_may_june_2026_manual_identity_sample.csv",identity_sample,list(identity_sample[0]),root)
    _write(long_dir/"april_may_june_2026_transitions.csv",transitions,list(transitions[0]),root)
    _write(long_dir/"april_may_june_2026_trajectories.csv",trajectories,list(trajectories[0]),root)
    _write(long_dir/"april_may_june_2026_temporal_review.csv",exhaustive,list(exhaustive[0]),root)
    _write(long_dir/"april_may_june_2026_temporal_sample.csv",temporal_sample,list(temporal_sample[0]),root)
    flag_counts={}
    for boundary in ("APR_TO_MAY","MAY_TO_JUN"):
        rows=[r for r in transitions if r["boundary"]==boundary]; flag_counts[boundary]={flag:sum(flag in r["primary_flags"].split("|") for r in rows) for flag in PRIMARY_FLAGS}; flag_counts[boundary].update({flag:sum(flag in r["secondary_flags"].split("|") for r in rows) for flag in SECONDARY_FLAGS})
    all_three_variations={field:sum(any(_different(field,grouped_month[c][i][field],grouped_month[c][i+1][field]) for i in (0,1)) for c in three_codes) for field in METADATA_FIELDS}
    reversal_counts={field:sum(row[field] not in {"NONE","NOT_COMPARABLE"} for row in trajectories) for field in ("progress_reversal","expenditure_reversal","revised_cost_reversal","project_name_reversion","agency_reversion","state_reversion")}
    summary={"dataset_version":DATASET_VERSION,"input_hashes":FROZEN_HASHES,"monthly_rows":{m:len(raw[m]) for m in MONTHS},"april_may":{k:v for k,v in april_may.items() if k!="variations"},"may_june":{k:v for k,v in may_june.items() if k!="variations"},"three_month_intersection":len(three_codes),"unique_project_union":len(master),"presence_patterns":dict(pattern_counts),"duplicate_project_codes":{m:0 for m in MONTHS},"identity_conflicts":0,"ambiguous_cases":0,"all_three_metadata_variations":all_three_variations,"project_master_rows":len(master),"project_month_rows":len(month_rows),"duplicate_canonical_ids":0,"duplicate_project_month_keys":0,"flag_counts":flag_counts,"reversal_counts":reversal_counts,"presence_gap_cases":len(gap_rows),"provenance_failures":0,"duplicate_locators":0,"identity_sample_rows":len(identity_sample),"temporal_sample_rows":len(temporal_sample),"exhaustive_review_rows":len(exhaustive)}
    write_json_replace(long_dir/"april_may_june_2026_longitudinal_summary.json",summary,repo_root=root)
    write_json_replace(processed/"dataset_metadata.json",{"dataset_version":DATASET_VERSION,"months_included":list(MONTHS),"input_hashes":FROZEN_HASHES,"row_counts":{"project_master":len(master),"project_month":len(month_rows)},"identity_method":"EXACT_PROJECT_CODE_VALIDATED_PAIMANA_V2_PERIOD","limitations":["Presence patterns have no completion/addition/removal semantics.","April manual validation is recorded separately from the still-empty sample columns.","Identity rule is not generalized beyond April-June 2026.","No labels, features, outcomes, predictions, or risk values exist."]},repo_root=root)
    report=ensure_parent(root/"outputs/reports/APRIL_MAY_JUNE_2026_LONGITUDINAL_PILOT_REPORT.md",root)
    report.write_text(_render_report(summary),encoding="utf-8")
    return summary


def _render_report(s: dict[str, Any]) -> str:
    return f"""# April-May-June 2026 Longitudinal Pilot Report

## Dataset and inputs

- Version: `{s['dataset_version']}`
- Frozen extraction hashes: `{json.dumps(s['input_hashes'], sort_keys=True)}`
- Monthly rows: `{json.dumps(s['monthly_rows'], sort_keys=True)}`
- Project-month rows: {s['project_month_rows']}
- Unique project union: {s['unique_project_union']}
- Three-month exact intersection: {s['three_month_intersection']}

## Identity continuity

- April-May: `{json.dumps(s['april_may'], sort_keys=True)}`
- May-June independently recomputed: `{json.dumps(s['may_june'], sort_keys=True)}`
- Presence patterns: `{json.dumps(s['presence_patterns'], sort_keys=True)}`
- Duplicate Project Codes / canonical IDs / project-month keys: 0 / 0 / 0
- Identity conflicts / ambiguous accepted links: 0 / 0

Presence patterns describe observation availability only. They do not mean new, completed, dropped, terminated, or cancelled.

## Metadata and temporal diagnostics

- All-three metadata variations: `{json.dumps(s['all_three_metadata_variations'], sort_keys=True)}`
- Boundary flag counts: `{json.dumps(s['flag_counts'], sort_keys=True)}`
- Descriptive reversal counts: `{json.dumps(s['reversal_counts'], sort_keys=True)}`
- April-June presence-gap cases: {s['presence_gap_cases']}
- Exhaustive primary-flag review projects: {s['exhaustive_review_rows']}

Changes and reversals are preserved source observations for review. They are not corrected or interpreted as risk.

## Provenance and review

- Provenance failures: {s['provenance_failures']}
- Duplicate source/locator keys: {s['duplicate_locators']}
- Identity sample: `validation/identity_continuity/april_may_june_2026_manual_identity_sample.csv`
- Temporal sample: `validation/longitudinal/april_may_june_2026_temporal_sample.csv`
- Exhaustive review: `validation/longitudinal/april_may_june_2026_temporal_review.csv`
- Presence-gap review: `validation/identity_continuity/april_may_june_2026_presence_gap_review.csv`

## Limits

This pilot uses exact Project Code only for the validated April-June PAIMANA V2 period. It preserves every monthly value and source locator. No completion inference, outcome, target, label, feature, prediction, risk score, confidence score, or alert priority was created. Human validation of the new identity and temporal artifacts remains required.
"""


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[2])); args=parser.parse_args()
    print(json.dumps(build_three_month_pilot(Path(args.repo_root)),indent=2,ensure_ascii=False))
