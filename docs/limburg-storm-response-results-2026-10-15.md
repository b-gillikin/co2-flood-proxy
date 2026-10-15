# Storm-response census: three linked analyses

2026-10-15. Internal results and interpretation aid for Brian, not dissertation
prose. Implemented in scripts 92–94. Examples do not substitute for the census.

## Execution and population

The [initial specification](limburg-storm-response-design-2026-10-15.md)
implements all three paths from the [literature review](reviews/limburg-event-insight-literature-review-2026-10-15.md):
event divergence, conditional peer-gauge usefulness, and repeat rain before
recovery. Existing analogue, p99 and threshold results remain unchanged.
This is an exploratory explanatory extension, not an operational forecast.

Primary catalogue: 468 qualifying rainfall episodes across 2010–2025, six
Dutch catchments defining regional storms and eight NL/DE response gauges.
There are 3,744 storm–gauge rows; 3,491 have complete, stable-period,
within-domain outcome windows. Of those, 2,292 do not exceed p99 during the
72h response. This does not prove that no earlier within-storm crossing occurred.
Missing/censored cases remain inventoried. Quality sensitivity additionally
removes documented calibration, July 2021 and German provisional-period concerns.

The 24-dry-hour sensitivity has 461 qualifying episodes, 3,688 rows and 3,336
exact numeric windows. Its population changes: merging also allows some
formerly sub-10mm episodes to qualify. It is not an identical paired cohort.
Representation arms always use matched queries/donors within each catalogue.

## Refinement after inspecting actual cases

The initial matcher used episode rainfall amount, intensity, duration, spatial
wet-area fraction and season. Its actual pairs sometimes represented different
rainfall phases or subsequent weather. The main forcing control was therefore
expanded to include first-six-hour rainfall and response-window rainfall
amount/intensity. The original `rain_episode` arm remains in the final
comparison. Initial artifacts and code snapshots are retained locally under
`episode_matching_development/` in both output directories.

This is an outcome-informed, hydrologically motivated refinement, not an
untouched validation or prespecified discovery. Script 93 names it explicitly.
Regression/peer comparisons also include early rainfall. No foundation
checkpoint, neural weights or model family was selected for a better result.

## 1. Individual events and divergence

Among 2,990 complete-history matched queries from 446 storms:

| Matcher | Mean absolute error of subsequent peak increment, own-era p99 units |
| --- | ---: |
| Episode rainfall, initial benchmark | 0.40563 |
| Rainfall including early phase and response-window rain | 0.36846 |
| Same rainfall plus initial river state | 0.38734 |
| Rainfall/state plus standardized raw history | 0.41664 |
| Rainfall/state plus frozen ordered TTM history | 0.40693 |

The storm-balanced episode-minus-window error difference is +0.03762
(year-block 95% interval +0.02779 to +0.04718). The 24h-separation direction is
similar: +0.01916 [+0.01199, +0.02956]. These are retrospective comparisons
conditioned on realized rain, not forecast skill. Table means weight gauge
queries equally; intervals first average differences within regional storms.

TTM beats raw-history matching by -0.01076 [-0.01673, -0.00398], also under
strict quality (-0.00982 [-0.01608, -0.00336]) and 24h separation (-0.00939
[-0.01761, -0.00285]). It remains worse than the strengthened rainfall matcher.
Adding state to this fixed distance also worsens average retrieval. Neither
result establishes that physical initial state is irrelevant: a conditional
association and this particular donor-selection distance are different estimands.

**Eys, 26 June 2020 versus 22 June 2023:** episode rainfall is 25.32 versus
22.77 mm, but the first six hours contain 23.62 versus 0.00 mm. At the regional
six-hour landmark, the 2020 local response is already receding while the main
2023 local rain has not arrived. Initial Q/p99 is similar (0.102 versus 0.113),
but the events occupy different local rainfall/response phases. Antecedent 72h
rain also differs (0.083 versus 3.918 mm), and the 2020 regional episode is local
while 2023 is broad. These observations do not uniquely identify soil moisture
or explain the entire peak difference. They show why the regional clock and
similar rainfall totals alone do not ensure comparable hydrological phase.

**Mesch, 8 June 2022 versus 15 May 2024:** episode rain is 18.84 versus 21.19 mm,
but next-72h rain is 3.79 versus 55.27 mm. Treating these as equivalent forcing
would misattribute substantial subsequent-weather differences to river state
or representation failure. All underlying curves and flags are available.

These are outcome-selected diagnostic illustrations, not independent validation.
They diagnose the new storm-centered comparison; they do not establish the
cause of all earlier p99-based analogue failures.

## 2. Relationships between tributaries

All 56 directed gauge pairs use expanding prior-year archives, matched rows
and fixed-ridge arms: target information, added peer rainfall, then added peer
initial flow/rise. There are 87,981 arm-level conditional hindcasts and 1,128
fold records. Training responses crossing the test year are purged. Peer
eligibility concerns its used inputs, not unused future Q. Realized rainfall
is explicitly conditioned on; these are not deployable forecasts.

Adding peer state after peer rainfall increases pooled absolute error by
+0.00536 [+0.00258, +0.00849], averaging pairs within storm before year resampling.
Broad storms: +0.00222 [-0.00060, +0.00495]; local storms: +0.01120 [+0.00170,
+0.02518]. These subgroup intervals do not themselves test a regime interaction.
All pair/regime estimates, including unfavorable ones, remain available; searching
those many cells for favorable intervals would not establish a new neighbour.

