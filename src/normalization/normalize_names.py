"""
PRAHARI — src/normalization/normalize_names.py

Normalize text fields: project names, agency names, state names.

Operations performed:
  - Strip leading/trailing whitespace
  - Collapse internal multiple spaces to single space
  - Strip trailing punctuation (periods, commas)
  - Normalize Unicode to NFC form

Operations NOT performed:
  - Fuzzy deduplication (this is an identity task, not normalization)
  - Acronym expansion
  - Case change (preserve original case)

Usage:
    from src.normalization.normalize_names import normalize_text_column
    df = normalize_text_column(df, 'project_name')
"""

from __future__ import annotations

import logging
import re
import unicodedata

import pandas as pd

logger = logging.getLogger(__name__)

_MULTI_SPACE_RE = re.compile(r" {2,}")
_TRAILING_PUNCT_RE = re.compile(r"[.,;:]+$")


def normalize_text_value(value: str) -> str:
    """Normalize a single text string.

    Args:
        value: Raw string.

    Returns:
        Cleaned string.
    """
    if not isinstance(value, str):
        return value

    # NFC Unicode normalization
    value = unicodedata.normalize("NFC", value)
    # Strip whitespace
    value = value.strip()
    # Collapse internal spaces
    value = _MULTI_SPACE_RE.sub(" ", value)
    # Strip trailing punctuation
    value = _TRAILING_PUNCT_RE.sub("", value).strip()

    return value


def normalize_text_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Normalize a text column in a DataFrame.

    The original column is overwritten with the normalized value.
    A '_raw' backup column is added ONLY if meaningful changes occurred.

    Args:
        df: Input DataFrame.
        column: Column name to normalize.

    Returns:
        New DataFrame with normalized column.
    """
    if column not in df.columns:
        logger.warning("Column '%s' not found; skipping text normalization.", column)
        return df

    df = df.copy()
    raw = df[column].copy()
    normalized = df[column].apply(
        lambda v: normalize_text_value(v) if pd.notna(v) else v
    )

    # Record raw values if any changes occurred
    changed_mask = raw.astype(str) != normalized.astype(str)
    if changed_mask.any():
        df[f"{column}_raw"] = raw
        logger.info(
            "Column '%s': %d values changed during text normalization.",
            column, changed_mask.sum()
        )

    df[column] = normalized
    return df
