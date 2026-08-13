# Dissertation Research and Code Guidelines

Status: reusable working standard for the remaining dissertation chapters.
This document records methodological and coding lessons from the chapter on
pre-high-water signal recurrence and spatial extent. It is not a protocol for
that chapter and does not prescribe the same estimator for another research
question.

## 1. The governing standard

A dissertation chapter should say something defensible about the world. It
should not primarily demonstrate that several models can be fitted to an
available dataset.

The question, population, observations and estimand come first. A statistical
model earns a place only when it is needed to estimate the stated quantity or
represent the dependence in the data. Technical sophistication is not a
contribution by itself.

A null or heterogeneous result is a valid result when:

- the question matters;
- the data can answer it at the stated resolution;
- the analysis was fixed before the outcome was inspected;
- uncertainty and missing evidence are represented honestly; and
- the interpretation was specified without depending on significance.

The objective is not to make a null result impossible. It is to make every
possible result informative.

## 2. Scope every chapter from scratch

Before reusing code, models or data, answer these questions in plain language:

1. **Predecessor:** What has already been observed or established?
2. **Unresolved problem:** What factual uncertainty remains?
3. **Population:** About which places, people, organisations, events or periods
   will the chapter speak?
4. **Unit of observation:** What is actually observed and at what temporal and
   spatial grain?
5. **Estimand:** What single quantity, or small set of quantities, answers the
   question?
6. **Transferability:** If required, what exactly is transferred, between what
   units, and what is explicitly not claimed?
7. **Required evidence:** Which inputs must exist before the estimand is
   identifiable?
8. **Possible readings:** What would a positive, null, heterogeneous or
   unavailable result mean?
9. **Excluded claims:** Which tempting interpretations lie outside the design?

Then ask the restart question:

> If the repository did not exist and the supervisor gave only the substantive
> question and dissertation sequence, is this the chapter I would design?

If the answer is no, stop adapting the inherited pipeline. Redesign the
chapter and retain only the evidence and code that still serve it.

### The one-sentence test

The question should be expressible in one sentence without listing models.
The contribution should be expressible as a sequence:

`prior observation -> prior explanation -> unresolved empirical test`

That sequence must be structural, not merely narrative. The new estimand must
actually extend what the predecessor work could establish.

### Define loaded words operationally

Terms such as *transferability*, *resilience*, *risk*, *performance*,
*recurrence*, *effect* and *early warning* are not self-defining. State:

- the quantity being compared;
- the source and destination units;
- the relevant spatial or temporal range;
- the validation or uncertainty procedure; and
- the stronger meanings that are excluded.

For example, spatial change in an event contrast is not automatically gauge
substitution, physical propagation, an operational radius or performance in
unobserved locations. Naming these boundaries prevents the methods and claims
from drifting apart.

## 3. Keep one direct empirical spine

Prefer one quantity that appears throughout the methods, tables, figures and
interpretation. In this chapter that quantity became event minus matched quiet
conditions. Another chapter may require a different quantity, but it should
still have a direct interpretation.

A strong default is:

1. define the outcome independently of the candidate explanatory signals;
2. define the comparison or reference observations;
3. compute the prespecified contrast or effect;
4. aggregate at the unit about which the claim is made;
5. estimate uncertainty at the level of genuine dependence; and
6. add one fixed relationship only if it answers a second stated estimand.

Simple does not mean statistically careless. It means that every
transformation and equation has a visible job in the argument.

### Model-selection rule

Use the least elaborate model that estimates the required quantity under a
credible representation of the data.

- Descriptive contrasts may need no predictive model.
- Ordinary regression may be sufficient for one prespecified association.
- Resampling may express clustered uncertainty more transparently than a
  complicated parametric hierarchy.
- SARIMAX, Kalman filters, random forests, neural networks or mixed-effects
  models belong only when the research question specifically requires their
  state, forecast, nonlinear or hierarchical estimand.
- Do not keep a model because it is interesting, conventional in data science,
  already implemented or likely to produce a non-null result.

There is no model-family search after an uninteresting result. Alternative
lags, thresholds, transformations and algorithms are not free robustness
checks; they change the question and multiply researcher degrees of freedom.

## 4. Data gates come before outcome analysis

Do not design around a plainly inadequate record merely because it is already
available. Attack the data constraint first. A short record with a handful of
events cannot support a broad transferability claim, regardless of model
complexity.

For each chapter, define a hard data gate containing:

- the target population and minimum number of independent units;
- the common observation period;
- minimum information per unit;
- coverage and missingness requirements;
- measurement and metadata requirements;
- required support across important strata; and
- the rule for stopping if the gate fails.

