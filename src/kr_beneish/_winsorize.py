"""_winsorize.py — Per-year 1%/99% winsorization of Beneish components."""

from __future__ import annotations

import pandas as pd

_COMPONENTS = ["dsri", "gmi", "aqi", "sgi", "depi", "sgai", "lvgi", "tata"]

_MIN_SAMPLES = 20  # minimum non-null values in a year to apply winsorization


def winsorize_components(df: pd.DataFrame) -> pd.DataFrame:
    """Clip each Beneish component at 1st/99th percentile per calendar year.

    Years with fewer than _MIN_SAMPLES non-null values for a component are
    left unclipped — not enough data to estimate stable percentiles.

    Winsorization is per-year: extreme values in year A do not affect the
    clipping thresholds used for year B.
    """
    df = df.copy()

    for comp in _COMPONENTS:
        if comp not in df.columns:
            continue
        for yr in df["year"].unique():
            mask = df["year"] == yr
            vals = df.loc[mask, comp].dropna()
            if len(vals) < _MIN_SAMPLES:
                continue
            lo, hi = vals.quantile(0.01), vals.quantile(0.99)
            df.loc[mask, comp] = df.loc[mask, comp].clip(lower=lo, upper=hi)

    return df
