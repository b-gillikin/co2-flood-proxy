# Chapter 1 — Tributary Regionalisation from a Deeply Instrumented Donor

**Research question**: If one tributary catchment is instrumented deeply, how far
does that knowledge transfer to others, and what governs the decay?

This is donor-catchment regionalisation. The **Worm at Rimburg** is the donor: it
holds the CO2 sensor and the groundwater wells, and is mid-range on every
response characteristic. It ranks **18th of 42 on centrality**, not 2nd of 17 —
that earlier claim was computed on a retired metric over a
structure-contaminated set and is withdrawn. The donor stands on its
instrumentation, which is the only criterion no other gauge can meet. The
**Geul** provides within-catchment validation through a three-gauge
upstream-to-downstream chain.

The Kerkrade sensor work is the substitution argument's **limiting case**, not a
second study: indoor CO2 carries no precursor skill (AUROC 0.46 against 0.872 for
72-hour rainfall), so one instrument in the stack has no marginal value over
rainfall a forecaster already holds. That is a methods-and-negative-result
section, not a spine.

**`docs/chapter-synthesis.md` is canonical** for the idea, the design and the
data. `docs/chapter-direction.md` carries framing detail and the directions not
taken; both supersede `docs/chapter-readiness-plan.md` and
`chapter/chapter-draft.md`.

> **Numbers in this README are provisional pending the fixes in
> `docs/chapter-review-2026-08-06.md`.** In particular the distance-decay result
> is being recomputed on the null-calibrated metric, which the repo's own scope
> decision mandates and the published figure did not use.

## The progression

Each step widens the scope of substitution, which is what makes this an arc
rather than three separate studies:

| | Question | Substitution across |
| --- | --- | --- |
| Viefhues (2022) | Does a deeply instrumented site carry hydrological signal? | — |
| Eryilmaz (2025) | Can public weather substitute for local instrumentation? | data source |
| This chapter | Can knowledge from one instrumented catchment substitute for instrumentation elsewhere? | **space** |

## Data

All primary sources are public and need no key.

| Source | Extent | Access |
| --- | --- | --- |
| Waterschap Limburg discharge | 2024-08-06 →, hourly, 59 gauges available (17 pulled) | public OData |
| KNMI meteorology, 7 stations | 2020 →, hourly | Azure-collected slim blobs |
| BRO groundwater, 3 wells | 2021-01-01 → 2025-08-27, 6-hourly | public REST |
| Visual Crossing weather | 2016 →, 4 locations | Azure blobs |
| Kerkrade IoT CO2 | 2025-01-31 →, one house | Azure blobs + Blynk exports |

Two things worth knowing. The Waterschap archive is a **rolling ~2-year window**,
so longer history needs a direct request to Waterschap Limburg, WVER, or GRDC.
And it is **not limited to the Netherlands** — German Lanuv gauges on the Roer and
Worm and Rijkswaterstaat Maas gauges come through the same interface.

## How to reproduce

Create the environment:

```bash
conda env create -f environment.yml
conda activate chapter1-co2
export MPLCONFIGDIR="$PWD/.matplotlib"
```

Refresh sources and rebuild the joined hourly frame, event catalogue and QC:

```bash
python scripts/update_data.py --skip-download
```

Fetch the gauge inventory and candidate discharge series:

```bash
python scripts/22_ingest_waterschap_gauges.py
```

Fetch and characterise groundwater. Water level is itself barometric and must be
corrected before use as an exposure:

```bash
python scripts/05a_fetch_bro_groundwater.py
python scripts/05b_barometric_efficiency.py
```

Then the analysis scripts, in any order. `scripts/README.md` lists them by role.

KNMI defaults to `data/raw/knmi`, which holds NetCDF requiring xarray. To rebuild
from the slim CSVs alone:

```bash
python scripts/04_ingest_knmi.py --skip-download --raw-dir data/raw/knmi/azure_slim
```

## Conventions

- Hourly UTC throughout; local times resolved at ingestion, never later.
- Coverage gaps are never interpolated, and **a row on the hourly grid is not an
  observation**. Anything counting coverage counts observed values.
- Contiguous blocks break at any gap over one hour, so a block is a run with no
  missing hours rather than a date range.
- `data/raw/` and `results/` are gitignored; every input is re-fetchable by script.

## Layout

| Path | Contents |
| --- | --- |
| `scripts/` | Numbered runnable steps; see `scripts/README.md` |
| `src/` | Shared loaders, feature builders, evaluation helpers |
| `docs/` | Direction, decisions log, data requests, source notes |
| `archive/` | Code retired 2026-08-06; see `archive/README.md` |
| `chapter/` | Generated scaffolding, **not** an author draft |

## Status

Analysis on the Kerkrade donor characterisation is complete; findings and their
caveats are in `docs/chapter-direction.md` and `docs/decisions.md`. The
regionalisation analysis is the current work.

One withdrawn result worth flagging: the barometric response function used 49
correlated lags under plain OLS and rings, so the "instantaneous response" claim
is an artifact and should not be cited pending regularisation.
