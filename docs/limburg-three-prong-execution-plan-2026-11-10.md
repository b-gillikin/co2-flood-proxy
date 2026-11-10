# Execution plan: water, new inundation, and geographic transfer

10 November 2026. Internal executable-study planning, not dissertation prose. Brian requested all three prongs, the supporting extensions, acquisition needs, storage and model runtimes. **Planning only:** metadata inspected, no new bulk imagery transfer, package installation, VM or scientific fitting queue launched. This supersedes the earlier short recovery plan as the execution roadmap, while retaining its diagnostic history.

## Audited specification — 10 November 2026

Read the [design audit](reviews/limburg-three-prong-design-audit-2026-11-10.md) with this roadmap. It supplies the authoritative model/product contracts, paired contrasts, source/target separation, annotation accounting and novelty qualifications. All W/F/T/R branches remain; this is not a smaller model sweep. The former runtime envelope below is a historical planning baseline, **not a current ETA**. Independent target annotation-pool repeats and source-data expansion must be enumerated and reprofiled before scheduling the affected full runs. No bulk fitting queue is launched.

## Objective and linked questions

Working chapter question: **When satellite AI is taken to a new river landscape, what observations and local training are needed to map newly flooded land reliably?**

- **W — Observable water:** How accurately can each task-appropriate pipeline map visible surface water, including narrow features and difficult surroundings?
- **F — New inundation:** How do pre-flood reference age/stability, a second pre-flood image and terrain affect mistakes between existing water and newly inundated land?
- **T — Transfer/adaptation:** In unfamiliar landscapes, how much do unlabeled imagery, local annotations and supported adaptation improve maps relative to competent conventional pipelines with the same information?
- **R — Reliability/resource account:** Can errors/unknown coverage be recognized, and what are the complete label, preparation, computation and storage requirements?

These are distinct empirical targets within one effort. Mapping does not establish next-day discharge prediction or warning skill. Completed discharge work is retained as supporting evidence; no automatic rerun. No requirement that AI win, no fixed effect-size threshold, no interview or operational deployment prerequisite. Agency relevance is the capability and complementary resources required to reuse a model, not unmeasured adoption or avoided harm.

## Execution assumptions and existing resources

Read on10November: Apple M3 Pro,18GPU cores,12CPU cores,36GiB unified memory; approximately122GiB free after the verified historical imagery offload. Continue one MPS worker and up to two CPU workers. Reduce CPU concurrency when unified memory/I/O contention would slow or destabilize the MPS job; do not reduce the scientific population instead. The existing50GiB local reserve persists. No Azure GPU/VM plan is reactivated. Azure is existing verified storage, subject to checking current credits, account/tier/retrieval costs and allocation before bulk offload.

Held:446 Sen1Floods11 chips across11events (52entirely no-water chips),5,000 Copernicus-Bench radar-change records across20event IDs (1,303without flood pixels but **none entirely water-free**), source scenes/local references, all four model weights/code, source/tensor caches and720-job results/recovery receipts. All5,000radar records contain a second pre-event VV/VH acquisition and DEM. Presence is checked; their units, nodata and grid validity are not yet audited for use. Existing catchment-average AlphaEarth exports are not dense spatial inputs.

The radar derivative is a water-containing subset, not a complete landscape census. See the audit for whole-area dry-support evaluation and full-Kuro/source-event inventory. Fresh held counts describe existing inventory, not a new model result.

## Phase0 — Storage, data identity and independent evaluation

### Storage first, alongside metadata work

