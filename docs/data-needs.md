# Limburg data needs — applied task refinement

Updated 1 November 2026 after acquisition. This table is **per proposed task**, not a new blanket requirement for the dissertation. Existing discharge analyses have their required inputs; no fresh gauge/weather request is necessary to finish them. [Task configurations](limburg-applied-task-configurations-2026-10-31.md), [registry](../config/limburg_applied_tasks_v1.json).

**1 November execution:** [verified acquisition, offloading and native checks](limburg-applied-implementation-2026-11-01.md). Offloaded55GiB of inactive Limburg source copies after hash/remote/restore verification. About95GiB remains free after acquiring the datasets below. Keep the canonical shared labeled dataset and 50-GiB reserve; no other chapter's data were touched.

## Needed for the identified mapping tasks

| Data | Held status | Why/where needed | Acquisition path and volume |
|---|---|---|---|
| Sen1Floods11 v1.1 hand labels, VV/VH, 13-band S2L1C | **Complete:** 446 aligned triplets, source MD5/size and SHA256 checked; every raster audited | TerraMind Tiny multimodal water mapping; Galileo radar probe; optical Tiny adaptation | [Author dataset](https://github.com/cloudtostreet/Sen1Floods11); canonical `data/raw/limburg_applied_tasks/sen1floods11`. Core **1,750,657,652 B = 1.63 GiB**, plus tiny JRC files |
| Dataset split/event identities and imagery dates | **Complete:** 446 chips/11 source events; published partitions audited; full leave-event-out rows and nested label budgets prepared | Train/validation/test separation, label-efficiency subsets, independent-event resampling and S1/S2 date differences | Ten events cross published train/test. Grouped evaluation tests every chip once. Reduced budgets select chips within training events, not fewer independent events |
| Flood-S1 / Kuro Siwo subset | **Complete acquisition/audit:** 5,000 records; published splits3000/1000/1000 share20 events | Copernicus-FM radar change task and matched radar comparator | [Official subset](https://huggingface.co/datasets/wangyi111/Copernicus-Bench/tree/main/l3_flood_s1). ZIP **5.61 GiB**, expanded **7.06 GiB**; Azure source readback verified. Preserve MNA, target ignore3 and source nodata0. Held-event transfer partitions still to prepare |
| Local individual event/pre-event acquisitions | **Acquired:** 530 tiles, 508,121,241 B, all Azure-readback verified; full pixel/date/orbit audit | Applied NL/DE cases and acquisition-time maps | Individual GEE S1 dB and13-band S2 L1C for Venlo/Eschweiler/Wassenberg; nearest same-orbit pre-window radar dates. 54 AOI/acquisition records;19 empty tiles retained as unknown. QA60 is not a complete cloud/shadow audit; coarse bands retain their native information scale |
| Independent local mapped-water/inundation references and assessed AOI/validity | **24 public vector packages held; quantitative label support remains to reconcile** | Quantitative local mapping accuracy, where supported | [EMSR520](https://mapping.emergency.copernicus.eu/activations/EMSR520/)/[EMSR517](https://mapping.emergency.copernicus.eu/activations/EMSR517/). Venlo sourceS1 July16; DE AOIs sourcePleiades July18. Preserve actual time offsets. Flood polygons are not automatically complete surface-water/dry labels. July2021-only evidence remains a case application |
| Exact model-compatible normalizers, masks and task heads | **Three native spatial CPU checks passed; heads untrained. Copernicus runtime portability unresolved** | Every spatial task | TerraMind/Galileo/Prithvi strict weight checks and real forward/backward passed. Waiting MPS/full-epoch profiling precedes comparative fitting. Copernicus native MMSegmentation import requires compiled `mmcv._ext`; passing `pip check` does not establish readiness. No further backbone download needed |

## Conditional additions, not required for binary water mapping

| Data | Status/use | When to obtain |
|---|---|---|
| Permanent-water reference and/or valid pre-event water observations | **All446 Sen1 JRC files acquired**, **515,103 B**. Local pre-event radar acquired; reference target/support still needs checking | Needed to distinguish event water from persistent water **if the chosen target requires it**. JRC is a proxy, not independent flood truth; do not erase genuine expansion |
| Additional independently mapped flood events | Not yet inventoried | Useful for local event generalization beyond July 2021; search open products first. Do not generate labels from gauge p99/H3 or model predictions |
| GEOID-Flood event/AOI inventory | **Main/held-out catalogs, shard index and README acquired; local activation subsets prepared** | EMSR517/520 entries supply scene/product leads, not another independent flood. Full global archive not pulled. [Primary record](https://arxiv.org/abs/2608.02315) |
| Urban/vegetation/terrain or obstruction masks | Catchments/DEM and some surface descriptors held; no complete classification audit | Helpful for explaining errors when maps/labels permit; not mandatory to start binary mapping |
| Full weak-label or new global benchmark collections | Not held | Only if selected label-efficiency/transfer work needs them. Do not download all 4,385 weakly labeled chips or a new global archive automatically |
| Feed delivery/outage logs and actual operational action records | Not held; previous drafts remain for Brian | Relevant only to realism of the older simulated monitoring-loss analysis, not an entry condition for spatial mapping or cost/accuracy work |
| New discharge/rainfall/soil/snow | Existing river/rainfall archives and **204/204 soil/snow months held** | No new acquisition needed for current discharge work. Soil/snow is a prepared supporting control, not a new requirement for mapping |

## Acquisition and independence cautions

The earlier public metadata API returned HTTP403. The ordinary public activation pages exposed working direct vector links; all24 listed packages are now retrieved. No provider request was sent or added. Not every EMSR517 AOI is in the Meuse basin; footprint layers are not independent truth events.

Our local register has 15 mixed threshold/documentary records, not pixel labels. Gauge threshold crossings do not identify flooded area. The EMSR520 page records activation at 15 July 2021 23:57 and product delivery on 17 July; acquisition time must be checked separately. A map made using the same satellite acquisition as a candidate model can be an operational comparison/reference, but is not automatically independent ground truth. Reference provenance must remain visible.

## Storage and downloads

Full benchmark and local imagery acquisitions above are complete. The radar ZIP and local acquisition/receipt pairs have verified private Azure copies; source recovery ledgers remain local and remotely preserved. The existing **50-GiB free-space reserve** remains. Native engineering checks are not comparative training/results. Rotate later caches/checkpoints only after verification; keep other chapters' data untouched. [Execution and restore instructions](limburg-applied-implementation-2026-11-01.md).
