# Expanded event-level analogue evidence

Internal numeric results and interpretation aid for Brian, not dissertation
prose. The expanded retrieval and quantitative event-level verification are
complete. Human relevance judgments remain blank; numerical agreement is not
a substitute for them.

## What ran

Script 81 uses the prepared Q-only census from script 80: 964 complete
histories and 851 complete, admissible 72h responses. The 56 additional Dutch
scorable events now participate in retrieval. The entire held inventory of
1,062 episodes remains available, including uncertain or incomplete records.
No new model, training, data request, outcome-based ranking or forecast claim.

The unchanged distance definitions compare standardized raw 512h histories,
raw histories plus observed discharge state, and ordered frozen TTM plus the
identical state block. Dutch-only and pooled NL/DE archives are each examined
with all physical rivers or other physical rivers only, and with the existing
measurement-concern sensitivity. German Wurm and Dutch Worm are one physical
river. Historical rain/Q, AlphaEarth and matched fusion results are preserved
in a companion table; they are not reinterpreted as newly fitted Q-only arms.

Five- and ten-donor estimates use the same nested ranking. Where fewer groups
are available, use that number rather than discard the query. An onset-linked
regional group contributes at most one donor; its full response must have
finished before the query cutoff. These groups are not verified meteorological
storms. Query future responses never enter the similarity calculation. Group identities
exclude or deduplicate related episodes.

| Population | Scorable | At least one prior group, main | Quality sensitivity |
|---|---:|---:|---:|
| Dutch Q-only | 614 | 610 | 567 |
| Pooled Q-only | 851 | 845 | 802 |

Counts are the same across arms and across the two river scenarios. Four Dutch
and six pooled episodes have no available earlier donor group. They remain
explicitly unavailable in the coverage table. Of 845 main pooled queries,
15 all-river and 17 cross-river queries have fewer than five donor groups.
`by_archive_status.csv` separates short archives from the original comparison
availability condition; that condition is not a universal research gate.

## What the census says

Five-donor main results below include available short archives. Level and peak
errors use Q / each event's own full-era p99; shape normalizes each response
by its own maximum for evaluation only. Lower values are better. The peak
estimate is the mean of donor peaks, not the peak of the mean donor curve.
Duration is hours above p99 inside the following 72h, not complete flood
or historical warning duration.

| Pooled scenario / method | Peak absolute error | Mean donor shape mismatch | Mean-curve level RMSE | Duration estimate error (h) | Final 24h mean level error |
|---|---:|---:|---:|---:|---:|
| All rivers: raw + state | 0.5996 | 0.2005 | 0.3560 | 7.704 | 0.1744 |
| All rivers: TTM + state | 0.6010 | 0.1961 | 0.3504 | 7.417 | 0.1656 |
| Other rivers: raw + state | 0.6501 | 0.2063 | 0.3721 | 8.016 | 0.1789 |
| Other rivers: TTM + state | 0.6464 | 0.2033 | 0.3668 | 7.789 | 0.1744 |
| Cutoff persistence, same pooled queries | 0.5870 | Not an analogue set | 0.8223 | 63.531 | Not tabulated |

Persistence is deliberately weak for response trajectories: it assumes no
recession. Ordinary historical analogues improve strongly over it too. These
comparisons show added response information relative to that explicit minimum
reference, not superiority over every possible use of the event's own history.
Current discharge already provides a strong peak-magnitude reference.

The matched AI increment is small and specific:

- Pooled all-river TTM reduces shape mismatch by 0.00445 (about 2.2%) versus
  raw + state; paired query-group interval [-0.00765, -0.00151]. The year-block
  and measurement-quality sensitivities support the same direction.
- Pooled cross-river shape reduction is 0.00305 (about 1.5%); group interval
  [-0.00614, -0.00016], with favorable year and quality checks. This is a
  modest response-matching increment, not a peak or warning-skill result.
- All-river final-24h level error improves by 0.00878 (about 5.0%); group
  interval [-0.01612, -0.00159]. Year and quality checks support this small
  recession-level increment. Dutch-only results also support it.
- Cross-river final-24h level improvement is uncertain. Neither pooled scenario
  establishes a TTM advantage for peak magnitude or duration; their paired
  intervals include zero. Timing differences are also small in point summaries.
- In the broader Dutch cross-river census, the shape interval now includes
  zero: -0.00331 [-0.00673, +0.00008], and quality does too. The earlier narrower
  positive comparison remains a historical result, not grounds to hide this.

Ten donors improve pooled TTM peak error to 0.5611 with all rivers and 0.6051
with other rivers. The corresponding all-river raw + state error is about
0.5632; no TTM-specific peak advantage is established. TTM's all-river point
advantage over persistence has group and year intervals including zero.
The group-balanced archive-median contrast is more favorable, but the matched
raw control improves too. Do not choose k or a reference because it creates a
better headline. Wider averaging and finding individually closer analogues
answer different questions.

All 851 responses have a median of five hours above p99. In 372 events the
first response hour contains the maximum; eight reach their first maximum at
hour 72, and 28 are still above p99 at the end. These are verification facts,
not cutoff predictors. They explain why peak-only accuracy and shape/recession
information can tell different stories. A rise after cutoff is not necessarily
a second storm; no rainfall mechanism is inferred from curve shape alone.

