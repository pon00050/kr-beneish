# kr-beneish

Beneish M-Score for Korean IFRS (KOSPI/KOSDAQ) companies.

```bash
uv add git+https://github.com/pon00050/kr-beneish
```

```python
from kr_beneish import compute_mscores

scores = compute_mscores(df)
flagged = scores[scores["flag"]]
```

## Documentation

- [`docs/korean-ifrs-adjustments.md`](docs/korean-ifrs-adjustments.md) — why and how the model is adjusted for K-IFRS
- [`docs/calibration.md`](docs/calibration.md) — Korean bootstrap threshold, TATA sign flip, labeled dataset methodology
- [`docs/design-decisions.md`](docs/design-decisions.md) — API design rationale
- [`docs/limitations.md`](docs/limitations.md) — known false positive patterns and structural limitations

## What it does

Computes the [Beneish (1999)](https://doi.org/10.2469/faj.v55.n5.2296) 8-variable M-Score for each company-year in a DataFrame. Returns the 8 components plus a composite score and a binary flag.

```
M = -4.84 + 0.920·DSRI + 0.528·GMI + 0.404·AQI + 0.892·SGI
         + 0.115·DEPI - 0.172·SGAI + 4.679·TATA - 0.327·LVGI
```

## Input

A pandas DataFrame with **14 required columns**:

| Column | Description |
|---|---|
| `corp_code` | DART 8-digit company identifier |
| `year` | Fiscal year (integer) |
| `receivables` | Trade receivables |
| `revenue` | Net revenue / sales |
| `cogs` | Cost of goods sold |
| `sga` | Selling, general & administrative expense |
| `ppe` | Property, plant & equipment (net) |
| `depreciation` | Depreciation & amortisation |
| `total_assets` | Total assets |
| `lt_debt` | Long-term debt |
| `net_income` | Net income / profit for the year |
| `cfo` | Cash flow from operations |
| `expense_method` | `"function"` or `"nature"` (Korean IFRS filing type) |
| `fs_type` | `"CFS"` (consolidated) or `"OFS"` (separate) |

All monetary values in the same unit (e.g., KRW millions). The function computes year-over-year ratios internally; each company needs **at least two consecutive years** to produce a score.

## Output

One row per scoreable company-year (first year per company is excluded — no prior-year lag available):

| Column | Description |
|---|---|
| `corp_code`, `year` | Identity |
| `dsri` | Days Sales in Receivables Index |
| `gmi` | Gross Margin Index |
| `aqi` | Asset Quality Index |
| `sgi` | Sales Growth Index |
| `depi` | Depreciation Index |
| `sgai` | SG&A Index |
| `lvgi` | Leverage Index |
| `tata` | Total Accruals to Total Assets |
| `m_score` | Composite M-Score (NaN if insufficient data) |
| `flag` | `True` if `m_score > threshold` |

## Threshold

The default threshold is **−1.78** (Beneish 1999, calibrated on US GAAP companies).

For Korean KOSDAQ data, a bootstrap calibration on 50 labeled cases (17 confirmed fraud, 13 clean controls, 20 auto-controls) gives a threshold of **−2.45** (CI [−3.50, −1.60]):

```python
scores = compute_mscores(df, threshold=-2.45)
```

The US threshold (−1.78) falls within the bootstrap CI and remains valid. The Korean threshold produces fewer false positives on KOSDAQ small-caps.

**All flags are hypotheses for human review, not fraud conclusions.** False positive rates are elevated for biotech/pharma companies (R&D capitalisation creates systematic TATA inflation).

## Korean IFRS adjustments

| Issue | Handling |
|---|---|
| Nature-of-expense filers (~19% of KOSDAQ) | GMI=1.0 and SGAI=1.0 (structurally undefined without a COGS/SGA line) |
| Zero denominators | Replaced with NaN before ratio computation (not 0 or Inf) |
| Inf from small denominators | Replaced with NaN after component computation |
| ≤2 of 5 core components null | Score still computed; null components imputed with neutral values |
| >2 of 5 core components null | m_score = NaN |

The 5 core components are: DSRI, AQI, SGI, DEPI, TATA.

## Winsorization

Components are winsorized at the 1st/99th percentile per calendar year, matching Beneish (1999) methodology. Years with fewer than 20 non-null observations are not winsorized.

## Validation dataset

```python
from kr_beneish.datasets import load_labels

labels = load_labels()
# corp_code, fraud_label (1=fraud, 0=clean), company_name
```

30 labeled Korean listed companies: 17 confirmed fraud/enforcement actions (FSS, court records, FSC sanctions), 13 clean controls (sustained low M-Scores, no known enforcement).

## What this library does NOT include

These features are intentionally left in the pipeline layer:

- XBRL → 14-column mapping (depends on your data source)
- `sector_percentile` computation
- `risk_tier` tiering
- `dart_link` generation
- `high_fp_risk` sector flag (biotech/pharma)
- Output to parquet/CSV
- Lasso/RF calibration scripts

## Requirements

- Python ≥ 3.10
- pandas ≥ 1.5
- numpy ≥ 1.20
