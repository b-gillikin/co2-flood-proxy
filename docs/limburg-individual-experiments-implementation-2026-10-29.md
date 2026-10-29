# Ten individual encoder experiments — implementation and execution

2026-10-29. Internal research aid. Brian writes the dissertation and sends email. The [audited design](limburg-ten-individual-experiments-plan-2026-10-29.md) remains the scientific specification; its JSON is a frozen design snapshot, not a live process monitor.

## Implemented work

Validation: **447 repository tests pass** with the explicit PROJ data path; Ruff, whitespace and changed-document local-link checks pass. One nonfatal NumPy/binary warning remains in the existing optional NetCDF soil/snow fixture; that test passes. Native encoder runtimes retain their recorded numerical-library versions.

Scripts 168–173 prepare conventional references, acquire Galileo's exact small physical-input extension, extract model-specific features, fit chronological residual heads, audit paired effects and manage the local queue. Outputs live in `results/limburg_individual_experiments_v1/`. Execution is recorded in `queue/progress.json`; each worker has its own progress/identity/manifest and logs in `logs/individual-experiments-v1/`.

The primary ledger contains all 481 rainfall episodes × eight gauges × four issue offsets × three information scenarios: **46,176 assessments before support/verification exclusions**. Each scenario retains 15,392 rows. Missing observations, unavailable source features and unavailable training remain visible; absent verification is unscored. The prepared conventional ledger reproduced **45,012 saved donor-mean predictions with zero mismatches**. An engineering fixture is not an empirical finding.

Nine experiments use separate same-gauge annual heads. DOFA uses six held-watercourse groups, combining all three Wurm/Worm stations. Source residuals and source ground features exclude both the outer held watercourse and the training source's watercourse. Inner folds additionally hold out one source watercourse and an earlier year. Both learned corrections share the same training rows, source-only processing and river/site/storm/offset weighting. Its rich/local-absent regimes are identical after whole-watercourse Q exclusion: the rich label is an explicit alias, not another result. No direct ranking against the same-gauge effect sizes is intended.

## Extraction contracts

| Model | Current individual readout | Raw comparison / declared mechanism check |
| --- | --- | --- |
| Presto | Native 12-month per-pixel features; area-weighted mean and SD, whole catchment/elevation thirds | Same monthly optical moments/indices/context; mean-only features from the same pixel outputs |
| AnySat | Four-week native patch outputs, whole catchment/elevation thirds | Same spatial optical inputs; global CLS output from the same forward pass |
| Galileo Nano | Twelve-month S2 plus exact monthly ERA5 temperature/precipitation and SRTM elevation/slope | Same physical/optical raw descriptors; S2-only encoding versus enriched encoding on the same optical-supported footprint |
| OlmoEarth v1.2 Tiny | Native per-time radar spatial features; retain four ordered summaries | Same orbit-88 VV/VH levels, variation, texture and change |
| CROMA | Four ordered SAR GAP vectors | Same raw radar amplitude, texture and change; documented contrast stretch followed by division by 255 |
| Prithvi EO2 Tiny TL | Per-time spatial tokens from observed HLS frames, pooled by catchment/zone | Same HLS observations; spatial-global mean per time from the same tokens |
| Copernicus-FM | Four ordered S2 frame vectors with real location, epoch day and token area | Same pixels/metadata; matched no-metadata forward pass |
| DOFA v1 | Reuse verified monthly landscape vectors; source-watercourse transfer | Same six non-RGB bands and usable indices, temporal raw summaries, terrain/area/location |
| TerraMind Tiny | Four ordered independent S2 frame vectors | Same ordered raw data; temporal-mean feature comparison from the same outputs |
| SatMAE | Reuse verified TOA/QA60 monthly snapshot vectors | Raw descriptors use exactly the cached encoder's accepted patches, pixels and dates |

All raw controls also receive fixed terrain summaries, relevant image-tile context outside the polygon, dates and coverage. Elevation thirds are descriptive regions, not mapped floodplains or travel times. Monthly/weekly windows end before the original rainfall landmark and stay frozen through the four issue offsets. Acquisition time is a nominal availability clock, not a reconstruction of product publication times.

AnySat and Prithvi drop wholly unobserved frames from their native temporal input. Prithvi uses the supported flexible frame count, regenerates its positional grid and reinserts missing slots with zero support in the four-slot readout. Galileo/OlmoEarth raw controls use the same observed native-token blocks as the encoder. No wholly missing source week or pixel is declared observed.

## Fitting and interpretation

C is the frozen conventional mean trajectory. C-median uses the same donors; fixed-year mean/median references expose archive refresh. Corrections predict residuals in mm/h and can reduce C; clipping occurs only after the residual is added. The raw arm may retain C. The encoded arm contains all zero-EO alpha candidates, the exact previously selected causal raw policy, C itself and the positive EO weights 0.1/1. Selection sees the latest two feasible earlier closed validation years, never the held year's responses. Every fitted transform sees only its training rows. Whole regional storms are excluded across year boundaries.

Main raw/EO blocks and their interactions with preceding-24h rain and C's predicted mean response share the same transform rule. Ridge minimizes weighted squared residual loss; earlier-year trajectory MAE chooses parameters. Small fits use exact weighted dual ridge. Large transfer fits use an equivalent bounded-memory conjugate-gradient solution, numerically checked against the dual objective; failures and convergence diagnostics are retained.

