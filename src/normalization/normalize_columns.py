"""
PRAHARI — src/normalization/normalize_columns.py

Rename raw extracted column headers to canonical PRAHARI field names.

The mapping is entirely config-driven (config.yaml → column_aliases section).

Design principles:
  - Unknown columns are PRESERVED with a warning, not silently dropped.
  - Original column names are recorded alongside canonical names.
  - A log entry is emitted for every column that cannot be matched.

Usage:
    from src.normalization.normalize_columns import rename_columns
    df_normalized = rename_columns(df_raw, config)
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def rename_columns(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Rename raw PDF extraction columns to canonical PRAHARI names.

    Columns not present in the alias map are preserved unchanged and a
    WARNING is logged. They are NOT dropped.

    Args:
        df: DataFrame with raw column headers from extraction.
        config: Parsed config.yaml dict containing 'column_aliases'.

    Returns:
        New DataFrame with renamed columns. Original df is NOT mutated.
    """
    aliases: dict[str, str] = config.get("column_aliases", {})

    rename_map: dict[str, str] = {}
    unmatched: list[str] = []

    for col in df.columns:
        # Strip whitespace from header before matching
        stripped = col.strip()
        if stripped in aliases:
            rename_map[col] = aliases[stripped]
        else:
            unmatched.append(col)

    if unmatched:
        logger.warning(
            "The following columns have no alias mapping and will be preserved as-is: %s",
            unmatched,
        )

    return df.rename(columns=rename_map)


def get_unmapped_columns(df: pd.DataFrame, config: dict[str, Any]) -> list[str]:
    """Return a list of column names that have no alias mapping.

    Useful for checking whether a new schema era introduces unexpected columns.

    Args:
        df: DataFrame to check.
        config: Parsed config.yaml dict.

    Returns:
        List of unrecognised column header strings.
    """
    aliases = config.get("column_aliases", {})
    return [col for col in df.columns if col.strip() not in aliases]
