"""_validate.py — Input validation for kr_beneish."""

from __future__ import annotations

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
