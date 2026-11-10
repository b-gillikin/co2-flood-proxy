# Chapter 1 — Satellite AI for high-water and flood assessment in Limburg

Updated: 2026-11-10. Living supervisor/research one-pager.

## Background

Satellite AI offers different forms of information about flooding: representations of catchment conditions and spatial estimates of surface water. Their value depends on the assessment task, available ground observations, reference labels, and computing requirements. This chapter evaluates these applications across Dutch and German tributaries and through flood-mapping benchmarks and local cases.

## Research question

Working direction, 10 November: How well do pretrained satellite models map water and flood extent in an unfamiliar river landscape, and what observations and local labels do they require?

## Motivation

The chapter examines whether pretrained satellite representations improve discharge assessment or flood mapping relative to conventional methods and matched raw-input controls. It considers accuracy, label requirements, coverage, and computing cost together. The contribution concerns measured assessment performance; operational warning and decision benefits require separate evidence.

## Research design

Two complementary analyses evaluate satellite AI for subsequent discharge and spatial water mapping. The discharge analysis tests representations under different ground-monitoring conditions. The mapping analysis evaluates spatial outputs, label efficiency, and transfer to local imagery. Each model receives a task-appropriate configuration and matched controls; findings from one task do not establish performance on the other.

Discharge comparisons use earlier-year training and tuning, issue-time-valid inputs, and storm exclusion. Mapping comparisons hold out whole events and select configurations using validation data. Uncertainty accounts for temporal and event dependence. The analyses are exploratory.

## Overview

The study evaluates whether frozen satellite representations improve subsequent 24-hour discharge assessment under different monitoring conditions, alongside water segmentation and flood-change detection. It examines training-label requirements, computing cost, and transfer to local flood cases.

## Method

For discharge assessment, ten individually configured encoders are compared with model-specific raw-input controls and conventional analogue references. Nine experiments use same-gauge annual prediction heads; DOFA uses transfer to held-out watercourses. Evaluation compares discharge trajectories and high-water errors on matched observations, with shared whole-year bootstrap draws.

For water and flood mapping, TerraMind Tiny multimodal segmentation, Galileo Nano radar probing, Prithvi EO2 Tiny optical adaptation, and Copernicus-FM radar change detection are compared with U-Net, pixel-linear, and physical controls. Evaluation uses five whole-event folds, three optimization seeds, and 100%, 20%, and 5% training-label conditions. Label subsets are shared across optimization seeds, and tuning uses validation data only.

Benchmark and local comparisons retain common pixel support, unknown coverage, reference timing, and measured processing costs. Repeated acquisitions and overlapping granules remain dependent observations.

## Data

- **River observations:** Eight Dutch and German tributary gauges, quality records, warning information, and supporting Maas observations.
- **Event and environmental inputs:** Rainfall, geography, soil, and snow; 481 regional storms and 15,392 assessment opportunities per monitoring regime. ERA5-Land soil/snow coverage spans all 204 months from January 2009 through December 2025.
- **Satellite representations:** Ten frozen encoders. Completed AlphaEarth and Tiny Time Mixers analyses provide supporting evidence.
- **Benchmarks:** All 446 Sen1Floods11 hand-labeled radar/optical chips and 5,000 before/after radar-change records are acquired and audited.
- **Local cases:** 24 Copernicus Emergency Management Service vector packages, 43 reference grids, and 530 imagery tiles across 54 area/sensor/scene cases. These include repeated dates and overlapping granules rather than 54 independent floods.
- **Model inputs:** Code, weights, runtimes, and relevant feature caches are held. Cloud, unknown coverage, and reference dependence are documented.

## Literature

Presto and Galileo motivate tests of satellite representations for discharge assessment. Sen1Floods11 provides a common water-mapping benchmark, while TerraMind, Galileo, Prithvi, and Copernicus-FM inform sensor and task configurations. Independent Earth-system model evaluation supports matched controls. Published capabilities do not establish benefit in Limburg; performance is evaluated for each task.

