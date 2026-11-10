# A chapter-sized Limburg study, calibrated against the two example dissertations

10 November 2026. **Active scope, accepted by Brian.** This is the internal
research outline; Brian writes the dissertation. Scope activation did not launch
scientific fitting or a bulk download. The broader roadmap is preserved in the
[future-ideas archive](../archive/future-ideas/2026-11-10-broad-spatial-programme/README.md),
outside this chapter's completion workload.

## 1. What the actual example chapters contain

Reviewed the contents and empirical-chapter introductions, data/methods,
conclusions, extensions/robustness structure and boundaries in both local PDFs.
Complete PDF text was extracted; the contents pages were also visually checked.
Page counts below include chapter-opening pages, exclude chapter references/
appendices, and use printed pagination. They calibrate intellectual scope, not
programme rules or identical workloads across disciplines.

| Dissertation / chapter | Central empirical task | Data/design and depth | Main text |
| --- | --- | --- | --- |
| Stefanie Cipriano Roost, Ch2, *In trust we reform?* | Explain support for flexible versus regulated crisis-response policies | One survey experiment, 9,105 respondents across nine countries; trust dimensions, treatment interactions, mechanisms/heterogeneity and substantial robustness | pp41–87:47pages |
| Roost, Ch3, *Brazil above everything* | Compare economic-insecurity and cultural explanations of the Bolsonaro vote | One2018election survey of2,506respondents; logistic models, voter-group heterogeneity, alternative measures/specifications | pp107–145:39pages |
| Roost, Ch4, *Who gets what, and who gets resentful* | Test differential preference responses to one transfer-policy expansion | Polish panel waves2008/2013/2018; beneficiary/excluded groups, panel/event-study design, related redistribution/tax/political outcomes and robustness | pp165–190:26pages |
| Rodrigo Ito, Ch2, *From Drains to Bridges* | Whether mobile researchers connect non-mobile researchers with foreign collaborators | Linked Colombian CV/scholarship/OpenAlex data;19,158mobility histories, restricted analytic sample; LPM, fixed effects and DiD/event study address the same network question | pp28–65:38pages |
| Ito, Ch3, *Local Gains From Global Minds* | Whether that collaboration improves research performance | Reuses linked data; matching+DiD, related performance outcomes, field heterogeneity and Brazilian external-validity analysis | pp91–119:29pages |
| Ito, Ch4, *Navigating the Knowledge boundaries* | Whether collaboration changes topic exploration and novelty | Closely related data/identification, but a separate chapter for a different substantive outcome; individual/global novelty measures and Brazilian comparison | pp139–159:21pages |
| Ito, Ch5, *Unpacking the collaboration* | How diaspora collaboration operates |25interviews and thematic analysis of one collaboration phenomenon, with explicitly limited heterogeneity/generalization | pp167–189:23pages |

Sources are `../../dissertation_final_documents/final_dissertation.pdf`
and `../../dissertation_final_documents/assessment_dissertation.pdf`.
Hashes, physical PDF-page ranges and extraction provenance are in the sizing
review JSON. Roost's bibliography is consolidated later in the volume; Ito uses
chapter references. Whole-chapter totals including appendices would therefore
be a misleading comparison of main scientific scope.

### Lessons for this dissertation

- These are substantial studies, not one regression and a discussion. They
  combine careful data construction, identification/evaluation, heterogeneity,
  robustness and substantive interpretation around an identifiable question.
- Data reuse is encouraged, but does not make every resulting question one
  chapter. Ito separates networks, performance and novelty even with a common
  data infrastructure and related methods.
- Supporting analyses examine the central explanation. They do not become a
  survey of every available estimator, outcome or scientific possibility.
- Policy implications follow from the empirical comparison. Neither example
  requires the author to evaluate all subsequent implementation mechanisms or
  demonstrate actual government adoption within every chapter.
- With a scoping review, Peja's linked CV/impact work, and other empirical
  candidates, Limburg should contribute one article-sized argument. Jordan's
  proposed local-learning/resource question is another reason not to give Limburg
  a second full local-label/adaptation programme.

## 2. Agreed intellectual core

Working title: **Pre-flood information and the reliability of transferred
satellite-AI flood maps.**

Main RQ: **How do satellite AI and conventional methods compare in mapping new
flood events, and how does the choice of pre-flood reference affect their performance?**

Two connected empirical questions:

1. How does a task-appropriate foundation-model pipeline compare with competent
   conventional pipelines on independent flood events?
2. With the event image/model held fixed, what changes when the pre-flood
   reference is updated through a declared, label-blind acquisition policy?

