# Limburg basin-aware AI: active development design

**Status:** historical internal research design, 2026-10-11; superseded on
2026-10-13 by `limburg-historical-analogue-active-design-2026-10-13.md`.
The four-arm RAG and three-condition policy experiments below are no longer
chapter requirements. Brian writes all dissertation text. This dated document
is retained to show the design's development.

## Research question

> **Can basin-aware AI produce reliable cross-border high-water assessments
> from fragmented Dutch and German data?**

Two supporting questions make the test and the policy contribution explicit:

1. Does combining river connections, historical event analogues and data
   provenance improve assessments compared with text-only AI?
2. Which gaps in agency data and standards most limit reliable, auditable
   assessments?

“Reliable” must be resolved into measured outcomes: factual accuracy, correct
station and river identity, appropriate use of historical rules, measurement-
quality handling, analogue relevance, unsupported-claim rate and calibrated
abstention. This retrospective study does not measure whether officials make
better decisions.

## Scientific architecture

The language model is an evidence synthesizer, not the hydrological model. The
system has four linked evidence layers:

1. **Documents and institutional rules:** dated provider correspondence,
   technical reports, warning conventions and agency responsibilities.
2. **Basin and provenance graph:** rivers, stations, jurisdictions, providers,
   rating periods, quality semantics and explicitly verified topological
   relationships.
3. **Historical event library:** aligned rainfall, discharge or stage, weather,
   cross-station response, missingness and measurement limitations for reviewed
   high-water episodes.
4. **Event and catchment representations:** conventional hydrological
   signatures as the mandatory baseline; one open time-series foundation model
   as a challenger; AlphaEarth catchment embeddings as a challenger to ordinary
   catchment attributes.

Retrieval is constrained by time, jurisdiction, river identity and evidence
quality before the LLM receives an evidence packet. Checked tools perform all
numerical calculations. Outputs identify supporting sources, calculations,
unresolved conflicts and insufficient evidence.

## Core comparisons

Two experiments answer different questions and must not be collapsed into one
arm ladder.

The **evidence-access ablation** uses A0--A3 from `system-arms.json`: the same
fixed generator receives no study evidence, curated source cards, source cards
plus checked tools, or those components plus the curated basin graph. This
tests the incremental effect of each evidence route on the 30-case
source-grounded benchmark. The general-LLM arm is a diagnostic reference;
the main evidence-access comparisons are A1--A3. The current source cards are
researcher-written summaries of held material, not raw-document retrieval.

The **historical-representation comparison** uses R0--R4 from
`representation-arms.json`:

| Arm | Evidence available | Purpose |
| --- | --- | --- |
| R0 | Conventional discharge-and-rainfall signatures | Interpretable practical analogue baseline |
| R1 | Raw standardized 512-observation discharge history | Same-input hydrograph-shape control |
| R2 | Frozen TTM-R2 representation of the identical discharge history | Isolated test of temporal pretraining |
| R3 | Prior-year AlphaEarth context on the common 2018+ subset | Bounded test of learned catchment context |

The cleanest representation contrast is R1 versus R2 because those arms receive
identical inputs. It tests the incremental value of the frozen TTM
representation relative to raw-sequence similarity; it does not isolate the
effect of pretraining from every other difference in representation and
distance. R0 is a practical hydrological benchmark with additional rainfall
information. R3 compares the same event representation with and without
learned catchment context and includes catchment area as a simple held-data
control. Its effective support is catchment/catchment-year, not the number of
event rows. A fused R0+R2 arm is conditional on different, individually useful
retrieval behavior. The generator model, prompt and decoding settings stay
fixed across evidence-access arms.

## Evaluation tasks

### Source-grounded assessment

The existing 30-case question bank tests station identity, applicable rules,
measurement provenance and justified abstention. It is a focused
evidence-handling benchmark, not yet a test of complete high-water situation
assessments. Before claiming that historical analogues improve AI assessments,
add a small, source-checked set of event-level tasks drawn from the held event
library. Keep those tasks separate from the original 30 factual cases and
review their gold answers before generation.

### Historical analogue retrieval

Given only information available by a declared assessment time, retrieve prior
events that are similar in storm forcing, antecedent state and tributary
response. Compare conventional hydrological signatures with pretrained
representations. Score the retrieved events against held-out response
properties and hand-reviewed hydrological plausibility.

### Masked-observation assessment

Hide a target observation, quality flag or source fragment from a known event.
Ask the system to characterize the event from the remaining Dutch and German
evidence. Score the recovered high-water state, provenance, river identity,
uncertainty and decision to abstain. Artificial masks must be labelled as such;
they do not turn the retrospective experiment into a live forecast evaluation.
The hidden fact must be removed from every accessible source card, tool result,
graph annotation and event packet for that case, not only from the displayed
time series.

## Policy experiment

Evaluate the same tasks under three information environments:

1. **Fragmented:** records substantially as agencies supplied or published
   them.
2. **Harmonized:** shared station identifiers, units, timestamps, river names,
   jurisdiction and verified topology.
