# Session handoff

Updated 2026-10-13 after the census and authorized representation checks.
Canonical design: `limburg-historical-analogue-active-design-2026-10-13.md`.
Execution/results: `limburg-analogue-steps-3-5-2026-10-13.md`.
Uncertainty/review: `limburg-analogue-step6-2026-10-13.md`.
Census: `limburg-analogue-census-2026-10-13.md`.
Latest checks: `limburg-representation-strengthening-2026-10-13.md`.

## Active question

> Can basin-aware AI find useful past high-water events across Limburg's Dutch
> and German tributaries, and identify when the evidence is too uncertain to use?

One retrospective representation comparison: conventional rain/Q signatures,
raw 512-hour Q shape, frozen TTM-R2, and a bounded prior-year AlphaEarth
increment. River identity and measurement provenance determine applicability.
No RAG-arm experiment, model training or operational forecast claim.

## Executed state

- Dutch inventory: 724 events; 570 complete common inputs, 558 complete
  responses. R0/R1/R2 share 534 queries from 186 storms. Peak-ratio MAE:
  R0 0.6423, raw Q 0.7492, TTM 0.7489, historical median 0.6424.
- Existing measurement-concern sensitivity: 497 paired queries; R0 0.5555,
  raw Q 0.6282, TTM 0.6352. No temporal learned-representation advantage yet.
- AlphaEarth delivery and prior-year join are validated. The 2018+ comparison
  has 304 complete inputs, 296 outcomes, six catchments/45 catchment-years;
  276 queries from 99 storms. Fixed TTM 0.6955, +area 0.6946, +AlphaEarth
  0.6641, historical median 0.6103. Context increment is descriptive and
  still trails the median; event rows are not independent catchment evidence.
- German Herzogenrath 1/Randerath delivered stage/Q converted by script 72:
  338 episodes, 336 complete known-onset Q histories, 237 exact-Q scoring
  responses. All 98 provisional episodes remain in the inventory, outside
  exact-Q scoring. Provider literal curves/domains, fixed UTC+1, complete
  trailing-hour means and unflagged redundant-local-sensor continuity remain
  explicit. Current datum does not guarantee historical datum stability.
- Common Q-only NL/DE run: 774 paired queries/236 storms, raw Q 0.6751,
  TTM 0.6969, historical median 0.5874. Country/watercourse scores saved
  separately. Regional storms are reclustered over the whole inventory;
  German Wurm and Dutch Worm form one physical river group. German
  rainfall/weather are unavailable in this pass, so no German R0/R3 claim.
- Scripts 70–72 save tidy paired results, representations, selected donors,
  quality flags and input/code hashes under ignored `results/` directories.
  Raw provider files remain local. Pinned inference runtime is installed in
  ignored `.venv-foundation`; use Python 3.11, not the shell's Python 3.9.
- The earlier source-card/RAG pilot is optional evidence QA/history only.
- Step 6: 9,999 paired query-storm resamples, year-block sensitivity, and
  six physical-river removals per cohort/sensitivity. TTM-minus-raw Dutch
  difference -0.0003, 95% interval [-0.0582, 0.0583]; pooled difference
  +0.0218 [-0.0250, 0.0679]. No temporal representation advantage established.
- AlphaEarth-minus-TTM difference -0.0315 [-0.0836, 0.0204]. Main point
  improvements survive all six river removals, but same-gauge donor share
  rises from 27.1% to 83.6%. Catchment identity is not response suitability.
- Every selected pair was audited for provenance; fourteen illustrative
  cards were inspected with AI assistance. Human verdicts remain blank.
  Conditional sampling intervals do not cover donor/measurement uncertainty.
- Validation: 102 tests passed. The earlier 54 Step 3–5 outputs and all ten
  Step 6 scientific/review CSV tables reproduced exactly in separate runs.
- User-authorized exploratory extension: script 74 reviews every saved
  selected slot (38,540; 14,318 distinct query–donor pairs), all 774 distinct
  queries, and the full eligible reference pools without sampling. All 1,062
  held episodes remain in a coverage table. The complete main-run atlas has
  133 chronological pages, indexed by gauge/date in a local HTML document.
