# Limburg analogue distributions: results and interpretation aid

Internal research aid for Brian; not dissertation prose or independent human
validation. Implements the [dated plan](limburg-analogue-distribution-implementation-plan-2026-10-15.md)
following the [scientific review](reviews/limburg-analogue-forecasting-review-2026-10-15.md).

## What this adds

The analysis evaluates the complete empirical distribution supplied by the
saved analogues, rather than only their mean trajectory or the similarity of
individual response shapes. It asks whether selected precedents supply better
ranges of subsequent discharge than the eligible historical archive.

Existing script-84 pooled-policy rankings, cohorts and own-rating-era p99
normalization are preserved. Every selected donor contributes its original
response trajectory with equal weight. The archive gives equal total mass to
each completed prior regional group and equal mass to its member events.
Current-discharge persistence is a separately labeled point reference.

The primary endpoint is mean exact empirical-distribution CRPS over response
hours 1–24, with 6h/12h/24h readouts and full hourly profiles. Lower is better.
The primary setting remains five donors, all rivers, main measurement
treatment. Ten donors, other-river archives and quality filtering are specified
supporting comparisons, not a replacement primary chosen after results.

The analysis remains retrospective: full-era p99, finalized observations and
the inherited complete-72h scoring cohorts are unchanged. A smaller CRPS at
hour 24 than hour 6 does not itself show greater long-lead predictability:
discharge scale and event phase also change during recession. Compare methods
at the same lead and on the same queries.

## Full-census coverage

| Cohort | Scoring-eligible cases before archive availability | Queries with prior archive | NL / DE queries |
| --- | ---: | ---: | ---: |
| Discharge history | 851 | 845 | 610 / 235 |
| Rainfall-matched | 770 | 764 | 554 / 210 |
| AlphaEarth/context | 373 | 365 | 294 / 71 |

The complete 1,062-event inventory remains visible for every setting.
Quality-filtered available populations are 802, 724 and 346, respectively.
These are matched cohorts, not independent samples or interchangeable rows in
a model leaderboard. The two German gauges belong to one watercourse.

There are 15 discharge-history queries with only one to four prior groups;
another 15 have five to nine. Thus the ten-donor setting has ten actual donors
for 815 of 845 primary queries. Short archives remain scored and identified;
no-archive cases remain unscored with an explicit reason.

Across all settings and methods, outputs contain 88,560 event/distribution
sets, 2,125,440 hourly scores, 7,692 reconstructed archives and 2,382,908
archive-membership rows. These counts include repeated settings and methods;
they are not counts of independent floods.

Paired intervals use 9,999 joint regional-group resamples and the existing
year-block sensitivity, seed 20261013. They remain conditional on the held
archive and exploratory development; they do not correct for every inspected
comparison, reused donor, provider error or the small number of catchments.
They are uncertainty estimates, not statistical pass criteria for the chapter.

## Main scores and ensemble-size sensitivity

Mean 24h CRPS, Q / own-era p99; all-river main treatment. Compare within a
cohort. The same cohort's archive score is unchanged between donor counts.

| Cohort | Method | Five donors (primary) | Ten donors (supporting) |
| --- | --- | ---: | ---: |
| Discharge history | Generic archive | 0.26892 | 0.26892 |
| Discharge history | Raw history | 0.30007 | 0.27562 |
| Discharge history | Raw + state | 0.27866 | 0.25771 |
| Discharge history | TTM + state | 0.27503 | 0.25399 |
| Rainfall-matched | Generic archive | 0.26825 | 0.26825 |
| Rainfall-matched | Conventional R0 | 0.26156 | 0.24765 |
| Rainfall-matched | Raw history | 0.29790 | 0.27345 |
| Rainfall-matched | Raw + state | 0.27610 | 0.25346 |
| Rainfall-matched | TTM + state | 0.27066 | 0.25255 |
| Context | Generic archive | 0.27390 | 0.27390 |
| Context | Temporal + state | 0.26616 | 0.25045 |
| Context | + area | 0.25340 | 0.24541 |
| Context | + identity | 0.25903 | 0.24993 |
| Context | + fixed-2017 context | 0.25135 | 0.24438 |
| Context | + annual AlphaEarth | 0.25824 | 0.24554 |

