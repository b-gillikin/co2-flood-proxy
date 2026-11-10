# Full plan audit: reconciled science, data and execution

10 November 2026. Read the execution roadmap, model contracts, first design audit,
compute design/policy, acquisition manifest, pinned catalogues and held author/
production adapters together. This is internal research planning, not dissertation
prose. Findings below correct cross-document contradictions; they do not discard
earlier results, add a backbone, reduce the census or require a positive result.

**Verdict:** retain the main RQ and W/F/T programme. The substantive contribution
remains evidence about reference quality and complementary local resources for
reusing flood maps in unfamiliar landscapes. The plan now has a coherent design,
but the old long queue is not an executable implementation of it. Work should
move to concrete data/model contracts and queue construction, not an additional
general model search or an endless series of design audits.

## Findings and disposition

| Priority | Finding | Correction / status |
| --- | --- | --- |
| High | Published GEOID val/test acquisition does not cover the released footprint of its candidate events | Computed the actual deficit; new pinned event-completion cohort and acquisition v2. No bulk transfer launched. |
| High | Compute text made a changed test set imply a changed fit | Separate training, inference and scoring identities. New planning helper/tests prevent this redundant fitting while preserving per-evaluation leakage checks. |
| High | r+2 tuning arithmetic was applied too broadly to source refits | r+2 only when the winning trial has the identical final training/selection contract. Changed source population needs all final refit seeds, usually r+3 for one shared-search block. Source CV search costs remain separate. |
| High | Provider benchmark-train normalization may contain our held target events | Pretraining statistics and benchmark-train statistics are different provenance. Use source-only permitted statistics for T0; reference reproduction may retain author statistics but is separately named. |
| Medium | Three target seeds were described as pure optimization variation, although source and target learning are linked | Define three paired end-to-end source→target seed chains, crossed with three label draws. Report combined seed-chain variation; do not claim separate source-versus-target variance identification. No nine-chain expansion. |
| Medium | Informative annotation was not yet a concrete algorithm | Primary T3 is one-shot source-model uncertainty/diversity ordering with source-fixed rules; iterative active learning remains a separately declared variant if implemented. Do not smuggle in additional fits/labels or call one-shot selection an iterative AL reproduction. |
| Medium | Difference-only change features may suppress stable absolute water information | Retain native author route, inspect permanent/flood confusion and add a training-only feature-information diagnostic. This is a representational risk, not a discovered bug or a new mandatory head/model sweep. |
| Medium | Broad issue-time language could imply a historical operational replay | This study uses current models on historical observations. Actual historical service availability/arrival logs are not supplied. Geographic transfer and retrospective input chronology do not establish real-time deployment or warning lead time. |
| Medium | A 3-class reference is not automatically acquisition-time visible water | Preserve dataset label construction/precedence, separate derived reference-water/flood layers and unknowns. Restrict W claims to compatible observable-water references; use native three-class semantics for F. |
| Low | Stale numerical counts/ETAs remained active-looking in JSON | Move superseded estimates to an explicitly historical field; actual W job counts remain unenumerated. Keep dated evidence, not an active 6–16-week promise. |
| Low | Exact interruption continuation risked becoming an unattainable bitwise requirement | Save complete resume state and verify data order/updates plus declared numerical replay tolerances. Do not promise bit-identical nondeterministic MPS execution or stop other branches if it is unavailable. |

## 1. Event census and acquisition correction

The pinned main catalogue's validation/test union represents **100 activation
IDs**, not 80+34 independent events. Its 3,439 tiles omit **2,097 train-named
tiles from 49 of those same events**. Including all released tiles of that event
cohort gives **5,536 main tiles**. With the separate nine-event/1,301-tile package,
the candidate acquisition footprint is **109 activation IDs / 6,837 tiles**.
These are candidate development/calibration/test resources, not 109 certified
independent floods or 109 final test domains. Storm/geography reconciliation and
role assignment remain necessary. No undocumented pixels outside the mapped
footprint become dry ground.

The v2 cohort specifies all released tiles for those events, regardless of the
provider split. A train-named tar member is not automatically training data in
our study. Missing same-event members cannot quietly be omitted from a claim
about the complete released footprint. Remaining noncohort events contained in
the same packages do not automatically enter source fitting or evaluation.

