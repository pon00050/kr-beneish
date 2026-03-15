"""test_score.py — Unit tests for _score.compute_mscore."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kr_beneish._components import compute_components
from kr_beneish._score import compute_mscore, BENEISH_THRESHOLD


def _scored(two_year_df):
    """Run components then compute_mscore on the two-year fixture."""
    df_comp = compute_components(two_year_df)
    return compute_mscore(df_comp)


class TestMScoreFormula:
    def test_known_m_score(self, two_year_df):
        """Hand-calculated M-Score for standard two-year fixture = -2.26 ±0.02."""
        result = _scored(two_year_df)
        row = result[result["year"] == 2020].iloc[0]
        expected = -2.26
        assert abs(row["m_score"] - expected) < 0.02, (
            f"M-Score={row['m_score']:.4f}, expected ~{expected}"
        )

    def test_first_year_is_nan(self, two_year_df):
        """Year T-1 (no lag) must have m_score=NaN."""
        result = _scored(two_year_df)
        row = result[result["year"] == 2019].iloc[0]
        assert pd.isna(row["m_score"])

    def test_flag_true_when_above_threshold(self, two_year_df):
        """flag=True when m_score > threshold."""
        result = compute_mscore(compute_components(two_year_df), threshold=-3.0)
        row = result[result["year"] == 2020].iloc[0]
        assert row["flag"] is True or row["flag"] == True

    def test_flag_false_when_below_threshold(self, two_year_df):
        """flag=False when m_score ≤ threshold."""
        result = compute_mscore(compute_components(two_year_df), threshold=0.0)
        row = result[result["year"] == 2020].iloc[0]
        assert row["flag"] is False or row["flag"] == False

    def test_flag_false_when_m_score_nan(self, two_year_df):
        """flag=False when m_score is NaN (first year)."""
        result = _scored(two_year_df)
        row = result[result["year"] == 2019].iloc[0]
        assert (row["flag"] is False) or (row["flag"] == False)


class TestNullTolerance:
    def test_two_null_core_still_computed(self, two_year_df):
        """≤2 null core components: m_score is still computed (not NaN)."""
        df = two_year_df.copy()
        df.loc[df["year"] == 2020, "receivables"] = None   # kills dsri
        df.loc[df["year"] == 2020, "net_income"] = None    # kills tata
        result = _scored(df)
        row = result[result["year"] == 2020].iloc[0]
        assert not pd.isna(row["m_score"]), (
            f"Expected non-null m_score with 2 null core components, got {row['m_score']}"
        )

    def test_three_null_core_yields_nan(self, two_year_df):
        """More than 2 null core components: m_score must be NaN."""
        df = two_year_df.copy()
        df.loc[df["year"] == 2020, "receivables"] = None   # kills dsri
        df.loc[df["year"] == 2020, "net_income"] = None    # kills tata
        df.loc[df["year"] == 2020, "depreciation"] = None  # kills depi
        df.loc[df["year"] == 2019, "depreciation"] = None  # kills depi_l too
        result = _scored(df)
        row = result[result["year"] == 2020].iloc[0]
        assert pd.isna(row["m_score"]), (
            f"Expected null m_score with 3 null core components, got {row['m_score']}"
        )

    def test_null_propagation_flag_stays_false(self, two_year_df):
        """flag is False even when m_score is NaN from too many null components."""
        df = two_year_df.copy()
        df.loc[df["year"] == 2020, "receivables"] = None
        df.loc[df["year"] == 2020, "net_income"] = None
        df.loc[df["year"] == 2020, "depreciation"] = None
        df.loc[df["year"] == 2019, "depreciation"] = None
        result = _scored(df)
        row = result[result["year"] == 2020].iloc[0]
        assert (row["flag"] is False) or (row["flag"] == False)


class TestThreshold:
    def test_default_threshold_is_beneish(self):
        """Default threshold constant matches Beneish (1999) value."""
        assert BENEISH_THRESHOLD == -1.78

    def test_custom_threshold_applied(self, two_year_df):
        """Custom threshold=-2.45 produces fewer flags than default=-1.78."""
        df_comp = compute_components(two_year_df)
        # M-Score ~ -2.26; above -1.78 → flagged; below -2.26 → not flagged at -2.45
        result_default = compute_mscore(df_comp, threshold=-1.78)
        result_strict = compute_mscore(df_comp, threshold=-3.0)
        row_default = result_default[result_default["year"] == 2020].iloc[0]
        row_strict = result_strict[result_strict["year"] == 2020].iloc[0]
        # m_score ~ -2.26 is above -1.78 → not flagged; above -3.0 → flagged
        assert not row_default["flag"]   # -2.26 < -1.78 → not flagged
        assert row_strict["flag"]        # -2.26 > -3.0  → flagged
