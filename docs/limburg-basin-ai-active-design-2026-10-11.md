# Limburg basin-aware AI: active development design

**Status:** internal research design, 2026-10-11. Brian writes all dissertation
text. This design builds on, but does not silently rewrite, the completed
retrospective event-study work.

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

## Core comparison

The principal comparison is about evidence representation, not a sweep of
language models:

| Arm | Evidence available | Purpose |
| --- | --- | --- |
| R0 | Text/document retrieval | Conventional RAG baseline |
| R1 | R0 plus basin graph and provenance | Value of structured basin and institutional knowledge |
| R2 | R1 plus conventional hydrological analogue retrieval | Value of observed event dynamics |
| R3 | R1 plus foundation-model event/catchment representations | Whether pretrained representations improve retrieval |

A fused R2+R3 arm is conditional: run it only if the two representations show
different, individually useful retrieval behavior. A question-only LLM may be
retained as a small negative control. The generator model, prompt and decoding
settings stay fixed across the core arms.

## Evaluation tasks

### Source-grounded assessment

The existing 30-case question bank tests station identity, applicable rules,
measurement provenance and justified abstention. It remains useful, but is no
longer the entire scientific contribution.

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

## Policy experiment

Evaluate the same tasks under three information environments:

1. **Fragmented:** records substantially as agencies supplied or published
   them.
2. **Harmonized:** shared station identifiers, units, timestamps, river names,
   jurisdiction and verified topology.
3. **Provenance-complete:** harmonized records plus available rating validity,
   datum history, threshold versions and measured/reconstructed/interpolated/
   provisional status.

The performance differences estimate the value of information governance. The
remaining failures and justified abstentions identify fields that agencies
would need to preserve or exchange. The potential policy product is a minimum
cross-border evidence standard for AI-supported assessment, derived from
observed errors rather than asserted in advance.

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
3. Run a bounded AlphaEarth catchment-embedding feasibility check.
4. Test one open time-series foundation model against the conventional event
   representation.
5. Proceed to LLM synthesis only after the retrieval and masked-observation
   tasks have meaningful baselines.

The first library contains 724 reviewed Dutch tributary onsets and 174,484
hourly event rows. German records have not yet been converted into equivalent
event objects; cross-border evaluation remains a required later step, not an
implicit property of the Dutch library.

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
