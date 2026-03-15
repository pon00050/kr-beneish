# Documentation Index

| Document | What it covers |
|---|---|
| [`korean-ifrs-adjustments.md`](korean-ifrs-adjustments.md) | Why and how the model is adjusted for K-IFRS: nature-of-expense filers, zero denominators, Inf handling, null tolerance guard, TATA invariance |
| [`calibration.md`](calibration.md) | Threshold calibration on Korean data, TATA sign flip finding, winsorization rationale, Lasso/RF feature importance, labeled dataset methodology |
| [`design-decisions.md`](design-decisions.md) | The 5 API design decisions: input contract, single public function, threshold parameter, labeled dataset inclusion, output scope |
| [`limitations.md`](limitations.md) | Known false positive patterns: biotech/pharma, first-year listings, TATA sign flip, nature-method blind spot, small sample gaps, CFS/OFS mixing |
| [`end-to-end-run.md`](end-to-end-run.md) | First end-to-end execution against synthetic data: full results table, component-level interpretation, pipeline behaviour confirmed |

## Quick orientation

If you are using this library:
- Start with the [README](../README.md) for API usage
- Read [limitations.md](limitations.md) before publishing results

If you are extending or calibrating this library:
- Read [calibration.md](calibration.md) for the Korean bootstrap study
- Read [design-decisions.md](design-decisions.md) before changing the API

If you are adapting for a non-Korean market:
- Read [korean-ifrs-adjustments.md](korean-ifrs-adjustments.md) to see which
  adjustments are Korea-specific vs. general IFRS
