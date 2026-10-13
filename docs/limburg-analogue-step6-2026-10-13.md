# Limburg analogue evaluation: Step 6

Internal interpretation aid, 2026-10-13. Brian writes dissertation prose.
Code: `scripts/73_analogue_uncertainty_review.py`.
Outputs: `results/basin_ai_step6/`.

Subsequent user-authorized full-response census:
`limburg-analogue-census-2026-10-13.md`. It extends usefulness beyond the peak
score and the fourteen illustrations. The conclusions below retain their
original scope; they do not rule out improvements in response-shape retrieval.

## Current conclusion

The tested frozen TTM representation does not establish a useful average
peak-response advantage over raw hydrograph similarity. AlphaEarth changes
retrieval substantially and improves the point estimate, but its improvement
remains uncertain. The context increment persists across the river-removal
checks; it is not solely an artifact of one retained river. The evidence does
not establish improved flood-warning performance or a generally superior AI
analogue method.

A substantive diagnostic is now visible: AlphaEarth primarily makes retrieval
more local to the query's catchment. That can remove poor cross-river matches,
but can also retrieve unsuitable extremes from the same gauge. Catchment
identity and event-response suitability are different properties. The present
comparison cannot attribute AlphaEarth's increment specifically to learned
hydrological characteristics rather than its ability to distinguish catchments.

## Paired uncertainty

The error remains the absolute error of the mean of five donor-event peak/p99
ratios against the query's subsequent 72-hour peak/p99 ratio. Negative paired
differences favor the challenger. All comparisons use identical queries and
eligible donor pools within their respective cohort.

| Comparison | Mean error difference | 95% storm-resampling interval | Query storms |
| --- | ---: | --- | ---: |
| Dutch TTM minus raw Q | -0.0003 | [-0.0582, 0.0583] | 186 |
| Dutch TTM minus conventional rain/Q | 0.1066 | [0.0516, 0.1635] | 186 |
| AlphaEarth+TTM minus TTM | -0.0315 | [-0.0836, 0.0204] | 99 |
| AlphaEarth+TTM minus area+TTM | -0.0305 | [-0.0644, 0.0032] | 99 |
| Pooled NL/DE TTM minus raw Q | 0.0218 | [-0.0250, 0.0679] | 236 |

Use 9,999 paired resamples of intact query storms, seed 20261013. The
estimator remains event-weighted: resample each cluster's total difference
and number of query events together. Repeating with intact calendar-year
blocks gives the same qualitative reading. A storm spanning New Year is
assigned wholly to its first query year. The full tables include both block
choices, the existing measurement-concern sensitivity, all fixed arms versus
the historical median, and river-specific differences.

These intervals are **conditional on the held archive and fixed retrievals**.
They do not quantify uncertainty in reused donor observations, p99 estimation,
pretraining, measurement errors, unseen catchments or long-term regime change.
The year-block check has only 16 years, and eight in the context subset. Report
these as sampling intervals with those limits, not as complete uncertainty or
proof of equivalence when zero lies inside. Contrasts are descriptive and
unadjusted for simultaneous multiple comparisons; no significance-driven arm
selection is made.

