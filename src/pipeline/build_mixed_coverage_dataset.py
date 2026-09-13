"""Build the Gate 2 mixed-coverage July 2023--June 2026 dataset.

The calendar has 36 months, but only source-backed project rows are emitted.
Aggregate-only and missing months are represented only in ``report_month``.
No imputation, interpolation, fuzzy identity linkage, labels, or predictions occur.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import fitz
import pdfplumber

from src.extraction.extractor_paimana import OUTPUT_COLUMNS, PROVENANCE_COLUMNS, classify_non_project_row
from src.utils.safe_io import ensure_parent, write_json_replace

DATASET_VERSION = "gate2-36m-window-30-project-months-mixed-v0.1"
DATASET_STATUS = "PROVISIONAL - MIXED COVERAGE - HUMAN VALIDATION PENDING"
BUILDER_VERSION = "mixed_coverage_gate2:0.1.5"
SAMPLE_SEED = 26103
AGGREGATE_ONLY = {"2023-12", "2024-04", "2024-05", "2024-08", "2024-09"}
MISSING_SOURCE = {"2025-02"}
SOURCE_ID_OVERRIDES = {"2024-07": "SRC-2024-07-P02"}
FROZEN_MONTHS = tuple([f"2025-{m:02d}" for m in range(7, 13)] + [f"2026-{m:02d}" for m in range(1, 7)])
MONTHS = tuple(
    f"{year:04d}-{month:02d}"
    for year in range(2023, 2027)
    for month in range(1, 13)
    if (year, month) >= (2023, 7) and (year, month) <= (2026, 6)
)
PROJECT_MONTHS = tuple(m for m in MONTHS if m not in AGGREGATE_ONLY | MISSING_SOURCE)
NEW_PROJECT_MONTHS = tuple(m for m in PROJECT_MONTHS if m not in FROZEN_MONTHS)

EXTRA_COLUMNS = [
    "schema_family", "ministry_raw", "sector_raw", "anticipated_doc_raw",
    "anticipated_cost_raw", "milestones_raw", "project_status_raw",
    "project_code_schema_available", "legacy_ocms_code_schema_available",
    "pmgid_schema_available", "physical_progress_schema_available",
    "anticipated_doc_schema_available", "anticipated_cost_schema_available",
]
EXTRACTED_COLUMNS = OUTPUT_COLUMNS + EXTRA_COLUMNS
MISSING_TOKENS = {"", "-", "N.A.", "NA", "N/A", "NONE"}
MONTH_NAME = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str], root: Path) -> None:
    path = ensure_parent(path, root)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def source_path(root: Path, month: str) -> Path:
    year, number = month.split("-")
    return root / "data" / "raw" / year / f"FlashReport_{year}_{number}.pdf"


def source_id(month: str) -> str:
    return SOURCE_ID_OVERRIDES.get(month, f"SRC-{month}")


def update_manifest_and_provenance(root: Path, new_rows: list[dict[str, Any]], summaries: dict[str, dict[str, Any]]) -> None:
    manifest_path = root / "data/metadata/source_manifest.csv"
    manifest = read_csv(manifest_path); fields = list(manifest[0])
    existing_ids = {row["source_id"] for row in manifest}
    for month in NEW_PROJECT_MONTHS:
        sid = source_id(month)
        if sid in existing_ids: continue
        year, number = month.split("-"); path = source_path(root, month); summary = summaries[month]
        row = {field: "" for field in fields}
        row.update({"source_id": sid, "source_group_id": f"FR-{month}", "source_part": "01",
                    "completeness_status": "SINGLE_FILE", "filename": path.name,
                    "relative_path": path.relative_to(root).as_posix(), "report_year": year,
                    "report_month": str(int(number)), "report_date_stated": f"{MONTH_NAME[int(number)]} {year}",
                    "file_status": "CANONICAL", "detected_schema": summary["schema_family"],
                    "detector_confidence": summary["confidence"],
                    "detector_evidence_pages": f"{summary['first_page']}-{summary['last_page']}",
                    "detector_rule": "mixed_coverage_structural_table_evidence", "sha256": summary["source_sha256"],
                    "page_count": str(fitz.open(path).page_count), "file_size_bytes": str(path.stat().st_size),
                    "text_extractable": "YES", "ocr_required": "NO", "extraction_status": "PROVISIONAL_VALIDATED",
                    "notes": "Mixed-coverage Gate 2 source; official count and serial sequence reconciled."})
        manifest.append(row); existing_ids.add(sid)
    write_csv(manifest_path, manifest, fields, root)

    provenance_path = root / "data/metadata/provenance.csv"
    existing = read_csv(provenance_path)
    new_ids = {row["observation_id"] for row in new_rows}
    existing = [row for row in existing if row["observation_id"] not in new_ids]
    provenance = []
    for row in sorted(new_rows, key=lambda item: (item["reporting_month"], int(item["serial_number_raw"]))):
        year, number = row["reporting_month"].split("-")
        provenance.append({"observation_id": row["observation_id"], "source_id": row["source_id"],
                           "source_sha256": row["source_sha256"], "source_group_id": f"FR-{row['reporting_month']}",
                           "source_part": "01", "filename": source_path(root, row["reporting_month"]).name,
                           "report_year": year, "report_month": str(int(number)), "pdf_page_index": row["pdf_page_index"],
                           "printed_page_number": row["printed_page_number"], "source_table": row["source_table"],
                           "source_table_number": row["source_table_number"], "extraction_method": row["extraction_method"],
                           "extractor_version": row["extractor_version"], "raw_row_locator": row["raw_row_locator"],
                           "extraction_timestamp_utc": "2026-09-06T00:00:00+05:30", "extracted_by": "mixed-coverage-gate2-builder",
                           "notes": "project-level observation; no imputation"})
    write_csv(provenance_path, existing + provenance, PROVENANCE_COLUMNS, root)


def _text(page: Any) -> str:
    return " ".join((page.get_text() or "").split())


def _month_evidence(text: str, month: str) -> bool:
    year, number = month.split("-")
    name = MONTH_NAME[int(number)]
    # Older PDFs concatenate words (``forJanuary``) or split glyph runs
    # (``Aug ust``). Compare an alphanumeric-only evidence view; never infer
    # the month from the filename alone.
    compact = re.sub(r"[^a-z0-9]", "", text.lower())
    tokens = {f"{name.lower()}{year}"}
    # September 2024's two-column text layer interleaves the ``t`` with the
    # adjacent column, yielding the directly observed token ``Sep ember2024``.
    if name == "September": tokens.add(f"sepember{year}")
    return any(token in compact for token in tokens)


def inspect_source(path: Path, month: str) -> dict[str, Any]:
    if not path.exists():
        return {"source_present": False, "sha256": "", "file_size_bytes": "", "page_count": "",
                "text_extractability": "NO", "month_evidence": False, "pdf_readable": False}
    raw_prefix = path.read_bytes()[:5]
    record: dict[str, Any] = {
        "source_present": True, "sha256": sha256(path), "file_size_bytes": path.stat().st_size,
        "pdf_readable": False, "month_evidence": False,
    }
    if raw_prefix != b"%PDF-":
        record.update(page_count="", text_extractability="NO", error="invalid_pdf_magic")
        return record
    try:
        document = fitz.open(path)
        record["page_count"] = document.page_count
        samples = [_text(document[i]) for i in range(min(8, document.page_count))]
        lengths = [len(value) for value in samples]
        nonempty = sum(length > 20 for length in lengths)
        record["text_extractability"] = "YES" if nonempty == len(lengths) else ("PARTIAL" if nonempty else "NO")
        opening = " ".join(_text(document[i]) for i in range(min(8, document.page_count)))
        record["month_evidence"] = _month_evidence(opening, month)
        record["pdf_readable"] = True
        document.close()
    except Exception as exc:  # source defect is retained as evidence
        record.update(page_count="", text_extractability="NO", error=f"{type(exc).__name__}: {exc}")
    return record


def build_coverage(root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    inspections = {month: inspect_source(source_path(root, month), month) for month in MONTHS}
    hashes: dict[str, list[str]] = defaultdict(list)
    for month, evidence in inspections.items():
        if evidence.get("sha256"):
            hashes[evidence["sha256"]].append(month)
    july = root / "data/raw/2026/FlashReport_2026_07.pdf"
    july_hash = sha256(july) if july.exists() else ""
    rows = []
    for month in MONTHS:
        evidence = inspections[month]
        if month in MISSING_SOURCE:
            coverage, table, aggregate, usable, reason = "MISSING_SOURCE", False, False, False, "public source unavailable"
        elif month in AGGREGATE_ONLY:
            coverage, table, aggregate, usable, reason = "AGGREGATE_ONLY", False, True, False, "valid monthly report lacks complete project-level table"
        else:
            coverage, table, aggregate, usable, reason = "PROJECT_LEVEL", True, True, True, "complete ongoing-project inventory candidate"
        duplicate = len(hashes.get(evidence.get("sha256", ""), [])) > 1 if evidence.get("sha256") else False
        quality = "PASS" if evidence.get("pdf_readable") and evidence.get("month_evidence") and not duplicate else "SOURCE_REVIEW_REQUIRED"
        if coverage == "MISSING_SOURCE": quality = "EXPECTED_MISSING"
        rows.append({
            "reporting_month": month, "source_id": source_id(month), "source_present": str(bool(evidence["source_present"])).upper(),
            "source_path": source_path(root, month).relative_to(root).as_posix() if evidence["source_present"] else "",
            "sha256": evidence.get("sha256", ""), "file_size_bytes": evidence.get("file_size_bytes", ""),
            "page_count": evidence.get("page_count", ""), "text_extractability": evidence.get("text_extractability", "NO"),
            "coverage_class": coverage, "project_table_present": str(table).upper(),
            "aggregate_summary_present": str(aggregate).upper(), "project_level_usable": str(usable).upper(),
            "month_evidence": str(bool(evidence.get("month_evidence"))).upper(),
            "duplicate_within_window": str(duplicate).upper(), "reason": reason, "quality_status": quality,
        })
    if july_hash and july_hash == inspections["2026-06"].get("sha256"):
        inspections["excluded_2026-07"] = {"sha256": july_hash, "duplicate_of": "2026-06", "status": "EXCLUDED_DUPLICATE"}
    return rows, inspections


def _runs(values: list[int]) -> list[list[int]]:
    result: list[list[int]] = []
    for value in values:
        if not result or value != result[-1][-1] + 1: result.append([value])
        else: result[-1].append(value)
    return result


def discover_table(path: Path) -> dict[str, Any]:
    document = fitz.open(path)
    pages = [_text(page) for page in document]
    ocms_starts = [i + 1 for i, text in enumerate(pages) if re.search(r"(?i)detail of ongoing projects costing", text)]
    if ocms_starts:
        # The complete OCMS project table repeats its title on every physical
        # page.  Using that evidenced contiguous run is safer than scanning to a
        # later annexure heading: some historical editions omit the old stop
        # phrase and would otherwise absorb hundreds of unrelated annexure pages.
        # A few editions insert a one-page continuation sheet without repeating
        # the title.  Join title runs across only a single missing page.
        ocms_runs: list[list[int]] = []
        for value in ocms_starts:
            if not ocms_runs or value > ocms_runs[-1][-1] + 2:
                ocms_runs.append([value])
            else:
                ocms_runs[-1].append(value)
        run = max(ocms_runs, key=len)
        first, last = run[0], run[-1]
        if len(run) < 5:
            stops = [
                i + 1 for i, text in enumerate(pages[first:], start=first)
                if "Project Status with respect to Original Schedule" in text
                or text.strip().upper().startswith("ANNEXURE")
                or text.startswith("List of Projects in which Expenditure is More than Approved Cost")
            ]
            last = (stops[0] - 1) if stops else document.page_count
        opening = " ".join(pages[:8])
        official = re.search(r"(?i)status of the\s*([\d,]+)\s*(?:Central Sector Infrastructure )?Projects", opening)
        document.close()
        return {"schema_family": "OCMS", "schema_classification": "NEW_COMPATIBLE_SCHEMA", "first_page": first,
                "last_page": last, "table_number": "DETAIL", "table_title": "Detail of ongoing Projects Costing Rs 150 Crore and above",
                "identity_fields": "Legacy OCMS embedded project code", "confidence": "HIGH",
                "official_project_count": int(official.group(1).replace(",", "")) if official else None}
    candidates = []
    for i, text in enumerate(pages, start=1):
        low = text.lower()
        if "ongoing projects as of" in low:
            candidates.append(i)
    runs = _runs(candidates)
    if not runs:
        document.close()
        raise RuntimeError(f"UNKNOWN schema: no evidenced project-level table in {path.name}")
    run = max(runs, key=len)
    nearby = " ".join(pages[max(0, run[0] - 3):min(document.page_count, run[0] + 1)])
    header = pages[run[0] - 1].lower()
    if not all(marker in header for marker in ("project name", "date of approval", "progress (%)", "project code")):
        document.close()
        raise RuntimeError(f"UNKNOWN schema: national table header incomplete in {path.name}")
    number = (re.findall(r"(?i)Table\s*:-?\s*(\d+).*?Ongoing Projects", nearby) or ["UNKNOWN"])[-1]
    totals = []
    for text in pages[:12]:
        totals.extend(int(value.replace(",", "")) for value in re.findall(r"(?i)\bTotal\s+([\d,]{3,})\b", text))
    official = totals[0] if totals else None
    document.close()
    return {"schema_family": "PAIMANA_V1", "schema_classification": "COMPATIBLE_VARIATION",
            "first_page": run[0], "last_page": run[-1], "table_number": number,
            "table_title": "Project List: Ongoing Projects", "identity_fields": "Project Code", "confidence": "HIGH",
            "official_project_count": official}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _wrapped(value: str, opening: str, closing: str) -> str:
    match = re.search(re.escape(opening) + r"\s*([^" + re.escape(closing) + r"]+)\s*" + re.escape(closing), value)
    return _clean(match.group(1)) if match else ""


def _triplet(value: Any, anticipated_brace: bool) -> tuple[str, str, str]:
    raw = _clean(value); anticipated = _wrapped(raw, "{" if anticipated_brace else "[", "}" if anticipated_brace else "]")
    revised = _wrapped(raw, "(", ")")
    original = re.split(r"\s*[({[]", raw, maxsplit=1)[0].strip()
    return original, revised, anticipated


def _identity_modern(value: Any) -> tuple[str, str, str]:
    lines = [line.strip() for line in str(value or "").splitlines() if line.strip()]
    if len(lines) < 3 or not (lines[-1].startswith("(") and lines[-1].endswith(")")):
        raise ValueError("compound identity lacks official code")
    if not (lines[-2].startswith("(") and lines[-2].endswith(")")):
        raise ValueError("compound identity lacks agency")
    code = lines[-1][1:-1].strip().replace(" ", "")
    agency = lines[-2][1:-1].strip()
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", code) or len(re.sub(r"\D", "", code)) < 6:
        raise ValueError("official code malformed")
    name_lines = lines[:-2]
    # A code at the start belongs to the project split at the bottom of the
    # preceding physical page/row; it is used there and excluded here.
    if name_lines and re.fullmatch(r"\([A-Za-z0-9._/ -]+\)", name_lines[0]): name_lines = name_lines[1:]
    return " ".join(name_lines).strip(), agency, code


def _identity_ocms(value: Any) -> tuple[str, str, str, str]:
    raw = _clean(value)
    # Older OCMS reports do not consistently print a comma immediately after
    # the closing project-code bracket.  The agency/state comma remains the
    # authoritative delimiter, so tolerate only that observed punctuation
    # variation and retain the strict bracketed-code requirement.
    match = re.search(r"\s*-\s*\[([^\]]+)\]\s*,?\s*([^,]+)\s*,\s*(.+?)\s*,?$", raw)
    if not match: raise ValueError("OCMS identity tail missing")
    return raw[:match.start()].strip(), _clean(match.group(2)), _clean(match.group(3)), _clean(match.group(1)).replace(" ", "")


def _recover_ocms_footer_serial(value: Any) -> str:
    """Recover a serial only from the observed ``FLASH REPORT`` footer collision.

    In the October 2022 PDF, the footer's leading ``F`` is occasionally merged
    into the serial-number cell (for example, ``F 5`` or ``166 F``).  Restrict
    recovery to exactly those two shapes so arbitrary mixed-content cells remain
    structural/non-project rows and the extractor continues to fail closed.
    """
    raw = _clean(value)
    match = re.fullmatch(r"(?:F\s+(\d+)|(\d+)\s+F)", raw)
    return next((group for group in match.groups() if group), "") if match else raw


def _remove_ocms_flash_report_overlay(cells: list[Any]) -> tuple[list[Any], bool]:
    """Remove one evidenced diagonal ``FLASH REPORT`` watermark collision.

    A December 2020 vector page distributes the watermark across a single
    otherwise valid 10-column row.  Match the complete observed signature
    before removing any fragments; partial matches remain unresolved.
    """
    if len(cells) == 7:
        serial = str(cells[0] or "")
        signature = (
            re.fullmatch(r"\d+F\d+", serial) is not None
            and str(cells[2] or "").startswith("H")
            and str(cells[3] or "").startswith("R")
            and str(cells[4] or "").startswith("E")
            and str(cells[5] or "").startswith("O")
            and str(cells[6] or "").startswith("T")
        )
        second_signature = (
            " F L - A\n[" in str(cells[1] or "")
            and str(cells[2] or "").endswith("\nS")
            and "\nH R[" in str(cells[3] or "") and str(cells[3] or "").endswith(" E")
            and "\nP[" in str(cells[4] or "") and "O1]" in str(cells[4] or "")
            and "RT[" in str(cells[5] or "")
        )
        if second_signature:
            cleaned = list(cells)
            cleaned[1] = str(cells[1]).replace(" F L - A\n[", " -\n[")
            cleaned[2] = re.sub(r"\nS$", "", str(cells[2]))
            cleaned[3] = str(cells[3]).replace("\nH R[", "\n[")[:-2]
            cleaned[4] = str(cells[4]).replace("\nP[", "\n[").replace("O1]", "1]")
            cleaned[5] = str(cells[5]).replace("RT[", "[")
            return cleaned, True
        if not signature:
            return cells, False
        cleaned = list(cells)
        cleaned[0] = serial.replace("F", "")
        # The diagonal overlay contributes L/A/S inside the project-name text.
        # Remove only the three exact observed corruptions; the bracketed code,
        # agency and state remain the authoritative identity evidence.
        identity = str(cells[1] or "").replace("WIDELNING", "WIDENING")
        identity = identity.replace("ANDA UP-GRADATISON", "AND UP-GRADATION")
        cleaned[1] = identity
        cleaned[2] = str(cells[2])[1:]
        cleaned[3] = str(cells[3])[1:]
        cleaned[4] = str(cells[4])[1:].replace("P.", ".", 1)
        cleaned[5] = str(cells[5])[1:].replace(" R\n", "\n", 1)
        cleaned[6] = str(cells[6])[1:]
        return cleaned, True
    if len(cells) != 10:
        return cells, False
    identity = str(cells[1] or "")
    signature = (
        "Central Sector\nProjects" in identity
        and str(cells[2] or "").endswith("\nSH")
        and str(cells[4] or "").endswith("\nRE")
        and str(cells[5] or "").endswith("\nP")
        and "\nO-" in str(cells[6] or "")
        and str(cells[7] or "").endswith("\nRT")
    )
    if not signature:
        return cells, False
    cleaned = list(cells)
    cleaned[1] = re.sub(r"F(?=NH-\d)", "", identity)
    cleaned[1] = re.sub(r"\s+-\s+LA\s*\n(?=\[)", " -\n", str(cleaned[1]))
    cleaned[1] = re.sub(r"\s*,\s*Central Sector\s*\nProjects\s*$", "", str(cleaned[1]))
    cleaned[2] = re.sub(r"\nSH$", "", str(cells[2]))
    cleaned[4] = re.sub(r"\nRE$", "", str(cells[4]))
    cleaned[5] = re.sub(r"\nP$", "", str(cells[5]))
    cleaned[6] = str(cells[6]).replace("\nO-", "\n-")
    cleaned[7] = re.sub(r"\nRT$", "", str(cells[7]))
    return cleaned, True


def _base(month: str, serial: str, source_hash: str, page: int, row_index: int, discovery: dict[str, Any]) -> dict[str, Any]:
    return {
        "observation_id": f"OBS-{month.replace('-', '')}-{int(serial):05d}", "reporting_month": month,
        "serial_number_raw": serial, "source_id": source_id(month), "source_sha256": source_hash,
        "pdf_page_index": page, "printed_page_number": page - 1, "source_table": discovery["table_title"],
        "source_table_number": discovery["table_number"], "extraction_method": "pdfplumber_table",
        "extractor_version": BUILDER_VERSION, "raw_row_locator": f"pdf_page_index={page},table_index=0,row_index={row_index}",
        "schema_family": discovery["schema_family"], "ministry_raw": "", "project_status_raw": "",
        "legacy_ocms_code_raw": "-", "pmgid_raw": "-", "start_date_raw": "",
        "approval_start_cell_raw": "", "project_code_schema_available": "TRUE",
        "legacy_ocms_code_schema_available": "FALSE", "pmgid_schema_available": "FALSE",
    }


def extract_project_month(path: Path, month: str, discovery: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    digest = sha256(path); accepted: list[dict[str, Any]] = []; unresolved = []; structural = Counter(); raw_rows = 0
    ocms_footer_serials_recovered = 0; ocms_overlay_rows_recovered = 0; blank_continuation_pages = 0
    text_document = fitz.open(path)
    with pdfplumber.open(path) as pdf:
        for page_number in range(discovery["first_page"], discovery["last_page"] + 1):
            tables = pdf.pages[page_number - 1].extract_tables() or []
            if not tables:
                page_text = _text(text_document[page_number - 1]).strip()
                if re.fullmatch(r"(?is)FLASH\s+REPORT\s+\d+", page_text):
                    blank_continuation_pages += 1
                    continue
                raise RuntimeError(f"{month} page {page_number}: no table")
            table = max(tables, key=len)
            for row_index, row in enumerate(table):
                raw_rows += 1; cells = list(row); serial = ""; overlay_source_cells = ""
                non_null = [_clean(cell) for cell in cells if cell is not None]
                if non_null and non_null == [str(i) for i in range(1, len(non_null) + 1)]:
                    structural["COLUMN_ORDINAL_HEADER"] += 1
                    continue
                if len(cells) == 10 and _clean(cells[0]) == "1" and _clean(cells[1]).startswith("FLAS") and _clean(cells[-1]).endswith("T 10"):
                    structural["FLASH_REPORT_FOOTER_COLLISION"] += 1
                    continue
                original_cells = list(cells)
                cells, overlay_recovered = _remove_ocms_flash_report_overlay(cells)
                if overlay_recovered:
                    ocms_overlay_rows_recovered += 1
                    overlay_source_cells = json.dumps(original_cells, ensure_ascii=False)
                if discovery["schema_family"] == "PAIMANA_V1" and len(cells) >= 7: serial = _clean(cells[-7])
                elif discovery["schema_family"] == "OCMS":
                    serial = _recover_ocms_footer_serial(cells[0])
                    if serial.isdigit() and serial != _clean(cells[0]):
                        cells[0] = serial
                        ocms_footer_serials_recovered += 1
                if not serial.isdigit():
                    structural[classify_non_project_row(cells)] += 1
                    continue
                try:
                    rec = _base(month, serial, digest, page_number, row_index, discovery)
                    if overlay_source_cells:
                        rec["overlay_source_cells_raw"] = overlay_source_cells
                        rec["overlay_recovery_method"] = "EXACT_FLASH_REPORT_VECTOR_OVERLAY_SIGNATURE"
                    if discovery["schema_family"] == "PAIMANA_V1":
                        if len(cells) < 7: raise ValueError(f"expected at least 7 cells, found {len(cells)}")
                        prefix, cells = cells[:-7], cells[-7:]
                        identity_lines = [line.strip() for line in str(cells[1] or "").splitlines() if line.strip()]
                        tail = identity_lines[-1][1:-1].strip() if identity_lines and identity_lines[-1].startswith("(") and identity_lines[-1].endswith(")") else ""
                        tail_is_code = len(re.sub(r"\D", "", tail)) >= 6
                        if len(identity_lines) < 2 or not tail_is_code:
                            following = None
                            if row_index + 1 < len(table): following = list(table[row_index + 1])
                            elif page_number < discovery["last_page"]:
                                next_tables = pdf.pages[page_number].extract_tables() or []
                                if next_tables: following = list(max(next_tables, key=len)[0])
                            if following and len(following) >= 7:
                                lead = [line.strip() for line in str(following[-6] or "").splitlines() if line.strip()]
                                if lead and re.fullmatch(r"\([A-Za-z0-9._/ -]+\)", lead[0]):
                                    cells[1] = str(cells[1] or "") + "\n" + lead[0]
                            refreshed = [line.strip() for line in str(cells[1] or "").splitlines() if line.strip()]
                            refreshed_tail = refreshed[-1][1:-1].strip() if refreshed and refreshed[-1].startswith("(") and refreshed[-1].endswith(")") else ""
                            if len(re.sub(r"\D", "", refreshed_tail)) < 6:
                                # Some vector tables clip a code even though the
                                # same page's ordered text layer contains it.
                                # Recover only from this serial and approval date
                                # on the same physical page.
                                page_text = _text(text_document[page_number - 1])
                                approval_token = re.escape(_clean(cells[2]))
                                pattern = rf"(?:^|\s){re.escape(serial)}\s+.*?\(([^()]*)\)\s+\(([A-Za-z0-9._/ -]*\d[A-Za-z0-9._/ -]*)\)\s+{approval_token}(?:\s|$)"
                                matches = list(re.finditer(pattern, page_text))
                                recovered = [match.group(2).replace(" ", "") for match in matches if len(re.sub(r"\D", "", match.group(2))) >= 6]
                                if len(set(recovered)) == 1:
                                    cells[1] = str(cells[1] or "") + "\n(" + recovered[0] + ")"
                        name, agency, code = _identity_modern(cells[1]); doc0, doc1, doc2 = _triplet(cells[3], True); cost0, cost1, cost2 = _triplet(cells[4], True)
                        prefix_values = [_clean(x) for x in prefix]
                        state_value = prefix_values[0] if len(prefix_values) >= 2 else ""
                        sector_value = prefix_values[-1] if prefix_values else ""
                        rec.update(project_name_raw=name, agency_raw=agency, project_code_raw=code, state_raw=state_value, sector_raw=sector_value,
                                   approval_date_raw=_clean(cells[2]), original_target_doc_raw=doc0, revised_doc_raw=doc1,
                                   anticipated_doc_raw=doc2, original_cost_raw=cost0, revised_cost_raw=cost1,
                                   anticipated_cost_raw=cost2, cumulative_expenditure_raw=_clean(cells[5]), physical_progress_raw=_clean(cells[6]),
                                   milestones_raw="", project_identity_cell_raw=str(cells[1] or ""), approval_start_cell_raw=str(cells[2] or ""),
                                   doc_cell_raw=str(cells[3] or ""), cost_cell_raw=str(cells[4] or ""), physical_progress_schema_available="TRUE",
                                   anticipated_doc_schema_available="TRUE", anticipated_cost_schema_available="TRUE")
                    else:
                        # OCMS first-page headers introduce extraction-only null
                        # columns. In addition, the final project on many pages is
                        # physically split, with its continuation as the first row
                        # of the next page. Reconstruct only that directly adjacent
                        # continuation; never search or fuzzy-match rows.
                        if any(cell is None for cell in cells):
                            cells = [cell for cell in cells if cell is not None]
                        identity_probe = _clean(cells[1]) if len(cells) > 1 else ""
                        identity_complete = re.search(r"\[[^\]]+\]\s*,\s*[^,]+\s*,\s*.+$", identity_probe) is not None
                        if not identity_complete and page_number < discovery["last_page"]:
                            following_tables = pdf.pages[page_number].extract_tables() or []
                            if following_tables:
                                continuation = list(max(following_tables, key=len)[0])
                                if any(cell is None for cell in continuation):
                                    continuation = [cell for cell in continuation if cell is not None]
                                if len(continuation) == len(cells) and len(cells) in {7, 10} and not _clean(continuation[0]):
                                    cells = [cells[0]] + [
                                        "\n".join(part for part in (_clean(cells[i]), _clean(continuation[i])) if part)
                                        for i in range(1, len(cells))
                                    ]
                        if len(cells) == 7:
                            name, agency, state, code = _identity_ocms(cells[1]); doc0, doc1, doc2 = _triplet(cells[3], False); cost0, cost1, cost2 = _triplet(cells[4], False)
                            expenditure = _clean(cells[5]).split("(", 1)[0].strip(); milestones = _clean(cells[6])
                            schema_layout = "OCMS_7_COMPOUND"
                        elif len(cells) == 10:
                            name, agency, state, code = _identity_ocms(cells[1])
                            cost_parts = [_clean(part) for part in str(cells[3] or "").splitlines() if _clean(part)]
                            doc_parts = [_clean(part) for part in str(cells[6] or "").splitlines() if _clean(part)]
                            cost0 = cost_parts[0] if cost_parts else ""
                            cost1 = cost_parts[1] if len(cost_parts) > 1 and cost_parts[1] != "-" else ""
                            cost2 = _clean(cells[4])
                            doc0 = doc_parts[0] if doc_parts else ""
                            doc1 = doc_parts[1] if len(doc_parts) > 1 and doc_parts[1] != "-" else ""
                            doc2 = _clean(cells[7])
                            expenditure = _clean(cells[5]); milestones = _clean(cells[9])
                            schema_layout = "OCMS_10_COLUMN"
                        else:
                            raise ValueError(f"expected 7 or 10 cells, found {len(cells)}")
                        rec.update(project_name_raw=name, agency_raw=agency, project_code_raw=code, legacy_ocms_code_raw=code,
                                   state_raw=state, sector_raw="", approval_date_raw=_clean(cells[2]), original_target_doc_raw=doc0,
                                   revised_doc_raw=doc1, anticipated_doc_raw=doc2, original_cost_raw=cost0, revised_cost_raw=cost1,
                                   anticipated_cost_raw=cost2, cumulative_expenditure_raw=expenditure, physical_progress_raw="",
                                   milestones_raw=milestones, project_identity_cell_raw=str(cells[1] or ""), approval_start_cell_raw=str(cells[2] or ""),
                                   doc_cell_raw=str(cells[3] if len(cells)==7 else cells[6] or ""), cost_cell_raw=str(cells[4] if len(cells)==7 else cells[3] or ""), physical_progress_schema_available="FALSE",
                                   anticipated_doc_schema_available="TRUE", anticipated_cost_schema_available="TRUE",
                                   legacy_ocms_code_schema_available="TRUE", schema_layout=schema_layout)
                    accepted.append(rec)
                except ValueError as exc:
                    unresolved.append({"page": page_number, "row_index": row_index, "serial": serial, "reason": str(exc), "cells": cells})
    text_document.close()
    serials = [int(row["serial_number_raw"]) for row in accepted]
    official = discovery.get("official_project_count")
    serial_repairs = []
    if official is not None and len(accepted) == official and not unresolved:
        deviations = [(index, row) for index, row in enumerate(accepted, 1) if int(row["serial_number_raw"]) != index]
        codes = [row.get("project_code_raw") for row in accepted]
        if deviations and len(deviations) <= 3 and len(codes) == len(set(codes)):
            for expected, row in deviations:
                source_serial = row["serial_number_raw"]
                row["source_serial_number_raw"] = source_serial
                row["serial_number_raw"] = str(expected)
                row["observation_id"] = f"OBS-{month.replace('-', '')}-{expected:05d}"
                row["serial_recovery_method"] = "SEQUENTIAL_ROW_ORDER_WITH_OFFICIAL_COUNT_AND_UNIQUE_CODES"
                serial_repairs.append({"source_serial": source_serial, "recovered_serial": expected,
                                       "project_code": row.get("project_code_raw"), "page": row.get("pdf_page_index")})
            serials = [int(row["serial_number_raw"]) for row in accepted]
    duplicates = len(serials) - len(set(serials))
    missing = sorted(set(range(1, max(serials, default=0) + 1)) - set(serials))
    summary = {"reporting_month": month, "source_id": source_id(month), "source_sha256": digest, **discovery,
               "builder_version": BUILDER_VERSION,
               "accepted_project_rows": len(accepted), "serial_min": min(serials, default=None), "serial_max": max(serials, default=None),
               "missing_serials": missing, "duplicate_serials": duplicates, "total_raw_table_rows": raw_rows,
               "ocms_footer_serials_recovered": ocms_footer_serials_recovered,
               "ocms_overlay_rows_recovered": ocms_overlay_rows_recovered,
               "blank_continuation_pages": blank_continuation_pages,
               "serial_repairs": serial_repairs,
               "structural_counts": dict(structural), "unresolved_rows": unresolved,
               "row_accounting_valid": raw_rows == len(accepted) + sum(structural.values()) + len(unresolved)}
    count_mismatch = official is None or max(serials, default=0) != official or len(accepted) != official
    if not accepted or unresolved or duplicates or missing or count_mismatch or not summary["row_accounting_valid"]:
        reasons = Counter(item["reason"] for item in unresolved)
        raise RuntimeError(f"{month} extraction gate failed: official={official} accepted={len(accepted)} unresolved={len(unresolved)} duplicates={duplicates} missing={len(missing)} reasons={dict(reasons)} examples={unresolved[:2]}")
    return accepted, summary


def extract_aggregate(path: Path, month: str) -> list[dict[str, Any]]:
    document = fitz.open(path); digest = sha256(path); rows = []
    patterns = [
        ("official_projects_in_scope", r"(?i)(?:status of the|based on the).*?([\d,]+)\s*(?:Central Sector Infrastructure )?Projects"),
        ("delayed_projects", r"(?i)([\d,]+)\s+projects?\s+(?:are|were)\s+delayed"),
    ]
    for page_index, page in enumerate(document, start=1):
        text = _text(page)
        if _month_evidence(text, month) and not any(row["field_name"] == "reporting_month_evidence" for row in rows):
            rows.append({"source_id": source_id(month), "source_sha256": digest, "reporting_month": month,
                         "physical_page": page_index, "printed_page": page_index - 1, "section_table": "report identity",
                         "field_name": "reporting_month_evidence", "field_value_raw": month,
                         "raw_locator": f"pdf_page_index={page_index};normalized_month_evidence"})
        for field, pattern in patterns:
            match = re.search(pattern, text)
            if match and not any(row["field_name"] == field for row in rows):
                rows.append({"source_id": source_id(month), "source_sha256": digest, "reporting_month": month,
                             "physical_page": page_index, "printed_page": page_index - 1, "section_table": "report-level aggregate",
                             "field_name": field, "field_value_raw": match.group(1),
                             "raw_locator": f"pdf_page_index={page_index};regex={field}"})
    document.close(); return rows


def _protected_files(root: Path) -> list[Path]:
    paths = []
    for month in FROZEN_MONTHS:
        paths.extend([source_path(root, month), root / f"data/extracted/ongoing/ongoing_{month.replace('-', '_')}.csv"])
    for relative in [
        "data/processed/pilot_2025_07_2026_06/project_master.csv",
        "data/processed/pilot_2025_07_2026_06/project_month.csv",
        "data/processed/pilot_2025_07_2026_06/dataset_metadata.json",
    ]: paths.append(root / relative)
    for folder in [root / "data/processed/pilot_2026_05_06", root / "data/processed/pilot_2026_04_06"]:
        if folder.exists(): paths.extend(p for p in folder.rglob("*") if p.is_file())
    return sorted(set(p.resolve() for p in paths if p.exists()))


def _snapshot(paths: Iterable[Path], root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256(path) for path in paths}


def _canonicalize(all_rows: list[dict[str, Any]], frozen_project_month: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    bridge: dict[str, str] = {}
    conflicts: dict[str, set[str]] = defaultdict(set)
    for row in frozen_project_month:
        legacy = _clean(row.get("legacy_ocms_code_raw"))
        if legacy.upper() not in MISSING_TOKENS:
            conflicts[legacy].add(row["project_code"])
    for legacy, current in conflicts.items():
        if len(current) == 1: bridge[legacy] = next(iter(current))
    combined: list[dict[str, Any]] = []
    for row in all_rows:
        raw_code = _clean(row["project_code_raw"])
        canonical_code = bridge.get(raw_code, raw_code)
        method = "VERIFIED_LEGACY_OCMS_BRIDGE" if raw_code in bridge else "EXACT_SOURCE_IDENTIFIER"
        combined.append({**row, "canonical_project_id": f"PRH-{canonical_code}", "identity_method": method,
                         "identity_status": "RESOLVED_EXACT"})
    for row in frozen_project_month:
        month = row["reporting_month"]
        combined.append({**row, "project_code_raw": row["project_code"], "canonical_project_id": row["canonical_project_id"],
                         "identity_method": "EXISTING_VALIDATED_CANONICAL_ID", "identity_status": "RESOLVED_EXACT",
                         "schema_family": "PAIMANA", "anticipated_doc_raw": "", "anticipated_cost_raw": "",
                         "sector_raw": "", "ministry_raw": "", "milestones_raw": "", "project_status_raw": "",
                         # These flags describe what the frozen 12-month extraction actually exposes,
                         # so downstream audits do not misclassify an absent column as a missing value.
                         "project_code_schema_available": "TRUE",
                         "legacy_ocms_code_schema_available": "TRUE" if month >= "2026-02" else "FALSE",
                         "pmgid_schema_available": "TRUE" if month >= "2026-04" else "FALSE",
                         "physical_progress_schema_available": "TRUE",
                         "anticipated_doc_schema_available": "FALSE",
                         "anticipated_cost_schema_available": "FALSE"})
    keys = [(row["canonical_project_id"], row["reporting_month"]) for row in combined]
    if len(keys) != len(set(keys)): raise RuntimeError("duplicate canonical project-month keys after exact bridge")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in combined: grouped[row["canonical_project_id"]].append(row)
    project_month = []
    gap_counts = Counter()
    for canonical, observations in grouped.items():
        observations.sort(key=lambda r: r["reporting_month"])
        for index, row in enumerate(observations):
            previous = observations[index - 1]["reporting_month"] if index else ""
            following = observations[index + 1]["reporting_month"] if index + 1 < len(observations) else ""
            prev_gap = month_distance(previous, row["reporting_month"]) if previous else ""
            next_gap = month_distance(row["reporting_month"], following) if following else ""
            if isinstance(prev_gap, int): gap_counts[prev_gap] += 1
            project_month.append({**row, "previous_project_observation_month": previous,
                                  "months_since_previous_project_observation": prev_gap,
                                  "next_project_observation_month": following, "months_to_next_project_observation": next_gap,
                                  "calendar_gap_present": str(bool((isinstance(prev_gap, int) and prev_gap > 1) or (isinstance(next_gap, int) and next_gap > 1))).upper()})
    master = []
    for canonical, observations in sorted(grouped.items()):
        observations.sort(key=lambda r: r["reporting_month"]); latest = observations[-1]
        master.append({"canonical_project_id": canonical, "project_code": _clean(latest.get("project_code_raw", latest.get("project_code", ""))),
                       "legacy_ocms": _clean(latest.get("legacy_ocms_code_raw")), "pmgid": _clean(latest.get("pmgid_raw")),
                       "canonical_name": latest.get("project_name_raw", latest.get("reported_project_name", "")),
                       "agency": latest.get("agency_raw", latest.get("reported_agency", "")), "ministry": latest.get("ministry_raw", ""),
                       "sector": latest.get("sector_raw", ""), "state": latest.get("state_raw", latest.get("reported_state", "")),
                       "first_observed_month": observations[0]["reporting_month"], "last_observed_month": latest["reporting_month"],
                       "project_level_observation_count": len(observations),
                       "calendar_span_months": month_distance(observations[0]["reporting_month"], latest["reporting_month"]) + 1,
                       "identity_method": latest["identity_method"], "identity_status": latest["identity_status"]})
    return master, project_month, {"legacy_bridge_entries": len(bridge), "ambiguous_legacy_codes": sorted(k for k, v in conflicts.items() if len(v) > 1), "interval_counts": dict(gap_counts)}


def month_distance(left: str, right: str) -> int:
    ly, lm = map(int, left.split("-")); ry, rm = map(int, right.split("-"))
    return (ry - ly) * 12 + rm - lm


def calendar_boundaries(coverage: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classes = {row["reporting_month"]: row["coverage_class"] for row in coverage}; rows = []
    for left, right in zip(MONTHS, MONTHS[1:]):
        lc, rc = classes[left], classes[right]
        if "MISSING_SOURCE" in (lc, rc): kind = "CROSSES_MISSING_MONTH"
        elif lc == rc == "PROJECT_LEVEL": kind = "CONTIGUOUS_PROJECT_LEVEL"
        elif lc == rc == "AGGREGATE_ONLY": kind = "AGGREGATE_TO_AGGREGATE"
        elif lc == "PROJECT_LEVEL": kind = "LEFT_PROJECT_RIGHT_AGGREGATE"
        else: kind = "LEFT_AGGREGATE_RIGHT_PROJECT"
        rows.append({"left_month": left, "right_month": right, "left_coverage": lc, "right_coverage": rc, "boundary_class": kind})
    return rows


def horizon_observability(coverage: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classes = {row["reporting_month"]: row["coverage_class"] for row in coverage}; result = []
    for anchor_index, anchor in enumerate(MONTHS):
        for horizon in (3, 6, 12):
            future = list(MONTHS[anchor_index + 1:anchor_index + 1 + horizon])
            available = [month for month in future if classes[month] == "PROJECT_LEVEL"]
            unavailable = [month for month in future if classes[month] != "PROJECT_LEVEL"]
            if len(future) < horizon: status = "RIGHT_CENSORED"
            elif not unavailable: status = "FULLY_OBSERVABLE"
            else: status = "CENSORED_BY_GAP"
            result.append({"anchor_month": anchor, "horizon_months": horizon,
                           "calendar_months_in_window": len(future), "project_level_months_available": len(available),
                           "unavailable_months": "|".join(unavailable), "observability_status": status})
    return result


def field_availability(project_month: list[dict[str, Any]]) -> list[dict[str, Any]]:
    definitions = [
        ("project_name", "project_name_raw", "reported_project_name", None),
        ("agency", "agency_raw", "reported_agency", None), ("state", "state_raw", "reported_state", None),
        ("approval_date", "approval_date_raw", "reported_approval_date", None),
        ("start_date", "start_date_raw", "reported_start_date", None),
        ("original_target_doc", "original_target_doc_raw", "reported_original_target_doc", None),
        ("revised_doc", "revised_doc_raw", "reported_revised_doc", None),
        ("original_cost", "original_cost_raw", "reported_original_cost", None),
        ("revised_cost", "revised_cost_raw", "reported_revised_cost", None),
        ("cumulative_expenditure", "cumulative_expenditure_raw", "reported_cumulative_expenditure", None),
        ("physical_progress", "physical_progress_raw", "reported_physical_progress", "physical_progress_schema_available"),
        ("anticipated_doc", "anticipated_doc_raw", None, "anticipated_doc_schema_available"),
        ("anticipated_cost", "anticipated_cost_raw", None, "anticipated_cost_schema_available"),
        ("legacy_ocms", "legacy_ocms_code_raw", None, "legacy_ocms_code_schema_available"),
        ("pmgid", "pmgid_raw", None, "pmgid_schema_available"),
    ]
    result = []
    for field, primary, fallback, flag in definitions:
        present = value_missing = unavailable = 0; months = set()
        for row in project_month:
            schema_available = row.get(flag, "TRUE") != "FALSE" if flag else True
            if not schema_available: unavailable += 1; continue
            value = _clean(row.get(primary, "") or (row.get(fallback, "") if fallback else ""))
            if value.upper() in MISSING_TOKENS: value_missing += 1
            else: present += 1; months.add(row["reporting_month"])
        result.append({"field_name": field, "project_month_rows": len(project_month), "present_values": present,
                       "value_missing": value_missing, "field_not_in_schema": unavailable,
                       "project_level_months_with_present_value": len(months), "months_with_present_value": "|".join(sorted(months))})
    return result


def _sample(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(rows) <= 20: chosen = rows
    else:
        ordered = sorted(rows, key=lambda r: int(r["serial_number_raw"])); chosen = [ordered[0], ordered[-1]]
        pool = [row for row in ordered[1:-1]]; chosen.extend(random.Random(SAMPLE_SEED).sample(pool, 18))
    return [{**row, "sample_category": "BOUNDARY" if row in (rows[:1] + rows[-1:]) else "SEEDED_FILL",
             "manual_row_confirmed": "", "manual_identity_confirmed": "", "manual_fields_confirmed": "",
             "manual_provenance_confirmed": "", "reviewer": "", "review_notes": ""} for row in chosen]


def build(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve(); protected_paths = _protected_files(root); protected_before = _snapshot(protected_paths, root)
    coverage, inspections = build_coverage(root)
    counts = Counter(row["coverage_class"] for row in coverage)
    if counts != Counter({"PROJECT_LEVEL": 30, "AGGREGATE_ONLY": 5, "MISSING_SOURCE": 1}):
        raise RuntimeError(f"coverage contract changed: {counts}")
    bad = [row["reporting_month"] for row in coverage if row["coverage_class"] != "MISSING_SOURCE" and row["quality_status"] != "PASS"]
    if bad: raise RuntimeError(f"source integrity failed: {bad}")
    write_csv(root / "data/metadata/source_coverage_2023_07_2026_06.csv", coverage, list(coverage[0]), root)
    all_new_rows = []; summaries = {}; schema_rows = []
    for month in NEW_PROJECT_MONTHS:
        tag = month.replace("-", "_")
        cached_rows = root / f"data/extracted/ongoing/ongoing_{tag}.csv"
        cached_summary = root / f"validation/extraction_validation/{month}/{tag}_extraction_summary.json"
        if cached_rows.exists() and cached_summary.exists():
            candidate_summary = json.loads(cached_summary.read_text(encoding="utf-8"))
            if (candidate_summary.get("source_sha256") == sha256(source_path(root, month))
                    and candidate_summary.get("builder_version") == BUILDER_VERSION
                    and candidate_summary.get("source_id") == source_id(month)):
                rows, summary = read_csv(cached_rows), candidate_summary
            else:
                discovery = discover_table(source_path(root, month)); rows, summary = extract_project_month(source_path(root, month), month, discovery)
        else:
            discovery = discover_table(source_path(root, month)); rows, summary = extract_project_month(source_path(root, month), month, discovery)
        all_new_rows.extend(rows); summaries[month] = summary
        write_csv(root / f"data/extracted/ongoing/ongoing_{tag}.csv", rows, EXTRACTED_COLUMNS, root)
        write_csv(root / f"validation/extraction_validation/{month}/{tag}_manual_sample.csv", _sample(rows), EXTRACTED_COLUMNS + ["sample_category", "manual_row_confirmed", "manual_identity_confirmed", "manual_fields_confirmed", "manual_provenance_confirmed", "reviewer", "review_notes"], root)
        write_json_replace(root / f"validation/extraction_validation/{month}/{tag}_extraction_summary.json", summary, repo_root=root)
    aggregate_paths = {}
    for month in sorted(AGGREGATE_ONLY):
        rows = extract_aggregate(source_path(root, month), month); path = root / f"data/extracted/aggregate/monthly_aggregate_{month.replace('-', '_')}.csv"
        write_csv(path, rows, ["source_id", "source_sha256", "reporting_month", "physical_page", "printed_page", "section_table", "field_name", "field_value_raw", "raw_locator"], root)
        aggregate_paths[month] = path.relative_to(root).as_posix()
    update_manifest_and_provenance(root, all_new_rows, summaries)
    for month in MONTHS:
        row = next(r for r in coverage if r["reporting_month"] == month)
        summary = summaries.get(month, {})
        schema_rows.append({"reporting_month": month, "coverage_class": row["coverage_class"], "table_number": summary.get("table_number", ""),
                            "table_title": summary.get("table_title", ""), "schema_family": summary.get("schema_family", "NO_PROJECT_LEVEL_SCHEMA" if row["coverage_class"] != "PROJECT_LEVEL" else "PAIMANA"),
                            "column_structure": "7-cell compound OCMS" if summary.get("schema_family") == "OCMS" else ("9-cell PAIMANA" if summary else ""),
                            "identity_availability": summary.get("identity_fields", ""), "project_code": str(row["coverage_class"] == "PROJECT_LEVEL").upper(),
                            "legacy_ocms": str(summary.get("schema_family") == "OCMS").upper(), "pmgid": "FALSE", "ministry": "FALSE", "sector": str(summary.get("schema_family") == "PAIMANA_V1").upper(),
                            "status": "FALSE", "anticipated_cost_date": str(bool(summary)).upper(), "milestones": str(summary.get("schema_family") == "OCMS").upper(),
                            "adapter": summary.get("schema_family", "NONE"), "confidence": summary.get("confidence", "N/A"), "notes": row["reason"]})
    schema_fields = list(schema_rows[0]); write_csv(root / "data/metadata/schema_family_2023_07_2026_06.csv", schema_rows, schema_fields, root)
    frozen_pm = read_csv(root / "data/processed/pilot_2025_07_2026_06/project_month.csv")
    master, project_month, identity = _canonicalize(all_new_rows, frozen_pm)
    out = root / "data/processed/longitudinal_2023_07_2026_06_mixed"
    master_fields = list(master[0]); pm_fields = sorted({key for row in project_month for key in row})
    write_csv(out / "project_master.csv", master, master_fields, root); write_csv(out / "project_month.csv", project_month, pm_fields, root)
    boundaries = calendar_boundaries(coverage); write_csv(out / "calendar_boundaries.csv", boundaries, list(boundaries[0]), root)
    horizons = horizon_observability(coverage); write_csv(out / "horizon_observability.csv", horizons, list(horizons[0]), root)
    availability = field_availability(project_month); write_csv(out / "field_availability.csv", availability, list(availability[0]), root)
    report_rows = [{"reporting_month": row["reporting_month"], "coverage_class": row["coverage_class"], "source_id": row["source_id"],
                    "source_present": row["source_present"], "project_level_usable": row["project_level_usable"],
                    "official_project_count": summaries.get(row["reporting_month"], {}).get("serial_max", ""),
                    "schema_family": next(s["schema_family"] for s in schema_rows if s["reporting_month"] == row["reporting_month"]),
                    "source_quality_status": row["quality_status"]} for row in coverage]
    write_csv(out / "report_month.csv", report_rows, list(report_rows[0]), root)
    metadata = {"dataset_version": DATASET_VERSION, "status": DATASET_STATUS, "created_at": "2026-09-06T00:00:00+05:30",
                "calendar_window": [MONTHS[0], MONTHS[-1]], "intended_calendar_months": 36, "project_level_months": list(PROJECT_MONTHS),
                "aggregate_only_months": sorted(AGGREGATE_ONLY), "missing_source_months": sorted(MISSING_SOURCE), "excluded_duplicate_months": ["2026-07"],
                "monthly_row_counts": {m: summaries[m]["accepted_project_rows"] for m in summaries} | {m: sum(1 for r in frozen_pm if r["reporting_month"] == m) for m in FROZEN_MONTHS},
                "canonical_project_count": len(master), "project_month_rows": len(project_month), "identity_audit": identity,
                "aggregate_artifacts": aggregate_paths, "source_inspections": inspections, "human_validation_status": "PENDING_FOR_18_NEW_PROJECT_LEVEL_MONTHS",
                "forbidden_transformations_applied": [], "known_limitations": ["five aggregate-only months", "February 2025 source missing", "July 2026 duplicate excluded", "no inferred lifecycle"]}
    write_json_replace(out / "dataset_metadata.json", metadata, repo_root=root)
    protected_after = _snapshot(protected_paths, root)
    if protected_before != protected_after: raise RuntimeError("protected artifact hash changed")
    hash_audit = {"status": "PASS", "files": protected_after}; write_json_replace(out / "protected_hash_audit.json", hash_audit, repo_root=root)
    return {"coverage": dict(counts), "new_months": len(NEW_PROJECT_MONTHS), "new_rows": len(all_new_rows), "master_rows": len(master),
            "project_month_rows": len(project_month), "summaries": summaries, "identity": identity, "protected_hashes": hash_audit}
