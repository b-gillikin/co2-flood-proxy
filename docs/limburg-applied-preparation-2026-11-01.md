# Applied mapping: runtime, tuning and local reference preparation

1 November 2026. Internal working specification and engineering record; Brian
writes dissertation prose. Extends the [execution record](limburg-applied-implementation-2026-11-01.md).
No comparative mapping result is reported here. Existing extraction and the
nine-job waiting profile queue retain their original source fingerprints.

**Subsequent design review:** the [dated research-design and literature review](reviews/limburg-applied-design-and-literature-review-2026-11-01.md)
identifies remaining physical comparators, total-label accounting, short-batch
handling and event-level synthesis before interpreting applied comparisons.
The executable preparation below does not establish that those scientific
comparison tasks are complete. Recommendations have not changed active workers.

**Subsequent implementation:** [the review corrections](limburg-applied-review-implementation-2026-11-01.md)
supersede the short-batch and comparator conventions below for new v2 fitting:
all training examples are retained, a conventional U-Net and physical controls
are added, and total label use is explicit. Earlier engineering records remain
historical; active extraction/profile sources are preserved.

## Copernicus native runtime

**Resolved on CPU.** Built real `mmcv==2.1.0` compiled operators on Apple Silicon
against held PyTorch2.9.1, with `MMCV_WITH_OPS=1 MAX_JOBS=1`. Removed mmcv-lite
from the isolated Copernicus overlay only. Native MMSegmentation1.2.2
Feature2Pyramid, UPerHead and FCNHead now import and execute. No dummy operators,
replacement decoder or original extraction-environment upgrade was used.

Build metadata initially failed because current setuptools removed
`pkg_resources`; pinning overlay setuptools80.9.0 fixed that. The benchmark
constructor also requests an obsolete `var_embed_llama3.2_1B.pt` URL (404).
Its required five dictionary keys are present in the held, renamed
`varname_embed/varname_embed_llama3.2_1B.pt`. The adapter creates a checked
legacy-filename symlink to those exact bytes. This does not edit vendor Python
or invent language embeddings; spectral radar forward does not use that branch.

The native real-data check used two distinct held radar records at224px,
strictly loaded all checkpoint keys, produced both3-class maps, backpropagated
finite gradients through51 head parameters, and confirmed no encoder gradients.
Batch-one evaluation also passed. SyncBN was retained without conversion.
The CPU engineering run took about6seconds under concurrent work; this is
**not** a comparative speed benchmark or trained-head accuracy result.

- [Native adapter](../src/applied_copernicus.py) and [repeatable check](../scripts/193_check_copernicus_runtime.py).
- [Build recipe](../environments/applied/build-copernicus.sh),
  [versions and hash-bearing check](../environments/applied/copernicus-native-check.json).
