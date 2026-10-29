# Final design audit: ten model-specific Limburg experiments

29 October 2026. Reviewed the six-part plan/configuration at commit `655c130`, prior source-contract audits, held input/coverage records and current code. Corrected the live design; no model fit/extraction or empirical result changed. This audit is a scientific/implementation review, not a blanket chapter gate or requirement for positive findings. The prior version is preserved in Git.

## Assessment

**The research question and ten model-specific roles are defensible. The first version was not precise enough to implement without scientifically consequential choices.** The corrections below address those choices. The remaining uncertainty is whether these representations help; that is what the experiments should establish. New local/token/multimodal adapters and the causal residual/transfer runner remain unimplemented, so numerical conformance cannot yet be certified.

## Findings and corrections

| Priority | Finding in original design | Correction now recorded |
| --- | --- | --- |
| High | Fixed equal raw/EO block weighting plus only a zero-whole-correction option repeats part of the forced-fusion problem. A useful raw correction could not explicitly reject EO. | Encoded heads contain all raw-only candidates exactly at EO weight zero, plus fixed 0.1/1 EO options. Select alpha and EO use entirely within earlier inner folds. Zero whole correction remains. Disclose candidate counts; no final-score weight search. |
| High | An additive linear EO residual could not express the proposed mechanism that surface state changes the response to storm conditions. Better spatial features alone would not resolve that mismatch. | Keep one ridge head, adding identical raw/EO interactions with observed prior-24h rain and causal baseline-predicted 24h mean Q. Training forecast conditioners come from the causal residual ledger. No observed future rain/Q, new learner or interaction search. |
| High | Same-gauge versus pooled fitting, common ground context and historical training-feature masks were not explicit. Different implementations could give one arm hidden or extra ground information. | Nine experiments use same-gauge/scenario heads. All learned arms receive identical permitted Q/rain/season/age/missingness context. Apply scenario masks to historical training/validation query features too; final historical donor availability remains the declared prior policy. |
| High | E08 excluded target-watercourse outcomes in the outer split but did not fully specify source residual construction. Source heads could be trained on easier same-watercourse residuals and deployed on other-watercourse errors. | Cross-fit each source watercourse as a held-out watercourse when generating its training residuals; repeat inside earlier-only inner folds. Exclude held-watercourse Q from donor responses AND source feature channels; explicitly canonicalize Wurm/Worm and group its sites. Equal watercourse weighting; target outcomes verification-only. |
| High | Support/fallback policy could compare an EO fallback to a raw correction on different rows or silently punish absent EO. | Exact paired query support for attribution. EO-unavailable encoded pipeline returns the raw correction when available; otherwise conventional C. Missing outcomes remain unscored/statused, not zero error. Separate supported increments from full-census pipeline utility. |
| High | “Site-balanced MAE” did not state whether pooled errors were native Q or area-normalized. Equal site weights do not remove different discharge scales. | Pooled scores use known-area mm/h, with explicit site/storm/offset/mask weighting; retain native m3/s per-site evidence. No hidden current Q/p99 normalization. E08 has watercourse-first weights. |
| Medium | Mean analogue trajectories are not necessarily the strongest point comparator under absolute error. A median reference was omitted. | Retain frozen C_mean as residual baseline, add coordinate-wise donor-median C as a declared point reference, score both on identical cases. Do not choose whichever is easier after results. |
| Medium | Raw summaries only inside the polygon could see less imagery than global encoder tokens whose input tiles extend outside it. “Same data” would then be too strong. | Give raw controls core-zone AND matching input-tile/context summaries, dates/masks and metadata; document unavoidable receptive-field differences. Area weighting alone does not remove context. |
| Medium | Several proposed ablations changed more than one thing: Copernicus metadata plus temporal readout; Prithvi spatial pooling; Presto cadence plus heterogeneity. Old pooled outputs cannot isolate these mechanisms. | One matched mechanism ablation per experiment. Produce paired outputs in the same pass where possible: Copernicus with/without metadata but same ordered readout; Prithvi local/global on the same forward pass; Presto mean/SD on the same twelve months; TerraMind ordered/mean from identical frames. Otherwise label configuration comparisons, not causal mechanism tests. |
| Medium | “Compact outputs” could still be implemented as millions of larger spatial/temporal patch files, repeating the storage problem. | Persist catchment/context features and resumable tile-level moment contributions, not a new full patch cache. Verify resume aggregation cannot double-count source weights. Measure peak scratch space rather than infer it from final vector size. |
| Medium | Year bootstrap wording could imply uncertainty over training, pretrained models or independent countries/watercourses. Some storms/assessment windows cross calendar boundaries. | Assign the whole storm to its initial-landmark year; resample saved paired predictions with all dependent rows together. State that intervals condition on fitted procedures and this network. E08's few watercourses receive individual reporting, not population claims from year resampling. |
| Medium | Physically named hypotheses could be mistaken for measured wetness/saturation or real-time flood progression. Pretraining overlaps were not explicit in this plan. | State that outcomes validate hydrological usefulness, not physical latent-variable measurement. Keep p99 high water separate from documented floods; horizon is next 24h, not eventual flooding. Frozen current models may have seen later historical imagery/locations; no strict unseen-basin/as-issued claim. |

## What is sound and retained

