"""kr_beneish — Beneish M-Score for Korean IFRS (KOSPI/KOSDAQ) companies."""

from __future__ import annotations

import pandas as pd

from ._components import compute_components
from ._score import compute_mscore, BENEISH_THRESHOLD
from ._validate import validate_input, REQUIRED_COLUMNS
from ._winsorize import winsorize_components

__version__ = "0.1.0"
__all__ = [
    "compute_mscores",
    "REQUIRED_COLUMNS",
    "BENEISH_THRESHOLD",
    "__version__",
]

_OUTPUT_COLUMNS = [
    "corp_code",
    "year",
    "dsri",
    "gmi",
    "aqi",
    "sgi",
    "depi",
    "sgai",
    "lvgi",
    "tata",
    "m_score",
    "flag",
]


def compute_mscores(
    df: pd.DataFrame,
    threshold: float = BENEISH_THRESHOLD,
) -> pd.DataFrame:
    """Compute Beneish M-Scores for a DataFrame of Korean company financials.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain these 14 columns:
            corp_code, year,
            receivables, revenue, cogs, sga, ppe, depreciation,
            total_assets, lt_debt, net_income, cfo,
            expense_method, fs_type

        Multiple companies and years are supported. Each company needs at least
        two consecutive years of data to produce a scoreable row.

        expense_method must be "function" or "nature". Nature-of-expense filers
        (~19% of KOSDAQ) cannot be scored for GMI/SGAI; those components are
        substituted with 1.0 (neutral).

    threshold : float
        M-Score above this value is flagged as potentially manipulative.
        Default: -1.78 (Beneish 1999 US calibration).
        Korean bootstrap alternative: -2.45 (see README for calibration notes).

    Returns
    -------
    pd.DataFrame
        One row per company-year where T-1 data is available. Columns:
            corp_code, year, dsri, gmi, aqi, sgi, depi, sgai, lvgi, tata,
            m_score, flag

        m_score is NaN for first-year rows (no prior year available) and for
        rows where more than 2 of the 5 core components are null.
        flag is False when m_score is NaN.

    Examples
    --------
    >>> import pandas as pd
    >>> from kr_beneish import compute_mscores
    >>> scores = compute_mscores(df)
    >>> flagged = scores[scores["flag"]]
    >>> scores_strict = compute_mscores(df, threshold=-2.45)
    """
    validate_input(df)
    df_comp = compute_components(df)
    df_wins = winsorize_components(df_comp)
    df_scored = compute_mscore(df_wins, threshold=threshold)

    # Filter to scoreable rows (T-1 data available)
    df_out = df_scored[df_scored["revenue_l"].notna()].copy()

    return df_out[_OUTPUT_COLUMNS].reset_index(drop=True)
