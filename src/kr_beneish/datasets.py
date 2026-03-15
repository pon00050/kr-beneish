"""datasets.py — Load bundled validation datasets."""

from __future__ import annotations

from importlib.resources import files

import pandas as pd


def load_labels() -> pd.DataFrame:
    """Load the 30-case labeled validation dataset.

    Returns a DataFrame with columns:
        corp_code     : DART 8-digit company code
        fraud_label   : 1 = confirmed fraud/enforcement action, 0 = clean control
        company_name  : Korean company name

    The dataset contains 17 confirmed fraud cases (FSS enforcement actions,
    court records, or FSC sanctions) and 13 clean controls (KOSPI/KOSDAQ
    companies with no known enforcement actions and sustained low M-Scores).
    All companies are Korean listed companies (KOSPI/KOSDAQ).
    """
    data_path = files("kr_beneish").joinpath("data/labels.csv")
    with data_path.open("r", encoding="utf-8") as f:
        return pd.read_csv(f)