## Actual examples: improvements and failures

The entire quantitative census is available, with no event sample replacing
it. Twelve illustrations deliberately select the largest favorable/unfavorable
mean-curve error changes on each of six physical rivers in the pooled main
cross-river five-donor analysis. They explain differences; they cannot estimate
success rates or validate human relevance. Four were visually inspected with
AI assistance (both Wurm examples, the Eyserbeek failure, and the Gulp failure).
No independent human verdict was entered.

- Wurm, 5 February 2013, 11:00 UTC: the query history includes preceding pulses.
  Observed Q falls below p99 by the first response hour and recedes. TTM donors
  reduce curve error relative to raw donors, whose mean implies a prolonged
  high-water response. TTM still overstates the early level and does not get
  every later wiggle right. This illustrates useful recession information and
  its residual error; it does not identify a storm mechanism.
- Wurm, 19 June 2019, 21:00 UTC: the observed response declines quickly.
  Raw donors are closer; TTM donors imply a much larger and more persistent
  response, including a later rise absent from the query. Similar embedding
  context is insufficient evidence of equivalent outcomes.
- Eyserbeek, 19 November 2024, 08:00 UTC: observed discharge reaches 2.642 p99
  at hour seven and remains above p99 for 20 response hours. Raw donors include
  a subsequent increase and better approximate the response. TTM's donor mean
  implies recession and substantially misses this rise. A close-looking history
  or modest average shape improvement does not guarantee surge identification.
- Gulp, 23 December 2024, 08:00 UTC: observed high water lasts three response
  hours. Raw analogues follow the recession closely; TTM donors overstate
  persistence and later rises. This is a failure case, not hidden by aggregate
  improvement elsewhere.

The short-archive and additional-input tables, response-phase summaries and
per-river summaries allow these patterns to be inspected without treating
illustrative extremes as representative. Donor shares are empirical descriptors,
not calibrated probabilities, and disagreement is not an automatic refusal rule.
A one-donor archive has zero within-set spread without becoming certain.

## What is and is not answered

The work now quantifies what completed historical responses add to cutoff
persistence, how learned versus raw histories differ on the same events, and
where individual examples help or mislead about the next response segment.
It supports modest learned-representation increments in shape and, with local
donors allowed, late-recession level. It does not establish universal AI
superiority, causal hydrological mechanisms, independent human understanding,
as-issued forecast skill, operational warning lead time or policy effectiveness.
The conventional rain/Q benchmark remains competitive on its original matched
population; its different input/period restrictions must stay visible.

All-era p99, finalized provider revisions and current foundation assets make
this retrospective. Intervals use 9,999 intact query-group or year resamples,
seed 20261013, conditional on the prepared donor archive. They do not resolve
reused-donor dependence, observation uncertainty, pretraining leakage or
multiple exploratory comparison/development uncertainty. Country labels are
confounded with river coverage, not an NL-versus-DE policy-effect estimate.

The next human task is to use the editable review packet to decide what an
assessment actually teaches about an event, beyond metric improvements. This
is interpretation work, not a new dataset or model prerequisite. Brian writes
all dissertation text. A useful chapter claim should center on these conditional
strengths and failure modes rather than force an overall model winner.

## Artifacts and checks

`results/basin_ai_expanded_event_pass/` (ignored scientific outputs):

- `event_browser.html`: all 851 scorable events, their complete 512h input
  histories, actual prior donor histories and next-72h verification curves;
  query, donor and persistence curves are explicitly distinguished.
- `event_assessments.csv`, `selected_donors.csv`, `coverage_including_unavailable.csv`:
  event estimates, selected identities, measurement information and no-archive rows.
- `event_method_contrasts.csv`, `summary.csv`, `by_river.csv`,
  `by_archive_status.csv`, `by_additional_input.csv`, response-phase tables:
  census contrasts and explicitly descriptive subdivisions.
- `paired_intervals.csv`: all 416 paired group/year interval rows.
- `existing_context_comparisons.csv`: preserved conventional/AlphaEarth/fusion
  evidence on its original matched populations.
- `outcome_selected_illustrations.csv`, `illustrations/`: selection record and
  twelve benefit/failure figures; response panels use shared vertical scales.
- `manifest.json`, `validation.json`: input/output/code hashes, execution settings
  and independent checks. Mutable human review fields remain in script 80's
  existing packet and are not overwritten or fabricated.

Independent verification recomputes all six pair-response metrics for 166,410
selected slots and peak, curve, duration and late-level aggregate errors for
all 33,888 score sets (maximum tolerance 1e-12). Every paired interval is
recomputed, with chronology, unique-group and physical-river exclusion checks.
All prepared and saved data fingerprints pass. Browser data contain exactly
851 complete histories/responses and every referenced donor ID; embedded
JavaScript passes syntax checking. The full suite passes 126 tests.

```sh
MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/81_run_expanded_event_analogues.py

# Verify saved results and regenerate research aids without reranking donors:
MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/81_run_expanded_event_analogues.py --audit-existing
```
