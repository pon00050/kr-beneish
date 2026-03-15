"""test_validate.py — Unit tests for _validate.validate_input."""

from __future__ import annotations

import pytest
import pandas as pd

from kr_beneish._validate import validate_input, REQUIRED_COLUMNS


def _make_valid_row() -> dict:
    return {
        "corp_code": "TEST001",
        "year": 2020,
        "receivables": 100,
        "revenue": 1000,
        "cogs": 600,
        "sga": 80,
        "ppe": 400,
        "depreciation": 50,
        "total_assets": 1500,
        "lt_debt": 200,
        "net_income": 100,
        "cfo": 80,
        "expense_method": "function",
        "fs_type": "CFS",
    }


class TestValidateInput:
    def test_valid_df_passes(self):
        """Full set of required columns raises no error."""
        df = pd.DataFrame([_make_valid_row()])
        validate_input(df)  # should not raise

    def test_empty_df_raises(self):
        """Empty DataFrame raises ValueError."""
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        with pytest.raises(ValueError, match="empty"):
            validate_input(df)

    def test_missing_single_column_raises(self):
        """Missing one column raises ValueError naming the column."""
        row = _make_valid_row()
        del row["receivables"]
        df = pd.DataFrame([row])
        with pytest.raises(ValueError, match="receivables"):
            validate_input(df)

    def test_missing_multiple_columns_raises(self):
        """Missing several columns raises ValueError listing them."""
        row = _make_valid_row()
        del row["revenue"]
        del row["cogs"]
        df = pd.DataFrame([row])
        with pytest.raises(ValueError, match="revenue"):
            validate_input(df)

    def test_missing_expense_method_raises(self):
        """expense_method is required — its absence must raise."""
        row = _make_valid_row()
        del row["expense_method"]
        df = pd.DataFrame([row])
        with pytest.raises(ValueError, match="expense_method"):
            validate_input(df)

    def test_non_dataframe_raises(self):
        """Passing a non-DataFrame raises ValueError."""
        with pytest.raises(ValueError, match="DataFrame"):
            validate_input({"corp_code": "x"})

    def test_required_columns_list_has_14_items(self):
        """REQUIRED_COLUMNS must contain exactly 14 entries per the API contract."""
        assert len(REQUIRED_COLUMNS) == 14
