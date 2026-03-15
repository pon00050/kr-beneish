"""test_components.py — Unit tests for each Beneish component formula."""

from __future__ import annotations

import numpy as np
import pytest
import pandas as pd

from kr_beneish._components import compute_components


class TestDSRI:
    def test_dsri_value(self, two_year_df):
        """DSRI = (rec_t/rev_t) / (rec_l/rev_l) = (130/1200)/(100/1000) = 1.0833."""
        result = compute_components(two_year_df)
        row = result[result["year"] == 2020].iloc[0]
        assert abs(row["dsri"] - 1.0833) < 0.001, f"DSRI={row['dsri']:.4f}"

    def test_dsri_first_year_nan(self, two_year_df):
        """First year has no lag — DSRI must be NaN."""
        result = compute_components(two_year_df)
        row = result[result["year"] == 2019].iloc[0]
        assert pd.isna(row["dsri"])

    def test_zero_revenue_yields_nan(self):
        """revenue=0 in denominator must produce NaN, not Inf."""
        df = pd.DataFrame([
            {
                "corp_code": "T", "year": 2019, "fs_type": "CFS",
                "expense_method": "function",
                "receivables": 100, "revenue": 0, "cogs": 50, "sga": 10,
                "ppe": 200, "depreciation": 20, "total_assets": 500,
                "lt_debt": 50, "net_income": None, "cfo": None,
            },
            {
                "corp_code": "T", "year": 2020, "fs_type": "CFS",
                "expense_method": "function",
                "receivables": 120, "revenue": 1000, "cogs": 600, "sga": 80,
                "ppe": 210, "depreciation": 22, "total_assets": 550,
                "lt_debt": 60, "net_income": 30, "cfo": 20,
            },
        ])
        result = compute_components(df)
        row = result[result["year"] == 2020].iloc[0]
        assert pd.isna(row["dsri"]), "DSRI should be NaN when prior-year revenue=0"
        assert not np.isinf(row["dsri"]), "DSRI must not be Inf"


class TestGMI:
    def test_gmi_value(self, two_year_df):
        """GMI = gross_margin_l / gross_margin_t = 0.40/0.4167 = 0.9600."""
        result = compute_components(two_year_df)
        row = result[result["year"] == 2020].iloc[0]
        assert abs(row["gmi"] - 0.9600) < 0.001, f"GMI={row['gmi']:.4f}"

    def test_gmi_nature_is_one(self, two_year_df):
        """Nature-of-expense companies must have GMI=1.0."""
        df = two_year_df.copy()
        df["expense_method"] = "nature"
        result = compute_components(df)
        row = result[result["year"] == 2020].iloc[0]
        assert row["gmi"] == 1.0, f"nature method GMI={row['gmi']}"


class TestAQI:
    def test_aqi_value(self, two_year_df):
        """AQI = (soft_t/ta_t) / (soft_l/ta_l).
        soft_t=1280, ta_t=1700, soft_l=1100, ta_l=1500 → 1.0267."""
        result = compute_components(two_year_df)
        row = result[result["year"] == 2020].iloc[0]
        assert abs(row["aqi"] - 1.0267) < 0.001, f"AQI={row['aqi']:.4f}"


class TestSGI:
    def test_sgi_value(self, two_year_df):
        """SGI = revenue_t / revenue_l = 1200/1000 = 1.20."""
        result = compute_components(two_year_df)
        row = result[result["year"] == 2020].iloc[0]
        assert abs(row["sgi"] - 1.2000) < 0.001, f"SGI={row['sgi']:.4f}"

    def test_zero_prior_revenue_yields_nan(self):
        """SGI with prior-year revenue=0 must be NaN, not Inf."""
        df = pd.DataFrame([
            {
                "corp_code": "T", "year": 2019, "fs_type": "CFS",
                "expense_method": "function",
                "receivables": 10, "revenue": 0, "cogs": 0, "sga": 0,
                "ppe": 100, "depreciation": 10, "total_assets": 200,
                "lt_debt": 20, "net_income": None, "cfo": None,
            },
            {
                "corp_code": "T", "year": 2020, "fs_type": "CFS",
                "expense_method": "function",
                "receivables": 20, "revenue": 500, "cogs": 300, "sga": 50,
                "ppe": 110, "depreciation": 11, "total_assets": 250,
                "lt_debt": 25, "net_income": 20, "cfo": 15,
            },
        ])
        result = compute_components(df)
        row = result[result["year"] == 2020].iloc[0]
        assert pd.isna(row["sgi"]), "SGI should be NaN when prior-year revenue=0"


class TestDEPI:
    def test_depi_value(self, two_year_df):
        """DEPI = (depr_l/(ppe_l+depr_l)) / (depr_t/(ppe_t+depr_t))
        = (50/450)/(55/475) = 0.11111/0.11579 = 0.9596."""
        result = compute_components(two_year_df)
        row = result[result["year"] == 2020].iloc[0]
        assert abs(row["depi"] - 0.9596) < 0.001, f"DEPI={row['depi']:.4f}"


class TestSGAI:
    def test_sgai_value(self, two_year_df):
        """SGAI = (sga_t/rev_t) / (sga_l/rev_l) = (110/1200)/(80/1000) = 1.1458."""
        result = compute_components(two_year_df)
        row = result[result["year"] == 2020].iloc[0]
        assert abs(row["sgai"] - 1.1458) < 0.001, f"SGAI={row['sgai']:.4f}"

    def test_sgai_nature_is_one(self, two_year_df):
        """Nature-of-expense companies must have SGAI=1.0."""
        df = two_year_df.copy()
        df["expense_method"] = "nature"
        result = compute_components(df)
        row = result[result["year"] == 2020].iloc[0]
        assert row["sgai"] == 1.0, f"nature method SGAI={row['sgai']}"


class TestLVGI:
    def test_lvgi_value(self, two_year_df):
        """LVGI = (lt_debt_t/ta_t) / (lt_debt_l/ta_l)
        = (260/1700)/(200/1500) = 0.1529/0.1333 = 1.1471."""
        result = compute_components(two_year_df)
        row = result[result["year"] == 2020].iloc[0]
        assert abs(row["lvgi"] - 1.1471) < 0.001, f"LVGI={row['lvgi']:.4f}"


class TestTATA:
    def test_tata_value(self, two_year_df):
        """TATA = (net_income - cfo) / total_assets = (100-80)/1700 = 0.01176."""
        result = compute_components(two_year_df)
        row = result[result["year"] == 2020].iloc[0]
        assert abs(row["tata"] - 0.01176) < 0.0001, f"TATA={row['tata']:.5f}"

    def test_tata_nan_when_net_income_null(self, two_year_df):
        """TATA is NaN when net_income is null."""
        df = two_year_df.copy()
        df.loc[df["year"] == 2020, "net_income"] = None
        result = compute_components(df)
        row = result[result["year"] == 2020].iloc[0]
        assert pd.isna(row["tata"])


class TestInfReplacement:
    def test_no_inf_in_components(self, two_year_df):
        """No component should contain Inf after computation."""
        result = compute_components(two_year_df)
        for comp in ["dsri", "gmi", "aqi", "sgi", "depi", "sgai", "lvgi", "tata"]:
            vals = result[comp].dropna()
            assert not np.isinf(vals).any(), f"{comp} contains Inf"
