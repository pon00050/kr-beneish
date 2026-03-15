# Calibration

This document describes how the M-Score threshold and winsorization parameters
were calibrated for Korean KOSDAQ data.

## Background

The Beneish (1999) model was calibrated on US GAAP companies from 1982–1992.
The standard threshold of **−1.78** is widely used across markets, but its
false positive rate on Korean KOSDAQ companies is noticeably higher than in
US datasets.

This library ships with the original Beneish coefficients and threshold as defaults.
This document records what was found when the threshold was re-estimated on a
Korean labeled dataset, so users can make an informed choice.

---

## Korean Bootstrap Threshold

### Method

A bootstrap re-estimation was run on 50 labeled Korean listed companies:
- **30 core labels** (from `data/labels.csv`):
  - 17 confirmed fraud/enforcement cases (FSS, courts, FSC sanctions, 2020–2026)
  - 13 clean controls (sustained mean M-Score < −2.8, no known enforcement)
- **20 auto-controls**: companies with mean M-Score < −2.5 over ≥3 years,
  no CB/BW activity, no regulatory flags — added to balance the sample

The bootstrap re-estimated the optimal decision threshold by maximising F1
across 1,000 resamples of the 50-case pool.

### Result

| Threshold | Source | False positive rate on KOSDAQ |
|---|---|---|
| **−1.78** | Beneish (1999), US GAAP | Higher than US |
| **−2.45** | Korean bootstrap, CI [−3.50, −1.60] | Lower |

The US threshold **−1.78 falls inside the bootstrap CI [−3.50, −1.60]**,
confirming it remains statistically defensible. Use −2.45 if you want
fewer false positives on KOSDAQ small-caps.

### Why the gap exists

Korean KOSDAQ companies tend to score higher (more suspicious) on the
Beneish scale for structural reasons that are not manipulation:

1. **High revenue growth** → elevated SGI (legitimate growth companies)
2. **R&D capitalisation** → elevated accruals → elevated TATA
3. **CB/BW financing** → balance sheet changes that affect AQI
4. **Small size** → volatile ratios from small denominators

These structural factors inflate false positive rates under the US calibration.

---

## TATA Sign Flip

When a Lasso regression was run on the 50-case Korean dataset, the TATA
coefficient came out **negative** (~−2.1), versus **+4.679** in Beneish (1999).

**Interpretation:** In Korean KOSDAQ, high accruals often signal legitimate
R&D capitalisation (growth-stage tech and biotech companies) rather than
earnings manipulation. The positive-accruals-as-manipulation assumption of
Beneish (1999) does not hold uniformly in this market.

**Library decision:** The library uses the original **+4.679** Beneish coefficient.
Reasons:
1. The Lasso estimate is unstable with 50 cases (high variance, CI includes 0)
2. The +4.679 coefficient is internationally recognised and reproducible
3. Users can apply their own calibrated coefficients to the component outputs

If you are researching KOSDAQ specifically and want the Korean-calibrated
coefficients, you can use the component outputs from this library and apply
your own formula on top.

---

## Winsorization

### What it does

Components are clipped at the **1st and 99th percentile per calendar year**
before the M-Score is computed. This prevents extreme outliers from distorting
the score distribution.

### Why per-year, not global

Korean KOSDAQ M-Score distributions shift over time (different economic cycles,
IFRS adoption effects, CB/BW market cycles). Global winsorization thresholds
estimated on 2018 data would be mis-calibrated for 2023 data.

Per-year winsorization also means each year's scores are internally consistent:
the 99th-percentile outlier in 2020 is clipped against 2020's own distribution,
not against all years combined.

### Minimum sample guard

Years with **fewer than 20 non-null values** for a given component are not
winsorized. With fewer than 20 observations, the 1st and 99th percentile
estimates are too noisy to be useful. This situation arises when:
- Running on a small sample (`--sample 10` in the pipeline)
- Filtering to a specific sector with few companies

### Source

Winsorization at 1%/99% is stated in Beneish (1999) as part of the methodology.
The per-year implementation follows Dechow et al. (2011) "Predicting Material
Accounting Misstatements."

---

## Lasso / RF Feature Importance (Informational)

A Lasso regression and Random Forest classifier were fit on the 50-case Korean
labeled dataset to understand which components are most informative:

| Component | Lasso coefficient | RF importance | Notes |
|---|---|---|---|
| DSRI | Active (positive) | High | Strongest single signal |
| AQI | Active (positive) | Moderate | Asset quality deterioration |
| SGI | Active (positive) | Low-moderate | High in growth cos → noisy |
| DEPI | Active | Low | Weak signal on KOSDAQ |
| TATA | Active (**negative**) | Moderate | Sign flip vs. Beneish |
| GMI | **Dropped by Lasso** | Low | Uninformative on KOSDAQ |
| SGAI | Active (negative) | Low | Marginal |
| LVGI | Active | Low | Moderate |

RF AUC: 0.756 ± 0.192 (high variance due to small n=50).

**Implication for users:** On KOSDAQ, DSRI is the single most actionable
component. Companies with DSRI > 2.0 in a given year warrant close examination
regardless of their overall M-Score.

---

## Labeled Dataset Methodology

The 30 cases in `data/labels.csv` were labeled as follows:

**Fraud = 1 (17 cases):**
- FSS (금융감독원) enforcement action confirmed: accounting irregularity investigation
  concluded with sanction, referral to prosecution, or trading suspension
- Court record confirmed: criminal indictment or conviction for accounting fraud
  (형사소송법 위반, 특경가법, 자본시장법)
- FSC (금융위원회) Securities and Futures Commission disciplinary action

**Fraud = 0 (13 cases):**
- Mean M-Score < −2.8 over ≥3 consecutive years
- No CB/BW activity in the same period
- No FSS/FSC enforcement actions
- No material restatements
- Listed continuously on KOSPI or KOSDAQ

**What this dataset is NOT:**
- Not a random sample of Korean companies
- Not balanced by sector
- Not sufficient for publication-grade calibration (n=30 is too small)

It is a **validation sanity check** — useful for confirming your pipeline
produces scores that order-of-magnitude agree with known outcomes. It is
not intended for fitting new coefficients.