Numerical floors must be labelled honestly. They may be accepted standards,
power-based quantities, practical minimum-information safeguards or values
chosen after a blinded availability audit. Do not present author-chosen values
as universal disciplinary thresholds.

When a floor cannot be justified analytically in advance:

1. audit only dates, geometry, missingness and outcome-independent counts;
2. show the consequences of a small set of candidate rules;
3. obtain a supervisor decision; and
4. freeze the rule before inspecting the substantive contrasts.

If the hard gate fails, stop and return to the supervisor. Do not silently
lower it, change populations, add outcome types or substitute a shorter record.

### Separate core and optional evidence

A compelling local case, mechanism or predecessor replication may enrich a
chapter without being necessary for the core contribution. Give it a separate
gate and a predeclared consequence:

- gate passes: include the case;
- gate fails: report that the case is unavailable;
- do not describe unavailable evidence as a null result; and
- do not let a personal or fragile data request block a viable regional study.

## 5. Preserve the difference between absence and non-observation

Missing data are not zero. A damaged gauge does not show that high water did
not occur. A censored event does not have an exact peak simply because an
analysis prefers one.

General rules:

- retain a complete time grid so missing cells remain visible;
- never compute lags, changes or crossings across a gap;
- do not interpolate extreme outcomes unless the estimand and source semantics
  explicitly justify it;
- distinguish observed zero, missing code, sensor ceiling and source failure;
- preserve timezone and daylight-saving conventions until they are resolved;
- represent uncertain timing as an interval; and
- exclude censored cases from estimators requiring an exact time rather than
  imputing a convenient value.

An important event may still be a descriptive or interval-censored anchor. It
need not be discarded, but it must not be made more precise than the evidence.

## 6. Match inference to dependence

The effective sample is determined by independent information, not the number
of rows produced by joins or pair expansions.

- Aggregate repeated observations to the unit about which the network or
  population claim is made.
- Do not treat every event-site, site-pair or hourly row as independent when
  they share a storm, person, organisation or source exposure.
- Resample or cluster at the natural dependence unit.
- When pairwise analysis expands `n` mechanically, report the number of unique
  source units and independent clusters as well as the number of pairs.
- Use leave-one-unit-out refits as influence checks when one location or case
  could dominate the result. Do not call them external validation unless the
  design truly tests prediction in unseen units.
- Compare models or specifications only on identical observations and folds.

These choices prevent pseudo-replication and inflated certainty without
requiring an elaborate statistical framework by default.

## 7. Pre-commit interpretation, including nulls

Before viewing substantive results, write a compact result-to-reading table.
Include at least:

- stable positive or negative association;
- near-zero result;
- heterogeneity across units or periods;
- sensitivity to one cluster or unit;
- sign change or non-monotonic pattern; and
- failure of the data or case gate.

No row should automatically trigger a new model, lag, subgroup or threshold.
Separate three statements that are often conflated:

1. **null:** the estimand is available and centred near zero;
2. **heterogeneous:** the estimand varies materially across units or events;
3. **unavailable:** the data cannot estimate the quantity under the agreed
   design.

## 8. Data-science code, not an analysis application

The live analytical path should read like the research design:

`load -> check -> define sample -> transform -> estimate -> tidy tables -> figures`

Use direct scripts and visible dataframe operations. A reader should be able
to trace a manuscript number back to source columns without learning a custom
software architecture.

### Preferred code shape

- One clear script for a coherent analysis is preferable to a package of
  managers, services and registries.
- Put fixed scientific choices near the top of the script with names that
  expose their meaning.
- Use `main()` to make execution order visible.
- Keep transformations in pandas, GeoPandas, xarray or similarly familiar
  scientific structures when practical.
- Return tidy dataframes from substantive steps and write them explicitly.
- Use functions for scientific definitions that are reused, difficult to read
  inline or important enough to test independently.
- Use `src/` sparingly for stable shared scientific logic. Do not move code
  there merely to make a script shorter.
- Keep source-specific ingestion separate from scientific analysis.
- Write an ingest only after inspecting the real delivered format; do not build
  speculative parsers for data that have not arrived.

A useful skeleton is:

```python
def main():
    observations = load_inputs()
    check_input_contract(observations)
    sample = define_sample(observations)
    estimates = estimate_prespecified_quantity(sample)
    estimates.to_csv(OUTPUT_TABLE, index=False)
    make_figures(estimates)
```

