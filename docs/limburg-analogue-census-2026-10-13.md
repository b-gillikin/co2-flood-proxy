# Reviewing the actual Limburg analogue sets

Internal results and interpretation aid, 2026-10-13. Brian writes dissertation
prose. Runner: `scripts/74_review_analogue_census.py`. Local outputs:
`results/basin_ai_analogue_census/`.

## Why the assessment changed

Brian requested a census of actual analogues because predicting a mean peak
and inspecting fourteen outcome-selected examples did not capture the richer
question of useful historical event context. The earlier peak result remains
valid for that narrow outcome. This extension is explicitly exploratory after
those results; it examines the existing retrievals without fitting models,
changing weights or reranking donors using their outcomes.

The review covers all 1,062 held episodes for data coverage, all 38,540 saved
selected slots across main and existing quality analyses, and all 774 distinct
evaluated query events. These slots repeat 14,318 distinct query–donor pairs
across arms/cohorts/sensitivities. There are 7,708 query sets and 3,072 distinct
query/cohort/sensitivity reference pools. The reference calculations use all
965,026 eligible query–candidate slots, with no sampled reference events.
None of these expanded pair counts is an independent sample size.

This is a census of the held archive and its actual retrievals. It does not
turn incomplete or provisional discharge into exact measurements, nor claim
to contain every Limburg flood. Every episode remains in `event_coverage.csv`.
Episodes lacking an eligible exact-Q response have no invented shape score;
older incomplete histories and initial queries with insufficient prior donors
also remain visible. Dutch and German input asymmetries remain documented.

## What was examined

Each actual donor is compared directly with the query's response in hours
1–72. The five-donor mean peak is no longer treated as the whole assessment.

| Diagnostic | Definition and meaning |
| --- | --- |
| Level mismatch | RMSE of the 72 Q/own-era-p99 values; retains relative high-water magnitude. |
| Shape mismatch | RMSE after separately dividing each response by its own response maximum; compares temporal form while level mismatch keeps magnitude visible. No time shifting or warping. |
| Peak timing mismatch | Absolute difference between the first maximum's hour in the response segment. |
| High-water duration mismatch | Absolute difference in observed hours at or above own-era p99. This is not duration above an official warning threshold. |
| Threshold-excess mismatch | Difference in the sum of positive Q/p99 minus one over 72 hours, in p99-hours; not physical flood volume or damage. |
| Terminal behavior mismatch | Difference in final-24-hour mean/response-maximum ratios; a simple description of how elevated the response remains. |

The audit also records standardized 512-hour history mismatch, complete
antecedent and response rainfall totals, river/gauge/country relationships,
rating identity and existing measurement concerns. Post-onset rainfall is
used only to understand observed response differences. German rainfall is
missing rather than assumed zero. All diagnostics remain separate; there is
no tuned overall relevance index or automatic human verdict.

For every query, the whole original eligible prior pool supplies a reference.
Each donor storm has equal total weight; multiple events within that storm
share its weight equally. A selected donor's percentile is the weighted
fraction of pool distances below its distance, plus half the tied mass.
Lower percentiles indicate a closer response relative to that archive; 0.5
is its weighted median. This is a reference distribution, not a trained
comparator or proof of operational skill.

The review separates individual-donor distances, the best member of a selected
set, and the mean response curve. The best member is retrospective set coverage;
it is not an available-at-onset oracle. A smooth ensemble curve can hide poor
individual analogues, and opposite donor peak errors can cancel in their mean.

## What the census shows

Mean individual-donor peak-scaled shape RMSE, lower being closer:

| Common cohort | Comparator | Challenger | Shape mismatch, comparator → challenger | Relative reduction |
| --- | --- | --- | --- | ---: |
| Dutch, 534 queries / 186 storms | Raw history | TTM | 0.2250 → 0.2188 | 2.7% |
| Context, 276 queries / 99 storms | TTM | TTM+AlphaEarth | 0.2270 → 0.2124 | 6.4% |
| Context, same queries | TTM+area | TTM+AlphaEarth | 0.2188 → 0.2124 | 2.9% |
| Pooled NL/DE, 774 queries / 236 storms | Raw history | TTM | 0.2204 → 0.2129 | 3.4% |

These changes were hidden by the mean-peak-only result. Dutch TTM improves
shape matching in 302/534 queries; pooled TTM in 433/774. AlphaEarth improves
over TTM in 173/276 queries, ties in four, and worsens it in 99. The mean
shape increment is favorable on every Dutch river and on German Wurm. The
AlphaEarth-versus-TTM shape increment is favorable on all six context rivers;
against the area control it is favorable on five, with Geul the exception.

The same shape directions persist in the existing measurement-concern
sensitivity. Conditional 95% paired query-storm intervals for the mean shape
differences are:

- Dutch TTM minus raw: -0.0062, [-0.0114, -0.0009].
- AlphaEarth+TTM minus TTM: -0.0146, [-0.0207, -0.0086].
- AlphaEarth+TTM minus area+TTM: -0.0064, [-0.0110, -0.0017].
- Pooled TTM minus raw: -0.0075, [-0.0124, -0.0024].

