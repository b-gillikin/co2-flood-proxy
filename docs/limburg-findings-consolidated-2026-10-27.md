# Limburg: consolidated findings for Brian

Internal evidence brief and writing aid, **not dissertation/article prose**.
The planned calculations are complete. This document consolidates saved results;
it introduces no new fitted model, event sample, bootstrap, retrieval or data need.

## Overall assessment

- Historical matching retrieves more similar subsequent response shapes than
  generic archive membership. Conventional hydrological matching also does this.
- TTM adds a modest shape-matching improvement in the broad Q-history census.
  Better individual matches do not imply consistently better response estimates.
- Added EO has useful conditional results, especially AnySat on German snapshot
  cases. Some other attractive results are not reproduced in larger eligible
  model-specific cohorts or with other-river archives.
- Cohort support, donor availability and the outcome being scored materially
  affect the conclusion. There is no demonstrated universal foundation-model
  winner, calibrated warning system or measured operator benefit.

## How this readout avoids selecting an attractive slice

The reporting hierarchy is an **explicit post-analysis organization**, not a
claim of prospective confirmatory specification. It retains the broad Q-only
comparison, all three EO readouts and both countries. For encoder-to-encoder
comparisons use the same all-ten intersection and donor universe. For each
encoder's applicability, also inspect its larger model-available population;
do not discard those events to manufacture a tidy leaderboard.

The fixed main view is pooled/all-river, requested k=5. Existing quality, k=10,
other-river, domestic and foreign sensitivities remain separate. Requested k
does not guarantee five/ten available donor storms. Both storm- and year-block
nominal 95% intervals are retained. "Both below zero" describes two saved
intervals, not multiplicity-adjusted confirmation. Intervals containing zero
do not establish equivalence or absence of useful information.

| Evidence population | Scored queries in the stated main view | Role |
|---|---:|---|
| Broad Q-history census, without EO availability requirements | 610 NL / 235 DE | TTM versus raw Q/state; earlier completed full-census comparison |
| Corrected rainfall, all-ten snapshot intersection | 363 NL / 111 DE | Common-population encoder/reference comparison |
| Corrected rainfall, all-ten twelve-month intersection | 275 NL / 74 DE | Separate context/population; not a paired test of longer history |
| Corrected rainfall, all-ten four-week intersection | 69 NL / 33 DE | Separate, smaller shared population |
| Full prior-year AlphaEarth context cohort | 294 NL / 71 DE | Earlier annual-context controls, kept distinct from EO intersections |

These are overlapping populations, not independent experiments to add together.
The 851 Q-eligible and 836 conventional-feature-complete events are eligibility
counts; the main EO review's 656 and corrected rainfall review's 646 are unions
of distinct scored queries across configurations. Configuration rows are not n.

## 1. Similarity retrieval works more consistently than response estimation

In the six main corrected-rain all-ten country/readout cells, conventional
matching improves mean individual peak-normalized shape error versus the
equal-storm-weighted whole eligible archive; both nominal intervals are below
zero in each cell. Raw-Q matching shows the same direction of evidence. This
supports event-specific matching, but is not an AI-specific result.

The whole-archive reference remains competitive for mean trajectories and
within-window duration. For example, German snapshot conventional retrieval
has curve-error difference **+0.0267** versus that archive (storm interval
[+0.0082, +0.0461]; year [+0.0083, +0.0473]), despite finding closer shapes.
Useful resemblance and accurate aggregate estimates are different achievements.

## 2. TTM has a modest contribution, with limits visible in the broader census

In the full Q-history main/pooled/five-donor comparison against raw Q/state:

| Country | Queries | Mean shape-error difference, TTM minus raw | Storm interval | Year interval |
|---|---:|---:|---|---|
| NL | 610 | −0.00407 | [−0.00706, −0.00120] | [−0.00689, −0.00199] |
| DE | 235 | −0.00543 | [−0.01078, −0.00049] | [−0.01023, −0.00116] |

The German shape improvement remains under the existing other-river and quality
restrictions; the Dutch other-river intervals include zero. This is evidence
about this archive's transfer, not a country treatment or a routed river model.
Full-curve and peak-error improvements are not comparably consistent.

On the narrower NL snapshot rainfall intersection, TTM versus conventional
reduces mean-trajectory error from **0.3357 to 0.3226** (about 4%) and duration
error by **0.595 h**. Both main-view intervals exclude zero for these contrasts.
The curve advantage becomes uncertain with other-river donors, quality filtering
and k=10; duration's quality result persists but its other-river/k=10 intervals
include zero. That duration is the number of hours above p99 within the next
72 hours—not warning lead time or whole-flood duration.

