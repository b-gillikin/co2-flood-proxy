# Limburg consistency audit before event-level interpretation

Internal research aid. Brian writes dissertation prose. No new model, data
request, fine-tuning, event exclusion or operational claim introduced.

## Finding

No material numerical mismatch was found. Independently reconstructing response
metrics, chronology, identities and candidate pools confirms the existing
retrieval results. The main remaining work is to establish what the analogues
add to understanding an event, rather than treating a similarity score as that
answer.

Script 79 checks 527,922 selected donor slots, 87,987 repeated score sets,
204 configurations, 6,023 candidate pools and 620,208 event-hours. These are
computational checks, not independent sample sizes. Fifty-four prepared input,
vector, receipt and model files and fifteen result CSVs are hash-verified.

## Fixed

1. **Replay provenance was incomplete.** Script 78 previously verified output
   hashes and then joined current inputs. It now verifies data/vector/model
   fingerprints before loading inputs or writing audit outputs, and records
   explicit input hashes. Its replay branch no longer builds or regenerates
   representation caches. Code revisions remain allowed and recorded; changed
   data requires a newly prepared run, not relabeling an old result as replayed.
   Once data are directly fingerprinted, updating upstream code metadata alone
   does not block an audit. Legacy runs use their original upstream manifest
   to recover that binding.
2. **Comparison invariants needed direct checks.** Saved-result validation now
   checks unique query scores/ranks, matching candidate counts, storm counts,
   observed peaks and median baselines across arms/k, completed donor responses
   and exclusion of same-group donors. Unknown physical-river identities cannot
   silently pass a cross-river exclusion.
3. **Unused weather coverage was an eligibility requirement.** Removed it from
   the shared rainfall/discharge comparison. All 724 held Dutch episodes have
   complete weather, so existing sample sizes and results do not change. No
   new weather acquisition is required for these representation comparisons.
4. **Live wording lagged behind the experiment.** The active plan now identifies
   fusion as executed; earlier mean-readout results are labeled historical.
   Retrieval comments explicitly acknowledge retrospective p99 scaling.
   The inventory distinguishes reviewed illustrations from unfinished event-
   level interpretation.
5. **Metric meaning needed an explicit distinction.** A regression test now
   separates the mean of donor peaks from the peak of the mean donor curve,
   and individual-donor timing mismatch from a predicted peak-time error.
   Column names remain stable for reproducibility; meanings are below.

## Scientific tightening for the next pass

| Issue | Evidence and implication | Action using held data |
|---|---|---|
| Analogue value versus own history is not yet established | R0 itself retrieves analogues; the expanding median does not use query history. Neither is an own-history-only reference. | State what was already apparent at cutoff, then what donors added. Use an explicit history-only reference, such as persistence, if claiming quantitative added value over history alone. This audit does not fit it. |
| The Q-only population is narrower than necessary | 58 primary-usable Dutch episodes have complete 512h Q histories but fail shared rainfall coverage; 56 also have complete 72h responses. None is excluded solely by weather. | Keep the matched rain/Q benchmark intact and include eligible extra episodes in a separate broader Q-only event census. Their inventory is saved; frozen TTM vectors still need extraction before scoring them. |
| Comparison cutoffs are not universal research gates | The shared Dutch sample has 558 scorable events and the pooled sample 795, before requiring 20 prior events/ten groups for the fixed-k checks. The resulting main comparisons use 534/760 queries. | Keep those matched comparison results, but record earlier events and limited donor availability in the event census. Shorter archives or unavailable analogues are findings about coverage, not a reason to discard the event or request more data. |
| A response window is not the complete flood | Of 760 pooled main queries, 329 peak at response hour 1, eight at hour 72, and 28 remain above p99 at hour 72. Dutch counts are 215/7/22 of 534. | Distinguish early recession, later peak and unfinished high water when interpreting cases. Do not call 72h above-p99 counts total flood duration. These positions do not invalidate otherwise valid events. |
| Shape improvement is not amplitude accuracy or event success | Shape normalization divides each held-out curve by its own response maximum; the known May 2024 illustration still misses a large late rise. | Show shape, level/magnitude and timing together. Held-out normalization is evaluation only; it does not enter donor ranking. |
| Median and selected donors have different storm weighting | Median uses every eligible gauge episode; retrieval selects one event per onset-linked group. The pooled all-river archive averages about 3.47 eligible events per group. | Label the existing median event-weighted. If a superiority claim depends on it, also check a group-balanced reference before attributing the gain to AI. Existing benchmark results remain reported. |
| “Storm” is an operational grouping label | Groups use 72h single-linkage of observed onsets; longest span is 176h. They are not independently verified meteorological storms. No held groups span calendar years. | Describe them as onset-linked regional episode groups. Keep the existing grouping for donor deduplication and conditional resampling; no new storm catalogue is required. |
| Country and river diversity are not interchangeable | Germany contributes two Wurm gauges; Wurm/Worm is one physical river across the border. Both main cohorts have six physical rivers. | Discuss cross-border applicability/provenance, not causal Dutch-versus-German differences or eight independent river systems. |
| Uncertainty remains conditional | Donor disagreement moderately tracks error, with river exceptions; reused donors, observation error and representation-development choices are outside the query resampling. | Present disagreement as a cue, source concerns separately, and failures explicitly. Do not turn the correlations into calibrated probabilities or a universal refusal rule. |