1. Inventory explicitly allowlisted inactive Limburg derived runs using the [existing offloader plan](limburg-derived-eo-offloader-plan-2026-11-04.md). Keep compact aggregates, scores, code, masks, manifests, figures and selected checkpoint receipts local. Protect current spatial tensors/weights and all other chapters.
2. Package large inactive patch caches into approximately1GiB content-addressed shards with streaming inventories. Verify every remote byte/member and a restore before retiring the exact local shard inputs. Do not equate an upload with recoverability or regeneration instructions with preserved results.
3. Aim initially to recover40–80GiB of actual local space, then maintain15–25GiB rotating input/feature working sets. This is a storage allowance, not permission to delete unique results or a scientific data cap. Shared links/APFS make directory totals different from reclaimable space.
4. Store newly acquired source shards and superseded bulky feature caches in verified Azure storage; local data staging remains resumable and bounded. Cloud download execution is not assumed available merely because Blob storage exists. Use resumable local acquisition unless a separate existing supported cloud runner is verified.
5. Plan2–5GiB of packing scratch, approximately5–15GiB of compact predictions/probabilities/checkpoints in rotation, and larger temporary feature blocks only after actual measurements. Avoid materializing every backbone's complete external-dataset cache concurrently.

### Data/evaluation identity

Create one source registry containing physical flood, CEMS activation, AOI, geometry, acquisition, orbit, label source/version/time, processing and model-pretraining overlap where documented. Match overlapping events/areas across Sen1Floods11, Kuro Siwo, WorldFloods, GEOID and local CEMS packages before defining training, meta-validation, calibration and test memberships.

**New metadata finding:** current GEOID main catalogue has10,935tiles; its named test split contains80activation IDs, validation34; separate heldout has1,301tiles/9activation IDs. Fifty main activation IDs span its provided splits; EMSR517 appears in both train/test and EMSR520 in train. These are catalogue observations, not claims of identical-pixel leakage. We must build our own event/geographic separation rather than inherit split names and assert independence. The current counts/dates differ from paper descriptions. Pin the release commit and file hashes before acquisition. Recompute area in a suitable CRS; do not trust a field called `area_m2` whose observed magnitudes resemble angular geometry areas.

Keep all eligible evaluation records in each declared task-specific census, including labeled dry tiles. The 5,000-record derivative is not a whole-landscape false-alarm census. Missing modalities/unknown reference pixels remain applicability outcomes, not dry negatives. Give cross-model matched-support contrasts plus each pipeline's complete coverage. Keep the newest external events unopened for scoring while the implementation/protocol is settled; metadata inspection does not make them untouched training examples. Development remains explicitly exploratory, without a new preregistration requirement.

## Data acquisition ledger

