# Chapter 1 — Limburg: applied satellite AI for high-water and flood assessment

Last substantively reviewed: 2026-10-31. Living supervisor/research brief; internal research aid, not dissertation prose.

## Research Question(s)

**Working refinement: Where can satellite AI improve assessment of high water and flooding, and at what data and computing cost?**

Existing experiments ask whether satellite representations help under limited ground monitoring. The proposed extension tests spatial water/flood mapping, local transfer and accuracy/resource trade-offs. These are distinct outputs; no spatial model has been trained or scored. [Task configurations and chapter review](limburg-applied-task-configurations-2026-10-31.md).

## Motivation

The FEWS/DRR motivation is reliable information about high water and flooding. Useful improvements could concern spatial accuracy, transfer or labeling/computing efficiency; a missing feed is not required. Deployment is outside scope. Our held-data reference does not represent the full Dutch/German operational forecasting service, and trajectory accuracy does not establish inundation or warning skill.

## Data

Eight Dutch/German tributary gauges, rainfall, provider quality notes, geography, ten frozen EO encoders and supporting Maas observations. The calendar contains **481 regional storms** and **15,392 assessment opportunities per regime**, before support checks. Soil/snow is complete (**204/204 months, 2009–2025**); its supporting control is prepared, not fitted. AlphaEarth, TTM, weather and warning records remain available. No new provider delivery is essential to finishing discharge work.

Mapping backbone code/weights are held; new task heads are untrained. Public hand-labeled inputs total **1.63 GiB**; a separate radar-change ZIP is **5.61 GiB**. Only metadata/splits and one sample triplet were acquired. Local individual acquisitions and credible spatial references remain to be matched. [Data needs](data-needs.md).

## Method

**Proposed mapping tasks:** TerraMind Tiny with a frozen backbone and trained spatial decoder on radar/optical water labels; Copernicus-FM on pre/event radar change; Galileo Nano with a radar segmentation probe. Prithvi Tiny needs adaptation. Compare matched raw/spatial baselines, label needs and total computing cost. Sen1Floods11 labels water, not automatically new inundation.

**Existing discharge branch:** compare conventional analogue trajectories, matched raw-descriptor corrections and corrections with encoder features; zero EO influence is permitted. Assess next-24h MAE under rich basin, local-Q absence and all-Q absence. Nine experiments fit same-gauge annual heads; **DOFA tests held-watercourse transfer**, keeping Wurm/Worm together. Its rich regime aliases local-Q absence.

Models: Presto, AnySat, Galileo, OlmoEarth, CROMA, Prithvi, Copernicus-FM, DOFA, TerraMind and SatMAE. Model-specific matched configuration comparisons test selected readout mechanisms. [Implementation](limburg-individual-experiments-implementation-2026-10-29.md).

## Methodology

**Mapping:** grouped scene/event validation; accuracy, coverage, false alarms and measured cost. Preserve unknown pixels and distinguish permanent/event water and acquisition/delivery times. Published-split reproduction alone does not establish local transfer; one local event supports a case application.

**Discharge:** retrospective availability study, causal issue clocks, chronological fitting/tuning, train-only transformations, matched inputs/support and 999 shared whole-year bootstrap draws. Retain measurement flags and storm dependence. Retrospective access limits operational interpretation. Intervals are exploratory, without multiplicity adjustment; no untouched-test or preregistration claim.

## Findings

**Partial evidence:** eight experiments/23 primary jobs and four configuration comparisons reviewed; Presto/Galileo pending. No broad encoder increment over raw controls is evident. Most same-gauge heads choose conventional/raw-only predictions. DOFA has a favorable local-Q-absent high-water transfer contrast, but broad/flood intervals include zero and all-Q absence reverses direction. AnySat helps selected events without reliably recovering peaks/timing. German observations are included. [Partial readout](limburg-individual-partial-readout-2026-10-31.md).

Earlier age/outage and scarcity comparisons found no general EO improvement; retain them as distinct supporting results. [Inventory](analysis-inventory.md). Mapping findings do not yet exist.

**Next:** finish pending jobs; acquire task labels/local references, check units/masks and decoder compatibility, then specify the matched mapping comparison. Existing workers are unchanged; older supporting sweeps are not automatically submitted. Brian writes dissertation prose.
