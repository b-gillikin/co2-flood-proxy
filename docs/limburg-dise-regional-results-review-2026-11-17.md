# First regional DISE fold: results, spatial strata and tree limits

17 November 2026. Internal results review for Brian; not dissertation prose.
No model was fitted, reselected or changed during this review. The completed
2021 benchmark and its full input/output identities remain frozen.

## Assessment

**There is a substantial all-day Wurm improvement from AlphaEarth in this fold,
but no robust added high-water skill yet.** The external all-day benefit is small
on average and concentrated in Erft. Some of the most consequential supplied
high-flow values become less accurate after correction than in raw GEOGLOWS.
Those distinctions matter more than a single aggregate ranking.

The review independently reconstructs 85 central metric rows using gauge means,
then river means, matching the stored scores to numerical precision. It checks
all three seed predictions against their saved ensemble, reviews every selected
configuration and all capped tuning fits, and inspects the river-effect and
July 2021 figures. No new experiment, threshold search or model family is added.

## Primary comparison

H+A is model/weather history plus conventional catchment attributes; H+A+E adds
the fixed AlphaEarth descriptor. Values below are balanced MAE in **mm/day**;
positive percentage reductions improve on H+A. These are descriptive paired
results on identical eligible rows, not confidence intervals.

| Population | H+A | H+A+E | MAE reduction |
| --- | ---: | ---: | ---: |
| Wurm, all days (1,089 gauge-days) | 0.563 | 0.433 | 23.15% |
| Wurm, high water (21 gauge-days) | 6.324 | 6.225 | 1.57% |
| Wurm, inherited strict-clean high water (14 gauge-days) | 3.622 | 3.651 | −0.78% |
| External rivers, all days (16,548 gauge-days) | 0.507 | 0.493 | 2.90% |
| External rivers, high water (274 gauge-days) | 7.068 | 6.947 | 1.71% |

For context, raw GEOGLOWS all-day MAE is 0.724 at Wurm and 0.643 externally.
The combined correction reduces those errors by 40.3% and 23.4%, respectively;
those are **total correction benefits**, not the incremental AlphaEarth effect.

The all-day Wurm benefit is not uniform across its three nested gauges:
Rimburg improves 20.2%, Herzogenrath 1 improves 35.2%, and Randerath worsens 9.7%.
On high-water days, only Herzogenrath improves; Rimburg and Randerath worsen.
Three gauges on one river do not provide three independent regional replications.

## External river differences

| Reserved system | All-day AlphaEarth MAE reduction | High-water reduction |
| --- | ---: | ---: |
| Ahr | −0.82% | 0.98% |
| Erft | 17.48% | −0.62% |
| Sieg | −1.60% | 3.88% |

The 2.9% external all-day average is driven by the Erft improvement, offset by
small losses in Ahr and Sieg. It is not a uniform transfer benefit. The external
all-day and high-water per-gauge contrast improves at 28 of 48 gauges and worsens
at 20; these nested gauges are not independent trials. River-balanced averages
and the median per-site change answer different questions; both are retained.

The predeclared substitution arm H+E also deserves retention: its Wurm all-day
MAE is 0.409, and external high-water MAE is 6.770, lower than H+A+E on those
outcomes. Adding conventional and learned descriptors together is not always
best. The primary contrast remains H+A+E versus H+A; do not promote a different
arm into a new primary question after inspecting this test year. H+E's capacity
limitations below also preclude an unconditional winner claim.

## Measurement and selection sensitivities

The all-day Wurm benefit persists under the article-faithful selection policy
(18.36% versus 23.15% under primary selection) and in every paired seed repeat
(17.9–27.7%). External all-day seed reductions range from 1.7% to 3.3%.
These primary-policy seed ranges measure algorithmic variation, not sampling uncertainty.

The high-water increment is much less stable:

- The primary Wurm gain is 1.57%, while the article-faithful policy gives a
  1.37% worsening. Across the three primary seed pairs it ranges from a 2.7%
  worsening to a 6.3% improvement.
- Wurm's strict-clean high-water sensitivity slightly favours H+A; the
  article-faithful strict-clean result worsens by approximately 6.5% with E.
- The external primary high-water gain is 1.71%, but the article-faithful
  comparison gives only 0.017%, effectively no material increment here.
- External row-level QA is unknown; a clean-only external result is undefined.
  Unknown is not coded as either verified clean or known bad.

The Wurm high-water set comprises 21 gauge-days on **nine calendar dates**;
the external set comprises 274 gauge-days on **35 dates**, across three river
systems. Neither count is a count of independent floods. There is one test year;
the saved between-year intervals are correctly undefined. No statistical
significance or general multi-year reliability is established.

## Spatial-stratum differences

These are evaluation strata of the same fitted models, **not retraining on
filtered donor pools**. The full census remains the main result.

| External evaluation view | Gauges / high-water gauge-days | All-day E reduction | High-water E reduction |
| --- | --- | ---: | ---: |
| All eligible external records | 48 / 274 | 2.90% | 1.71% |
| High-overlap proxies | 47 / 270 | 3.24% | 1.84% |
| High overlap and location-consistent | 46 / 263 | 3.30% | 1.65% |
| Severe mapping-stress view | 1 / 4 | −4.42% | −1.62% |

The small external gains survive restriction to the stricter overlap/location
view; they are not solely created by the problematic held-out spatial match. Their magnitude remains
small, and some RMSE contrasts still favour H+A.

The severe held-out mapping-stress view contains **only Schoenau / Erft
(DEA13730)**. Its all-day MAE is 0.482 for H+A and 0.504 with E; high-water MAE
is 14.513 versus 14.748. Do not generalize one site into an estimate of a whole
mapping-quality population. The 19 stress records in the entire regional pool
are mostly donors, not 19 held-out stress sites. No causal conclusion about
mapping error or about removing weak training donors follows from these views.

