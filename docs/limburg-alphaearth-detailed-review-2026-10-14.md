# AlphaEarth: detailed donor and event-information review

Internal research aid; Brian writes dissertation prose. AlphaEarth is an
explicitly evaluated landscape-context component of the active chapter. This
pass reviews its donor choices and conditional contributions instead of assuming
that its value disappears because a temporal representation is stronger.
All numerical results are retrospective; AI-assisted case notes are separate
from independent human validation.

## What was tested

Use the existing 304 complete AlphaEarth/context inputs and 296 admissible 72h
responses. There are 290 queries with available completed prior onset groups,
271 in the existing measurement-concern sensitivity. Six no-archive episodes
remain visible. Use available short archives rather than the earlier universal
20-event/ten-group comparison restriction; every arm shares identical events,
candidate pools and actual donor counts. Retain the original narrower results.

Two fixed temporal representations are examined on this same context population:

- Original family: mean-pooled frozen TTM, preserving the earlier AlphaEarth
  comparison and reproducing its old donor/rank/distance controls on shared IDs.
- Strengthened family: the already-held ordered TTM patch vectors plus the
  same observed discharge-state block supplied to all controls. This checks
  whether geography contributes beyond the stronger existing event readout.

Each family has temporal-only, plus area, plus gauge identity, plus fixed-2017
AlphaEarth, and plus prior-year annual AlphaEarth controls. Area is log
catchment area; identity is one-hot gauge identity. Spatial vectors are the
same held normalized 64-dimensional catchment means. All added context blocks
use the existing equal-RMS-block distance rule; state retains its existing
robust scaling. No training, weight search, new checkpoint, data download or
new model roster. Adding context redistributes block contributions; controls
use the same rule so context representations are compared fairly.

Use all rivers and other physical rivers only, five- and ten-donor nested
prefixes, main and quality checks. A single onset-linked group contributes at
most one donor, with its whole response completed before the query cutoff.
Wurm/Worm remains one physical river. The group labels are not independently
verified meteorological storms. Conventional rainfall/Q is a matched benchmark.
The generic eligible archive is also retained as a group-balanced reference.

This review's direct matched comparisons cover **six Dutch gauge catchments**,
not the full pooled NL/DE cohort. Held exports also include Herzogenrath 1 and
Randerath, plus the inventory-only Dutch gauge 6.Q.25: these data are present,
not awaiting download. They are explicitly listed in `held_context_assets.csv`.
Using them in a broader Q-only context cohort would be an available extension,
not a missing-data requirement or a conclusion established by this six-site
comparison. Do not claim that this pass validates German geographic transfer.

## What AlphaEarth changes

On five-donor main queries, the strengthened annual AlphaEarth arm replaces
an average **3.09 donor events** relative to temporal/state alone with all rivers,
and **3.28** with other rivers. It retains about 2.65 and 2.35 onset groups,
respectively. Some changes therefore swap gauges within a retained regional
onset group rather than add a new independent historical episode.

With all rivers allowed, the slot-weighted same-gauge share rises from **30.9%**
temporal/state to **77.9%** annual AlphaEarth. Identity reaches 94.7%, and fixed
2017 context 85.3%. Geography often brings the retrieval back toward known
catchment behavior, but AlphaEarth is not equivalent to selecting only one's
own gauge. These shares use the actual five-donor slots; early short archives
have fewer slots.

With other rivers required, identity supplies the same constant different-gauge
penalty to every candidate and cannot change donor order. That is verified for
both temporal families and sensitivities. Annual and fixed AlphaEarth still
change which other catchments and events are selected. Area-only emphasizes
similar physical size; landscape-vector similarity can select different donors.
A smaller embedding distance is partly a consequence of the selection rule,
not independent proof of physical hydrological suitability.

Every donor replacement is saved, with entered/exited shape mismatch and
retained event/group counts. The difference in mean individual shape error
exactly equals the entered-minus-exited error sum divided by the common actual
donor count. This explains where a change comes from without using outcomes
to choose or rerank the donors.

## Does that improve the comparison?

Five-donor main strengthened-family results, 290 matched queries:

| Context | Shape mismatch, all rivers | Peak absolute error, all rivers | Donor peak-time mismatch (h), all rivers | Shape mismatch, other rivers | Peak absolute error, other rivers | Donor peak-time mismatch (h), other rivers |
|---|---:|---:|---:|---:|---:|---:|
| Temporal + state | 0.2096 | 0.6283 | 10.81 | 0.2159 | 0.6566 | 10.96 |
| + area | 0.2077 | 0.6274 | 10.66 | 0.2212 | 0.6405 | 10.17 |
| + identity | 0.2090 | 0.6242 | 10.84 | 0.2159 | 0.6566 | 10.96 |
| + fixed-2017 AlphaEarth | 0.2074 | 0.6267 | 10.84 | 0.2184 | 0.6613 | 10.07 |
| + annual AlphaEarth | 0.2076 | 0.6132 | 10.43 | 0.2187 | 0.6702 | 9.82 |
| Conventional rain/Q | 0.2014 | 0.6421 | 10.25 | 0.2093 | 0.6507 | 10.14 |

