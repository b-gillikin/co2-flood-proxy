# Limburg high-water analogues: active research design

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
R4 fusion remains optional only if R0 and R2 have useful, distinct behavior;
it is not necessary to complete the chapter.

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

## Next work

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
AI-inspected case cards. The temporal advantage is not established; the small
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