The five-donor discharge-history comparison does not establish a distributional
TTM advantage: TTM minus raw/state is -0.00362, regional-group interval
[-0.01095, +0.00372], and year interval [-0.01091, +0.00264]. Against the archive,
TTM is slightly worse in point estimate (+0.00612), with both intervals
including zero. Closer shape precedents alone do not settle this endpoint.

With ten donors, the TTM distribution improves on the archive by 0.01492,
about 5.6%, with group interval [-0.02311, -0.00709] and year interval
[-0.02755, -0.00398]. However, raw/state also improves, and TTM's additional
0.00372 reduction has a group interval including zero. Its year interval is
slightly negative; retain that uncertainty distinction. This is an
ensemble-size-dependent retrieval result, not proof that TTM is essential.

Conventional rainfall/Q remains competitive. At ten donors it improves on
its archive by 0.02060, about 7.7%, with group and year intervals excluding
zero. TTM minus conventional R0 is +0.00490; both intervals include zero.
The positive point difference favors conventional summaries. At five donors,
R0 is also better in point estimate; the paired year interval excludes zero
while the group interval does not. Report both rather than a universal winner.

Quality filtering preserves the ten-donor TTM-minus-archive direction in the
discharge-history cohort (-0.01232; group interval [-0.01969, -0.00528]).
Its TTM-minus-raw/state interval still includes zero. In the other-river
ten-donor setting, TTM improves on the archive in the group interval but the
year interval includes zero. All results remain available, without choosing
the most favorable uncertainty scheme.

## AlphaEarth and geographic transfer

In the all-river context cohort, annual AlphaEarth improves point CRPS over
temporal/state alone by 0.00793 at five donors and 0.00490 at ten. Both
group/year intervals include zero in these incremental comparisons. Area and
fixed-2017 context have lower point errors than annual AlphaEarth; the annual
model is not a unique context winner. Some control differences are clearer
under year blocks, reinforcing this qualification.

The ten-donor AlphaEarth distribution improves over its generic archive
(-0.02836; group [-0.04146, -0.01549], year [-0.05055, -0.00161]). That does
not establish that annual satellite context caused the gain: the temporal
and simpler geographic controls matter.

Requiring donors from other physical rivers reverses the geographic point
increment. At ten donors, annual AlphaEarth has CRPS 0.26814 versus temporal
0.25244, difference +0.01570, with group interval [+0.00694, +0.02519] and year
interval [+0.00560, +0.02930]. At five donors the point difference is also
unfavorable, with a group interval including zero and a positive year interval.
Thus landscape similarity can redirect retrieval toward less informative
future distributions in this particular cross-river setting. It does not
follow that AlphaEarth is generally unsuitable for hydrology.

Country results are heterogeneous. Ten-donor temporal retrieval improves
over the archive in NL point scores (0.26312 versus 0.28641), while the held
German Wurm queries have slightly worse TTM points (0.23030 versus 0.22350).
The learned increment over raw/state is also not shared in direction there.
These are site/cohort comparisons, not causal effects of national warning
systems. AlphaEarth/context support is only 294 NL and 71 DE queries.

## What the ranges actually cover

Central 10th–90th empirical quantile range at +24h, all-river main treatment:

| Cohort and method | Five-donor observed coverage | Ten-donor observed coverage |
| --- | ---: | ---: |
| Discharge history, TTM/state | 73.3% | 79.3% |
| Discharge history, raw/state | 75.0% | 79.1% |
| Discharge history, generic archive | 80.7% | 80.7% |
| Rainfall-matched, conventional R0 | 70.4% | 74.7% |
| Rainfall-matched, TTM/state | 72.5% | 77.5% |
| Context, temporal/state | 72.1% | 71.8% |
| Context, annual AlphaEarth | 66.8% | 71.0% |

