"""
PRAHARI Gate 2 — Batch PDF Audit Script
scripts/audit_all_pdfs.py

Runs pdf_inspector + schema_detector on all canonical/multipart source files.
Excludes REJECTED_DUPLICATE and MISSING manifest entries.

REPRODUCIBILITY:
- Every run gets a unique audit_run_id (timestamp-based).
- Output is written to outputs/reports/audit_<audit_run_id>.json
- A symlink/copy "audit_latest.json" is kept pointing to the most recent run.
- Historical audit outputs are NEVER overwritten.

RAW-PATH GUARD:
- This script never writes to data/raw/.
- All writes use the centralized resolved-path safe I/O utility.

SHA-256 VERIFICATION:
- For each file, SHA-256 is verified against source_manifest BEFORE inspection.
- Hash is verified again AFTER inspection.
- Mismatch = INSPECTION_FAILED.

Usage:
    python scripts/audit_all_pdfs.py [--config config.yaml] [--max-pages N]
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import platform
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import yaml

from src.extraction.pdf_inspector import compute_sha256, inspect_pdf
from src.extraction.schema_detector import SchemaEvidence, detect_schema
from src.pipeline.source_registry import (
    ELIGIBLE_STATUSES, EXCLUDED_STATUSES, SourceRegistryError, resolve_source,
    resolve_primary_target,
)
from src.utils.safe_io import write_json, write_json_replace

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Version info for reproducibility
# ---------------------------------------------------------------------------

def _get_library_version(module_name: str) -> str:
    try:
        import importlib.metadata
        return importlib.metadata.version(module_name)
    except Exception:
        try:
            mod = __import__(module_name)
            return getattr(mod, "__version__", "UNKNOWN")
        except ImportError:
            return "NOT_INSTALLED"


def _build_run_metadata(config: dict, config_hash: str) -> dict:
    return {
        "audit_run_id": f"audit-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "pdfplumber_version": _get_library_version("pdfplumber"),
        "PyMuPDF_version": _get_library_version("pymupdf"),
        "pipeline_version": config.get("project", {}).get("version", "UNKNOWN"),
        "config_hash": config_hash,
        "platform": platform.platform(),
    }


# ---------------------------------------------------------------------------
# Manifest loader — only eligible files
# ---------------------------------------------------------------------------

def load_eligible_manifest_rows(manifest_path: Path) -> list[dict]:
    """Load source_manifest.csv rows with file_status in ELIGIBLE_STATUSES."""
    rows = []
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            status = row.get("file_status", "").strip()
            if status in ELIGIBLE_STATUSES:
                rows.append(row)
            elif status in EXCLUDED_STATUSES:
                logger.info("Skipping %s — file_status=%s", row.get("filename", "?"), status)
            else:
                logger.warning("Unknown file_status='%s' for %s — skipping", status, row.get("filename", "?"))
    return rows


# ---------------------------------------------------------------------------
# SHA-256 guard
# ---------------------------------------------------------------------------

def _verify_sha256_or_fail(path: Path, expected: str, label: str) -> str | None:
    """
    Compute and compare SHA-256. Returns None on match, error string on mismatch.
    """
    if not expected or expected.strip() == "":
        return f"{label}: No expected SHA-256 in manifest — cannot verify"
    try:
        actual = compute_sha256(path)
    except Exception as exc:  # noqa: BLE001
        return f"{label}: SHA-256 computation failed: {exc}"
    if actual.lower() != expected.lower().strip():
        return (
            f"{label}: SHA-256 MISMATCH. "
            f"Expected={expected[:16]}...  Got={actual[:16]}..."
        )
    return None


# ---------------------------------------------------------------------------
# Known table pages from config
# ---------------------------------------------------------------------------

def _get_known_table_pages(config: dict, filename: str) -> list[int] | None:
    """
    Return known table page numbers for a specific file from config,
    or None if not configured.
    """
    target = config.get("extraction", {}).get("primary_target", {})
    if target.get("source_file", "") == filename:
        pages = target.get("representative_pdf_page_indices")
        if pages:
            return [int(page) for page in pages]
    return None


# ---------------------------------------------------------------------------
# Main audit function
# ---------------------------------------------------------------------------

def audit_one(
    manifest_row: dict,
    config: dict,
    max_pages: int | None,
    run_meta: dict,
) -> dict:
    """
    Run full inspection + schema detection on one manifest row.
    Returns a combined result dict.
    """
    filename = manifest_row.get("filename", "UNKNOWN")
    rel_path = manifest_row.get("relative_path", "")
    expected_sha256 = manifest_row.get("sha256", "")
    source_id = manifest_row.get("source_id", "")

    result = {
        "source_id": source_id,
        "source_group_id": manifest_row.get("source_group_id", ""),
        "source_part": manifest_row.get("source_part", ""),
        "filename": filename,
        "relative_path": rel_path,
        "file_status": manifest_row.get("file_status", ""),
        "audit_run_id": run_meta["audit_run_id"],
        "sha256_pre_check": None,
        "sha256_pre_match": None,
        "sha256_post_check": None,
        "sha256_post_match": None,
        "inspection": None,
        "schema": None,
        "audit_errors": [],
    }

    try:
        resolved = resolve_source(
            source_id,
            REPO_ROOT / config.get("manifest", {}).get("file", "data/metadata/source_manifest.csv"),
            REPO_ROOT,
        )
        pdf_path = resolved.path
    except SourceRegistryError as exc:
        result["audit_errors"].append(str(exc))
        result["inspection"] = {"document_text_extractable": "INSPECTION_FAILED", "errors": [str(exc)]}
        result["schema"] = {"detected_schema": "INSPECTION_FAILED", "error_detail": str(exc)}
        return result

    # File existence check
    if not pdf_path.exists():
        result["audit_errors"].append(f"File not found: {pdf_path}")
        result["inspection"] = {"document_text_extractable": "FAILED", "errors": ["file_not_found"]}
        result["schema"] = {"detected_schema": "INSPECTION_FAILED", "error_detail": "file_not_found"}
        return result

    # PRE-inspection SHA-256 verify
    pre_err = _verify_sha256_or_fail(pdf_path, expected_sha256, "PRE")
    result["sha256_pre_check"] = compute_sha256(pdf_path)
    result["sha256_pre_match"] = pre_err is None
    if pre_err:
        result["audit_errors"].append(pre_err)
        logger.error("SHA-256 PRE-check FAILED for %s: %s", filename, pre_err)
        result["inspection"] = {"document_text_extractable": "INSPECTION_FAILED", "errors": [pre_err]}
        result["schema"] = {"detected_schema": "INSPECTION_FAILED", "error_detail": pre_err}
        return result

    # Get known table pages from config
    known_table_pages = _get_known_table_pages(config, filename)

    # PDF inspection
    logger.info("  Inspecting: %s", filename)
    inspection = inspect_pdf(pdf_path, repo_root=REPO_ROOT, known_table_pages=known_table_pages)
    result["inspection"] = inspection.to_dict()

    # Schema detection
    logger.info("  Schema detection: %s", filename)
    schema_ev: SchemaEvidence = detect_schema(pdf_path, config, max_pages=max_pages)
    result["schema"] = schema_ev.to_dict()

    # POST-inspection SHA-256 verify
    post_err = _verify_sha256_or_fail(pdf_path, expected_sha256, "POST")
    result["sha256_post_check"] = compute_sha256(pdf_path)
    result["sha256_post_match"] = post_err is None
    if post_err:
        result["audit_errors"].append(f"CRITICAL: {post_err} — source file may have been modified during inspection!")
        logger.error("SHA-256 POST-check FAILED for %s — FILE MODIFIED DURING INSPECTION!", filename)
        result["inspection"] = {
            "document_text_extractable": "INSPECTION_FAILED",
            "errors": [post_err],
            "invalidated": True,
        }
        result["schema"] = {
            "detected_schema": "INSPECTION_FAILED",
            "confidence": "NONE",
            "error_detail": post_err,
            "invalidated": True,
        }

    return result


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _write_output(out_dir: Path, audit_run_id: str, payload: dict) -> Path:
    """Write timestamped audit JSON. Never overwrites historical runs."""
    out_file = out_dir / f"{audit_run_id}.json"
    write_json(out_file, payload, repo_root=REPO_ROOT)

    # Update "latest" pointer (plain JSON file, NOT a symlink, for Windows compatibility)
    latest_file = out_dir / "audit_latest.json"
    latest_pointer = {"latest_audit_run_id": audit_run_id, "latest_file": out_file.name}
    write_json_replace(latest_file, latest_pointer, repo_root=REPO_ROOT)

    return out_file


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def _print_summary(results: list[dict]) -> None:
    print("\n" + "=" * 100)
    print(f"{'SOURCE_ID':<24} {'FILENAME':<44} {'PGS':>4} {'TEXT':>6} {'SCHEMA':<18} {'CONF':<7} {'PRE_SHA':>7} {'POST_SHA':>8}")
    print("=" * 100)
    for r in results:
        insp = r.get("inspection") or {}
        schema = r.get("schema") or {}
        pages = insp.get("page_count") or "ERR"
        text = insp.get("document_text_extractable", "?")
        sch = schema.get("detected_schema", "?")
        conf = schema.get("confidence", "?")
        pre = "OK" if r.get("sha256_pre_match") else "FAIL"
        post = "OK" if r.get("sha256_post_match") else "FAIL"
        fname = r["filename"][:43]
        print(f"{r['source_id']:<24} {fname:<44} {str(pages):>4} {text:>6} {sch:<18} {conf:<7} {pre:>7} {post:>8}")
        if r.get("audit_errors"):
            for err in r["audit_errors"]:
                print(f"  *** ERROR: {err}")
    print("=" * 100)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="PRAHARI — Batch PDF Audit")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--max-pages", type=int, default=None,
                        help="Limit pages per PDF for schema detection (default: all)")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    config_bytes = config_path.read_bytes()
    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    run_meta = _build_run_metadata(config, hashlib.sha256(config_bytes).hexdigest())
    logger.info("Audit run: %s", run_meta["audit_run_id"])
    logger.info("Python: %s  pdfplumber: %s", run_meta["python_version"], run_meta["pdfplumber_version"])

    manifest_path = REPO_ROOT / config.get("manifest", {}).get("file", "data/metadata/source_manifest.csv")
    manifest_rows = load_eligible_manifest_rows(manifest_path)
    # Fail before auditing if canonical target metadata contradicts the manifest.
    resolve_primary_target(config, REPO_ROOT)
    logger.info("Eligible source files: %d", len(manifest_rows))

    results = []
    for row in manifest_rows:
        logger.info("Auditing: %s (%s)", row.get("filename"), row.get("source_id"))
        r = audit_one(row, config, max_pages=args.max_pages, run_meta=run_meta)
        results.append(r)

    # Build output payload
    payload = {
        "run_metadata": run_meta,
        "total_files_audited": len(results),
        "results": results,
    }

    out_dir = REPO_ROOT / "outputs" / "reports" / "audit_runs"
    out_file = _write_output(out_dir, run_meta["audit_run_id"], payload)
    logger.info("Audit output: %s", out_file)

    _print_summary(results)

    # Return non-zero exit code if any file had errors
    any_errors = any(r.get("audit_errors") for r in results)
    return 1 if any_errors else 0


if __name__ == "__main__":
    sys.exit(main())
