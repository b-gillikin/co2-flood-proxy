# Three passes from the research problem: potential Limburg paths

13 November 2026. Internal research aid. Brian asked for three passes through problem → literature gap → consequential question → evidence/method fit → challenge/defence before choosing a proportionate study. This starts again from the problem. Local adaptation, annotation strategies, a ten-encoder comparison, RAG, particular foundation models and the recently acquired imagery are not commitments. No experiment, pilot, download, request, queue or RQ change was implemented.

These are three complete conceptual passes, with different starting points. The outcomes are candidate paths and comparative judgments, not three studies to execute. The literature check is targeted, not exhaustive; the proposed empirical gaps are hypotheses about worthwhile contributions, not verified claims of being first.

## Pass 1 — Start with the information needed during an unfolding event

### Problem

For a forecaster on a small international river, another station can contain advance information about a developing wave. The substantive issue is the value and timing of that information along a physically connected reach, rather than whether a representation can find similar historical rivers.

### Literature and what remains worth asking

Busker et al. (2026) documents regional FEWS arrangements and says hydrological data exchange is already well organized; the WVER public portal itself includes Dutch Wurm/Rimburg as well as German stations. We therefore reject an initial framing that Dutch and German agencies simply fail to share gauge data. A receiving-agency information comparison could still quantify the incremental value of particular observations and the sensitivity to delay, but would not identify the causal effect of existing cooperation or prove a current operational shortcoming.

Kirschstein and Sun (ICML 2024) shows that adding river topology to neural forecasts need not help. Thus neither a network model nor an AI advantage should be presumed. The JCAR Rur system description inventories existing Wurm/Rur models; this is an already modeled basin, not a modeling vacuum. Any claim of superiority over an operational service would need its actual forecasts, not merely our home-built baseline.

Sources:
- https://nhess.copernicus.org/articles/26/1457/2026/nhess-26-1457-2026.html
- https://wver.de/karten_messwerte/Messdatenportal/aktuelle_Werte_Pegel.html
- https://arxiv.org/abs/2405.19836
- https://www.jcar-atrace.eu/_default_upload_bucket/jcar-atrace-stress-testrur010scoping-and-system-understanding_final_1.pdf

### Candidate A: the warning-information value of a connected cross-border reach

**Question:** When does an upstream observation add useful advance information about high water farther downstream, and how quickly does that value disappear as the observation gets older?

A plausible receiving application is the Wurm/Worm chain including Herzogenrath, Rimburg and Randerath. Exact station order, tributary junctions and usable overlapping periods would need reconciliation before any model design. These are gauges on one connected river system, not three independent catchments. Herzogenrath 2 is Broicher Bach, not another Wurm mainstem gauge; Honsdorf is Beeckfließ.

**Why an answer could matter:** it could quantify which existing feeds deserve reliable integration and low latency, and where upstream observations buy little additional time beyond the local gauge. This can inform monitoring/data-service priorities. It does not establish that an authority currently lacks the feed, that a prediction is timely enough for evacuation, or that improved predictions save lives.

**Data fit:** long local discharge, German stage/discharge, RADOLAN rainfall, rating histories and provider notes are held. Dutch Rimburg discharge has documented July 2021 rating-domain exceedance; German post-2021 extreme discharge is provisional. A German downstream **stage** target may avoid using provisional extreme discharge as exact truth, subject to stage continuity/era checks. Historic receipt timestamps are not held; imposed delays would be explicit scenarios, not reconstructed outages. Historical stage thresholds and comparable bankfull levels must not be assumed available.

**Proportionate method, if selected:** one physically connected reach, a short-range past-observation forecasting task, a simple lag/routing or regression alternative and one suitably chosen sequence-learning alternative. Compare information sets and usable forecast horizons. No new encoder collection, hydrodynamic solver or GNN is implied. This is a concept, not a chosen horizon/model protocol.

**Strongest objection:** upstream observations helping downstream forecasts is established hydrology, and sophisticated existing services may already exploit it. The short reach may offer little extra lead. A generic improvement would be a weak novelty claim.

**Strongest defence:** the potentially useful empirical result is the incremental value, limits and latency sensitivity of identified cross-border observations under extreme conditions, beyond a strong local baseline. It may be small or absent. The information/service question is different from merely comparing predictor accuracy. Whether the regional estimate would be consequential remains unresolved; we cannot infer it from correlations or promise an AI advantage.

**What would distinguish it from previous attempts:** the October storm-response analysis tested all directed gauge pairs using realized future rainfall and a 72-hour conditional response; it found no generally useful peer increment. Earlier analogue/discharge experiments are also completed negative or mixed evidence. A past-only, verified upstream/downstream reach comparison is a different estimand, but these earlier results lower confidence and must be disclosed. The new study must not be sold as something no one has tried simply because it uses another name.