- Full-response shape differs from mean-peak prediction: TTM improves average
  peak-scaled shape mismatch by 2.7% Dutch / 3.4% pooled versus raw history,
  with favorable conditional storm/year intervals and mean directions on
  every river. AlphaEarth improves shape by 6.4% versus TTM and 2.9% versus
  the area control. These are exploratory, modest increments.
- Timing/duration do not consistently improve; Dutch TTM timing is worse.
  Conventional rain/Q remains better on Dutch shape and level. Census
  diagnostics distinguish individual donors from averages, rainfall context,
  and response segments that may start in recession or end before high water
  is over. No numerical metric becomes an automatic human relevance verdict.
- Census validation: 108 tests passed; ten scientific CSV tables reproduced
  exactly. All 55 input/code hashes and every atlas/query index entry checked.
- Scripts 75–77 now execute exploratory, fixed pooling/state and context
  controls. Ordered TTM preserves all eight patch states. A matched observed
  state block is supplied equally to raw/mean/ordered controls using only
  prior-pool scaling. No training, architecture change or weight sweep.
- Dutch ordered TTM + state: peak MAE 0.6389, shape RMSE 0.2008; rain/Q
  benchmark 0.6423/0.1997. Point proximity is not an equivalence result.
  Against matched raw + state, ordered TTM adds a shape increment -0.0064
  Dutch / -0.0057 pooled, with favorable storm/year intervals and quality
  sensitivity. Pooling alone improves timing; state accounts for much of
  the peak gain in both raw and learned representations.
- AlphaEarth's common-frame rain/Q benchmark now runs on identical 276-query
  pools. Gauge identity nearly matches its shape gain; the residual difference
  and annual-versus-static difference remain uncertain. Do not claim that
  the six-site result uniquely establishes learned hydrological attributes.
- Projection check complete: explicit 10-m EPSG:3035 table downloaded and
  compared with the original angular-grid export. Direction changes <0.000314;
  no main or quality donor set changes. Original CSV preserved.
- Latest validation: 112 tests passed; all 51 scientific CSV outputs reproduced
  exactly, 56 input/code hashes checked, 588 finite interval rows, and all donor
  sets verified as five distinct eligible prior storms. Repo lint/format passed.

## Next work: event interpretation and cross-river application

Read the latest checks note before interpreting the original model scores.
All 102,645 new selected slots / 20,529 sets have census diagnostics; all
seven outcomes have paired intervals and river summaries. Sixteen original
control configurations replay their previous predictions. The new tables and
comparison figures are under `results/basin_ai_representation_checks/`.

The census corrects the earlier narrow relevance assessment. Open
`results/basin_ai_analogue_census/index.html` for all main-run actual analogue
sets; browser Find locates a date or gauge. Detailed tables also cover every
quality-sensitivity selection. The fourteen older case cards remain historical
illustrations, not the basis of the census. Brian writes the interpretation;
independent human validation has not been claimed or made a new requirement.
That atlas depicts the original settings; the latest donor identities are in
the new selected-pair tables.

Discuss the fixed mean-of-five aggregation versus a median benchmark under
MAE, the distinction between peak error and full-response relevance, and the
limited independent catchment support. No change of aggregator or model has
been made in response to these results.

A purposeful possible next AlphaEarth scenario excludes same-river donors,
asking about finding other-river analogues when a local archive is absent.
It retains observed query histories, so it is not an ungauged-flow prediction
test. This is not yet run or a chapter requirement. Interpretation of actual
event successes/failures can continue independently. No extra data request.

Preserve null/mixed results alongside the exploratory shape evidence. The
expanded relevance assessment was explicitly requested by Brian; earlier
peak-only conclusions must not be generalized to every meaning of usefulness.
Keep the existing retrievals and report all diagnostics, rather than choosing
a favorable metric or tuning weights after the census.
The rating-era p99 labels/scaling remain retrospective; neither these scores
nor a relevant analogue establish live warning skill or operator benefit.
