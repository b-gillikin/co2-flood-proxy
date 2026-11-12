# Plan: local adaptation for flood-response mapping

12 November 2026. Internal research plan, not dissertation prose. Brian explicitly chose response mapping rather than early-warning prediction. The completed reference-policy study and its validity corrections remain preserved. This plan specifies the next study; it does not start training or replace completed results.

## Purpose and research question

An agency receives a flood image and can either use a transferred mapping model unchanged or spend local expert effort improving it. We will assess what additional map quality that work buys and whether the improvement extends beyond the labelled locations.

RQ: **How much can limited local annotation improve transferred satellite flood maps, and which areas should be labelled first?**

The single empirical comparison concerns the amount and allocation of local information. Model performance, spatial generalization, negative transfer and preparation/computation requirements explain that comparison. No river-flow forecast, warning lead time, peak prediction, causal adoption or lives-saved outcome is introduced.

Ryd and Nearing's Fine Flood Forecasts supplies the structure—transferable capability, local adaptation, strong alternatives and where adaptation helps—not the satellite architecture or a forecasting claim. ALFA and other annotation/adaptation studies are direct precedents. The focused novelty check must distinguish our budget accounting, spatial separation, correction transfer and receiving context rather than claim that active learning or fine-tuning is new.

## 1. Fix the response scenario and information clock

Primary scenario: **response-time local adaptation**. After a suitable image is available, an analyst supplies a limited set of annotations and the model maps separate, unlabelled areas. Existing reference maps simulate those annotations. The result is a retrospective annotation-budget experiment, not observed live operator performance.

Historical preparation is different: annotations available before an event could support pre-event specialization. Our current local references chiefly describe one July 2021 episode; they cannot be labelled historical preparation for that same episode. Do not add a second preparation experiment unless dated prior local references support it.

Record acquisition time, reference time, any documented image availability/processing times, and measured adaptation/inference time. Acquisition is a lower bound on availability, not proof an agency had the product then. Where annotation or delivery delay is unmeasured, report it as unknown or an explicitly assumed scenario. Do not derive annotation minutes from labelled pixel counts. Compare the observed acquisition with documented local event development for response context, without inventing a statutory decision deadline or warning archive.

## 2. Prepare the receiving and development evidence

Keep Venlo, Eschweiler and Wassenberg as the regional application. The completed support inventory selects nearest-reference-time local cases without scores: Venlo 16 July; the German cases 18 July, approximately 6.58h from reference time. Existing label/source dependence and unknown coverage remain explicit.

Finish unique ground-footprint/source-reference grouping, including all dates and overlapping views. Build spatially disjoint annotation and evaluation pools, with separation based on actual model input context and geolocation support. Inspect coverage under that separation before setting budgets. Partial labels are allowed: use small annotation regions with larger image context, and loss/scoring only on the relevant known support. Unknown is not dry.

The target remains mapped event-flood designation, with the source three-class definitions retained and local assessed/non-hydrographic support stated. Local hydrography is not an independently validated permanent-water target. Do not relabel event water as permanent merely because two images are dark.

Use the held Kuro/source events for pseudo-target development and protocol choices; any pseudo-target must be excluded from its source model's training and forbidden validation history. Reconcile reusable cross-fit states. International held events can replicate the adaptation comparison with explicitly separate evidence roles; only geometry- and target-compatible inputs support the intended analysis. Prior inspection is disclosed as exploratory reuse. Do not add countries to manufacture a local result.

No bulk data pull is currently justified. Additional regional event/reference acquisition becomes necessary only if the chosen claim extends to later floods or pre-event local preparation. Metadata/label inventory precedes any such request. No new gauge, soil/snow, hydraulic, population or economic data are default requirements.

## 3. Retain a small, capable comparator set

- Copernicus-FM source-trained paired-SAR pipeline, unchanged and locally adapted. Start with its supported frozen-encoder/head adaptation route; disclose that this does not exhaust full backbone adaptation.
- Source-trained same-input U-Net, unchanged and locally adapted with a declared source-developed training/stopping recipe.
- Existing physical SAR comparator, unchanged; include simple local recalibration under the same counted label budget. This tests whether expert work is more usefully spent calibrating a simpler method, without introducing another model family.

Hold imagery, radiometry, reference policy and evaluation targets fixed. Use geometry-compatible pre/post inputs; do not repeat the P0/P1 reference experiment. Select the eligible reference by a score-blind declared rule. Keep its actual water state/chronology qualifications visible.

No LoRA/full-fine-tuning grid, new encoder collection, third-image/DEM fusion or AlphaEarth branch. This is practical pipeline comparison, not causal identification of pretraining's effect. Equal label information matters; identical parameter counts are not asserted.

## 4. Compare local annotation allocation

Three policies on a common eligible annotation pool:

1. Random sampling.
2. Source-prediction uncertainty.
3. Spatial/appearance coverage using declared, label-free descriptors.

Choose actual acquisition units and three nested positive budgets from the prepared pools. Report unique known pixels, labelled area, region count and any validation/stopping/calibration consumption, rather than percentages alone. Include zero target labels as the unchanged-transfer baseline. Do not use hidden flood/error labels to ensure positives, discard inconvenient draws or design the coverage policy.

