# Foundation models for changing storm and catchment conditions

2026-10-15. Targeted primary-source review and internal advice, not dissertation
prose, an exhaustive census or an executed benchmark. No weights/images were
downloaded. [Idea 1](../limburg-ideas-2026-10-15.md) is saved and remains unrun.

## Assessment

There are credible complements to annual AlphaEarth. Dated EO representations
could describe changes in antecedent surface conditions. Their value for Limburg
wetness and event divergence must be tested; general mapping/flood-segmentation
benchmarks do not establish it. No model found here supplies verified hourly
storm forcing, subsurface state and river response together for these catchments
without additional adaptation.

AlphaEarth has not been established incapable of contributing. The held annual
product has different temporal support from a storm. The latest three-prong
run did not test it; earlier tasks found conditional/limited added value.
That does not rule out useful date-specific satellite information.

## Candidates

| Candidate and verified primary access | Relevant capability | Fit and limitation |
| --- | --- | --- |
| **OlmoEarth v1.2 Tiny**: [repository](https://github.com/allenai/olmoearth_pretrain), [export documentation](https://docs.olmoearth.allenai.org/embeddings/), [release history](https://docs.olmoearth.allenai.org/changelog/) | Spatiotemporal S1/S2 representation; documented 1–12-month context and several spatial resolutions. Tiny encoder ~12.5M parameters/192-dimensional vectors. | First practical EO candidate for monthly/seasonal antecedent surface condition. Weights/code and hosted exports exist; hosted access needs credentials. Custom artifact licence, not assumed Apache/MIT. No validated hourly wetness output. |
| **Galileo Nano/Tiny**: [ICML paper](https://arxiv.org/html/2502.09356v3), [code/weights](https://github.com/nasaharvest/galileo) | Masked multimodal encoder: SAR/optical sequences, terrain and climate inputs. Original encoders ~0.8M/5.3M parameters. Pretraining uses 24 monthly steps; ERA5 and TerraClimate variables are included. | Strong lightweight candidate for joint surface/climate context. Mask unused modalities rather than requiring every training source. Hourly RADOLAN is not a validated substitute for its monthly inputs. |
| **AnySat**: [paper](https://arxiv.org/abs/2412.14123), [code](https://github.com/gastruc/AnySat), [author model card](https://huggingface.co/g-astruc/AnySat/blob/689ccbbd582cedd770be5bcbb350ead5ee450779/README.md) | JEPA-style model for heterogeneous sensor scales/resolutions; dated S1/S2 sequences and additional Landsat modes. | Strong alternative when acquisition sequences and spatial flexibility matter. Requires imagery preparation. Flood segmentation performance does not establish soil-moisture or event-prediction skill. |
| **Presto**: [paper](https://arxiv.org/abs/2304.14065), [code](https://github.com/nasaharvest/presto) | Lightweight remote-sensing pixel-time-series encoder, usable for frozen feature extraction and simple downstream models. | Efficient seasonal-state reference; less spatial detail, not an hourly runoff model. |
| **TerraMind 1.0**: [code](https://github.com/IBM/terramind), [Copernicus embedding workflow](https://documentation.dataspace.copernicus.eu/APIs/openEO/openeo-community-examples/python/60_geospatial-embeddings/terramind/terramind-embedding.html) | Multimodal encoder/generative model with S1/S2 embedding access. The documented backbone is single-timestep; the example takes an annual median. | Dated scene encodings are plausible. Copying the annual example would repeat the temporal-averaging issue. Generated modalities are predictions, not independent measurements. |
| **Prithvi-EO-2.0**: [model card](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-600M-TL), [paper](https://arxiv.org/abs/2412.02732) | Multitemporal optical HLS encoder, 30m pretraining, 300M/600M variants. | Credible but heavier and cloud-limited; no SAR in this model's contract. A [2026 soil-moisture preprint](https://arxiv.org/abs/2602.18083) reports negligible embedding gain over handcrafted features in its specific task, cautioning against assumed advantage. |
| **CROMA**: [official code](https://github.com/antofuller/CROMA) | SAR, optical and joint encoders, with SAR-only inference and pooled/patch embeddings. | Useful radar-sensitive dated-state reference. Repeated encodings can measure representation change; the model is not itself a temporal hydrological model. |
| **Aurora + hydrological decoders**: [2026 journal paper](https://doi.org/10.1029/2025JH000837), [released checkpoint/code](https://github.com/lehmannfa/aurora-lite-decoder) | Frozen atmospheric latent states feed shallow heads for precipitation, evaporation, runoff and soil water. Published 6-hour/0.25-degree experiments; soil-moisture persistence is a strong baseline. | Direct weather–land-state research fit, but heavy atmospheric inputs/compute and coarse local support. Decoded runoff is not routed gauge Q. Repository describes older preprint settings: reconcile checkpoint/protocol before claiming journal reproduction. |
| **GraphRiverCast**: [2026 preprint](https://arxiv.org/html/2602.22293v1) | Topology-informed discharge/depth/storage model, CaMa-Flood pretraining; daily 15-arc-minute global and 6-arc-minute regional experiments. Future forcing is an input. | Conceptually relevant to connected-river relationships, but poor immediate temporal support for hourly small streams. Public usable checkpoint not verified in this review. Research lead, not ready download. |
| **HydroGEM**: [preprint](https://arxiv.org/abs/2512.14106), [author inference artifacts](https://huggingface.co/Ejokhan/HydroGEM) | Paired stage/Q anomaly detection and suggested reconstruction; inference checkpoint/tutorials, research/noncommercial licence. | Measurement-QA adjunct for held German pairs, not wetness/forecasting. Suggested repairs need review; genuine extremes must not be automatically replaced. Stage-derived Q is not independent stage validation. |
| **KG-Chronos-2**: [September 2026 preprint](https://arxiv.org/abs/2609.21381) | Frozen Chronos-2 with hydraulic-project graph, retrieval and fitted residual/correction components. Evaluates 64 fixed 24h windows from two held-out HEC-RAS simulations on shared geometry. | Interesting inspiration for combining a temporal model with checked river structure. It is a warm-start hydraulic surrogate, not a directly transferable gauge-only forecaster; 4,675 simulated sections are not independent real flood events. Released runnable artifacts were not verified here. |

The [streamflow foundation-model benchmark](https://doi.org/10.1088/3049-4753/ae4982)
supports temporal FM research but does not imply that another generic sequence
model adds EO surface-state information. Announced hydrological FM projects
also must be distinguished from released, usable pretrained artifacts.

## Candidates in the TUM perspective

The TUM-led [2026 perspective](https://doi.org/10.1038/s43247-025-03127-x)
is a design synthesis, not a hydrological performance ranking. Its journal
comparison explicitly discusses SatMAE, SkySense, SatlasPretrain and DOFA;
its [2024 precursor inventory](https://arxiv.org/html/2405.04285v1) also explicitly
lists Presto, CROMA and the original Prithvi. Distinguish those versions from
newer checkpoints and from models independently identified above.

| Candidate | Relevance to this chapter | Priority judgement |
| --- | --- | --- |
| Presto | Temporal pixel representations combine optical, SAR and environmental inputs. | Particularly useful lightweight starting point for antecedent-condition representations; not an hourly river model. |
| CROMA | Radar–optical representations, including radar-only inference. | Useful for comparing dated surface-condition encodings through cloudy periods; needs a separate temporal comparison. |
| SatMAE / Prithvi | Explicit temporal optical representations. | Credible alternatives; cloud availability and input cadence need checking. Original Prithvi in the precursor is not Prithvi-EO-2.0. |
| SkySense | Multimodal temporal representation and geolocation. | Strong conceptual fit; larger and more involved than the first probe should require. Runnable weights/configuration have not been validated locally. |
| DOFA | Flexible sensor/wavelength representations. | Relevant to heterogeneous sensors, but that flexibility does not by itself encode evolving catchment wetness or river response. |

These are task-fit judgements, not conclusions reported by TUM. The journal
also includes weather/nowcasting families (DGMR, NowcastNet, Pangu-Weather,
ClimaX and NeuralGCM). Their natural role would be storm forcing or atmospheric
context. Applying a regional radar nowcaster to hourly RADOLAN needs an explicit
cadence/domain-transfer assessment; a global atmospheric model is not a direct
replacement for small-catchment rain/Q histories. This is a separate option,
not another arm added to the current analysis.

A further TUM-lab lead is [Copernicus-FM](https://github.com/zhu-xlab/Copernicus-FM),
a DOFA extension with spectral/non-spectral modalities and flexible metadata
encoding, released weights and examples. This is a separately checked lab
resource, not asserted here to appear in the perspective's model comparison.
It merits an access/input-contract check alongside Galileo/AnySat if sensor
flexibility matters. A timestamp-aware encoder is not automatically a temporal
hydrological model. No download or benchmark was started.

## Important temporal check

[OlmoEarth's training archive](https://github.com/allenai/olmoearth_pretrain/blob/main/docs/Pretraining-Dataset.md)
also uses monthly mosaics. A [14-day live-fuel-moisture adaptation](https://github.com/allenai/olmoearth_projects/blob/main/docs/lfmc.md)
demonstrates a shorter-cadence application, but vegetation fuel moisture is
neither soil moisture nor runoff storage. Event-aligned shorter inputs would
be tested transfer, not an assumed pretrained capability.

Weather evolves over hours; satellite-observed antecedent surface condition
often changes over days/weeks. Keep radar/gauges for hourly storm/river dynamics.
SAR/optical embeddings could add information about surface water, vegetation
and state, but may instead encode season, roughness, land cover or sensor
geometry. They do not directly observe hourly subsurface saturation.

## Recommended research question

**Do pre-event satellite-observed departures from a catchment's usual surface
condition help distinguish events that look similar in rainfall and river history?**

This complements Idea 1 without asking an EO model to supply the whole forecast.
Start with one candidate: **OlmoEarth Tiny** for documented monthly export and
practical access, or **Galileo Tiny** for local flexible multimodal encoding.
AnySat is the strongest alternative if dated acquisitions/spatial context
become the key requirement. These are fit recommendations, not demonstrated
Limburg performance or a commitment to another model-comparison sweep.

Use the full cohort with usable pre-event imagery, recording unavailable cases.
Compare static context with within-catchment, season-adjusted embedding
departures, computing reference conditions from training years only. Test the
increment beyond rain/Q histories, season/date and simple optical/SAR features
on identical events. If an encoder receives climate inputs, compare with those
raw inputs too; otherwise an apparent representation gain may just be extra data.
An optional conventional soil-moisture product could help interpret results,
but is not a new prerequisite or ground truth for an embedding by definition.

Every input window must end by the assessment cutoff. A calendar-month composite
containing later days would leak future information. The hosted export contract
needs checking: use a completed prior month if necessary, or explicitly
truncated local inputs. Prior-month features do not measure wetting in the
last three days. Only a few partly nested catchments support spatial claims;
repeated events are more useful for testing temporal change than general
cross-basin transfer.

## Actual data/work implications

Held: annual AlphaEarth, terrain/catchments, hourly RADOLAN, gauge records and
ERA5-Land temperature/dewpoint/pressure. This review did not establish a held
event-aligned S1/S2 scene archive. Most EO candidates need open imagery pulls,
calibration/masking/alignment and frozen inference, not another agency email.
Historical Sentinel availability does not cover the complete 2010–2025 record;
retain a common observed subset and acquisition-age/cloud/revisit metadata.
AnySat's legacy Landsat support is an alternative, not automatically equivalent
coverage across models.

Aurora's published hydrological decoder requires multiple atmospheric variables
on pressure levels plus surface/static fields. Our three local ERA5-Land
variables are insufficient. Full initialization data and suitable compute are
additional work. [Aurora 1.5 is announced with hourly capability](https://www.microsoft.com/en-us/research/project/aurora-forecasting/faq/),
but this review did not verify a released configuration reproducing the cited
hydrological decoder experiment. It is not the proposed first test.

No candidate has been executed locally in this review. If selected, the next
action is input/coverage auditing and a frozen-encoder smoke test, followed by
a complete matched-event evaluation rather than a few favorable illustrations.
