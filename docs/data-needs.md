# Limburg data needs — applied task refinement

Updated 31 October 2026. This table is **per proposed task**, not a new blanket requirement for the dissertation. Existing discharge analyses have their required inputs; no fresh gauge/weather request is necessary to finish them. [Task configurations](limburg-applied-task-configurations-2026-10-31.md), [registry](../config/limburg_applied_tasks_v1.json).

**1 November implementation plan:** [research, acquisition and Azure offloading](limburg-applied-study-plan-2026-11-01.md). Approximately 61.7 GiB is free, leaving only 11.7 GiB above the existing reserve. Verify/offload inactive Limburg products before full staging; keep a canonical shared labeled dataset and rotate larger task inputs. No transfer, deletion or full download was performed by creating the plan.

## Needed for the identified mapping tasks

| Data | Held status | Why/where needed | Acquisition path and volume |
|---|---|---|---|
| Sen1Floods11 v1.1 hand labels, VV/VH, 13-band S2L1C | **Partial:** public listings, metadata/splits and one aligned chip triplet only; full set not downloaded | TerraMind Tiny multimodal water mapping; Galileo radar probe; candidate optical comparison | [Author dataset](https://github.com/cloudtostreet/Sen1Floods11); public `gs://sen1floods11/v1.1/data/flood_events/HandLabeled/`. Verified listings: 446 files each. Labels 2,553,880 B; S1 729,495,935 B; S2 1,018,607,837 B. Core total **1,750,657,652 B = 1.63 GiB** as stored, excluding metadata/cache |
| Dataset split/event identities and imagery dates | **Metadata/split files acquired**, full partition audit pending | Train/validation/test separation, label-efficiency subsets, independent-event resampling and S1/S2 date differences | Same public bucket plus [event documentation](https://github.com/cloudtostreet/Sen1Floods11). Preserve parent scene/event IDs; author split reproduction does not itself prove held-event transfer |
| Flood-S1 / Kuro Siwo subset | **Not held** | Copernicus-FM radar change task and any truly matched radar comparator | [Official subset](https://huggingface.co/datasets/wangyi111/Copernicus-Bench/tree/main/l3_flood_s1). API confirms ZIP **6,025,208,085 B = 5.61 GiB compressed**; expanded bytes not established. LFS SHA256 recorded in registry. Download the flood subset, not all Copernicus-Bench |
| Local individual event/pre-event acquisitions | **Catalogue leads held; exact task-ready pairs not verified** | Applied NL/DE transfer and acquisition-time water maps | Existing catalogue has July 10–20 2021 S1 scenes on nine dates, S2 L1C/L2A on July 11/14/16/19. These are catalogue counts/footprints, not proof of clear coverage or local pixels. Export individual GEE Sentinel-1/2 acquisitions with acquisition/orbit/angle/validity metadata; do not substitute weekly composites |
| Independent local mapped-water/inundation references and surveyed AOI/validity footprints | **Not verified as usable spatial labels** | Quantitative local mapping accuracy | Open [EMSR520 Netherlands/Meuse](https://mapping.emergency.copernicus.eu/activations/EMSR520/) and [EMSR517 western Germany](https://mapping.emergency.copernicus.eu/activations/EMSR517/). Check geometry, acquisition time, source sensor, confidence, unknown areas and reference dependence. Individual download links/products still need retrieval. July2021-only evidence would be a case application, not broad multi-event validation |
| Exact model-compatible normalizers, masks and task heads | **Backbone weights and source examples held; trained new heads absent** | Every spatial task | Train head on the task labels. A catchment feature table or pretrained backbone alone cannot produce a validated water map. No new backbone download is necessary for TerraMind Tiny, Galileo Nano or Copernicus-FM base |

## Conditional additions, not required for binary water mapping

| Data | Status/use | When to obtain |
|---|---|---|
| Permanent-water reference and/or valid pre-event water observations | Sen1Floods11 JRCWaterHand public listing: 446 objects, **515,103 B**; not downloaded. Local JRC/open pre-event data require date/support checking | Needed to distinguish event water from persistent water **if the chosen target requires it**. JRC is a reference proxy, not independent flood truth; permanent-water masks must not erase genuine expansion |
| Additional independently mapped flood events | Not yet inventoried | Useful for local event generalization beyond July 2021; search open products first. Do not generate labels from gauge p99/H3 or model predictions |
| GEOID-Flood event/AOI inventory | Newly identified open CEMS-derived benchmark; local overlap not checked | Inspect metadata as an additional reference/product lead before pulling imagery. Its full global archive is not required. [Primary record](https://arxiv.org/abs/2608.02315) |
| Urban/vegetation/terrain or obstruction masks | Catchments/DEM and some surface descriptors held; no complete classification audit | Helpful for explaining errors when maps/labels permit; not mandatory to start binary mapping |
| Full weak-label or new global benchmark collections | Not held | Only if selected label-efficiency/transfer work needs them. Do not download all 4,385 weakly labeled chips or a new global archive automatically |
| Feed delivery/outage logs and actual operational action records | Not held; previous drafts remain for Brian | Relevant only to realism of the older simulated monitoring-loss analysis, not an entry condition for spatial mapping or cost/accuracy work |
| New discharge/rainfall/soil/snow | Existing river/rainfall archives and **204/204 soil/snow months held** | No new acquisition needed for current discharge work. Soil/snow is a prepared supporting control, not a new requirement for mapping |

## Acquisition and independence cautions

The CEMS documented public activation-metadata API returned HTTP403 for EMSR517/520 during this pass; normal public activation pages remain accessible. This is an unresolved retrieval route, not evidence the reference products are absent or that an email request is now compulsory. No provider request was sent or added.

Our local register has 15 mixed threshold/documentary records, not pixel labels. Gauge threshold crossings do not identify flooded area. The EMSR520 page records activation at 15 July 2021 23:57 and product delivery on 17 July; acquisition time must be checked separately. A map made using the same satellite acquisition as a candidate model can be an operational comparison/reference, but is not automatically independent ground truth. Reference provenance must remain visible.

## Storage and downloads

No full dataset download or new training was launched during this review. Only small metadata, splits, author config and a 1.54-MiB aligned sample triplet were fetched. The existing **50-GiB free-space reserve** remains. Full Sen1Floods11 hand data is modest enough for a local pull after allowing for processing/head checkpoints. Kuro Siwo's ZIP plus expanded/cache volume must be budgeted before acquisition; expanded size is unknown, and the ZIP should not be counted as the full working footprint. Keep other chapters' data untouched.
