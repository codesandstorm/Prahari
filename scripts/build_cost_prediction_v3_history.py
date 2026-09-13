"""Audit and build the immutable-source Cost Prediction V3 history.

The external raw archive is read-only.  A month is admitted only after internal
month evidence, PDF integrity, exact project identity, and complete serial/row
accounting all pass.  Existing V2 artifacts are inputs and are never rewritten.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.final_prediction import add_month
from src.ml.prediction_research_v2 import dataset_fingerprint, read_csv, write_csv
from src.pipeline.build_mixed_coverage_dataset import discover_table, extract_project_month, sha256

START, END = "2018-01", "2022-06"
V2_DATA = ROOT / "data/processed/longitudinal_2022_08_2026_06_research_v2"
V3_DATA = ROOT / "data/processed/longitudinal_2018_01_2026_06_cost_research_v3"
OUT = ROOT / "outputs/ml/cost_prediction_v3"
INVENTORY_META = ROOT / "data/metadata/cost_v3_source_inventory_2018_01_2022_06.csv"


def months(start: str, end: str) -> list[str]:
    result, current = [], start
    while current <= end:
        result.append(current)
        current = add_month(current, 1)
    return result


def _portable(month: str) -> str:
    year, number = month.split("-")
    return f"data/raw/{year}/FlashReport_{year}_{number}.pdf"


def _internal_month_evidence(document: pymupdf.Document, month: str) -> tuple[str, str]:
    year, number = month.split("-")
    month_name = __import__("calendar").month_name[int(number)]
    opening = "\n".join(document[index].get_text("text") for index in range(min(10, document.page_count)))
    normalized = re.sub(r"\s+", " ", opening)
    exact = re.search(rf"(?i)\b{month_name}\s*,?\s+{year}\b", normalized)
    numeric = re.search(rf"(?<!\d){int(number):02d}[/-]{year}(?!\d)", normalized)
    status = "VERIFIED_MONTH" if exact or numeric else "MONTH_AMBIGUOUS"
    return status, (exact.group(0) if exact else numeric.group(0) if numeric else "")


def inventory_one(raw_root: Path, month: str) -> dict[str, object]:
    year, number = month.split("-")
    path = raw_root / year / f"FlashReport_{year}_{number}.pdf"
    base: dict[str, object] = {
        "reporting_month": month, "expected_path": _portable(month), "file_exists": path.is_file(),
        "filename": path.name, "file_size_bytes": path.stat().st_size if path.is_file() else 0,
    }
    if not path.is_file():
        return {**base, "sha256": "", "pdf_page_count": 0, "pdf_readable": "NO",
                "text_extractable": "NO", "first_page_title_header": "", "internal_month_evidence": "",
                "month_verification_status": "MISSING", "apparent_source_organization": "UNKNOWN",
                "pdf_eof_marker": "NO", "encrypted": "UNKNOWN", "schema_discovery_status": "MISSING",
                "schema_family": "UNKNOWN", "schema_layout": "UNKNOWN", "table_first_page": "",
                "table_last_page": "", "stated_project_count": "", "notes": "MISSING_SOURCE"}
    digest = sha256(path)
    eof = b"%%EOF" in path.read_bytes()[-4096:]
    try:
        document = pymupdf.open(path)
        readable = document.page_count > 0
        sample = "\n".join(document[index].get_text("text") for index in range(min(3, document.page_count)))
        first = re.sub(r"\s+", " ", document[0].get_text("text")).strip()[:500]
        month_status, evidence = _internal_month_evidence(document, month)
        organization = "MOSPI_IPMD" if re.search(r"(?i)(Ministry of Statistics|Infrastructure.*Project Monitoring)", sample) else "UNKNOWN"
        encrypted = "YES" if document.needs_pass else "NO"
        page_count = document.page_count
        document.close()
    except Exception as exc:
        return {**base, "sha256": digest, "pdf_page_count": 0, "pdf_readable": "NO",
                "text_extractable": "NO", "first_page_title_header": "", "internal_month_evidence": "",
                "month_verification_status": "UNREADABLE", "apparent_source_organization": "UNKNOWN",
                "pdf_eof_marker": "YES" if eof else "NO", "encrypted": "UNKNOWN",
                "schema_discovery_status": "UNREADABLE", "schema_family": "UNKNOWN", "schema_layout": "UNKNOWN",
                "table_first_page": "", "table_last_page": "", "stated_project_count": "",
                "notes": f"PDF_OPEN_ERROR:{type(exc).__name__}"}
    try:
        discovery = discover_table(path)
        schema_status, family = "PROJECT_TABLE_DISCOVERED", discovery["schema_family"]
        first_page, last_page = discovery["first_page"], discovery["last_page"]
        stated = discovery.get("official_project_count") or ""
    except Exception as exc:
        probe = pymupdf.open(path)
        annexure_pages = [index + 1 for index, page in enumerate(probe)
                          if re.search(r"(?i)Details? of Ongoing Projects having", page.get_text("text"))]
        probe.close()
        if annexure_pages:
            schema_status, family = "PARTIAL_PROJECT_ANNEXURES", "OCMS_STATUS_ANNEXURES"
            first_page, last_page = min(annexure_pages), max(annexure_pages)
        else:
            schema_status, family = "SCHEMA_UNKNOWN", "UNKNOWN"
            first_page = last_page = ""
        stated = ""
        discovery = {}
    notes = []
    if not eof: notes.append("EOF_MARKER_NOT_IN_FINAL_4KB")
    if month_status != "VERIFIED_MONTH": notes.append(month_status)
    if schema_status != "PROJECT_TABLE_DISCOVERED": notes.append("NO_COMPLETE_PROJECT_TABLE_DISCOVERED")
    return {**base, "sha256": digest, "pdf_page_count": page_count,
            "pdf_readable": "YES" if readable else "NO", "text_extractable": "YES" if sample.strip() else "NO",
            "first_page_title_header": first, "internal_month_evidence": evidence,
            "month_verification_status": month_status, "apparent_source_organization": organization,
            "pdf_eof_marker": "YES" if eof else "NO", "encrypted": encrypted,
            "schema_discovery_status": schema_status, "schema_family": family, "schema_layout": "PENDING_ROW_AUDIT",
            "table_first_page": first_page, "table_last_page": last_page, "stated_project_count": stated,
            "notes": "|".join(notes)}


def extraction_worker(raw_root_text: str, month: str) -> dict[str, object]:
    raw_root = Path(raw_root_text)
    year, number = month.split("-")
    path = raw_root / year / f"FlashReport_{year}_{number}.pdf"
    try:
        discovery = discover_table(path)
        rows, summary = extract_project_month(path, month, discovery)
        layouts = Counter(row.get("schema_layout", "OCMS_7_COMPOUND") for row in rows)
        return {"month": month, "status": "PASS", "rows": rows, "summary": summary,
                "schema_layout": "|".join(f"{key}:{value}" for key, value in sorted(layouts.items()))}
    except Exception as exc:
        return {"month": month, "status": "FAIL", "error": f"{type(exc).__name__}:{exc}"[:12000]}


def _known_later_hashes() -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    ledger = V2_DATA / "source_ledger.csv"
    if ledger.is_file():
        for row in read_csv(ledger):
            if row.get("sha256"):
                result[row["sha256"]].append(row.get("reporting_month", "UNKNOWN"))
    return result


def _set_report_links(rows: list[dict[str, object]]) -> None:
    by_project: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_project[str(row["canonical_project_id"])].append(row)
    for observations in by_project.values():
        observations.sort(key=lambda row: str(row["reporting_month"]))
        for index, row in enumerate(observations):
            previous = str(observations[index - 1]["reporting_month"]) if index else ""
            following = str(observations[index + 1]["reporting_month"]) if index + 1 < len(observations) else ""
            row["previous_project_observation_month"] = previous
            row["next_project_observation_month"] = following
            row["months_since_previous_project_observation"] = "" if not previous else _distance(previous, str(row["reporting_month"]))
            row["months_to_next_project_observation"] = "" if not following else _distance(str(row["reporting_month"]), following)
            row["calendar_gap_present"] = "TRUE" if previous and add_month(previous, 1) != row["reporting_month"] else "FALSE"


def _distance(left: str, right: str) -> int:
    return (int(right[:4]) - int(left[:4])) * 12 + int(right[5:]) - int(left[5:])


def build(raw_root: Path, workers: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    expected = months(START, END)
    inventory = [inventory_one(raw_root, month) for month in expected]
    later_hashes = _known_later_hashes()
    groups: dict[str, list[str]] = defaultdict(list)
    for row in inventory:
        if row["sha256"]:
            groups[str(row["sha256"])].append(str(row["reporting_month"]))
    for row in inventory:
        digest = str(row["sha256"])
        same = groups.get(digest, [])
        later = later_hashes.get(digest, [])
        row["duplicate_hash_status"] = "UNIQUE" if len(same) == 1 and not later else "DUPLICATE_SOURCE"
        row["duplicate_with_months"] = "|".join(sorted(set(same + later) - {str(row["reporting_month"])}))
        row["candidate_duplicate_status"] = "SUSPICIOUS" if row["duplicate_hash_status"] != "UNIQUE" else "NONE"
    write_csv(INVENTORY_META, inventory)
    write_csv(OUT / "source_inventory.csv", inventory)
    (OUT / "source_inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    eligible = [str(row["reporting_month"]) for row in inventory
                if row["month_verification_status"] == "VERIFIED_MONTH"
                and row["pdf_readable"] == "YES" and row["text_extractable"] == "YES"
                and row["duplicate_hash_status"] == "UNIQUE"
                and row["schema_discovery_status"] == "PROJECT_TABLE_DISCOVERED"]
    extracted: dict[str, dict[str, object]] = {}
    with ProcessPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(extraction_worker, str(raw_root), month): month for month in eligible}
        for future in as_completed(futures):
            result = future.result()
            extracted[str(result["month"])] = result
            print(json.dumps({key: value for key, value in result.items() if key != "rows" and key != "summary"}), flush=True)

    admission, accounting, accepted_rows = [], [], []
    inv_by_month = {str(row["reporting_month"]): row for row in inventory}
    for month in expected:
        inv = inv_by_month[month]
        result = extracted.get(month)
        if result and result["status"] == "PASS":
            rows = result["rows"]  # type: ignore[assignment]
            summary = result["summary"]  # type: ignore[assignment]
            for row in rows:  # type: ignore[union-attr]
                code = str(row.get("project_code_raw", "")).strip()
                row.update(canonical_project_id=f"PRH-{code}", project_code=code,
                           identity_status="RESOLVED_EXACT", identity_method="EXACT_AUTHORITATIVE_PROJECT_CODE",
                           reported_project_name=row.get("project_name_raw", ""), reported_agency=row.get("agency_raw", ""),
                           reported_state=row.get("state_raw", ""), reported_approval_date=row.get("approval_date_raw", ""),
                           reported_original_target_doc=row.get("original_target_doc_raw", ""), reported_revised_doc=row.get("revised_doc_raw", ""),
                           reported_original_cost=row.get("original_cost_raw", ""), reported_revised_cost=row.get("revised_cost_raw", ""),
                           reported_cumulative_expenditure=row.get("cumulative_expenditure_raw", ""),
                           reported_physical_progress=row.get("physical_progress_raw", ""), reported_start_date=row.get("start_date_raw", ""))
            accepted_rows.extend(rows)  # type: ignore[arg-type]
            accepted = len(rows)  # type: ignore[arg-type]
            layout = str(result["schema_layout"])
            month_status, reason = "ADMIT_COST_TARGET", "complete row accounting; exact bracketed project codes; explicit crore header"
            accounting.append({"month": month, "stated_count": summary["official_project_count"], "parsed_count": accepted,
                               "difference": accepted - int(summary["official_project_count"]), "recovered_count": summary["ocms_footer_serials_recovered"],
                               "unresolved_count": len(summary["unresolved_rows"]), "duplicate_count": summary["duplicate_serials"],
                               "accepted_count": accepted, "serial_min": summary["serial_min"], "serial_max": summary["serial_max"],
                               "table_first_page": summary["first_page"], "table_last_page": summary["last_page"], "status": "PASS"})
            inv["schema_layout"] = layout
        else:
            accepted, layout = 0, str(inv.get("schema_layout", "UNKNOWN"))
            if inv["duplicate_hash_status"] != "UNIQUE": month_status, reason = "REJECT_DUPLICATE", str(inv["duplicate_with_months"])
            elif inv["month_verification_status"] != "VERIFIED_MONTH": month_status, reason = "QUARANTINE_SEMANTICS", str(inv["month_verification_status"])
            elif inv["schema_discovery_status"] == "PARTIAL_PROJECT_ANNEXURES": month_status, reason = "QUARANTINE_SEMANTICS", "status-specific annexures do not evidence one complete non-overlapping project universe"
            elif inv["schema_discovery_status"] != "PROJECT_TABLE_DISCOVERED": month_status, reason = "QUARANTINE_PARSER", "complete non-overlapping project table not evidenced"
            else:
                reason = str((result or {}).get("error", "extraction not run"))
                month_status = "QUARANTINE_SEMANTICS" if "official=" in reason and "accepted=" in reason and "unresolved=0" in reason else "QUARANTINE_PARSER"
            accounting.append({"month": month, "stated_count": inv["stated_project_count"], "parsed_count": 0,
                               "difference": "", "recovered_count": 0, "unresolved_count": "UNKNOWN", "duplicate_count": "UNKNOWN",
                               "accepted_count": 0, "serial_min": "", "serial_max": "", "table_first_page": inv["table_first_page"],
                               "table_last_page": inv["table_last_page"], "status": month_status, "reason": reason})
        admission.append({"month": month, "source_status": month_status, "schema_family": inv["schema_family"],
                          "schema_layout": layout, "project_level": "YES" if month_status == "ADMIT_COST_TARGET" else "UNKNOWN",
                          "stated_rows": inv["stated_project_count"], "parsed_rows": accepted, "accepted_rows": accepted,
                          "identity_support": "EXACT_PROJECT_CODE" if accepted else "NOT_ADMITTED",
                          "original_cost_support": "YES" if accepted else "NOT_ADMITTED",
                          "revised_cost_support": "YES" if accepted else "NOT_ADMITTED",
                          "anticipated_cost_support": "SEPARATE_FIELD" if accepted else "NOT_ADMITTED",
                          "expenditure_support": "SEPARATE_FIELD" if accepted else "NOT_ADMITTED",
                          "completion_support": "SCHEDULE/STATUS_FIELDS_ONLY; DISAPPEARANCE_NOT_COMPLETION" if accepted else "NOT_ADMITTED",
                          "cost_target_compatible": "YES" if accepted else "NO", "reason": reason,
                          "sha256": inv["sha256"], "page_count": inv["pdf_page_count"],
                          "provenance_status": "SOURCE_PROVENANCE_PARTIAL"})
    write_csv(OUT / "source_admission_ledger.csv", admission)
    write_csv(OUT / "row_accounting.csv", accounting)
    write_csv(OUT / "source_inventory.csv", inventory)

    v2_rows: list[dict[str, object]] = list(read_csv(V2_DATA / "project_month.csv"))
    existing_ids = {str(row.get("project_code_raw", "")): str(row["canonical_project_id"]) for row in v2_rows if row.get("project_code_raw")}
    for row in accepted_rows:
        code = str(row["project_code_raw"])
        row["canonical_project_id"] = existing_ids.get(code, f"PRH-{code}")
    all_rows = v2_rows + accepted_rows
    fields = sorted({key for row in all_rows for key in row})
    for row in all_rows:
        for field in fields:
            row.setdefault(field, "")
    all_rows.sort(key=lambda row: (str(row["reporting_month"]), str(row["canonical_project_id"])))
    keys = [(str(row["canonical_project_id"]), str(row["reporting_month"])) for row in all_rows]
    if len(keys) != len(set(keys)):
        raise RuntimeError("V3_DUPLICATE_PROJECT_MONTH_KEYS")
    _set_report_links(all_rows)
    write_csv(V3_DATA / "project_month.csv", all_rows, fields)

    old_report = {row["reporting_month"]: row for row in read_csv(V2_DATA / "report_month.csv")}
    coverage: dict[str, str] = {}
    report_rows = []
    admission_by_month = {row["month"]: row for row in admission}
    for month in months("2018-01", "2026-06"):
        if month in admission_by_month:
            status = admission_by_month[month]["source_status"]
            coverage_class = "PROJECT_LEVEL" if status == "ADMIT_COST_TARGET" else "QUARANTINED"
        elif month in old_report:
            coverage_class = old_report[month]["coverage_class"]
            status = "FROZEN_V2_" + coverage_class
        else:
            coverage_class, status = "MISSING_SOURCE", "MISSING_SOURCE"
        coverage[month] = coverage_class
        count = sum(str(row["reporting_month"]) == month for row in all_rows)
        report_rows.append({"reporting_month": month, "coverage_class": coverage_class, "project_rows": count,
                            "source_status": status, "temporal_use": "ELIGIBLE_WHERE_CONTIGUOUS" if coverage_class == "PROJECT_LEVEL" else "CENSOR_CROSSING_HORIZONS"})
    write_csv(V3_DATA / "report_month.csv", report_rows)

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in all_rows:
        grouped[str(row["canonical_project_id"])].append(row)
    masters = []
    for pid, observations in sorted(grouped.items()):
        observations.sort(key=lambda row: str(row["reporting_month"])); latest = observations[-1]
        masters.append({"canonical_project_id": pid, "project_code": latest.get("project_code_raw", ""),
                        "project_name": latest.get("project_name_raw", ""), "first_observed_month": observations[0]["reporting_month"],
                        "last_observed_month": latest["reporting_month"], "observed_months": len(observations), "identity_status": "RESOLVED_EXACT"})
    write_csv(V3_DATA / "project_master.csv", masters)

    v2_source = read_csv(V2_DATA / "source_ledger.csv")
    source_rows = [{"source_id": f"SRC-{row['month']}", "reporting_month": row["month"],
                    "source_path": _portable(row["month"]), "sha256": row["sha256"], "page_count": row["page_count"],
                    "schema_family": row["schema_family"], "schema_layout": row["schema_layout"],
                    "project_rows": row["accepted_rows"], "source_status": row["source_status"],
                    "provenance_status": row["provenance_status"], "reason": row["reason"]} for row in admission]
    for row in v2_source:
        source_rows.append({"source_id": row.get("source_id", ""), "reporting_month": row["reporting_month"],
                            "source_path": row.get("source_path", ""), "sha256": row.get("sha256", ""),
                            "page_count": row.get("page_count", ""), "schema_family": row.get("schema_family", "UNKNOWN"),
                            "schema_layout": "PREEXISTING_V2", "project_rows": row.get("project_rows", ""),
                            "accepted_rows": row.get("project_rows", ""),
                            "source_status": "FROZEN_V2_" + row.get("v2_use", row.get("project_level_status", "UNKNOWN")),
                            "provenance_status": row.get("provenance_status", "V2_MANIFEST_VERIFIED"),
                            "reason": row.get("reason", "")})
    write_csv(V3_DATA / "source_ledger.csv", sorted(source_rows, key=lambda row: row["reporting_month"]))

    schema_rows, availability = [], []
    for month in months("2018-01", "2026-06"):
        sample = next((row for row in all_rows if row["reporting_month"] == month), None)
        schema_rows.append({"reporting_month": month, "schema_family": sample.get("schema_family", "UNKNOWN") if sample else "UNAVAILABLE",
                            "schema_layout": sample.get("schema_layout", "PREEXISTING_V2") if sample else "UNAVAILABLE",
                            "classification_basis": "observed table structure and field evidence; not year",
                            "project_code": "AVAILABLE" if sample else "UNKNOWN", "cost_unit": "INR_CRORE" if sample else "UNKNOWN"})
        for field in ("project_code_raw", "original_cost_raw", "revised_cost_raw", "anticipated_cost_raw", "cumulative_expenditure_raw", "physical_progress_raw"):
            state = "UNKNOWN" if not sample else ("AVAILABLE" if any(str(row.get(field, "")).strip() for row in all_rows if row["reporting_month"] == month) else "UNREPORTED_OR_STRUCTURAL")
            availability.append({"reporting_month": month, "field": field, "availability_state": state,
                                 "schema_family": sample.get("schema_family", "") if sample else ""})
    write_csv(V3_DATA / "schema_ledger.csv", schema_rows)
    write_csv(V3_DATA / "field_availability.csv", availability)
    write_csv(OUT / "schema_summary.csv", schema_rows)

    identity = []
    for left, right in zip(months("2018-01", "2026-06"), months("2018-01", "2026-06")[1:]):
        a = {row["canonical_project_id"] for row in all_rows if row["reporting_month"] == left}
        b = {row["canonical_project_id"] for row in all_rows if row["reporting_month"] == right}
        identity.append({"from_month": left, "to_month": right, "from_projects": len(a), "to_projects": len(b),
                         "exact_overlap": len(a & b), "new_appearances": len(b - a), "disappearances": len(a - b),
                         "boundary_status": "CONTIGUOUS_PROJECT_LEVEL" if coverage[left] == coverage[right] == "PROJECT_LEVEL" else "BLOCKED_BY_SOURCE_COVERAGE"})
    write_csv(V3_DATA / "identity_continuity.csv", identity)
    write_csv(OUT / "identity_continuity.csv", identity)

    fingerprint = dataset_fingerprint(all_rows)
    metadata = {"version": "cost-prediction-v3-history.1", "status": "MACHINE_PROVISIONAL_RESEARCH",
                "calendar_months": len(months("2018-01", "2026-06")), "row_count": len(all_rows),
                "project_count": len(grouped), "project_level_months": sum(value == "PROJECT_LEVEL" for value in coverage.values()),
                "quarantined_months": [key for key, value in coverage.items() if value == "QUARANTINED"],
                "missing_months": [key for key, value in coverage.items() if value == "MISSING_SOURCE"],
                "dataset_fingerprint": fingerprint, "v2_source_unchanged": True, "raw_sources_read_only": True,
                "july_2026_included": False, "target_validation_status": "MACHINE_PROVISIONAL",
                "research_mode": "PROTOTYPE_RESEARCH_OVERRIDE"}
    V3_DATA.mkdir(parents=True, exist_ok=True)
    (V3_DATA / "dataset_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (V3_DATA / "README.md").write_text(
        "# Cost Prediction V3 historical research dataset\n\nGenerated from admitted immutable Flash Reports. "
        "It is machine-provisional research data, not a production model-release artifact.\n", encoding="utf-8")
    (OUT / "source_audit_status.json").write_text(json.dumps({"metadata": metadata, "admission_counts": Counter(row["source_status"] for row in admission)}, indent=2), encoding="utf-8")
    print(json.dumps({"metadata": metadata, "admission_counts": Counter(row["source_status"] for row in admission)}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=os.environ.get("PRAHARI_RAW_ROOT"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.raw_root is None:
        parser.error("--raw-root or PRAHARI_RAW_ROOT is required")
    build(args.raw_root.resolve(), args.workers)