## 3. Added EO has a substantive conditional example: AnySat on DE snapshot cases

For 111 German queries (68 query storms, seven year blocks) on the shared
snapshot population, AnySat + TTM/state versus conventional matching gives:

| Outcome | Difference in error/mismatch | Storm interval | Year interval |
|---|---:|---|---|
| Individual shape error | −0.01351 | [−0.02085, −0.00644] | [−0.02368, −0.00403] |
| Mean-trajectory RMSE, Q/p99 | −0.03350 | [−0.05038, −0.01728] | [−0.05602, −0.01026] |
| Peak-estimate absolute error, Q/p99 | −0.08059 | [−0.14169, −0.02121] | [−0.14513, −0.02580] |
| Mean individual-donor peak-time mismatch | −3.77 h | [−5.64, −2.00] | [−6.63, −0.52] |
| Final-24-hour mean-level absolute error | −0.04050 | [−0.06523, −0.01512] | [−0.08096, −0.00099] |

Mean-trajectory RMSE is **0.3009 → 0.2674**, about an 11% reduction. Against TTM
itself, the curve improvement is −0.02470 with both intervals below zero;
shape, individual-donor timing and late-response errors also improve in that
main view. Duration is less certain. Timing mismatch is not a warning lead time
or the error of a single predicted peak time.

This result is not solely an all-ten-intersection finding: its larger
model-available archive still shows a curve advantage against conventional and
TTM. Quality filtering retains that evidence. Other-river and k=10 curve
contrasts are weaker/resampling-sensitive, although the other-river peak and
late-level advantages over conventional remain in both nominal interval views.
The late-level contrast also retains both-below-zero intervals at k=10.

**Weight to give it:** a promising, task-specific EO result worth discussing,
not a validated AnySat winner. It was identified among many exploratory
comparisons; DE is represented by two Wurm gauges. The experiment does not
isolate pretraining from raw EO information or reveal which physical property
the embedding used.

## 4. Some appealing improvements depend strongly on which archive is available

| Example | Shared all-ten result | Larger/support sensitivity | Interpretation |
|---|---|---|---|
| Copernicus-FM + TTM/state, NL four-week curve, versus TTM | −0.02023; both intervals below zero; 69 queries | +0.00264; both intervals include zero; 201 model-available queries | Small shared-cohort gain is not reproduced in the broader application population. |
| CROMA + TTM/state, DE twelve-month curve, versus TTM | −0.02835; both intervals below zero; 74 queries | −0.00408; both intervals include zero; 98 model-available queries | A gain against the weaker TTM result is not a stable general encoder advantage. |
| Same CROMA configuration versus conventional | −0.00638; both intervals include zero | With other-river donors: +0.03907, both intervals above zero | Improving on TTM alone does not establish an improvement on the stronger reference or transfer to other rivers. |

These changes involve both query membership and eligible donor archives. They
are not formal tests that cohort membership caused the performance difference.
They demonstrate why the larger eligible census and shared-population comparison
must both remain visible.

EO-only retrieval has no shape contrast with both intervals below zero versus
conventional in the fixed six-cell shared view; several contrasts are worse.
That supports retaining river-state/history information in this configured
retrieval task. It does not establish that EO-only models cannot work under
different designs or training.

## 5. AlphaEarth and the supplemental imagery have bounded roles

- **AlphaEarth:** no consistent general shape/mean-trajectory advantage over
  the temporal control in the earlier full annual-context cohort. There is a
  specific NL donor peak-time mismatch reduction of about **0.92 h** (294
  queries; storm interval [−1.79, −0.06], year [−1.73, −0.11]). Retain this
  selective result without turning annual context into a measured storm-wetness
  signal. EO-matched AlphaEarth populations are supplied separately in the
  consolidated tables.
- **TOA/QA60 and alternate radar orbits:** common-query/common-donor comparisons
  show mixed changes, not a blanket improvement. DE four-week TOA curve gains
  have only 10–11 common queries. Orbit 15 snapshot has seven queries per country;
  orbit 161's common cohorts are NL-only. There are also adverse shape contrasts
  (e.g. SatMAE NL snapshot and CROMA orbit 161 NL annual). These are bounded source/
  support sensitivities, not clean causal tests of reflectance or architecture.

## 6. Actual cases explain the aggregate trade-offs

Use the [visually inspected case pairs](reviews/limburg-actual-analogue-review-2026-10-27.md):

- Herzogenrath, September 2018: a changed CROMA donor set follows a rapid recession
  more closely than TTM alone.
