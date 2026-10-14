# Cross-river analogue and retrieval checks

**Supporting controls and sensitivities — status updated 2026-10-14.**
Retain the matched benchmarks/ablations described in the
[evidence index](limburg-analogue-evidence-index-2026-10-14.md). Latest temporal
and spatial main results are reported separately; cohort scores are not a
single leaderboard.

Internal research aid; Brian retains dissertation prose writing.
User-authorized exploratory extension of the historical analogue experiment.
No new model, model training, data request or operational forecast claim.

## Questions and fixed comparisons

1. Can useful analogues be found when the query's own physical river is absent
   from the donor archive? Exclude its entire physical river, retaining the
   query's observed history. German Wurm and Dutch Worm are one river. This is
   a donor-availability scenario, not an ungauged or unseen-river forecast.
2. Where do conventional and learned retrieval disagree? Review every scored
   query, stratified by river and existing measurement-concern sensitivity.
   Extremal signed shape disagreements illustrate mechanisms to investigate;
   they are outcome-selected, not independent relevance-validation examples.
3. Does donor count matter, and does donor disagreement track response error?
   Compare fixed k = 3, 5, 10 distinct completed prior storms. Require at least
   20 eligible events and ten storms in every configuration so k does not
   change query eligibility. This additional minimum is a comparison condition,
   not a new chapter-wide gate. Use nested ranked donor prefixes. Report loss
   of eligible queries and pair availability scenarios on their overlap.
4. Do conventional signatures and TTM complement each other? One equal-block
   conventional + ordered-TTM combination, matched against conventional + raw
   history. The conventional columns are identical in both. Per-column
   median/IQR scaling and block RMS distance scales use eligible prior donors
   only. There is no tuned fusion weight or outcome-based reranking.

Dutch comparisons include conventional rain/Q, raw Q, matched raw/TTM state,
and the two fusion arms. Pooled NL/DE comparisons use Q-only inputs because
German rainfall is not held. The common 2018+ context sample additionally
compares original mean-TTM + AlphaEarth against area and gauge-identity
controls; it retains that backbone rather than silently changing two factors
at once. AlphaEarth's cross-river test is Dutch-only in this pass.

## Measures and inference

The six existing individual-donor response distances remain available, alongside
mean-donor peak error and ensemble-curve level RMSE. Lower is better. Shape,
level, peak and timing are separate targets; there is no composite winner score.
Paired contrasts use 9,999 intact query-storm resamples, with whole-storm year
blocks as sensitivity. These are unadjusted exploratory, fixed-archive intervals;
reused donor, model-pretraining and measurement uncertainty are not resampled.

Donor peak, curve and normalized-shape dispersion are computed from completed
prior responses. Spearman association with the query's corresponding error is
reported with 999 query-storm resamples. Positive association supports a useful
uncertainty diagnostic; it does not establish a calibrated confidence interval,
an abstention threshold or prospective warning skill. The donor peak range is
an empirical range, not a prediction interval. Shape dispersion and mean
individual shape error are partly geometrically related, so peak and ensemble
level associations are the stronger checks of practical uncertainty usefulness.

The rating-era p99 denominator uses retrospective records. Query responses
at hours 1–72 are evaluation targets only. No response rainfall, response
shape or query error enters retrieval. No event is discarded because its
chosen method performs poorly. Existing source-quality exclusions remain
separate sensitivity analyses.

## Execution

```sh
MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/78_cross_river_analogue_checks.py
```

Outputs live in ignored `results/basin_ai_cross_river_checks/`: query and
selected-donor census, eligibility, cohort/river summaries, paired intervals,
spread-error associations, disagreement census and twelve illustrative plots.
Raw provider data remain local. The manifest links source hashes, upstream
representation manifest and output hashes.

## Results

The run assesses 87,987 repeated query/configuration sets and 527,922 selected
slots. These are computational counts, not independent event sample sizes.

| Sample | All-river main / quality queries | Other-river main / quality queries |
|---|---:|---:|
| Dutch | 534 / 496 | 530 / 490 |
| Pooled Dutch–German | 760 / 722 | 757 / 712 |
| Common context | 264 / 247 | 264 / 247 |

Ten-storm availability removes one additional Dutch quality query, fourteen
pooled main queries and twelve context main queries relative to the earlier
five-storm runs. Cross-river exclusions then further reduce availability as
shown above. The original inclusion rules remain unchanged outside this check.

### 1. Other-river analogues

