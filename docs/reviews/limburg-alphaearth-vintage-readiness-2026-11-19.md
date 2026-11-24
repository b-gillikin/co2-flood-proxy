# Limburg imagery-year and representation readiness

19 November 2026. Internal research record.

| Comparison | Descriptor year | Discharge evaluation and control |
| --- | --- | --- |
| Completed multiyear | 2017 AlphaEarth | Local 2021–2025 and external 2021–2024, C0 |
| Completed Geul benchmark | 2020 AlphaEarth and TESSERA | Geul 2021, same C0 including 2017 land cover |
| Active imagery-year comparison | 2017 versus 2020 AlphaEarth | Same 30 original folds and same C0 |
| Planned product comparison | Matched 2020 satellite descriptors, documented pretest windows for other products | Common enriched C1, with input vintages recorded |

The 2020 snapshot predates held evaluation and is also applied retrospectively
to older training rows and 2020 validation rows. The primary outcome stays daily
high-water MAE. The 13.86% local withheld-river all-day gain belongs to the
completed 2017 AlphaEarth comparison.

## Verified

- All 1,151,268 daily rows and 123 nonembedding columns matched the original
  feature table exactly in values and order. Observed-hours metadata changed
  from nullable integer to float in storage, with identical values and
  missingness. This field is outside the predictor and split definitions.
- All 30 held-group/year assignments and the inner-fold map matched. Wurm
  2021 has a distinct execution ID to bypass the legacy 2017 cache. The
  original model settings and both selection policies carry forward. Package
  versions match across the original study, Geul benchmark and active run.
- Reused Geul 2021 split rows, inner membership and weights matched exactly.
  Its 267 observed test days include four high-water days. The prior audit
  verified exact reproduction of the conventional predictions in that fold.
- The two 2020 satellite inputs cover all 394 gauge records. Both AlphaEarth
  years use the same collection and 10 m EPSG:3035 mean convention. All seven
  local geometry hashes match including the two German aliases, and held
  local 2020 means agree with the new export within 1.5e-14. Of 387 regional
  hashes, 384 match. The three exceptions are documented topologically equal
  repairs with identical original and new valid-pixel counts.
- Ruff and diff whitespace checks passed. The worker and hashed input files
  were left in place.

## After the worker finishes

The runner writes fold receipts, paired predictions and pooled point scores.
Verify all 81,857 paired rows and reproduce the archived C0 and 2017 summaries.
Check selected tuning fits for tree-cap saturation. Report direct 2020 versus
2017 contrasts and each vintage versus C0 across local chronological, local
withheld-river, and external evaluation, with year and river breakdowns.
Use the inherited 999 paired whole-year and synchronized time-block draws
with explicit undefined draws and high-water and clean high-water support.
Run the prepared readout after all folds complete:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 \
  .venv-dise/bin/python scripts/288_review_alphaearth_vintages.py
