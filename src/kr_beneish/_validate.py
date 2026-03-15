"""_validate.py — Input validation for kr_beneish."""

from __future__ import annotations

import warnings

import pandas as pd

REQUIRED_COLUMNS: list[str] = [
    "corp_code",
    "year",
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
    "expense_method",
    "fs_type",
]


def _warn_fs_type_inconsistency(df: pd.DataFrame) -> None:
    """Warn if any company has mixed fs_type values across years.

    Mixing CFS and OFS rows for the same company produces meaningless
    year-over-year ratios because the T and T-1 balance sheets cover
    different consolidation scopes.
    """
    counts = df.groupby("corp_code")["fs_type"].nunique()
    mixed = counts[counts > 1].index.tolist()
    if mixed:
        warnings.warn(
            f"Mixed fs_type (CFS/OFS) detected for {len(mixed)} company(s): "
            f"{mixed}. Year-over-year ratios are unreliable when fs_type "
            "changes across years. Use CFS throughout for best results.",
            UserWarning,
            stacklevel=3,
        )


def validate_input(df: pd.DataFrame) -> None:
    """Raise ValueError if df is missing required columns or is empty."""
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Expected pd.DataFrame, got {type(df).__name__}.")
    if df.empty:
        raise ValueError("Input DataFrame is empty.")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Input DataFrame is missing required columns: {missing}. "
            f"All required columns: {REQUIRED_COLUMNS}"
        )
    _warn_fs_type_inconsistency(df)