These ranges are not calibrated confidence guarantees. With five equally
weighted members, the stated inverse-CDF 10th–90th range is the member minimum
and maximum; it is a coarse empirical quantile range. As a mathematical
reference, five iid continuous draws would cover an independent sixth draw
between their extrema with probability 4/6, not 80%. Our selected neighbours
are not iid draws, so that reference is not a correction to apply here.
It explains why nominal quantile labels and predictive coverage must be
distinguished. We evaluate the specified finite distribution, not an inferred
infinite ensemble, and retain the fixed five/ten count comparison.

Coverage near 80% at one lead is insufficient evidence of calibration across
leads, rivers or severe events. For ten-donor TTM in the full discharge cohort,
coverage is 68.8% at +6h, 76.3% at +12h and 79.3% at +24h. At +24h its width
is 0.687 Q/p99 versus archive 0.687, but five-donor TTM is wider than the
archive (0.851 versus 0.687) while covering less often. Range location and
tail allocation matter as well as width. A low-coverage result should not
automatically be explained as simply too narrow.

Most +24h misses for the ten-donor TTM distribution are above its upper edge
(16.0%, compared with 4.7% below). Unrepresented sustained flow or later rises
remain plausible failure modes, not processes established from shape alone.
Pointwise ranges do not imply simultaneous trajectory coverage. No calibration
model, warning decision or newly trained confidence/refusal rule was fitted.

## Actual examples

All 24 reused, outcome-independently selected sentinel panels received AI
visual inspection. They remain illustrations, not independent human labels
or a sample used instead of the numerical census. Examples, five-donor
all-river discharge-history comparison:

- Voer, 18 June 2016: TTM follows the sustained elevated response better than
  the archive (24h CRPS 0.118 versus 0.275). This is consistent with useful
  event-context matching; it is not a population-level TTM success rate.
- Eyserbeek, 15 August 2010: both distributions miss the large continuing
  response. TTM is narrower and worse (1.012 versus 0.864).
- Geleenbeek, 3 July 2013: a donor's later rise expands the upper range when
  the query actually recedes. TTM is much wider and worse (0.417 versus 0.133).
- German Wurm, 13 January 2011: both sets miss sustained high flow; a confident
  recession narrative would be misleading (TTM 0.980 versus archive 0.925).

## Interpretation for the chapter

This pass adds a real distinction: selected historical trajectories can carry
useful distributional information, particularly with ten donors, while their
AI-specific increment and uncertainty reliability remain limited. It does not
justify replacing the declared five-donor primary with the better supporting
setting or claiming operational forecasts.

Use the existing relevance/shape evidence together with these probability
diagnostics. Conventional hydrology is strong, the archive is a demanding
reference, and AlphaEarth's benefit is conditional on the transfer setting.
For FEWS interpretation, the empirical lesson is to expose the actual donor
count, provenance and disagreement, and verify range coverage rather than
equating agreement with trustworthy guidance. No operator benefit, historical
warning lead time, physical inundation or damage reduction is measured here.

## Reproduce and audit

```bash
python scripts/90_evaluate_analogue_distributions.py
python scripts/91_audit_analogue_distributions.py
```

Use the pinned foundation environment. Ignored outputs are in
`results/basin_ai_analogue_distributions/`: complete inventory and exclusions,
selected-donor references, all archive memberships and weights, hourly/event
scores, country/river/count summaries, per-gauge m³/s summaries, paired
differences/intervals, full lead profiles, plots and four sentinel pages.

The manifest binds actual inputs, source hashes, versions, seed and settings.
The independent auditor reconstructs memberships and every score through a
different CDF-gap formulation, and replays all bootstrap intervals through
multinomial group counts. It verifies 7,692 archives, 2,382,908 membership rows,
2,125,440 hourly scores, 88,560 event sets, 4,968 summary/profile rows and all
3,840 intervals. All estimable intervals have 9,999 finite draws; none failed.
The maximum numerical discrepancy is 1.46e-13. Input, output and source hashes
match. A full rerun reproduces all 39 existing scientific data files byte for
byte; the final figure refinement additionally exports the full hourly lead
profiles. The chapter suite passes 173 tests; repository lint, changed-source
formatting and whitespace checks pass. Both summary figures and all four
sentinel pages received AI visual inspection. Brian's human-review fields
are unchanged.