3. **Provenance-complete:** harmonized records plus available rating validity,
   datum history, threshold versions and measured/reconstructed/interpolated/
   provisional status.

Within this fixed benchmark, the performance differences estimate how the AI
system responds to improved information governance. They do not estimate the
effect of harmonization on real agency decisions or flood outcomes. The
remaining failures and justified abstentions identify candidate fields that
agencies would need to preserve or exchange. The potential policy product is a
minimum cross-border evidence standard for AI-supported assessment, derived
from observed system errors rather than asserted in advance.

These are constructed evidence conditions, not historical agency states. Hold
questions, underlying facts and the generator fixed across conditions; document
exactly which identifiers or provenance fields were made available. A condition
with less information must not be scored against facts it could not establish
without treating justified abstention as a correct response.

## Operationalization recommendation to retain

If the retrospective evaluation succeeds, the plausible government use is an
auditable assessment layer alongside existing FEWS infrastructure. It could
begin with archive review and data-quality checking, proceed to live shadow
mode, and only later become operator-facing decision support. It would assemble
evidence and expose uncertainty; it would not replace hydrological models,
issue public warnings or remove operator authority.

Operational claims require later live feeds, authoritative identifiers,
security, versioned models and metadata, audit logging, operator evaluation and
clear responsibility for conflicts. These are recommendations and future
validation needs, not dissertation implementation requirements.

## Scope guard

The bounded dissertation experiment uses one cross-border regional case,
historical data already held or openly obtainable, one fixed language model,
one time-series foundation-model challenger and one geospatial embedding
product. It does not require:

- a new foundation model or broad fine-tuning programme;
- a full FEWS dashboard or production deployment;
- automatic warnings or claims about operator behavior;
- a survey of every hydrology, weather or geospatial foundation model;
- expansion to the entire Meuse basin before the Limburg/Wurm design works;
- interviews; or
- treating unavailable historical thresholds or datum histories as data that
  must be acquired before analysis can begin.

Add a new model or dataset only when it tests a named comparison and has a
predefined evaluation outcome. A more complex system is not itself a research
contribution.

## Immediate sequence

1. **Completed 2026-10-11:** build a versioned event library with
   assessment-time history separated from withheld outcomes.
2. **First baseline completed 2026-10-11:** establish conventional hydrological
   signatures and analogue-retrieval baselines. The deliberately simple
   top-five analogue mean did not improve on an expanding historical median,
   so useful analogue evidence is an empirical target rather than an assumed
   property of the architecture.
3. **Completed 2026-10-12:** export and validate prior-year AlphaEarth
   catchment summaries for the held Dutch catchments and two delivered German
   Wurm gauges. Because the product begins in 2017, its fair comparison uses a
   common event subset from 2018 onward rather than all 570 temporal events.
4. **Model and protocol fixed 2026-10-11:** test pinned TTM-R2 `512-96-r2`
   against the conventional signature and raw 512-hour hydrograph controls on
   the same 570 complete events. No fine-tuning or model sweep is planned.
5. Proceed to LLM synthesis only after the retrieval and masked-observation
   tasks have meaningful baselines.

The corrected library contains 724 reviewed Dutch tributary onsets and 422,816
event-hour rows: exactly 512 assessment observations and 72 withheld outcome
hours per event. The earlier 174,484-row statement described the retired
168-hour library. German records have not yet been converted into equivalent
event objects; cross-border evaluation remains a required later step, not an
implicit property of the Dutch library.

The p99 event definition and p99 normalization were calculated retrospectively
from each full rating era. They are fixed archive labels for this study, not
thresholds that were known at each historical onset. Event-history features
exclude observations after onset, but this design does not constitute a
prospective forecast backtest.

## Locked literature basis

The targeted foundation-model review is recorded in
`docs/limburg-foundation-model-literature-2026-10-11.md`. The core literature
now covers Earth-FM selection criteria, controlled remote-sensing benchmarks,
independent Earth-system evaluation, hydrometeorological use boundaries,
zero-shot streamflow TSFMs and geospatial embeddings as catchment descriptors.

The literature narrows rather than expands the experiment. AlphaEarth remains
the single geospatial representation product and one open TSFM remains the
single temporal challenger. Each must beat or add useful retrieval behavior to
the same conventional hydrological baseline on held-out Limburg events.
AlphaEarth represents catchment context; it does not replace event-scale rain,
antecedent state or hydrographs. A model review, leaderboard or new pretraining
effort is outside scope.

The scientific selection, time-boundary rule and reproducible download path
are fixed in `docs/limburg-foundation-download-readiness-2026-10-11.md`.

The 2026-10-12 RAG and geospatial-reasoning refresh is recorded in
`docs/limburg-basin-ai-literature-refresh-2026-10-12.md`. It adds no model or
dataset. It sharpens the evaluation by separating retrieval from synthesis,
using claim-level citation support, preserving hard unanswerable cases and
adding a gold-evidence oracle packet as a diagnostic ceiling.
