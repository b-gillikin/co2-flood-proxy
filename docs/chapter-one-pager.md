# Chapter 1 — Limburg: satellite AI under limited ground monitoring

Last substantively reviewed: 2026-10-31. Living supervisor/research brief; internal research aid, not dissertation prose.

## Research Question(s)

**Can satellite AI help assess developing high water when ground-monitoring data are limited?**

Use held NL–DE observations as verification, reduce the information available to an assessment, and test whether satellite representations help beyond comparable conventional and raw satellite inputs.

## Motivation

Monitoring can be delayed, interrupted or sparse. The practical FEWS/DRR question is whether satellite context improves assessment of the next day's river response when ground observations are limited. Our held-data reference is not the full Dutch/German operational forecasting service. Simulated shortages do not establish actual outage frequencies, and trajectory accuracy does not establish inundation or warning skill.

## Data

Eight Dutch/German tributary gauges, catchment rainfall, provider quality notes, catchment geography, ten frozen EO encoders and supporting Maas observations. The shared calendar contains **481 regional storms**; each individual experiment has **15,392 assessment opportunities per regime**, including repeated issue times and nonresponses, before support/outcome checks. Retain the full eligible census and report unsupported cases. Soil/snow acquisition is complete: **204/204 months, 2009–2025**; its shared physical-state control is prepared, not fitted. AlphaEarth, TTM, weather and warning records remain supporting evidence. No new provider delivery is essential to completing the current experiment.

## Method

Ten individually designed experiments respect checkpoint inputs/readouts. Compare a conventional analogue mean trajectory (C), a chronological correction with matched raw descriptors (C+R), and the same correction with frozen encoder features (C+R+E). Zero EO influence is permitted. Assess next-24h point-trajectory MAE in mm/h and native m³/s under rich basin, local-Q absence and all-Q absence. Nine experiments use same-gauge annual heads; **DOFA separately tests held-watercourse transfer**, keeping Wurm/Worm sites together. Its rich regime aliases local-Q absence.

Models: Presto, AnySat, Galileo, OlmoEarth, CROMA, Prithvi, Copernicus-FM, DOFA, TerraMind and SatMAE. Model-specific matched configuration comparisons test selected readout mechanisms. [Implementation](limburg-individual-experiments-implementation-2026-10-29.md).

## Methodology

Retrospective controlled observation-availability study: causal issue clocks and earlier closed training labels; chronological fitting/tuning; train-only transformations; exact raw-input parity; fallback and paired-support accounting; shared 999 whole-year bootstrap draws. Account for repeated issues/storm dependence and retain measurement flags. EO acquisition dates and retrospective model/reanalysis access limit operational interpretation. Intervals are exploratory and conditional, not multiplicity-adjusted. This direction evolved after earlier analyses; no untouched-test or preregistration claim.

## Findings

**Partial current evidence:** eight experiments/23 distinct primary jobs and four configuration comparisons reviewed; Presto and Galileo remain pending. No broad encoder increment over matched raw controls is evident in completed jobs. Most same-gauge heads select conventional/raw-only predictions; small arm differences are not automatically EO contributions. DOFA has a favorable local-Q-absent high-water transfer contrast, but its broad/flood intervals include zero and all-Q absence reverses the point direction. AnySat helps selected events without reliably recovering their peaks/timing. German observations are included; several models' DE high-water ties reflect zero selected EO contribution. [Partial readout, event examples and hashed snapshot](limburg-individual-partial-readout-2026-10-31.md).

**Retained earlier evidence:** completed fixed-retrieval age/outage and scarcity comparisons did not show a general EO improvement. Later model-specific diagnostics extracted small conditional increments but did not reliably beat the strong conventional trajectory. They remain distinct supporting results, not interchangeable versions of the current experiments. [Analysis inventory](analysis-inventory.md).

**Next:** finish/audit the two pending models, consolidate all ten, then separately implement the prepared soil/snow, combined-mask, C+E attribution and SatMAE product/support checks. [Supporting preparation](limburg-individual-supporting-preparation-2026-10-31.md). No new supporting computation was launched during this review. Brian writes all dissertation/article prose.
