# Limburg — pre-flood information and satellite-AI flood mapping

Living research brief. **Scope accepted by Brian, 10 November 2026.** Brian writes
the dissertation; this is an internal research aid.

## Research Question(s)

**How do satellite AI and conventional methods compare in mapping new flood
events, and how does the choice of pre-flood reference affect their performance?**

Two connected comparisons: performance of task-appropriate pipelines on new
events, and the effect of replacing the delivered reference with a compatible,
more recent image preceding the provisional event cutoff while holding the
event image and model fixed.

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
head; (2) same-input standard U-Net; (3) source-calibrated physical SAR
threshold/change rule. Each receives P0 delivered reference and P1 updated
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

The mapping, event review and validity consolidation are complete. The external
paired census has 913 tiles; 447 have references matching event-image geometry.
All 167 local scene/grid records pass geometry. The international cohort supplies
principal evaluation evidence; local July 2021 cases form one Dutch/German
receiving episode, not independent country comparisons.

On compatible geometry, episode-balanced flood IoU is .452 Copernicus-FM,
.445 U-Net and .341 physical under P0; .365/.372/.280 under P1. Copernicus minus
U-Net is +.008 [−.023,.037]: no clear superiority or equivalence. Its newer-reference
change is −.087 [−.224,.001], attenuating to −.022 [−.063,.008] when the existing
listed <=24h radar/label timing check is also applied. Cohorts change with these
restrictions; attenuation does not isolate geometry or timing as its cause.

The event review finds heterogeneous changes in flood designation, including
switches to permanent-water and background predictions and improvements in
precision. Broad water recognition can remain intact. The target is agreement
with the released event-flood classification, not independently verified new
inundation since P1. Derived permanent-water labels and local reference timing
qualify interpretation. Newer references are not demonstrated to be generally
harmful, and reference sensitivity itself is established in earlier literature.

The unrestricted full-catalogue results and all prior model outputs remain
preserved. The geometry restriction is a transparent post-result validity
correction, not a fresh confirmatory experiment. No new model, selector,
training run or data branch is needed to report the completed comparison.

Final source-fit logged epochs total about 2.03h Copernicus and 1.27h U-Net,
excluding source development/cache preparation/startup. External execution windows
are 10.47h and 4.97h including IO/archival overhead, not isolated inference or
operational latency. Predictions remain in 46 verified Azure archives (83.14 GiB).

[Current consolidated account](limburg-study-consolidation-2026-11-11.md) ·
[Numerical receipt](reviews/limburg-validity-consolidation-2026-11-11.json) ·
[Agreed design](limburg-chapter-sized-study-2026-11-10.md) ·
[Handoff](HANDOFF.md) ·
[Historical spatial findings](limburg-consolidated-findings-2026-11-10.md) ·
[Future ideas](../archive/future-ideas/2026-11-10-broad-spatial-programme/README.md).
