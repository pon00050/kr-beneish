"""test_datasets.py — Tests for kr_beneish.datasets.load_labels()."""

from __future__ import annotations

import pandas as pd
import pytest

from kr_beneish.datasets import load_labels


class TestLoadLabels:
    def test_returns_dataframe(self):
        df = load_labels()
        assert isinstance(df, pd.DataFrame)

    def test_row_count(self):
        """Dataset documents 30 cases: 17 fraud + 13 clean controls."""
        df = load_labels()
        assert len(df) == 30

    def test_required_columns_present(self):
        df = load_labels()
        assert {"corp_code", "fraud_label", "company_name"}.issubset(df.columns)

    def test_fraud_label_is_binary(self):
        df = load_labels()
        assert set(df["fraud_label"].unique()).issubset({0, 1})

    def test_label_distribution(self):
        """17 fraud cases and 13 clean controls per documentation."""
        df = load_labels()
        assert df["fraud_label"].sum() == 17
        assert (df["fraud_label"] == 0).sum() == 13

    def test_corp_codes_are_positive_integers(self):
        """CSV stores corp_code as int (leading zeros not preserved in CSV format)."""
        df = load_labels()
        assert pd.api.types.is_integer_dtype(df["corp_code"])
        assert (df["corp_code"] > 0).all()

    def test_no_null_values(self):
        df = load_labels()
        assert df.isnull().sum().sum() == 0

    def test_corp_codes_are_unique(self):
        df = load_labels()
        assert df["corp_code"].nunique() == len(df)

    def test_returns_new_dataframe_each_call(self):
        """load_labels() should not return a mutable shared reference."""
        df1 = load_labels()
        df2 = load_labels()
        df1.loc[0, "fraud_label"] = 999
        assert df2.loc[0, "fraud_label"] != 999
