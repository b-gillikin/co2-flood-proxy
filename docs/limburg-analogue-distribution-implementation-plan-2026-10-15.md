# Implementation plan: distributions from the existing Limburg analogues

Date: 2026-10-15. Internal analysis plan for Brian; Brian writes dissertation
prose. This implements the smallest extension recommended by the
[scientific review](reviews/limburg-analogue-forecasting-review-2026-10-15.md).
Planning only: no new empirical result or model execution in this document.

## Purpose and scope

Answer: do the retrieved historical events provide a better distribution of
subsequent discharge than the eligible historical archive, and how reliable
are their uncertainty ranges?

Use the full existing eligible census, saved rankings and held observations.
The main target is the distribution of hourly discharge over response hours
1–24, with readouts at hours 6, 12 and 24. This extends the present retrospective
analogue question. Full-era p99 normalization and finalized records remain
explicit limitations. A past-only forecast reconstruction is a separately
decidable extension, not a dependency of this work.

## 1. Bind the run to the existing evidence

Create `scripts/90_evaluate_analogue_distributions.py` and a dated run manifest.
Use the canonical script-84 cross-border run rather than mixing donor rankings
from successive exploratory runs:

- `results/basin_ai_cross_border_completion/selected_donors.csv`;
- its assessments, coverage tables, manifest, and the prepared cohort inputs
  identified by that manifest;
- the corresponding held normalized response curves. The independently
  replayed `p99_72/response_p99.parquet` from script 88 can supply curves after
  checking event identities, scales and equality with the original source.

Verify the relevant input/output hashes and record source revisions. Do not
rerun a historically pinned script merely because its source has since been
extended compatibly. Bind this analysis to actual saved inputs and outputs.

Reconstruct eligible archives from the original cohort definitions, chronology,
measurement sensitivity and physical-river restrictions. Match each saved
query's candidate-event and candidate-group counts. Reconstructing archives
is necessary because selected-donor tables alone do not contain every eligible
unranked event.

## 2. Fix cohorts and comparison priorities

Primary setting: pooled NL/DE donor policy, all rivers, main measurement
treatment and five donors where available. Existing ten-donor, other-river
and quality settings are supporting comparisons. Do not repeat domestic and
foreign archive experiments or the p95/five-day catalogues in this extension.

| Cohort | Comparisons | Interpretation |
| --- | --- | --- |
| Discharge histories | Raw history, raw/state, ordered TTM/state; each against its eligible archive | Primary learned temporal increment: TTM/state versus raw/state |
| Rainfall-matched | Conventional R0 and the same temporal arms; each against that cohort's archive | Practical comparison with hydrological summaries |
| AlphaEarth/context | Temporal/state, plus area, identity, fixed-2017 and prior-year annual AlphaEarth | Geographic increment on the exact matched context population |

Use the archived names and settings, not newly generated features or models.
Save all donor sets and actual counts used. The context cohort does not gain a
new R0 arm: its controls already exist. The rainfall-matched R0 comparison is
reported separately; differing candidate pools must not be presented as an
identical-input context ablation.

Preserve all existing eligible queries, including fewer-than-five/ten donors.
Retain no-archive cases in coverage outputs without fabricating predictions.
Do not select an illustrative sample as the numerical evaluation population.
Use identical query IDs and candidate pools within each paired comparison.

Retain the inherited 72h response-availability/cohort rules for reproducibility,
although the new score uses the first 24h. State this restriction in the flow
table: the analysis does not claim to recover all cases with only 6–24h follow-up.
Changing to horizon-specific eligibility belongs to the separate forecasting
reconstruction, since it would also change donor availability and rankings.

## 3. Construct empirical distributions without changing retrieval

At every response hour, each selected donor contributes its existing Q/p99
value. Give selected donors equal weights summing to one. Keep the same donor
trajectories across hours; do not select a fresh set at each lead.

The generic reference includes every eligible prior event, with equal total
weight per regional group and equal event weights within each group. Rebuild
it separately for each cohort/scenario/measurement setting. Do not use an
event-count-weighted archive or the whole record including future events.

Preserve the existing own-era p99 mapping. For within-query scoring, multiplying
every donor and query value by the target gauge's p99 gives the equivalent
target-gauge discharge scale. Use Q/p99 for cross-gauge summaries and retain
m³/s summaries by gauge. No response-peak normalization enters these scores.

Carry existing current-discharge persistence as a point/degenerate-distribution
reference; it is not an uncertainty model. Keep its results separately labeled.
No new trajectory anchoring, weighting, training or recalibration is performed.

## 4. Score accuracy and diagnose uncertainty

Primary endpoint: each query's mean CRPS across hours 1–24, then the
event-weighted mean on the matched cohort. Lower is better. Report lead-specific
CRPS at 6h, 12h and 24h and the full lead profile; do not choose a favorable lead
after results. Compare paired differences rather than rank different cohorts.

For weights w summing to one, use the exact empirical-distribution score:

    CRPS = sum_i w_i |x_i - y| - 0.5 sum_i sum_j w_i w_j |x_i - x_j|.

