# Audit of the accepted Limburg chapter — 10 November 2026

Internal research aid for Brian; no dissertation prose. Scope remains the agreed
three-pipeline, two-reference-policy study. No new model fit, bulk imagery pull,
cloud job or agency request was launched. Evidence consists of a fresh primary-
literature/documentation pass, the full held source/external metadata census,
source-raster headers and completed fit/cache receipts. This is not new accuracy.

## Overall judgment

**Keep this chapter. It is appropriately sized and methodologically grounded.**
It has one applied question: how model choice and pre-flood reference preparation
affect transferred flood maps and their preparation burden. The design is sound;
its new external-image integration is not yet run-ready. Resolve the specific
input/target contracts below rather than restart the broad programme. No positive
result, publication-score reproduction or minimum event count is a stopping gate.

The originality is a bounded empirical comparison, not a claim to have discovered
that reference images matter. Selection of Copernicus-FM is informed by task fit
and the completed, inspected experiments; disclose that history. The untouched
out-of-period evaluation is particularly valuable for the resulting settled design.

## Literature-to-design audit

| Primary source | What we take from it | What we do differently / cannot claim |
| --- | --- | --- |
| [Wang et al., Copernicus-FM, ICCV 2025](https://arxiv.org/html/2503.11849v2) and held author code | Separately encode pre/post SAR; difference spatial features; train a UPerNet head while freezing the backbone. | This is a published task route, not discharge inferred from pooled EO. Whole-event source evaluation and flood-class IoU differ from the author benchmark; do not expect or require its exact reported score. |
| [Hostache, Matgen and Wagner, 2012](https://doi.org/10.1016/j.jag.2012.05.003) | Direct precedent for choosing an appropriate no-flood SAR reference. | Publisher abstract/metadata reviewed; full methods were not accessible in this pass. Reference selection itself is established, not our novelty claim. |
| [Tupas et al., 2023](https://www.mdpi.com/2072-4292/15/5/1200) | Compare reference choices and competent SAR change methods; geometry, background state and reference definition matter. | Their temporal background models can outperform a recent single image. Our two-image policy study does not reproduce a full GFM system or establish that P1 is better. |
| [GEOID-Flood, 2026 preprint](https://arxiv.org/html/2608.02315v1), [pinned release card](https://huggingface.co/datasets/links-ads/geoid-flood/blob/15db1cc0babbe3e570aa9fb582823c533504c971/README.md) | Task-matched external flood/permanent-water evaluation and explicit cross-dataset processing. | Use the pinned release's actual counts and processing, not paper counts or its loader's normalization by default. Its derived permanent-water label is not independent field truth. |
| [Phunjanna et al., 2026 preprint](https://arxiv.org/html/2608.30895v1) | Separate pipeline ranking, fixed-checkpoint input reliance, geographic weighting and deployment claims. | Our P1 is an obtainable alternative reference, not an arbitrary corrupted-input test. We estimate the fixed-pipeline input-policy effect, not the causal effect of pretraining or attainable accuracy after retuning. |

This is a synthesis of existing methods, not a new segmentation architecture.
It can produce new knowledge about the model × reference-policy interaction,
its event-specific error mechanisms and the resources needed to obtain it. That
contribution remains empirical: a tiny or imprecise difference must be reported
as such, not promoted into equivalence, avoided loss or institutional benefit.

## Findings and necessary refinements

### 1. Hold processing and targets fixed, as well as the model

P1 must not simultaneously change reference date, radiometric product, processor,
resolution and resampling. Prefer the same processing chain as delivered P0.
If P1 must come from another service, verify/recreate P0 through that chain first;
if both policies require harmonized imagery, record that change explicitly rather
than call a processing effect an age effect. Event imagery is common to P0/P1.
[SAR processing options](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S1GRD.html)
include distinct calibration, correction and filtering choices; conversion from
dB to linear alone does not establish compatibility. Kuro's processed source data,
GEOID GRD/RTC and existing GEE scenes need an explicit bridge. Do not infer gamma0
from the name RTC: the pinned card and paper use differing descriptions.

Keep the model's supported linear-intensity input, [0,.15] clip, author per-date
statistics and actual date/location/token-area metadata explicit. The held author
statistics are asymmetric between dates; that is confirmed author-code behavior,
not a silently corrected typo. Record their benchmark-training provenance rather
than claim newly estimated fold-only statistics. Check finite pixels, clipping,
per-date metadata and identical-acquisition behavior using source-only diagnostics.
Physical methods receive the same raw acquisitions and valid footprint; they need
not inherit neural standardization/clipping as an artificial restriction.

The evaluation flood target must be the **same** in P0 and P1. Do not reconstruct
"truth" from whichever pre-image is being tested. Preserve the CEMS floodmask,
composed three-class label, permanent-water mask and disagreement between them.
Report original flood-delineation agreement alongside the declared composed-label
score where class composition changes flood support. This uses already selected
masks, not a new labeling programme.

### 2. Make the acquisition policy fully executable

Choose the latest eligible compatible image before a documented event onset,
under one source-fixed orbit/look geometry, calibration, valid-coverage and
chronology rule. Record platform and swath geometry, not merely ascending versus
descending. Do not select an image using its target-model score or manually
inspect labels to find a pleasing reference. Catalogue event time is a lead for
onset, not automatically local onset truth. A new image may already show elevated
water; older references can also be seasonally inappropriate. These are reasons
to test the policy, not assumptions of benefit.

An unchanged P1=P0 is a zero-change policy outcome. Missing P1 has no invented
prediction: retain P0 and report applicability plus genuinely paired support.
Do not turn non-coverage into dry land or selectively omit the hard cases.

### 3. External evidence is stronger than a local case alone, but has qualifications

The census script read all **5,000 source records / 20 events** and all
**1,301 external tiles / nine activation IDs**, not a sample. Source post-images
range 2015-02-02 to 2022-02-03. External events are in 2026: temporal new-event
separation is supported. **26 external tiles, all in EMSR868 (Greece), intersect
source-record bounding boxes.** Keep them in new-event evaluation and identify
source-overlapping versus new-footprint results. Non-overlapping tile footprints
do not prove unfamiliar river basins, regions or climates.

**251 external tiles have a listed post-SAR acquisition more than 24h from the
listed label reference time**, with some offsets exceeding five days. This is a
metadata discrepancy to reconcile, not proof each label is wrong. Check actual
CEMS sensor/product timing; retain the full released-cohort account and show
results by timing/provenance. The 24h count is diagnostic, not a universal validity
cutoff. Floods can change within hours. Where timing remains unresolved, call the
score reference-map agreement, not verified simultaneous inundation accuracy.

Nine activations are not automatically nine independent storms. Resolve linked
Iberian activations/documented flood episodes before event-resampling claims.
The Portugal/Spain activations contain 737/1,301 tiles, so make event-balanced
results primary, with pixel/area-weighted totals separate. Aggregate repeated or
overlapping mapped ground cells once per physical-event comparison; retain every
released record in coverage/provenance. July 2021 local AOIs remain dependent and
previously inspected, useful for interpretation rather than a second pristine test.

### 4. The physical control needs a named, defensible specification

The existing control is a validation-calibrated dark-water/backscatter-drop rule,
not GFM. Source-only calibration, proper geometry/radiometry, a declared spatial
noise/mask convention and performance checks against the selected SAR literature
are needed before calling it a competent conventional comparator. Freeze one
well-supported implementation; do not add four physical-model families. Extra
DEM/HAND/history is not automatically required by the two-image question.

### 5. Reuse source fitting; do not multiply external inference by source folds

There are **15 full-label source-fold states for Copernicus and 15 for standard
U-Net**, each across five folds/three seeds. Fifty actual candidate fits were
used in those 30 selections; archived checkpoints have recovery receipts.
That supports reusable development evidence, not automatic availability of an
all-source model. Their selected fits trained on source crossfit subsets.

For primary external inference, use one final source-trained state per learned
pipeline per seed (six states), with a source-only selection/refit rule. Set epoch
budget and hyperparameters from development records, then fit the declared final
source pool without inspecting external scores. Do not implicitly deploy a
five-fold ensemble or repeat 30 CV states because the study has two references.
Existing states may instead be reused where their actual population and selection
contract is the declared analysis; identify the reduced training pool honestly.
Eight of 30 selections are at a learning-rate boundary (3 native, 5 U-Net): review
source learning/stopping evidence, with targeted source correction if warranted.
A boundary is diagnostic, not a compulsory expensive sweep or invalidation.

### 6. Native-grid inference and uncertainty need the new cohort integration

All source chips are 224px; external tiles are 1024px at nominal 10m. **Do not
shrink a whole target tile to224px.** Cover the native grid in declared windows,
update crop metadata, pad/mask edges and verify stitching/coverage. The existing
local application hardcodes512px; it cannot simply be reused for1024px tiles.
Any overlap/halo convention is selected using source development, not target IoU.

Average training-seed results within events before paired event inference;
seeds, pixels, AOIs and overlapping tiles do not supply independent event n.
Report each event, leave-one-event/linked-episode-out summaries and descriptive
uncertainty, including undefined no-flood IoU cases. The model × reference contrast
uses exactly paired support. Avoid a large significance-search table; primary
reference effects and interaction are estimates with uncertainty. Map errors,
coverage and reference age explain the result without another learned model.

## Required data and acquisition path

| Input | Held / remaining | Actual need |
| --- | --- | --- |
| Source paired SAR/labels | All5,000 held; all224px headers checked | Reuse source images, identity/quality records and compatible frozen features |
| Copernicus weights, head implementation; U-Net | Held; 30 completed source-fold selected states, recovery documented | Reconcile final-source state contract; no new backbone |
| External delivered SAR + label/validity/floodmask/permwater | Pinned metadata; nine shards **9.068GiB** not pulled by this audit | Retrieve only selected layers; actual raster/radiometry and mask QA follows |
| Compatible updated pre-flood SAR | Not inventoried | Search [CDSE STAC](https://documentation.dataspace.copernicus.eu/APIs/STAC.html) on declared footprints; obtain the same processing product. P1 one two-band date over all1301full tiles is **10.164GiB uncompressed float32 payload** before overlap deduplication/compression, not a download quote |
| Processing parity and CEMS source-time metadata | Some catalogue names/times held; source processing and actual label timing need reconciliation | Use provider code/tags and open CEMS records; matching-chain P0/P1 retrieval may add data if delivered products cannot be reproduced |
| Existing NL/DE SAR, mapped references, René/Jens notes | Held | Local timing/error context; no extra gauge/weather request introduced |

The tar shards are uncompressed containers of compressed GeoTIFFs. Keeping the
COGs avoids immediately expanding the entire cohort into large uncompressed
arrays. The 9.068GiB is the packaged transfer, not total working storage.
No optical, dense AlphaEarth, extra meteorology or new local-label campaign is
needed for this accepted question. A DEM may be an internal processor input if
required to reproduce the existing product, not a new model branch.

## Compute and storage audit

Measured machine: Apple M3 Pro,36GiB unified RAM. About122GiB free at audit;
50GiB reserve leaves approximately72GiB usable before further offload.

- Keep **one MPS worker and up to two CPU workers**, with actual unified-memory
  and disk admission. Copernicus's metadata calculations currently use CPU;
  task-head fitting runs on MPS. Do not assume the whole encoder can move to MPS.
- Previous full-label selected fits took medians of **82min native** and
  **38min standard U-Net**, on source subsets with shared cached features.
  These are observed fit times, not new all-source or end-to-end estimates.
- Existing frozen source cache:5000pairs,11.216GiB,894.7s recorded total. A simple
  extrapolation for all1301target tiles,25windows/tile and three distinct dates
  gives **~2.4h for encoder preparation alone**. This excludes heads, U-Net,
  reading, masks, stitching, transfer and archiving. It is not a run ETA.
- With25padded224px windows/tile, the external census entails **32,525 spatial
  windows**, up to97,575unique date-encoder views and390,300learned window forwards
  (two pipelines × two policies × three seeds). Overlap increases these counts;
  absent/identical P1 and source-selected support handling may reduce them.
- Caching every date feature would occupy **~219GiB**; caching both full difference
  feature sets ~146GiB. Twelve per-seed learned probability maps per tile total
  **~183GiB uncompressed**; four seed-mean maps ~61GiB. These are shape arithmetic,
  not transferred or measured compressed sizes. Keeping all argmax maps alone
  would use ~17.8GiB and would not preserve probability diagnostics.

**Use tile/event streaming**, shared per-date encoding across the three seeds,
lossless outputs, bounded rotating caches and verified remote preservation.
Consume each feature block in all needed heads before retirement; retain exact
inputs, weights, predictions and analysis provenance needed for recovery. Do not
silently discard individual probabilities merely to fit the disk. No change to
labels, seeds, support or scientific comparison is needed for this optimization.
Target an initial20–40GiB additional local working envelope with rotation; this is
a scheduling allowance to profile, not a measured peak or universal hard limit.
Unbounded new-data caches do not fit the present disk.

Planning scale is **days of local compute, not the former multi-week adaptation
programme**, if completed source development is reusable. A precise calendar ETA
needs the actual final-source recipe, source corrections (if any), P1 support and
one representative complete1024px inference/archive pass. Additional source
search/processing harmonization must be charged explicitly. No claim of a cheaper
or faster deployed service follows from these preliminary receipts.

## Next preparation, staying within scope

1. Write selected radiometry/class/reference/physical-method contracts and verify
   source-state compatibility, including a true final-source refit recipe.
2. Pull the pinned external core, reconcile label-source times and geography, and
   catalogue P1 under the fixed processing/chronology rule. Keep a complete record
   of exclusions, duplicate support and unchanged/unavailable updates.
3. Implement/test1024px native-grid inference, paired scoring and streaming recovery;
   profile a complete representative tile before giving the execution ETA.
4. Run the accepted comparison and its targeted source/error checks. The archived
   multi-model, target-adaptation and AlphaEarth branches remain archived.

Receipts, full census CSVs, source headers, exact formulas and reproducible audit
code are in [the companion directory](limburg-chapter-scope-audit-2026-11-10/).

## Position of the Limburg receiving case

The primary new-event evidence comes from the external cohort; Limburg supplies
a grounded Dutch/German receiving case and timing/observability interpretation.
Do not describe those external estimates as measured NL/DE operational performance
or the local July2021 case as evidence about every tributary. Nominal10m SAR and
its acquisition schedule will not resolve every narrow-channel or peak-flood
feature. This is a mapping/reference-quality chapter with local application,
not the earlier tributary-response chapter under a new model name.