- Tseng et al. (2023). *Lightweight, Pre-trained Transformers for Remote Sensing Timeseries*. [Paper](https://doi.org/10.48550/arXiv.2304.14065).
- Tseng et al. (2025). *Galileo: Learning Global & Local Features of Many Remote Sensing Modalities*. [Paper](https://doi.org/10.48550/arXiv.2502.09356).
- Ullrich et al. (2025). *Recommendations for Comprehensive and Independent Evaluation of Machine Learning-Based Earth System Models*. Journal of Geophysical Research: Machine Learning and Computation. [Article](https://doi.org/10.1029/2024JH000496).
- Bonafilia et al. (2020). *Sen1Floods11: A Georeferenced Dataset to Train and Test Deep Learning Flood Algorithms for Sentinel-1*. CVPR Workshops. [Paper](https://www.grss-ieee.org/wp-content/uploads/earthvision2020/july_stuff/webpage/papers/Bonafilia_Sen1Floods11_A_Georeferenced_Dataset_to_Train_and_Test_Deep_Learning_CVPRW_2020_paper.pdf).
- Jakubik et al. (2025). *TerraMind: Large-Scale Generative Multimodality for Earth Observation*. [Paper](https://doi.org/10.48550/arXiv.2504.11171).
- Szwarcman et al. (2024). *Prithvi-EO-2.0: A Versatile Multi-Temporal Foundation Model for Earth Observation Applications*. [Paper](https://doi.org/10.48550/arXiv.2412.02732).
- Wang et al. (2025). *Towards a Unified Copernicus Foundation Model for Earth Vision*. [Paper](https://doi.org/10.48550/arXiv.2503.11849).

## Progress

All ten discharge experiments and declared configuration comparisons are complete. The results show no broad improvement over matched raw-input controls. Individual gains coexist with deterioration; DOFA has a favorable high-water transfer contrast with limitations in other regimes and sparse flood evidence. Differences in model-specific support prevent a simple encoder ranking.

Spatial fitting and evaluation are complete: 720 training jobs, 20 physical controls, 48 benchmark contrasts and 60 matched local groups passed the completion/recovery audit. Copernicus-FM radar change improves on the implemented physical control and retains mean event IoU from .574 at full training labels to .558 at 5%; superiority to trained U-Net is not established. TerraMind, Galileo and Prithvi generally underperform trained same-input controls; Galileo deteriorates sharply at 5% training labels. Reduced training fractions do not imply equally reduced total labeling requirements because validation labels remain available. Local findings are reference-map agreement, with substantial timing, coverage and target-semantic qualifications. No consistent local winner or operational warning benefit is established. See the [consolidated findings review](limburg-consolidated-findings-2026-11-10.md). Next work is synthesis and targeted inspection of retained spatial predictions, without a new general model sweep.

## Paper-guided refinement — 10 November

The [methodological recovery plan](limburg-paper-guided-recovery-plan-2026-11-10.md) prioritizes spatial mapping/transfer as the primary development direction, with discharge results retained as supporting evidence. Water identification, new inundation and geographic transfer remain separate targets. Initial training-only Galileo granularity/readout/learnability and Prithvi label-resolution diagnostics are complete; controlled reference fits and spatially faithful model comparisons are not yet launched. The question is provisional while these methodological comparisons define the final experiment. Completed results above remain historical evidence, not outcomes of this refinement.


## Audited next-study specification — 10 November

The [three-prong design audit](reviews/limburg-three-prong-design-audit-2026-11-10.md) and [execution roadmap](limburg-three-prong-execution-plan-2026-11-10.md) now govern the planned spatial extension. Main working question: **When satellite AI is taken to a new river landscape, what observations and local training are needed to map newly flooded land reliably?** Water capability, antecedent-reference quality and unfamiliar-landscape adaptation are three linked questions; reliability/coverage and total local resource requirements accompany each. Completed discharge and spatial results above remain unchanged supporting evidence.

The intended contribution is controlled evidence about reference quality and the complementary local data/training needed for reusable flood mapping, rather than another generic encoder ranking. Close existing studies are explicitly acknowledged. Model/data product bridges, source and whole-area dry support, independent splits, exact adaptation/annotation protocols and measured resources remain preparation work. All requested branches are retained; the full run has not begun and the former runtime envelope needs updating. This does not create a scientific stop rule or require AI to win.


## Compute/resource refinement — 10 November

The [compute design](limburg-three-prong-compute-design-2026-11-10.md) separates reusable source preparation, independent target learning and shared full-map outputs. Frozen features and modular reference comparisons are reused under exact data/model identities; full/PEFT adaptation retains live encoder computation. All eligible evaluation records, declared contrasts and independent annotation/optimization repeats remain. New execution optimizations require parity and complete-development profiling; the long queue is not launched and there is no replacement ETA yet. Resource reporting distinguishes the dissertation grid from the cost of making a new map with a trained pipeline.


## Full-plan reconciliation — 10 November

The [full audit](reviews/limburg-three-prong-full-audit-2026-11-10.md) retains the questions and all requested branches. It corrects event-complete acquisition, separate training/inference/scoring identities, source-refit cost accounting, normalization provenance and seed-chain interpretation. The revised GEOID candidate cohort contains109activation IDs/6,837tiles before development/test role and cross-source reconciliation; its conservative all-split packaging envelope is224.373GiB, staged rather than held locally at once. Metadata date checks passed; raster/model QA and actual queue/profile implementation remain. No new model accuracy result, fitting queue or bulk download was produced.


## Chapter-sized recommendation after dissertation comparison — 10 November

The [scope recommendation](limburg-chapter-sized-study-2026-11-10.md) replaces the broad programme as the proposed single-chapter completion target. Working question: **How do satellite AI and conventional methods compare in mapping new flood events, and how does the choice of pre-flood reference affect their performance?** Compare Copernicus-FM, a same-input standard U-Net and a reference-aware physical baseline, using two reference-acquisition policies with the event image/trained models fixed. Use one independent complete eligible external cohort and the assessable Dutch/German radar cases. Reference quality, map errors/coverage and complementary preparation/compute requirements form one empirical contribution.

The recommendation parks the separate model-family benchmark, target-label/adaptation grid, active learning, dense AlphaEarth prior and difficult-environment extensions. Existing studies/data/results remain preserved. The target is one substantial empirical article, approximately30–40main thesis-format pages as a planning illustration. Nine existing external SAR/mask shards total9.068GiB; updated reference imagery remains to inventory. This is a proposed scope, not new findings, a launched queue or a promise that AI improves the maps.
