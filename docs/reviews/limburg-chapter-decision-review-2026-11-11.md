# What chapter does the completed work support?

11 November 2026. Internal research assessment for Brian, not dissertation prose. Recommendation only: no scope/configuration, manuscript, labels, predictions, models or queue changed. No extra empirical run is authorized by this note.

## Assessment

Retain the accepted 10 November mapping study as one article: **Transferring satellite AI for flood mapping: model performance and reference information, with a Dutch–German application.** This is a working description, not manuscript text or an adopted title. Its central question remains the accepted comparison: how satellite AI and conventional methods compare on new flood events, and how reference choice changes their performance.

The chapter is an empirical evaluation of the complementary information needed to reuse a mapping model. It is not a tributary-forecasting chapter, a new reference-selection algorithm, or a study of institutional adoption. Its principal evaluation population is international, with a geographically explicit July 2021 Dutch/German receiving case. If a geographically primary Limburg study is non-negotiable, the present study cannot simply be renamed to satisfy that preference; it would require a deliberately different evidence design. That alternative is not recommended as the next automatic step.

The scope is suitable; scientific completion remains conditional on resolving the interpretation and acquisition-geometry issues below. A successful corrective selector, an AI victory and a minimum significant difference are not completion requirements. No committee outcome is guaranteed.

## Material reviewed

- Dissertation-manuscript `docs/reviews/chapter-scope-benchmark-audit-2026-11-11.md` and the underlying `dissertation_final_documents/analysis/chapter-comparison-2026-11-11.md`.
- Current HANDOFF, one-pager, accepted chapter-sized design, acquisition/evaluation specifications, source-fit and scoring audits, results guide and event-review memo.
- Completed analogue consolidation (27 October), representation diagnostics (29 October), ten model-specific discharge readout (2 November), 1 November applied-design review, completed spatial findings/recovery audit and literature-method comparison (10 November).
- Hostache et al. (2012) full text supplied by Brian, current notes, and the Tupas 2023/2024 and Copernicus-FM primary records reviewed in the recent literature pass. No claim of a new exhaustive systematic search.
- Actual reference-search code (`229_inventory_chapter_p1.py`), current evaluation configuration, local case-score schema and latest completed numerical results guide.

## 1. Distinguish the completed studies

| Work | What it actually establishes | Role in this chapter |
| --- | --- | --- |
| Tributary analogues, TTM and EO representations | Matching can improve resemblance; some conditional gains, without a general improvement in subsequent-response estimation | Historical research trajectory; not a second results spine |
| Gauge-delay/absence/scarcity and model-specific discharge corrections | Configuration-specific increments; no broad advantage over strong matched conventional assessment | Retain complete records; do not present EO mapping as a repair of a hydrological prediction failure |
| Four spatial task families, training-label fractions, 720 neural jobs | Task-dependent results; no universal foundation-model advantage; label fractions exclude the full validation burden | Development evidence explaining selected task/model; selected source validation belongs in supplement, not a four-family second paper |
| Accepted three-pipeline/two-reference study | Source-trained mapping performance on new events and fixed-model sensitivity to reference replacement | Main empirical study |
| Event review | Separates water recognition from flood designation and documents heterogeneous error routes and chronology issues | Explanatory evidence within the same study; explicitly post-result |
| Hostache-inspired selector | A defensible candidate corrective method, already related to an established literature | Future/optional follow-up, not an automatic requirement or new centre of gravity |

These are not one long confirmatory experiment. Record exploratory development and why the selected pipeline was retained. Source-only tuning of final states protects external scoring, but does not erase earlier model/task selection after inspecting earlier results.

## 2. Why this is a chapter rather than another comparison exercise

The practical uncertainty is whether acquiring a capable transferable mapping model is sufficient, or whether its apparent flood assessment depends materially on how baseline observations are prepared and interpreted. The design compares complete mapping pipelines and one obtainable input policy while holding trained states and event imagery fixed. It measures map agreement, coverage, class errors and resource requirements.

A useful result can be that a tested model offers no clear advantage over trained U-Net, while reference information produces material, physically interpretable differences. That is not evidence that information investment universally beats model investment, nor that reference quality is a newly discovered physical principle. The contribution must be the measured comparison and its applicability, not a general slogan about data quality.

The policy connection is the evidence and preparation needed to commission/reuse an AI assessment component. It can inform specifications for acquisition provenance, temporal baseline, reported class semantics and validation. It does not measure agency decisions, warning lead time, institutional capacity, economic returns or avoided losses. No interviews, welfare model or extra governance experiment is needed to discuss those bounded implications.

## 3. Evidence presently available

The latest run is complete, not an unfinished model queue: six final learned states, all 1,301 released external tiles, 913 harmonized paired triplets, three pipelines, three training seeds for learned methods, and event/coverage/error summaries. Nine activations are represented by eight conservative dependence blocks, not thousands of independent floods. The 167 local scene/grid records form 14 acquisition cases within one July 2021 episode; 35 records have a changed reference.

Episode-balanced harmonized flood IoU is .396/.380/.295 for Copernicus-FM/U-Net/physical P0, and .274/.269/.227 for P1. Copernicus minus U-Net is .016, with the reported block-bootstrap interval [-.035,.082]; reference change is -.121 [-.242,-.018]. These are map-agreement quantities under the recorded target/support, not verified independent field accuracy. Eight blocks make uncertainty coarse. Delivered-image and harmonized-image comparisons have different cohort/processing contexts and must remain separate.

The completed event review shows that many correct flood predictions switch to permanent-water predictions under P1; broad water recognition can remain stable. Other events lose detections to background, and March Italy improves mainly through precision. Official regional chronology corroborates earlier flooding in Babahoyo, but does not independently verify every affected pixel. This heterogeneity belongs in the main result rather than a claim that one explanation fits all cases.

