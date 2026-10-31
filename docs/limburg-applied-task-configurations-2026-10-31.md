# Applied task configurations and chapter review

31 October 2026. Internal research/methods note, not dissertation prose. Brian requested concrete task configurations, another whole-chapter pass and identification of additional data. No existing model result, label or active worker was changed. This note refines the direction; it does not report new model performance.

## Main recommendation

Test **spatial water/flood assessment in the models' documented task interfaces**, including accuracy, transfer, label requirements and computing cost. Retain the discharge experiments as evidence about the more indirect hydrological application. Do not turn every encoder into another next-day discharge correction or require a missing feed/agency decision as justification.

Working question: **Where can satellite AI improve assessment of high water and flooding, and at what data and computing cost?**

The immediate, concrete empirical task is narrower: how accurately and efficiently can the supported models map water or event-related water from real acquisitions, and how does that hold across events/locations? A connection to subsequent discharge is a separate extension, not required to validate a useful map. This broadens the earlier scarcity-only RQ and changes the output being tested; it is a substantive extension, not a relabeling of old results.

The machine-readable [task registry](../config/limburg_applied_tasks_v1.json) identifies the exact held source contracts, hashes, inputs, heads, labels, comparison arms and remaining setup. These are **identified configurations, not launched or fully runtime-validated training jobs**.

## 1. TerraMind Tiny: the most concrete first task

