# Next research direction: where local annotation helps transferred flood mapping

11 November 2026. Internal research proposal and first evidence inventory, not dissertation prose or a launched protocol. Brian asked to pursue another part of the November 10 ideas with stronger novelty and substantive potential. The completed mapping/reference study remains intact. No new training, model weights, bulk imagery download or annotation campaign starts from this note.

## Recommendation and practical question

Select **target-local adaptation and annotation allocation**, rather than another reference-image policy, model tournament or generic source-label reduction.

Plain-language question: **When reusing a satellite-AI flood mapper, which local areas are worth labelling, and how much does that work improve maps elsewhere in the receiving landscape?**

Working empirical RQ: At the same total local annotation budget, how do random, uncertainty-based and landscape-coverage selection change flood-map errors on spatially separate target areas, relative to unadapted transfer and a source-trained conventional neural baseline?

The uncertain proposition is not merely that more labels can improve a fit. It is whether selecting representative local conditions teaches transferable corrections that ordinary uncertainty selection misses. A model can be confidently wrong after transfer; uncertain boundary pixels are not automatically the most valuable adaptation examples. These are hypotheses, not established explanations of our current models.

## Why choose this over the other parked routes?

| Route | Judgment |
| --- | --- |
| Local adaptation and label allocation | Best next candidate: directly changes the complementary local work supplied by an agency; existing labeled imagery permits controlled simulated budgets and independent spatial evaluation |
| Second pre-event image / terrain | Strong held-data fit, but Kuro already supplies multitemporal observations and DEM; adding these alone is weak novelty and remains close to the troubled reference branch |
| Crop/patch corrections | Necessary for particular implementation claims, but correcting preprocessing is not itself a substantive chapter |
| Dense AlphaEarth normal-water prior | Already closely precedented by GEOID; requires additional dense data and independent reference handling |
| Confidence/review alone | Useful, but a generic uncertainty-error correlation is well studied; use uncertainty as an annotation comparator rather than declare a separate reliability chapter |

## Literature positioning

- ALFA (Adhikari et al., IJCAI 2025), https://ijcai.org/proceedings/2025/1057, already studies consistency-based active annotation with elevation guidance. Neither active learning nor faster annotation is an empty gap.
- Selvam et al. (2024), https://arxiv.org/html/2409.09907v1, studies parameter-efficient foundation-model adaptation. Fine-tuning/LoRA alone is not new.
- Chen et al. (2026), https://doi.org/10.1029/2025JH001145, studies event-level unlabelled adaptation for coastal inundation and explicitly calls for validation beyond those settings. Our proposed supervised local-label comparison is distinct, not a reproduction of CIM-TTDA.
- Farajpoor and Narimani (2026 preprint), https://arxiv.org/html/2610.34904, already compare compact-model accuracy, source fine-tuning fractions, event exclusion, efficiency and reliability. A further generic small-label model comparison would overlap substantially.

The contribution candidate is **how a fully counted local annotation allocation produces spatially transferable corrections under target shift**, including confident errors, negative transfer and where acquired labels fail to generalize. This combination needs a focused full-method comparison before asserting novelty. No claim that these components or their combination have never been studied; no 'first' claim. Evidence of consequential improvement is possible, not promised. Label allocation and correction transfer could also prove unhelpful.

## One bounded empirical design

Use one task-supported SAR foundation-model pipeline and one source-trained same-input U-Net, starting from valid source-only states. Preserve a physical/no-new-label reference where it answers the same target. Copernicus-FM is an initial practical candidate because its paired-SAR adapter and source states are already held, not because it won previously. Verify the local adaptation route; frozen-encoder/head adaptation is a narrower claim than full backbone fine-tuning. Do not add LoRA, full fine-tuning and several backbones by default.

Within each target domain, separate acquisition/adaptation blocks from evaluation blocks by actual ground footprint, with overlap/context buffers. All dates and duplicate views of a ground patch stay in the same block; duplicated labels cannot count as new budget. All final evaluation labels remain hidden from sampling and adaptation. This is retrospective simulated local annotation, not an actual live annotator trial.

Compare three label-allocation policies:

1. Random selection from the permitted spatial pool.
2. Source-model uncertainty selection from that same pool.
3. Coverage of distinct local landscape/appearance conditions. Prefer simple spatial and raw-SAR descriptors initially; terrain or independent hydrography only if verified and justified. Do not choose samples using hidden true flood/error labels. Any use of foundation embeddings for selection must be explicit and separated from a claim of model-neutral sampling.

Use a small nested budget curve, defined in unique native-area patches/pixels and also reported in square kilometres. Choose actual counts after the spatial-pool inventory; percentages alone obscure wildly different site budgets. Include any target labels used for tuning, stopping or calibration. Freeze adaptation settings using source pseudo-target development where feasible. Repeated annotation draws and optimization seeds remain separate sources of variation, not independent floods. Shared annotation sets support clean learner comparisons; model-specific uncertainty policies are compared as complete acquisition-plus-adaptation pipelines, not as identical-label algorithm contrasts.

