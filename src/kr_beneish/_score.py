"""_score.py — Compute Beneish M-Score from components."""

from __future__ import annotations

import numpy as np
import pandas as pd

BENEISH_THRESHOLD: float = -1.78

_CORE_COMPONENTS = ["dsri", "aqi", "sgi", "depi", "tata"]


def compute_mscore(
    df: pd.DataFrame,
    threshold: float = BENEISH_THRESHOLD,
) -> pd.DataFrame:
    """Compute M-Score from the 8 Beneish components.

    Beneish (1999) 8-variable formula:
        M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
            + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI

    Null handling:
    - m_score = NaN if more than 2 of the 5 core components
      (dsri, aqi, sgi, depi, tata) are null.
    - m_score = NaN for first-year rows (no T-1 lag available; detected via
      revenue_l being NaN).
    - DEPI and LVGI: imputed with 1.0 (neutral — unchanged rate/leverage).
    - TATA: imputed with 0.0 (neutral — zero accruals).
    - GMI and SGAI: used directly; already set to 1.0 for nature-method
      companies in _components.py.
    - flag = False when m_score = NaN.
    """
    df = df.copy()

    null_core = df[_CORE_COMPONENTS].isna().sum(axis=1)

    df["m_score"] = np.where(
        null_core > 2,
        np.nan,
        (
            -4.84
            + 0.920 * df["dsri"].fillna(1.0)
            + 0.528 * df["gmi"]
            + 0.404 * df["aqi"].fillna(1.0)
            + 0.892 * df["sgi"].fillna(1.0)
            + 0.115 * df["depi"].fillna(1.0)
            - 0.172 * df["sgai"]
            + 4.679 * df["tata"].fillna(0.0)
            - 0.327 * df["lvgi"].fillna(1.0)
        ),
    )

    # First year has no T-1 lag — null out
    df.loc[df["revenue_l"].isna(), "m_score"] = np.nan

    df["flag"] = df["m_score"].notna() & (df["m_score"] > threshold)

    return df
