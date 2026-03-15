# End-to-End Run — First Validation

This document records the first end-to-end execution of `kr_beneish` against
synthetic data representing a clean company and a suspicious company. It serves
as a reference for expected library behaviour and output interpretation.

---

## Setup

**Library version:** 0.1.0
**Date:** 2026-03-15
**Python:** 3.13.5
**Threshold:** −1.78 (Beneish 1999 US calibration, default)

### Input data

Two synthetic companies, three years each (2021–2023). The first year (2021)
provides the T-1 lag baseline; scoreable rows are 2022 and 2023.

**Company A001** is constructed to represent a stable, modestly growing company:
revenues growing ~5% per year, receivables tracking revenue, costs and margins
stable, strong cash conversion (CFO close to net income).

**Company B001** shares identical 2021 financials with A001 but diverges sharply
from 2022 onward: receivables surge far ahead of revenue growth, accruals spike
(net income high but CFO near zero), debt escalates.

```python
from kr_beneish import compute_mscores

scores = compute_mscores(df)
```

---

## Results

| corp_code | year | dsri | gmi | aqi | sgi | depi | sgai | lvgi | tata | m_score | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A001 | 2022 | 1.048 | 1.000 | 1.003 | 1.050 | 0.987 | 1.000 | 1.016 | 0.005 | −2.376 | False |
| A001 | 2023 | 1.016 | 1.000 | 1.007 | 1.029 | 0.994 | 0.995 | 0.992 | 0.005 | −2.410 | False |
| B001 | 2022 | 2.727 | 1.100 | 1.040 | 1.100 | 1.049 | 1.364 | 1.641 | 0.088 | −0.590 | True |
| B001 | 2023 | 1.435 | 1.045 | 1.025 | 1.045 | 1.059 | 1.116 | 1.385 | 0.106 | −1.648 | True |

---

## Interpretation

### A001 — not flagged

All eight components are near 1.0 (neutral). M-Scores of −2.38 and −2.41 sit
well below the −1.78 threshold and also below the Korean bootstrap alternative
of −2.45. The pattern is consistent with organic growth with no manipulation
signals.

### B001 — flagged in both years

Three components dominate the elevated M-Score:

**DSRI (Days Sales Receivables Index) = 2.73 in 2022.**
Receivables tripled (100 → 300) while revenue grew only 10% (1000 → 1100).
This is the strongest single signal — receivables growing far faster than
revenue is a classic revenue recognition manipulation pattern (booking sales
before cash is received, or fictitious sales).

**TATA (Total Accruals to Total Assets) = 0.088–0.106.**
Net income is high (150, 180) but CFO is near zero (10, 5). Almost all reported
earnings are accrual-based rather than cash-backed. Large positive TATA is the
single highest-weighted component in the Beneish formula (coefficient 4.679)
and a strong indicator of earnings inflation.

**LVGI (Leverage Index) = 1.64 in 2022.**
Long-term debt rose 75% (200 → 350) in a single year. Elevated leverage
alongside weak cash generation is consistent with a company under financial
pressure that may have incentives to inflate reported earnings.

DSRI normalises somewhat in 2023 (2.73 → 1.44) as the base effect of the 2022
jump is absorbed, but the M-Score remains above the threshold because TATA
continues to worsen and LVGI stays elevated.

---

## Pipeline behaviour confirmed

This run verified the following pipeline properties:

1. **First-year rows suppressed.** 2021 rows for both companies are excluded
   from output because no T-1 lag is available.

2. **Output schema.** Twelve columns returned: `corp_code, year` + 8 components
   + `m_score, flag`. No lag columns or intermediates in the output.

3. **Threshold logic.** `flag=True` when `m_score > -1.78`. A001's scores of
   −2.38 / −2.41 correctly produce `flag=False`; B001's scores of −0.59 / −1.65
   correctly produce `flag=True`.

4. **GMI and SGAI neutrality for nature-method filers.** Both companies use
   `expense_method='function'` so GMI and SGAI are computed normally. For
   nature-method companies these would be set to 1.0; that path is covered in
   `test_components.py::test_gmi_nature_is_one` and
   `test_components.py::test_sgai_nature_is_one`.

5. **Multi-company, multi-year handling.** Lag columns are computed within each
   `corp_code` group; A001's 2022 lag correctly uses A001's 2021 values, not
   B001's.

---

## Notes

- Winsorization was a no-op here: only 2 companies × 2 scoreable years = 4 rows
  per component, well below the 20-sample minimum required to compute stable
  percentiles. In production datasets with hundreds of companies per year,
  winsorization would clip extreme outliers.

- The synthetic B001 values were chosen to produce clear, readable signals, not
  to represent any real company. Real manipulation cases rarely show DSRI of 2.7
  in a single year; gradual deterioration over multiple years is more common.

- For the Korean bootstrap threshold (−2.45), A001's 2022 score of −2.376 would
  also be flagged. This illustrates why threshold choice matters and why the
  calibration notes in [`calibration.md`](calibration.md) should be read before
  publishing results.
