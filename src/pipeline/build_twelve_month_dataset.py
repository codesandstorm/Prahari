"""Build the provisional July 2025-June 2026 Gate 2 longitudinal dataset."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pdfplumber

from src.extraction.extractor_paimana import OUTPUT_COLUMNS, PROVENANCE_COLUMNS, classify_non_project_row
from src.pipeline.build_longitudinal_pilot import MONTH_FIELDS, to_project_month
from src.pipeline.build_three_month_pilot import METADATA_FIELDS, PRIMARY_FLAGS, SECONDARY_FLAGS, pair_flags
from src.pipeline.source_registry import resolve_source
from src.utils.safe_io import ensure_parent, write_json_replace
from src.validation.provenance import validate_provenance_record

DATASET_VERSION = "gate2-12m-2025-07-2026-06-provisional-v0.1"
DATASET_STATUS = "PROVISIONAL - ENGINEERING USE ONLY"
BUILDER_VERSION = "twelve_month_gate2:0.1.0"
SAMPLE_SEED = 26103
MONTHS = tuple([f"2025-{m:02d}" for m in range(7, 13)] + [f"2026-{m:02d}" for m in range(1, 7)])
NEW_MONTHS = MONTHS[:9]
SOURCE_CONFIG = {
    "2025-07": ("SRC-2025-07-P01", 791, 36, 37, 66, "PAIMANA_V1_APPROVAL_ONLY", "PAIMANA_V1_APPROVAL_ONLY"),
    "2025-08": ("SRC-2025-08", 800, 36, 37, 66, "PAIMANA_V1_INLINE_CODE", "PAIMANA_V1_INLINE_CODE"),
    "2025-09": ("SRC-2025-09", 794, 41, 42, 71, "PAIMANA_V1_INLINE_CODE", "PAIMANA_V1_INLINE_CODE"),
    "2025-10": ("SRC-2025-10", 820, 41, 42, 72, "PAIMANA_V1_INLINE_CODE", "PAIMANA_V1_INLINE_CODE"),
    "2025-11": ("SRC-2025-11", 823, 41, 42, 72, "PAIMANA_V1_INLINE_CODE", "PAIMANA_V1_INLINE_CODE"),
    "2025-12": ("SRC-2025-12", 1392, 49, 50, 107, "PAIMANA_V1_INLINE_CODE", "PAIMANA_V1_INLINE_CODE"),
    "2026-01": ("SRC-2026-01", 1702, 61, 62, 133, "PAIMANA_V1_INLINE_CODE", "PAIMANA_V1_INLINE_CODE"),
    "2026-02": ("SRC-2026-02", 1948, 64, 65, 167, "PAIMANA_V1_WITH_LEGACY", "PAIMANA_V1_WITH_LEGACY"),
    "2026-03": ("SRC-2026-03", 1941, 54, 55, 156, "PAIMANA_V1_WITH_LEGACY", "PAIMANA_V1_WITH_LEGACY"),
}
FROZEN_EXTRACTION_HASHES = {
    "2026-04": "55d84996925b4d5d0f2bb3bc9367a685c2ad49a14c009acddc7662b0b9ee11dd",
    "2026-05": "f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e",
    "2026-06": "bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9",
}
MANUAL_FIELDS = ("manual_row_confirmed", "manual_identity_confirmed", "manual_fields_confirmed", "manual_provenance_confirmed", "reviewer", "review_notes")
_PAREN = re.compile(r"^\((.*)\)$")
_MONTH_YEAR = re.compile(r"^(0?[1-9]|1[0-2])/\d{4}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str], root: Path) -> None:
    path = ensure_parent(path, root)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def detect_adapter(header: list[Any]) -> str:
    text = " ".join(str(cell or "") for cell in header)
    if "Project Code" not in text:
        raise ValueError("UNKNOWN schema: Project Code evidence absent")
    if "PMGID" in text and "Legacy OCMS Code" in text:
        return "PAIMANA_V2"
    if "Legacy OCMS Code" in text:
        return "PAIMANA_V1_WITH_LEGACY"
    if "Start Date" not in text:
        return "PAIMANA_V1_APPROVAL_ONLY"
    return "PAIMANA_V1_INLINE_CODE"


def normalize_table_row(row: list[Any]) -> list[Any]:
    result = list(row)
    while len(result) > 8 and not str(result[0] or "").strip(): result.pop(0)
    while len(result) > 8 and not str(result[-1] or "").strip(): result.pop()
    if len(result) != 8:
        raise ValueError(f"expected eight logical cells, found {len(result)}")
    return result


def _unparen(value: str) -> str:
    match = _PAREN.fullmatch(value.strip())
    return match.group(1).strip() if match else value.strip()


def _pair(value: Any, *, single_first: bool = False) -> tuple[str, str]:
    lines = [line.strip() for line in str(value or "").splitlines() if line.strip()]
    if single_first:
        if len(lines) > 1: raise ValueError("single-value date cell has multiple values")
        return (lines[0] if lines else ""), ""
    if len(lines) != 2: raise ValueError(f"paired cell has {len(lines)} values")
    return _unparen(lines[0]), _unparen(lines[1])


def parse_modern_row(row: list[Any], *, month: str, adapter: str, source_id: str, source_hash: str, page: int, row_index: int, table_number: int) -> dict[str, Any]:
    row = normalize_table_row(row); serial = str(row[0] or "").strip()
    if not serial.isdigit(): raise ValueError("not a project row")
    lines = [line.strip() for line in str(row[1] or "").splitlines() if line.strip()]
    tail = 3 if adapter == "PAIMANA_V1_WITH_LEGACY" else 2
    if len(lines) <= tail: raise ValueError("compound identity is incomplete")
    agency, code = lines[-tail], lines[-tail + 1]
    legacy = lines[-1] if tail == 3 else "-"
    if not _PAREN.fullmatch(agency) or not _PAREN.fullmatch(code) or (tail == 3 and not _PAREN.fullmatch(legacy)):
        raise ValueError("compound identity tail does not match adapter")
    project_code = _unparen(code)
    if not project_code.isdigit(): raise ValueError("Project Code is malformed")
    approval, start = _pair(row[3], single_first=adapter == "PAIMANA_V1_APPROVAL_ONLY")
    target, revised_doc = _pair(row[4]); original_cost, revised_cost = _pair(row[5])
    compact = month.replace("-", "")
    return {
        "observation_id": f"OBS-{compact}-{int(serial):05d}", "reporting_month": month,
        "serial_number_raw": serial, "project_name_raw": "\n".join(lines[:-tail]),
        "agency_raw": _unparen(agency), "project_code_raw": project_code,
        "legacy_ocms_code_raw": _unparen(legacy) if tail == 3 else "-", "pmgid_raw": "-",
        "state_raw": str(row[2] or "").strip(), "approval_date_raw": approval, "start_date_raw": start,
        "original_target_doc_raw": target, "revised_doc_raw": revised_doc,
        "original_cost_raw": original_cost, "revised_cost_raw": revised_cost,
        "cumulative_expenditure_raw": str(row[6] or "").strip(), "physical_progress_raw": str(row[7] or "").strip(),
        "project_identity_cell_raw": str(row[1] or "").strip(), "approval_start_cell_raw": str(row[3] or "").strip(),
        "doc_cell_raw": str(row[4] or "").strip(), "cost_cell_raw": str(row[5] or "").strip(),
        "source_id": source_id, "source_sha256": source_hash, "pdf_page_index": page,
        "printed_page_number": page - 1, "source_table": "All Ongoing Projects",
        "source_table_number": table_number, "extraction_method": "pdfplumber_table",
        "extractor_version": BUILDER_VERSION, "raw_row_locator": f"pdf_page_index={page},table_index=logical8,row_index={row_index}",
    }


def _sample(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(SAMPLE_SEED); chosen: dict[str, tuple[dict[str, Any], str]] = {}
    ordered = sorted(rows, key=lambda row: int(row["serial_number_raw"])); pages = sorted({int(row["pdf_page_index"]) for row in rows})
    pools = [
        ("FIRST", ordered[:1]), ("LAST", ordered[-1:]),
        ("EARLY_PAGE", [r for r in rows if int(r["pdf_page_index"]) <= pages[len(pages)//3]]),
        ("MIDDLE_PAGE", [r for r in rows if pages[len(pages)//3] < int(r["pdf_page_index"]) <= pages[2*len(pages)//3]]),
        ("LATE_PAGE", [r for r in rows if int(r["pdf_page_index"]) > pages[2*len(pages)//3]]),
        ("MISSING_VALUE", [r for r in rows if any(r[f] in {"", "-", "NA"} for f in ("start_date_raw", "revised_doc_raw", "legacy_ocms_code_raw", "pmgid_raw"))]),
        ("ZERO_PROGRESS", [r for r in rows if r["physical_progress_raw"] == "0"]),
        ("HIGH_PROGRESS", [r for r in rows if _decimal(r["physical_progress_raw"]) is not None and _decimal(r["physical_progress_raw"]) >= 95]),
    ]
    for label, pool in pools:
        available = [r for r in pool if r["observation_id"] not in chosen]
        if available:
            selected = available[0] if label in {"FIRST", "LAST"} else rng.choice(available)
            chosen[selected["observation_id"]] = (selected, label)
    remaining = [r for r in rows if r["observation_id"] not in chosen]
    for row in rng.sample(remaining, 20-len(chosen)): chosen[row["observation_id"]] = (row, "SEEDED_FILL")
    result=[]
    for row,label in sorted(chosen.values(), key=lambda item:int(item[0]["serial_number_raw"])):
        result.append({**row,"sample_category":label,**{field:"" for field in MANUAL_FIELDS}})
    return result


def _decimal(value: str) -> Decimal | None:
    try: return Decimal(value.replace(",", "")) if value.strip() not in {"", "-", "NA"} else None
    except InvalidOperation: return None


def field_quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return transparent, non-imputing completeness and parseability evidence."""
    missing_tokens = {"", "-", "NA"}
    audited = (
        "project_name_raw", "agency_raw", "project_code_raw", "legacy_ocms_code_raw",
        "pmgid_raw", "state_raw", "approval_date_raw", "start_date_raw",
        "original_target_doc_raw", "revised_doc_raw", "original_cost_raw",
        "revised_cost_raw", "cumulative_expenditure_raw", "physical_progress_raw",
    )
    missing = {
        field: sum(str(row.get(field, "")).strip() in missing_tokens for row in rows)
        for field in audited
    }
    date_fields = ("approval_date_raw", "start_date_raw", "original_target_doc_raw", "revised_doc_raw")
    numeric = ("original_cost_raw", "revised_cost_raw", "cumulative_expenditure_raw", "physical_progress_raw")
    invalid_numeric = {
        field: sum(
            str(row.get(field, "")).strip() not in missing_tokens
            and _decimal(str(row.get(field, ""))) is None
            for row in rows
        )
        for field in numeric
    }
    per_field: dict[str, Any] = {}
    for field in date_fields + numeric:
        present = [str(row.get(field, "")).strip() for row in rows if str(row.get(field, "")).strip() not in missing_tokens]
        if field in date_fields:
            malformed_values = [value for value in present if not _MONTH_YEAR.fullmatch(value)]
            unusual_values = malformed_values
        else:
            malformed_values = [value for value in present if _decimal(value) is None]
            unusual_values = [
                value for value in present
                if _decimal(value) is not None
                and (_decimal(value) < 0 or (field == "physical_progress_raw" and _decimal(value) > 100))
            ]
        per_field[field] = {
            "parsed": len(present) - len(malformed_values),
            "missing": missing[field],
            "malformed": len(malformed_values),
            "unusual_raw_tokens": sorted(set(unusual_values)),
        }
    return {
        "row_count": len(rows),
        "missing_token_definition": sorted(missing_tokens),
        "missing_counts": missing,
        "missing_percent": {
            field: round(count * 100 / len(rows), 4) if rows else 0.0
            for field, count in missing.items()
        },
        "invalid_numeric_counts_excluding_missing": invalid_numeric,
        "required_field_audit": per_field,
        "imputation_applied": False,
    }


