# Limburg high-water analogues: active research design

## Three linked explanatory analyses — 2026-10-15

Brian authorized the divergence, relationship and escalation paths from the
literature review. The [executed storm-response census](limburg-storm-response-results-2026-10-15.md)
adds rainfall-defined episodes and nonresponses to investigate when comparisons
are useful or misleading. Scripts 92–94 preserve earlier empirical results.
The initial [specification](limburg-storm-response-design-2026-10-15.md) and
results distinguish prospective choices from an outcome-informed forcing-window
refinement. Both 12h/24h catalogues are executed and independently audited.
These are realized-rainfall-conditioned explanatory analyses. There is no
general peer-state or AI advantage, and recovery evidence is segmentation-
sensitive. Brian retains all dissertation writing.

## Analogue distributions — 2026-10-15

Brian authorized the [distributional extension](limburg-analogue-distribution-results-2026-10-15.md)
after the scientific review and implementation plan. Scripts 90/91 score the
saved script-84 pooled donor sets over hours 1–24, preserving the RQ, full
eligible census, current representations, full-era normalization and fixed
five/ten-donor settings. All-river and other-river, measurement-quality and
country/river evidence remain visible. This extends retrospective evidence
evaluation; it does not reconstruct as-issued forecasts.

The declared five-donor primary has no clear TTM distributional advantage.
Ten-donor support can improve on the generic archive while conventional
rain/Q remains competitive. AlphaEarth's geographic increment is conditional
and can hurt cross-river distribution scores. Range coverage and width are
empirically checked, without fitting a calibration model or treating donor
agreement as a guarantee. The source-bound manifest, independent numerical
audit and reproduction receipt document execution. Brian retains all prose
and independent human-review fields.

## Event-definition robustness — 2026-10-14

[Both requested sensitivity analyses](limburg-event-definition-results-2026-10-14.md)
are complete: p95/72h and p99/120h against the held p99/72h baseline, with
fixed p99 state/response scaling and all available candidate cases. The small
TTM/state shape increment over raw/state remains favorable in direction in both
countries; Dutch five-day group uncertainty includes zero. Conventional rain/Q
beats TTM/state shape on the broader matched p95 cohorts. AlphaEarth timing
benefits vary with population, country and control, so no universal geographic
improvement is established. Generic archive duration/mean-trajectory limits
remain; this is case retrieval rather than demonstrated warning prediction.

Retain p99/72h as the main definition, with alternatives and common-onset/mapped
episode evidence visible. Earlier p95 assessment starts are not operational lead
time. Scripts 88/89 preserve prior results, replay the baseline and independently
audit all source catalogues and numerical results; 160 tests pass. No new model,
training, data request, dissertation prose or human verdict. The remaining work
is synthesis and Brian's case review/writing, not another required model run.


## Warning-threshold progression — 2026-10-14

The user-authorized [full analysis](limburg-warning-threshold-results-2026-10-14.md) adds a census of
all native Dutch threshold records and every held p99 event, plus an H1-started
analogue application. It preserves the existing research question, frozen
representations and earlier numerical runs. Current H1/H2/H3 threshold names
are provider categories, not verified inundation or historical warning labels.
German events remain in the broader analogue analysis; no equivalent German
thresholds are invented. Internal design, missing-history sensitivity and
reproduction details are in `limburg-warning-threshold-analysis-2026-10-14.md`.
Brian retains all dissertation prose and independent human-review fields.


## Cross-border completion — 2026-10-14

[The completed country readout](limburg-cross-border-completion-2026-10-14.md)
now tests pooled/domestic/foreign archives, derives German rainfall from held
radar crops and extends strengthened TTM/state geographic controls to German
catchments. Main pooled populations: Q-only 610 NL / 235 DE, rain-matched
554 NL / 210 DE, context 294 NL / 71 DE. Earlier stage statements about
unavailable German rainfall or an unexecuted geographic extension are historical.

Pooling improves German donor peak-time similarity but worsens peak magnitude;
Dutch primary archive effects are small/uncertain. TTM's main shape increment
over matched raw/state appears in both countries, with quality uncertainty
for the Dutch group interval. The new German conventional rain/Q benchmark
has lower main peak error than TTM; quality makes that difference uncertain.
Dutch AlphaEarth timing benefit is not clearly established at the German sites.
All quality/count sensitivities, provider flags and coverage losses are retained.
No national causal comparison, live forecast claim, training or new data request.

Scripts 84/85 and the evidence index document execution and numerical audit.
Independent human fields remain unchanged; Brian writes dissertation prose.

## Current evidence hierarchy — 2026-10-14

Use the [evidence index](limburg-analogue-evidence-index-2026-10-14.md) for the
current readout: expanded temporal census (81), information/reference review
(82), and matched AlphaEarth review (83). Earlier execution sections below
remain dated development history. Keep meaningful mean/ordered/state controls,
matched rain/Q and fusion sensitivities; do not treat every stage as equally
current evidence. Outcome-informed refinements remain exploratory.