**Pass-1 judgment:** best current balance of data fit, specific FEWS use and manageable scope. Worth conceptual consideration, not ready for a run or a claim of novelty.

## Pass 2 — Start with a scientific failure that can harm flood information

### Problem

An automated quality-control system can mistake a genuine rapid flood rise for a sensor problem. It can also accept a bad reading as evidence of a flood. These errors have opposite practical consequences. A model that calls all unusual measurements anomalies does not solve this distinction.

### Literature and what remains worth asking

Kuhaneswaran et al. (2026) explicitly separates erroneous outliers from legitimate extremes, but its validation injects faults into daily gauge series. That is a direct precedent, not an empty gap. It suggests a potentially valuable regional extension focused on subdaily flood dynamics and independent failure evidence, rather than another anomaly-detector tournament. A nearby October 2026 low-cost water-level study is especially relevant because its abstract reports difficulty for ML during hydrological events. Its publisher abstract was inspected, but the full text was blocked; treat its detailed methods as unreviewed.

Sources:
- https://www.mdpi.com/2073-4441/18/4/446
- https://doi.org/10.1016/j.hydroa.2026.100228 (publisher full text inaccessible during this pass)

### Candidate B: protecting flood signals during automated quality control

**Question:** Can a monitoring system flag faulty gauge readings without suppressing genuine flood extremes, and does nearby-gauge/rainfall context help?

**Why an answer could matter:** a defensible review flag could preserve critical high-water information while directing an analyst toward genuinely suspect readings. The output would initially be a flagged observation, not automatic deletion or an issued public warning. Quantities of interest include genuine extreme observations incorrectly flagged and independently documented faults missed, rather than only aggregate anomaly accuracy.

**Data fit:** long subdaily records and provider-specific failure/rating notes are held. However, they are not a comprehensive pointwise fault-label collection. René confirms zeros are genuine zero flow. Jens confirms that German final series can use redundant sensors at the same station, not neighboring-gauge reconstruction. The delivered archive can therefore hide primary-sensor faults; individual substitutions are not flagged. Uncertain high-flow rating relations are not the same as failed stage sensors. A synthetic-fault benchmark is possible with held data, but cannot demonstrate detection of real, previously unlabelled failures.

**Additional evidence that would materially improve this path:** a bounded set of confirmed faults, sensor substitution intervals or retained primary/backup streams, ideally spanning genuine flood rises as well as ordinary conditions. This is a possible future acquisition path, not an email sent or a new request requirement imposed on the dissertation. Sparse documentary episodes can support cases; they cannot be silently promoted to a comprehensive labeled benchmark.

**Proportionate method, if selected:** a conventional provider-relevant screening rule against one contextual learning approach, tested on untouched genuine extreme episodes and independently adjudicated faults where available. Synthetic perturbations could supplement those tests with explicit scope. No requirement for a foundation model, 13-detector comparison or downstream forecast experiment.

**Strongest objection:** without verified failures, we may build a classifier that recognizes our own artificial glitches. The archive has already been cleaned and sensor-substituted. A full real-world fault-detection claim is currently less well supported than Candidate A's forecasting target.

**Strongest defence:** this directly addresses the reliability of the information FEWS consumes and uses the provider-specific measurement knowledge already gathered. A focused real-error/real-extreme study could be more substantive than forcing another small average prediction gain. The contribution would be application-specific evidence and failure analysis, not inventing anomaly detection. Lack of comprehensive labels limits the claim; it is not proof that the topic is unworthy.

**Pass-2 judgment:** a distinct, practically meaningful candidate, with the clearest additional-evidence need. Keep it as a serious alternative. Do not start a full study on synthetic faults and retrospectively describe it as validated operational QA.

## Pass 3 — Start with what can be observed, while challenging the urge to reuse assets

### Problem

An algorithm evaluated only when a suitable satellite image and reference map exist can have a favorable score while offering little information during brief floods. Missing coverage, invisible water and algorithmic mistakes require different responses.

### Literature and what remains worth asking

Tarpanelli et al. (2022) already evaluates European Sentinel flood-observation opportunities. Prince et al. (2025) directly assesses coincidence between high flows and satellite acquisitions for synthetic map suitability. Thus “satellites sometimes miss floods” is established and would not be a sufficient new contribution. Regional work could still quantify end-to-end availability versus conditional mapping performance for an explicit response purpose. Whether that regional evidence changes a monitoring choice, rather than restating a known limitation, remains unestablished.

Sources:
- https://nhess.copernicus.org/articles/22/2473/2022/
- https://repository.library.noaa.gov/view/noaa/72796

### Candidate C: which high-water situations satellite AI actually covers

**Question:** Across the full regional high-water record, which events can satellite AI provide information about, when, and which remain unobserved despite good image-level scores?