The six declared mechanism comparisons run under local-Q absence only, with common raw/encoder query **and training** support. Galileo's enriched/optical-only comparison uses the optical-supported enriched feature output. TerraMind's mean comparison changes temporal detail and dimension together; it does not isolate order alone. SatMAE's separate SR/TOA product-and-support sensitivity remains supporting: an unmatched score subtraction is not a radiometric-domain effect.

The review independently recomputes point losses, retains every assessment and reports paired encoder–raw, encoder–C-mean and encoder–C-median effects, site-native units, high-water/documented-flood strata, country/watercourse/site results, availability and actual correction/fallback modes. Shared 999 whole-year draws assign a storm and all issues/sites to its initial-landmark year. Nonfinite draws are counted. Intervals condition on fitted procedures and this held network. Actual-case tables select large improvements/deteriorations for interpretation and are explicitly post hoc.

## Execution and storage

The queue enforces **at most one MPS worker plus two CPU workers**, including fitting/review CPU jobs. Each model has an isolated real-imagery fixture, a full-context benchmark and resumable full extraction. Completed features feed their own scoring/review jobs; failure of one model does not cancel other models. Benchmarks measure memory and compact-output volume. The Mac is kept from idle sleep while the controller runs; closing the lid can still suspend work.

Transient spatial tensors are discarded after weighted moment aggregation. Atomic tile contributions, receipts and compact catchment/context tables replace per-patch caches; restarting does not add the same tile twice. Existing selected outputs, raw imagery, model weights and other chapters' data are preserved. The earlier authorized Disk Cleanup recovered 13.03 GiB; its receipt is [documented separately](disk-cleanup.md). No new cloud compute or storage spend is introduced.

Start/resume (from this repository):

```sh
.venv-foundation/bin/python -u scripts/173_queue_individual_experiments.py --run
```

The controller needs normal Mac GPU access. Read-only status:

```sh
.venv-foundation/bin/python scripts/173_queue_individual_experiments.py --status
```

After primary checks, the two combined-mask profiles, supporting C+E attribution, soil/snow control and SatMAE product sensitivity remain separately identified supporting work. They are **not claimed implemented or completed by the primary queue**. The queue contains the 29 distinct primary model/scenario fits and six matched configuration comparisons, plus engineering/review tasks. Do not silently replace same-scenario training by a frozen-head distribution-shift replay; that would need a documented design amendment.

## Engineering history and provenance

- Exact Galileo extension: 17 verified GeoTIFFs, approximately 5.03 MiB. SRTM elevation/slope and ERA5-Land monthly temperature/total precipitation are held in `data/raw/limburg_galileo_physical/`. ERA5 bands are bound to provider band names in the receipts even though GeoTIFF descriptions were absent. Product units remain kelvin/metres; unused export-helper shifts are not applied.
- A GEE request initially combined incompatible region/grid/dimension arguments; it was corrected before acquisition. No invalid export is used.
- Native runtimes lacked geospatial/Parquet readers. A minimal overlay was installed. Original NumPy 1.26.4 and Torch versions were verified/restored before inference; the temporary modern-NumPy upgrade produced no encoder result. The overlay is recorded under `environments/eo-screen/` and worker identities include actual imported runtime versions.
- Prithvi's regenerated positional grid initially stayed on CPU under MPS. The adapter moves that generated grid to the selected device without changing its values. Implicit upstream tensor allocations use the same device context. Native smoke tests passed after these corrections.
- A transfer-cache integration test caught pandas Series promotion and microsecond/nanosecond ambiguity in fixed-year closure. Closure now uses explicit nanosecond timestamps, with early unavailable cases tested through serialization/resume. No production transfer score was generated by the faulty branch.
- The broad test run needed an explicit PROJ database path; all nine affected geospatial tests passed with that path. The controller sets it for the full-suite proof and workers.
- Full-ledger plumbing exposed repeated decompression of reference arrays; arrays are now loaded once per scoring process. A path-construction defect was corrected in the isolated engineering runner before any production score was generated.
- The conventional preparation was executed before import/style formatting of its helper. The executed bytecode, script, design snapshot, formatted-equivalent source and function-level equivalence proof are preserved in `preparation/source_snapshot/` and `source-compatibility.json`. Later changes to the separately used transfer helper are not represented as the source of that earlier same-gauge ledger.
- Engineering one-patch outputs and scores are isolated under `engineering/` and `engineering_scores/`; they are never scientific census feature tables or findings. Production identities bind source code, selected cached outputs, exact checkpoints/publisher code, runtime, source files, physical inputs and spatial geometry.

There is no positive-result requirement, fixed minimum support gate, new RQ, new provider request or manuscript-writing step in this implementation.

Acquisition update: the previously authorized soil/snow pull stopped at 163/204 months after a remote connection closed. It was resumed sequentially on 29 October, preserving completed files/receipts and the failure history. Its manifest remains the live status source; this does not delay the primary queue.

Execution record (29 October): code commit `d725937` was pushed before launch. The local controller is running; all ten final source-bound native fixtures passed, and full-context benchmarks have started. The current readiness JSON tracks this execution. Primary fits/reviews and supporting work remain pending; no new empirical finding is claimed. Runtime versions are saved in `queue/runtime.json`, alongside the source-bound queue state.
