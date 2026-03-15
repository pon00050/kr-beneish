"""test_validate.py — Unit tests for _validate.validate_input."""

from __future__ import annotations

import warnings

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


def _make_row(corp_code: str, year: int, fs_type: str) -> dict:
    """Valid row with overridden corp_code, year, and fs_type."""
    row = _make_valid_row()
    row.update({"corp_code": corp_code, "year": year, "fs_type": fs_type})
    return row


class TestFsTypeConsistencyWarning:
    def test_mixed_fs_type_emits_warning(self):
        """A company with CFS in one year and OFS in another triggers UserWarning."""
        df = pd.DataFrame([
            _make_row("C001", 2019, "CFS"),
            _make_row("C001", 2020, "OFS"),
        ])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            validate_input(df)
        messages = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
        assert any("C001" in m for m in messages), (
            f"Expected warning mentioning C001, got: {messages}"
        )

    def test_consistent_fs_type_no_warning(self):
        """Consistent fs_type across years produces no UserWarning."""
        df = pd.DataFrame([
            _make_row("C001", 2019, "CFS"),
            _make_row("C001", 2020, "CFS"),
        ])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            validate_input(df)
        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        assert not user_warnings

    def test_mixed_fs_type_names_affected_companies(self):
        """Warning message includes the corp_code of the offending company."""
        df = pd.DataFrame([
            _make_row("MIXED001", 2019, "CFS"),
            _make_row("MIXED001", 2020, "OFS"),
            _make_row("CLEAN001", 2019, "CFS"),
            _make_row("CLEAN001", 2020, "CFS"),
        ])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            validate_input(df)
        messages = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
        assert any("MIXED001" in m for m in messages)
        assert not any("CLEAN001" in m for m in messages)
