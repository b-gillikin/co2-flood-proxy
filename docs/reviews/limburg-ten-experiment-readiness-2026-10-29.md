# Ten-experiment readiness sweep

29 October 2026. Research/engineering preparation, not a scientific result. The [six-part experiment plan](../limburg-ten-individual-experiments-plan-2026-10-29.md) and [machine-readable designs](../../config/limburg_individual_encoder_experiments_v1.json) are recorded. No extraction, fitting or scoring was launched.

## What is ready

- All ten individual designs specify hypothesis, exact primary input/cadence, checkpoint/output/readout, raw-data comparator, high-water comparison and interpretation.
- The held selected run directories, aggregate vectors, checkpoint files and existing environment Python executables are present for all ten. This is a filesystem inventory, not a fresh dependency/weight-integrity/forward-pass certification.
- The common source has 481 rainfall-defined regional episodes and 3,848 site–episode cases before experiment-specific support/verification/fold checks. Final analysis retains the census and unavailable-case ledger rather than taking an event sample.
- Core discharge/rainfall, catchment geography, GLO30 DEM and compact/expanded EO catalogue files are present. Earlier run audits and pinned source/weight manifests remain applicable to the old routes; new routes need their own numerical conformance checks.
- Eight designs require new, targeted encoding of held imagery; **DOFA and SatMAE initially reuse encoder vectors**. Ten experiments do not imply ten unnecessary full re-extractions.
- Approximately **67.9 GiB free** at this sweep. Existing corrected caches remain intact. Stream compact features; retain no dense token cubes. This is not a measured guarantee of enough space for an unbenchmarked implementation.

## Existing context support for the planned cadence

The read-only join checks all 3,848 initial-landmark site–episode rows. These are finite nonzero **existing pooled vectors**, before outcome/training/donor requirements. New spatial/multimodal outputs can have different coverage; these are not projected completed-experiment sample sizes.

| Experiment | Planned context | Existing supported rows / 3,848 |
| --- | --- | ---: |
| Presto | Twelve months | 2,016 |
| AnySat | Four weeks | 1,534 |
| Galileo | Twelve months | 1,959 |
| OlmoEarth | Four weeks | 1,192 |
| CROMA | Four weeks | 1,192 |
| Prithvi | Four weeks | 1,314 |
| Copernicus-FM | Four weeks | 1,600 |
| DOFA | Twelve months | 2,016 |
| TerraMind | Four weeks | 1,600 |
| SatMAE TOA | Completed-month snapshot | 2,082 |

The unsupported rows stay in the census with fallback/status. No additional satellite pull is automatically required; acquisition gaps versus new-feature support losses must be distinguished if a targeted recovery is later justified. These differences preclude a naive model ranking using each model's own supported average.

## What still needs implementation

The old runners cannot execute this plan unchanged. They use the previous averaged representations and learned standalone heads. The new work is primarily feature construction and validated residual/transfer readouts.

| Experiment | Held basis | Preparation still needed |
| --- | --- | --- |
| E01 Presto | Monthly S2 sequences, weights, dates and geography | Pixel mean/variance extraction, observed-area moments, twelve-month raw summaries and support joins |
| E02 AnySat | Coherent S2 sequences and checkpoint | Native spatial output/grid contract, zone pooling and equivalent raw spatial summaries |
| E03 Galileo | S2, Nano checkpoint, existing weather and GLO30 | Exact ERA5 monthly conventions; SRTM elevation/slope acquisition or verified held source; multimodal tensor/mask mapping. GLO30 is not SRTM, ERA5 soil water is not TerraClimate soil water |
| E04 OlmoEarth | Valid radar sequence route, v1.2 Tiny | Per-time/token readout, area pooling, same-orbit raw radar-change controls |
| E05 CROMA | Corrected radar route and completed orbit sensitivities | Per-date compact outputs, masked raw radar texture/amplitude controls |
| E06 Prithvi | HLS, Tiny TL and four-frame inputs | Token footprint mapping, contributing-area pooling, matched HLS descriptors |
| E07 Copernicus-FM | S2, base weights, known coordinates/date/scale | Populate metadata, verify units, ordered outputs and equal-metadata controls |
| E08 DOFA | Held v1 twelve-month vectors | Raw red-edge/NIR/SWIR descriptors; watercourse-grouped chronological transfer folds and source-only baseline. Target-river Q must not leak through neighbouring gauges |
| E09 TerraMind | Tiny S2L2A route | Ordered-frame frozen-backbone output and equally ordered raw comparator; wrapper/API conformance |
| E10 SatMAE | Completed TOA/QA60 snapshot vectors and SR sensitivity | Same-product/mask raw descriptors, exact joins and paired product-domain accounting |

