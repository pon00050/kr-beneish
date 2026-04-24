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


---

**Working notes** (regulatory analysis, legal compliance research, or anything else not appropriate for this public repo) belong in the gitignored working directory of the coordination hub. Engineering docs (API patterns, test strategies, run logs) stay here.

---

## NEVER commit to this repo

This repository is **public**. Before staging or writing any new file, check the list below. If the content matches any item, route it to the gitignored working directory of the coordination hub instead, NOT to this repo.

**Hard NO list:**

1. **Any API key, token, or credential — even a truncated fingerprint.** This includes Anthropic key fingerprints (sk-ant-...), AWS keys (AKIA...), GitHub tokens (ghp_...), DART/SEIBRO/KFTC API keys, FRED keys. Even partial / display-truncated keys (e.g. "sk-ant-api03-...XXXX") leak the org-to-key linkage and must not be committed.
2. **Payment / billing data of any kind.** Card numbers (full or last-four), invoice IDs, receipt numbers, order numbers, billing-portal URLs, Stripe/Anthropic/PayPal account states, monthly-spend caps, credit balances.
3. **Vendor support correspondence.** Subject lines, body text, ticket IDs, or summaries of correspondence with Anthropic / GitHub / Vercel / DART / any vendor's support team.
4. **Named third-party outreach targets.** Specific company names, hedge-fund names, audit-firm names, regulator-individual names appearing in a planning, pitch, or outreach context. Engineering content discussing Korean financial institutions in a neutral domain context (e.g. "DART is the FSS disclosure system") is fine; planning text naming them as a sales target is not.
5. **Commercial-positioning memos.** Documents discussing buyer segments, monetization models, pricing strategy, competitor analysis, market positioning, or go-to-market plans. Research methodology and technical roadmaps are fine; commercial strategy is not.
6. **Files matching the leak-prevention .gitignore patterns** (*_prep.md, *_billing*, *_outreach*, *_strategy*, *_positioning*, *_pricing*, *_buyer*, *_pitch*, product_direction.md, etc.). If you find yourself wanting to write a file with one of these names, that is a signal that the content belongs in the hub working directory.

**When in doubt:** put the content in the hub working directory (gitignored), not this repo. It is always safe to add later. It is expensive to remove after force-pushing — orphaned commits remain resolvable on GitHub for weeks.

GitHub Push Protection is enabled on this repo and will reject pushes containing well-known credential patterns. That is a backstop, not the primary defense — write-time discipline is.