Year-block intervals give the same direction for these shape contrasts. The
full table reports all six diagnostics, both sensitivities and both block
choices, rather than showing only favorable contrasts. These are unadjusted,
exploratory, archive-conditional intervals; repeated donors and measurement
uncertainty are not fully represented. Census summaries describe the observed
archive exactly; the intervals concern variation in the query mix under the
resampling assumptions, not doubt about whether every saved pair was included.

The improvements are modest and have tradeoffs. Dutch raw-history donors have
a mean peak-time mismatch of 9.28 hours versus TTM's 10.19; the paired increase
is +0.91 hours, interval [0.25, 1.55]. Among the 302 Dutch queries whose shape
improves, 143 have worse mean timing mismatch. In the context cohort, timing
improves from 11.59 to 10.76 hours with AlphaEarth, but its interval includes
zero. There is no consistent improvement in high-water duration.

Conventional rainfall/discharge signatures remain the strongest Dutch method:
shape RMSE 0.1997, versus raw 0.2250 and TTM 0.2188. Their selected donors have
a mean whole-pool shape percentile of 0.3845, versus raw 0.4587 and TTM 0.4348.
On the common context subset, TTM's percentile is 0.4628, area+TTM 0.4378,
and AlphaEarth+TTM 0.4211. Representations retrieve somewhat enriched shapes,
but most of the eligible archive is not made irrelevant by that enrichment.
For example, 267/774 pooled TTM query sets have a mean shape percentile above
0.5. Report the heterogeneity alongside the average.

## Why full event context matters

The chronological atlas shows individual donor trajectories, not just their
averages. Early recession, prolonged elevation and later renewed rises can
have similar peaks while telling different stories. The first context page,
for example, shows several March 2019 queries with large later rises across
tributaries that their selected donor curves do not reproduce. That is an
observed response mismatch; weather records are needed to discuss its cause,
and no cause is assigned from the curve alone.

Within the 774 distinct evaluated queries, 337 have their response maximum
at hour 1 and eight at hour 72; 28 still exceed p99 at hour 72. The assessment
often concerns an already receding pulse, and sometimes ends during elevated
water. A 72-hour onset-centered segment is consequently not automatically
the entire flood event. This affects the meaning of peak timing and recession.

Mean individual peak error also differs substantially from error of the mean
peak: Dutch TTM 0.9578 versus 0.7489; context AlphaEarth 0.8462 versus 0.6641;
pooled TTM 0.8729 versus 0.6969. Opposite donor errors partly cancel. The
five-donor peak range contains the query peak in about 67–70% of those cases,
but that retrospective containment is not a calibrated forecast interval.

The earlier same-gauge preference remains real: context goes from 27.1% with
TTM to 83.6% with AlphaEarth. Better shape beyond the area control is relevant
evidence, but does not isolate learned catchment properties from geographic
identity. The cross-border archive likewise adds evidence from two German
gauges on Wurm, not two new independent river systems.

## Research reading and the practical review packet

The richer result is that representations can improve the form of retrieved
responses without improving peak prediction or timing. That answers part of
the original event-analogue question and makes the previous blanket reading
of "no useful AI improvement" too broad. It does not make the improvement
large, establish process explanations, or show operational usefulness.

Keep the question centered on which historical evidence is useful, under
which conditions, and with what measurement qualifications. Foundation-model
success need not mean winning every score. Conventional signatures earn
their place here because they represent event rainfall explicitly; raw Q
history is expected to win its own history-distance comparison by design.

Open `results/basin_ai_analogue_census/index.html` for the complete main-run
index. Browser Find locates a gauge, river or date. It links every query set
to a chronological atlas page and row, with all five actual donors plotted
against the query. Main runs have 133 pages covering all 1,584 query/cohort
entries; overlap between cohorts is explicit. `all_selected_pair_diagnostics.csv`
also covers every quality-sensitivity selection. `paired_query_diagnostics.csv`
provides each comparison's six differences for every query. Detailed donor
identity and source metadata remain in the pair table.

The numerical audit is complete for all selections. Figure inspection is AI
assistance and visual QA, not a human verdict for every curve. Brian can use
the complete atlas for his own interpretation; no new human-labeling exercise
is required merely to report the quantitative census.

## Literature and reproduction

The whole-curve perspective follows the motivation in
[Wendi, Merz and Marwan (2019)](https://doi.org/10.1029/2018WR024111), §1.
The warning against inferring causes from shape alone is supported by
[Tarasova et al. (2019)](https://doi.org/10.1002/wat2.1353), §2.3. The chapter
does not implement their classification or cross-recurrence algorithms.

```bash
MPLCONFIGDIR=/tmp/limburg-mpl .venv-foundation/bin/python scripts/74_review_analogue_census.py
```

Use `--no-atlas` to reproduce tables without rendering the 133-page packet.
Input/code hashes and coverage counts are in `summary.json`. Raw provider
records remain local. Six scientific tests protect shape/magnitude separation,
timing, missingness, onset exclusion, reference storm weighting and tied ranks.

Validation: 108 tests passed; repository lint, changed-file formatting and
whitespace checks passed. All ten scientific CSV tables reproduced byte for
byte in a separate directory. All 55 input/code hashes matched, every selected
slot had six finite diagnostics and bounded reference percentiles, and all
133 atlas files/index entries cover exactly the 1,584 main query/cohort rows.
The local `reproduction.json` records these checks. Summary plots and selected
atlas pages were visually checked for layout and curve interpretation; this
does not imply a qualitative human verdict for every query.
