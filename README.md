# Chapter 1 — Donor Transfer Across Maas Tributaries

**Research question**: Given a gauged tributary catchment, how much of what you
would learn from instrumenting it can you get instead from a neighbouring gauge —
and how far does that reach?

Measured as a **substitution gap in AUROC** against the 0.05 threshold inherited
from Eryilmaz (2025), on **Waterschap Limburg's own published Fase alarm
thresholds**, over the Limburg Maas tributary network. The **Worm at Rimburg** is
the worked case.

## Where to read

| Document | Role |
| --- | --- |
| **`docs/chapter-synthesis.md`** | **Canonical.** Idea, design, data. Every figure quoted from an artifact in `results/`. Start here. |
| `docs/chapter-scope-and-preregistration.md` | Scope proposal + the binding pre-registration. Take to the supervisor. |
| `docs/analysis-inventory.md` | Every analysis the chapter has run, and why each passes or fails |
| `docs/HANDOFF.md` | Session state only |
| `docs/decisions.md`, `docs/scope-decisions.md` | Audit trail and live decisions |
| `docs/predecessor-notes.md` | Viefhues (2022) and Eryilmaz (2025) in detail |
| `archive/README.md` | What was retired, and why |

## Status, stated plainly

**The chapter has no positive result about Maas tributaries yet.** What stands is
inherited, negative, or descriptive:

- Public weather substitutes for indoor sensing — gap **−0.012** within fold
- Indoor CO2 carries no precursor skill — **0.46** against rainfall's **0.872**
- Response similarity decays with distance — **−0.311**, 9.7% of variance, net of
  a measured procedural floor
- Donor reach varies from **−0.58 to +0.21** depending on which catchment you
  stand on

**The central test — what a donor gauge buys against a receiver's own — is not
built.** It is gated on a supervisor conversation, not on data or code.

## Data

All primary sources are public and need no key.

| Source | Extent | Access |
| --- | --- | --- |
| Waterschap Limburg discharge | 2024-08 → 2026-08, hourly, 59 locations → **38 after filtering** | public OData |
| Waterschap Limburg water level | same window, **272 natural locations**, unused | same endpoint |
| LANUK NRW discharge | 1950 → 2026, 42 German gauges | open licence |
| RWS Maas main stem | 2000 → 2026, 10-min | CC0 |
| DWD precipitation | 1995 → 2026, 34 stations | open licence |
| KNMI meteorology, 7 stations | 2020 →, hourly | Azure-collected slim blobs |
| Kerkrade IoT CO2 | 2025 → 2026, one house, **31% complete** | Azure blobs + Blynk exports |

The Waterschap archive is a **rolling ~2-year window**; longer history needs a
direct request, tracked in `docs/data-requests.md`. It is **not limited to the
Netherlands** — German and Rijkswaterstaat gauges come through the same interface.

**The binding constraint:** Fase 1 fires a median of **3 times per gauge** over the
record, and 11 of 37 gauges never reach it. No method repairs that.

## Reproduce

```bash
conda env create -f environment.yml
conda activate chapter1-co2
export MPLCONFIGDIR="$PWD/.matplotlib"
```

Refresh sources and rebuild the joined hourly frame, event catalogue and QC:

```bash
python scripts/update_data.py --skip-download
```

Then the analysis scripts in any order; `scripts/README.md` lists them by role.
Note `23_catchment_similarity.py` takes ~12 minutes.

Tests: use `pytest tests/` (84 pass). A bare `pytest` collects `archive/tests/`
and fails.

## Conventions

- Hourly UTC throughout; local times resolved at ingestion, never later.
- Coverage gaps are never interpolated, and **a row on the hourly grid is not an
  observation**. Anything counting coverage counts observed values.
- Contiguous blocks break at any gap over one hour.
- **One currency: the AUROC gap.** An analysis needing a new currency to express
  its result is out of scope by definition.
- **Never pool a score across groups** fitted on different data.
- No interpretive sentence containing a number is written into a generated
  artifact as a string literal.
- `data/raw/` and `results/` are gitignored; every input is re-fetchable by script.

## Layout

| Path | Contents |
| --- | --- |
| `scripts/` | 16 numbered runnable steps; see `scripts/README.md` |
| `src/` | Shared loaders, feature builders, the substitution harness |
| `docs/` | Canonical synthesis, pre-registration, decisions, source notes, reviews |
| `archive/` | Code and documents retired 2026-08-05 → 07; see `archive/README.md` |
