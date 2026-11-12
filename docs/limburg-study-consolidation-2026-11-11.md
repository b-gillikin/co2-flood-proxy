# Limburg mapping study: validity resolution and consolidated findings

11 November 2026. Internal research/writing aid for Brian, not dissertation prose. Supersedes the interpretation of unrestricted results in the living brief; original protocols, scores, images and dated reviews remain preserved. The accepted question, three mapping pipelines, trained states and geographic evidence roles are unchanged. This work audits metadata and reaggregates existing predictions; no new training, imagery retrieval, reference selector or agency request.

## What was resolved

### 1. Target semantics

| Evidence | Coding and construction | What it can establish |
| --- | --- | --- |
| Source Flood-S1/Kuro labels | Author legend: 0 no water, 1 permanent water, 2 flood, 3 outside AOI. The executed adapter maps 3, invalid radar and invalid MNA to ignored support. Copernicus and U-Net retain the same three-class target. | Source-supervised event-flood designation, not an independent per-pixel history at an arbitrary replacement date |
| External released label | 0 background, 1 permanent water, 2 flood, 255 unknown. CEMS flood delineation plus a derived permanent-water layer; the paper describes an AlphaEarth-based permanent-water procedure. The pinned release/card, not paper counts, defines the executed dataset. | Agreement with the released event-flood classification; permanent water is not independently surveyed truth |
| External source-mask check | Existing floodmask/permwater reconstruction, with flood taking precedence and unknown preserved, scored on the original known support | Sensitivity to class construction; not a new manual adjudication or an independent label |
| Local CEMS proxy | Assessed mapped-flood versus mapped background, excluding hydrography/streams and trace-only areas; mapped to model classes 2/0 with unknown 255. There is no certified permanent-water target. | Local flood-map agreement and coverage; not an evaluation of local permanent-water accuracy |
| Water-union diagnostic | Combine target classes 1+2 and prediction classes 1+2; keep original unknown/validity support | Whether a change affects water recognition versus its event-flood designation; neither peak inundation nor newly inundated land since P1 |

The author Flood-S1 wrapper's plotting legend confirms the executed source class order; no numeric class-swap bug was found. `src/applied_change_task.py` retains those labels. The pinned GEOID code's paired binary evaluation explicitly calls water present at both dates 'permanent'. Our neural pipelines instead predict the three classes directly, while the physical comparator has explicit pre/post logic. A neural class-1 output is therefore a learned designation, not proof of enduring water.

The estimand is now explicit: **the effect of replacing the supplied reference on agreement with a fixed released event-flood map, conditional on the same event image, trained pipeline and scored support.** P1 does not redefine truth. We cannot score actual newly inundated area since P1 because no independently validated P1 water-state target is held. An earlier transient flood can create a temporal-baseline conflict; do not interpret every lost flood-class detection as a demonstrated loss of true water recognition.

The full paired target-construction census contains 35,670,281 composed flood pixels. Reconstructing the original masks retains all of those and adds 2,956,847 pixels designated permanent by the composed target: about 7.7% of source-mask flood support. These are owned pixel counts, not independent observations. On compatible geometry, Copernicus's P1−P0 change is −.087 under the composed label and −.090 under mask reconstruction; under the additional timing check, −.022 and −.025. The interpretation is not driven solely by that class-construction choice. No target was altered in the original results.

### 2. Acquisition geometry

Checked every product named in the full 1,301-tile catalogue and all 913 actual triplet receipts. Reused cached CDSE metadata and fetched 90 missing product records; all required external product metadata are now available. Earth Engine independently returned metadata for all 18 distinct acquisitions used in the 167 local records. New local P1 geometry was not inferred from its selection rule.

Compatibility requires matching relative orbit, ascending/descending pass, IW mode, VV/VH polarization and look direction against the event/post image. Same constellation platform is reported separately; cross-platform matching tracks are permitted. The metadata check does not establish identical local incidence angles, terrain response or effective resolution.