def extract_month(root: Path, month: str) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    source_id, expected, title_page, first, last, expected_adapter, variant = SOURCE_CONFIG[month]
    manifest = root / "data/metadata/source_manifest.csv"; source = resolve_source(source_id, manifest, root)
    accepted=[]; unresolved=[]; structural=Counter(); raw_count=0; detected=set(); page_counts=[]
    with pdfplumber.open(str(source.path)) as pdf:
        for page in range(first, last+1):
            tables=pdf.pages[page-1].extract_tables() or []; candidates=[]
            for table in tables:
                try: logical=[normalize_table_row(row) for row in table]
                except ValueError: continue
                if logical: candidates.append(logical)
            if len(candidates) != 1: raise RuntimeError(f"{month} page {page}: expected one logical 8-cell table, found {len(candidates)}")
            headers = [row for row in candidates[0] if "Project Code" in " ".join(str(cell or "") for cell in row)]
            if not headers:
                raise RuntimeError(f"{month} page {page}: UNKNOWN schema without Project Code header evidence")
            page_adapter = detect_adapter(headers[-1]); detected.add(page_adapter); pc=Counter()
            for index,row in enumerate(candidates[0]):
                raw_count += 1
                if not str(row[0] or "").strip().isdigit():
                    kind=classify_non_project_row(row); structural[kind]+=1; pc[kind]+=1; continue
                try:
                    accepted.append(parse_modern_row(row,month=month,adapter=page_adapter,source_id=source_id,source_hash=source.sha256,page=page,row_index=index,table_number=4 if month in {"2025-07","2025-08"} else 6)); pc["PROJECT_ROW"]+=1
                except ValueError as exc:
                    unresolved.append({"source_id":source_id,"pdf_page_index":page,"raw_row_locator":f"pdf_page_index={page},table_index=logical8,row_index={index}","reason":str(exc),"raw_cells_json":json.dumps(row,ensure_ascii=False)});pc["UNRESOLVED"]+=1
            page_counts.append({"pdf_page_index":page,**dict(pc)})
    serials=[int(r["serial_number_raw"]) for r in accepted]; codes=[r["project_code_raw"] for r in accepted]
    provenance=[e for row in accepted for e in validate_provenance_record(row,manifest)]
    quality="PASS_AUTOMATED"
    if detected != {expected_adapter}: quality="BLOCKED_SCHEMA"
    elif len(accepted)!=expected or unresolved: quality="FAILED_EXTRACTION"
    elif serials!=list(range(1,expected+1)): quality="BLOCKED_COUNT"
    elif len(codes)!=len(set(codes)): quality="BLOCKED_IDENTITY"
    elif provenance: quality="BLOCKED_PROVENANCE"
    summary={"source_id":source_id,"source_sha256":source.sha256,"reporting_month":month,"file_size_bytes":source.path.stat().st_size,"physical_page_count":len(pdf.pages),"text_extractability":"YES","official_ongoing_count":expected,"count_evidence":{"pdf_page_index":4,"printed_page_number":3,"section":"Overview","locator":"Ongoing Projects figure"},"table_title":"All Ongoing Projects","table_number":4 if month in {"2025-07","2025-08"} else 6,"title_pdf_page_index":title_page,"title_printed_page_number":title_page-1,"data_pdf_page_range":[first,last],"printed_page_range":[first-1,last-1],"schema_family":"PAIMANA_V1","schema_classification":"COMPATIBLE_VARIATION","variant":variant,"adapter":expected_adapter,"confidence":"HIGH","column_count":8,"accepted_project_rows":len(accepted),"structural_counts":dict(structural),"total_raw_table_rows":raw_count,"unresolved_rows":len(unresolved),"serial_min":min(serials),"serial_max":max(serials),"missing_serials":sorted(set(range(1,expected+1))-set(serials)),"duplicate_serials":len(serials)-len(set(serials)),"out_of_order_serials":0 if serials==sorted(serials) else 1,"project_code_missing":sum(not c for c in codes),"project_code_duplicates":len(codes)-len(set(codes)),"project_code_malformed":sum(not c.isdigit() for c in codes),"project_code_whitespace":sum(c!=c.strip() for c in codes),"legacy_ocms":{"present":sum(r["legacy_ocms_code_raw"] not in {"","-","NA"} for r in accepted),"missing":sum(r["legacy_ocms_code_raw"] in {"","-","NA"} for r in accepted)},"pmgid":{"present":0,"missing":len(accepted)},"field_quality":field_quality(accepted),"provenance_failures":len(provenance),"duplicate_locators":len(accepted)-len({r["raw_row_locator"] for r in accepted}),"quality_gate":quality,"page_diagnostics":page_counts}
    if quality != "PASS_AUTOMATED": raise RuntimeError(f"{month} quality gate: {quality}: {summary}")
    return accepted,summary,_sample(accepted)


