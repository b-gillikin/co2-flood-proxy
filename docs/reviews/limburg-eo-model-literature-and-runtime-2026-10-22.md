# EO model literature and runtime review — 22 October 2026

Internal research aid, not dissertation prose. This supplements the
[publisher-documentation review](limburg-ten-model-documentation-review-2026-10-22.md)
with original papers, appendices and cross-model evaluations. The
[retirement/restart record](limburg-eo-retirement-and-restart-2026-10-22.md)
describes the corrected extraction now running. Earlier execution notes remain
dated history.

**Assessment:** the literature supports frozen-feature comparisons and supplies
useful configuration details. This pass found no additional demonstrated input
defect requiring interruption of the corrected run. It does not establish that
our settings are optimal, or that EO embeddings will improve hydrological
analogues. Finish the declared comparison before selecting further adaptations.
No encoder, runtime, input population or evaluation rule was changed in this pass.

## Scope and source record

Reviewed the ten model families' papers, relevant appendices, the OlmoEarth
v1.2 update, PANGAEA, GEO-Bench-2, Corley et al.'s preprocessing study, and a
direct soil-moisture application. Fifteen primary-source documents were saved
locally: 13 HTML papers and two PDFs, about 19.2 MB before text extracts. The
[companion JSON](limburg-eo-model-literature-and-runtime-checks-2026-10-22.json)
records URLs, retrieved versions and file hashes. Full sources
are under `data/raw/foundation_assets/documents/eo-literature-2026-10-22/` and
are excluded from Git. CROMA's throughput/compute appendix pages 24–25 were also
rendered and visually inspected.

This is a targeted methods review, not an exhaustive citation census. Published
benchmark numbers, model-card claims and our own implementation observations
are distinguished below. Checkpoint/source revisions remain those in
`config/limburg_eo_model_assets.json`; the review did not update them.

## What each model has actually been used for

The configuration column combines paper evidence with our inspected, pinned
adapter. It is not a claim that the papers used Limburg's inputs or readouts.