These are interpretation and comparison choices, not conditions for stopping
research. No additional provider data is needed to perform the event-level
work with the existing cohort. The broader Q-only census can proceed without
rainfall for its additional events; rainfall-dependent comparisons retain
matched samples.

## Metric dictionary

| Saved measure | What it measures | What it does not measure |
|---|---|---|
| `analogue_prediction` | Mean of individual donor maximum Q/p99 over response hours 1–72 | Peak of the mean curve; physical discharge at the query site; operational forecast |
| `mean_donor_peak_absolute_error` | Absolute difference between that mean and the query's response maximum, in p99-ratio units | Mean individual donor error; absolute error in m³/s |
| `ensemble_curve_level_rmse` | RMSE between mean donor Q/p99 curve and observed query response | Independent donor similarity; inundation depth |
| `mean_peak_scaled_shape_rmse` | Mean individual-donor shape mismatch after each response is divided by its own maximum | Peak magnitude accuracy; proof that a useful assessment was learned |
| `mean_peak_time_difference_h` | Mean absolute difference between each donor's first response maximum and the query's, in hours | Error of an estimated peak time; warning lead time |
| `mean_high_water_duration_difference_h` | Difference in observed hours at or above own-era p99 within the 72h window | Total flood duration; time above a historical official warning level |
| `mean_excess_area_difference_p99_h` | Difference in summed positive Q/p99 excess above one, in p99-hours | Flood volume or monetized damage |
| `mean_terminal_peak_ratio_difference` | Difference in last-24h mean / response-peak ratio | Measured return to normal after the full event |
| `peak_range_contains_query` | Whether the query response maximum lies inside the selected donor extrema | Calibrated prediction-interval coverage |

Events are discharge-defined p99 episodes. German stage helps quality/admissibility;
these outputs are not harmonized water levels, observed inundation or historical
warning-threshold crossings. The delivered records can contain retrospective
provider revisions, and full-era p99 uses later observations. “At cutoff” here
means the observed history window in an archival analysis, not proof that the
finalized values and model assets were available to an operator on that date.

## Reproduction

```sh
MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/78_cross_river_analogue_checks.py --audit-existing

MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/79_audit_analogue_consistency.py
```

Independent audit outputs: `results/basin_ai_consistency_audit/`. All six pair
metrics and aggregated peak, curve and spread metrics agree within 1e-12.
Candidate identities/counts and event-weighted medians are independently
reconstructed. UTC timestamps equal onset + relative hour; every event has
584 unique hours spanning -511 through +72. Input fingerprints and outcome
artifacts agree; no material empirical result or earlier event-review decision was
changed. Round-trip CSV reads preserve floating-point precision in replays.

The audit also reconstructs all 906 standardized raw histories from the held
512h windows, verifies the 192/1536-dimensional finite normalized TTM vectors,
and confirms prior-year context for all 304 eligible AlphaEarth events. Norms
of stored float32 vectors are accumulated in float64; their maximum ordered-
vector deviation from one is 2.48e-7. No vectors are renormalized or reranked.
All selected donors are independently checked for membership in their actual
eligible pools, including source-quality and full physical-river exclusions.
Country and measurement flags match the event metadata.

Validation: 120 tests pass; the five focused cross-river tests also pass after
the final replay-metadata adjustment. Repository lint, changed-Python formatting
and whitespace checks pass. No additional data or event-level experiment was
run. Additional Q-only episodes and shorter archives remain explicitly pending
interpretation rather than silently labeled analyzed.
