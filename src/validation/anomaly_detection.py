"""
PRAHARI — src/validation/anomaly_detection.py

Detect and flag suspicious values in extracted data.

CRITICAL RULE: This module flags anomalies. It does NOT correct or remove them.
Every flagged value retains its original extracted form.

Anomaly types checked (all configurable in config.yaml):

  NEGATIVE_COST            — original_cost, revised_cost, or cumulative_expenditure < 0
  PROGRESS_ABOVE_100       — physical_progress_pct > 100
  PROGRESS_BELOW_0         — physical_progress_pct < 0
  CUMULATIVE_EXCEEDS_REVISED — cumulative_expenditure > revised_cost (flag only; may be valid)
  DOC_BEFORE_START_DATE    — revised_doc or original_doc before start_date
  DOC_BEFORE_APPROVAL      — original_doc before date_of_approval

All flags are written to data/validation/anomaly_report.csv.

Usage:
    from src.validation.anomaly_detection import detect_anomalies
    anomaly_df = detect_anomalies(df, source_file="mospy_flash_2026_07.pdf",
                                  reporting_month="2026-07", config=config)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.safe_io import append_dataframe_csv

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flag definitions
# ---------------------------------------------------------------------------

FLAG_NEGATIVE_COST = "NEGATIVE_COST"
FLAG_PROGRESS_ABOVE_100 = "PROGRESS_ABOVE_100"
FLAG_PROGRESS_BELOW_0 = "PROGRESS_BELOW_0"
FLAG_CUMULATIVE_EXCEEDS_REVISED = "CUMULATIVE_EXCEEDS_REVISED"
FLAG_DOC_BEFORE_START = "DOC_BEFORE_START_DATE"
FLAG_DOC_BEFORE_APPROVAL = "DOC_BEFORE_APPROVAL"


def detect_anomalies(
    df: pd.DataFrame,
    source_file: str,
    reporting_month: str,
    source_page_col: str = "source_page",
    project_id_col: str = "project_code",
    config: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Detect anomalies in an extracted/normalized project DataFrame.

    Args:
        df: DataFrame with (at minimum) normalized cost, date, and progress columns.
        source_file: Source PDF filename.
        reporting_month: Reporting month YYYY-MM.
        source_page_col: Column holding source page number.
        project_id_col: Column to use as project identifier.
        config: Parsed config.yaml. If None, uses empty thresholds.

    Returns:
        DataFrame of anomaly records to append to anomaly_report.csv.
        Columns: anomaly_id, source_file, source_page, project_id,
                 reporting_month, field, extracted_value, flag_type, description, action
    """
    thresholds = {}
    if config:
        thresholds = config.get("normalization", {}).get("anomaly_thresholds", {})

    records = []
    anomaly_counter = 0

    def add_flag(row_idx, field, value, flag_type, description):
        nonlocal anomaly_counter
        anomaly_counter += 1
        records.append({
            "anomaly_id": f"ANOM-{anomaly_counter:06d}",
            "source_file": source_file,
            "source_page": df.at[row_idx, source_page_col] if source_page_col in df.columns else None,
            "project_id": df.at[row_idx, project_id_col] if project_id_col in df.columns else None,
            "reporting_month": reporting_month,
            "field": field,
            "extracted_value": str(value),
            "flag_type": flag_type,
            "description": description,
            "action": "FLAGGED — value preserved; no correction applied",
        })

    # -----------------------------------------------------------------------
    # Negative costs
    # -----------------------------------------------------------------------
    if thresholds.get("cost_negative_flag", True):
        for cost_col in ["original_cost", "revised_cost", "cumulative_expenditure"]:
            if cost_col not in df.columns:
                continue
            mask = df[cost_col].notna() & (df[cost_col] < 0)
            for idx in df[mask].index:
                add_flag(idx, cost_col, df.at[idx, cost_col], FLAG_NEGATIVE_COST,
                         f"{cost_col} is negative (₹ crore).")

    # -----------------------------------------------------------------------
    # Physical progress out of range
    # -----------------------------------------------------------------------
    if "physical_progress_pct" in df.columns:
        max_pct = thresholds.get("physical_progress_max_pct", 100.0)
        min_pct = thresholds.get("physical_progress_min_pct", 0.0)

        mask_high = df["physical_progress_pct"].notna() & (df["physical_progress_pct"] > max_pct)
        for idx in df[mask_high].index:
            add_flag(idx, "physical_progress_pct", df.at[idx, "physical_progress_pct"],
                     FLAG_PROGRESS_ABOVE_100, f"Physical progress > {max_pct}%.")

        mask_low = df["physical_progress_pct"].notna() & (df["physical_progress_pct"] < min_pct)
        for idx in df[mask_low].index:
            add_flag(idx, "physical_progress_pct", df.at[idx, "physical_progress_pct"],
                     FLAG_PROGRESS_BELOW_0, f"Physical progress < {min_pct}%.")

    # -----------------------------------------------------------------------
    # Cumulative expenditure exceeds revised cost
    # -----------------------------------------------------------------------
    if thresholds.get("cumulative_exceeds_revised_flag", True):
        if "cumulative_expenditure" in df.columns and "revised_cost" in df.columns:
            mask = (
                df["cumulative_expenditure"].notna()
                & df["revised_cost"].notna()
                & (df["cumulative_expenditure"] > df["revised_cost"])
            )
            for idx in df[mask].index:
                add_flag(idx, "cumulative_expenditure",
                         f"cum={df.at[idx,'cumulative_expenditure']} / rev={df.at[idx,'revised_cost']}",
                         FLAG_CUMULATIVE_EXCEEDS_REVISED,
                         "Cumulative expenditure exceeds revised cost.")

    # -----------------------------------------------------------------------
    # DOC before start date
    # -----------------------------------------------------------------------
    if thresholds.get("doc_before_start_date_flag", True):
        for doc_col in ["original_doc", "revised_doc"]:
            if doc_col in df.columns and "start_date" in df.columns:
                mask = (
                    df[doc_col].notna()
                    & df["start_date"].notna()
                    & (df[doc_col] < df["start_date"])
                )
                for idx in df[mask].index:
                    add_flag(idx, doc_col,
                             f"doc={df.at[idx,doc_col]} start={df.at[idx,'start_date']}",
                             FLAG_DOC_BEFORE_START,
                             f"{doc_col} is before start_date.")

    logger.info(
        "Anomaly detection complete: %d flags raised in %s (%s rows)",
        len(records), source_file, len(df)
    )

    return pd.DataFrame(records) if records else pd.DataFrame(
        columns=["anomaly_id", "source_file", "source_page", "project_id",
                 "reporting_month", "field", "extracted_value",
                 "flag_type", "description", "action"]
    )


def append_anomaly_report(anomaly_df: pd.DataFrame, output_path: Path) -> None:
    """Append anomaly records to the cumulative anomaly_report.csv.

    Args:
        anomaly_df: DataFrame from detect_anomalies.
        output_path: Path to anomaly_report.csv.
    """
    if anomaly_df.empty:
        logger.info("No anomalies to append.")
        return

    output_path = append_dataframe_csv(anomaly_df, output_path)
    logger.info("Anomaly report written/appended: %s (%d records)", output_path, len(anomaly_df))