The existing package structure gives a conservative transfer envelope of
**145 shards / 224.373 GiB**, compared with v1's65shards/87.010GiB. The additional
80train-named shards total137.362GiB; this overfetches packaging because reliable
event-level tar offsets/selective transfer are not yet verified. Retain only
eligible exact cohort members as study inputs. This is a network/package upper
envelope, not simultaneous disk occupancy or a reason to keep all tar copies.
Use bounded staging, verified recovery and actual Azure headroom/cost accounting;
do not assume the old storage allowance fits every archive or increase it silently.

Both manifests are preserved. v1 is historical; execution now points to v2 and
the event-completion cohort. No download was started. If future source/role
assignment genuinely needs additional events, document that cohort amendment;
do not silently treat all package contents as authorized training information.

The current dataset card explains that **v1.1** revises the data described in
the **v1.0 paper**. The earlier count difference is therefore not in itself a
provider error. Pin model-reproduction populations separately from v1.1 external
evaluation. Author splits preserve AOIs, not necessarily whole activations.
[Author dataset card](https://huggingface.co/datasets/links-ads/geoid-flood).

## 2. Actual metadata checks completed

Across all6,837candidate tiles, the acquisition timestamps parsed from the
listed product IDs had:

- zero missing pre-SAR/post-SAR/pre-optical acquisition dates;
- zero pre-SAR acquisitions on/after the post-SAR acquisition;
- zero listed pre-optical acquisitions on/after either the event metadata time
  or the post-SAR acquisition.

These are useful checks that passed. They do not certify raster masks, class
semantics, intensity units, orbit compatibility, label date coincidence or service
arrival time. Parse sensing time, not processing/reprocessing time in product
names. S2 can be a mosaic: retain actual source-product provenance rather than
treat the CEMS delineation timestamp as a single optical observation. Current
product-list chronology does not create unheld per-pixel acquisition dates.
Raw rasters must still be audited as acquired. The author's delivered radar
precision/quantization is part of the pinned release; our lossless caches preserve
those delivered values, not nonexistent original full-precision observations.

Machine evidence: `limburg-three-prong-full-audit-data-2026-11-10.json`.

## 3. Three identities, with separate eligibility checks

**Training identity** includes model/checkpoint and initial state, training
inputs/labels, validation/selection contract, preprocessing fitted population,
seed/optimizer/schedule/stopping, sampling/augmentation/window order and numerical
runtime. Hash every declared training field, including future additions. Target
images used for transductive fitting belong here. Missing settings cannot
authorize reuse.

**Inference identity** additionally identifies the selected weights, target
imagery/metadata, preprocessing, tiling, numerical policy and output class grid.
Different target scenes need different predictions, not source refits. Different
temporal neural inputs/heads likewise need their corresponding inference.

**Scoring identity** identifies prediction version, labels/validity, region/event
role, calibration/reference/threshold policy, stitching and metric definition.
Different references or evaluation subsets may share predictions but retain
separate scores. Any fitted calibration has its own fitting/label provenance.

For every reuse, prove the relevant target is excluded from forbidden source
fitting, selection, normalization, calibration and adaptation blocks. Identical
training hashes alone do not prove independence. Identical cached source rasters
do not authorize sharing learned target models. Exact full-pool/rounded-budget
aliases apply only with fixed candidate/test blocks, canonical selected records
and identical training order/policy; a different selection history breaks the alias.

The added `spatial_plan_audit.fit_identity` enforces a conservative planning
identity, not a complete scientific eligibility certification or production
deduplicator. Tests cover changed labels, selection, initialization, numerics,
future training fields, missing identities and independent evaluation reports.

## 4. Source selection versus refit

For an unchanged final training/selection pool, one seed's r-rate search supplies
its selected state and two new seed fits: r+2. If a final source refit expands the
training population or changes its stopping contract, the tuning winner is not
that refit. Budget r+3 for one shared-search block plus three refits; separately
include all required source-CV/meta-validation fits. An r+2 saving cannot be
asserted for a changed data population merely because the architecture matches.

Reserve calibration labels or generate valid held-out calibration predictions
under the stated design. The source-refit stopping/update policy is fixed from
source meta-validation when target labels are unavailable; it cannot select its
best epoch on the target reference. Model-specific author-reference reproduction
retains its own original population/metric/tuning protocol and is not counted
as a second independent scientific result.

Normalization is subject to the same rule. Model-pretraining constants can be
documented prior information. A provider's benchmark-train mean/std may include
our target events after regrouping; it is not automatically a legitimate
source-only constant. T0 recomputes permitted statistics on its source pool or
uses a justified pretrained contract. Unlabeled target normalization, if tested,
is a declared target-adaptation configuration with its information/cost counted.

## 5. Model, endpoint and annotation checks

Keep each model's spatial task and canonical radiometry, published modality
normalization, original support, masks, strict state loading and intended
trainable/frozen boundary. PEFT needs gradients through intervening frozen layers
to its adapters and is not implemented by a complete frozen-feature cache.
L1C/L2A, post optical versus pre optical, date metadata, true DEM support and
unknown-versus-background distinctions remain substantive compatibility checks.

Copernicus-FM's difference head follows the author implementation. A difference
alone can discard absolute stable-water information: two equal feature maps
give zero regardless of whether their content is water or land. Actual inputs
also have dates and asymmetric source normalization, so this observation is not
proof that real scenes yield equal features or that the head cannot work. Test
controlled feature/normalization fixtures and permanent-water errors before a
claim about model-family capability. Keep modular W-to-F comparisons available;
do not add an unannounced absolute-feature branch only after external scores.
[Author method](https://arxiv.org/html/2503.11849v1).

The primary three T seeds are **end-to-end seed chains**: source model seed and
its target training seed are paired, then crossed with three independent nested
annotation draws. Report joint source/target training variability separately
from annotation variability. This does not identify source versus target
optimization effects individually and does not require a new3×3seed Cartesian
product. The usual30-state illustration is unchanged when full-pool aliases are
legitimate; actual compatible-domain counts and repeated rounded pools govern
the final queue.

Primary T3 is **one-shot informative annotation**: generate uncertainty and
spatial-diversity ordering from the fixed source model and unlabeled candidate
imagery; tune scoring/aggregation/weights only on source pseudo-targets, randomize
ties reproducibly and acquire full patches at the shared nested budgets. No
unseen reference labels determine class balance, scores or stopping. Full-pool
training order is canonical. Include the complete selection inference cost.
Iterative AL can remain a declared variant if an algorithm is specified; it
requires charged intermediate fitting/query rounds and no leakage from the held
test blocks. One-shot ordering is not an exact ALFA reproduction.

W measures observable water at acquisition time. F preserves the native target
definition and label construction: permanent-water and flood inventories need
not equal visible water on every dated image. Report class precedence/conflicts
and independent-reference sensitivities rather than silently relabeling every
nonzero class as reliable acquisition-time water. Deriving an input prior from
the target map remains forbidden. The existing independent AlphaEarth-reference
requirement is retained; no new compulsory manual annotation is added.

## 6. Reporting and implementation disposition

Choose the resampling/estimand unit for the endpoint: physical-event summaries
for event mapping, independent landscape-held-out groups for unfamiliar-region
claims, and a repeated-landscape endpoint for new events in familiar regions.
Record storm/geography overlap; several AOIs or repeated acquisitions do not
become independent floods. Report paired common-support differences plus each
pipeline's full coverage and unknown/review burden. Label-selection and seed-chain
variation are separate; folds/pixels do not provide extra independent events.
Small independent support limits precision, not chapter continuation.

Current-model mapping of historical imagery is a retrospective capability study.
Backbones, datasets and annual products can have been released after those floods.
Even cutoff-safe imagery does not establish that a historical agency had those
models, timely delivery or the same resources. Policy outputs are tested mapping
trade-offs and complementary resource requirements, not simulated warning skill
or proven adoption/avoided harm. No new monitoring-log request is necessary for
the stated questions.

**Implementation remains:** source/target role manifest, actual raster/model
contracts, explicit fusion/adaptation/probability paths, dependency-graph queue,
full end-to-end profiling and verified recovery. The new identity helper and
metadata checks advance preparation; they do not certify those unimplemented
parts. No new fit, model/download queue, empirical accuracy or gate pass occurred.
All previously requested branches remain; observationally incompatible cells are
reported with reasons, not fabricated or treated as dry.

Existing working edits to Brian's one-pager and all other chapter data remain
preserved. Legacy estimates and v1 acquisition are retained as dated history;
the active configuration points at the corrected records.