| Selected checkpoint | Primary literature and uses | Configuration implication for this run |
| --- | --- | --- |
| **OlmoEarth v1.2 Tiny** | [v1.2 report, §§2–3 and Appendix B](https://arxiv.org/html/2605.20804v3), with the [v1 methods](https://arxiv.org/html/2511.13655v1): frozen kNN/linear probes and adapted environmental tasks. | The update is explicitly evaluated as a frozen encoder. Keep the selected v1.2 weights, SAR route, masks and dates; v1 benchmarks are lineage, not interchangeable checkpoint results. |
| **Galileo Nano** | [ICML paper, §4.1 and Appendices B–D](https://arxiv.org/html/2502.09356v3): image/pixel-series classification and segmentation, including crops and flood mapping; frozen probes and kNN. | Variable token patch size is a documented compute/detail trade-off. Our size 8 is supported. Missing modalities can remain masked; neither hourly rainfall nor newly acquired climate channels are required. |
| **AnySat base** | [CVPR paper, §§3.3–4.2 and Appendix C](https://arxiv.org/html/2412.14123v3): land cover, crop/tree classes, deforestation, flood and burn-scar mapping; probing and fine-tuning. | Patch size is a physical length in metres, distinct from image width. Keep our 20 m patch, dated S2 route and tile output. The corrected day convention follows executable publisher sources; the paper does not resolve that README discrepancy. |
| **Prithvi EO-2.0 Tiny TL** | [Family paper, §§III-A/B and applications](https://arxiv.org/html/2412.02732v3): disaster mapping, crop/land-cover and ecosystem tasks. Its main results concern 300M/600M models; the [Tiny publisher card](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-tiny-TL) supports this smaller release. | Keep six-band HLS, 30 m support and the Tiny-specific configuration. The paper's four-frame pretraining explains the cadence origin; flexible inference is supported by the held implementation/card. Twelve-frame inference is transfer, not a reproduced four-frame experiment. |
| **CROMA base SAR** | [NeurIPS paper and Appendix A](https://proceedings.neurips.cc/paper_files/paper/2023/file/11822e84689e631615199db3b75cd0e4-Paper-Conference.pdf): unimodal/joint frozen representations, classification, clustering, kNN and segmentation. | SAR-only encoding is legitimate. Keep the corrected publisher 0–1 input transform. Spatial extrapolation support does not turn independently encoded dates into a native temporal model. |
| **DOFA v1 base e100** | [Original v1 paper, experiments and Supplement D](https://arxiv.org/html/2403.15356v1): wavelength-conditioned transfer, including frozen classification/segmentation heads. | Wavelengths are in micrometres. Keep the documented six non-TCI Satlas-band conversion and 224-pixel input. Newer DOFA/DOFA+ experiments do not describe this exact checkpoint; no manufactured RGB channels are needed. |
| **Copernicus-FM base** | [Paper, §§4–6 and Appendix B](https://arxiv.org/html/2503.11849v3): frozen downstream heads and averaged geographic embeddings for climate statistics. | Keep DN normalization, wavelength/bandwidth units and explicit unknown metadata. The model was trained to tolerate absent metadata. Its climate example concerns long-term spatial statistics, not storm evolution or river forecasting. |
| **TerraMind 1.0 Tiny** | [ICCV paper, §5.4 and Appendix 11.2](https://arxiv.org/html/2504.11171v5): averaged frozen patch embeddings used in nearest-neighbour/prototype classification without weight updates; other experiments use fine-tuning or generation. Main reported comparisons use larger variants. | This is direct precedent for similarity retrieval. Our Tiny S2-L2A backbone is a distinct declared route. Its frame mean has no temporal attention. TiM, diffusion generation and their settings are not part of this extraction. |
| **Presto default pretrained** | [Paper, §§5.1–5.3 and Appendices A.2/A.6](https://arxiv.org/html/2304.14065v4): pixel-series crop, environmental regression and image classification with simple downstream models. | Monthly pretraining supports seasonal context; shorter observed histories are demonstrated. Our weekly readout remains a cadence transfer. The corrected per-pixel months/masks are appropriate; absent Dynamic World is supported. |
| **SatMAE multispectral base e199** | [NeurIPS paper, §5.4 and Appendix A.3.3](https://arxiv.org/html/2207.08051v3): multispectral classification/transfer, separately from its temporal RGB experiments. | Our 96-pixel input, 8-pixel tokens and ten retained bands match the multispectral setup. Keep the corrected executable normalization. Temporal-RGB settings and random training augmentations are not requirements for this checkpoint's deterministic extraction. |

## Runtime information that is useful here

| Evidence | What it does and does not tell us |
| --- | --- |
| **CROMA Appendix Table 14, p.24:** ViT-B at 120×120 is reported at **1,532.1 images/s** on an A100-40GB; SatMAE ViT-B at 96×96 at **692.5 images/s**. | These are the authors' benchmark throughput measurements, not our SAR-only Mac throughput. Sensor/implementation, batching, device and I/O differ. The appendix explains the extra spectral-group tokens in SatMAE. No local completion estimate follows from these numbers. |
| **AnySat §4.2:** approximately **3 ms for one mono-date TreeSatAI tile**. | A useful scale reference, not a forecast for our longer sequences. The paper also changes training batch size with dataset/sample shape; those training batches are not prescribed inference batches. |
| **Galileo Appendix D, Table 14:** Nano's EuroSAT encoding cost is **0.25 GMACs at size 8** versus **0.06 at size 16**, with task performance changing too. | Confirms that token size changes both computation and representation. Our fixed size 8 is defensible; changing it now would change the experiment, not merely accelerate identical work. |
| **OlmoEarth v1.2 §§2.2/3 and Appendix B:** fewer S2 tokens and about **5.3× fewer S2 MACs for Base** than v1; an additional linear-versus-convolution optimization is benchmarked on NVIDIA hardware. | We already selected v1.2. Neither figure is a promised speed-up for our Tiny SAR route. CUDA/bfloat16 kernel results cannot be assumed on Apple MPS. |
| **Presto Appendix A.2:** image cost explicitly scales with pixels encoded. | Our all-observed-pixel extraction can be lengthy despite the small encoder. The paper's short Mac CPU fine-tuning example is a different task/data volume. Keep the validated four-thread/128-pixel batch profile; the paper supplies no superior Mac setting. |
| **Prithvi, DOFA, Copernicus-FM, TerraMind and SatMAE** report substantial training/benchmark configuration detail. | This pass did not find a reproducible timing for our exact checkpoint, input window, Mac runtime and storage pipeline. Pretraining GPU-hours and batch sizes do not set frozen-inference time. No environment update or precision change is justified by those figures alone. |

The local logs, rather than published GPU timings, should determine remaining
time. This review did not rerun encoders or benchmark competing worker counts.
The two-CPU/one-MPS queue continues unchanged.

## Evaluation lessons from independent comparisons

**Preprocessing can change a ranking.** [Corley et al. (CVPRW 2024)](https://openaccess.thecvf.com/content/CVPR2024W/PBVS/html/Corley_Revisiting_Pre-trained_Remote_Sensing_Model_Benchmarks_Resizing_and_Normalization_Matters_CVPRW_2024_paper.html)
demonstrate sensitivity to input sizing and normalization. That supports the
input corrections already made; it does not prescribe resizing every catchment
to the same physical footprint. Preserve each declared sensor/product/footprint
and avoid interpreting the outcome as an architecture-only ranking.

**Single-date feature aggregation has precedent.** Galileo Appendix C.3 uses
mean/max pooling across dates. [PANGAEA §4 and §5.5](https://arxiv.org/html/2412.04204v2)
instead tests trained linear or lightweight temporal aggregation over frozen
per-date encoders. Our fixed frame mean is a simpler supported design choice;
it cannot recover ordering, and poor results would not establish that all
temporal adaptations of the backbone fail. Adding a trained temporal head is
a different learning experiment, not a required repair.

**Benchmark leaders are not automatically leaders as frozen features.**
[GEO-Bench-2 §6.3.2](https://arxiv.org/html/2511.15658v2) finds that freezing
changes performance and ranking. Its main protocol also uses a common
normalization with a fine-tuning caveat. Copying that transform into every
frozen adapter would discard checkpoint-specific input conventions. Retain
our matched-event/donor comparisons against hydrology, rather than importing a
published leaderboard or optimizing settings on final response outcomes.

**The hydrological signal remains empirical.** A [2026 soil-moisture preprint,
§§III–IV](https://arxiv.org/html/2602.18083v1) evaluates frozen Prithvi-300M
features with station-grouped validation and finds little gain over compact
features in that task. It also discusses spatial pooling dilution. This is
relevant caution, not a Limburg performance prediction. Its nearest-date radar
matching can use later acquisitions; that selection must not be copied into
our pre-event windows. We retain the existing cutoff and acquisition-age checks.

## Two possible improvements, neither an automatic extra run

1. **Presto's spatial spread.** Its §5.2 pools pixel embeddings using a
   concatenated mean and standard deviation; we retain only the mean. That is
   an explicit difference, not an input bug. If a subsequent question warrants
   heterogeneity features, preserve per-patch counts, sums and squared sums and
   combine them correctly over the catchment. Pixel variance cannot be recovered
   from patch means alone. This would require additional Presto encoding, not
   replacement of all ten models. It was not added mid-run.
2. **Copernicus-FM's held metadata.** Appendix B.4 supports testing known
   location/time/area instead of unknown encodings. The current route is valid
   but does not use that capability. Any later comparison should hold imagery
   and donor support fixed and retain identity/season controls. This needs no
   new imagery; it is a separately labelled adaptation, not a condition for
   completing the current comparison.

These are options to assess against the actual analogue failures and the cost
of another pass. There is no literature-based requirement here for extra
modalities, new labels, fine-tuning, more model arms or another full extraction.
The comparison has a defensible precedent; whether it explains subsequent
Limburg high-water behaviour is what the pending results must establish.

## Review verification

The companion receipt records the source inventory and verifies that the 42
tracked extraction/aggregation/control files kept their hashes during this
documentation pass. No new empirical result or model-performance conclusion
was generated. Existing 307-test restart validation remains the preceding code
check, not a test suite rerun for these documentation edits. The generated
Mendeley bibliography was not hand-edited; these source links and the companion
inventory are the local literature supplement.
