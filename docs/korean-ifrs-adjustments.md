# Korean IFRS Adjustments

This document explains why and how the Beneish M-Score formulas are adjusted
for Korean IFRS financial statements.

## Background

The Beneish (1999) model was calibrated on US GAAP companies. Korean listed
companies (KOSPI/KOSDAQ) file under K-IFRS (Korean International Financial
Reporting Standards), which differs in several ways that directly affect how
the 8 Beneish ratios are computed.

---

## 1. Nature-of-Expense Filers (~19% of KOSDAQ)

### The problem

Korean companies can classify expenses in the income statement either by
**function** (cost of goods sold, SG&A — the typical method) or by
**nature** (raw materials, employee benefits, depreciation — grouped by type
rather than by where they occur in the business).

Under K-IFRS IAS 1.99–105, both methods are permitted. Approximately 19% of
KOSDAQ-listed companies file by nature of expense.

This means:
- No `cogs` (cost of goods sold) line item
- No `sga` (selling, general & administrative) line item

### Effect on Beneish components

| Component | Requires | Effect |
|---|---|---|
| **GMI** | gross margin = (revenue − cogs) / revenue | Undefined — no cogs |
| **SGAI** | sga / revenue ratio | Undefined — no sga |
| DSRI | receivables / revenue | Unaffected |
| AQI | (total_assets − ppe) / total_assets | Unaffected |
| SGI | revenue growth | Unaffected |
| DEPI | depreciation / (ppe + depreciation) | Unaffected |
| LVGI | lt_debt / total_assets | Unaffected |
| TATA | (net_income − cfo) / total_assets | Unaffected |

### Resolution

Set **GMI = 1.0** and **SGAI = 1.0** for nature-method companies.

Rationale: 1.0 is the neutral value for a ratio (no year-over-year change).
This zeroes out their contribution to the M-Score formula:
- GMI: `0.528 × 1.0 = 0.528` (same as if gross margin were flat year-on-year)
- SGAI: `−0.172 × 1.0 = −0.172` (same as if SGA ratio were flat)

This is conservative: it neither inflates nor deflates the score.
It does NOT mean these companies are clean — only that GMI and SGAI
cannot be scored.

**Implementation:** `_components.py` checks `expense_method == "nature"` and
overrides the computed value with 1.0 after the ratio is calculated.

---

## 2. Zero Denominators

### The problem

Small-cap and early-stage KOSDAQ companies frequently have:
- **Zero revenue** in one or more years (pre-revenue stage companies, restructuring years)
- **Zero receivables** in the prior year (new product launch, cash-only business model)

Standard division produces `Inf` rather than a meaningful ratio.

### Resolution

Replace zero with `NaN` **before** computing any ratio:

```python
rev = df["revenue"].replace(0, np.nan)
ta  = df["total_assets"].replace(0, np.nan)
```

This causes the affected component to become `NaN` rather than `Inf`.
The null-tolerance guard then handles it (see Section 4).

---

## 3. Inf from Small Denominators

### The problem

A prior-year denominator of, say, 1 KRW million with a current-year numerator
of 1,000 KRW million produces a ratio of 1,000 — extreme but not technically Inf.
However, near-zero denominators can also produce actual `Inf` through floating-point
operations (e.g., if a pandas numeric conversion introduces rounding to exactly 0).

### Resolution

After computing all 8 components, replace any remaining `Inf` or `-Inf` with `NaN`:

```python
for comp in _COMPONENTS:
    df[comp] = df[comp].replace([np.inf, -np.inf], np.nan)
```

Then apply per-year winsorization (1%/99%) to clip large-but-finite outliers.
See [`docs/calibration.md`](calibration.md) for the winsorization rationale.

---

## 4. Null Tolerance Guard

### The problem

Once some components are NaN (from zero denominators, missing data, or
nature-method substitution), the question is: when should the M-Score be
considered unreliable enough to withhold entirely?

### Resolution

The library distinguishes between **core** and **ancillary** components:

| Category | Components | Why |
|---|---|---|
| Core (5) | DSRI, AQI, SGI, DEPI, TATA | Empirically most significant in Beneish (1999); not substituted |
| Ancillary | GMI, SGAI, LVGI | GMI/SGAI substituted for nature filers; LVGI often undisclosed |

If **more than 2 of the 5 core components** are null, `m_score = NaN`.
Otherwise, null core components are imputed with neutral values:

| Component | Imputed value | Neutral rationale |
|---|---|---|
| DSRI | 1.0 | Receivables/revenue ratio unchanged |
| AQI | 1.0 | Asset quality unchanged |
| SGI | 1.0 | Revenue flat |
| DEPI | 1.0 | Depreciation rate unchanged (common for CF-subtotal-only filers) |
| TATA | 0.0 | Zero accruals (not 1.0 — TATA is a level, not a ratio) |
| LVGI | 1.0 | Leverage unchanged |

---

## 5. TATA: Cash Flow Method Invariance

Korean IFRS allows both the **direct method** and **indirect method** for
the cash flow statement. About 70% of KOSDAQ companies use the indirect method.

TATA = (net_income − cfo) / total_assets

This formula is **invariant** to the method used. Both the direct and indirect
methods produce the same `cfo` total. The difference is only in the breakdown
shown below the total. No adjustment is needed.

---

## 6. DEPI: Net PPE Approximation

K-IFRS requires PPE to be reported **net** of accumulated depreciation on the
balance sheet (unlike US GAAP, which often reports gross PPE separately).

The DEPI formula requires gross PPE as a proxy for the depreciable asset base.
We approximate it as:

```
gross_PPE ≈ net_PPE + current_year_depreciation
```

This is the same convention used in the original Beneish (1999) implementation
and in subsequent Korean applications of the model.

---

## 7. LVGI: Missing Long-term Debt

Many small KOSDAQ companies are entirely equity-financed or have only
short-term borrowings. When `lt_debt` is not disclosed (null), LVGI is null.

This alone does **not** kill the M-Score — LVGI is ancillary, not core.
It is imputed with 1.0 (leverage unchanged).

---

## Summary Table

| Issue | Frequency | Resolution |
|---|---|---|
| Nature-method filers | ~19% of KOSDAQ | GMI = SGAI = 1.0 |
| Zero revenue | Rare, early-stage | Replace 0 → NaN before ratio |
| Inf from near-zero denominators | Rare | Replace Inf → NaN after ratio |
| Missing lt_debt | Common, small-caps | LVGI = NaN → imputed 1.0 |
| Missing CFO/net_income | Occasional | TATA = NaN → counted in null_core |
| >2 core components null | Rare (data quality) | m_score = NaN (withheld) |
