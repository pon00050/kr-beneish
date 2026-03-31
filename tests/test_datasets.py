"""test_datasets.py — Tests for kr_beneish.datasets.load_labels()."""

from __future__ import annotations

import io

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


class TestLoadLabelsFixtures:
    """Fixture-based isolation tests that monkeypatch importlib.resources.files().

    These tests decouple load_labels() from the bundled data file so that the
    happy path, missing-file, and malformed-CSV branches can be exercised
    independently of the real labels.csv.
    """

    @pytest.fixture()
    def _patch_files(self, monkeypatch):
        """Factory fixture: call with a CSV string; patches files() for the test."""

        def _apply(content: str) -> None:
            class _Ctx:
                def __enter__(self_) -> io.StringIO:
                    return io.StringIO(content)

                def __exit__(self_, *a: object) -> None:
                    pass

            class _Traversable:
                def joinpath(self_, *a: object) -> "_Traversable":
                    return self_

                def open(self_, mode: str = "r", encoding: str | None = None) -> _Ctx:
                    return _Ctx()

            monkeypatch.setattr(
                "kr_beneish.datasets.files", lambda _pkg: _Traversable()
            )

        return _apply

    def test_happy_path_with_fixture(self, _patch_files: object) -> None:
        """Happy path: fixture-provided valid CSV loads into a correct DataFrame."""
        _patch_files(
            "corp_code,fraud_label,company_name\n"
            "10001,1,테스트회사A\n"
            "20002,0,테스트회사B\n"
        )
        df = load_labels()
        assert isinstance(df, pd.DataFrame)
        assert {"corp_code", "fraud_label", "company_name"}.issubset(df.columns)
        assert len(df) == 2

    def test_missing_file_raises_file_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FileNotFoundError propagates when the bundled labels.csv is absent."""

        class _Missing:
            def joinpath(self, *a: object) -> "_Missing":
                return self

            def open(self, mode: str = "r", encoding: str | None = None) -> None:
                raise FileNotFoundError("labels.csv not found")

        monkeypatch.setattr("kr_beneish.datasets.files", lambda _pkg: _Missing())
        with pytest.raises(FileNotFoundError):
            load_labels()

    def test_malformed_csv_raises_parser_error(self, _patch_files: object) -> None:
        """pd.errors.ParserError raised when CSV contains an unclosed quoted field."""
        _patch_files(
            'corp_code,fraud_label,company_name\n10001,"unclosed,Company\n'
        )
        with pytest.raises(pd.errors.ParserError):
            load_labels()