Map coverage, error locations and resource requirements are reporting dimensions
of these two comparisons. They do not need separate model-development RQs.

The policy question is the complementary information an organization needs when
reusing an AI mapping capability. An agency can adopt a more sophisticated
model, prepare more suitable reference observations, or combine both. We can
measure differences in flood-map quality, coverage and preparation/compute burden;
we cannot infer the financial return to an investment, warning lead time or
avoided losses. This is an applied information-quality study with an AI comparison.

## 3. One empirical design, not three parallel research programmes

### Pipelines

Core learned pipeline: **Copernicus-FM's task-supported paired-SAR change route**,
with pretrained frozen encoder and trained segmentation head. It has a published
flood-change role and held data/code/weights; it does not require converting pooled
landscape embeddings into discharge. Its choice is justified by task/input fit,
not an assertion that its earlier results won.

Comparators:

- A competent same-input standard U-Net, trained on the same permitted source
  labels and selected without external-test information.
- A reference-aware physical SAR change/water method, with source-selected
  settings and the same available acquisitions/support.

All compare the same flood-mapping endpoint. Different architecture versus
pretraining are not separately identified: no claim that this isolates the
causal effect of pretraining, so a large random-initialization study is unnecessary.
Existing Galileo, Prithvi and TerraMind work is retained as supporting evidence/
methodological history, not repeated as three additional full chapter programmes.

### Reference intervention

Two pre-specified input policies:

- **P0: delivered reference.** Use the documented pre-event acquisition provided
  with the benchmark/service pair.
- **P1: updated reference.** Use a more recent compatible pre-event acquisition
  where available under one predeclared orbit/radiometry/coverage/chronology rule.

Both use one pre-image and the same event image. This is **replacement**, not a
new two-pre-image fusion architecture. It preserves the supported model interface
and makes a clean applied contrast. Hold the source-trained models fixed across
P0/P1; thresholds and acquisition policy are set using source development and
metadata, not external error maps. Update actual sensing-date/location metadata.
The estimand is the effect of this input policy on a fixed pipeline's predictions,
not the maximum attainable accuracy after independently retraining every variant.

The external catalogue's delivered pre/post SAR separations range roughly12–775days.
That motivates testing reference quality, not assuming that the newest image is
always best. Recent water may already be elevated; chronology/season/coverage
remain part of interpretation. If P1 equals P0, retain the case and alias identical
predictions. If a usable updated reference is unavailable, preserve the case in
the P0 and applicability account and report matched-support P1 results separately.
Neither missingness nor a failed update becomes a dry pixel or a deleted event.

This yields **three pipelines × two reference policies**, with only **two learned
source-model families**. Repeated seeds, source folds, parameter trials, tiles and
reports are not additional scientific questions.

### Data and evaluation population

- **Source development:** start with all5,000held Kuro/Copernicus radar records
  across20events. Retain their conditioned water-containing sample description.
  Existing source cross-validation can be reused only where it matches the
  final contract; correct demonstrably affected source fits rather than rerun
  every earlier study. Broader source acquisition is justified only by a specific
  coverage problem, not automatically required to complete the chapter.
- **Independent external cohort:** the separate GEOID heldout package is a
  candidate: all1,301tiles from nine2026activations. Resolve source/event/geographic
  overlap and label compatibility before assigning the final evaluation roles.
  Use the complete eligible released footprint of that cohort; no score-based
  selection or random test subset. Do not call every case an unfamiliar landscape
  if only its event/date is unseen. Country/region transfer claims follow actual
  exclusion checks, not dataset names.
- **Grounded receiving case:** retain all assessable existing Dutch/German radar
  cases, organized around physical events/reaches rather than repeated tiles.
  July2021 provides a substantive transboundary case, not many independent floods.
  Use René/Jens records for event timing and measurement context, not as pixel
  inundation truth. Preserve imagery/reference offsets and previous inspection
  history; these local cases are not pristine confirmatory tests.

Metadata packaging for the external SAR/label/validity/floodmask/permwater subset
is **nine shards /9.068GiB**, already pinned in the broader manifest. More recent
pre-event SAR must be inventoried over this cohort and the local case footprints.
The9.068GiB is exact package size, not the complete new-data total; extra imagery
volume/coverage and recovery costs remain to measure. No global post-optical,
S1S2-Water, WorldFloods, dense AlphaEarth, urban-coherence or vegetation archive is
required for this core. The224GiB catalogue-wide packaging envelope is not a
scientific minimum for this smaller declared population.

### Analysis and rigor that stay