## Largest misses and calibration references

MAE and RMSE give different warnings. Relative to raw GEOGLOWS, H+A+E high-water
MAE improves by 1.6% at Wurm and 10.7% externally, while high-water RMSE **worsens
by 14.1% and 10.3%**. Better typical error coexists with more damaging large misses.
Incrementally, E slightly reduces high-water RMSE relative to H+A, but does not
remove the correction's tail problem relative to the uncorrected product.

The July 2021 Wurm plots show pronounced attenuation of the supplied daily
surges at Herzogenrath 1 and Randerath. At Randerath on 15 July, adding E makes
an already attenuated estimate lower. At Herzogenrath E helps relative to H+A
but both corrected estimates remain below the raw product on the largest days.
Ahr/Erft tail examples show analogous misses, including Kreuzberg and the
spatially conflicted Schoenau record. Perke on 29 January is an opposing failure:
the correction amplifies an overestimate. The problem is not only underestimation.

On the strict-clean Wurm high-water rows, both primary corrections improve on
raw GEOGLOWS. The incremental E result is mixed even there: MAE is 0.8% worse
than H+A, while RMSE is 3.3% better. The article-faithful sensitivity does not
replicate a clear added high-water benefit. Do not interpret the overall tail
warning as a claim that every correction worsens every reliably measured event.

Several largest Wurm differences lie outside the inherited strict-clean criteria.
That does not establish their supplied observations are wrong. Keep the main
census, qualifications and sensitivity together. External observation QA cannot
be resolved from this review. Daily means are not instantaneous peaks or stage
thresholds, and these are retrospective reconstructions, not forecast warnings.

The donor-FDC reference does not rescue the result: all-day MAE is 0.953 at Wurm
and 1.234 externally, worse than raw GEOGLOWS. The extra-label local FDC reference
is especially unstable in extrapolated high flows (all-day Wurm MAE 2.092 and
high-water MAE 19.105), although it performs well on the strict-clean high-water
subset. Preserve this calibration failure; do not cap its extreme predictions
post hoc to make a tidier comparator. Its access to target history remains an
explicitly different information budget.

The review establishes these error patterns, not their cause. It does not show
whether forcing, training-event support, the residual formulation or other
assumptions cause attenuation. Do not introduce an untested explanation as a
finding or add a new model family on that basis.

## Tree-limit diagnostics

There are **26 capped fits out of 128 tuning fits**. Seven of the 32 selected-
configuration inner fits hit the 1,500-tree limit.

| Policy / arm | Final refit trees | Selected inner fits hitting cap |
| --- | ---: | ---: |
| Primary H | 755 | 0/4 |
| Primary H+A | 475 | 0/4 |
| Primary H+A+E | 502 | 0/4 |
| Primary H+E | 1,312 | 2/4 |
| Article-faithful H | 506 | 0/4 |
| Article-faithful H+A | 1,327 | 2/4 |
| Article-faithful H+A+E | 1,404 | 2/4 |
| Article-faithful H+E | 829 | 1/4 |

The selected primary H+A/H+A+E pair is not itself capped, so its result is not
simply two fits terminating at the maximum. **Model selection is not completely
cleared of the cap issue:** the primary H+A+E runner-up has weighted validation
MSE 0.587246 versus the winner's 0.586271 (only approximately 0.17% apart), and
one runner-up fold is capped. H+E and several article-faithful selections have
more direct capacity limitations. A final tree count below 1,500 is not proof
that every contributing inner fit converged before the limit.

## Recommended continuation

Retain this direction and the frozen benchmark; do not relabel the all-day gain
as a demonstrated high-water or warning benefit. Before scaling, perform one
**fair capacity extension** within the same method:

1. Give all four arms/policies the same declared 3,000-tree maximum, retaining
   the same candidates, folds, seed, stopping criteria, observations and test
   populations. Refit the 26 previously capped tuning jobs from scratch; reuse
   truly early-stopped jobs only with verified unchanged settings.
2. Reselect using the same validation-only criterion, then refit affected final
   seed ensembles and rescore the same frozen test rows. Do not choose the cap
   according to which gives a favourable AlphaEarth test result.
3. Report both budgets, remaining cap hits and any selection changes. This is
   an already motivated capacity diagnostic, not a requirement for a positive
   outcome. The original benchmark remains available.

The 26 capped jobs originally consumed approximately 557 seconds; allowing a
larger cap plus affected refits is a modest follow-up, likely tens of minutes
rather than a new extraction campaign. Actual runtime remains to be measured.
**This review did not launch it.** After that check, a locked multi-year evaluation
can determine whether the all-day value transfers across years and whether
high-water gains are more consistent than this first fold suggests.

Practical DRR interpretation: average-flow reconstruction gains do not justify
automatically replacing a raw global estimate during severe high water. A
prospective agency use would require event-tail validation, measurement
provenance and visibility of failure cases. This retrospective benchmark does
not establish operational warning skill, avoided losses or operator benefit.

## Artifacts and verification

Review directory: `results/limburg_dise_regional_benchmark_v1/review_2026_11_17/`.
It contains primary and selection-policy contrasts, per-gauge results, seed
sensitivity, observed daily maxima, weighted high-water squared-error changes,
symmetric helped/harmed examples, candidate/tree-limit tables and two inspected
figures. Source results are unchanged; 85 principal metric rows were independently
recomputed and all seed ensembles reproduce their saved predictions exactly.
The frozen output manifest and review receipt pin their hashes. No empirical
confidence interval was manufactured, no test case was discarded, and no new
model fit or data pull occurred.