The 24h pooled main contrast remains unfavorable (+0.00492 [+0.00181, +0.00778]);
strict quality is near zero (+0.00032 [-0.00279, +0.00304]). There is no robust
generally useful peer-state increment under this setup. That does not establish
that network relationships are absent: this tests information conditional on
rainfall/local state, not unconditional synchrony or verified routing. No travel
time, confluence amplification or national treatment effect is claimed. Exact
Wurm station order remains unasserted in the curated graph.

## 3. Progression versus recovery

The main ledger contains 5,096 repeat pulses, including unknown recovery states.
The exact known-state pulse analysis has 2,254 records from 338 storms (strict
quality: 2,090/333). Recovery is an operational proxy: remaining above half the
initial six-hour rise when that initial rise exceeds 0.02 p99. It is not a
measurement of soil storage or a universal hydrological threshold.
The label concerns excess flow immediately before the pulse, not proof that
the river never crossed the half-rise level earlier. Pulse regressions use
the common exact-72h parent cohort, so they are not a maximal census of every
otherwise available 24h pulse response. All detected pulses remain inventoried.

The storm-level before-recovery indicator has a positive conditional association
with the 72h increment: +0.11593 [+0.00956, +0.21448], or +0.10865 [+0.00422,
+0.21067] under strict quality. The temporally more specific rise *after* a repeat
pulse is uncertain and slightly negative: -0.02771 [-0.08696, +0.02697]. With
24h storm separation it becomes +0.05924 [+0.00152, +0.10908]; the quality
version also changes sign. There is not a stable demonstrated repeat-pulse
mechanism. A repeat pulse within the storm-level outcome window can follow an
earlier peak, so its association must not be described as causing that peak.

Pre-rain flow is positively associated with later increment across specifications,
consistent with established state/wetness literature rather than a new physical
finding. The negative early-rise coefficient needs restraint: the outcome
subtracts landmark Q while early rise includes landmark Q. Adding early rise
back to the outcome algebraically shifts its coefficient by +1. This is not
evidence that an early rise physically protects against a later flood.

## Contribution and remaining limits

This pass diagnoses when comparisons can be misleading: phase and subsequent
forcing can dominate an apparently similar rainfall total. It supplies a broad,
nonresponse-inclusive test of conditional inter-river information and a currently
unstable recovery hypothesis. It does not establish a new flood mechanism,
reliable escalation classifier or general AI advantage.

No new data request, neural weight training, RAG, hydraulic solver or simulated
storm is added. AlphaEarth remains existing landscape context rather than an
hourly state measurement. Current Dutch warning thresholds remain supporting
reference levels from the separate native-resolution analysis, not new
inundation observations. The 1 km/hour radar uses the existing end-hour labels;
RW accumulation ends ten minutes before its rounded label, limiting subhour
timing interpretations. Catchment delineations retain their existing provenance.

## Reproduce and inspect

From the chapter root, using the existing foundation environment:

```bash
.venv-foundation/bin/python scripts/92_build_storm_response_catalogue.py
.venv-foundation/bin/python scripts/93_analyse_storm_responses.py
.venv-foundation/bin/python scripts/94_audit_storm_response_analysis.py

.venv-foundation/bin/python scripts/92_build_storm_response_catalogue.py --dry-hours 24 --output-dir results/storm_response_24h
.venv-foundation/bin/python scripts/93_analyse_storm_responses.py --output-dir results/storm_response_24h
.venv-foundation/bin/python scripts/94_audit_storm_response_analysis.py --output-dir results/storm_response_24h
```

Locally, GeoPandas required valid `PROJ_DATA` and plotting a writable
`MPLCONFIGDIR`; no upgrade was needed. Inputs, code, checkpoint and outputs are
hash-bound. The independent audit reconstructs every main matching score
(47,847), donor slot (238,109), peer prediction (87,981), paired interval (686),
response row (3,744) and repeat-pulse record (5,096). Maximum numerical discrepancy
is below 3e-14. The 24h audit also passes: 46,517 matching scores, 85,497 peer
predictions and 686 intervals; maximum below 5e-14. Association point estimates
are checked with a separate weighted least-squares solver; coefficient bootstrap
intervals are not independently refitted draw by draw. No coefficient bootstrap
draw is rank-deficient in these runs.

All 180 chapter tests pass, including scientific checks on missing-hour storm
boundaries, complete outcomes, completed prior donors, outcome-free distances,
training-only scaling, pulse uncertainty, dependence and rainfall-phase matching.
Two static figures were AI-inspected; no independent human validation is claimed.
Year intervals use 1,999 draws and remain exploratory/model-conditional; they do
not capture all researcher choices, archive uncertainty or multiple pair searches.
Rerunning the main analysis reproduced all 17 scientific CSV/Parquet outputs
byte for byte (`reproduction.json`); the independent audit passed again afterward.
All 46 output hashes in the prior distribution-analysis manifest also remain
unchanged. No older empirical output was regenerated or overwritten.

Ignored local outputs: `results/storm_response/` and `results/storm_response_24h/`.
Start with `case_browser.html`, `illustrative_pair_evidence.csv`,
`matching_summary.csv`, `paired_intervals.csv`, `peer_pooled_intervals.csv`,
`conditional_coefficients.csv` and `audit.json`. Source records and curve
browsers are not published to Git.