All 913 external P0/P1 references match each other. However, 466 do not match the post image's relative orbit and/or pass. This inherited reference/event pairing is consequential: matching P1 to P0 did not establish event-image compatibility. All 167 local records match their post geometry, including the 35 updated-reference records.

| External paired population | Tiles | Activations / conservative blocks | Owned scored pixels |
| --- | ---: | ---: | ---: |
| Original full paired census | 913 | 9 / 8 | 610,524,945 |
| Both references compatible with event geometry | 447 | 8 / 7 | 286,951,030 |
| Compatible plus listed radar/label difference <=24h | 385 | 7 / 6 | 258,134,714 |

Greece has no compatible paired tiles; its striking original result remains a full-catalogue stress-test case, not evidence for matched-geometry performance. Other activations lose some but not all tiles. The 24h restriction is an existing descriptive sensitivity, not an assertion that all shorter offsets are valid or longer offsets invalid.

## Corrected results hierarchy

The full released-cohort results remain intact. Use the geometry-compatible estimate to describe the intended matched-acquisition application, and present the original catalogue result as a broader input-policy stress test. Declare that the validity restriction was applied after results, using metadata rather than favorable scores. Do not describe it as an untouched confirmatory evaluation.

Each restriction retains the original prediction-blind overlap ownership; excluded owners' overlap is not reassigned to newly available predictions. Therefore this is an explicitly restricted, equally scored support, not a claim to have remapped every compatible scene footprint. All pipelines share the same support. Aggregation remains counts within activation, seed averaging, conservative episode blocks, 9,999 paired bootstrap draws and leave-one-block-out results.

| Population | Copernicus P0 IoU | U-Net P0 IoU | Copernicus−U-Net, interval | Copernicus P1−P0, interval |
| --- | ---: | ---: | --- | --- |
| Full paired | .396 | .380 | +.016 [−.035, .082] | −.121 [−.242, −.018] |
| Compatible geometry | .452 | .445 | +.008 [−.023, .037] | −.087 [−.224, .001] |
| Compatible + listed timing <=24h | .441 | .438 | +.002 [−.051, .044] | −.022 [−.063, .008] |

These are event-flood IoU differences, not percentage-point classification accuracy. The intervals reflect few blocks and are not equivalence tests. Cohort changes accompany the restrictions: attenuation does not identify geometry or timing as the sole causal explanation for the original average.

Compatible-geometry P0/P1 flood IoU is .452/.365 for Copernicus, .445/.372 for U-Net and .341/.280 for the physical rule. With the timing restriction it is .441/.418, .438/.408 and .324/.305. Water-union agreement for Copernicus is .505/.538 on compatible geometry and .415/.457 with the timing restriction. Those explanatory endpoints use the same fixed composed labels and are not independent water truth.

The source-mask alternative and other existing validity/boundary conventions are retained in the numerical record. Every original all-cohort contrast and its bootstrap interval is exactly reproduced before reporting the added restrictions. No source threshold, checkpoint, seed, test label or original score was replaced.

## What remains of the event explanation

The full transition census remains useful: some flood-designated pixels switch to class 1 while remaining recognized as water; others switch to background. March Italy is an improvement counterexample. But the most dramatic Greece result is outside matching geometry, and some Ecuador examples have substantial reference-time offsets. These qualifications must accompany their maps, not appear only in an appendix.

Within compatible geometry and the listed <=24h subset, Copernicus event flood IoU P0→P1 includes Mozambique .779→.761, Spain/Portugal .481→.402, Portugal .615→.460, Colombia .409→.389, France .480→.490, Ecuador .015→.000, and March Italy .412→.438. The Ecuador subset is not interchangeable with the earlier high-IoU Babahoyo driver. Preserve all event/support tables and avoid explaining the restricted aggregate with an excluded dramatic tile.

All local acquisitions pass geometry; the local July 2021 limitations concern target timing/semantics and coverage. They remain one Dutch/German flood episode, not an NL–DE country-effect study. René/Jens data support timing/context, not flood-pixel truth.

