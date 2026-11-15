# Limburg — high-water assessment with alternative discharge information

Living research aid, updated 14 November 2026. Brian writes dissertation prose.

## Research Question(s)

When gauge observations are replaced by global modelled discharge, how well can
we assess developing high water, and can AI improve that assessment?

Compare information sources on the same rivers/events; distinguish hydrological
learning, raw satellite context and encoder value. European replication remains
a separate later stage, tied to a specific finding or limitation.

## Motivation

Identify what high-water assessment capability needs current local observations,
what a global discharge product supports, and whether AI adds enough value to
justify its cost. This can inform monitoring resilience and agency investment;
it does not establish operational warning improvement or avoided losses.

## Data

Held NL/DE discharge and provider measurement qualifications, common RADOLAN
rainfall, and verified Presto/AnySat raw and encoded context tables. GEOGLOWS
hourly 2010–2025 series are downloaded for seven tributary reaches and both Meuse
context sites, with stream topology and contributing-polygon checks. Eys has
been dropped from both targets and predictors; its original data are preserved.
Model outlets approximate gauge sections and are not identical physical locations.

## Method

All 481 held regional rainfall episodes × seven gauges × four issue offsets:
13,468 opportunities per stage. Compare observed and GEOGLOWS Q inputs, keeping
rainfall and observed next-24h verification unchanged. Nine active Q feeds in
both stages. Conventional analogue mean/median, persistence, local flow-duration
calibration, hydrology-only correction, matched raw-EO correction and encoder
correction. Core encoders: Presto and AnySat, used separately with existing data.

## Methodology

Paired retrospective source substitution; closed earlier-storm archives,
chronological annual fitting/tuning, identical training/validation opportunities
across correction arms and train-only missing-feature treatment. Missing raw EO
falls back to the causal hydrology policy; missing encoder input falls back to
raw. Evaluate high-water MAE, the full census with fallbacks and joint high-water/
EO-supported results, plus peaks, timing and actual analogue selections. Shared
year bootstrap retains the declared site population and counts undefined draws.
Historical data have informed prior work: this is exploratory, not a blind new
confirmatory dataset. Retrospective GEOGLOWS publication delay is not replayed;
there is no as-issued/live-fallback claim.

## Findings / current status

All six setup-audit corrections implemented. Seven-target inputs regenerated,
full-input audit passed, 57 relevant tests passed, dependency checks clean.
Full comparison fitting launched on 14 November 2026 at 19:09 America/New_York,
with automatic review after fitting. No performance findings are available yet. Earlier
research and the superseded eight-target setup remain preserved.

[Corrected protocol and commands](limburg-geoglows-stages12-protocol-v2-2026-11-14.md) ·
[Active configuration](../config/limburg_geoglows_stages12_v2.json) ·
[Audit resolution](reviews/limburg-geoglows-audit-corrections-2026-11-14.md) ·
[Earlier research account](limburg-short-research-account-2026-11-14.md).
