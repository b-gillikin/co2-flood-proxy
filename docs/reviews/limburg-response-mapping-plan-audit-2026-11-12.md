# Audit: is the proposed local-adaptation study worth running?

12 November 2026, after acquisition. Internal research judgment and design audit; not dissertation prose. Read the current plan, proposal, acquisition/methods review, spatial-support census, actual local-reference preparation/scoring code, completed case scores and source-fit records, and the dissertation chapter-size benchmark. Rechecked the primary Lee/Li, DIAL, ALFA, Fine Flood Forecasts and CEMS workflow records. No fitting, tuning, new performance comparison, queue or download was started.

## Judgment

**Do not launch the full proposed factorial experiment as written.** The underlying local-adaptation question is scientifically legitimate and potentially useful, but this plan is not yet a sufficiently discriminating, executable study. A valid computational comparison is not automatically a worthwhile chapter contribution. The amount already downloaded or computed provides no scientific reason to continue.

The earlier statement that only preparation remained was too confident: preparation remains, but so do a substantive comparator choice, exact supervision semantics and a convincing empirical contribution. This audit does not prove the idea will fail, does not require AI to win, and does not introduce a favorable-result threshold. It also does not recommend another model search, another geography or an open-ended succession of pilots.

## Findings

### 1. The proposed selection-policy comparison is established prior art

Lee/Li already compares random, uncertainty and PCA/K-means diversity in flood mapping. ALFA studies active human-guided flood annotation, while DIAL studies correction/adaptation and transfer between images in remote sensing. A new region, more careful accounting and blocked evaluation can make a useful empirical extension; they do not by themselves establish an important new finding. Calling spatial correction transfer novel without qualification would also be too strong after reading DIAL.

Keep the practical question of complementary local work. Make annotation-policy superiority secondary unless there is a precise reason to expect it to reveal something beyond the established comparison. The existing proposition that confidently wrong regions may be missed by uncertainty is a defensible hypothesis, not an observed mechanism or guaranteed gap. Ryd/Nearing motivates local agency control; it is not direct evidence that our SAR adaptation will help.

Sources: https://arxiv.org/html/2404.19043v1 ; https://arxiv.org/html/2201.01047v1 ; https://ijcai.org/proceedings/2025/1057 ; https://arxiv.org/html/2504.12559v1 .

### 2. An inexpensive, scientifically consequential comparator is missing

The physical rule's local recalibration is useful, but it does not answer whether a transferred **neural** map needs weight adaptation at all. A change in the flood-score decision rule may correct some local errors without retraining the model. This is especially plausible when source sampling selected water-containing chips and target flood prevalence varies sharply.

Compare an unchanged neural pipeline, simple local recalibration of that pipeline's existing flood score, and local weight/head adaptation, using the same permitted labels and evaluation ground. Develop the recalibration rule and threshold-selection criterion on source pseudo-targets; target labels used for calibration count in the budget. This is one cheap decision-rule comparison, not another encoder or learning-model search. A local calibration advantage is potentially useful; adaptation is not required to win.

Without that comparison, an apparent adaptation improvement could be attributed to a complicated learning intervention even when a simpler decision-rule adjustment would suffice. Whether this is the actual explanation is unknown; no new calibration analysis was run in this audit.

### 3. Local supervision is binary; the source model has three classes

`src/applied_local_reference.py` provides **mapped flood / mapped non-flood** on assessed, non-hydrographic support and ignores unknown/trace-only areas. Its documentation explicitly does not certify all residual non-flood as independently observed dry ground. `scripts/248_run_chapter_local.py` encodes that reference as 0/2/255 for scoring. That convenient coding is **not** a license to train a three-class cross-entropy as though every local 0 were certified source-class background, rather than simply not mapped flood.

The adaptation loss must match the local information. One defensible route retains the existing three-class output but uses the flood-versus-non-flood marginal for local supervision: positive loss on `p(flood)`, negative loss on `p(background)+p(permanent)`, acquired known pixels only. It does not supply local permanent-water labels. Source pseudo-target development must choose the precise loss/stopping/regularization recipe before target evaluation. This audit recommends a contract, not an untested implementation or a new classifier family.

This is a real scientific implementation issue to resolve before fitting. The completed scoring analysis did not train on these local labels, so this finding does not invalidate its scores.