Evaluate flood-class omissions/false area, IoU/precision/recall and change from the unadapted source state on exactly the same evaluation support. Report water-union diagnostics separately. Show where corrected errors lie and whether the correction transfers beyond labelled blocks. Do not require an arbitrary pass threshold or call a positive IoU difference demonstrated operator benefit. No inference of annotation hours from patch count.

## Data fit and the local limitation

Held source imagery: 5,000 Kuro/Copernicus records across 20 events, labels/validity, source states and published three-class definitions. If a source event becomes a pseudo-target, the relevant source state must exclude that event and its prohibited development labels; the final all-source checkpoint cannot be used as if unseen. Existing cross-fit states may be reusable only after exact manifest reconciliation.

Held external evidence: the full released catalogue and the corrected 447 geometry-compatible paired tiles. Existing inspection means exploratory reuse, not a pristine new external test. Regions/episodes and label acquisition timing still determine valid split units. The original geometry/target issues must not be imported as if fixed by adaptation.

Held local evidence: 167 mapped scene/grid records across 14 acquisition cases for Venlo/Eschweiler/Wassenberg, all matching geometry, within **one July 2021 flood episode**. The new `docs/reviews/limburg-local-adaptation-evidence-inventory-2026-11-11.json` enumerates all cases, known/flood pixel counts and offsets. Repeated acquisitions reuse reference maps. Some local flood support is sparse; a random budget can legitimately obtain no positive examples and that outcome must not be silently resampled away.

The held local data can potentially support **same-event spatial adaptation and transfer**, after spatial/temporal reference checking. They do not establish next-flood durability or national NL/DE differences. A later-event claim requires another temporally suitable local event/reference. Search existing CEMS/local archives and source-event identity first; do not assume a new global event proves local temporal transfer or add a distant region to make the title local. No independently verified permanent-water truth is manufactured from local hydrography.

The near-term scientific task is to inventory the unique target-label footprints and their acquisition/source dates, then form defensible spatial adaptation/test pools. This is not a new blanket gate: if temporal evidence supports only a narrower spatial estimand, report that design explicitly; if a stronger claim is chosen, acquire the evidence it actually needs.

## Policy contribution and scope

The use case is an agency deciding where to put scarce local expert effort when reusing a mapping capability. Outputs can quantify map-error reductions and transfer per counted label budget; they cannot establish organizational adoption, actual staff-hours saved, warning lead time or avoided damages. No interviews, UI, economic loss model or new forecasting study is introduced.

Keep Limburg/nearby Germany as the receiving application. Existing international events can supply source development and replication of the adaptation experiment, with that evidence role explicit. If local next-event generalization is essential, pursue a documented additional regional event rather than silently treating international results as local validation.

## Next work, before a long run

1. Build unique spatial label/support and chronology inventory; determine supported local and external target pools, with all exclusions visible.
2. Review the closest papers' complete splits, label accounting and annotation policies; settle the exact contribution and one supported adaptation route.
3. Specify fixed sampling/budgets/target splits and same-input controls; profile a complete adaptation and evaluation cycle for credible compute sizing.
4. Execute the declared full eligible study, retaining all original unadapted results and unfavorable outcomes. No new ten-encoder extraction campaign.

This is a proposed substantive next direction with initial held-data evidence, not a claim that the chapter problem is solved or that positive findings are guaranteed.

## Follow-through — 12 November: local spatial-support census

`257_inventory_local_adaptation_support.py` now inventories actual owned label support. It selects the nearest listed reference-time acquisition case per AOI by the worst absolute slice offset, ties by case ID, without consulting model scores or flood counts. Adjacent slices retain their different sensing seconds. This is a feasibility inventory, not the final adaptation/test split.

| Receiving site | Selected acquisition | Listed reference-time offset | Known owned area | Mapped flood area |
| --- | --- | ---: | ---: | ---: |
| Eschweiler | 18 July 2021 | +6.58h | 116.50 km² | 0.38 km² |
| Wassenberg | 18 July 2021 | +6.58h | 30.54 km² | 1.59 km² |
| Venlo | 16 July 2021 | 0–0.007h | 118.98 km² | 11.68 km² |

These are reference-map areas on the existing owned support, not independently surveyed flood extent. Sparse positive support and incomplete known masks differ by site. At native 32/64/128px diagnostic granularity, many image windows are only partially labelled; Wassenberg and Venlo have no fully known 128px blocks under this grid convention. That does not mean the imagery or all larger windows are unusable. It means an experiment that requires fully labelled large chips would unnecessarily discard evidence.

Use small annotation regions with larger native-resolution image context, compute supervised loss only at acquired known pixels, and keep unknown excluded. Count actual unique acquired labels as well as proposed patch area; do not silently count unknown ground as an oracle annotation. Final spatial separation must account for the larger model context, not just the small labelled region. Repeated views remain grouped by ground footprint. Diagnostic block sizes are not yet selected annotation budgets or independent n.

The design opportunity remains local annotation allocation and correction transfer. The census does not demonstrate that any selection policy or adapted model improves a map. No fitting or additional imagery acquisition has occurred. Full receipt: `docs/reviews/limburg-local-adaptation-support-2026-11-12.json`.