Share random and coverage annotation draws across learners. Model-specific uncertainty strategies may select different regions; compare them as complete sampling-plus-adaptation policies, not identical-label architecture experiments. Use repeated label draws and three optimization seeds with their different uncertainty roles recorded. Source pseudo-target development fixes stopping/hyperparameters where feasible; all additional target supervision must be charged if used.

Start with one-shot label selection, rather than iterative query/retrain cycles. An iterative policy is not a hidden extra workload. Region/context masks and label identities are stored so no ground location appears in both adaptation supervision and evaluation.

## 5. Evaluate errors and spatial transfer

Primary estimates: change from the unadapted source state at each budget, and difference between annotation policies at the same budget, on identical held evaluation support. Report flood IoU, precision/recall, missed mapped-flood area and falsely mapped-flood area. Use water-union scores only as a separate diagnostic where the target supports them.

Assess corrections in unlabelled areas and their spatial distribution. Include confident original errors, failures of adaptation, dry/negative areas and draws without positive annotations. All eligible test records remain accounted for. Separate the effects of receiving fewer valid labels from changes in the evaluation population.

Local cases form one physical flood episode; patch/draw/seed variation is not independent event replication. Use event-aware summaries for the broader replication collection and descriptive site-specific local results. Same-event spatial transfer does not demonstrate performance on the next flood or country-level institutional differences.

Cross-site transfer within the held region is a targeted secondary check of whether corrections travel beyond the supplying site, where the reference/input contracts support it. It must not become a new forecasting or national-comparison study.

## 6. Interpret usefulness and resource requirements

The policy decision is whether, and where, a mapping organization should spend local annotation effort before releasing an adapted response product. The empirical outputs are error-versus-label-budget curves, spatial correction/failure examples, applicability and measured adaptation/inference costs.

Missing mapped inundation and falsely flagged terrain can matter for reconnaissance and verification priorities, but this experiment does not directly measure rescue decisions, staff-hours saved, households assisted or avoided deaths. No population overlay or CLIMADA model is required to make that bounded connection. Risk to people motivates the use case; demonstrated map quality and available timing determine what the study can substantiate.

Ryd/Nearing supports the local-control/capability argument; Copernicus Rapid Mapping documents the response information role. Neither validates our adaptation nor establishes operational benefit. A map available after the peak remains a response/recovery observation, not an advance warning.

## 7. Execute in finite stages, then consolidate

A. Finish target identity/chronology/spatial pools and closest-paper method comparison. Deliver one executable target/sampling/label-budget specification and a claim table.

B. Implement masked local supervision and the two adaptation/recalibration routes. Check the existing published backbone/normalization/metadata contracts, acquired-label-only loss, spatial separation and checkpoint provenance. Run a source-only pseudo-target development/profile cycle and profile complete target adaptation/inference. These are correctness and cost checks, not a requirement to obtain a favorable score.

C. Enumerate exact eligible targets × policies × budgets × draws × seeds, reuse compatible states/features, and publish measured runtime/storage estimates before launching the census. Frozen features can be shared; full trainable-network paths cannot reuse detached features as though gradients reached the encoder. Use one MPS worker and bounded CPU work if actual memory/profile permits. Preserve the 50-GiB free reserve, resumable outputs and verified Azure recovery where needed. No unsupported multi-week ETA is made now.

D. Run the settled full eligible comparison and inspect actual corrections and harms. Retain all zero-label originals, failed/unavailable cases and unfavorable results. Consolidate the question, contribution and limitations from the completed evidence; do not add a new model because the outcome is weak.

## Deliverables and chapter size

One response-mapping study: a data/reference/support account, one controlled adaptation-and-allocation experiment, spatial error/transfer analysis, local timeline/application and transparent resource/policy discussion. Main displays: support/timing; label-budget curves; policy contrasts; correction/failure maps; resource/applicability table. Full queues, all masks/draws and prior experiments belong in supporting records.

This remains an empirical proposal with an open outcome. It does not promise a novel algorithm, AI superiority or a committee result. The next action is Stage A, not restarting the prior broad spatial programme.

Sources: https://arxiv.org/html/2504.12559v1 ; https://ijcai.org/proceedings/2025/1057 ; https://arxiv.org/html/2610.34904 ; https://mapping.emergency.copernicus.eu/about/rapid-mapping-portfolio/ ; https://mapping.emergency.copernicus.eu/about/linking-with-early-warning-system/ .

## Acquisition and literature continuation — 12 November

[Focused full-text review and acquisition](reviews/limburg-response-mapping-literature-and-data-2026-11-12.md) and [machine-readable receipt](reviews/limburg-response-mapping-acquisition-2026-11-12.json). All 12 core papers and the supplied paper's SD1–SD4 are accessible locally. Lee/Li already compares random, uncertainty and diversity; these policies are established comparators, not our novelty. PixelPick supports sparse-label loss; DIAL distinguishes correction from wider adaptation; neither licenses hidden error-label query selection or importing natural-image annotation minutes.

The existing core inputs are held. Additional bounded acquisition adds 15 paired February 2021 Rhine/German SAR tiles, their public Copernicus reference products and Dutch maximum-extent/ordinance context. This is a candidate second regional episode, not a validated later event on the same Limburg tributaries. Belgian products found during the regional inventory stay contextual and do not expand the primary population. No additional model, optical archive, HydroATLAS or DEM branch was introduced. Ground-pool separation, label rasterization/meaning and source-fit lineage still need Stage A preparation before fitting.