### 4. Local references have different strengths and limitations

The actual selected source tables identify **Pleiades optical imagery at 0.5 m on 18 July, 10:50 UTC** for Eschweiler and Wassenberg. The chosen SAR is approximately 6.58 hours later. Venlo's reference identifies **Sentinel-1 on 16 July, 05:41 UTC**, essentially the same acquisition used as input. Thus it would be wrong to dismiss every local reference as derived from the same radar image. It would also be wrong to treat all three as equally independent contemporaneous truth.

An adapted model may learn useful optical-derived local flood delineation, but timing, visibility and class definitions can also change agreement. Spatial separation does not remove a reference error shared across the whole product. Report changes in reference-map agreement, with the optical/radar and timing distinctions explicit; do not label them demonstrated changes in true flood accuracy. Existing independent optical evidence is a strength. A field campaign or a new independent label archive is **not** made compulsory by this audit; stronger accuracy claims would need stronger evidence.

### 5. The apparent local sample size overstates event replication

The selected cases provide the following **owned, known reference support under the previous comparison's masks**:

| Site | Known area km² | Mapped flood km² | Mapped flood as fraction of known pixels |
| --- | ---: | ---: | ---: |
| Eschweiler | 116.4997 | 0.3836 | 0.329% |
| Wassenberg | 30.5382 | 1.5905 | 5.208% |
| Venlo | 118.9837 | 11.6779 | 9.815% |

These are pixels in **one July 2021 episode**, not millions of independent floods. Repeated acquisitions/seeds/draws do not increase the number of episodes. The February 2021 Rhine material may provide a second regional episode after reference preparation; it is not a later flood in the same tributary landscape and does not establish temporal persistence of corrections.

Spatially separated same-event evaluation is legitimate for the stated question. It can support a bounded local case study. It cannot establish next-event reliability, national NL–DE differences or a general national allocation policy. Patches and seeds can characterize conditional variation, not supply an event-level confidence interval.

### 6. Random selection needs a stated operational population and annotation unit

At Eschweiler, broad uniform selection from known ground predominantly encounters mapped non-flood. That can legitimately test wide-area annotation but can also make policy differences primarily a consequence of finding rare positives, rather than transferring corrections. The present plan does not yet decide which question is intended.

Specify whether the agency reviews its whole valid image, an independently defined river corridor, or candidate map regions. Choose that population for the use case, not to improve scores. The same population must underlie all compared policies. Any corridor or candidate restriction must be based on information available before revealing reference labels. No hidden flood/error labels, convenient resampling or retrospective class balancing.

Equal numbers of region proposals do not guarantee equal acquired known pixels, label diversity or human time. Report proposed regions, actual unique labels/area and failed/unassessable queries. A known-support mask can itself use derived hydrography/trace information; distinguish a pre-existing observability restriction from exclusions based on later reference interpretation. Simulated labels establish a label-budget comparison, **not measured staff-effort savings**.

### 7. Some support conventions still belong to the previous experiment

The support inventory correctly reads the previous study's masks. However `scripts/248_run_chapter_local.py` defines common validity as the intersection of P0, P1 and post-image support. The proposed adaptation study uses one fixed reference policy. It should not silently inherit the extra validity requirement for an unused second reference.

Prepare a new, explicitly versioned support population for the chosen input pair; preserve the original masks/results. Do not treat the current census numbers as the final adaptation denominators. Group repeated physical ground and larger model input contexts when separating annotation/test areas. Partial labels are usable; requiring fully labelled large chips is unnecessary. Context non-overlap is necessary but is not proof of statistical independence.

### 8. The three-seed statement is ambiguous, and matters here

Existing source initializations vary substantially on the selected local cases. For example, Wassenberg U-Net P0 IoU across the three source seeds is approximately .333, .363 and .008. These are existing reference-agreement results, not new tests or evidence for a particular explanation.

The proposed three optimization seeds must not accidentally be treated as three independent events, or silently replace source-initialization variation. Pair every adapted result with its own unadapted source state and use shared annotation draws where appropriate. Decide whether stochastic repeats vary source initialization, adaptation randomness, or both. A paired three-realization design can disclose combined stochastic variability without automatically requiring a costly full source-seed × adaptation-seed Cartesian product. Keep label-draw variability distinct. Report the realized design rather than claiming separately estimated variance components that were not crossed.

