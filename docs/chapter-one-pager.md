# Limburg — satellite-informed discharge reconstruction

Living research aid, updated 16 November 2026. Brian writes dissertation prose.
Independent DISE-inspired adaptation accepted; local preparation/benchmark
completed, full regional comparison not launched.

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
regulation information remains unresolved. Seven local gauges represent five
river groups; Eys remains excluded and the Meuse is not added as a new target.

CAMELS-DE-1h metadata and selective time-series access are verified. The bounded
inventory contains 286 donor candidates, 49 reserved external candidates in
Ahr/Erft/Sieg and 52 overlap-review cases. These are not final independent or
quality-verified training/test populations. Regional reach matching, source-clock
checks and selected-series/descriptor acquisition remain.

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
chronological test years 2021–2025 and nested river-group withholding. All three
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
complete observed/model pairs. A complete local held-Wurm 2021 nested fitting
benchmark ran 76 fits in 13.44 seconds. It verifies local feasibility, not the
regional research claim. Thirty relevant tests, Ruff, dependency checks and
input/output receipt verification pass. About 79.3 GiB remains free; no GPU job,
full regional queue, Azure offload or other-chapter cleanup was started.

[Design](limburg-dise-research-design-2026-11-16.md) ·
[Preparation, audit and next work](limburg-dise-preparation-2026-11-16.md) ·
[Completed GEOGLOWS results](limburg-geoglows-first-results-2026-11-14.md).