This use of dependence-aware resampling follows the general warning in
[Clark et al. (2021), *The Abuse of Popular Performance Metrics in Hydrologic
Modeling*](https://doi.org/10.1029/2020WR029001): performance rankings can be
sensitive to finite hydrological samples. Their work focuses on NSE/KGE;
it does not validate this chapter's particular analogue score or block choice.
The separate issue of observation uncertainty is directly relevant to
[the 2024 HESS study of discharge observation uncertainty and model
performance](https://hess.copernicus.org/articles/28/5011/2024/).
Neither source licenses treating a resampling interval as a substitute for
source-quality review.

## River and catchment dependence

Each influence run removes one physical river group from **both** queries
and candidate donors, then repeats retrieval and any prior-pool scaling. It
compares refitted errors with the original errors on exactly the same surviving
queries. Storm identities remain the original cohort definitions. This checks
influence; it is not validation on an unseen river. Wurm/Worm is one group,
including both German gauges and Dutch Rimburg.

- Dutch TTM-minus-raw differences range from -0.0106 to +0.0260 after river
  removal. Their direction is not stable.
- TTM remains worse than the conventional rain/Q comparator in all six Dutch
  main refits: differences +0.0822 to +0.1409.
- AlphaEarth-minus-TTM differences remain negative in all six main refits:
  -0.0700 to -0.0164. Against the area control they range from -0.0501 to
  -0.0056. Thus no single river's presence explains the entire point increment.
- After removing measurement-concern queries/donors, AlphaEarth still improves
  on TTM in all six refits, but its comparison with area becomes slightly
  positive (+0.0008) when Geleenbeek is removed.
- Pooled TTM-minus-raw differences remain positive in all six main refits:
  +0.0095 to +0.0320. Removing Wurm/Worm also removes all German queries;
  it cannot be interpreted as evidence about an additional German basin.

Six catchments remain six catchments, not 276 independent catchment replications.
The 45 represented catchment-years also repeat these same sites.

## What the selected analogues reveal

On the common context sample, same-gauge donor slots are:

| Representation | Same-gauge slots / all slots | Share |
| --- | ---: | ---: |
| TTM | 374 / 1,380 | 27.1% |
| TTM + area | 987 / 1,380 | 71.5% |
| TTM + AlphaEarth | 1,154 / 1,380 | 83.6% |

This is directly measured retrieval behavior. The interpretation that context
acts partly as a catchment-identity preference is an inference, not an ablation
proving its mechanism. No identity-only model or new weighting experiment was
added after seeing the results.

Every selected pair carries query/donor gauge, country, physical river identity,
rating identity, existing measurement flags and provider-status text. For
contextual review it also carries 24/72-hour rain summaries where held, p99,
response peak ratio and time to peak. German rainfall remains missing.
Inherited `provider_status` strings such as `pending_range_check` are historical
gauge-level labels: they are not current unsent requests or automatic event
exclusions. Event-level review decisions and measurement flags govern this audit.

The Dutch main TTM result contains 352 of 2,670 donor slots where the query or
donor has a retained measurement concern. The context arm has 162/1,380 such
slots, and pooled TTM 400/3,870. These are flags, not adjudicated measurement
errors. All become zero in the existing quality sensitivity. No provisional
German response is scored or selected as an exact-Q donor. All 98 provisional
German episodes remain available in the event inventory.

Repeated donors are also visible. In the pooled TTM run, 3,870 slots use 208
distinct prior storms; the most reused storm occupies 145 slots (3.75%). This
is archive reuse, not 3,870 independent historical flood observations. Distinct
prior storms within each top-five set do not make different queries independent.

## Visual relevance review

The packet contains fourteen illustrative cards: the largest gain, largest
loss, median paired difference and a measurement-concern query in each cohort,
plus two German examples because the first pooled selections were all Dutch.
Selection is outcome-informed and explicit. These examples cannot estimate a
relevance success rate or substitute for an independent, blinded human review.

The plots show standardized assessment histories, individual donor responses,
and the query's withheld response. Both response panels use the same vertical
scale. The plotted donor-curve mean is illustrative: the scored quantity is
the **mean of individual donor peaks**, not the peak of the mean curve. The
score uses hours 1–72; hour 0 is shown to orient the onset.

AI-assisted readings of the inspected plots and source flags are recorded in
`docs/reviews/limburg-analogue-visual-review-2026-10-13.md`. Human verdict fields
in `results/basin_ai_step6/human_review_cases.csv` remain blank. Completed human
fields are preserved on rerun; the script refuses to silently discard them if
case selection changes. The automated and AI-assisted work is complete; an
independent human-validation claim remains unavailable until that review exists.

## What the chapter can currently say

- This particular frozen representation and retrieval rule did not improve
  average peak-response similarity over the controls in these archives.
- Satellite context materially changes which past events are retrieved;
  much of that change is a strong preference for the same catchment. Its
  average error increment is modest and uncertain with six catchments.
- Similar standardized histories, same-gauge identity and a close average
  peak can each coexist with poor matching of the subsequent hydrograph.
  The selected examples illustrate this distinction; they do not estimate
  its prevalence or justify switching the primary outcome after results.
- Cross-border retrieval was executed with harmonized clocks, river aliases,
  storm identities and rating/quality metadata. Country alone neither proves
  nor invalidates hydrological relevance. The German evidence covers two
  gauges on one river, with provisional high flows retained but not scored
  as precise Q observations.

For an eventual FEWS evidence-exchange recommendation, the supported minimum
fields are canonical gauge/river identity, clock and interval semantics,
rating period, event-onset versus peak certainty, and source-quality provenance.
The concrete basis is the Wurm/Worm alias/nesting and the retained uncertain
query/donor records. This study has not shown that an agency decision improves
when these fields are supplied.

The comparison also combines a retrieval rule and its fixed five-donor mean
aggregation. MAE targets a conditional median, whereas the analogue rule uses
a mean. The simple historical median is consequently a demanding relevant
benchmark, but its advantage cannot by itself prove that every retrieved
analogue is hydrologically uninformative. Record that design limitation;
do not silently replace the aggregator to obtain a better score.

## Reproduction

Run in the installed Python 3.11 foundation environment:

```bash
MPLCONFIGDIR=/tmp/limburg-mpl .venv-foundation/bin/python scripts/73_analogue_uncertainty_review.py
```

Outputs include paired intervals and row-level differences, river-exclusion
refits, a complete pair-provenance table, donor reuse counts, fourteen review
plots and the review table, and a summary uncertainty figure. Input/code
hashes are recorded in `summary.json`. Raw provider files remain local.

Validation: all 102 tests passed, including checks of unequal-storm weighting,
paired-query alignment and deterministic case selection. Repository lint,
changed-Python formatting and whitespace checks passed. All ten scientific
and review CSV outputs reproduced byte for byte in a separate output
directory; the local `reproduction.json` records their hashes. The run produces
52 interval rows and 60 paired river-removal contrasts from 96 arm refits.
