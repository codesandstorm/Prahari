"""
PRAHARI — src/validation/validate_rows.py

Row-level integrity checks after extraction.

Checks performed:
  - Required fields (project_name, source_id, pdf_page_index, source_table) are non-null.
  - reporting_month is in YYYY-MM format.
  - pdf_page_index is a positive one-based physical PDF page index.

These are structural checks, NOT domain anomaly checks.
Domain anomaly checks live in anomaly_detection.py.

Usage:
    from src.validation.validate_rows import validate_extraction
    issues_df = validate_extraction(df, reporting_month="2026-07")
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_YYYY_MM_RE = re.compile(r"^\d{4}-\d{2}$")


def validate_extraction(
    df: pd.DataFrame,
    reporting_month: str,
    required_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Validate structural integrity of an extracted DataFrame.

    Args:
        df: Extracted (possibly normalized) DataFrame.
        reporting_month: Expected reporting month in YYYY-MM format.
        required_cols: List of column names that must be non-null.
                       Defaults to ['project_name', 'source_id', 'pdf_page_index', 'source_table'].

    Returns:
        DataFrame of validation issues. Empty DataFrame if all checks pass.
        Columns: row_index, check_name, description
    """
    if required_cols is None:
        required_cols = ["project_name", "source_id", "pdf_page_index", "source_table"]

    issues: list[dict] = []

    # --- Check reporting_month format ---
    if not _YYYY_MM_RE.match(str(reporting_month)):
        issues.append({
            "row_index": None,
            "check_name": "REPORTING_MONTH_FORMAT",
            "description": f"reporting_month '{reporting_month}' is not in YYYY-MM format.",
        })

    # --- Required columns existence ---
    for col in required_cols:
        if col not in df.columns:
            issues.append({
                "row_index": None,
                "check_name": "MISSING_COLUMN",
                "description": f"Required column '{col}' is absent from the DataFrame.",
            })

    # --- Per-row required field null checks ---
    for col in required_cols:
        if col not in df.columns:
            continue
        null_mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        for idx in df[null_mask].index:
            issues.append({
                "row_index": idx,
                "check_name": f"NULL_REQUIRED_FIELD",
                "description": f"Required field '{col}' is null/empty at row {idx}.",
            })

    # --- pdf_page_index is a positive integer ---
    if "pdf_page_index" in df.columns:
        for idx, val in df["pdf_page_index"].items():
            try:
                page = int(val)
                if page < 1:
                    raise ValueError
            except (ValueError, TypeError):
                issues.append({
                    "row_index": idx,
                    "check_name": "INVALID_PDF_PAGE_INDEX",
                    "description": f"pdf_page_index '{val}' is not a positive integer at row {idx}.",
                })

    if issues:
        logger.warning("validate_extraction: %d issues found.", len(issues))
    else:
        logger.info("validate_extraction: all checks passed (%d rows).", len(df))

    return pd.DataFrame(issues) if issues else pd.DataFrame(
        columns=["row_index", "check_name", "description"]
    )
