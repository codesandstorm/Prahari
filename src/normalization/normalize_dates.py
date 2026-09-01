"""
PRAHARI — src/normalization/normalize_dates.py

Parse and normalise date fields from raw extraction output.

Design principles:
  - Attempt all configured date formats in order.
  - On parse failure: preserve original string in a '_raw' column and
    set the parsed column to NaT. Log a warning.
  - Never silently discard a value.
  - Return both the raw string and parsed datetime for auditability.

Usage:
    from src.normalization.normalize_dates import parse_date_column
    df['date_of_approval'], df['date_of_approval_raw'] = (
        parse_date_column(df['date_of_approval'], config)
    )
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)


def parse_date_series(series: pd.Series, config: dict[str, Any]) -> tuple[pd.Series, pd.Series]:
    """Parse a Series of raw date strings into datetime and preserve raw values.

    Tries configured formats first, then falls back to dateutil's flexible parser.
    Failures result in NaT with a warning.

    Args:
        series: Raw date string Series.
        config: Parsed config.yaml dict with normalization.date_formats.

    Returns:
        Tuple of (parsed_series, raw_string_series).
        parsed_series — pd.Series[datetime64], NaT where parsing failed.
        raw_string_series — pd.Series[str], original values preserved.
    """
    formats: list[str] = config.get("normalization", {}).get("date_formats", [])
    missing_markers: list[str] = config.get("normalization", {}).get("missing_markers", [])

    raw_series = series.copy().astype(str)
    parsed: list[pd.Timestamp | None] = []

    for value in series:
        value_str = str(value).strip() if pd.notna(value) else ""

        # Treat as missing
        if value_str in missing_markers or value_str == "" or value_str == "nan":
            parsed.append(pd.NaT)
            continue

        # Try configured formats
        parsed_dt = None
        for fmt in formats:
            try:
                parsed_dt = pd.to_datetime(value_str, format=fmt)
                break
            except (ValueError, TypeError):
                continue

        # Fallback: dateutil flexible parser
        if parsed_dt is None:
            try:
                parsed_dt = pd.Timestamp(dateutil_parser.parse(value_str, dayfirst=True))
            except (ValueError, OverflowError):
                logger.warning("Could not parse date value: %r — set to NaT", value_str)
                parsed_dt = pd.NaT

        parsed.append(parsed_dt)

    return pd.Series(parsed, index=series.index, name=series.name), raw_series


def parse_date_column(df: pd.DataFrame, column: str,
                      config: dict[str, Any]) -> pd.DataFrame:
    """Parse a date column in-place, adding a '_raw' backup column.

    The original column is replaced with parsed datetime.
    A new '<column>_raw' column is added with the original string values.

    Args:
        df: DataFrame containing the column.
        column: Column name to parse.
        config: Parsed config.yaml dict.

    Returns:
        Modified DataFrame (new copy; original not mutated).
    """
    if column not in df.columns:
        logger.warning("Column '%s' not found in DataFrame; skipping date parse.", column)
        return df

    df = df.copy()
    parsed, raw = parse_date_series(df[column], config)
    df[f"{column}_raw"] = raw
    df[column] = parsed
    return df