The names should become domain-specific in real code. Avoid generic objects
such as `AnalysisManager`, `ModelFactory`, `PipelineRegistry` or
`ExperimentRunner` unless the dissertation genuinely has repeated production
requirements that justify them.

### Comments and naming

Comment scientific reasoning, not obvious syntax. Good comments explain:

- why a window excludes its endpoint;
- why a missing code remains missing;
- why events are aggregated before fitting;
- why one period is censored;
- why a threshold is computed from a particular population; or
- why a sensitivity does not change the primary estimand.

Names should include the unit or meaning where ambiguity is possible:
`pressure_hpa`, `distance_km`, `timestamp_utc`, `rain_72h_mm`. Avoid names such
as `data2`, `score_final`, `temp_result` and unexplained abbreviations.

### Abstraction test

Before adding a class, configuration layer or helper, ask:

1. Is the behavior repeated in the live analysis?
2. Does isolating it make a scientific rule easier to audit or test?
3. Will a reader understand the analysis faster after the abstraction?
4. Does it serve the current design rather than a hypothetical future one?

If the answers are mostly no, keep the code direct.

## 9. Test scientific claims, not software volume

There is no desirable number of tests. A growing test count is not evidence of
a stronger dissertation.

Add a test when a plausible error could change:

- who or what enters the analytical sample;
- an event, control, exposure or censoring definition;
- temporal or spatial alignment;
- leakage between reference and evaluation data;
- an uncertainty calculation;
- a reported number; or
- the interpretation of a figure or table.

High-value tests include gap-honest event detection, contamination-free
controls, training/reference-only scaling, censoring exclusions, spatial
assignment and missing-code handling. Small synthetic positive, null and
heterogeneous examples are useful when an estimator itself is being
implemented.

Do not routinely test:

- behavior already guaranteed by pandas or another mature dependency;
- trivial getters or formatting;
- every branch of collection infrastructure;
- speculative parsers; or
- implementation details that do not affect a scientific claim.

Real-file QC artifacts are often more valuable than large fixture suites for
one-off research ingests. Record row counts, time coverage, duplicates,
missingness, units, sentinels and source hashes.

## 10. Make every reported number reproducible

Use a simple data lineage:

- `data/raw/`: immutable native deliveries and correspondence, normally
  ignored by Git;
- `data/interim/`: normalized, analysis-ready source tables;
- `data/processed/` or `results/`: tidy events, contrasts, estimates and figure
  data; and
- manuscript figures/tables generated from those tidy artifacts.

For every external delivery:

1. preserve the original file and licence or email;
2. hash it before transformation;
3. document timezone, units, sampling, flags and missing codes;
4. make transformations deterministic;
5. retain missingness rather than silently repairing it; and
6. save a compact QC/provenance table.

Every quantitative statement in a chapter should regenerate from a named tidy
artifact. Do not make a manually edited spreadsheet or copied console value the
source of a manuscript number.

## 11. Keep the documentation architecture small

Each document needs one job:

- **synthesis:** canonical question, contribution, design and current research
  status;
- **protocol:** precise estimators, gates and pre-committed readings;
- **scope decisions:** concise live choices;
- **data requests/contracts:** required inputs and unresolved evidence;
- **analysis inventory:** what is prospective, supporting, conditional or
  retired;
- **literature source notes/matrix/BibTeX:** source-level evidence;
- **decision log:** append-only historical record, including superseded paths;
- **handoff:** short current session state; and
- **README:** entry point, commands and boundaries.

Do not create a new canonical document because the current one is inconvenient
to update. Remove or archive obsolete plans, duplicate reviews, generated
scaffolds and superseded how-to documents. Git history is the archive; the live
tree should describe the current chapter.

For session continuity, begin by reading `HANDOFF.md` and end by updating it.
Keep the handoff to current state and next actions rather than repeating the
whole project history.

## 12. Build the literature corpus before writing synthesis

Organize the search around evidence questions, not a target source count.
Retain:

- peer-reviewed primary evidence directly addressing those questions;
- canonical methodological sources where appropriate;
- official product and measurement documentation; and
- local institutional reports when they are the authoritative record of an
  event or dataset.

Canonical sources should be included when applicable even if a numerical
source target has already been met. Conversely, a source does not belong merely
to fill a thematic quota.

For each source, verify citation metadata and record its question, geography,
sample, outcome definition, method, author-reported findings, author-stated
limitations and exact locators. Keep citation keys consistent across notes,
the evidence matrix and BibTeX.

Source notes are not a literature review. They should not invent an aggregate
consensus, novelty claim or chapter argument. The doctoral researcher should
read across the sources and write that synthesis. AI assistance may support
search, metadata verification and source-level summaries, but should not
replace the researcher's interpretation or prose.