- Local build/install logs: `results/applied_study_v1/runtime/`.
- Recipe follows the [official MMCV macOS build instructions](https://github.com/open-mmlab/mmcv/blob/main/docs/en/get_started/build.md).
- MPS has not been tested because Galileo still owns it. CPU compatibility does
  not establish MPS compatibility, throughput or feasible full-grid cost.

Primary radar preprocessing retains the published0–.15 linear-intensity clip,
means and asymmetric pre/post standard deviations. Record that asymmetry as a
source convention, not an unnoticed correction. All four source channels must
be finite and nonzero; MNA/ignore3 remains unknown. Imputation for network
context does not restore a target label. Same-input comparators use exactly
these tensors and validity masks. This is an author-compatible normalization
comparison; it does not establish that those normalizers are universally best.

## Fair, validation-only comparator tuning

[Runner192](../scripts/192_tune_applied_water.py) supports TerraMind, Galileo,
Prithvi and Copernicus change tasks. It defaults to a printed plan. `--run`
explicitly starts fitting; `--evaluate-selected` permits **one** final test
pass for the validation-selected checkpoint. Candidate fits never access test
imagery or test scores. Selection and checkpoint hashes are recorded first.
The earlier runner185 remains unchanged for its active profiling queue; do
not use its train mode as a learning-rate-search loop, since it scores test
at the end of every invocation.

Policy, fixed before comparative results:

| Choice | Convention |
|---|---|
| Comparison | Each named task against its own same-input compact U-Net and pixel-linear control; not a single all-model ranking |
| Tuning allowance | Three rates per learner, with equal epoch ceilings, label subsets, seeds and selected task batch size |
| Native rates | Author/reference-centered `[lr/5, lr, 5lr]`: TerraMind2e-5, Galileo1e-3, Prithvi5e-5, Copernicus1e-3 |
| Scratch rates | `[1e-4, 1e-3, 1e-2]`; do not force scratch models to use tiny pretrained learning rates |
| Selection | Whole validation-event target-class IoU, best checkpoint/epoch; first candidate wins exact ties |
| Partition | Every eligible event/chip tested once; a separate whole event is validation; training excludes both |
| Label budget | Nested100/20/5% complete labeled chips within each training event, seeds42/1729/31415; all test chips retained |
| Batch/order | Same task batch size; deterministic shuffle/augmentation seed per epoch, independent of model parameter count. Training drops the final short batch; evaluation never drops records |
| Loss | TerraMind task uses Dice for all learners; Galileo/Prithvi CE. Copernicus native uses published primary CE +0.4 auxiliary CE; scratch controls use primary CE |
| Schedule | TerraMind plateau family for every learner (common `1-validation IoU` monitor); Galileo published warmup/cosine family; Prithvi cosine; Copernicus declared cosine adaptation |
| Failed trials | Record nonfinite/failed runs; never silently replace them or score test if no finite validation winner exists |
| Costs | Count all tuning trials, backbone/token preparation, failed fits and final inference; distinguish reusable feature extraction from head-only cost |

This is a **bounded tuning comparison**, not a claim of exhaustive optimization.
An endpoint winner is reported as such; no test-informed grid expansion.
Native architecture/auxiliary heads and adaptation choices differ: gains are
pipeline gains, not a clean causal attribution to encoder pretraining alone.
One validation event per fold is a limited selection sample; report per-event
outcomes and seed variability rather than treating pixels as independent.
Learning-rate budgets are practical study choices, not disciplinary thresholds.
Batch/compute scheduling still uses measured device profiles; this code does
not authorize an automatic large fitting grid.

Water-task full leave-event-out folds already cover446 chips/11events.
[Change-fold preparation196](../scripts/196_prepare_radar_change_partitions.py)
now prepares20 whole-activation folds for all5,000 radar-change records and
nested subsets. Published radar splits share all20 events; reproduction and
new-event transfer must remain separate. Partition checks establish disjoint
source events, not absence from encoder pretraining.

CPU engineering smoke fits: three1-epoch linear candidates on one5% training
subset for each of the multimodal-water and radar-change tasks. These validate
data/optimization/selection plumbing only, **without any test scoring**. They
are not the final trained comparisons. Manifests distinguish nondefault epochs.
Local receipts: `results/applied_study_v1/tuning/` and `runtime/*tuning-smoke*`.

Example (plan only; use the matching overlay and task-profile batch size):

```sh
.venvs-applied/galileo/bin/python scripts/192_tune_applied_water.py \
  --task galileo --learner native --fold Bolivia_20180215 \
  --feature-cache data/processed/limburg_applied_galileo_spatial_v1
```

## Local CEMS scoring conventions

The three selected AOIs cover one July2021 regional event, not independent
national samples. The selected-source DBFs, actual post-image footprints and
crisis-layer attributes determine support. The [official vector-package manual](https://mapping.emergency.copernicus.eu/about/rapid-mapping-manual/product-overview/what-is-delivered-in-a-product/vector-package/)
distinguishes crisis information from base reference layers; these are mapped
products rather than field truth.

Preparation194 produces **43 unique10m grid masks** linked to all530 local
imagery tiles. There are2,660,543 eligible mapped-comparison pixels, including
136,536 mapped-flood pixels, before per-model source/QA/common-support filtering.
These are inventory counts, not independent observations or accuracy results.

1. Assessed support is selected post-image footprint intersect AOI, minus the
   same source's Not Analysed/no-data polygons. Eschweiler has37 post-image Not
   Analysed polygons; Venlo has one no-data polygon. AOI extent alone is not
   an assessed-pixel mask.
2. Only `event_type=5-Flood`, `notation=Flooded area` supplies instantaneous
   mapped-flood positives. DE source layers also contain **319 Eschweiler and
   111 Wassenberg Flood trace polygons**. Trace-only areas are unknown for
   current-water comparison, not dry or current-water positives. Traces remain
   available in source products for historical affected-area interpretation.
   Landslide/mudflow polygons are not flood labels.
3. Exclude mapped hydrography polygons and rasterized stream lines from the
   shared flood proxy. They are not a complete permanent-water inventory.
   A water model's positive there would not demonstrate new inundation.
4. Remaining assessed pixels outside mapped flood are **mapped non-flood**,
   not independently confirmed dry. Quantitative results are explicitly
   reference-map agreement. Binary surface-water and native3-class flood
   outputs retain their task identities; within this restricted common mask,
   compare water-positive versus native class2 as mapped-flood candidates.
   Do not claim the water model learned permanent-versus-new water separation.
5. Polygon rasterization uses pixel centers; stream exclusion uses all-touched
   pixels. Retain original source scale, map limitations and10m boundary effects.
6. Score exact aligned grids on the intersection of every compared model's
   valid input/prediction mask. Optical QA60 excludes known cloud/cirrus when
   supplied; it does not certify cloud-shadow-free pixels. Unknown inputs and
   labels remain unknown. A missing acquisition is not a dry map.
7. Pre-event radar is conditioning input, not a post-event-reference test case. The scene-pair inventory marks it accordingly. Use an AOI/acquisition case with nonoverlapping grids. Never pool different
   acquisition times, overlapping scene tiles or repeated maps as additional
   independent events. Scorer195 rejects grid/CRS mismatch and within-case
   overlap. Preserve actual signed reference-time offsets; the nearest image
   is a qualified comparison, not a simultaneous observation.
8. Venlo's reference uses Sentinel-1, including the matching held acquisition;
   radar agreement shares source information. DE uses Pleiades July18 and
   held images differ in time/sensor. Neither provides a country ranking,
   independent operator evaluation or verified warning benefit.

[Preparation194](../scripts/194_prepare_local_reference_scoring.py),
[scorer195](../scripts/195_score_local_reference_agreement.py), and
[mask/metric helpers](../src/applied_local_reference.py) make these conventions
executable. Local outputs and input hashes are in
`results/applied_study_v1/local_references/scoring/`. The prediction manifest
requires explicit common-case identities, task semantics, source validity,
time offsets and reference-dependence descriptions. No local predictions have
been scored yet.

## Next execution

Let ongoing Presto/Galileo extraction and the existing waiting profiles finish.
Profile Copernicus on the available intended device, then allocate the matched
fitting runs using actual cost and the50GiB reserve. Apply trained maps to local
cases with these conventions, inspect errors and update the living brief only
when those outcomes exist. No new data request or dissertation question follows
from these preparation fixes.

Validation:32 tests passed; all new Python files passed Ruff. The20 original extraction source hashes and3 waiting-profile source hashes remain unchanged. About93GiB free remains; the50GiB reserve is unchanged.