Shape is the mean of individual query-to-donor peak-scaled response mismatches.
Peak error evaluates mean donor maxima against the query maximum in Q/own-era
p99. **Timing is mean absolute mismatch between each donor's first response
maximum and the query's first maximum.** It is not forecast peak-time error,
warning lead time or a prediction from the peak of a mean curve.

### Original mean-TTM family

The earlier modest all-river shape increment survives the broader matched
context census: annual shape mismatch 0.2125 versus temporal 0.2259 (about
5.9% lower); paired query-group difference -0.01343 [-0.01949, -0.00735].
Against area, the difference is -0.00654 [-0.01097, -0.00204].

The remaining difference against identity (-0.00097) and fixed-2017 context
(-0.00204) has group/year intervals including zero. Conventional rain/Q has
lower shape mismatch. Thus the original mean representation's gain is real
relative to its stated temporal/area controls, while much of the benefit can
also be produced by stable catchment context or identity. It does not uniquely
establish annual learned landscape information.

### Stronger temporal/state family

At five donors, annual context's all-river shape difference from temporal/state
is -0.00200 [-0.00631, +0.00213]; its cross-river difference is +0.00284
[-0.00285, +0.00799]. Most shape benefit from the original comparison is no
longer a clear incremental gain over the stronger event-history representation.
Peak, whole-curve and duration contrasts against temporal/state and most simple
context controls also include zero. No overall AlphaEarth accuracy winner.

There is a more specific cross-river timing increment: **-1.140 hours** relative
to temporal/state, query-group interval [-1.852, -0.480] and year-block interval
[-2.184, -0.387]. The quality check is -1.085 hours with favorable group/year
intervals. Directions vary by river: Geleenbeek worsens, Voer changes little,
and four rivers improve. This is conditional response-timing relevance,
not uniform superiority or a geographic mechanism identified from embeddings.

A fixed-2017 context also improves cross-river timing by about 0.884 hours in
point summaries. Annual minus fixed is -0.256 hours, with intervals including
zero at five donors. Area is competitive; annual minus area is -0.356 hours
with intervals including zero. Stable geographic context explains much of the
five-donor point gain.

### Ten donors: retain the additional evidence and its sensitivity

At ten donors, annual context's cross-river timing difference from temporal/state
is **-1.278 hours**, group interval [-1.714, -0.874], year interval
[-2.042, -0.728]. Annual minus area is -0.931 hours with favorable main group/year
intervals. Annual minus fixed-2017 is **-0.631 hours** [-0.934, -0.332], with a
favorable main year interval too.

That annual/static increment is weaker in the quality check: -0.320 hours,
group interval [-0.621, -0.032], but year interval [-0.582, +0.037]. Ten-donor
main shape also has a small favorable group contrast against fixed context;
it is not a general improvement across outcomes and settings. Preserve all
five/ten and quality/year results rather than choose the setting that supports
a preferred story. The evidence does not justify saying annual updates never
help, or that annual updating is essential.

Annual/static comparisons also change the prior-vector RMS scale because
annual vectors and fixed vectors form different prior clouds. They compare
complete retrieval representations under the same rule, not a causal experiment
that isolates annual landscape change from all scaling effects.

### Specificity versus the eligible archive

Strengthened annual AlphaEarth retrieves individually closer shapes than the
generic eligible archive: 0.2076 versus 0.2400 all-river; 0.2187 versus 0.2446
cross-river. Existing temporal/state retrieval already supplies much of this
specificity. The generic archive has lower duration error in point summaries;
no overall continuation-prediction advantage is established. This preserves
the prior review's distinction between selecting relevant precedents and
averaging them into an accurate single continuation.

All intervals use 9,999 paired query-group/year resamples, seed 20261013,
conditional on the prepared archive. There are six geographical units despite
many event rows, and only eight query years in this context sample. Intervals
do not cover reused-donor, observation, pretraining or exploratory
multiple-comparison uncertainty. A favorable interval is not human relevance
validation or proof of a causal landscape attribute.

## Actual event review

All 296 eligible context responses remain in the coverage/census table, with
method evidence for 290. Visual AI-assisted interpretation covers 18 cases
selected by date/prior donor spread (three per river), plus eight explicitly
outcome-selected benefit/deterioration illustrations across both families and
river scenarios. All 26 figures were inspected. The reviewer is not independent
or formally blinded; these are research-aid notes, not human labels or a
representative success-rate sample.

Examples make AlphaEarth's contribution and its limitations concrete:

- **Eyserbeek, 8 December 2025:** annual context removes a false middle-window
  renewed rise present in temporal, fixed, area and identity means, while still
  overestimating the initial level. A genuine local annual/static difference;
  an illustration cannot establish global annual superiority.
- **Worm, 24 December 2018:** annual and fixed geography better reproduce the
  late recession background than temporal, area or identity. A stable-context
  contribution with little uniquely annual interpretation.
