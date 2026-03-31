# CLAUDE.md

Standalone PyPI library: Beneish M-Score for Korean IFRS companies.

## Ecosystem

Part of the Korean forensic accounting toolkit.
- Hub: `../forensic-accounting-toolkit/` | [GitHub](https://github.com/pon00050/forensic-accounting-toolkit)
- Task board: https://github.com/users/pon00050/projects/1
- Role: Foundation library
- Depends on: none
- Consumed by: krff-shell (Beneish M-Score computation)

## Common Commands

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ -v --cov=kr_beneish

# Build distribution
uv run python -m build
```

## Architecture

Single public function: `compute_mscores(df, threshold=-1.78)` in `__init__.py`.

Internal pipeline:
1. `_validate.py` — checks 14 required columns, raises `ValueError`
2. `_components.py` — computes 8 Beneish ratios + lag columns
3. `_winsorize.py` — per-year 1%/99% clip (≥20 samples per year)
4. `_score.py` — Beneish formula + null handling + flagging

Source layout: `src/kr_beneish/`. Package data: `src/kr_beneish/data/labels.csv`.

Modules:
- `_validate.py`, `_components.py`, `_winsorize.py`, `_score.py` — internal pipeline (see above)
- `datasets.py` — `load_labels()`: loads `data/labels.csv` via `importlib.resources`; returns DataFrame with `corp_code`, `fraud_label`, `company_name` (30 cases: 17 fraud, 13 clean)

## Known Gaps

| Gap | Why | Status |
|-----|-----|--------|
| `_components.py` `shift(1)` doesn't guard non-consecutive years | Gap years (e.g., 2019→2021) silently pair T with T-2, producing incorrect ratios | Unblocked — bug risk |
| No `test_datasets.py` for `load_labels()` | `importlib.resources` packaging-sensitive code untested | Unblocked |
| Labeled dataset (n=30) too small for publication-grade calibration | Bootstrap CI is wide: [-3.50, -1.60]; see `docs/calibration.md` | By design — needs more labeled cases |

## What Stays Out

These are pipeline-layer features, NOT in this library:
- XBRL → 14-column mapping
- `sector_percentile`, `risk_tier`, `dart_link`, `high_fp_risk`
- Output to parquet/CSV
- Statistical calibration scripts

## TATA fillna

`tata.fillna(0.0)` — neutral value is zero accruals, not 1.0. All other imputed
components use `fillna(1.0)` (neutral ratio = unchanged). This is intentional;
do not change without updating `test_known_values.py`.

## Korean IFRS

- `expense_method="nature"` companies: GMI=1.0 and SGAI=1.0. Do not change.
- Inf → NaN replacement happens in `_components.py` AFTER computing all ratios.
- Winsorization is in `_winsorize.py`, AFTER Inf→NaN replacement.

## Commit Protocol

1. `uv run pytest tests/ -v` — all green
2. Stage specific files by name
3. Commit and push
