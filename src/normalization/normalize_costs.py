"""
PRAHARI — src/normalization/normalize_costs.py

Parse and normalise cost / expenditure fields from raw extraction output.

All costs are normalised to ₹ crore (Indian units). Raw values are preserved.

Design principles:
  - Strip currency symbols, commas, whitespace.
  - Handle "lakh" and "crore" unit markers (PLAUSIBLE — to verify in actual data).
  - On parse failure: preserve raw value; set numeric column to NaN.
  - Flag negative values and values exceeding plausible project scale as anomalies.
    DO NOT auto-correct them.

Usage:
    from src.normalization.normalize_costs import parse_cost_column
    df = parse_cost_column(df, 'original_cost', config)
"""

from __future__ import annotations

import logging
import re
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Strip currency markers, grouping commas, and whitespace while preserving the
# decimal point. A character class containing "." previously turned 1234.56
# into 123456 and silently inflated costs by 100x.
_CURRENCY_RE = re.compile(r"(?:₹|Rs\.?|,|\s)", re.IGNORECASE)
_LAKH_RE = re.compile(r"lakh", re.IGNORECASE)
_CRORE_RE = re.compile(r"crore|cr\.?", re.IGNORECASE)


def _parse_single_cost(value_str: str) -> float | None:
    """Parse a single cost string to a float in ₹ crore.

    Args:
        value_str: Raw string value from PDF extraction.

    Returns:
        Float value in crore, or None on parse failure.
    """
    s = value_str.strip()

    has_lakh = bool(_LAKH_RE.search(s))
    has_crore = bool(_CRORE_RE.search(s))

    # Remove unit markers and currency symbols
    s = _LAKH_RE.sub("", s)
    s = _CRORE_RE.sub("", s)
    s = _CURRENCY_RE.sub("", s)
    s = s.strip()

    if not s:
        return None

    try:
        numeric = float(s)
    except ValueError:
        return None

    # Unit conversion
    if has_lakh:
        numeric = numeric / 100.0   # 1 lakh = 0.01 crore
    # If crore or no unit detected: assume crore (standard for PAIMANA reports)

    return numeric


def parse_cost_column(df: pd.DataFrame, column: str,
                      config: dict[str, Any]) -> pd.DataFrame:
    """Parse a cost column, adding normalised numeric and raw backup columns.

    Adds:
        <column>_raw   — original string value
        <column>       — float in ₹ crore (NaN on parse failure)

    Anomaly flags are NOT written here; they are handled in
    src/validation/anomaly_detection.py.

    Args:
        df: Input DataFrame.
        column: Column name to parse.
        config: Parsed config.yaml dict.

    Returns:
        New DataFrame with parsed column and raw backup.
    """
    if column not in df.columns:
        logger.warning("Column '%s' not found; skipping cost parse.", column)
        return df

    missing_markers: list[str] = config.get("normalization", {}).get("missing_markers", [])

    df = df.copy()
    raw_vals = df[column].astype(str)
    df[f"{column}_raw"] = raw_vals

    parsed: list[float | None] = []
    for val in raw_vals:
        if val.strip() in missing_markers or val.strip() in ("", "nan"):
            parsed.append(np.nan)
        else:
            result = _parse_single_cost(val)
            if result is None:
                logger.warning("Could not parse cost value: %r — set to NaN", val)
            parsed.append(result)

    df[column] = pd.array(parsed, dtype="Float64")
    return df