- Randerath, March 2019: changing all five donors still misses a later, larger
  rise. A different retrieval is not necessarily informative about what follows.
- Voer, May 2024: normalized shape improves while trajectory and duration errors
  worsen substantially. This makes the similarity/estimation distinction tangible.
- Gulp, September 2017: AnySat and TTM return the same two donors. A good-looking
  match supplies no incremental EO evidence in that case.

These were chosen after inspecting outcomes. They explain successes/failures;
they do not estimate their prevalence or constitute a validation sample. Dutch
inherited provider labels describe July 2021 gauge context, not exclusions of
unrelated 2015/2024 events.

## What is established, and what Brian should avoid claiming

| Component | Supported interpretation | Not established |
|---|---|---|
| Similarity/dissimilarity | Some methods retrieve closer future shapes; cases expose misleading similarities and changed donor choices. | A hydrological mechanism explaining why each event behaved as it did. |
| Response estimation | Saved donor trajectories/peaks contain selectively useful information about the withheld next 72 hours; several references remain competitive. | As-issued forecast skill, calibrated flood probabilities or warning lead time. |
| Cross-river/country transfer | Conditional transfer evidence under explicit donor restrictions, including informative failures. | National policy effects, independent country treatments, or upstream/downstream causation. |
| Uncertainty | Documented support limits, measurement flags and conditional exploratory intervals. | A validated safe-to-use/abstain threshold for operators. |

The operational direction remains an evidence-linked historical precedent tool.
The retrospective design can inform what it should display and when to flag
limited support. Actual decision benefit or deployment reliability needs a
separate future evaluation; no such evaluation is required to report this study.

## All-ten lookup, not a model ranking

Each row below counts **36 dependent reporting cells** (three readouts × two
countries × six outcomes) for EO + TTM/state versus conventional in the fixed
main view. Different readouts have different populations; cells overlap heavily.
Counts omit effect size, multiplicity adjustment and sensitivity survival, so
they must not be used to select a winner.

| Encoder | Both intervals favour challenger | Both favour conventional | Both include zero | Resampling-sensitive |
|---|---:|---:|---:|---:|
| AnySat | 10 | 0 | 19 | 7 |
| Copernicus-FM | 5 | 1 | 26 | 4 |
| CROMA | 3 | 1 | 25 | 7 |
| DOFA | 1 | 0 | 25 | 10 |
| Galileo | 5 | 2 | 26 | 3 |
| OlmoEarth | 5 | 0 | 22 | 9 |
| Presto | 3 | 0 | 23 | 10 |
| Prithvi | 5 | 2 | 23 | 6 |
| SatMAE | 1 | 0 | 27 | 8 |
| TerraMind | 4 | 1 | 25 | 6 |

## Artifacts and closure

Script `142_consolidate_limburg_findings.py` produces
`results/limburg_findings_consolidation_2026_10_27/`:

- `contrasts.parquet`: saved point estimates and both interval views; all
  populations, settings and undefined results remain labelled.
- `fixed_reporting_view.parquet`, `sensitivity_comparison.parquet` and
  `population_comparison.parquet`: traceable main/sensitivity/broader-census views.
- `model_scorecard.parquet`: the dependent-cell lookup above.
- Three `*_vs_conventional.png`/`.pdf` forest figures covering every encoder,
  the controls, both countries and both uncertainty views, one per EO readout.
- A manifest binding inputs, reporting source and output hashes. No bootstrap
  was rerun; reverse contrasts negate and swap saved bounds exactly.

All three figures were visually checked. Reporting tests protect comparison
direction, cohort identity, undefined intervals, resampling-sensitive results
and agreement of point estimates/counts between bootstrap views. Full suite:
**338 passed**; test log `logs/limburg-findings-consolidation-tests-2026-10-27.log`.

The agreed computational and consolidation work is now complete. Brian can use
this brief, the tables and case figures to write the chapter/paper. No additional
model, data collection or experiment is made a prerequisite by this synthesis.


## Flood-focused case review — completed 2026-10-27

See [the case review](limburg-flood-case-review-2026-10-27.md) and `results/flood_case_review_2026_10_27/index.html`. All five requested steps are complete: source-bounded register, measurement/eligibility tracing, saved analogue inspection, failure diagnosis and case sheets/timelines. Seven core H3 cases are retained; only two linked continuous-response queries are pre-flood, with a third representing recovery. No models were fitted or reranked. Distinct support, retrieval and averaging failures qualify the earlier mean-performance findings. Full suite: 345 tests. Verification: `scripts/144_audit_flood_case_review.py`. An erroneous older prose claim about Voer hourly averaging was corrected; saved numerical outcomes were unchanged.