| Data | Purpose and action | Size / route / caveat |
|---|---|---|
| Current source imagery, labels, model assets | Reuse; verify identities, restore selected states when needed | Already held; no new model weights initially required |
| Full Kuro Siwo GRD/label/metadata source-event inventory | Recover independent source landscapes and suitable dry-area support absent from the conditioned derivative; reconcile the advertised43events with release metadata | Extra acquisition and fitting volume pending inventory; no SLC/coherence substitution, no automatic assumption that more bytes are sufficient |
| SL2 pre-event radar and DEM | Audit and register all5,000held records, compute date/orbit/validity/terrain descriptors | Already held; zero new source-download bytes |
| Galileo author reference splits, preprocessing and configs | Pin held source/weights; recover missing tiny metadata only | Normally<50MiB; no new full extraction archive |
| GEOID main validation/test plus separate heldout: GRD, pre-optical, DEM, labels and masks | External SAR/change evaluation, source-independent meta-validation where overlap allows, local-label adaptation pools | **87.01GiB** for currently listed requested shards, excluding duplicate RTC and all training shards. Public[release](https://huggingface.co/datasets/links-ads/geoid-flood),[code](https://github.com/links-ads/geoid-flood). At20/100Mbps, ideal transfer10.4/2.1h; allow roughly0.5–3days with retries/staging. |
| Matched post-event Sentinel-2 and extra pre-event Sentinel-1 | Extend optical/multimodal applicability and two-reference comparisons only where actual compatible acquisitions exist | Planning allowance10–40GiB for clipped AOIs, exact amount from catalogue. GEOID provides **pre-event optical**, not contemporaneous post-event optical. Do not relabel it as the latter. Ref-date mismatch can prevent accuracy scoring despite a successful download. |
| WorldFloods extended metadata, labels and matched external optical imagery | Independent-event optical transfer; all eligible metadata-selected evaluation cases, not favorable-image selection | Inventory metadata first; allowance5–30GiB for evaluation assets, not full training archive. [Dataset](https://doi.org/10.5281/zenodo.8153513). Exact asset sizes and event overlap pending. |
| S1S2-Water metadata, masks and compatible evaluation imagery | Ordinary-water/environmental transfer and potential additional source/reference coverage | Full current release approximately154.17GiB in six large ZIPs; metadata11.7KiB. Start with catalogue and needed evaluation assets/windows where access supports them, allowance5–25GiB. If packaging requires full ZIPs, record required transfer up to154GiB and stage remotely; do not assume selective ZIP access works. [Release](https://zenodo.org/records/11278238). |
| Dense earlier-year AlphaEarth features | Train/evaluate a normal-water prior over supported held Kuro/local AOIs with independent labels | Export/retrieve all64bands at10m for declared nonoverlapping AOI/year footprint. Full5,000×224²float32 coverage is59.8GiB before spatial deduplication/compression, an upper-envelope calculation for the held footprint, not measured transfer. Plan10–60GiB initially. Global GEOID coverage would be much larger and is not automatically included in this prior branch. |
| JRC surface-water history, land-cover/settlement overlays and missing DEM coverage | Matched normal-water reference, environment strata, terrain/representativeness | Clip to declared AOIs; allowance1–6GiB. Use cutoff-safe history for issue-time claims; full-record occurrence is retrospective. Land cover is contextual evidence, not a flood label. |
| Adaptation/annotation/uncertainty code and full-text papers | Reproduce supported methods in isolated runtimes | Typically<1GiB, excluding any separately declared checkpoint. CIM-TTDA code ZIP is19.6KiB. Obtain Ratté-Fortin et al.2026 full methods if accessible; abstract-only evidence does not supply an execution recipe. |
| UrbanSARFloods processed coherence and independent urban labels; DeepFlood vegetation references | Explicit difficult-environment extension, after checking input/head/reference compatibility | Metadata first;5–30GiB working allowance is **not a measured release size**. Use processed assets if documented; raw-SLC processing is a separate costed branch, not a hidden prerequisite. If unavailable/incompatible, report that observational limit rather than claim evaluation. |

These data releases can overlap; reconcile before summing unique acquisition. Working planning envelope for the selected non-urban acquisition is roughly120–250GiB, with larger transfer if S1S2 ZIP packaging forces it. This is **not all local disk use at once**. Maintain remote recovery and rotating local inputs. Download completeness and software compatibility are checked independently of whether a method improves accuracy.

AlphaEarth catalogue currently documents annual layers beginning2017; inspect actual available years at execution, rather than assume a2016layer or2025availability. Earlier events remain outside that branch, visible in the full applicability inventory. Event-year annual features can include post-event information. Use earlier available years for an antecedent claim, and explicitly separate retrospective mapping. GEOID's permanent-water reference is AlphaEarth-derived: it is not independent validation of our AlphaEarth prior. Use independently sourced/manual Kuro water labels or another checked reference for that branch.

## Phase1 — Paper-guided reproduction and methodological corrections

**Galileo:** reproduce held author normalization, reference split/population, patch4/readout and16-rate LP search; retain patch8 as the controlled route comparison. Separately evaluate full dry/wet support and whole-event tests. Correct readout/cache dimensions together. The training-only patch4/8 and learnability checks already pass; they do not reproduce author accuracy. Keep reference metric/class averaging separate from our equal-event target-class scores. Inspect optimization boundaries/ceilings on validation, with matched documented tuning effort for applied controls.

**Prithvi:** retain fully trainable Tiny/UPerNet; compare whole-scene224 with spatially faithful224windows or a supported flexible-size route. Derive crop georeferencing/location metadata. Every parent image participates each epoch. A deterministic rotating window schedule covers every eligible source window across complete cycles, shared with raw-input controls; this avoids multiplying training by nine merely because inference needs nine windows. Stop only after the scheduled coverage cycle and validation-based convergence rules, not because outcomes look favorable. Full original-grid inference covers every valid pixel with declared overlap blending.

**TerraMind:** retain the frozen Tiny route and add supported task adaptation (full fine-tuning; parameter-efficient route in the transfer phase). Match modalities, crop support, decoder/output convention and raw-input controls. The held task is13-band S2L1C+S1GRD; external S2L2A cannot be passed as L1C or padded with invented B10. Obtain compatible L1C or verify a separate supported L2A modality route. No assumption that freezing is a bug: the literature supports both modes.

**Copernicus-FM:** verify the paired-radar/reference architecture, normalization and exact3-class semantics; restore existing verified comparable states instead of refitting identical cells. Record any native-runtime adaptation. The second-pre/terrain routes need explicit trainable decoder-side fusion branches, per-input sensitivity checks and matched raw-input controls; author loader options alone do not implement them. A failed reproduction narrows that configuration's claim and does not stop other workstreams.

Deliverable: source-to-execution matrix, author-reference results, production/revised bridge, learning curves, prediction examples, independent source/input hashes and measured updated profiles. Use no test scores to choose the correction.

## ProngW — Observable-water capability

Evaluate Galileo radar, Prithvi optical and TerraMind multimodal in their own compatible roles. Baselines: matched-input standard U-Net, retained compact/linear/physical controls where they answer a real question. Add an architecture-matched random initialization only for an explicit pretraining-effect claim.

Report per-event water IoU/precision/recall, area over/underestimation, boundary/width/connected-patch strata and usable coverage. Define geometry strata in pixel/metre units using source resolution before viewing method differences. Reference-mask width is a label descriptor, not an independent surveyed channel width. Test crop/detail differences and environment-specific errors; do not attribute every dark return or omission to a mechanism without supporting imagery/labels. Preserve dry-only chips and unknowns.

Source comparison planning basis:10trained configurations across5event-group folds and3optimization seeds (150selected states), approximately250candidate fits with a3-rate source search or up to900with16rates everywhere. The latter would add roughly1–2compute weeks to the ordinary-source-search allowance and must be reflected in the measured queue estimate rather than silently absorbed. The exact comparable cells reused from completed runs are listed, not counted as new fits. Author reproduction is separately costed. Five folds preserve event separation, not a claim of five independent floods.

## ProngF — Newly inundated land and antecedent information

Build a common reference-date/validity contract and a full3-class confusion account. Compare a modular water-to-flood pipeline against learned paired change, not just foundation versus U-Net.

- **F0:** event-water map plus a declared static/antecedent normal-water reference; no unsupported claim that one image establishes new floodwater.
- **F1:** nearest valid pre-event map plus event map.
- **F2:** two pre-event observations plus event; preserve/disclose their disagreement and ages, do not treat two observations as proof of permanence.
- **F3:** the same temporal evidence plus DEM/terrain through a documented learned/physical route.
- **F4:** independently validated earlier-year AlphaEarth normal-water prior versus the non-AI normal-water reference.

Reuse the W source models and their pre/event probability maps for F0–F4 modular comparisons. Do not train five identical heavy encoders merely to change a reference mask. For direct learned change, compare one-pre, two-pre and two-pre+terrain with Copernicus-FM and matched standard U-Net. This is6trained configurations×5folds×3seeds=90selected states, roughly150–540candidates before exact-result reuse. Use compatible dates and the same target pixels; additionally retain the full population with declared missing-reference fallback. A conditional two-image gain cannot hide lost coverage.

Measure flooding confused with permanent water, permanent water falsely reported flooded, area bias and normal-water-edge errors. Test whether reference age/disagreement relates to errors; do not assume a unique causal explanation. Normal seasonal water expansion and CEMS flood labels remain distinct. A terrain prior regularizes mapping; it is not a hydraulic inundation model and must not erase real disconnected/urban water by rule.

Train linear/shallow spatial AlphaEarth decoders on independent supported water references, using geographic/event holdout. Reuse all64bands; do not average across catchments. Stream dense features in bounded shards and retain compact prior maps/provenance locally. Approximately30selected small-decoder states for2decoder types×5groups×3seeds; add the training-free matched history reference. Evaluate its contribution to F on the exact supported population. Report native10m/30m product resolution and reference age, and include a resolution-matched sensitivity before attributing a gain to learned embeddings rather than finer spatial support.

## ProngT — Transfer, local labels and adaptation

### Separate experiments

- **T0:** source-trained model applied to a new event/region without target labels. This is transfer without local adaptation, not an unfitted generic encoder called zero-shot.
- **T1:** a declared unlabeled target-adaptation method, compared with unchanged source inference. Include failure/drift; target reference labels cannot tune it.
- **T2:** source-model adaptation with local labels, using nested1/5/20%target annotation pools and a100%-of-available-adaptation-pool reference. Test blocks remain excluded even from the100%pool.
- **T3:** random versus informative acquisition of labels, using shared candidate/test pools, nested budgets and repeated masks/seeds. Simulated pixels/patches/area are not measured human annotation-hours.
- **T4:** frozen head versus supported full/parameter-efficient adaptation. Include at least optical/multimodal fine-tuning candidates and appropriate raw-input references; no new backbone collection is required.

Distinguish prior local-event labels from labels collected within another part of the current event. Where repeated local events exist, evaluate adaptation to a later event; otherwise same-event spatially blocked adaptation is a separate endpoint. Do not claim that withheld target blocks from one flood constitute independent new-flood validation. Define spatial buffers from source footprint/geolocation support and inspect sensitivity; no universal guessed distance.

Freeze adaptation hyperparameters/steps using **source pseudo-target meta-validation**. This avoids repeating LR searches or consuming uncounted target labels for each target fit. If local validation/calibration labels are used, deduct them from the declared target budget and report that alternative explicitly. Preserve all3optimization seeds and cross them with3independent nested target annotation-pool draws for label-sensitive comparisons; retain the full-pool duplicate only once per seed. Report both variation sources separately. Shared full-label source tuning follows the existing approved reuse. Do not silently reuse reduced-label tuning where the old protocol promised independent selection; a new source-fixed adaptation policy is a separately described experiment.

Each model has a task-specific eligible target census. GEOID supplies post-event radar and pre-event optical: Prithvi's post-optical task needs another actual acquisition/reference, while pre-optical+event-radar fusion is an explicitly different temporal configuration. Country labels do not imply country-policy differences; environmental transfer and cross-agency adoption are not interchangeable.

Original one-pool planning formula (superseded for revised queue sizing): primary adaptation states =3seeds×4positive budgets×sum(eligible target domains per trained system). For8systems all supported on Ndomains, this is96Nstates. Extra informative acquisition on2systems and3low-label budgets adds18N;2parameter-efficient branches add18N;2unlabeled branches add6N. Total illustration138N, **not a fixed final job count**. Current external SAR metadata offers up to89activation IDs before storm/overlap/support reconciliation; optical/multimodal counts differ. Use that inventory to enumerate exact jobs before launching, rather than multiplying every method by every incompatible target.

Report local-label learning curves, target/source shift descriptors, positive/negative transfer, precision/recall/coverage, compute and where adaptation provides no useful change. Existing source-training scarcity results remain separate.

## Cross-cuttingR — Reliability, hard environments and applied interpretation

Restore selected states and infer logits/probabilities; stored hard class predictions cannot reconstruct calibrated probabilities. Compare source-calibrated confidence, optional counted target calibration and held-out error. Report risk–coverage curves, flood omissions among accepted and referred areas, calibration by event and whether simple distribution-shift descriptors help anticipate failure. Conformal outputs require a stated unit and assumptions; no new-region guarantee follows from dependent pixels.

Include difficult environments in the analysis census. Align land-cover/settlement/context overlays and use separately supported urban/vegetation labels for stronger claims. Processed urban coherence/reference data and DeepFlood are a distinct extension: inventory/download compatibility first, then a matched intensity-versus-intensity+coherence/appropriate-input comparison. Do not claim an encoder recovered unobserved beneath-canopy flooding from open-water labels. A full raw-SLC processor or additional image-scale backbone is separately scoped if required; these unknown costs are not hidden inside the main ETA.

Independent uncertainty uses whole physical events/geographic groups and optimization-seed reporting, not pixels as independent replications. Metrics describe water mapping/new inundation at observed acquisitions. No depth, damages, public-warning lead time, adoption or reduced-loss claim is inferred. Connect measured outcomes to the resources an agency would need, with documented assumptions rather than new interviews.

## Audited compute execution

The [compute design](limburg-three-prong-compute-design-2026-11-10.md) and `config/limburg_three_prong_compute_policy_v1.json` specify unique preparation/fit/prediction nodes, shared frozen features and modular probabilities, source-fixed tuning reuse, three source-refit seeds for external application, bounded working shards and exact epoch-resume state. Existing caches/optimizations are not counted as new gains. All scientific populations/contrasts, independent annotation draws and optimization seeds remain. New grouped-probe, cache and concurrency options require parity and complete-profile evidence; none is silently enabled in the old queue.

The policy-facing resource account separates one-off research, reusable source preparation and cold/warm new-area mapping. The old tuning helper cannot handle the16-rate author-reference grid unchanged, and best-weight checkpoints do not support exact interrupted epoch continuation. These are explicit implementation items. Source rates and annotation workload arithmetic are recorded in `docs/reviews/limburg-three-prong-compute-review-2026-11-10.json`; they are not a measured speedup or final ETA.

## Runtime and workload estimates

[Measured basis](reviews/limburg-three-prong-execution-estimates-2026-11-10.json):25completed full-label candidate fits per task/learner from v5. These include training/setup under recorded contention, not cold extraction, test application or cloud recovery.

| Model/pipeline | Measured median full-label candidate | Planning range for a comparable new source fit | What changes the estimate |
|---|---:|---:|---|
| Galileo frozen spatial probe |5.2min |3–20min CPU | Patch4 feature volume, validation, author schedule; extraction separately |
| Prithvi Tiny full adaptation |41.6min |30–150min MPS | Crop cycling versus exhaustive9window epochs, batch size, convergence |
| TerraMind Tiny frozen decoder |4.7min |4–20min MPS | Cached feature/crop support and changed decoder |
| TerraMind Tiny full/PEFT adaptation |Not previously measured |20–120min MPS allowance | Requires an uncached real epoch/profile; no extrapolation from cached head cost as fact |
| Copernicus-FM frozen backbone/change decoder |82.8min |45–240min MPS | Extra antecedent/terrain features and changed head; no automatic full-backbone tuning |
| Matched standard U-Net |6–38min by task |5–90min MPS | Source population, channels, pixels/update and label budget |
| AlphaEarth linear/shallow decoder |Not measured here |10–90min CPU/MPS allowance | Dense footprint/I/O and decoder; feature transfer separately |
| Target adaptation |Not measured for new design |Typically0.5–20min/state allowance; large/full-label target or backbone tuning can exceed60min | Actual target area, label budget, cached versus trainable encoder, steps selected on source meta-validation |

These are **individual LR candidates/adaptation states**, not complete model studies. Source reference models alone entail hundreds of candidates; target adaptation can entail thousands of smaller fits. Reuse source weights, probability maps and exact feature caches rather than repeating preparation. Budget temperature/power contention and source/data load separately.

| Work package | Initial wall/compute allowance on this Mac | Parallelism/dependency |
|---|---|---|
| Metadata, independent splits, storage pilot |2–5working days; large verified offload may run longer | CPU/network, alongside contract work |
| Selective acquisition and QA |1–4network days initially; GEE/large ZIP work may add several days | Resumable/staged; no simultaneous full local archive |
| Author reproduction and revised runtime checks |2–5working days; roughly0.5–3CPU/MPS days | Before interpreting revised model comparisons |
| W source fits, geometry/coverage evaluation |Approximately3–8MPS days plusCPU probing and feature preparation | Source subset caches shared; comparable existing fits reused |
| F temporal/terrain comparisons and AlphaEarth prior |Approximately5–12MPS days plus1–4CPU/network days | Modular reference changes reuse maps; direct change fits cost separately |
| T complete adaptation/label selection/PEFT/unlabeled comparisons |Approximately12–35MPS days plusCPU work, provisional until domain inventory and pilot profiles | Source training reused; per-target policies fixed by meta-validation |
| R calibration, complete test inference, event review and final audit |Approximately2–6compute days plus3–7working days of review | Partial overlap with completed W/F/T outputs |
| Urban/coherence/vegetation extension |Additional3–10compute days **if processed compatible inputs are available** | Raw-SLC preparation or new architectures require a new explicit estimate |

Historical, pre-audit core programme allowance: roughly22–61MPS-equivalent days plus CPU/network work. At70%effective availability, with overlapping preparation and1–3weeks of engineering/review, the original allowance was **approximately6–16calendar weeks; superseded pending revised inventory/profiles**. The difficult-environment extension can add1–3weeks; raw-SLC work is not costed as if known. This is a planning envelope, not a completion promise or an authorized compute cap. Target-event count, target area and new adapter costs remain important unknowns. Re-estimate from a real complete epoch and an end-to-end large-target run before scheduling the full queue. Report aggregate candidate/state counts, device-seconds and critical path; never divide total work by three merely because three workers exist.

First reviewed W/reproduction results can arrive before the full programme, approximately1–2weeks after execution begins if acquisition/runtime checks cooperate. Unfavorable results do not trigger a new model search. An implementation failure gets diagnosed/versioned while other independent tracks continue.

## Concrete execution order and deliverables

1. Build exact dataset/model/version registry and verified storage rotation; pin/public-source metadata, overlap graph and semantic/clock checks. Deliver acquisition manifest, split map, backup/restore ledger and measured scratch budget.
2. Execute author-reference and Galileo/Prithvi corrections in isolated versions; profile TerraMind adaptation and modular/direct change routes. Deliver reference reproduction/bridge and measured resource sheet.
3. Run W across the eligible census while auditing and acquiring F/T inputs in the CPU/network lanes. Deliver original-resolution predictions/probabilities, geometry/environment errors and complete support ledger.
4. Run F modular reference comparisons, direct change and independent AlphaEarth prior; carry unmatched/unknown cases explicitly. Deliver reference-contribution and3-class error decomposition with whole-event uncertainty.
5. Freeze source-meta-validated adaptation policies and target annotation/evaluation blocks; enumerate every task-compatible job. Run T0–T4 with source/target/selection/calibration accounting and checkpoint reuse. Deliver adaptation learning curves, transfer errors and actual resource records.
6. Execute R and the compatible difficult-environment extension, consolidate empirical claims and rerun the completion/provenance/recovery audit. Update the living one-pager and supervisor evidence brief. Brian writes the dissertation prose and sends any correspondence; no new agency emails are currently prerequisites.

Maintain one versioned queue with independent W/F/T/R tags, resumable completed units, one MPS owner and two CPU slots. Record failed/undefined cases rather than silently omit them. Preserve previous results; source/model improvements are a separately identified study version. Freeze each scientific comparison before its new test outcomes are inspected, without pretending earlier exploratory knowledge was absent.

## Machine-readable planning records

- `config/limburg_three_prong_execution_plan_v1.json`: scope map, work packages, worker/resource assumptions, formula-based job counts, pending status.
- `config/limburg_three_prong_geoid_acquisition_v1.json`: pinned public release URLs, per-shard SHA256/bytes, selected modalities; no download launched.
- `docs/reviews/limburg-three-prong-execution-estimates-2026-11-10.json`: measured source-fit runtimes and inspected release volumes.
- `docs/reviews/limburg-three-prong-planning-provenance-2026-11-10.json`: inspected metadata/catalogue hashes and release revision.

The user's disk-space follow-up is incorporated: small safe cleanup opportunities were inspected without deleting useful files; the substantial recovery is the verified older patch-cache offload, not removing raw sources or other chapters. The prior duplicate cleanup already freed about4.5GiB. Subsequent authorized cleanup retired45.000GiB of historical compact imagery after verified Azure reconciliation, recovering44.987GiB observed space. Current spatial inputs, embeddings/results and other chapters were untouched. See recovery/README.md and the dated offload report; this does not imply that current inputs can be retired.
