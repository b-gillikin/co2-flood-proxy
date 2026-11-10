# Chapter1 — Limburg: applied satellite AI for high-water and flood assessment

Updated 2 November 2026. Living internal supervisor/research brief; Brian writes dissertation prose.

## Research Question(s)

**Where can satellite AI improve assessment of high water and flooding, and at what data and computing cost?**

Two task families: assessing subsequent river discharge under limited ground monitoring; mapping surface water/new flooding from imagery and examining local transfer, labels and computing cost. Each model gets its intended configuration and matched inputs/comparators.

## Motivation

FEWS/DRR requires dependable information about river behaviour and inundation. Benefits could be accuracy, spatial information, reduced annotation needs or lower computing cost. Deployment is outside scope; mapping accuracy and discharge error are distinct from warning lead time or operational decision benefit.

## Data

Eight Dutch/German tributary gauges; 481 regional storms and 15,392 assessment opportunities per regime; rainfall, quality notes, geography, warning records and supporting Maas observations. Soil/snow 204/204 months held. AlphaEarth and TTM remain supporting completed work.

All 446 Sen1Floods11 hand-labelled radar/optical chips and 5,000 before/after radar-change records are acquired/audited. Held local material includes 24 CEMS vector packages, 43 reference grids and 530 imagery tiles across 54 AOI/sensor/scene cases. Cases include overlapping granules/repeated dates from July2021, not 54 independent floods. The local atlas preserves cloud/unknown support, timing and reference dependence.

All model code/weights and runtimes are held. Versioned Galileo features cover446 chips and match the original byte-for-byte. Copernicus's5000 exact frozen spatial differences are cached; its author's float64 Fourier calculation remains on CPU, with the trainable mapping head on MPS. No new data request is necessary to start these comparisons.

## Method

**Completed discharge work:** ten individually configured frozen encoders plus chronological, model-specific raw-input and conventional analogue controls; next 24h trajectory assessment under rich/local-Q-absent/all-Q-absent regimes. Nine use same-gauge annual heads; DOFA uses held-watercourse transfer. The whole103-task queue and 35 result reviews are complete.

**Spatial comparisons:** TerraMind Tiny multimodal water segmentation; Galileo Nano radar probe; Prithvi EO2 Tiny optical adaptation; Copernicus-FM before/after radar flood change. Each has compact/standard U-Net, pixel-linear and physical controls. Current plan:720 final fits /1200 candidate fits in five whole-event folds per task, covering the full53 task/event units, seeds42/1729/31415 and100/20/5% training-label conditions. Label subsets are fixed across optimization seeds; tuning is shared only on identical annotations. Validation stopping keeps the50/100-epoch ceilings. [Grouped execution design](limburg-grouped-execution-2026-11-02.md). First wave covers one held fold/seed42/full labels in each task and all four learned configurations.

## Methodology

Discharge: causal issue clocks, earlier-year training/tuning, storm exclusion, matched support and999 shared whole-year bootstrap draws. Mapping: whole-event held folds, validation-only selection, complete prediction census, matched local pixel support, separate acquisition/delivery times, coverage and measured pipeline costs. Count validation labels and cold feature extraction. Repeated pixels/seeds/acquisitions do not become independent floods. All inference is exploratory, with no preregistration or untouched-study claim.

## Findings

The completed discharge evidence does not show a broad encoder increment over matched raw controls. Individual improvements coexist with deterioration. Presto/Galileo complete that picture; DOFA has a specific favorable high-water transfer contrast, with flood/other-regime limitations. A zero contrast often reflects identical selected fallbacks. [Completed review](../results/completed_discharge_2026_11_02_final/readout.md).

Physical controls are complete across 53 folds; all 6,338 saved predictions and unknown masks were independently verified. All 16 spatial model/comparator configurations have successful profiles, including repaired Prithvi; Copernicus's cached/uncached output equivalence was checked. Spatial comparative accuracy/local transfer findings remain pending. [Launch and recovery record](limburg-spatial-launch-2026-11-02.md).

Current execution lives in the pointer `results/applied_study_v3/current-queue.json`. The versioned v5 queue retains the full event census with fewer repeated fits, using exact tensor/frozen-encoder caches, batched evaluation, two CPU fit lanes and one exclusive MPS fit lane. Common task batch-size changes are explicitly recorded; earlier fitted scores are not pooled into v5. It runs full fits, qualified local applications, versioned readouts and verified Azure offloading of inactive checkpoints. [Execution optimization](limburg-spatial-execution-optimization-2026-11-02.md). Keep 50GiB free; other chapters are untouched.


## Audited next-study specification — 10 November

The [three-prong design audit](reviews/limburg-three-prong-design-audit-2026-11-10.md) and [execution roadmap](limburg-three-prong-execution-plan-2026-11-10.md) now govern the planned spatial extension. Main working question: **When satellite AI is taken to a new river landscape, what observations and local training are needed to map newly flooded land reliably?** Water capability, antecedent-reference quality and unfamiliar-landscape adaptation are three linked questions; reliability/coverage and total local resource requirements accompany each. Completed discharge and spatial results above remain unchanged supporting evidence.

The intended contribution is controlled evidence about reference quality and the complementary local data/training needed for reusable flood mapping, rather than another generic encoder ranking. Close existing studies are explicitly acknowledged. Model/data product bridges, source and whole-area dry support, independent splits, exact adaptation/annotation protocols and measured resources remain preparation work. All requested branches are retained; the full run has not begun and the former runtime envelope needs updating. This does not create a scientific stop rule or require AI to win.


## Compute/resource refinement — 10 November

The [compute design](limburg-three-prong-compute-design-2026-11-10.md) separates reusable source preparation, independent target learning and shared full-map outputs. Frozen features and modular reference comparisons are reused under exact data/model identities; full/PEFT adaptation retains live encoder computation. All eligible evaluation records, declared contrasts and independent annotation/optimization repeats remain. New execution optimizations require parity and complete-development profiling; the long queue is not launched and there is no replacement ETA yet. Resource reporting distinguishes the dissertation grid from the cost of making a new map with a trained pipeline.