- One common high-water/monitoring-scarcity RQ, with model-specific observational roles and raw-data comparators. Shared ridge readouts are a controlled probe, not a claim that every encoder has the same optimal downstream model.
- Native checkpoints, units, masks, dates and output footprints are specified. Ten experiments do not become ten new architectures or ten identical full-scenario sweeps.
- All 481 rainfall episodes/eight sites remain in the census. This is a census of that declared rainfall calendar, **not all possible floods or independent regional climates**. Future outcomes may define evaluation-only strata, not issue-time predictors or episode selection.
- Chronological donors/heads, whole-storm separation, later-year inner evaluation and a zero contribution option. Ridge is fitted with squared loss but selected/scored with corrected-trajectory MAE; disclose that distinction.
- High-water results and documented-flood cases remain essential companion evidence; improvement dominated by ordinary flows is not a demonstrated flood-monitoring benefit.
- No new field measurements, agency request, flood-extent labels, operational deployment, generative-model branch or hydraulic study is added. Optional Galileo modalities remain masked unless explicitly implemented; the exact proposed climate/terrain groups need reconciliation.

## Model-specific audit disposition

| Model | Design judgment | Remaining numerical/input check |
| --- | --- | --- |
| Presto | Pixel moments and twelve-month cadence have a documented basis; not a calibrated wetness model | Area-weighted pixel mean/SD with partial months; mean-only ablation on identical output |
| AnySat | Spatial patch output is a supported use; elevation thirds are a transparent zoning hypothesis | Native patch grid/footprint and output masks; do not assume 10m dense resolution |
| Galileo | Supported climate/terrain groups make a defensible equal-input enrichment test | Exact product/normalizer/channel cadence; missing groups remain masked rather than invented |
| OlmoEarth | Ordered v1.2 radar tokens are a plausible surface-change representation | Time tokens attend all earlier frames; validate date/mask axes, not a causal one-frame decoder claim |
| CROMA | Radar texture plus raw amplitude is an appropriate distinction | Correct stretch/scaling and observed-neighbour texture statistics; fixed orbit geometry |
| Prithvi | Local pooling addresses an actual support mismatch in a large HLS tile | Tubelet/token support, boundary weights, and surrounding-context parity; Tiny checkpoint only |
| Copernicus-FM | Metadata use is supported and needs no new acquisition | Epoch/area/coordinate units; representative dates of composites are approximations, with spread/age disclosed |
| DOFA | Held-network watercourse transfer fits a landscape role but is a different estimand | Canonical river graph and source-only residual calibration; few related watercourses limit inference |
| TerraMind | Ordered downstream use of single-frame features is legitimate | Wrapper/direct output agreement; do not claim pretrained temporal attention or generated truth |
| SatMAE | Product-matched spatial readout is legitimate for the selected multispectral checkpoint | Exact scene/mask pairing for domain claims; SR/TOA contrast may otherwise mix support and radiometry |

All ten have a reason to be tested and a comparable raw reference. None needs an invented physical label or a positive result to justify inclusion. The checks above belong to the forthcoming adapter implementation; old successful loading cannot establish them for changed outputs.

## Remaining implementation checks, not new research barriers

1. Demonstrate future/hidden-Q poisoning invariance for raw descriptors, landmark joins, matched support and cross-fitted residuals. Training labels/outcomes must close before each training boundary. Baseline lookup refresh and head refitting have distinct clocks and should be logged.
2. Test weighted pixel/token moments against direct calculations; valid areas must not count overlapping tiles twice. Do not silently turn a missing token into a zero-observation feature or calculate spectral indices from imputed reflectance.
3. Validate each changed forward pass in its exact pinned environment, including metadata-only/missing-modality cases. Native temporal outputs can attend all pre-landmark frames; a time-indexed token is not an isolated observation of that date.
4. Record complete feature dimensions, fitting sample sizes, case/region observation ages, missing groups, fallback counts and fit-selection stability. High-dimensional small-sample ridge can legitimately choose no correction. This design cannot establish that no stronger raw/nonlinear or fine-tuned alternative could help.
5. Measure extraction time/memory/temp disk and queue within the laptop's actual capacity. These checks prevent another avoidable full re-extraction; they do not require a positive pilot before retaining a model's full-census evidence.

## Literature cross-check

The existing individual-use review supplies the ten model papers, exact-checkpoint qualifications and publisher examples. Two additional methodological checks reinforce the audit without adding new models/data requirements:

- [An argument for parsimony in differentiable hydrologic models](https://hess.copernicus.org/articles/30/5173/2026/) discusses how catchment attributes can act as geographic identifiers rather than transferable physical explanations. This supports identity/location controls and modest interpretation of E08; it does not validate these encoders or require its hydrological architecture.
- [Rethinking Evaluation in the Era of Time Series Foundation Models](https://arxiv.org/abs/2510.13654v3) distinguishes evaluation contamination from ordinary downstream splitting. Its subject is time-series models, so its warning about pretraining overlap is a methodological analogy here, not proof that these EO checkpoints contain our test examples.

**Disposition:** corrected live design is suitable for implementation and per-model engineering validation. It is not yet an executable/audited ten-part numerical run. No requirement to pause all ten for one experiment's optional input or an arbitrary score threshold is introduced.

Preparation validation after the amendment: **38 tests passed** (11 preparation/contract checks plus 27 existing scarcity/diagnostic regressions); Ruff and local link checks passed. These are not results of the unimplemented revised statistical head or adapter forwards.