### 9. The matrix is larger than its description suggests

Even before external replication, three sites × three policies × three budgets × five illustrative label draws × three stochastic realizations × two learners is **810 adaptations**, plus calibration and unchanged predictions. Five draws is an illustration, not a chosen requirement. Crossing a second independent three-seed axis would triple that. Runtime is unmeasured; these counts are not an ETA.

The dissertation examples support one coherent empirical argument with adequate robustness, not exhaustive enumeration of all possible knobs. Preserve all eligible receiving ground and unfavorable outcomes within a specified comparison. A census of ground/events is different from a census of model/hyperparameter configurations. There is no scientific requirement to run every allocation policy, secondary cross-site transfer and broad international replication as equally primary questions.

### 10. The policy connection is plausible, but has not been demonstrated

CEMS explicitly uses post-event mapping for emergency response. That makes error reduction and local preparation relevant. The study does not measure whether either government would prefer retraining, how long an analyst takes to create the required annotations, or whether a map arrives early enough to change a decision. Acquisition time is not delivery time. Product-derived labels are not observed live expert interactions.

The smallest credible implication is the conditions under which a receiving mapping team can improve a transferred map using limited local information, and whether adaptation adds value beyond simpler recalibration. That is a concrete capability question with a policy audience. It should not be sold as established operator benefit or emergency-warning performance. No interviews, welfare model, exposure overlay or deployment study is required to report that limited contribution honestly.

Source: https://mapping.emergency.copernicus.eu/about/rapid-mapping-portfolio/ .

## Recommendation

Retain local adaptation as a **candidate**, but revise the plan before treating the whole matrix as work to execute. The central contrast worth considering is **unchanged transfer versus local recalibration versus local adaptation on unlabelled ground**. The existing U-Net remains a strong conventional alternative; no foundation-model win is required. Query-policy selection can remain a secondary comparison rather than drive the entire chapter.

Settle the observable target/loss, receiving population and annotation unit, exact spatial support and paired stochastic design. Then write down the precise new empirical claim that could remain informative under positive, null and harmful outcomes, alongside the closest prior papers. This is a finite design revision, not another multi-week experiment, a new literature search or a requirement to obtain significance. Profiling can establish cost after that revision; this audit does **not** launch a pilot or an outcome-based proceed/stop test.

If the honest contribution after those choices is merely that fine-tuning on a few released labels improves agreement with that same product nearby, the study should be downgraded or set aside rather than expanded until it looks interesting. Conversely, a well-supported regional finding that simple recalibration captures most of the useful improvement, or that adaptation reliably corrects distinct errors beyond it, could be substantive. These are examples of discriminating questions, not promised results or acceptable-outcome gates. Whether the bounded contribution merits a dissertation article remains an author/supervisor judgment.

No new mandatory field data, forecast data, local operator trial, additional country or model family follows from this audit. Download integrity and method feasibility are assets, not evidence that a full experiment is warranted.

## Evidence and execution record

- Plan: `docs/limburg-response-mapping-plan-2026-11-12.md`.
- Methods/acquisition review: `docs/reviews/limburg-response-mapping-literature-and-data-2026-11-12.md`.
- Support census: `docs/reviews/limburg-local-adaptation-support-2026-11-12.json`.
- Actual reference source tables: `results/applied_study_v1/local_references/selected-source-tables.json`.
- Local target code: `src/applied_local_reference.py`, `scripts/194_prepare_local_reference_scoring.py`, `scripts/248_run_chapter_local.py`.
- Existing case scores: `results/limburg_chapter_sized_v1/local/case_scores.parquet` (metadata/table reads only; no new scoring).
- Source-fit record: `docs/reviews/limburg-chapter-scope-audit-2026-11-10/existing-source-fits.csv` and final-source-fit documentation.
- Scope comparison: dissertation manuscript `docs/reviews/chapter-scope-benchmark-audit-2026-11-11.md`, with the Ito/Roost chapter inventory.

No code, results, scientific labels, queue or completed study changed. No new significance/accuracy gate imposed. The assessment above supersedes the earlier unconditional recommendation to keep the complete proposed matrix.
