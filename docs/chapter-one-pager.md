# Limburg — satellite-informed discharge reconstruction

Living research aid, updated 17 November 2026. Brian writes dissertation prose.
Independent DISE-inspired adaptation accepted; local preparation/benchmark
completed, audit corrections implemented in v2; full regional comparison not launched.

## Research Question(s)

Can satellite-derived catchment information make a global discharge model more
accurate during high water, including on other rivers?

Characterize source errors; test AlphaEarth's incremental value beyond common
weather and conventional catchment descriptors; evaluate transfer without local
target-river calibration.

## Motivation

Assess when globally available satellite information can supplement local
hydrological modelling and monitoring capacity. Identify prerequisites, costs,
severe errors and transfer limitations relevant to agency investment. This is
daily retrospective reconstruction, not a demonstration of forecast lead time,
operational warnings or avoided flood losses.

## Data

René/Jens observations and provider qualifications, verified GEOGLOWS discharge,
2017 AlphaEarth catchment means, and newly acquired gauge-specific ERA5-Land
weather for 2017–2025. Consistent conventional descriptors use SRTM terrain,
2017 Copernicus fractional land cover and a surface field-capacity proxy;
regulation coverage remains incomplete; a no-dam inventory entry does not rule
out other controls or management. Seven local gauges represent five
river groups; Eys remains excluded and the Meuse is not added as a new target.

CAMELS-DE-1h observations and matched predictors now cover 387 regional gauges:
337 provisional donors and 50 reserved external records in Ahr/Erft/Sieg. There
are 823,956 complete observed daily values in 2018–2024. UTC hour-end timing is
verified from the primary paper. These are not independent or uniformly
quality-verified populations. The spatial review preserves all records with
explicit overlap/location strata; high-overlap and location-consistent
sensitivity views contain 344 and 331 gauges. One search-boundary gauge was
recovered; eight additional station/reference conflicts were identified.
Regional observations end in 2024; 2025 predictors do not create 2025 labels.

## Method

One pooled XGBoost log-residual correction of daily GEOGLOWS discharge. Compare
weather/model history alone, plus conventional attributes, plus AlphaEarth, and
plus both. Use observed Q as verification, never current observed Q as an input
to reconstruct itself. Keep raw GEOGLOWS and appropriate calibration references.

Stage 1 establishes the local daily reference. Stage 2 trains with permitted
historical local/regional donor data and tests the same seven local gauges.
Stage 3 tests reserved external rivers without their calibration labels.

## Methodology

All eligible days; identical cohorts and tuning budgets across feature sets;
chronological test years 2021–2025, nested river-group withholding and
reconstructed-discharge RMSE (mm/day) for primary early stopping and selection. All three
Wurm gauges leave together. Prior-landscape descriptors, train-only transforms,
common weather definitions, quality/missingness records and paired high-water
and all-day evaluation. Report measurement/geometry limitations and river/storm
dependence. Current local data have informed prior experiments; do not claim
blind confirmation or historical as-issued foundation-model availability.

## Findings / current status

The completed earlier next-24h GEOGLOWS experiment found conventional correction
value but no dependable incremental Presto/AnySat gain. Its outcome differs
from this daily reconstruction study; results are preserved separately.

Current preparation has 20,454 local gauge-days for 2018–2025, including 19,538
complete observed/model pairs. The corrected local held-Wurm 2021 nested benchmark completed
152 fits, including one selection-policy sensitivity, in 32.19 seconds. It verifies local feasibility, not the
regional research claim. Thirty-seven relevant tests, Ruff, dependency checks and
input/output receipt verification pass. All regional observation transfers and
source/daily checksums are verified. All matched regional inputs are assembled:
1,272,069 model and weather gauge-days each, plus 387 embedding/control rows.
No model/weather cells are missing; every spatial row has valid support. All
acquisition workers have finished. Regional feature assembly/audit is complete
(1,151,268 rows); the first full 152-fit regional-fold benchmark is complete.
Its 2021 test census has 17,637 eligible days across 51 contributing gauges;
two additional external gauges lack 2021 verification, explicitly recorded.
No GPU job, full regional fitting queue, Azure offload or other-chapter cleanup
was started; 74.8 GiB was free at verification, above the 50-GiB reserve.

The [design audit](reviews/limburg-dise-research-design-audit-2026-11-16.md)
supports retaining this study. Its corrections to model selection, calendar
exclusions, conventional references and population-aware scoring are now
[implemented](limburg-dise-audit-corrections-2026-11-16.md).
Daily-flow improvement remains distinct from flood-peak or warning improvement.

[Design](limburg-dise-research-design-2026-11-16.md) ·
[Preparation, audit and next work](limburg-dise-preparation-2026-11-16.md) ·
[Completed GEOGLOWS results](limburg-geoglows-first-results-2026-11-14.md).

[Completed spatial review and current input locations](limburg-dise-spatial-resolution-2026-11-16.md).

[Regional preparation and current benchmark](limburg-dise-regional-benchmark-2026-11-16.md).


Completion update — 17 November 2026: the first regional-fold benchmark finished
all **152 fits**, calibration and scoring in **39.3 minutes**. Input/output hashes
reverify; 303 metric records and the prediction/calibration tables are available.
No workers remain active. This is one 2021 fold; the results and capacity review
is now complete, with a fair capacity extension recommended before full scaling.


Results review — 17 November 2026: in the first 2021 regional fold, adding
AlphaEarth to the conventional model reduces all-day Wurm MAE by 23.1% and
external MAE by 2.9%; high-water gains are only 1.6%/1.7% and do not hold
consistently under measurement/selection sensitivities. High-water RMSE is worse
than raw GEOGLOWS. External gains persist in high-overlap views but vary by river.
Selected primary H+A/HA+E fits are uncapped; other selected and near-tied tuning
candidates hit the limit. A fair capacity check is recommended before full
scaling; no new run is launched. [Full review](limburg-dise-regional-results-review-2026-11-17.md).
