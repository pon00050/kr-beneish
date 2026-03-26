# Known Limitations

This document lists known false-positive patterns, data quality issues, and
structural limitations of applying the Beneish M-Score to Korean KOSDAQ data.

---

## 1. High False Positive Rate for Biotech/Pharma

**Companies affected:** Biotech (WICS G3510), pharma (G3520), medical devices (G3520)

**Why it happens:**
Korean biotech companies capitalise R&D expenditure under K-IFRS IAS 38 when
specific development criteria are met. This creates high non-current assets
relative to revenue, inflating AQI (asset quality "deterioration") and
potentially TATA (when capitalised R&D exceeds amortisation).

**Quantified:** In a sample of KOSDAQ biotech companies with no enforcement
history, ~60–70% were flagged at the −1.78 threshold in at least one year.

**How to handle:**
Use sector codes to post-filter results. The krff-shell pipeline
sets a `high_fp_risk` flag for WICS G3510/G3520 companies. This library
does not include that flag (it requires sector data not in the 14-column input).

---

## 2. First-Year of Listing (No Prior-Year Data)

**Companies affected:** All newly listed companies in their first year on KOSPI/KOSDAQ

**Why it happens:**
The M-Score requires year-over-year ratios (T vs T-1). For a company's first
filing year, there is no T-1 data. `m_score` is set to `NaN` for these rows.

**Implication:** Companies that manipulate financials *before* listing (IPO
window dressing) cannot be detected by this model in their listing year.

---

## 3. TATA Sign Flip on KOSDAQ Growth Companies

**Companies affected:** High-growth KOSDAQ companies (tech, biotech, early-stage)

**Why it happens:**
The Beneish (1999) model assigns a **positive** coefficient to TATA (+4.679),
treating high accruals as a manipulation signal. In Korean KOSDAQ, high accruals
often reflect genuine R&D capitalisation, not manipulation.

**Effect:** Growth-stage companies with legitimate R&D pipelines score higher
(more suspicious) than they should. This is not a bug in the implementation;
it reflects a genuine limitation of applying a US-GAAP model to K-IFRS.

**How to handle:**
Users with labelled Korean data can refit the TATA coefficient. The component
outputs (including `tata`) are available in the library's output for this purpose.

---

## 4. Nature-of-Expense Filers: GMI and SGAI Blind Spot

**Companies affected:** ~19% of KOSDAQ companies

**Why it happens:**
As described in [`docs/korean-ifrs-adjustments.md`](korean-ifrs-adjustments.md),
nature-method filers have no COGS/SGA line. GMI and SGAI are set to 1.0 (neutral).

**Effect:** For these companies, the M-Score is based only on 6 components
(DSRI, AQI, SGI, DEPI, LVGI, TATA). Gross margin manipulation and SGA inflation
are invisible to the model.

**No fix is possible** without an alternative source of cost-of-sales data
(e.g., segment reporting, management discussion notes). This is a structural
limitation of the nature-of-expense format.

---

## 5. Small Sample Winsorization Gaps

**Companies affected:** Any year where a component has fewer than 20 non-null values

**Why it happens:**
When running on a small dataset (e.g., a single sector or a handful of companies),
per-year winsorization is skipped because there are not enough observations to
estimate stable 1%/99% percentiles.

**Effect:** Extreme outlier scores may pass through unclipped, inflating or
deflating M-Scores for that year.

**How to handle:**
Run on a sufficiently large dataset (ideally 100+ companies per year). For
single-company analysis, set `threshold` to a more conservative value.

---

## 6. Consolidated vs. Separate Financial Statements

**Companies affected:** All companies with subsidiaries

**Why it happens:**
Korean listed companies file both consolidated (CFS) and separate/parent-only
(OFS) financial statements. The ratios can differ materially between the two.

**This library's position:**
The input column `fs_type` accepts `"CFS"` or `"OFS"` but does not adjust
any formula based on the statement type. If a company's rows contain mixed
`fs_type` values across years (e.g., CFS in 2019 and OFS in 2020), the library
emits a `UserWarning` naming the affected companies, because the T/T-1
year-over-year ratios will span two different consolidation scopes and produce
unreliable results. The computation proceeds regardless; the warning is a
data quality signal, not an error.

**Best practice:** Use CFS (consolidated) when available, as it more accurately
represents the economic entity. OFS may be appropriate for holding-company
analysis.

---

## 7. The Model Detects Symptoms, Not Causes

The Beneish M-Score identifies **accounting patterns associated with manipulation**,
not manipulation itself. A high score can arise from:

- Genuine earnings management that does not cross into fraud
- Legitimate accounting choices that happen to inflate the score
- Data quality issues (misclassified XBRL fields, restatements)
- The structural issues above (biotech, nature-method, first-year)

**All flags from this library are hypotheses for human review, not fraud
conclusions.** Regulatory action requires far more evidence than a high M-Score.

---

## 8. LVGI: Long-term Debt Scope

K-IFRS balance sheets do not always separate current vs. non-current portions
of debt the same way US GAAP does. Some companies include lease liabilities
(IFRS 16) in `lt_debt`; others show them separately.

**Effect:** LVGI is noisy across companies depending on how lease liabilities
are classified. The impact is typically small (LVGI has a coefficient of
only −0.327 in the formula).

---

## Calibration Study Sample Size Warning

The Korean bootstrap threshold (−2.45) was estimated from **50 labeled cases**.
This is too small for high-confidence calibration. The 95% CI [−3.50, −1.60]
is wide. Both thresholds (−1.78 and −2.45) fall within it.

Do not treat −2.45 as a "precisely calibrated Korean threshold." It is a
directional estimate suggesting the US threshold may be somewhat too permissive
for KOSDAQ, not a definitive answer.