**Decision date:** 2026-10-13. Internal research plan; Brian writes dissertation text.
This supersedes the four-arm RAG and three-condition information-governance
experiments in the 2026-10-11 basin-AI design. Those files remain as dated
research history and evidence-preparation aids, not chapter requirements.

## Question and contribution

> Can basin-aware AI find useful past high-water events across Limburg's Dutch
> and German tributaries, and identify when the available evidence is too
> uncertain to use?

The research test is whether learned event and catchment representations add
useful historical analogues beyond transparent hydrological summaries. The
policy connection is concrete: station identity, river relationships, rating
eras, provisional measurements and source provenance determine whether an
analogue can be trusted for cross-border evidence exchange. This is a
retrospective archive study, not an operational forecast or warning study.

## One core comparison

Use the held 512-hour assessment histories and 72 withheld response hours.
Compare the fixed representation arms in `ai-eval/representation-arms.json`:

| Arm | Role |
| --- | --- |
| R0 conventional discharge and rainfall signatures | Practical hydrological benchmark |
| R1 raw 512-hour discharge shape | Same-input temporal control |
| R2 frozen TTM-R2 discharge representation | Temporal foundation-model challenger |
| R3 prior-year AlphaEarth catchment context | Bounded geospatial increment on the common 2018+ subset |

R1 versus R2 tests the *frozen representation's* incremental value against raw
similarity on identical inputs. It does not isolate pretraining as a causal
mechanism. R0 includes rainfall, so it is the practical comparator, not a
same-input control. R3 must be compared with the same event representation
without AlphaEarth and with a simple catchment-area control. Its independent
support is limited by catchments and years, not by the count of event rows.
R4 has been tested as a fixed exploratory conventional/TTM fusion with a
matched raw-history fusion control. It is not necessary to complete the chapter.

For each query event, eligible analogues come from earlier regional storms
whose 72-hour responses have finished by the query cutoff. Select at most one
event per prior storm so one multi-gauge storm cannot fill the top-k list.
Hold the eligible queries and candidate pool fixed across paired comparisons.
Score retrieved events against the withheld
72-hour response and reviewed hydrological relevance. Report archive
counts, watercourse-specific results, paired storm-clustered uncertainty and
leave-one-watercourse-out behavior. On the corrected distinct-storm selection,
the conventional top-five analogue mean and expanding historical median are
effectively tied (peak-ratio MAE 0.6423 versus 0.6424 on 534 queries). That is
an honest baseline rather than a reason to search for new models after results.
Retain the existing measurement-concern flags in the main run and repeat the
paired comparison without flagged queries or donor events as a sensitivity.
An uncertain peak need not erase a known onset, but it may weaken a
response-based score. Following Brian's explicit request after the peak-only
results, relevance is now examined across every saved selection with whole
response shape, timing, duration, terminal behavior, rainfall and provenance.
The extension is exploratory and separately dated in the decision log. Its
census does not require a new human-labeling experiment; it cannot be described
as independent human validation. The earlier peak outcome remains reported.

The full-rating-era p99 event labels and normalization are retrospective.
They must not be described as values known at each historical onset. No
as-issued forecast skill, warning lead time or agency decision benefit follows
from this design.

## Cross-border and policy interpretation

The Dutch library remains unchanged; script 72 now supplies a separate German
Wurm library and pooled common-Q comparison. Preserve the provider's redundant-local-sensor continuity,
rating validity and provisional post-July-2021 high-flow status. Keep the two
Wurm stations nested within one watercourse; do not count them as independent
tributaries. Use only inputs that can be aligned on both sides, or report the
German analysis separately with its narrower input set.

Record cases where a retrieved event looks similar numerically but is
inapplicable because of river identity, rating era, quality, missingness or
provisional discharge. These failures support a bounded recommendation for
minimum cross-border identifiers and provenance fields. A source-linked
example assessment may illustrate a result after the quantitative comparison;
it is not a second RAG experiment or evidence of operator usefulness.

## What is no longer required

- No general-LLM versus RAG versus tools versus graph arm comparison.
- No 30-question generated-answer benchmark, generator selection or LLM
  scoring exercise to complete this chapter.
- No fragmented/harmonized/provenance-complete policy experiment.
- No masked-observation task or extra event-assessment benchmark solely to
  connect a RAG system to the representation comparison.

The 30-case bank, source inventory, verified basin graph, rubric and script 63
remain as optional evidence QA and historical feasibility work. They can help
check factual statements or source links, but their completion is not a gate
for the core analysis. The prior design and audits remain dated records of why
the scope was narrowed.

## Original execution and subsequent extensions