## 4. What the literature leaves for us

Hostache 2012 directly precedes reference contamination and actual-acquisition reference selection. Tupas 2023 calls for time-series references/localized investigation; Tupas 2024 already follows up part of that agenda and identifies weaknesses during prolonged flooding and environmental false alarms. Their future-work statements are not unclaimed territory by default. Copernicus-FM supplies a task-supported paired-SAR route, not a promise of superiority over trained spatial controls.

A defensible contribution candidate is the comparison of transferable AI and conventional mapping under a fixed, reproducible reference-policy change, with explicit separation of visible water, event flood designation, acquisition applicability and local receiving conditions. This is an empirical extension of existing work, not invention of SAR change detection. Its exact novelty relative to other reference-sensitive AI studies still needs a focused comparison table before making a strong novelty claim. Do not use a generic 'first' claim.

Adding a successful replacement selector would answer a different extension: whether a particular correction recovers agreement. It is not necessary merely because the current policy performs poorly. If pursued later, it must retain originals, use past-only candidate/statistic availability, avoid target-score selection and be declared as a post-result follow-up. Synthetic seasonal references and real acquisitions also need different metadata/processing treatment; do not casually feed either into an acquisition-based model as if identical.

## 5. Remaining scientific resolution, before another substantive run

### A. Define the mapping target and distinguish semantic change from error

The primary target stays the fixed released event-flood mask, with permanent water separate. Changing the reference does not redefine that evaluation target. But a two-date method may instead distinguish water newly appearing since its supplied reference. An earlier/ongoing flood can therefore be classified differently without broad water recognition failing. Derived permanent-water labels can themselves depend on an historical baseline.

Write the exact intended output and class construction for source training, released target and local proxies side by side. Use existing label-composition sensitivity and water/flood transitions to quantify what can be distinguished. Report target disagreement where unresolved. Do not silently relabel test pixels, call recent-image increments a complete event footprint, or claim every lost flood label is a demonstrated loss in true inundation accuracy. If label construction prevents the proposed interpretation, revise that interpretation or use already held valid targets; a new learned model does not resolve it.

### B. Audit acquisition geometry against the event image

The current P1 search explicitly matches platform, relative orbit and pass to the P0 reference. This preserves P0/P1 geometry as an intervention, but does not itself establish pre/post geometric compatibility. Hostache's condition is matching the crisis image. Matching processing grids or linear intensity does not substitute for acquisition geometry.

Use held source-product metadata to enumerate pre/post orbit, pass and platform for all three dates; quantify coverage and existing scores on matching versus mismatching support. This is a finite validity check, not another model experiment. If mismatches are material, restrict/stratify the scientifically appropriate estimand and describe the full released-cohort result separately. If a corrected acquisition policy is needed for a claim, declare the correction and recompute only affected material. Do not promise no rerun before that check, or launch an entire selector programme to evade it.

### C. Set the interpretation of the reference policy

P1 is latest eligible before a catalogue date, not independently verified unflooded terrain or an agency's actual procedure. P0 is a delivered/held baseline, not a documented operational choice. The completed comparison tests these policies. It does not rank recent versus old imagery generally, or show that agencies made this mistake. Keep the official chronology and cases supporting and contradicting the proposed mechanism.

### D. Close costs and contribution, without another data branch

Reconcile retained timings for retrieval/preparation, encoder work, source fitting and inference; distinguish shared experimental caching from a specified reuse setting. Unequal runtimes/device contention limit operational latency claims. No new benchmark sweep is required. Complete the focused novelty table and choose the small main-text evidence set. No new weather, gauge, optical or hydraulic data are a default requirement of this chapter.

## 6. Geography and chapter sizing

The example audit supports roughly one central question, one coherent design and substantial supporting analysis. Its 25–40-page planning range is not a university rule. International data are scientifically legitimate, just as the benchmark dissertations use multi-country evidence. They must not be represented as NL/DE operational performance.

Keep three evidence roles explicit:

1. Source development: existing training/selection data, outside final receiving claims.
2. International new-event evaluation: the principal replicated evidence for the pipeline/reference comparisons.
3. Venlo/Eschweiler/Wassenberg July 2021: a bounded NL/DE receiving case demonstrating timing, reference and observability constraints. Multiple AOIs/acquisitions are not multiple independent disasters or a country comparison.

Do not add geographies or chase more local floods just to make the title true. Equally, do not make the international chapter a Limburg-primary study by narrative emphasis alone. Recommend the transparent international-evaluation/local-application structure. A decision to require a Limburg-primary population would be a substantive redesign for Brian/supervisors, not a small follow-up.

One article: introduction/use and gap; source/evaluation/local evidence; paired design and target definitions; model/reference results; error and applicability analysis; bounded local case; implications/limits. Approximately five main displays can cover cohort/support, model contrasts, policy effects, class transitions and local acquisition timing. Full tuning, previous model families, extensive maps, recovery receipts and historical directions belong in appendices/archive as appropriate. They are not all promised main-text results.

## 7. Decision and next action

Retain the accepted question and three-pipeline comparison. Do not promote the Hostache selector, prolonged-flood modelling, a new model family, or a geography pivot into the completion workload. First resolve A–C using current evidence, then complete resource/novelty consolidation. Correct only concrete threats found by those checks. Retain negative, positive and heterogeneous outcomes without choosing a desired winner.

This is a plausible substantive empirical chapter with completed evidence and identifiable limitations, not a guaranteed publishable manuscript or committee pass. Its credibility will depend on how well the final target, geometry and contribution withstand scrutiny, not the number of trained models or accumulated files. No completed study is erased, and no new stopping gate is introduced.