- **Worm, 18 August 2019:** annual/fixed context select more rapidly receding
  responses than temporal/state, but retain one irrelevant later donor surge.
  Partial shape gain and misleading continuation information can coexist.
- **Worm, 7 February 2024:** annual context removes relevant sustained-response
  examples and implies recession too quickly. Fixed context and area retain
  more of the observed persistence. Geography can also steer retrieval badly.
- **Geul, 31 January 2018:** only one prior onset group is available. Geography
  chooses a different gauge response within that group and better retains
  background, but puts the secondary rise too early. This is not additional
  independent storm evidence; a zero donor spread would not mean certainty.
- **Gulp, 30 April 2018:** only three prior groups. Annual and fixed contexts
  overstate late activity; temporal, area and identity are closer. All miss the
  early observed rise. Retain this case rather than exclude its short archive.
- **Voer, 17 August 2024:** the outcome-selected annual arm has worse normalized
  individual shape matching but a late background visually closer to the query.
  All miss the early peak. A shape deterioration is not automatically worse
  performance on every outcome.
- **Geleenbeek, 18 November 2019, and Geul, 26 February 2024:** landscape-aware
  donors add later rises absent from the query. A small context-vector distance
  is insufficient evidence of interchangeable event continuation.
- **Worm, 9 September 2025:** every context control misses the delayed large
  surge. AlphaEarth does not infer the unseen future storm forcing from a
  catchment's landscape representation.

Exact per-case notes and donor IDs are in
`reviews/limburg-alphaearth-case-notes-2026-10-14.json` and local `case_facts.csv`.
The source identifies all 26 cases and their selection basis. Human review
fields in the existing packet remain untouched.

## How this belongs in the chapter

Keep AlphaEarth in the methods, matched results and case discussion as the
**landscape-context test of which past events are comparable**. Its demonstrated
role is donor routing plus some conditional response-timing information, with
concrete gains and failures. The richer temporal/state representation makes
its residual contribution smaller and more specific, not absent by assumption.

The results do not support treating annual landscape change as a cause of
flood response, decoding individual embedding bands into known physical
attributes, or claiming global superiority over area/identity/static controls.
Annual imagery years are prior to each event, but the current embeddings and
TTM assets were not necessarily available as issued at those historical dates.
The full-era p99 and finalized provider revisions also keep this retrospective.

For the FEWS/policy discussion, an inspectable analogue assessment can expose
how adding geographical context changes its precedents and whether a simpler
physical-size or identity control gives a different story. That is a plausible
analyst-training or event-review use; operator decision quality, warning lead
time and DRR benefits are untested. Do not convert own-era p99 or embedding
similarity into an agency warning phase or a calibrated probability.

No automatic method promotion, elimination, preregistration requirement,
additional dataset request or new chapter gate follows from these results.
Both temporal and geographic foundation components now have explicit empirical
roles and limits. Brian can write the chapter around this comparison without
requiring either component to win every metric.

## Artifacts and validation

Runner: `scripts/83_review_alphaearth_event_information.py`.
Ignored outputs: `results/basin_ai_alphaearth_information_review/`.

- `query_evidence.csv`, `selected_donor_evidence.csv`: 24,684 score sets and
  118,503 top-ten donor slots, with five/ten prefixes and context metadata.
- `context_coverage.csv`, `event_comparison_census.csv`: all 296 response
  episodes, including six no-archive events with missing estimates.
- `donor_set_changes.csv`, `donor_change_summary.csv`: 17,952 replacement
  decompositions, event/group overlap and changes in shape mismatch.
- `donor_context_by_k.csv`, `paired_river_directions.csv`: routing and
  physical-river directions; geographic proximity is descriptive, not validation.
- `summary.csv`, `by_river.csv`, `paired_intervals.csv`,
  `generic_context_archive.csv`: common-frame controls and archive references.
- `review_cases.csv`, `case_facts.csv`, `cases/`, `ai_case_review.csv`:
  case selection, explicit controls, shared response-axis scales and attributed
  AI observations. Human verdicts remain unfilled.
- `held_context_assets.csv`: nine held catchment exports and the six included
  in this matched test; German context assets are present.
- `old_control_replay.csv`, `static_original_replay.csv`, `validation.json`,
  `manifest.json`: reproducibility, model/data/output fingerprints and checks.

Independent checks reconstruct every pair-response metric and every scored
peak/curve/duration/late-level aggregate to 1e-12. All 1,120 interval rows are
recomputed. All 20 original cross-river control configurations reproduce donor
IDs, ranks and distances on their old shared IDs. Fixed-2017 original all-river
controls reproduce on 276 main / 257 quality queries. All 1,122 archive curves
have independent groupby verification. Cross-river identity matches temporal
rankings exactly. Tests verify matched temporal/state blocks, identity's
constant cross-river penalty and event-versus-group replacement accounting.
The full suite passes 133 tests; repository lint, changed-code formatting and
whitespace checks pass. Old scientific results and human fields are unchanged.

```sh
MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/83_review_alphaearth_event_information.py

# Verify saved retrieval/results and regenerate research aids:
MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/83_review_alphaearth_event_information.py --audit-existing
```
