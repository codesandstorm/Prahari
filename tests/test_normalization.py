"""
PRAHARI — tests/test_normalization.py

Unit tests for normalization modules.

All tests use synthetic DataFrames — no PDFs or real data required.
"""

from __future__ import annotations

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# normalize_columns tests
# ---------------------------------------------------------------------------

class TestRenameColumns:

    def _make_config(self) -> dict:
        return {
            "column_aliases": {
                "Project Code": "project_code",
                "Project Name": "project_name",
                "Agency": "agency",
                "Original Cost": "original_cost",
            }
        }

    def test_known_columns_renamed(self):
        from src.normalization.normalize_columns import rename_columns
        df = pd.DataFrame(columns=["Project Code", "Project Name", "Agency"])
        config = self._make_config()
        result = rename_columns(df, config)
        assert "project_code" in result.columns
        assert "project_name" in result.columns
        assert "agency" in result.columns

    def test_unknown_columns_preserved(self):
        from src.normalization.normalize_columns import rename_columns
        df = pd.DataFrame(columns=["Project Code", "Some New Column"])
        config = self._make_config()
        result = rename_columns(df, config)
        assert "Some New Column" in result.columns  # preserved, not dropped

    def test_original_df_not_mutated(self):
        from src.normalization.normalize_columns import rename_columns
        df = pd.DataFrame(columns=["Project Code"])
        config = self._make_config()
        _ = rename_columns(df, config)
        assert "Project Code" in df.columns  # original unchanged


# ---------------------------------------------------------------------------
# normalize_dates tests
# ---------------------------------------------------------------------------

class TestParseDateSeries:

    def _make_config(self) -> dict:
        return {
            "normalization": {
                "date_formats": ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"],
                "missing_markers": ["-", "N/A", "NA", ""],
            }
        }

    def test_standard_date_parsed(self):
        from src.normalization.normalize_dates import parse_date_series
        series = pd.Series(["15-06-2026"])
        config = self._make_config()
        parsed, raw = parse_date_series(series, config)
        assert pd.notna(parsed.iloc[0])
        assert parsed.iloc[0].day == 15
        assert parsed.iloc[0].month == 6
        assert parsed.iloc[0].year == 2026

    def test_missing_marker_becomes_nat(self):
        from src.normalization.normalize_dates import parse_date_series
        series = pd.Series(["-"])
        config = self._make_config()
        parsed, raw = parse_date_series(series, config)
        assert pd.isna(parsed.iloc[0])

    def test_raw_value_preserved(self):
        from src.normalization.normalize_dates import parse_date_series
        series = pd.Series(["INVALID DATE"])
        config = self._make_config()
        parsed, raw = parse_date_series(series, config)
        assert raw.iloc[0] == "INVALID DATE"
        assert pd.isna(parsed.iloc[0])


# ---------------------------------------------------------------------------
# normalize_costs tests
# ---------------------------------------------------------------------------

class TestParseCostColumn:

    def _make_config(self) -> dict:
        return {
            "normalization": {
                "missing_markers": ["-", "N/A", "", "Nil"],
            }
        }

    def test_numeric_string_parsed(self):
        from src.normalization.normalize_costs import parse_cost_column
        df = pd.DataFrame({"original_cost": ["1234.56"]})
        config = self._make_config()
        result = parse_cost_column(df, "original_cost", config)
        assert abs(result["original_cost"].iloc[0] - 1234.56) < 0.001

    def test_grouping_commas_preserve_decimal_point(self):
        from src.normalization.normalize_costs import parse_cost_column
        df = pd.DataFrame({"original_cost": ["₹ 5,000.25"]})
        result = parse_cost_column(df, "original_cost", self._make_config())
        assert abs(result["original_cost"].iloc[0] - 5000.25) < 0.001

    def test_missing_marker_becomes_nan(self):
        from src.normalization.normalize_costs import parse_cost_column
        df = pd.DataFrame({"original_cost": ["-"]})
        config = self._make_config()
        result = parse_cost_column(df, "original_cost", config)
        assert pd.isna(result["original_cost"].iloc[0])

    def test_raw_value_preserved(self):
        from src.normalization.normalize_costs import parse_cost_column
        df = pd.DataFrame({"original_cost": ["₹ 5,000.00"]})
        config = self._make_config()
        result = parse_cost_column(df, "original_cost", config)
        assert "original_cost_raw" in result.columns
        assert result["original_cost_raw"].iloc[0] == "₹ 5,000.00"

    def test_negative_value_not_silently_corrected(self):
        from src.normalization.normalize_costs import parse_cost_column
        df = pd.DataFrame({"original_cost": ["-100"]})
        config = self._make_config()
        result = parse_cost_column(df, "original_cost", config)
        # Negative value preserved — anomaly flagging happens elsewhere
        assert result["original_cost"].iloc[0] == -100.0


# ---------------------------------------------------------------------------
# normalize_names tests
# ---------------------------------------------------------------------------

class TestNormalizeTextColumn:

    def test_whitespace_stripped(self):
        from src.normalization.normalize_names import normalize_text_value
        assert normalize_text_value("  NHAI  ") == "NHAI"

    def test_internal_spaces_collapsed(self):
        from src.normalization.normalize_names import normalize_text_value
        assert normalize_text_value("NH  Authority") == "NH Authority"

    def test_trailing_period_removed(self):
        from src.normalization.normalize_names import normalize_text_value
        assert normalize_text_value("Project Alpha.") == "Project Alpha"

    def test_case_preserved(self):
        from src.normalization.normalize_names import normalize_text_value
        assert normalize_text_value("MoSPI") == "MoSPI"