Remove obsolete model literature when the associated method is no longer part
of the question. A bibliography should support the live chapter, not document
every path explored during development.

## 13. Keep operational infrastructure outside the analysis

Collection infrastructure may be necessary when an API is slow, rate-limited
or must run while a laptop is closed. Isolate it from the scientific code and
keep it as small as the operational requirement allows.

- Store secrets in environment or managed application settings, never Git.
- Persist only the state required for restart and provenance.
- Make acquisition idempotent and validate before marking an item complete.
- Allow visible failure or a blocked state; do not silently skip files.
- Keep operational tests separate from the default scientific suite.
- Do not let a collector, dashboard or cloud deployment become part of the
  chapter's methodological contribution.
- Stop and retire parallel data sources once the chapter selects one source.

Infrastructure complexity is justified by reliable acquisition, not by the
desire to make a research repository resemble a production platform.

## 14. Warning signs of drift

Pause for review when any of these appears:

- the research question is described through model names;
- “transferability” or another key term has multiple meanings across files;
- a short or biased dataset is accepted because code already exists for it;
- the main result depends on picking a best model, lag, threshold or subgroup;
- a null result is treated as a reason to search again;
- optional evidence blocks the entire chapter;
- rows or pairs are counted as independent observations despite shared events;
- an exact value is imputed for a damaged or censored extreme;
- a source sensitivity is added without a decision it could change;
- tests grow faster than substantive analysis;
- classes, registries, configuration and pipeline layers obscure simple
  dataframe operations;
- multiple documents claim to be canonical;
- the live tree retains output from questions the chapter no longer asks;
- the code can run, but no one can state what quantity it estimates; or
- the methods support stronger claims than the chapter says it will make.

When drift is suspected, perform a deletion review. For every live component,
ask whether it supplies a binding input, estimates a live quantity, protects a
scientific claim or reproduces a required predecessor. If it does none of
these, remove it from the live path.

## 15. Reviewer-style chapter audit

Use adversarial peer-review questions rather than reassurance. The reviewer’s
job is to identify what would make the claim wrong, unidentified, unsupported
or unimportant—not to reward the amount of work completed. Lead a review with
the overall verdict and the few issues that could change the chapter’s
contribution. Distinguish fatal design problems, major revisions and minor
presentation issues. Support criticism with the protocol, data, code or source
record rather than generic preferences.

Ask:

### Contribution

- Is the contribution empirical, or mainly a new application of familiar
  models?
- Does the chapter extend the predecessor sequence in its estimand, not just
  its introduction?
- Would the result remain worth reporting if every coefficient were near zero?

### Identification and measurement

- Is the outcome defined independently of the proposed signals?
- Can the observations support the population and temporal/spatial claim?
- Are missingness, censoring, measurement change and source failure explicit?
- Is the apparent sample size larger than the independent information?

### Analysis

- Can every model be linked to a sentence in the research question?
- Were choices fixed before outcomes were inspected?
- Is uncertainty aligned with the natural dependence structure?
- Are sensitivities finite, motivated and interpretation-changing?

### Claims

- Does association become causation anywhere in the prose?
- Does descriptive coherence become prediction, substitution or operational
  reach?
- Are unavailable evidence, null evidence and heterogeneous evidence kept
  distinct?
- Are the limits stated as boundaries of the design rather than generic
  caveats at the end?

### Code and artifacts

- Can a reviewer trace each chapter number to a tidy table and source file?
- Is the live code shorter and clearer than the research logic it implements?
- Are comments about scientific choices rather than Python syntax?
- Could any infrastructure or test code be removed without weakening a claim?

## 16. Recommended workflow for the next chapters

1. Write the predecessor sequence and one-sentence question.
2. Define the population, unit, estimand, transferability meaning and excluded
   claims.
3. Create a prospective synthesis before analytical code.
4. Identify binding data and measurement metadata.
5. Build and run a blinded feasibility gate.
6. Return unresolved scope and numerical floors to the supervisor.
7. Build a verified source corpus organized by evidence questions.
8. Freeze the protocol and result-to-reading table.
9. Write direct source-specific ingests from the delivered formats.
10. Implement the smallest analysis that estimates the fixed quantities.
11. Add only claim-protecting tests.
12. Generate tidy tables and figures before drafting numerical prose.
13. Conduct a reviewer-style claim and dependency audit.
14. Delete or archive everything that no longer serves the final argument.

The repeated discipline is: **question first, evidence second, estimand third,
code fourth, prose from verified artifacts last**.