```

It writes `completion_review.json` alongside the paired predictions.

## Outstanding for the extension

- StefaLand candidate hash verified. The checkpoint includes a Runoff
  projection, and runoff-free inference for this artifact remains unresolved.
  The public Liu et al. archive documents CAMELS TE1–TE5 reproduction with
  annual AlphaEarth inputs. Seek the runoff-free encoder or matching annual
  descriptors, normalization and units, and a worked reference example.
- Basin2Vec's advertised public package contains precomputed USGS lookup
  vectors. The repository release API returned an empty list on this pass.
  Request encoder weights, exact channel order and units, normalizers and
  reference input/output before specifying a European source crosswalk.
- Assemble C1 from verified input recipes, with actual dates and source
  definitions. Pilot each newly usable encoder for input compatibility and
  label exclusion, then benchmark a matched C1 fold. Artifact investigations
  can proceed independently from the active fits.

Sources: [Liu et al. reproduction archive](https://zenodo.org/records/22001499),
[Basin2Vec documentation](https://github.com/Muhammad-Talha-MT/basin2vec),
[StefaLand methods](https://arxiv.org/html/2509.17942v3).

## Matched 2020 satellite comparison — completed 20 November 2026

Both products use a fixed 2020 descriptor over the same reference polygons.
C0 retains its original covariates, including 2017 land-cover fractions. The
primary selection policy is native-discharge RMSE. High-water MAE is the
primary outcome. Local evaluation covers 2021–2025 and reserved external
evaluation covers 2021–2024. The original 2017 versus 2020 AlphaEarth contrast
remains a separate result about imagery year.

All 30 folds, 81,857 paired gauge-days and saved output hashes verified.
The 2020 AlphaEarth and C0 columns reproduce the prior archive exactly.
TESSERA required 29 fresh outer folds with 38 fits each (1,102 fits total);
Geul 2021 reused its verified benchmark. Three selected TESSERA tuning
folds reached the tree limit (Wurm, Gulp and Voer, each in 2021, under the
primary policy). Treat capacity as a diagnostic for the C1 benchmark.

The table reports percent reduction in MAE relative to C0. Negative values
indicate higher error. Brackets give the paired 95% percentile range from
synchronized 30-day blocks, conditional on the evaluated rivers and fixed
predictions. The two local regimes reuse the same gauge-days.

| Evaluation and stratum | Gauge-days | AlphaEarth 2020 | TESSERA 2020 |
| --- | ---: | ---: | ---: |
| Local, time held out, all days | 12,362 | +1.17 [−0.68, +3.10] | −0.70 [−2.23, +0.79] |
| Local, time held out, high water | 226 | −2.72 [−5.56, −0.13] | −2.10 [−5.26, +0.55] |
| Local, whole river held out, all days | 12,362 | +2.58 [−0.30, +5.59] | +0.56 [−1.60, +2.81] |
| Local, whole river held out, high water | 226 | −2.11 [−5.58, +1.46] | −6.47 [−10.41, −3.04] |
| Reserved external, all days | 57,133 | +0.33 [−3.19, +3.21] | +2.65 [−0.16, +4.96] |
| Reserved external, high water | 1,055 | +0.11 [−7.40, +12.74] | −1.32 [−8.47, +6.96] |

The paired draws favour TESSERA over AlphaEarth for external all-day error
(+0.93 to +3.80% reduction), while TESSERA's improvement over C0 is
uncertain. For held local rivers at high water, TESSERA has higher error than
AlphaEarth (−7.24 to −2.43% reduction). The strictly clean subset preserves
the local high-water deterioration (172 gauge-days). For held rivers,
AlphaEarth worsens 4.65% and TESSERA 9.33%; 751/999 paired draws are defined.
No external clean-only comparison is available. External high-water intervals
have 628/999 defined draws because some draws lack required gauge support.

### River and year differences

| River/system | AlphaEarth all-day reduction vs C0 | TESSERA all-day reduction vs C0 |
| --- | ---: | ---: |
| Geleenbeek | +3.87% | +19.11% |
| Geul | +0.60% | +2.99% |
| Gulp | −5.61% | +2.56% |
| Voer | −14.02% | −0.31% |
| Wurm | +14.99% | −17.71% |
| Ahr | −1.52% | +2.86% |
| Erft | +13.31% | +15.89% |
| Sieg | −4.66% | −3.69% |

Local rows hold the whole river out. AlphaEarth improves local withheld-river
all-day MAE in four of five test years, with year effects from −1.91% to
+4.66%. TESSERA improves two of five years, with effects from −4.45% to +5.93%.
On withheld local rivers at high water, TESSERA worsens pooled MAE in each
year. Both products lower high-water MAE on the Gulp by about 10%. That
river-level result coexists with weaker pooled performance.

Clean daily high-water episode examples, selected to show gains as well as
losses, use the mean absolute error over the eligible rows of the episode
(mm/day). These are descriptive illustrations from the same archive.

| River and episode start | Gauge-days | C0 | AlphaEarth | TESSERA |
| --- | ---: | ---: | ---: | ---: |
| Gulp, 11 March 2024 | 3 | 1.269 | 0.954 | 1.222 |
| Voer, 7 February 2024 | 3 | 1.732 | 1.848 | 1.527 |
| Wurm, 28 January 2021 | 8 | 2.574 | 3.436 | 3.534 |

The matched evidence supports modest, river-dependent gains in routine
discharge reconstruction and no dependable high-water gain for either 2020
product over C0. The completed 2017 AlphaEarth all-day gain of 13.86% on held
local rivers becomes 2.58% with 2020 AlphaEarth under the same C0 design.
Report that dependence on the choice of year alongside the product comparison.
The study measures retrospective daily discharge error. Evaluation of warning
decisions would use issued forecasts, warning thresholds and lead times.

Reproduce from
`results/limburg_representation_extension_v1/satellite_c0_multiyear_2020/`
using `completion_review.json`, `paired_predictions.parquet`, and the fold
receipts. The completion review includes river, year, both selection policies,
and 14-day, 30-day, 60-day and whole-year resampling results.