At five donors, ordered TTM + observed state improves mean individual-donor
shape RMSE over matched raw + state from 0.21218 to 0.20705 Dutch (2.4%) and
0.21020 to 0.20638 pooled (1.8%). Paired differences and conditional 95% query-
storm intervals are -0.00513 [-0.00885, -0.00173] and -0.00382
[-0.00703, -0.00061]. Year-block and measurement-quality sensitivities agree
on direction with intervals below zero. Magnitude and timing increments over
matched raw remain uncertain. Gains are heterogeneous: Dutch Wurm/Worm does
not improve on shape; pooled Geul and Voer do not improve.

Conventional Dutch rain/Q shape RMSE is 0.20630 versus TTM + state's 0.20705;
peak errors are 0.65765 and 0.65821. Their paired differences span zero. This
is not proof of equivalence or of learned superiority over the practical
benchmark.

Removing local-river donors generally worsens response matching. On identical
757 pooled queries, TTM + state peak error increases from 0.58966 to 0.64574:
+0.05608 [0.03228, 0.08141]. The cross-river scenario remains evaluable; this
loss quantifies the value of local examples instead of declaring transfer
impossible. Availability contrasts are saved separately on overlapping queries.

AlphaEarth's cross-river shape increment over original mean-TTM is -0.00194
[-0.00832, 0.00422]; peak increment -0.02163 [-0.08272, 0.04260]. Its mean
individual-donor peak timing mismatch improves from 11.670h to 10.286h:
-1.385h [-2.254, -0.601], supported by year and quality sensitivity and a
negative timing difference on all six physical rivers. Conventional timing is
10.252h, so this is an increment over TTM, not a new best-performing system.
The identity control produces identical donor choices to mean-TTM once the
same river is excluded; its one-hot contribution is constant across eligible
other gauges. This is an expected negative control, not proof of equivalence
between identity and geographical embeddings in general.

### 2. Actual disagreements

The complete disagreement census records each comparison, direction, source
concern flag, peak position, duration and observed rainfall context. At five
cross-river donors, Dutch TTM + state has closer shapes than conventional
retrieval for 264 queries, worse shapes for 264, and two ties. Pooled TTM versus
matched raw improves 396 queries, worsens 326 and ties 35. AlphaEarth versus
conventional improves 89 and worsens 175 context queries.

Twelve extremal signed-disagreement response figures were inspected with AI
assistance. Twelve companion figures show the actual 512-hour standardized
inputs as well as withheld responses; two were visually checked for layout
and alignment. This is not independent human labeling or a census of visually
verified mechanisms. Examples to guide Brian's interpretation:

- Gauge 11.Q.32, 2017-11-28: TTM + state retrieves sharper recessions than
  rain/Q, while rain/Q includes more delayed and repeated donor peaks. The
  input plot also shows closer alignment of a preceding pulse around -100h.
  This illustrates an available-history pattern, not a causal explanation.
- German gauge 2828300000200, 2014-10-09: cross-river TTM includes a donor with
  a more similar early peak and recession than the matched raw set, while
  secondary pulses still disagree. Full-river exclusion includes both national
  sides of Wurm/Worm.
- Gauge 11.Q.32, 2024-05-21: AlphaEarth has lower average normalized-shape
  error than rain/Q, but neither set captures the large rise near hour 71.
  A relative metric improvement can coexist with a substantial event failure.
- Gauge 13.Q.34, 2016-06-18: the largest Dutch cross-river disagreement against
  TTM carries an existing measurement-concern flag. It remains in the main
  results and is removed only in the documented quality sensitivity.

Some successful examples are rapid recessions, and some failures involve
prolonged tails or later pulses. These selected examples do not establish
basin mechanisms, calibrated skill or the prevalence of those patterns.

### 3. Donor count and uncertainty

Ten versus five donors improves mean-peak estimation while often slightly
worsening average individual-donor shape matching. For pooled cross-river TTM
+ state, peak error decreases 0.64574 → 0.59271: -0.05303
[-0.07372, -0.03296]. Shape RMSE changes 0.20638 → 0.20698:
+0.00060 [-0.00124, 0.00251]. For Dutch cross-river TTM, peak error decreases
0.65821 → 0.63299, but individual shape mismatch increases 0.20705 → 0.21027.
Conventional retrieval also benefits from more donors. This is principally
an averaging-versus-exemplar-quality trade-off, not a gain uniquely due to AI.

