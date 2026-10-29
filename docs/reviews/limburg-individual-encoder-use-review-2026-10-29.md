# Using each Limburg EO encoder on its own terms

29 October 2026. Internal research aid; Brian writes dissertation prose. Documentation/literature and held-code review, **not a new empirical analysis**. This pass launches no extraction, model change, download campaign or scoring run. The proposals below are recommendations, not new requirements for the chapter.

## What this review changes

The ten checkpoints do not represent ten interchangeable ways to measure the same hydrological state. They differ in their observational unit, training tasks, sensor, spatial footprint, temporal design and output. Valid preprocessing is necessary, but does not make one catchment-vector/nearest-neighbour recipe an adequate test of every model's capabilities.

The corrected extractions remain valid evidence about the declared routes. The completed learned-readout diagnostics also remain evidence: small increments against matched learned controls, without a reliable improvement over the strongest conventional reference. Neither result establishes that these encoders have exhausted their possible hydrological uses. Equally, better model-specific use is not a promise of a positive result.

This review checks the selected checkpoint, rather than attributing the largest or newest family member's capabilities to it. Evidence consists of the pinned source/card inventory in `config/limburg_eo_model_assets.json`, selected production runs in `config/limburg_eo_coherent_selected_runs.json`, corrected adapters, cached papers under `data/raw/foundation_assets/documents/eo-literature-2026-10-22/`, and publisher documentation revisited on 29 October. The [22 October source-contract audit](limburg-ten-model-documentation-review-2026-10-22.md) preserves source revisions and earlier input corrections; its pending-rerun wording is historical. Current diagnostic results are in [the findings note](../limburg-eo-signal-findings-2026-10-29.md).

## 1. Presto — pixel-level antecedent surface condition

**What we have/use.** Default pretrained Presto; ten-band S2 inputs with missing modalities masked, actual pixel months and locations. Native temporal encoding of pixel series, then pixel/patch/catchment means. Recent four-week, completed-month snapshot and twelve-month representations are held. The latest diagnostic evaluated recent and snapshot, not the twelve-month route.

**What its evidence supports.** Presto learns pixel time series and supports variable sequence lengths. Its paper includes live fuel moisture regression and uses concatenated **mean and standard deviation of pixel embeddings** for image-level tasks. Twelve monthly steps resemble pretraining; shorter sequences are supported, so four weekly steps are an explicit transfer choice, not automatically an invalid input. Fuel moisture evidence is relevant to surface-state representation, but does not validate soil moisture or river discharge prediction.

**What we can do with these data.** Represent antecedent vegetation/surface condition and its spatial variability; condition a hydrological assessment on that state. Test the already-held twelve-month context separately from short-term context. Its recent learned-readout signal makes this a plausible candidate, not a proven winner.

**What we should do.** First assess the held native-cadence representation through a small learned correction to the strong conventional prediction, permitting zero EO contribution. If that warrants further extraction, preserve pixel-level mean **and variance**, with area/support weighting and a small number of physically motivated regions. Accumulate moments while encoding rather than store every pixel token. A catchment's heterogeneous saturation/land cover may matter more than its average latent state. This is a physical hypothesis, not an interpretation already established by embedding dimensions.

**Cost/data distinction.** Existing twelve-month vectors need only downstream work. Published pixel mean-plus-SD requires re-encoding: the current cache has only patch means. SD of patch means is a useful between-patch descriptor but is not the paper's pixel SD. S1, weather and terrain inputs could be added later using the official helper; give the conventional control the same raw information. No Dynamic World acquisition is necessary just to use Presto correctly. Fine-tuning, if later justified, should use catchment-level supervision/aggregation; do not label every pixel with gauge Q as though it were a pixel measurement.

