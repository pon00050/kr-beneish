# CLAUDE.md

Standalone PyPI library: Beneish M-Score for Korean IFRS companies.

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

Same as kr-forensic-finance:
1. `uv run pytest tests/ -v` — all green
2. Stage specific files by name
3. Commit and push