Donor spread has modest positive association with error. At five cross-river
TTM donors, curve-spread versus ensemble-level-error Spearman rho is 0.320
Dutch [0.199, 0.432] and 0.318 pooled [0.218, 0.423]. Peak-spread rho is 0.239
and 0.264. Within-river associations are heterogeneous: curve rho ranges from
0.135 to 0.486 Dutch, and -0.128 to 0.469 pooled. The pooled Geul association
is negative; Geleenbeek peak association is near zero. A single universal
confidence rule would overstate this result.

The practical research output can present a few close individual examples
and separately show a wider donor-set summary and disagreement. Preserve
all fixed-k results; do not replace the original five-donor comparison with
an outcome-selected optimal k. Empirical donor ranges are not calibrated
probabilistic intervals; their coverage rises mechanically with donor count.

### 4. Matched fusion

On the 530 Dutch cross-river queries, conventional + ordered-TTM gives shape
RMSE 0.20639 versus conventional + raw's 0.21246: -0.00608
[-0.00936, -0.00286]. It approximately matches conventional alone (0.20630;
paired difference spans zero), while donor peak timing mismatch improves
10.603h → 9.607h: -0.996h [-1.624, -0.376]. Timing direction improves on all
six rivers and survives the quality and year sensitivities. This is closer
donor timing, not an additional hour of operational warning lead time.

The smaller context archive reverses that timing advantage: fusion-TTM is
1.405h worse than conventional and 1.385h worse than matched raw fusion.
Both storm and year intervals support the adverse direction. On exactly the
same 264 query IDs, retaining the full Dutch donor archive gives fusion timing
9.929h versus conventional 10.290h; restricting to the context archive gives
11.658h versus 10.252h. Candidate composition and prior-pool scaling both
change, so this is an archive-availability diagnostic, not causal isolation
of any single old event or of time drift. The common-query archive table
makes this limitation explicit.

## Working recommendations

Keep ordered TTM + observed state as a supported temporal candidate, retaining
matched raw and conventional controls. Retain AlphaEarth as a limited context
comparison: there is cross-river timing evidence beyond identity, but no clear
shape or magnitude advantage over the practical benchmark. Do not tune weights
to manufacture one. Keep fusion as an exploratory complementarity result,
with the archive-dependent limitation reported rather than choosing the
favorable period alone.

For the existing research-aid presentation, distinguish close exemplars,
mean response estimates, donor disagreement, measurement provenance and
missing archive coverage. These results support that distinction without
adding a dashboard, a new model, fine-tuning or additional data requirements.

The expanding prior-pool median is retained as a magnitude benchmark in
`historical_median_intervals.csv`. Ten-donor pooled all-river TTM peak error
is 0.55567 versus median 0.58445; its storm interval barely excludes zero,
but the year interval and quality sensitivity span zero. Matched raw + state
has slightly lower point error (0.55478). Cross-river ten-donor TTM is 0.59271
versus median 0.59383, with an interval spanning zero. More donors improves
estimation relative to five without establishing an AI-specific magnitude
advantage or a robust win over the historical median.

## Verification and reproduction

- 115 tests pass, including cross-national physical-river exclusions,
  selected-prefix scoring and equal conventional inputs in fusion controls.
- Default engine reproduces all 534 original R0 queries; 26 original five-
  donor control configurations replay on their current eligible overlaps.
- All nested prefixes, distinct donor storms, completed prior outcomes,
  physical-river exclusions and measurement-quality exclusions verified.
- Five selected retrieval configurations across every cohort and both
  sensitivities rerun from the held inputs, reproducing all donor IDs,
  storm IDs, ranks and distances (absolute tolerance 1e-12).
- All 15 scientific CSV hashes verified; five additional audit tables
  reproduce exactly. The 1,472 primary paired interval rows are separately
  rederived from the saved query census. All resampling draws are finite.
- All twelve response illustrations and the donor-count summary figure
  inspected with AI assistance; two input-history figures checked visually.
  Remaining input-history figures are generated and available, not claimed
  as individually inspected. No independent human-review labels fabricated.

`--audit-existing` verifies hashed retrieval outputs and rederives the paired
availability, median-benchmark, archive-overlap, within-river uncertainty and
original-control checks. The manifest retains the original retrieval source
hash and adds the audit source hash. This avoids claiming that a postprocessing
rerun independently repeated every retrieval configuration. Local
`retrieval_replay.json` and `reproduction.json` record the additional checks.
Repository lint, changed-Python formatting and whitespace checks pass.