A **shared chronological residual backbone** is not yet implemented for this plan. It must build training residuals from earlier-only out-of-fold baseline predictions, refit within inner folds, preserve a zero-correction option and score the strongest conventional method on the identical cases. Include a fixed-year conventional reference so its rolling archive refresh is not confused with encoder/model-class effects. E08 needs a separate source-watercourse transfer implementation and mm/h targets, not a relabelled same-gauge fit.

A **raw-descriptor builder** is also needed: observed-only spectral indices, spatial moments, temporal changes and simple masked radar textures on each model's actual product/grid/window. Equal-input controls must receive the same metadata, climate and terrain additions as their encoded counterpart. DOFA's six-band route lacks visible red/green, so do not invent NDVI/MNDWI for its raw comparator; use available red-edge/NIR/SWIR contrasts.

## Data reconciliation

No new discharge, rainfall or flood-label request is required for these targets. Spatial flood mapping, generative products and new sensors remain outside this run.

Galileo is the one planned input extension needing exact product work. The pinned source uses ERA5-Land monthly temperature and precipitation plus SRTM elevation/slope; the plan leaves TerraClimate, VIIRS and other groups masked. Check monthly accumulation, pixel-area aggregation, units/scales, normalizer and release-clock limitations. A small SRTM/ERA5 product pull, if needed, should cover the existing extent/windows only. Its availability need not delay the other nine experiments.

The soil/snow manifest at this sweep records **155/204 months validated (76%)**, active December 2021, no resumed-run failures, last update 2026-10-29 13:57:54 UTC. This is the latest manifest, not independent process monitoring. Soil/snow is a later shared physical-state control after completion and wrangling; it does not have to stop the ten primary experiments. Comparing a later physical-control arm must preserve exact paired coverage and earlier-only source windows.

Native-cadence and supplemental context support differ. File existence does not prove finite features for all 481 episodes, all required previous months or adequate training years. Build an experiment-specific row ledger before fitting, retain unsupported cases with the declared conventional fallback, and show paired-supported effects separately. No arbitrary minimum support threshold is imposed here; unidentified folds receive an explicit fallback/status and narrower claim.

## Execution preparation

Use `python scripts/167_check_individual_encoder_readiness.py --with-coverage` to repeat the read-only asset/design sweep. Its [JSON receipt](limburg-ten-experiment-readiness-2026-10-29.json) records checked paths, source hashes and the observed disk/download snapshot. Its successful exit means the inventory completed; **it does not mean the experiments are runnable**. It cannot launch jobs and never promotes receipt existence alone to scientific readiness.

Next implementation order:

1. Shared residual/transfer evaluation and raw-descriptor foundation, with synthetic/manual leakage and mask checks.
2. Cached-vector E08/E10 feature tables; model-specific extraction adapters developed alongside them.
3. For each new route: publisher-compatible fixture, missing-support fixture, weighted-pooling checks and an actual full-context runtime/memory/disk benchmark. Record hashes, frame/band/grid contracts, aggregation math and device/environment.
4. Queue model-specific extraction with one MPS lane and at most two CPU lanes; use measured throughput and memory, not presumed architecture equivalence. Avoid overlapping heavy scoring/extraction when it increases pressure. Independent experiments proceed while another is repaired.
5. Full-census evaluation, complete prediction/coverage provenance and paired review for each experiment; retain all outcomes. No extra severity/model search is launched just because an effect is null.

No defensible finish-time estimate exists until these changed routes are benchmarked. Preserve earlier results as common-interface evidence. This is a prepared design and dependency list, **not ten ready-to-launch production jobs**. Brian's approval of scientific direction is not a reason to ask again about routine authorized implementation; the outstanding work is engineering and data reconciliation.

## Preparation checks completed

Seven new preparation tests and 27 existing scarcity/EO-diagnostic regression tests passed (**34 total**). Checks cover complete/unique six-part designs, rejection of malformed designs, refusal to equate receipt presence with executable readiness, the TOA SatMAE route, and exclusion of future/zero-vector rows from held context support. Ruff checks/formatting and local-document link checks pass. These checks validate preparation tools and preserve earlier code behaviour; they do not validate model adapters or outcomes that have not been implemented.
