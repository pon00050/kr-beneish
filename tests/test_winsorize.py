"""test_winsorize.py — Unit tests for _winsorize.winsorize_components."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kr_beneish._winsorize import winsorize_components, _MIN_SAMPLES


def _make_winsorize_df(n: int = 30, year: int = 2020) -> pd.DataFrame:
    """Create a synthetic DataFrame with n rows for one year."""
    rng = np.random.default_rng(42)
    vals = rng.normal(1.0, 0.5, n).tolist()
    # Insert extreme outliers at first and last positions
    vals[0] = 1000.0
    vals[-1] = -1000.0
    return pd.DataFrame({
        "corp_code": [f"C{i:04d}" for i in range(n)],
        "year": year,
        "dsri": vals,
        "gmi": [1.0] * n,
        "aqi": [1.0] * n,
        "sgi": [1.0] * n,
        "depi": [1.0] * n,
        "sgai": [1.0] * n,
        "lvgi": [1.0] * n,
        "tata": [0.0] * n,
    })


class TestWinsorizeComponents:
    def test_clips_upper_extreme(self):
        """Values above 99th percentile are clipped to the 99th percentile."""
        df = _make_winsorize_df(n=30)
        result = winsorize_components(df)
        hi = df["dsri"].dropna().quantile(0.99)
        assert result["dsri"].max() <= hi + 1e-9, "Upper extreme not clipped"

    def test_clips_lower_extreme(self):
        """Values below 1st percentile are clipped to the 1st percentile."""
        df = _make_winsorize_df(n=30)
        result = winsorize_components(df)
        lo = df["dsri"].dropna().quantile(0.01)
        assert result["dsri"].min() >= lo - 1e-9, "Lower extreme not clipped"

    def test_skips_year_with_few_samples(self):
        """Years with n < MIN_SAMPLES non-null values are NOT winsorized."""
        n = _MIN_SAMPLES - 1  # one below threshold
        df = _make_winsorize_df(n=n)
        df.loc[0, "dsri"] = 9999.0  # extreme value
        result = winsorize_components(df)
        # Should be unchanged because n < _MIN_SAMPLES
        assert result.loc[0, "dsri"] == 9999.0, "Extremes clipped despite n<MIN_SAMPLES"

    def test_per_year_isolation(self):
        """Winsorization thresholds in year A do not affect year B."""
        df_a = _make_winsorize_df(n=30, year=2019)
        df_b = _make_winsorize_df(n=30, year=2020)
        # Give year B extreme that's within year A's distribution
        df_b.iloc[0, df_b.columns.get_loc("dsri")] = 5.0
        combined = pd.concat([df_a, df_b], ignore_index=True)
        result = winsorize_components(combined)

        # Year A clip threshold computed from year A data only
        hi_a = df_a["dsri"].dropna().quantile(0.99)
        result_a = result[result["year"] == 2019]["dsri"]
        assert result_a.max() <= hi_a + 1e-9

        # Year B is independent
        hi_b = df_b["dsri"].dropna().quantile(0.99)
        result_b = result[result["year"] == 2020]["dsri"]
        assert result_b.max() <= hi_b + 1e-9

    def test_missing_component_column_skipped(self):
        """If a component column is absent the function does not raise."""
        df = _make_winsorize_df(n=30)
        df = df.drop(columns=["lvgi"])
        winsorize_components(df)  # should not raise

    def test_non_clipped_values_unchanged(self):
        """Values within the 1st–99th range are not modified."""
        df = _make_winsorize_df(n=30)
        result = winsorize_components(df)
        lo = df["gmi"].dropna().quantile(0.01)
        hi = df["gmi"].dropna().quantile(0.99)
        # gmi is all 1.0 so no clipping should occur; values unchanged
        assert (result["gmi"] == 1.0).all()
