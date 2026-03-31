"""_components.py — Compute the 8 Beneish M-Score components."""

from __future__ import annotations

import numpy as np
import pandas as pd

_LAG_COLS = [
    "receivables",
    "revenue",
    "cogs",
    "sga",
    "ppe",
    "depreciation",
    "total_assets",
    "lt_debt",
    "fs_type",
    "expense_method",
]

_NUMERIC_COLS = [
    "receivables",
    "revenue",
    "cogs",
    "sga",
    "ppe",
    "depreciation",
    "total_assets",
    "lt_debt",
    "net_income",
    "cfo",
]

_COMPONENTS = ["dsri", "gmi", "aqi", "sgi", "depi", "sgai", "lvgi", "tata"]


def compute_components(df: pd.DataFrame) -> pd.DataFrame:
    """Compute 8 Beneish components for each company-year.

    Adds lag columns (T-1) and 8 component columns to a copy of df.
    Returns the enriched DataFrame — does NOT filter rows.

    Korean IFRS adjustments:
    - expense_method='nature': GMI=1.0 and SGAI=1.0 (structurally undefined
      without a COGS/SGA line).
    - Zero denominators: replaced with NaN before ratio computation (not 0).
    - Inf from small denominators: replaced with NaN after computation.
    """
    df = df.copy()

    for col in _NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["corp_code", "year"]).reset_index(drop=True)

    for col in _LAG_COLS:
        df[f"{col}_l"] = df.groupby("corp_code")[col].shift(1)

    # Guard against non-consecutive years: if the prior row is not year-1,
    # the lag is invalid (e.g. company missing 2020, so 2021 would pair with
    # 2019). Set all lag columns to NaN for those rows.
    year_l = df.groupby("corp_code")["year"].shift(1)
    non_consecutive = year_l.notna() & (year_l != df["year"] - 1)
    for col in _LAG_COLS:
        df.loc[non_consecutive, f"{col}_l"] = np.nan

    # Safe denominators (zero → NaN to avoid Inf)
    rev = df["revenue"].replace(0, np.nan)
    rev_l = df["revenue_l"].replace(0, np.nan)
    ta = df["total_assets"].replace(0, np.nan)
    ta_l = df["total_assets_l"].replace(0, np.nan)

    # Derived intermediates
    df["gross_profit"] = df["revenue"] - df["cogs"]
    df["gross_profit_l"] = df["revenue_l"] - df["cogs_l"]
    df["gross_margin"] = df["gross_profit"] / rev
    df["gross_margin_l"] = df["gross_profit_l"] / rev_l
    df["soft_assets"] = df["total_assets"] - df["ppe"]
    df["soft_assets_l"] = df["total_assets_l"] - df["ppe_l"]

    # 1. DSRI — Days Sales in Receivables Index
    df["dsri"] = (df["receivables"] / rev) / (df["receivables_l"] / rev_l)

    # 2. GMI — Gross Margin Index (1.0 for nature-method companies)
    gmi_raw = df["gross_margin_l"] / df["gross_margin"].replace(0, np.nan)
    df["gmi"] = np.where(df["expense_method"] == "nature", 1.0, gmi_raw)

    # 3. AQI — Asset Quality Index
    df["aqi"] = (df["soft_assets"] / ta) / (df["soft_assets_l"] / ta_l)

    # 4. SGI — Sales Growth Index
    df["sgi"] = df["revenue"] / rev_l

    # 5. DEPI — Depreciation Index
    ppe_depr = (df["ppe"] + df["depreciation"]).replace(0, np.nan)
    ppe_depr_l = (df["ppe_l"] + df["depreciation_l"]).replace(0, np.nan)
    df["depi"] = (df["depreciation_l"] / ppe_depr_l) / (df["depreciation"] / ppe_depr)

    # 6. SGAI — SG&A Index (1.0 for nature-method companies)
    sgai_raw = (df["sga"] / rev) / (df["sga_l"] / rev_l)
    df["sgai"] = np.where(df["expense_method"] == "nature", 1.0, sgai_raw)

    # 7. LVGI — Leverage Index (null if lt_debt unavailable)
    df["lvgi"] = (df["lt_debt"] / ta) / (df["lt_debt_l"] / ta_l)

    # 8. TATA — Total Accruals to Total Assets
    df["tata"] = (df["net_income"] - df["cfo"]) / ta

    # Replace Inf with NaN (zero-denominator artefacts)
    for comp in _COMPONENTS:
        df[comp] = df[comp].replace([np.inf, -np.inf], np.nan)

    return df