Use source-only model/threshold selection and three independent source-training
seeds. Target labels evaluate predictions; no target fine-tuning or target-label
learning curve enters this core. Native-grid complete inference, validity masks,
consistent class semantics and temporal-reference provenance remain essential.

Primary results: paired event-level flood-map IoU differences between methods,
P1−P0 within each method, and the corresponding method×reference contrast.
Report permanent/flood confusions, false/missed mapped-flood area, per-event
variation and full versus common support. Use dependence-aware paired uncertainty,
not millions of pixels as independent observations. Distinguish reference-map
agreement from independently verified flood truth. Inspect reference age and
disagreement as explanatory descriptors, with no new failure-prediction model.

Targeted robustness: alternative defensible reference/validity timing convention,
reference provenance/label-composition sensitivity using already available masks,
and justified alignment/boundary sensitivity. No full alternative model zoo.
If the data show a specific threat, address it directly and document the effect.

Costs cover the actual source fitting and both new-area reference policies:
preparation, retrieval, feature extraction, complete inference, memory and coverage.
Simple confidence/error diagnostics can use retained probabilities. Learned
reliability prediction, a conformal-method comparison and a deployment study are
not necessary to interpret this experiment.

## 4. What moves out of this chapter's completion scope

Park the large target-label budget grid, all-target TTDA, active-learning study,
PEFT/full-adaptation comparison, dense AlphaEarth prior development, third-image/
terrain fusion architecture experiments, urban coherence and beneath-canopy study.
Their existing notes/data/results are preserved. They can support subsequent
papers or other chapters if scientifically distinct and deliberately selected.
Do not turn them back into hidden prerequisites through a readiness checklist.

The completed discharge/analogue and broad spatial comparisons remain historical
evidence and potential supplementary work. Reproducing every author benchmark
for all four model families is not an additional scientific obligation of this
chapter. Verify the selected pipeline's intended implementation and reasonable
training behavior; retain unfavorable results without forcing all model families
into a single table or searching for a winning alternative.

## 5. Appropriate size and visible contribution

Aim for one substantial empirical article, roughly30–40main thesis-format pages
plus necessary references/appendix, not a page-count gate:

| Component | Approximate planning space |
| --- | --- |
| Problem, prior work and information/policy argument |4–6pages |
| Data, cases and reference-quality diagnosis |5–7pages |
| Comparative design and methods |5–6pages |
| Main paired results and error explanations |8–10pages |
| Dutch/German case and practical interpretation |3–4pages |
| Discussion and conclusion |4–5pages |

Most importantly, the reader should leave with one empirically supported account
of **when model choice and reference-image preparation improve transferred flood
maps, and what an organization must supply to obtain that performance**. This is
not a claim that nobody has studied pre-flood images; it is the measured
model–information comparison and its documented applicability. The independent
test events and local case provide different evidence for the same account.

Compared with the examples, this has one coherent target, a small set of competing
pipelines, a controlled mechanism/input contrast, independent validation,
heterogeneity/error analysis and a policy interpretation. A precise null or
heterogeneous contrast can answer that question; it does not justify declaring
an equivalence or automatically make the results important. Precision, reference
quality and substantive interpretation still determine the strength of the study.

This also gives the dissertation differentiated chapters: review maps the field;
Limburg studies information quality in applied mapping; Peja connects structure
verification to physical/economic adaptation appraisal; Tagoloan evaluates global
forecasts locally; Jordan studies atmospheric warning/adaptation if included.
Their final inclusion remains a supervisory/author decision, not a chapter-count
rule.

## 6. Workload implications and next work

No thousands-of-target-adaptation-state grid is needed. If the selected source
fits must all be rebuilt, five source event folds × two learned pipelines ×
three seeds give30selected source states; three final refit seeds per pipeline
add six. These are upper illustrative rebuilding counts, not a requirement to
discard valid existing fits or a candidate-search count. Every source search,
calibration and changed-population refit is still charged. The two input policies
reuse the same trained states; they do not double fitting. The physical control
does not have independent neural training seeds.

Exact runtime depends on selected-state reuse, actual reference acquisition and
large-grid inference. Do not substitute a new unsupported calendar promise for
the old programme ETA. Resource engineering supports this question; it no longer
dictates a requirement to run every possible model/adapter combination.

Next work within the accepted scope: validate selected model/reference/label contracts;
lock the independent event cohort and local case inventory; catalogue P1 imagery
and paired support; enumerate only the source fits actually needed; then execute
the two contrasts and their shared inference/error/resource analysis. No new
agency email or human interview is introduced. No fitting/download was launched
by this scope decision.