Sources: [paper](https://arxiv.org/html/2304.14065v4), [official implementation and usage](https://github.com/nasaharvest/presto).

## 2. AnySat — spatially structured, multitemporal landscape observation

**What we have/use.** AnySat base, ten-band S2 sequences, supported tile output. A 640 m tile is encoded with 20 m attention patches. Corrected dates follow the pinned executable demo/loaders where these differ from README prose. We then reduce tiles to catchment vectors.

**What its evidence supports.** Cross-resolution/multimodal representation learning and tile, patch and dense outputs; spatial downstream tasks use that structure. A valid tile output is not necessarily the most informative output for a river catchment. S2-only is supported; its name does not require every modality.

**What we can do.** Preserve contrasts between valley/floodplain, hillslope and other contributing areas, and relate their pre-event condition to later river behaviour. Paired S1/S2 could complement optical cloud gaps if aligned at the correct physical extent. Patch/dense outputs could also support mapping tasks, but those would require independent spatial labels and a different target.

**What we should do.** First inspect/reaggregate existing tile vectors by held geography to determine whether useful spatial contrasts survive. If finer support is needed, extract patch/dense features for meaningful contributing areas rather than average another complete tiled census. Retain temporal order where the native model supports it. Recent diagnostic increments justify considering this alongside Presto, not combining them automatically.

**Cost/data distinction.** Coarse tile reaggregation can reuse caches; 20 m/local features cannot be reconstructed from tile vectors and require new encoding of existing imagery. SAR fusion is a separate supported input extension, with per-modality dates and availability. It is not a fix required for S2-only validity. Fine-scale water mapping would need appropriate dates and labels, not just existing gauge outcomes.

Sources: [paper](https://arxiv.org/html/2412.14123v3), [official input/output guide](https://github.com/gastruc/AnySat).

## 3. Galileo — physically enriched, multiscale environmental context

**What we have/use.** Galileo **Nano**, native temporal S2-only inputs with other groups masked, token-consistent pooling. Its 320 m input footprint differs materially from the kilometre-scale routes. Do not transfer results for Galileo Tiny or larger checkpoints to Nano.

**What its evidence supports.** Separate space-time, spatial, temporal and static input groups, with local/global representation objectives. Climate/water-balance and terrain inputs are part of the design, not quantities inferred automatically from our S2-only route. Its documentation supports missing groups, so the present route is legitimate but partial.

**What we can do.** Build an antecedent environmental-state representation combining observed surface condition with terrain and appropriately aggregated climate/water-balance variables. This is closer to the basin-state question than expecting optical S2 alone to encode a developing storm.

**What we should do.** Make a model-specific multimodal proposal using only verified channel definitions, units, grids and cadence. Inventory held terrain/weather against those exact groups before any acquisition. Monthly model inputs must not be filled with hourly rainfall merely because both describe weather. Compare S2-only, physically enriched Galileo, and a control receiving the identical raw physical variables. Otherwise an apparent encoder benefit may simply be additional data.

**Cost/data distinction.** Adding modalities requires fresh Galileo encoding and some product/convention reconciliation; held ERA5/RADOLAN are not automatically exact substitutes for the trained climate products. Native local features are another option, not a simultaneous mandatory change. The weak/uncertain current diagnostic increment does not prove enrichment will help.

Sources: [paper](https://arxiv.org/html/2502.09356v3), [official modality and masking guide](https://github.com/nasaharvest/galileo).

## 4. OlmoEarth — radar-based temporal surface change

**What we have/use.** **v1.2 Tiny**, ascending Sentinel-1 VV/VH sequences; corrected token masks and pooled native temporal features. S2 is not currently supplied. Later v1.3 location-query pooling is not a capability of this selected checkpoint.

**What its evidence supports.** Multimodal spatiotemporal learning with explicit missing-observation handling. Encoder outputs can retain space/time structure. The official quickstart's pooled feature example does not mean pooling away every time/space dimension is compulsory. Most application evidence concerns surface tasks, not hourly river trajectories.

**What we can do.** Represent antecedent radar-observed surface condition and its changes without optical cloud dependence. Compare ordered/local features with the current global temporal summary; inspect the relation to raw VV/VH changes, acquisition geometry and season before calling a feature wetness.

**What we should do.** Give the existing SAR route a temporal-change readout, with a raw-backscatter/change control and fixed orbit handling. First use cached spatial patch differences where possible. Re-encode only if per-date/token outputs are needed: those cannot be recovered from the present pooled vector. S1/S2 fusion is an optional later question, not an immediate requirement.

**Cost/data distinction.** Existing SAR is sufficient for this proposal; no new global download. Partial ten-band optical input must follow v1.2's actual band/mask contract before fusion; training band dropout alone is not proof that any arbitrary API tensor is valid. Do not silently fill B01/B09 or borrow newer-version APIs.

Sources: [v1.2 paper](https://arxiv.org/html/2605.20804v3), [official inference quickstart](https://github.com/allenai/olmoearth_pretrain/blob/main/docs/Inference-Quickstart.md).

## 5. CROMA — radar texture, not an absolute wetness meter

**What we have/use.** Base SAR branch, 120-pixel/1.2 km VV/VH images, corrected publisher normalization, pooled `SAR_GAP`; frames encoded independently then averaged. Primary and supplemental orbit routes are separately recorded.

**What its evidence supports.** Radar/optical contrastive and masked learning, supported SAR-only inference, pooled and spatial SAR outputs. The prescribed per-image/per-channel contrast stretch removes absolute brightness offset/scale. Output-vector normalization cannot restore information removed at input.

**What we can do.** Use spatial radar texture/pattern alongside, rather than instead of, absolute calibrated backscatter. Compare per-date pattern changes on consistent orbit geometry. Its somewhat better snapshot diagnostic is a reason to examine cadence, not to claim CROMA has temporal attention.

**What we should do.** Retain the publisher transform and pair the representation with raw VV/VH level/change summaries in a controlled readout. Supply those raw summaries to the non-encoder control too. If spatial localization matters, extract SAR tokens before the pooled readout. Do not change normalization ad hoc to preserve amplitude and still label that route publisher-compatible.

**Cost/data distinction.** Raw SAR summaries require no new imagery or encoder. Ordered frame vectors or pre-pooling tokens require extraction unless the relevant separate snapshot outputs already supply the desired dates. Keep orbit 88/15/161 distinct; more observations are not interchangeable viewing geometry. The optical/joint branch expects a different band set; absent B01/B09 are not a deficiency of the valid radar branch.

Sources: [paper](https://proceedings.neurips.cc/paper_files/paper/2023/file/11822e84689e631615199db3b75cd0e4-Paper-Conference.pdf), [official output/normalization example](https://github.com/antofuller/CROMA).

## 6. Prithvi — HLS landscape condition with a large spatial footprint

**What we have/use.** EO 2.0 **Tiny TL**, six HLS bands at 30 m; time/location inputs and native temporal processing. The 224-pixel tile spans **6.72 km**, followed by non-CLS token mean. This can include substantial surrounding landscape even when catchment overlap weights are exact.

**What its evidence supports.** HLS land-surface representations and supervised spatial/regression adaptation. The exact Tiny card matters; large 300M/600M published results are not Tiny results. The configured four frames and flexible longer inference are different regimes; twelve months is supported transfer, not exact training reproduction.

**What we can do.** Describe antecedent landscape/moisture/snow-related optical condition, with careful spatial support and acquisition-age accounting. Those physical interpretations need validation; the features are not calibrated moisture observations. Snapshot gains in the diagnostic show that longer context is not automatically better.

**What we should do.** Address spatial pooling before adding another modality: retain tokens associated with the contributing catchment, separately summarize relevant regions, and compare against the current whole-tile representation. Token footprints and contextual receptive fields still matter; selecting an inside token does not remove all outside context. Use the already-held snapshot/recent/monthly alternatives transparently rather than select a cadence from favorable final scores.

**Cost/data distinction.** New token pooling requires Prithvi re-encoding of held HLS; no new imagery is intrinsically necessary. Cached tile vectors only permit coarse regional weighting. Fine-tuning a catchment head is possible; a new segmentation project is not needed for the current RQ.

Sources: [exact Tiny TL card](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-tiny-TL), [family paper](https://arxiv.org/html/2412.02732v3).

## 7. Copernicus-FM — sensor/product-aware context with explicit metadata

**What we have/use.** Base, ten-band S2, published spectral normalization and benchmark patch-mean/LayerNorm readout; coordinates/date/token-area metadata currently supplied as unknown. This is supported missing metadata, not a preprocessing defect. The separate TOA/QA60 supplemental route is already held.

**What its evidence supports.** Flexible spectral and supported nonspectral inputs plus explicit location, time and scale metadata. Metadata units are longitude/latitude, days since 1970, and internal patch-token area in km². For the current 16×10 m token that area is 0.0256 km², not full image/catchment area. Supported heterogeneous products do not make arbitrary hydrological series a pretrained input type.

**What we can do.** Represent landscape/surface context while using the location/date/scale information the model was designed to consume. Compare product-domain effects using the existing SR/TOA routes. A potential natural role is between-catchment environmental context, not necessarily within-gauge hour-to-hour dynamics.

**What we should do.** If revisiting this model, use the held real metadata in one explicitly documented route and inspect the existing product-domain comparison first. Include simple identity/coordinates/season controls so improvement is not credited to learned wetness when metadata supplies catchment identity or date. This is a targeted model-specific change, not another ten-model rerun.

**Cost/data distinction.** Metadata and TOA comparison need no new acquisition. Enabling metadata changes encoder outputs and needs Copernicus-FM re-encoding. Monthly climate-grid embeddings cannot be treated as hourly tributary state; novel-variable use requires a separate compatibility argument.

Sources: [paper](https://arxiv.org/html/2503.11849v3), [official implementation/metadata guide](https://github.com/zhu-xlab/Copernicus-FM/tree/main/Copernicus-FM).

## 8. DOFA — cross-sensor landscape representation

**What we have/use.** **v1 ViT-base e100**, matched source/weights, six non-TCI S2 bands, wavelength conditioning and documented quantized transfer. This is not the newer DOFA checkpoint/code pair advertised by the current README.

**What its evidence supports.** Wavelength-conditioned adaptation across sensor/band configurations for EO tasks. Wavelength flexibility does not remove product normalization or spatial-support requirements. A single-frame backbone plus frame mean is not a temporal hydrological model.

**What we can do.** Describe vegetation/land-cover/surface differences between catchments and assess portability across sensors or sites. Our same-gauge learned-head diagnostic largely conditions away static between-catchment differences. That diagnostic therefore cannot settle this potential use; earlier cross-river results remain relevant and should be read before proposing more experiments.

**What we should do.** Retain as a landscape/transfer comparator. Do not prioritize another hourly-response extraction solely because its current increment is small. Any future cross-river test should ask whether it explains transfer beyond area, season, coordinates and conventional/static descriptors. A cross-sensor test is a different scientific question, not a required rescue for the scarcity RQ.

**Cost/data distinction.** Existing vectors support this review and downstream conditioning. New sensor inputs would require verified units/bands/normalization and encoding; the dynamic wavelength layer alone is insufficient. No silent source/weight upgrade is justified.

Sources: [v1 paper](https://arxiv.org/html/2403.15356v1), [official source/version warnings](https://github.com/zhu-xlab/DOFA).

## 9. TerraMind — multimodal surface features; generation is a separate capability

**What we have/use.** 1.0 Tiny, supported ten-band S2L2A subset, encoder-only spatial features pooled across separately encoded dates. We do not currently use TiM or a generative decoder.

**What its evidence supports.** Multimodal land-surface learning; official supervised flood-mapping configurations and a multitemporal wrapper. The wrapper does not give a single-frame backbone native temporal attention. Generation/TiM requires the corresponding components and cannot be inferred from having an encoder checkpoint.

**What we can do.** Preserve spatial surface features for antecedent context, or learn a lightweight ordered-date readout. S1/S2 fusion is supported in the wider implementation. Supervised flood-extent mapping is a defensible application, but requires independent spatial flood labels and is not equivalent to forecasting a gauge trajectory.

**What we should do.** Keep a surface-context role under the current RQ. If temporal readout is justified, follow the documented wrapper/readout approach rather than assume equal averaging uses its temporal potential. Do not add generated DEM/land cover as verified physical truth or as a replacement for hydraulic geometry.

**Cost/data distinction.** Existing vectors permit current context assessment. Fresh temporal/spatial features require encoding, not necessarily new imagery. Any flood-mapping or generation extension has its own labels/components/validation and should remain optional, not another chapter dependency.

Sources: [paper](https://arxiv.org/html/2504.11171v5), [official examples/configurations](https://github.com/IBM/terramind).

## 10. SatMAE — multispectral spatial features, with product-domain care

**What we have/use.** Multispectral ViT-base e199, ten bands, 96-pixel input, corrected publisher stretch/quantization; independent dates averaged. The selected checkpoint is **not temporal RGB SatMAE**. The TOA/QA60 supplemental route already exists.

**What its evidence supports.** Masked multispectral pretraining and downstream supervised spatial representation use. The family includes a separate temporal method, but its capabilities cannot simply be assigned to our multispectral checkpoint. Pretraining/downstream radiometric domain and feature readout matter.

**What we can do.** Supply landscape/spectral context and compare native-product transfer. Ordered per-date vectors or patch features could support a trained downstream state/change task; their benefit is an empirical question. The current weak diagnostic gives no positive reason to prioritize it over better-matched candidates.

**What we should do.** Interpret the completed SR versus TOA/QA60 comparison before any new extraction. Keep this model as a spatial baseline unless that comparison identifies a concrete issue worth resolving. If a temporal head is later used, call it a downstream temporal head on SatMAE features, not the pretrained temporal SatMAE model.

**Cost/data distinction.** The held supplemental comparison needs no new imagery or encoding. Current pooled sequence vectors cannot recover ordered weekly frame vectors. Monthly snapshot vectors may supply an existing monthly sequence where all required dates exist; verify exact support instead of assuming completeness. Dense patch tokens require fresh extraction.

Sources: [paper](https://arxiv.org/html/2207.08051v3), [official checkpoint distinctions and transforms](https://github.com/sustainlab-group/SatMAE).

The [read-only inventory](limburg-individual-encoder-use-inventory-2026-10-29.json) records selected checkpoints, sample cache schemas, aggregate row counts and SHA-256 hashes of held papers/code/configurations. Counts are archive rows, not eligible independent events or proof of complete support for the new rainfall census.

## What is recoverable now

Inspection of an NPZ in each selected run found an embedding vector plus validity and acquisition-day arrays. The retained representations have dimensions: Presto 128, AnySat 768, Galileo 128, OlmoEarth 192, CROMA 768, Prithvi 192, Copernicus-FM 768, DOFA 768, TerraMind 192, SatMAE 768. These are per-inference-patch caches, not dense token/pixel/time caches. One-file schema inspection does not establish completeness of every file; the completed run audits supply that evidence.

- **No encoder work:** existing twelve-month/snapshot/recent vectors; coarse patch reaggregation and between-patch variability; held supplemental scores; raw SAR summaries; fitting a small residual correction to the strong conventional method.
- **Re-encode held imagery for a specific reason:** Presto pixel moments; AnySat/Prithvi local tokens; OlmoEarth ordered/spatial outputs; Copernicus-FM metadata; genuinely new multimodal inputs.
- **New inputs/labels only if the scientific question warrants them:** exact Galileo climate products not already compatible; missing optical bands for another branch; independent flood-extent labels for mapping. None becomes a blanket chapter requirement.

Catchment overlap weights describe how a global patch vector contributes; they cannot remove surrounding pixels that influenced that vector. Reweighting overlapping patches also needs careful support/overlap accounting, not an unweighted average of cached vectors. Encoded composites must remain strictly before the assessment time; representative dates do not make a multiday composite an instantaneous acquisition. Product delivery remains nominal, not independently validated as-issued availability.

## Recommended direction

**Keep the RQ; change the role assigned to the representation.** The operational question remains whether satellite AI helps assess developing high water when conventional observations are scarce, late or absent. EO is most plausibly an antecedent surface/landscape-state conditioner, not a substitute observation of current discharge. This is a mechanism to test, not an established finding.

1. Review existing native-cadence and supplemental evidence, model by model. Start with Presto's held twelve-month context and SatMAE/Copernicus product-domain results; do not perform another full matrix just to fill cells.
2. Use a small learned correction to the **strong conventional prediction**, rather than replace it with the weaker standalone learned head. First candidates are Presto and AnySat, for their mechanism and diagnostic evidence. Train residual targets from earlier out-of-fold baseline predictions, not fitted training residuals, and keep a zero-correction option. Choose/evaluate within chronological training folds; report high-water separately. This is still exploratory development on inspected data.
3. If a specific representation bottleneck remains credible, make one targeted change: Presto pixel heterogeneity, AnySat contributing-area tokens, or Galileo verified physical modalities. Choose for the physical question and available evidence, not a promise that one must win. CROMA/raw radar and Copernicus metadata are distinct alternatives, not simultaneous requirements.
4. Retain the other models as informative comparators in their documented roles. No model is obliged to become a successful hourly predictor. No full re-extraction is recommended at this point.

This pass does not discover another known numerical preprocessing defect. It identifies underused outputs/modalities and task mismatch hypotheses. It does not erase the negative fixed-fusion results, certify optimum use, or establish operational benefit. AlphaEarth and TTM remain separate static-landscape and hydrological time-series comparators; neither is one of these ten EO encoder routes.
