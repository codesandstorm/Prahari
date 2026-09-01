"""
PRAHARI — src/validation/missingness.py

Quantify missing values per field per source report.

For each column in an extracted DataFrame, report:
  - total_rows
  - non_null_count
  - null_count
  - null_pct
  - source_file

Output is written to data/validation/missingness_report.csv.

Usage:
    from src.validation.missingness import compute_missingness
    report_df = compute_missingness(df, source_file="mospy_flash_2026_07.pdf")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.safe_io import append_dataframe_csv

logger = logging.getLogger(__name__)


def compute_missingness(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """Compute per-column missingness statistics.

    A value is counted as missing if it is:
      - pd.NA / pd.NaT / None
      - Empty string ""
      - The string "nan"

    Args:
        df: Extracted / normalized DataFrame.
        source_file: Source PDF filename (for the report).

    Returns:
        DataFrame with columns:
            field_name, source_file, total_rows, non_null_count, null_count, null_pct, notes
    """
    records = []
    total = len(df)

    for col in df.columns:
        series = df[col]

        # Treat empty strings and literal "nan" as missing
        is_missing = series.isna() | (series.astype(str).str.strip().isin(["", "nan"]))
        null_count = int(is_missing.sum())
        non_null_count = total - null_count
        null_pct = round(100.0 * null_count / total, 2) if total > 0 else 0.0

        records.append({
            "field_name": col,
            "source_file": source_file,
            "total_rows": total,
            "non_null_count": non_null_count,
            "null_count": null_count,
            "null_pct": null_pct,
            "notes": "",
        })

    return pd.DataFrame(records)


def append_missingness_report(
    new_report: pd.DataFrame,
    output_path: Path,
) -> None:
    """Append a missingness report to the cumulative CSV.

    If the file does not exist, it is created.
    If it exists, new rows are appended (no duplicates removed —
    caller should deduplicate by source_file if re-running).

    Args:
        new_report: DataFrame returned by compute_missingness.
        output_path: Path to missingness_report.csv.
    """
    output_path = append_dataframe_csv(new_report, output_path)
    logger.info("Missingness report written/appended: %s", output_path)
