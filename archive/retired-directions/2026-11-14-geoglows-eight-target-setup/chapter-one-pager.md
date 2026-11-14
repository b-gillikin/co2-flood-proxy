# Limburg — assessing high water with alternative discharge information

Living research aid, updated 14 November 2026. Brian writes dissertation prose.

Latest audit: [comparison corrections identified](reviews/limburg-geoglows-code-design-audit-2026-11-14.md). Brian accepts dropping Eys from inputs and targets in both stages. The revised plan has seven targets (13,468 opportunities per stage); the eight-target preparation described below is retained pending correction/regeneration. No full run has started.

## Research Question(s)

When gauge observations are replaced by global modelled discharge, how well can
we assess developing high water, and can AI improve that assessment?

Compare reference versus alternative inputs on the same rivers/events, separate
simple calibration from hydrological learning and satellite representation value,
and consider European replication only after a specific Stage 2 conclusion.

## Motivation

Understand what high-water assessment capability requires current local gauges,
what a global discharge service can supply, and whether AI adds enough value to
justify its cost. This can inform monitoring resilience and agency investment;
it does not demonstrate improved warnings or avoided losses.

## Data

Held NL/DE discharge, measurement qualifications, RADOLAN rainfall and corrected
AnySat/Presto feature tables. GEOGLOWS hourly series for 2010–2025 are downloaded
for seven tributary reaches and both Meuse context sites. The full stream network
and catchment polygons were checked against our held catchments. Eys lacks an
independent model reach: retain it as a separate coverage case, never substitute
Geul flow. Observed future discharge remains the verification target.

## Method

Full 481-storm, eight-gauge, four-offset census: 15,392 opportunities per stage.
Observed versus GEOGLOWS inputs; replace all ten query/donor Q channels in Stage 2,
with Eys explicitly missing. Keep rainfall and targets unchanged. Compare
conventional analogues, persistence, prior-only monthly quantile mapping,
hydrology-only correction, matched raw-EO correction and encoder correction.
AnySat and Presto are separate task-specific comparisons; no ten-model sweep.

## Methodology

Paired retrospective input substitution, chronological annual fitting/tuning and
closed earlier-storm donors. Primary direct product comparison on seven mapped
targets; full eight-gauge pipeline accounting retained. Evaluate next-24h observed
Q, high-water strata, peak/timing errors, coverage and actual event selections,
using matched support and shared whole-year uncertainty. The archive has been
examined before: this is exploratory research, not a new blind confirmatory test.
GEOGLOWS reanalysis release lag is not replayed: no as-issued forecast claim.

## Findings / current status

Stages 1–2 inputs prepared and audited; full model comparison not launched.
No new performance finding. Setup caught a wrong nearest-reach match at Eys and
resolved the Wurm/Broicher Bach confluence. Earlier completed studies remain
preserved as prior evidence, not scores for the new paired comparison.

[Protocol and run commands](limburg-geoglows-stages12-protocol-2026-11-14.md) ·
[Active configuration](../config/limburg_geoglows_stages12_v1.json) ·
[Short account of earlier work](limburg-short-research-account-2026-11-14.md).
