# Limburg — pre-flood information and satellite-AI flood mapping

Living research brief. **Scope accepted by Brian, 10 November 2026.** Brian writes
the dissertation; this is an internal research aid.

## Research Question(s)

**How do satellite AI and conventional methods compare in mapping new flood
events, and how does the choice of pre-flood reference affect their performance?**

Two connected comparisons: performance of task-appropriate pipelines on new
events, and the effect of replacing the delivered reference with a compatible,
more recent pre-flood image while holding the event image and model fixed.

## Motivation

Flood maps support situational awareness and disaster-risk assessment. Reusing
an AI model also requires suitable observations and preparation. The chapter
examines whether model choice, reference preparation, or their combination
changes map quality and coverage, and measures the associated resource burden.
This can inform agency data/pipeline priorities; it does not demonstrate better
warnings, agency adoption or avoided losses.

## Data

Held source data: 5,000 paired-SAR radar-change records across 20 events, with
known water-containing sample selection. Existing Dutch/German individual radar
acquisitions and mapped references provide receiving-case evidence. René/Jens
records supply event timing and measurement context, not pixel flood labels.

External evaluation: all 1,301 released tiles across nine 2026 GEOID
heldout activations, subject to source/event/geographic and label checks. The
SAR/label/validity/permanent-water package (**9.068 GiB**) is downloaded and
hash-verified. The updated-reference inventory has 1,118 metadata candidates;
915 permit a single-product P0/P1/post triplet and 913 of these map to
the tested Earth Engine collection. All 913 harmonized triplet rasters were
downloaded and independently verified. Local July 2021 maps were already
inspected and represent one physical flood, not independent confirmatory events.

## Method

Three pipelines: (1) Copernicus-FM frozen paired-SAR encoder with trained spatial
head; (2) same-input standard U-Net; (3) competent reference-aware physical SAR
change/water method. Each receives P0 delivered reference and P1 updated compatible
reference under a source-fixed, label-blind acquisition rule. No third-image
fusion or target fine-tuning. Reuse exact compatible source fits; use source-only
selection and three source-training seeds for learned pipelines.

## Methodology

A paired comparative study of model and information quality. Retain the full
eligible external census and all assessable local radar cases. Hold event images
and trained weights fixed across reference policies. Evaluate method differences,
within-method P1−P0 changes, and their interaction using flood-class IoU,
permanent/flood confusion, false/missed mapped area and common/full support.
Respect physical-event dependence and label/reference provenance. Record actual
preparation, fitting and mapping costs. Absent imagery remains unknown; missing
P1 updates stay visible in coverage and applicability reporting.

## Findings

**No findings yet for the accepted reference-policy comparison.** Earlier
completed discharge/analogue and spatial work is retained as supporting evidence.
It did not establish a general satellite-AI advantage; those results motivated
more task-appropriate mapping and a focused information-quality question. They
are not results of P0 versus P1.

All six source-only final fits and the full external mapping census are complete.
Accuracy scoring, paired event comparisons and a systematic map atlas are now
running in a recoverable queue. Predictions are backed up in 46 verified Azure
archives (83.1 GiB); scoring restores bounded batches and retains compact class
maps locally. Local-case coverage and comparison remain outstanding.
The 409 released tiles with
no flood-class target pixels remain in false-alarm/coverage reporting.
[Agreed design](limburg-chapter-sized-study-2026-11-10.md) ·
[Data needs](data-needs.md) · [Handoff](HANDOFF.md) ·
[Completed findings](limburg-consolidated-findings-2026-11-10.md) ·
[Future ideas](../archive/future-ideas/2026-11-10-broad-spatial-programme/README.md).

Latest [scientific/data/compute audit](reviews/limburg-chapter-scope-audit-2026-11-10.md)
and [acquisition/grid audit](reviews/limburg-steps2-3-acquisition-grid-2026-11-10.md):
keep the scope. The paired reference experiment uses one harmonized SAR chain;
source processing differences, coverage and local-case provenance stay visible.