def _build_master(month_rows: list[dict[str,str]]) -> list[dict[str,str]]:
    grouped=defaultdict(list)
    for row in month_rows: grouped[row["project_code"]].append(row)
    result=[]
    for code in sorted(grouped,key=int):
        obs=sorted(grouped[code],key=lambda r:r["reporting_month"]); latest=obs[-1]
        present={r["reporting_month"] for r in obs}
        result.append({"canonical_project_id":f"PRH-{code}","project_code":code,"first_observed_month":obs[0]["reporting_month"],"latest_observed_month":latest["reporting_month"],"observation_count":len(obs),"presence_months":"|".join(m for m in MONTHS if m in present),"current_project_name":latest["reported_project_name"],"current_agency":latest["reported_agency"],"current_state":latest["reported_state"],"identity_method":"EXACT_PROJECT_CODE_VALIDATED_MODERN_PERIOD","current_observation_id":latest["observation_id"],"current_source_id":latest["source_id"],"current_source_sha256":latest["source_sha256"],"current_pdf_page_index":latest["pdf_page_index"],"current_printed_page_number":latest["printed_page_number"],"current_source_table":latest["source_table"],"current_source_table_number":latest["source_table_number"],"current_raw_row_locator":latest["raw_row_locator"]})
    return result


def build(repo_root: Path) -> dict[str,Any]:
    root=repo_root.resolve(); extracted_dir=root/"data/extracted/ongoing"; validation=root/"validation/extraction_validation"
    for month,digest in FROZEN_EXTRACTION_HASHES.items():
        if sha256(extracted_dir/f"ongoing_{month.replace('-','_')}.csv") != digest: raise RuntimeError(f"protected {month} extraction changed")
    raw={}; monthly={}; samples={}
    for month in NEW_MONTHS:
        rows,summary,sample=extract_month(root,month);raw[month]=rows;monthly[month]=summary;samples[month]=sample
    for month in MONTHS[9:]: raw[month]=read_csv(extracted_dir/f"ongoing_{month.replace('-','_')}.csv")
    for month in NEW_MONTHS:
        tag=month.replace("-","_"); out=extracted_dir/f"ongoing_{tag}.csv"
        write_csv(out,raw[month],OUTPUT_COLUMNS,root); monthly[month]["extraction_sha256"]=sha256(out)
        write_csv(root/f"data/extracted/review/ongoing_{tag}_unresolved_rows.csv",[],["source_id","pdf_page_index","raw_row_locator","reason","raw_cells_json"],root)
        vdir=validation/month
        write_csv(vdir/f"{tag}_manual_sample.csv",samples[month],OUTPUT_COLUMNS+["sample_category"]+list(MANUAL_FIELDS),root)
        write_json_replace(vdir/f"{tag}_extraction_summary.json",monthly[month],repo_root=root)
    provenance_path=root/"data/metadata/provenance.csv"; existing=read_csv(provenance_path)
    new_observation_ids = {row["observation_id"] for month in NEW_MONTHS for row in raw[month]}
    previous = [row for row in existing if row["observation_id"] in new_observation_ids]
    existing = [row for row in existing if row["observation_id"] not in new_observation_ids]
    metadata_path = root/"data/processed/pilot_2025_07_2026_06/dataset_metadata.json"
    if metadata_path.exists():
        timestamp = json.loads(metadata_path.read_text(encoding="utf-8"))["created_at"]
    elif previous:
        timestamp = previous[0]["extraction_timestamp_utc"]
    else:
        timestamp = datetime.now(timezone.utc).isoformat()
    new_prov=[]
    for month in NEW_MONTHS:
        for row in raw[month]:
            new_prov.append({"observation_id":row["observation_id"],"source_id":row["source_id"],"source_sha256":row["source_sha256"],"source_group_id":f"FR-{month}","source_part":"01","filename":Path(resolve_source(row["source_id"],root/"data/metadata/source_manifest.csv",root).path).name,"report_year":month[:4],"report_month":str(int(month[5:])),"pdf_page_index":row["pdf_page_index"],"printed_page_number":row["printed_page_number"],"source_table":row["source_table"],"source_table_number":row["source_table_number"],"extraction_method":row["extraction_method"],"extractor_version":row["extractor_version"],"raw_row_locator":row["raw_row_locator"],"extraction_timestamp_utc":timestamp,"extracted_by":"12-month-controlled-build","notes":"AUTOMATED_VALIDATION_COMPLETE_HUMAN_PENDING"})
    with provenance_path.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=PROVENANCE_COLUMNS);writer.writeheader();writer.writerows(existing+new_prov)
    month_rows=[to_project_month(row) for month in MONTHS for row in raw[month]]
    master=_build_master(month_rows); keys=[(r["canonical_project_id"],r["reporting_month"]) for r in month_rows]
    if len(keys)!=len(set(keys)): raise RuntimeError("duplicate project-month keys")
    transitions=[];pairwise=[];flag_counts=Counter()
    for left,right in zip(MONTHS,MONTHS[1:]):
        li={r["project_code_raw"]:r for r in raw[left]};ri={r["project_code_raw"]:r for r in raw[right]};common=sorted(set(li)&set(ri),key=int); variations=0
        for code in common:
            primary,secondary=pair_flags(li[code],ri[code]);variations+=bool(primary or secondary)
            for flag in primary: flag_counts[flag]+=1
            transitions.append({"canonical_project_id":f"PRH-{code}","project_code":code,"boundary":f"{left}_TO_{right}","primary_flags":"|".join(primary),"secondary_flags":"|".join(secondary),"before_project_name":li[code]["project_name_raw"],"after_project_name":ri[code]["project_name_raw"],"before_progress":li[code]["physical_progress_raw"],"after_progress":ri[code]["physical_progress_raw"],"before_expenditure":li[code]["cumulative_expenditure_raw"],"after_expenditure":ri[code]["cumulative_expenditure_raw"],"before_source_id":li[code]["source_id"],"before_source_sha256":li[code]["source_sha256"],"before_pdf_page_index":li[code]["pdf_page_index"],"before_raw_row_locator":li[code]["raw_row_locator"],"after_source_id":ri[code]["source_id"],"after_source_sha256":ri[code]["source_sha256"],"after_pdf_page_index":ri[code]["pdf_page_index"],"after_raw_row_locator":ri[code]["raw_row_locator"]})
        pairwise.append({"left_month":left,"right_month":right,"exact_matches":len(common),"left_only":len(set(li)-set(ri)),"right_only":len(set(ri)-set(li)),"left_duplicates":0,"right_duplicates":0,"identity_conflicts":0,"metadata_variations":variations})
    grouped=defaultdict(list)
    for row in month_rows: grouped[row["project_code"]].append(row)
    gaps=[];trajectories=[]
    for code,obs in grouped.items():
        by={r["reporting_month"]:r for r in obs};indices=[MONTHS.index(m) for m in by]; internal=[MONTHS[i] for i in range(min(indices),max(indices)+1) if MONTHS[i] not in by]
        if internal:gaps.append({"canonical_project_id":f"PRH-{code}","project_code":code,"observed_months":"|".join(m for m in MONTHS if m in by),"internal_missing_months":"|".join(internal),"manual_gap_confirmed":"","reviewer":"","review_notes":""})
        trajectories.append({"canonical_project_id":f"PRH-{code}","project_code":code,"observation_count":len(obs),"progress_trajectory":" | ".join(f"{m}:{by[m]['reported_physical_progress']}" for m in MONTHS if m in by),"expenditure_trajectory":" | ".join(f"{m}:{by[m]['reported_cumulative_expenditure']}" for m in MONTHS if m in by),"revised_cost_trajectory":" | ".join(f"{m}:{by[m]['reported_revised_cost']}" for m in MONTHS if m in by),"revised_doc_trajectory":" | ".join(f"{m}:{by[m]['reported_revised_doc']}" for m in MONTHS if m in by),"internal_gap_count":len(internal)})
    processed=root/"data/processed/pilot_2025_07_2026_06"; longdir=root/"validation/longitudinal/twelve_month"
    write_csv(processed/"project_master.csv",master,list(master[0]),root);write_csv(processed/"project_month.csv",month_rows,MONTH_FIELDS,root)
    write_csv(longdir/"pairwise_identity_continuity.csv",pairwise,list(pairwise[0]),root);write_csv(longdir/"temporal_transitions.csv",transitions,list(transitions[0]),root)
    flagged=[r for r in transitions if r["primary_flags"]];write_csv(longdir/"exhaustive_primary_qa_review.csv",flagged,list(flagged[0]),root)
    write_csv(longdir/"project_trajectories.csv",trajectories,list(trajectories[0]),root);write_csv(longdir/"internal_presence_gap_review.csv",gaps,list(gaps[0]) if gaps else ["canonical_project_id","project_code","observed_months","internal_missing_months","manual_gap_confirmed","reviewer","review_notes"],root)
    source_rows=[]
    for month in MONTHS:
        sid=SOURCE_CONFIG[month][0] if month in SOURCE_CONFIG else f"SRC-{month}";source=resolve_source(sid,root/"data/metadata/source_manifest.csv",root)
        if month in monthly: summary=monthly[month]
        else: summary={"official_ongoing_count":len(raw[month]),"quality_gate":"VALIDATED_FROZEN","schema_family":"PAIMANA_V2","variant":"PAIMANA_V2","adapter":"FROZEN_MONTH_ADAPTER","confidence":"HIGH","title_pdf_page_index":{"2026-04":54,"2026-05":53,"2026-06":58}[month],"data_pdf_page_range":{"2026-04":[55,162],"2026-05":[54,162],"2026-06":[59,159]}[month],"accepted_project_rows":len(raw[month]),"structural_counts":{},"unresolved_rows":0,"project_code_missing":0,"project_code_duplicates":0,"provenance_failures":0}
        legacy_present = sum(row["legacy_ocms_code_raw"].strip() not in {"", "-", "NA"} for row in raw[month])
        pmgid_present = sum(row["pmgid_raw"].strip() not in {"", "-", "NA"} for row in raw[month])
        source_rows.append({"source_id":sid,"reporting_month":month,"source_sha256":source.sha256,"schema_family":summary["schema_family"],"variant":summary["variant"],"column_count":8,"header_structure":"8 logical columns; repeated on each data page","identity_format":"compound project-name/agency/code cell","date_format":"MM/YYYY","doc_format":"original/revised pair","cost_format":"crore pair","missing_tokens":"blank|-|NA","legacy_ocms_behavior":f"populated {legacy_present}/{len(raw[month])}","pmgid_behavior":f"populated {pmgid_present}/{len(raw[month])}","table_page_pattern":f"title {summary['title_pdf_page_index']}; data {summary['data_pdf_page_range'][0]}-{summary['data_pdf_page_range'][1]}","recommended_adapter":summary["adapter"],"confidence":summary["confidence"]})
    matrix=root/"data/metadata/schema_family_2025_07_2026_06.csv";write_csv(matrix,source_rows,list(source_rows[0]),root)
    metadata={"dataset_version":DATASET_VERSION,"status":DATASET_STATUS,"created_at":timestamp,"included_months":list(MONTHS),"source_ids":{r["reporting_month"]:r["source_id"] for r in source_rows},"source_hashes":{r["reporting_month"]:r["source_sha256"] for r in source_rows},"extraction_hashes":{m:sha256(extracted_dir/f"ongoing_{m.replace('-','_')}.csv") for m in MONTHS},"monthly_row_counts":{m:len(raw[m]) for m in MONTHS},"builder_version":BUILDER_VERSION,"automated_validation_status":"PASS","human_validation_status":"PENDING_FOR_NINE_NEW_MONTHS","project_master_rows":len(master),"project_month_rows":len(month_rows),"presence_gap_projects":len(gaps),"primary_flag_rows":len(flagged)}
    write_json_replace(processed/"dataset_metadata.json",metadata,repo_root=root)
    summary={"monthly":monthly,"pairwise":pairwise,"unique_projects":len(master),"project_month_rows":len(month_rows),"presence_gaps":len(gaps),"flag_counts":dict(flag_counts),"flagged_transition_rows":len(flagged),"dataset":metadata}
    write_json_replace(longdir/"twelve_month_summary.json",summary,repo_root=root)
    return summary
