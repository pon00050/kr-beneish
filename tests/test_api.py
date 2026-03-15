"""test_api.py — Integration tests for compute_mscores() public API."""

from __future__ import annotations

import pandas as pd
import pytest

from kr_beneish import compute_mscores, REQUIRED_COLUMNS, BENEISH_THRESHOLD

_EXPECTED_OUTPUT_COLUMNS = {
    "corp_code", "year",
    "dsri", "gmi", "aqi", "sgi", "depi", "sgai", "lvgi", "tata",
    "m_score", "flag",
}


class TestOutputSchema:
    def test_output_has_correct_columns(self, minimal_df):
        """compute_mscores returns exactly the 12 documented output columns."""
        result = compute_mscores(minimal_df)
        assert set(result.columns) == _EXPECTED_OUTPUT_COLUMNS

    def test_no_lag_columns_in_output(self, minimal_df):
        """No internal lag columns (_l suffix) leak into the output."""
        result = compute_mscores(minimal_df)
        leaked = [c for c in result.columns if c.endswith("_l")]
        assert not leaked, f"Lag columns leaked: {leaked}"

    def test_no_intermediate_columns_in_output(self, minimal_df):
        """No intermediate computed columns (gross_profit, soft_assets, etc.) leak."""
        result = compute_mscores(minimal_df)
        internal = {"gross_profit", "gross_margin", "soft_assets"}
        leaked = internal & set(result.columns)
        assert not leaked, f"Internal columns leaked: {leaked}"


class TestOutputRows:
    def test_first_year_excluded(self, minimal_df):
        """Rows without T-1 data (first year per company) are excluded."""
        result = compute_mscores(minimal_df)
        assert 2019 not in result["year"].values, "First year should be excluded from output"

    def test_scoreable_rows_included(self, minimal_df):
        """Year T (with T-1 available) is present in output."""
        result = compute_mscores(minimal_df)
        assert 2020 in result["year"].values

    def test_multi_company_multi_year(self):
        """Multiple companies each contribute one row per scoreable year."""
        rows = []
        for i in range(3):
            for yr in [2019, 2020, 2021]:
                rows.append({
                    "corp_code": f"C{i:02d}",
                    "year": yr,
                    "fs_type": "CFS",
                    "expense_method": "function",
                    "receivables": 100 + i,
                    "revenue": 1000 + i * 10,
                    "cogs": 600,
                    "sga": 80,
                    "ppe": 400,
                    "depreciation": 50,
                    "total_assets": 1500,
                    "lt_debt": 200,
                    "net_income": 100,
                    "cfo": 80,
                })
        df = pd.DataFrame(rows)
        result = compute_mscores(df)
        # Each company contributes 2 scoreable years (2020, 2021); first year excluded
        assert len(result) == 6
        assert result["corp_code"].nunique() == 3


class TestThresholdParam:
    def test_custom_threshold_changes_flags(self, minimal_df):
        """threshold=-2.45 produces different flag counts than default."""
        default = compute_mscores(minimal_df)
        strict = compute_mscores(minimal_df, threshold=-2.45)
        # M-Score ~ -2.26: above -1.78 → not flagged; above -2.45 → flagged
        assert not default["flag"].any()   # -2.26 is below -1.78
        assert strict["flag"].any()        # -2.26 is above -2.45

    def test_default_threshold_constant_used(self, minimal_df):
        """compute_mscores() with no threshold uses BENEISH_THRESHOLD."""
        result_default = compute_mscores(minimal_df)
        result_explicit = compute_mscores(minimal_df, threshold=BENEISH_THRESHOLD)
        pd.testing.assert_frame_equal(result_default, result_explicit)


class TestInputValidation:
    def test_raises_on_missing_column(self, minimal_df):
        """Missing required column raises ValueError."""
        df = minimal_df.drop(columns=["revenue"])
        with pytest.raises(ValueError, match="revenue"):
            compute_mscores(df)

    def test_raises_on_empty_df(self, minimal_df):
        """Empty DataFrame raises ValueError."""
        df = minimal_df.iloc[0:0]
        with pytest.raises(ValueError, match="empty"):
            compute_mscores(df)
