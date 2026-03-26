"""test_known_values.py — Regression tests against hand-calculated reference values.

Ported from the pre-split forensic monolith (now this standalone library).
These tests lock in the exact formula implementation as executable specification
and guard against accidental coefficient or sign changes during refactors.

Reference: Beneish (1999) 8-variable model.
Coefficients: -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
              + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
"""

from __future__ import annotations

import pandas as pd
import pytest

from kr_beneish import compute_mscores


class TestKnownValues:
    """End-to-end regression against hand-calculated M-Score for a synthetic company.

    Two-year dataset (T-1=2019, T=2020):
        revenue:       T-1=1000, T=1200
        receivables:   T-1=100,  T=130    → DSRI = 1.0833
        cogs:          T-1=600,  T=700    → GMI  = 0.9600
        ppe:           T-1=400,  T=420
        depreciation:  T-1=50,   T=55    → DEPI = 0.9596
        total_assets:  T-1=1500, T=1700
        soft_assets:   T-1=1100, T=1280  → AQI  = 1.0267
        sga:           T-1=80,   T=110   → SGAI = 1.1458
        lt_debt:       T-1=200,  T=260   → LVGI = 1.1471
        net_income:    T=100,    cfo=80  → TATA = 0.01176
                                            SGI  = 1.2000

    M-Score = -4.84 + 0.920*1.0833 + 0.528*0.9600 + 0.404*1.0267
                    + 0.892*1.2000 + 0.115*0.9596 - 0.172*1.1458
                    + 4.679*0.01176 - 0.327*1.1471
            ≈ -2.26
    """

    @pytest.fixture
    def reference_df(self) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "corp_code": "TEST001",
                "year": 2019,
                "fs_type": "CFS",
                "expense_method": "function",
                "receivables": 100,
                "revenue": 1000,
                "cogs": 600,
                "sga": 80,
                "ppe": 400,
                "depreciation": 50,
                "total_assets": 1500,
                "lt_debt": 200,
                "net_income": None,
                "cfo": None,
            },
            {
                "corp_code": "TEST001",
                "year": 2020,
                "fs_type": "CFS",
                "expense_method": "function",
                "receivables": 130,
                "revenue": 1200,
                "cogs": 700,
                "sga": 110,
                "ppe": 420,
                "depreciation": 55,
                "total_assets": 1700,
                "lt_debt": 260,
                "net_income": 100,
                "cfo": 80,
            },
        ])

    def test_all_components_match_hand_calculation(self, reference_df):
        """All 8 Beneish components match hand-calculated values."""
        from kr_beneish._components import compute_components

        result = compute_components(reference_df)
        row = result[result["year"] == 2020].iloc[0]

        assert abs(row["dsri"] - 1.0833) < 0.001, f"DSRI={row['dsri']:.4f}"
        assert abs(row["gmi"]  - 0.9600) < 0.001, f"GMI={row['gmi']:.4f}"
        assert abs(row["aqi"]  - 1.0267) < 0.001, f"AQI={row['aqi']:.4f}"
        assert abs(row["sgi"]  - 1.2000) < 0.001, f"SGI={row['sgi']:.4f}"
        assert abs(row["depi"] - 0.9596) < 0.001, f"DEPI={row['depi']:.4f}"
        assert abs(row["sgai"] - 1.1458) < 0.001, f"SGAI={row['sgai']:.4f}"
        assert abs(row["lvgi"] - 1.1471) < 0.001, f"LVGI={row['lvgi']:.4f}"
        assert abs(row["tata"] - 0.01176) < 0.0001, f"TATA={row['tata']:.5f}"

    def test_m_score_matches_hand_calculation(self, reference_df):
        """End-to-end M-Score = -2.26 ±0.02."""
        result = compute_mscores(reference_df)
        row = result[result["year"] == 2020].iloc[0]
        expected = -2.26
        assert abs(row["m_score"] - expected) < 0.02, (
            f"M-Score={row['m_score']:.4f}, expected ~{expected}"
        )

    def test_not_flagged_at_default_threshold(self, reference_df):
        """M-Score ~ -2.26 is below -1.78 threshold → not flagged by default."""
        result = compute_mscores(reference_df)
        row = result[result["year"] == 2020].iloc[0]
        assert not row["flag"], f"Should not be flagged at default threshold (m_score={row['m_score']:.4f})"

    def test_flagged_at_korean_bootstrap_threshold(self, reference_df):
        """M-Score ~ -2.26 is above -2.45 → flagged at Korean bootstrap threshold."""
        result = compute_mscores(reference_df, threshold=-2.45)
        row = result[result["year"] == 2020].iloc[0]
        assert row["flag"], f"Should be flagged at -2.45 threshold (m_score={row['m_score']:.4f})"

    def test_nature_method_sets_gmi_sgai_neutral(self, reference_df):
        """Nature-of-expense companies: GMI=1.0 and SGAI=1.0."""
        df = reference_df.copy()
        df["expense_method"] = "nature"
        result = compute_mscores(df)
        row = result[result["year"] == 2020].iloc[0]
        assert row["gmi"]  == 1.0, f"nature GMI={row['gmi']}"
        assert row["sgai"] == 1.0, f"nature SGAI={row['sgai']}"
