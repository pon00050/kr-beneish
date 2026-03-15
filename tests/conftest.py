"""conftest.py — Shared pytest fixtures for kr_beneish tests."""

from __future__ import annotations

import pytest
import pandas as pd


@pytest.fixture
def two_year_df() -> pd.DataFrame:
    """Minimal two-year (2019–2020) synthetic dataset for one company.

    Values chosen so all 8 Beneish ratios are hand-calculable:
        revenue:       T-1=1000, T=1200   → SGI = 1.20
        receivables:   T-1=100,  T=130    → DSRI = (130/1200)/(100/1000) = 1.0833
        cogs:          T-1=600,  T=700    → gross margin T-1=0.40, T=0.4167
                                            GMI = 0.40/0.4167 = 0.9600
        ppe:           T-1=400,  T=420
        depreciation:  T-1=50,   T=55
                                            DEPI = (50/450)/(55/475) = 0.9596
        total_assets:  T-1=1500, T=1700
        soft_assets:   T-1=1100, T=1280  → AQI = (1280/1700)/(1100/1500) = 1.0267
        sga:           T-1=80,   T=110   → SGAI = (110/1200)/(80/1000) = 1.1458
        lt_debt:       T-1=200,  T=260   → LVGI = (260/1700)/(200/1500) = 1.1471
        net_income:    T=100
        cfo:           T=80              → TATA = (100-80)/1700 = 0.01176
    """
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


@pytest.fixture
def minimal_df(two_year_df) -> pd.DataFrame:
    """Alias for two_year_df — used by integration tests."""
    return two_year_df
