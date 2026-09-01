"""
PRAHARI — src/extraction/pdf_inspector.py

PDF integrity inspection for MoSPI Flash Report source files.

DESIGN PRINCIPLES (updated after Codex review 2026-09-01):

1. If a required extraction dependency is unavailable, text_extractable returns
   UNKNOWN (string), NOT True/False.

2. Document-level and target-table-level extractability are DISTINGUISHED.

3. Sampling strategy:
     - cover/early page (pages 1–3)
     - representative middle page
     - detected project-table page (if known)
     - near-end page
   Results stored per sampled page.

4. compute_sha256 is the authoritative file integrity check. All callers must
   verify SHA-256 before AND after processing against source_manifest.

5. This module does NOT write to data/raw/. It only reads.

6. No OCR is performed. If target-table pages yield zero chars, that is recorded
   as ocr_may_be_required=True — it does NOT trigger OCR.

EXTRACTABILITY VALUES:
    "YES"      — pdfplumber available and text extracted successfully
    "NO"       — pdfplumber available but text yields 0 chars on sampled pages
    "UNKNOWN"  — pdfplumber not installed; cannot determine extractability
    "FAILED"   — pdfplumber available but an exception occurred during extraction
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.utils.safe_io import safe_destination

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Raw-path write guard
# ---------------------------------------------------------------------------

def _assert_not_raw_path(path: Path | str) -> None:
    """
    Raise ValueError if path is inside data/raw/.

    This guard must be called before any write operation.
    The data/raw directory is treated as an immutable source store.
    """
    safe_destination(path)


# ---------------------------------------------------------------------------
# SHA-256 integrity
# ---------------------------------------------------------------------------

def compute_sha256(path: Path, chunk_size: int = 65536) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        path       : Path to file. Must exist.
        chunk_size : Read buffer size in bytes.

    Returns:
        Lowercase hex digest string (64 chars).

    Raises:
        FileNotFoundError if path does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_sha256(path: Path, expected_hex: str) -> bool:
    """
    Compare file SHA-256 against an expected value.
    Returns True if matched, False otherwise.
    """
    actual = compute_sha256(path)
    return actual.lower() == expected_hex.lower()


# ---------------------------------------------------------------------------
# Per-page sample result
# ---------------------------------------------------------------------------

@dataclass
class PageSample:
    page_number: int       # 1-indexed
    char_count: int
    table_count: int
    snippet: str           # first 120 chars of text
    contains_project_table_markers: bool
    extractable: str       # YES | NO | FAILED


@dataclass
class InspectionResult:
    """Full inspection result for one PDF file."""

    filename: str
    relative_path: str
    file_size_bytes: int
    sha256: str | None
    page_count: int | None
    opens_ok: bool

    # Document-level extractability
    document_text_extractable: str   # YES | NO | UNKNOWN | FAILED
    # Target-table extractability (based on known or detected table pages)
    table_text_extractable: str      # YES | NO | UNKNOWN | FAILED | NOT_CHECKED
    table_page_text_status: str       # STRUCTURED_TEXT | TEXT_ONLY | NO_TEXT | FAILED | NOT_CHECKED

    ocr_may_be_required: bool
    sampled_pages: list[PageSample] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    page_errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "relative_path": self.relative_path,
            "file_size_bytes": self.file_size_bytes,
            "sha256": self.sha256,
            "page_count": self.page_count,
            "opens_ok": self.opens_ok,
            "document_text_extractable": self.document_text_extractable,
            "table_text_extractable": self.table_text_extractable,
            "table_page_text_status": self.table_page_text_status,
            "ocr_may_be_required": self.ocr_may_be_required,
            "sampled_pages": [
                {
                    "page_number": s.page_number,
                    "char_count": s.char_count,
                    "table_count": s.table_count,
                    "snippet": s.snippet,
                    "contains_project_table_markers": s.contains_project_table_markers,
                    "extractable": s.extractable,
                }
                for s in self.sampled_pages
            ],
            "errors": self.errors,
            "notes": self.notes,
            "page_errors": self.page_errors,
        }


# ---------------------------------------------------------------------------
# Project-table marker detection
# ---------------------------------------------------------------------------

_PROJECT_TABLE_MARKERS = [
    "All Ongoing Projects",
    "Project Code",
    "Project Name",
    "Ongoing Projects",
    "Completed Projects",
    "Legacy OCMS Code",
    "PMGID",
]


def _has_project_table_markers(text: str) -> bool:
    return any(marker in text for marker in _PROJECT_TABLE_MARKERS)


# ---------------------------------------------------------------------------
# Page index selection for sampling
# ---------------------------------------------------------------------------

def _select_sample_page_indices(
    total_pages: int,
    known_table_pages: list[int] | None = None,
) -> list[int]:
    """
    Return 0-indexed page indices to sample for extractability testing.

    Strategy:
    - Pages 0, 1, 2  (cover/early)
    - Mid-document page
    - Last 2 pages
    - Any known project-table pages (0-indexed)
    """
    indices: set[int] = set()

    for i in range(min(3, total_pages)):
        indices.add(i)

    if total_pages > 5:
        indices.add(total_pages // 2)

    for i in range(max(0, total_pages - 2), total_pages):
        indices.add(i)

    if known_table_pages:
        for p in known_table_pages:
            idx = p - 1  # convert to 0-indexed
            if 0 <= idx < total_pages:
                indices.add(idx)

    return sorted(indices)


# ---------------------------------------------------------------------------
# Main inspection function
# ---------------------------------------------------------------------------

def inspect_pdf(
    path: Path,
    repo_root: Path | None = None,
    known_table_pages: list[int] | None = None,
) -> InspectionResult:
    """
    Inspect a single PDF for integrity and text extractability.

    Args:
        path              : Absolute path to the PDF.
        repo_root         : Repository root for relative_path calculation.
        known_table_pages : 1-indexed list of pages known to contain project tables.
                            If provided, those pages are explicitly sampled.

    Returns:
        InspectionResult — never raises; errors captured in result.errors.
    """
    rel_path = str(path.relative_to(repo_root)) if repo_root else str(path)

    result = InspectionResult(
        filename=path.name,
        relative_path=rel_path.replace("\\", "/"),
        file_size_bytes=path.stat().st_size if path.exists() else -1,
        sha256=None,
        page_count=None,
        opens_ok=False,
        document_text_extractable="UNKNOWN",
        table_text_extractable="NOT_CHECKED",
        table_page_text_status="NOT_CHECKED",
        ocr_may_be_required=False,
    )

    if not path.exists():
        result.errors.append("File does not exist")
        result.document_text_extractable = "FAILED"
        return result

    # SHA-256
    try:
        result.sha256 = compute_sha256(path)
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"SHA256 failed: {exc}")

    # Check pdfplumber availability
    try:
        import pdfplumber
        pdfplumber_available = True
    except ImportError:
        pdfplumber_available = False
        result.document_text_extractable = "UNKNOWN"
        result.table_text_extractable = "UNKNOWN"
        result.table_page_text_status = "UNKNOWN"
        result.notes.append("pdfplumber not installed — text extractability UNKNOWN")
        return result

    # Open PDF
    try:
        with pdfplumber.open(str(path)) as pdf:
            result.page_count = len(pdf.pages)
            result.opens_ok = True

            sample_indices = _select_sample_page_indices(
                result.page_count, known_table_pages
            )

            doc_char_counts = []
            table_page_chars = []

            for idx in sample_indices:
                page = pdf.pages[idx]
                try:
                    txt = page.extract_text() or ""
                    tables = page.extract_tables() or []
                    char_count = len(txt)
                    has_markers = _has_project_table_markers(txt)

                    sample = PageSample(
                        page_number=idx + 1,
                        char_count=char_count,
                        table_count=len(tables),
                        snippet=txt.strip()[:120].replace("\n", " | "),
                        contains_project_table_markers=has_markers,
                        extractable="YES" if char_count > 50 else "NO",
                    )
                    result.sampled_pages.append(sample)
                    doc_char_counts.append(char_count)

                    if known_table_pages and (idx + 1) in known_table_pages:
                        table_page_chars.append(char_count)

                except Exception as exc:  # noqa: BLE001
                    result.errors.append(f"Page {idx + 1} extraction error: {exc}")
                    result.page_errors.append({"pdf_page_index": idx + 1, "error": f"{type(exc).__name__}: {exc}"})
                    result.sampled_pages.append(
                        PageSample(
                            page_number=idx + 1,
                            char_count=0,
                            table_count=0,
                            snippet="",
                            contains_project_table_markers=False,
                            extractable="FAILED",
                        )
                    )

    except Exception as exc:  # noqa: BLE001
        result.opens_ok = False
        result.document_text_extractable = "FAILED"
        result.errors.append(f"pdfplumber open failed: {type(exc).__name__}: {exc}")
        return result

    # Document-level extractability
    if doc_char_counts:
        total_chars = sum(doc_char_counts)
        result.document_text_extractable = "YES" if total_chars > 200 else "NO"
        if total_chars <= 200:
            result.ocr_may_be_required = True
            result.notes.append(
                f"Very low total chars across sampled pages ({total_chars}). "
                "Possible scanned/image PDF. Verify before proceeding."
            )
    else:
        result.document_text_extractable = "FAILED"

    # Table-level extractability
    if known_table_pages:
        if table_page_chars:
            result.table_text_extractable = (
                "YES" if any(c > 50 for c in table_page_chars) else "NO"
            )
            table_samples = [
                sample for sample in result.sampled_pages
                if sample.page_number in known_table_pages
            ]
            if any(sample.extractable == "FAILED" for sample in table_samples):
                result.table_page_text_status = "FAILED"
                result.table_text_extractable = "FAILED"
            elif any(sample.table_count > 0 and sample.contains_project_table_markers for sample in table_samples):
                result.table_page_text_status = "STRUCTURED_TEXT"
            elif any(sample.char_count > 50 and sample.contains_project_table_markers for sample in table_samples):
                result.table_page_text_status = "TEXT_ONLY"
            else:
                result.table_page_text_status = "NO_TEXT"
            if result.table_text_extractable == "NO":
                result.ocr_may_be_required = True
                result.notes.append(
                    "Target table pages yielded zero/minimal chars — "
                    "table may require OCR."
                )
        else:
            result.table_text_extractable = "FAILED"
            result.table_page_text_status = "FAILED"
    else:
        result.table_text_extractable = "NOT_CHECKED"
        result.notes.append(
            "known_table_pages not provided — table-level extractability not checked."
        )

    return result
