# Event-definition robustness: execution plan and fixed choices

Internal analysis aid, not dissertation prose. Authorized by Brian on 2026-10-14.
Two one-factor checks; no threshold search, new model, data request or training.

| Run | Event percentile | Local crossing-link interval | Changed factor |
| --- | ---: | ---: | --- |
| baseline | 99 | 72h | None; reproduce held script-84 pooled results |
| percentile | 95 | 72h | Event-selection percentile only |
| separation | 99 | 120h | Local episode linkage only |

Support: [Tuel & Martius 2021, §3.1](https://nhess.copernicus.org/articles/21/2949/2021/)
explicitly compare 95th and 99th daily-discharge percentiles. The local
[Geul study, Tsiokanos et al. 2024, §2.3.1](https://hess.copernicus.org/articles/28/3327/2024/)
uses p99 daily maxima and five-day separation. Ours adapts the existing hourly
crossing-link algorithm to 120h; it does not reproduce their daily-peak method.

Keep the reference **p99 normalizer**, model weights/readout, 512h histories,
72h verification response, regional 72h grouping rule, prior completed archives,
river identities, quality rules, equal block weights and 5/10 donor reporting
fixed. Recompute event onsets and resulting regional groups in each catalogue;
never transfer a stale storm ID to a changed event population. This isolates
selection/grouping effects from a trivial change in error units. Duration and
excess endpoints remain above p99, explicitly not above p95. The p95 catalogue
asks whether the main analogue conclusions extend to an earlier/broader
high-water selection; its scores are not a same-event causal comparison.
The official H1/H2/H3 definitions and completed H1 analysis do not change.

Rebuild every candidate episode from held Dutch and German hourly observations,
using the same era rules and onset-censoring logic. Preserve censored cases in
the catalogue; exact-onset/model-input availability is separate. Preserve the
held Dutch primary-eligibility convention (exact onset and 72h preceding rain
available), including its legacy effect on the Q-only comparison; do not
silently correct that convention inside this sensitivity. German provenance
and exact-response eligibility remain literal. No input-history repair is
introduced: these are sensitivities to script 84, not to the newer H1 input
repair. All eligible cases are used, not sampled.

Run the pooled Q-only, rain-matched and geographic-context comparisons, with
all-river/cross-river and main/quality results. Country breakdowns retain NL/DE
composition. Retain the exact same temporal, conventional and context-control
arms as the corresponding script-84 cohorts. Domestic/foreign archive-policy
experiments are not repeated: archive policy is held pooled to isolate the
requested factors. Reuse frozen vectors only when event ID and original
512h history match; extract ordered TTM vectors for new input histories with
the same pinned backbone. No head training or use of future responses.

Report full-cohort results, common-onset subsets and coverage/event-membership
changes separately. Common-onset comparisons still have changed donor archives,
so they isolate some composition effects, not the whole selection mechanism.
Use paired model differences within each run with 9,999 intact regional-group
and year resamples, seed 20261013. Do not subtract raw errors across populations
and label that a performance gain. Preserve unfavorable results and any changed
conclusions; this is outcome-informed exploratory robustness, not confirmation.

Checks: baseline catalogue, p99 scales, eligibility, flags, signatures and frozen
histories must match held preparation; baseline scores/donors reproduce the
held pooled outputs. Synthetic tests cover threshold shifts, exact linkage
boundaries, censored-first chains, fixed normalizers and unchanged response
windows. Independently reconstruct every selected pair/set metric and candidate
chronology; hash all sources, input data, vectors and results. Replaying the
saved outputs verifies summaries and paired contrasts without reranking donors.

Execution optimization: cache the exact lexicographically sorted unique rows
of each frozen non-robust vector block. Each query selects only its eligible
prior row codes before calculating its original RMS scale. Robust state blocks
retain the original per-query calculation. This removes repeated wide-row
sorting without using later events to set scales. Duplicate, robust-state and
future-outlier tests require bitwise-identical distances. Rerun the entire
baseline through the cached implementation and require identical donor IDs,
distances and all scored metrics before interpreting the alternatives.