Use a sorted, cumulative-weight implementation for large archives, independently
checked against the direct pairwise formula on small cases. Apply the exact
same target to selected donors and the group-balanced archive. Do not apply an
iid fair-ensemble correction automatically to selected, dependent neighbours.

Diagnostics:

- Empirical median absolute error and mean squared error, matching each point
  functional to its loss. Preserve existing trajectory and shape findings as
  context, without rerunning or combining them into a tuned score.
- Central 50% and 80% pointwise interval coverage, interval width, and fractions
  below/above the interval at 6h, 12h and 24h. Use the inverse weighted empirical
  CDF with an explicit tie/boundary convention for all methods.
- Report quantile discreteness and actual donor counts. Five-member empirical
  quantiles are coarse; advertised interval labels are targets to evaluate,
  not coverage guarantees. Pointwise intervals are not simultaneous trajectory
  bands. One-donor distributions remain scored and explicitly marked as such.
- Summaries by country, physical river and fixed actual-count categories
  1–4, 5–9 and 10 donors, with case/group counts. These are descriptive support
  checks, not subgroups searched for a winning claim.

Do not fit a calibration model. This pass diagnoses empirical reliability;
it does not guarantee conditional calibration or learn a refusal rule. Keep
sparse H1/H2/H3 results in the existing analysis rather than adding another
threshold probability task here.

## 5. Quantify uncertainty and inspect concrete cases

Use the existing seed 20261013 and 9,999 joint regional-group bootstrap draws,
with the existing year-block sensitivity. Resample all compared methods
together and retain their matched query sets. For a pooled NL/DE contrast,
use shared regional groups rather than independently resampling countries.
Report failures, undefined contrasts and group/year counts explicitly.

Primary contrasts:

- Ordered TTM/state minus raw/state, discharge-history cohort;
- Ordered TTM/state minus conventional R0, rainfall-matched cohort;
- Annual AlphaEarth minus temporal/state on the context cohort, accompanied
  by the existing area, identity and fixed-context controls.

Report method-minus-archive comparisons alongside these. Intervals remain
conditional on the held archive and exploratory development; group/year draws
do not remove uncertainty from reused donors, few catchments or provider errors.

Reuse the existing outcome-independent sentinel case IDs where they overlap
this run. Plot donor trajectories, the verification response, median and
pointwise ranges alongside the archive reference. Numerical results remain
a census; figures illustrate how spread and error relate. Label AI inspection
separately from Brian's independent human-review fields.

## 6. Validate implementation and reproduce the run

Add focused tests for:

- Hand-calculated weighted CRPS, unequal weights, ties, permutation invariance,
  degenerate distributions, and linear scaling between Q/p99 and m³/s;
- Sorted versus direct pairwise CRPS and weighted-quantile conventions;
- Group-balanced archive weights, including invariance to duplicating an
  identical group's event distribution;
- Correct hour indices 1–24, 6/12/24 readouts, matched queries and short/no
  archive reporting;
- Query-response perturbation changes scores but cannot change donor IDs,
  ranks, weights or archive construction;
- Candidate chronology, distinct selected groups and other-river restrictions.

Add `scripts/91_audit_analogue_distributions.py` to independently reconstruct
archive membership, weights, scores, count/coverage summaries and paired
contrasts from the saved rows. Check selected distributions against donor IDs
and source curves. Record input, code and output hashes plus all audit results.

Run relevant new tests and existing analogue consistency tests, then the chapter
suite and lint/format checks. Replay the saved run from its manifest and compare
deterministic scientific outputs. Audit results before interpreting numerical
differences; an implementation failure calls for correction, not dropping
unfavorable events. These are correctness checks, not statistical pass criteria.

## 7. Deliver evidence and interpretation aids

Write ignored outputs under `results/basin_ai_analogue_distributions/`:

- Query inventory/coverage and explicit reasons for unscored cases;
- Donor-set references and group-balanced archive membership/weights;
- Hourly and per-event CRPS and interval diagnostics;
- Matched country/river summaries, paired contrasts and uncertainty intervals;
- CRPS lead profiles, coverage-versus-width plots and sentinel illustrations;
- Run manifest, validation report and independent audit receipt.

Create a short internal results memo with the usable sample, observed effects,
uncertainty, calibration limits and links to the existing shape/trajectory
evidence. Update the evidence index and handoff after execution. Brian writes
all dissertation prose. Commit/push code, tests and internal documentation
after checks; keep source records, large outputs and credentials out of Git.

Interpretation is predeclared at the level needed here: a smaller CRPS supports
a better empirical distribution on this specified population; satisfactory
marginal coverage with very wide intervals is not useful precision; narrow
ranges with poor coverage indicate overconfidence. Better shape retrieval
without a distributional advantage supports a casebook interpretation. All
directions, including null and unfavorable outcomes, remain reportable.

## Separate possible extension

A genuine past-only prediction reconstruction would recalculate p99/selection
from earlier records, issue estimates before seeing follow-up availability,
use horizon-specific verification, and explicitly address trajectory anchoring
and finalized-data assumptions. It can use held data. This plan does not make
that additional implementation a requirement or silently add it to this run.
