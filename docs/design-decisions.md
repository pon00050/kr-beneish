# Design Decisions

This document records the five major API design decisions made before
implementing this library, with the rationale behind each choice.

---

## Decision 1: Input contract — pre-normalized columns only

**Choice:** Accept a 14-column DataFrame with pre-normalized financial values.
The library does NOT handle XBRL parsing, DART API calls, or raw financial
statement normalization.

**Alternatives considered:**
- Accept raw DART/XBRL field names and handle mapping internally
- Accept multiple input formats (XBRL, Excel, custom CSV)

**Why this choice:**
The XBRL→column mapping is the hard part of working with Korean financial
data. The mapping logic depends on the data source (OpenDART field names
differ from raw XBRL), the IFRS version, and reporting quirks. Embedding
this in the library would:
1. Make the library tightly coupled to a specific data source (OpenDART)
2. Require updating the library whenever DART changes its schema
3. Mix data access concerns with the computation

Keeping the library focused on "given these 14 numbers, compute M-Score"
makes it composable: researchers using Bloomberg, FnGuide, or KIS Data can
all use it by normalizing their own columns.

**Trade-off:** First-time users need to build their own XBRL→14-column
mapper. The README specifies exactly what each column means.

---

## Decision 2: Single public function

**Choice:** `compute_mscores(df, threshold=-1.78)` is the only public function.
All internal modules are private (`_validate`, `_components`, etc.).

**Alternatives considered:**
- Expose each module as a public API (`compute_components()`, `winsorize()`)
- Expose a class-based API (`BeneishScorer().fit(df).transform(df)`)

**Why this choice:**
The computation is a linear pipeline: validate → components → winsorize → score.
There is no meaningful partial use case: you always want all 8 components plus
the final score. A class API would add complexity without benefit for this use case.

Internal modules are private to preserve the right to refactor the pipeline
without breaking downstream code. The output contract (12-column DataFrame)
is stable; the internal implementation is not guaranteed to be.

**Trade-off:** Power users who want to run only certain stages cannot do so
through the public API. They can import internal modules (`from kr_beneish._components
import compute_components`) with the understanding that these are not stable APIs.

---

## Decision 3: Threshold as a parameter, US default

**Choice:** Default threshold **−1.78** (Beneish 1999). Accept `threshold=`
kwarg. Document −2.45 Korean bootstrap in the README and calibration docs.

**Alternatives considered:**
- Hardcode −2.45 as the default (Korean-specific)
- Make threshold required (no default)
- Expose a `fit()` method to estimate threshold from labeled data

**Why this choice:**
The US threshold −1.78 is the internationally recognised benchmark. Researchers
and analysts comparing results across markets expect this value. Changing the
default would silently produce different results from every other Beneish
implementation, making comparison harder.

The Korean bootstrap estimate (−2.45) is informative but based on 50 cases —
too small for high-confidence calibration. Documenting it as an alternative
respects the uncertainty.

A `fit()` method is out of scope for v0.1. Users who want calibration can
use the component outputs with sklearn directly.

---

## Decision 4: Ship labeled dataset as package data

**Choice:** Include `data/labels.csv` (30 cases) in the installed package.
Accessible via `kr_beneish.datasets.load_labels()`.

**Alternatives considered:**
- Ship no data (pure computation library)
- Host data externally and download on first use
- Include a larger synthetic dataset

**Why this choice:**
The labels represent months of manual research (cross-referencing FSS
enforcement records, court filings, and company histories). Making them
available to other researchers has direct scientific value.

Bundling them in the package avoids network dependencies and version skew
(external URLs can break). The file is 1.5 KB; package size is not a concern.

**What the data is and isn't:** See [`docs/calibration.md`](calibration.md)
for a full description of labeling methodology and limitations.

---

## Decision 5: Output scope — components + score + flag + zone

**Choice:** Return only: `corp_code, year, dsri, gmi, aqi, sgi, depi, sgai,
lvgi, tata, m_score, flag, zone`.

The `zone` column provides the standard Beneish three-level interpretation
using fixed boundaries: `"clean"` (< −2.00), `"caution"` (−2.00 to −1.78),
`"flagged"` (> −1.78), or `None` when `m_score` is NaN. Zone boundaries are
independent of the `threshold` parameter — `flag` handles the parameterised
binary; `zone` always reflects the documented Beneish interpretation zones.

**Excluded from output:**
- `sector_percentile` — requires WICS sector codes (external data)
- `risk_tier` (Low/Medium/High/Critical) — tiering logic belongs to the caller
- `dart_link` — URL construction depends on the application (web vs. script)
- `high_fp_risk` — sector-specific biotech/pharma flag needs sector codes
- `extraction_date` — metadata, not a Beneish output

**Why this choice:**
All the excluded columns require additional data sources beyond the 14 inputs,
or they embed business logic (what counts as "high risk"?) that should be the
caller's decision.

Adding them would either:
1. Require more input columns (sector codes, CFS/OFS history) → larger contract
2. Embed opinionated thresholds that researchers might reasonably disagree with

A minimal output contract is easier to compose. Callers can JOIN the output
back to their own data to add any enrichment they need.

---

## Non-decision: Coefficients

The Beneish (1999) coefficients are used as-is:
```
-4.84, +0.920, +0.528, +0.404, +0.892, +0.115, -0.172, +4.679, -0.327
```

No re-calibration of coefficients was done for v0.1. The Korean bootstrap
(see [`docs/calibration.md`](calibration.md)) estimated a new **threshold**
but not new **coefficients**. Coefficient re-calibration would require a
labelled dataset at least 10× larger than the current 50 cases.