Steps 1–6 are implemented and executed. TTM has no average peak-error advantage
over raw Q on 534 Dutch queries (0.7489 versus 0.7492). On 276 common-subset
queries, AlphaEarth lowers TTM error from 0.6955 to 0.6641, but remains above
the historical median's 0.6103. The German extension preserves 338 episodes,
including 98 provisional ones, with 237 eligible exact-Q scoring responses.
Its Q-only pooled R1/R2 comparison uses 774 identical queries from 236 storms.
The execution note `limburg-analogue-steps-3-5-2026-10-13.md` records all choices,
counts, sensitivity results and source hashes.

Step 6 results are in `limburg-analogue-step6-2026-10-13.md`: paired storm/year
sampling intervals, river-removal refits, all-pair provenance and fourteen
AI-inspected case cards. For the original mean-readout peak score, the temporal
advantage is not established; the small
context improvement remains uncertain despite surviving main river-removal
checks. Context greatly increases same-gauge retrieval, which can help or
harm response similarity. Intervals are conditional on the held archive.

Independent human verdicts remain blank in the review packet. Brian's
interpretation should distinguish close peak aggregates from full-response
relevance and address the fixed mean aggregation versus a median benchmark
under MAE. No new outcome or model has been added. Interpret positive, null
and unstable results within the retrospective scope; do not infer usefulness
from a small descriptive error difference.

The subsequent full-census note `limburg-analogue-census-2026-10-13.md` records
a richer result: modest TTM-versus-raw and AlphaEarth-versus-TTM/area shape
increments across the fixed actual analogue sets. Timing and high-water
duration have different readings; rain/Q signatures remain a strong Dutch
comparator. Every main-run set appears in the chronological atlas, while all
quality-sensitivity selections appear in the diagnostics. No representation
was retrained or selected using these expanded outcomes. Treat the full
response as historical evidence to inspect, keeping shape, magnitude and
timing separate rather than reducing usefulness to a single mean-peak score.

The latest authorized exploratory pass is recorded in
`limburg-representation-strengthening-2026-10-13.md`. It keeps original
controls while comparing ordered TTM readout and matched discharge-state
blocks; AlphaEarth is checked against common-frame rain/Q, gauge identity,
static 2017 context and a separately validated metric-grid export. The
original pooling freeze was a first-pass implementation choice, not a
scientific ban on testing a motivated alternative. These variations leave the
research question, held observations, donor timing rules and source-quality
treatment intact. No best-score search or model training is introduced.

## Authorized cross-river and retrieval extension

Brian subsequently authorized script 78's other-physical-river donor scenario,
actual-disagreement census, fixed 3/5/10-storm neighborhoods, donor-spread/error
assessment and one equal-block conventional/TTM fusion with matched raw fusion.
The scenario retains observed query histories and uses completed distinct prior
storms. It is a retrospective donor-availability test. The ten-storm minimum
holds k comparisons on the same queries; it does not replace the original
five-storm run or create a new chapter-wide gate. All archives, k values,
quality sensitivities and mixed results remain reported. See
`limburg-cross-river-checks-2026-10-13.md`; no additional data or training.

## Tightened preparation for event-level interpretation

Script 80 prepares the full held-event inventory, 964 Q-only input histories
and 851 complete admissible responses, including 58 additional frozen inputs
and 56 additional complete responses. Original matched rain/Q and AlphaEarth
comparisons remain separate and unchanged. Short/no donor archives remain
visible rather than being excluded from interpretation by a comparison cutoff.

The own-history reference is cutoff persistence with undefined peak timing;
the added historical reference is an equal-group-mass median with a midpoint
half-mass rule. Both are joined to every original scored query set. They are
explicit reference checks, not new trained models or proof of added event
understanding. Response-phase fields verify what followed cutoff, without
entering retrieval. Blank, editable review fields separate the history-only
assessment, donor information added, observed verification and uncertainty.
The extra vectors are ready; broader retrieval and those verdicts remain
pending. See `limburg-event-interpretation-readiness-2026-10-13.md`.

## Subsequent execution

The preparation described above is followed by the completed expanded event
pass in `limburg-expanded-event-pass-2026-10-13.md`. Earlier pending statements
record the preparation stage. Script 81 uses available short archives and
keeps unavailable queries explicit; no original comparison or human review
field is replaced. Quantitative verification is complete; human relevance
judgments remain unfilled.

## Subsequent detailed geographic-context review — 2026-10-14

AlphaEarth remains an explicit landscape-context arm. Its controlled donor
changes and actual event cases are evaluated in
`limburg-alphaearth-detailed-review-2026-10-14.md`, including geographic blocks
with the existing strengthened temporal/state readout. The original paired
mean-readout comparison remains preserved. Annual/static, area/identity and
five/ten/quality sensitivities distinguish routing and donor timing from
claims of overall predictive superiority or causal landscape change. No model
training, new data requirement or chapter gate; Brian writes all prose.