**Why an answer could matter:** a mapping organization could distinguish conditions for satellite mapping from conditions needing other observation/verification. The implied choice is monitoring complementarity, not upgrading the encoder. Gauges alone do not locate inundation and satellite maps do not replace live gauge forecasting.

**Data fit:** the gauge chronology, acquired imagery/metadata, existing mapping outputs and July 2021 references are valuable. But the image archive is selected; it is not a complete account of every relevant acquisition. A complete opportunity census would need public catalogue coverage and cloud/validity checks over a declared overlap period. The broad high-water ledger is not a ledger of confirmed physical inundation. Pixel accuracy for every gauge episode is not verifiable from the held maps. Acquisition time does not establish when a product was available to an agency.

**Proportionate method, if selected:** regional opportunity/phase accounting plus existing fixed-mapper case evidence, clearly separating high-water events from independently documented floods. No new model training is intrinsically necessary. One episode with several image acquisitions remains one episode. Do not infer hydraulic connection or flood extent from a high percentile at a remote gauge.

**Strongest objection:** this overlaps closely with prior work and may be a valuable supporting analysis or short methods/application paper, rather than the substantive new AI chapter Brian seeks. The large existing EO investment is a tempting but scientifically irrelevant reason to choose it.

**Strongest defence:** coverage failures can be more consequential than small differences in conditional IoU. Quantifying a complete regional denominator and explicit timing/unknown support could be useful. That usefulness still needs an identifiable receiving task; it is not created by adding roads/population overlays, more sensors, or a new timing metric.

**Pass-3 judgment:** useful supporting/application candidate; currently weaker than A/B as a standalone chapter direction. Do not elevate it simply to reuse the EO runs.

## Other paths considered and not promoted

- New floodwater/peak-footprint reconstruction from late imagery: a different physical target, with insufficient independent temporal extent truth currently held; risks recreating the prior reference-policy problem.
- More EO encoders, new adaptation/allocation variants or another analogue formulation: do not begin from a demonstrated unmet substantive problem and would inherit considerable overlap with completed work.
- A general cross-country warning taxonomy/RAG system: the regional institutional comparison is already directly covered by Busker et al.; no automatic return to the four-arm RAG study that Brian rejected.
- A confluence/backwater causal explanation: hydrologically interesting, but held regional timing/Q alone does not identify local backwater. Existing Meuse context is not new hydraulic evidence. It would need a different evidence base and could overlap Peja's hydraulic work.
- Generic forecast-performance leaderboard: does not by itself supply the agency information question or a distinct contribution.

These are judgments about current fit, not permanent bans or claims that the topics cannot support good research.

## Comparison after three passes

| Candidate | Most credible contribution candidate | Current evidence fit | Main unresolved issue | Relative assessment |
| --- | --- | --- | --- | --- |
| A. Connected cross-border observation value | Incremental advance information and its latency sensitivity on a verified reach | Strongest: continuous hydrometeorological data, with important quality qualifications | Added value over a strong local/routing baseline, prior-literature overlap and actual short reach/horizon | First to discuss, not selected |
| B. Flood-preserving quality control | Distinguishing real measurement faults from legitimate extremes using hydrological context | Partial: excellent trajectories and provider notes; incomplete fault identities | Confirmed failures/backup streams versus merely synthetic validation | Serious alternative with evidence acquisition need |
| C. End-to-end satellite coverage | Conditional mapping skill versus information availability across a regional event denominator | Partial: many assets, incomplete full opportunity/physical-flood truth | Close prior art and whether it answers a consequential regional choice | Supporting or reserve path |

None is declared first-of-kind, publication-ready or guaranteed to produce a favorable result. A useful null result is possible if the comparison is specific and convincing. A null on a vague or redundant question remains weak. AI is a candidate means, not a compulsory treatment that must outperform.

No three-path programme is proposed. Before choosing, discuss which substantive problem is worth solving, taking the objections and their defences together. The next decision is conceptual, not authorization to launch another pilot or computational queue. The earlier study and all acquired material remain preserved; sunk costs carry no weight in selecting the next direction.

## Evidence and provenance used

Held records inspected: current response-mapping plan/audit and validity consolidation; local support and acquisition receipts; LANUK 13 October clarification; Waterschap source/QC metadata; October storm-response results (including the negative conditional peer-state comparison); completed discharge readout; Meuse context; existing monitoring scenario specification. These were read to identify evidence and avoid repeating a completed study, not to let the available files dictate the question.

Primary online records inspected for this reassessment: Busker 2026 full article and exchange discussion; Kirschstein/Sun abstract and author/proceedings PDF excerpts; WVER live station portal; JCAR Rur report relevant system/model sections; Kuhaneswaran 2026 methods including synthetic validation; Tarpanelli 2022 article; Prince 2025 NOAA primary record/abstract. The October 2026 low-cost QA paper is abstract-only because publisher full text returned 403. No claim of exhaustive novelty clearance or full-text review of every search hit.