The held author file `terramind/configs/terramind_v1_tiny_sen1floods11.yaml` already specifies this exact model size. [Author config](https://github.com/IBM/terramind/blob/main/configs/terramind_v1_tiny_sen1floods11.yaml).

- **Task/target:** binary surface-water segmentation on Sen1Floods11 hand labels. Values: -1 unknown, 0 non-water, 1 water. These labels include permanent water; do not call every positive pixel new inundation.
- **Inputs:** paired VV/VH Sentinel-1 GRD in dB and 13-band Sentinel-2 L1C, using the source modality-specific standardization. Not our ten-band L2A weekly composite route.
- **Architecture:** pretrained `terramind_v1_tiny`, frozen backbone; modality merge mean; intermediate layers 2/5/8/11; spatial neck and UNetDecoder with channels 256/128/64/32. Train the decoder; two output classes, Dice loss, ignore -1.
- **Author reference settings:** seed 42, batch 8, at most 100 epochs, AdamW learning rate 2e-5. Those are a reproducible starting configuration, not a runtime estimate or instruction to reserve a GPU. Profile precision/batch/device compatibility before the actual run; MPS cannot simply be assumed to support a CUDA-style mixed-precision recipe.
- **Useful comparison:** a same-input compact supervised U-Net and transparent spectral/radar feature baseline. Report accuracy versus label amount and total cost, not only a test-set mean. Claiming an isolated pretraining effect would need an appropriate architecture/training control; it is not inferred from beating a differently shaped U-Net.
- **Next setup:** canonical source folders are `S1Hand`/`S2Hand`; the author config names staged `S1GRDHand`/`S2L1CHand`. Explicitly map paths without altering pixels/labels. Metadata carries different S1/S2 dates; retain that alignment uncertainty.

This is an author-supported **frozen encoder + trained spatial decoder** test. It is different from our frozen catchment features + discharge-residual head.

## 2. Copernicus-FM: native radar change detection

Held sources identify `copernicusfm_cd` + `cobench_flood_s1`; see the [official benchmark](https://github.com/zhu-xlab/Copernicus-FM/tree/main/Copernicus-Bench).

- **Task/target:** three-class Flood-S1/Kuro Siwo benchmark, ignore class 3. Class-value meanings must be checked against the downloaded benchmark, not guessed from the task title. Do not compare its class scores directly with binary Sen1Floods11 water scores.
- **Inputs:** one pre-event and one event-date VV/VH pair, 224px chips; source loader uses linear radar intensity clipped to [0,0.15]. Our held dB weekly composites are not a drop-in replacement. Each date has lon/lat, day since 1970 and token area 0.0256 km².
- **Architecture:** held pretrained base encoder, frozen; multiscale post-minus-pre features, Feature2Pyramid, UPerHead and FCN auxiliary head. Cross-entropy plus 0.4 auxiliary loss.
- **Author reference settings:** batch 16, 50 epochs, learning rate .001. Source model/decoder/normalization and their costs remain part of the comparison.
- **Useful comparison:** matched raw SAR change and a supervised spatial predictor, on exactly the same acquisitions and valid target footprint.
- **Source details requiring adaptation/checking:** loader reads an MNA validity raster but does not return it; verify whether target class 3 already encodes all invalidity. It defaults a missing target to an all-zero mask; our adapter must retain unknown targets instead. The declared pre/post standard deviations are asymmetric; preserve an exact reproduction record and resolve the source convention rather than silently normalize differently. The stack uses mmcv/mmseg and SyncBN; Mac single-device compatibility needs an isolated environment/forward check. These issues concern implementation validity, not a blanket stop on other tasks.

This route tests change at an observed acquisition, not a forecast of the flood before that acquisition.

## 3. Galileo Nano: a compact native radar segmentation probe

Held `galileo/src/eval/datasets/configs/sen1floods11.json` and `eval.py` specify a single-time VV/VH binary segmentation task with a frozen spatial representation and linear-probe evaluation. [Official implementation](https://github.com/nasaharvest/galileo).

- **Task/input:** Sen1Floods11 water/non-water, S1 only, dB normalization, 64×64 subpatches. Same underlying source data as task 1, but a different modality/context configuration. The Nano wrapper must be explicitly checked; results for larger Galileo models do not establish Nano performance.
- **Readout:** spatial linear segmentation probe. The author code includes full/20%/5%/1% training partitions and five LP runs; these are useful precedents for label-efficiency work, not an automatic mandate to run every sweep.
- **Applied correction:** published preprocessing retains only subpatches with positive water labels. Reproduce that condition separately if reproducing the paper; **retain valid dry subpatches for the applied evaluation**, so false positives over ordinary land are measured. Keep parent scenes/event identities when splitting and resampling. Derived patches are not independent floods.
- **Useful comparison:** same-input radar feature classifier and compact spatial model. Relative to fused TerraMind, compare shared radar-only variants before attributing differences to architecture or model size. Do not credit fewer inputs as equal-information superiority.

This is a concrete compact-model candidate for accuracy/resource trade-offs. Its actual end-to-end efficiency remains unmeasured.

## 4. Prithvi Tiny TL: promising compact alternative, needs explicit adaptation

The [official Sen1Floods11 example](https://github.com/NASA-IMPACT/Prithvi-EO-2.0/blob/main/configs/sen1floods11.yaml) uses six optical bands and a spatial decoder, but its listed backbones are larger variants. The [exact Tiny card](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-tiny-TL) identifies a pretrained 5M-parameter model.

Do not present the example as a ready-made Tiny flood checkpoint. It contains `backbone_pretrained: false`, a placeholder model name, and layer-selection examples for other backbones. An actual pretrained Tiny test must load the held weights, verify Tiny depth/token indices and a compatible neck/decoder, and use a supported single-frame/metadata route without fabricating time steps. Its six-band S2L1C adapter differs from the HLS pretraining product and the existing held HLS discharge features. Official resizing from 512 to 224 changes spatial detail; compare on a common evaluation grid. This is a candidate after the direct configurations above, not another prerequisite.

## Where the other encoders fit

The [all-model source review](limburg-applied-model-use-review-2026-10-31.md) remains the role map. CROMA/DOFA have change-detection wrappers in the held Copernicus-Bench code; they are possible matched radar comparators after version/normalization checks. AnySat's dense output and OlmoEarth's spatial heads support mapping, but need their actual task/readout contracts; their current catchment summaries are insufficient. Presto and SatMAE remain surface-representation candidates, not required additional subprojects. AlphaEarth remains landscape/transfer context, TTM a time-series model. No new model family or ten-model × every-task sweep is necessary.

## What the whole-chapter pass changes

| Finding in current chapter | Refinement |
|---|---|
| Live framing repeatedly narrows usefulness to missing Q and 24h discharge improvement | Keep those results; broaden the proposed applied task to spatial assessment and accuracy/data/resource trade-offs |
| Several valid native representations are reduced to catchment vectors | Use spatial outputs/heads for a spatial task; old pooled caches cannot restore pixel localization |
| Antecedent composites and event maps have different temporal meaning | Match individual acquisitions to reference times; never use during/after-event imagery as an earlier forecast input |
| Threshold episodes and documentary impacts are mixed in the 15-record local register | Keep them as event/context evidence; acquire separate spatial labels for spatial scores |
| Strong raw controls exist, but their task is discharge | Retain them for discharge; use matched raw imagery/spatial baselines for mapping |
| Runtime records mix hardware, resumptions and competing workers | Preserve engineering logs; measure fair cold-start/training/inference/peak-memory costs separately |
| Author examples include selected positive patches or latent unknown-mask handling | Disclose reproduction populations and evaluate all valid applied terrain; keep unknown separate from dry |
| A mapping success could become another automatic push toward next-day Q | Validate the map first; downstream hydrological value is optional additional evidence, not a required rescue |
| README/old plan text uses multiple historical “current” labels | Add one dated current-status pointer; preserve dated protocols/results and active source hashes |

## Grounding beyond an off-the-shelf benchmark

Published data first establishes intended-task setup and supports supervised evaluation. The chapter's local application should then inspect all eligible acquisitions/reference areas in the held NL/DE region, including Meuse floodplain where useful; the eight small tributaries do not have to bound every mapping AOI. Retain failures over narrow channels, urban areas, vegetation/cloud/shadow and fast-changing water where supported by observations. Do not infer those mechanisms merely from low aggregate accuracy.

The empirical contribution could be local transfer, label efficiency, a useful accuracy–resource trade-off, or a diagnosed limit between image mapping and river assessment. A generic published-split leaderboard alone is weak grounding. New accuracy/efficiency claims require measured comparisons; a nonsignificant score difference is not equivalence. No operator interview, new hydraulic solver or operational deployment is required to make this an applied study.

### Literature check: precedents and the remaining question

- **Kuro Siwo** (NeurIPS 2024, peer reviewed) supplies manually annotated multi-temporal radar observations across 43 flood events and a flood-mapping benchmark. It supports the pre/event radar task, not a claim that our local study is the first foundation-model flood application. [Primary paper](https://proceedings.neurips.cc/paper_files/paper/2024/hash/43612b0662cb6a4986edf859fd6ebafe-Abstract-Datasets_and_Benchmarks_Track.html).
- **GEOID-Flood** (2026 arXiv record; accepted ECCV workshop according to that record) already compares foundation and conventional encoders across single-image, multi-temporal and multimodal flood segmentation. Its reported improvement is modest. Therefore, "foundation models can map floods" is not our gap. Its CEMS-derived event inventory is a useful additional **metadata/reference lead**, particularly for local overlap; the complete archive is not another required download. Reference dependence still needs checking. [Primary record](https://arxiv.org/abs/2608.02315).
- **Cross-Architecture Foundation-Model Distillation for Edge Flood Segmentation** (September 2026 preprint, submitted to JSTARS) demonstrates an accuracy/annotation/compute trade-off using a Prithvi teacher and compact student. Importantly, a simple MNDWI threshold is competitive on two of its external benchmarks. This strengthens the case for real same-input spectral/radar controls and measured cost, while showing that lightweight flood AI is also an established research direction. Distillation is **not added** to our task list. [Primary record](https://arxiv.org/abs/2609.20441).

The defensible local question is which supported representation/readout is useful on the observable NL/DE flood settings, under explicit acquisition timing, label support and resource constraints. Whether available local references support a substantial comparative result remains unresolved. If only one well-mapped event is available, describe it as a local case application with benchmark support; do not claim broad local transfer. Mapping should supply spatial evidence relevant to the basin's flood assessment, rather than become a disconnected generic leaderboard or require a new hydrological model to justify itself. Bibliographic records are retained in [the accompanying BibTeX file](limburg-applied-task-literature-2026-10-31.bib); no external library synchronization is claimed.

## Immediate sequence

1. Use [data needs](data-needs.md) to acquire the labeled core, splits and metadata, then individual local acquisitions/reference products. Start with task 1 or 3 for the simplest supported native setup; task 2 has a separate preprocessing/software path.
2. Validate masks/units/georeferencing, grouped partitions and one model forward/backward pass in isolation; record runtime/memory. This is an engineering check, not the scientific sample.
3. Freeze one matched mapping comparison and its label/transfer/resource reporting before full fitting; use the full eligible labeled evaluation, with event-level uncertainty and all-valid coverage.
4. Finish/review the current Presto/Galileo discharge work separately. Do not automatically submit the four older supporting discharge sweeps while this new direction is being honed; their preparation remains available and no existing running task is interrupted.

## Verification performed now

Eleven held/downloaded source contracts are hashed in the registry. `scripts/176_audit_applied_task_readiness.py` checks native configuration fields and the acquired small raster sample without importing/running models. The single aligned Bolivia sample has 512×512 label/S1/S2 rasters, 1/2/13 bands and labels -1/0/1; cloud MD5 and local SHA256 are recorded. Source data listings, metadata and split files are retained under `docs/reviews/applied-task-config-2026-10-31/`. One sample verifies plumbing only; full dataset integrity, local AOI overlap and model training remain unverified.