## Resource account

Final source fitting logs account for every completed epoch: approximately 2.03 hours summed across the three Copernicus refits and 1.27 hours across the three U-Net refits. Those are logged epoch durations, not total study costs; source development/tuning, feature preparation, startup and analyst work are additional.

The external controller's execution windows are about 10.47 hours for Copernicus and 4.97 hours for U-Net. These include reading, archival and other execution overhead under the actual laptop conditions; they are not isolated inference benchmarks or operational service latency. The 46 previously readback-verified prediction archives total 83.14 GiB. No claim of cheaper equal-quality deployment or measured annotation savings follows. The detailed cost receipt explicitly marks unmeasured components rather than inventing totals.

## Consolidated scientific account

Supported: a transferred Copernicus-FM mapping pipeline is usable for evaluation against held reference maps, but has no clear average advantage over trained same-input U-Net. Reference choice can materially change event-flood designation, with heterogeneous examples of preserved water recognition, background rejection and improved precision. Applicability and interpretation require correct acquisition geometry, label semantics and acquisition/reference chronology.

Not supported: universal deterioration from newer images; a general AI advantage; proof that transient water is permanent; independent pixel-level confirmation of every event explanation; measured operator or warning benefit; or a new discovery that SAR references matter. After validity checks, the average deterioration is weaker and uncertain. The result is less dramatic and more defensible.

This remains one paired comparative mapping study, internationally evaluated with a Dutch/German application. No new selector, model family, weather acquisition, local hydraulic model or labelling campaign is added. The article's contribution is the bounded empirical model/information comparison and its applicability. Contribution strength is an author/supervisor judgment; these corrections do not prove acceptance or create a new significance gate.

## Main evidence set for Brian

1. Cohort, target provenance, geometry and usable-support accounting.
2. Three pipeline comparisons with uncertainty on compatible support; original full catalogue separately.
3. Paired reference effects with the existing timing/label/validity sensitivities.
4. Selected event errors linked to their own compatible support, with full event tables available.
5. July 2021 local receiving-case timeline, coverage and map agreement.
6. Transparent resource account and bounded FEWS/DRR implications.

Historical discharge/analogue results and the larger spatial programme remain development/supporting records, not additional mandatory results sections. A focused related-work comparison should distinguish this reference-policy evaluation from Hostache's selector, Tupas's time-series reference construction, and GEOID's representation/temporal/modality benchmark. None licenses a 'first' claim.

## Reproduction

Run from chapter1-co2, using the existing environments:

```sh
.venv-foundation/bin/python scripts/254_audit_chapter_validity.py --local-metadata-only
.venvs-applied/copernicus/bin/python scripts/254_audit_chapter_validity.py --fetch-metadata
.venvs-applied/copernicus/bin/python scripts/255_consolidate_chapter_validity.py
.venvs-applied/copernicus/bin/python scripts/256_record_chapter_consolidation.py
```

The first command refreshes metadata only; omit it on a cached reproduction. The second reuses CDSE caches and only retrieves missing metadata. Outputs: `results/limburg_chapter_sized_v1/validity/`. Compact tracked numbers/provenance: `docs/reviews/limburg-validity-consolidation-2026-11-11.json`. Interpretation contract: `config/limburg_chapter_interpretation_v1.json`. Original results remain at `evaluation/summary/` and `event_review/`.

Source semantics: held Copernicus author wrapper `data/raw/limburg_dynamic_model_weights/code/copernicus_fm/Copernicus-Bench/src/datasets/cobench_floods1_wrapper.py`; pinned GEOID card under the 10 November scope-audit sources; pinned GEOID `scripts/eval_flood_paired.py`; our `src/applied_change_task.py`, `src/applied_local_reference.py` and `scripts/248_run_chapter_local.py`. Published explanations: [GEOID paper](https://arxiv.org/html/2608.02315v1), [Kuro Siwo paper](https://arxiv.org/html/2311.12056). Version differences and the lack of independent per-pixel history remain explicit.
