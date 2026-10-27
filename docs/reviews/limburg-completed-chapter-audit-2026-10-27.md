# Limburg completed-chapter audit — 27 October 2026

Internal scientific and implementation review for Brian; not dissertation prose.
No empirical result, encoder, donor rule, threshold or completed run was changed.

## Assessment

The chapter has a scientifically defensible core: a retrospective study of whether
learned representations retrieve useful historical high-water analogues beyond
transparent hydrological references. It has completed, internally consistent
outputs. It is not an architecture-only EO leaderboard, a validated flood-warning
system, or a causal explanation of catchment response. The remaining priorities
are better benchmark coverage, direct comparisons across input routes, explicit
support/uncertainty reporting, and a much tighter presentation of the evidence.

No finding in this audit justifies abandoning the chapter, requiring another
large imagery collection, or restarting all ten encoder extractions. Some useful
follow-up calculations use the existing inputs and outputs. Proposed work below
is not represented as already executed or as a new blanket gate.

## What was reviewed and checked

- Current RQ, one-pager, active design, evidence index, earlier analogue/
  distribution/storm-response/threshold analyses, current protocols, source notes
  and model-selection history.
- All **91 bibliography entries** for relevance and inherited directions; the
  detailed model/method literature layer includes the **15 held primary documents**
  from the October 22 review, associated papers/appendices and pinned official
  README/model-card/input documentation for all ten encoders. This is a targeted
  chapter audit, not a new systematic review or a claim that every inherited
  bibliography item was reread cover to cover. Inactive CO2, case-crossover and
  RAG references remain historical context, not active scientific components.
- TTM/AlphaEarth preparation; checkpoint loading; model-specific transforms,
  temporal readouts, masks and dates; acquisition/staging; exact-area aggregation;
  retrieval, donor eligibility, scoring, bootstrap and automated review code.
- Main comparison and all four supplemental comparison/review manifests,
  all selected-run contracts and recorded final input/output hashes: **149 unique
  files hashed, zero mismatches**, all selected models verified. This does not
  rehash every raw raster and every millions-of-patches payload; their earlier
  acquisition/extraction/aggregation validation remains part of the provenance chain.
- Full suite: initially 310 passed/9 failed because the test environment lacked a
  configured PROJ database. Repeating with the existing installed database gave
  **319 passed in 34.39 s**, with no package or model-environment changes.
- Additional primary-source searches on embedding aggregation, hydrological
  analogues, event diagnostics, catchment descriptors and evaluation. See the
  source section below. New evidence was not used to select favorable settings.

Read-only reproduction: script `134_audit_completed_limburg.py`, using the existing
foundation environment and `PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj`.
The compact results are in `completed-audit-2026-10-27/integrity-evidence.json`.
The bibliography inventory and audit-time source snapshot sit beside it. The
source snapshot does not retroactively certify missing run-time dependency hashes.

## Priority findings

### H1. Remove the inherited 512-hour rainfall completeness restriction from the conventional benchmark in a separately labelled follow-up

The conventional signature's longest rainfall feature uses **168 hours**, but
`84_complete_cross_border_analogues.py:add_rain_signatures` requires all **512
hours** of rainfall, and script 102 imports that restriction into `rain_ids`.
In the 851 Q-eligible events, **836 have every actual conventional predictor**,
but only **770** satisfy the inherited longer-rain-history rule: **66 avoidable
exclusions**. This is measured on the held prepared inputs, not an estimate of
how many additional cases each EO model would gain.

The current paired results remain valid for their declared restricted cohort.
The restriction is not a measurement or leakage requirement for a 168-hour
predictor. Preserve the completed analysis; use actual feature completeness in a
separate corrected benchmark pass and report the population change. No new
rainfall download or neural inference is needed. Do not silently broaden the
old result's denominator.

### H2. Establish the generic historical reference on the exact EO populations

Earlier script-82 work found that good individual analogues did not reliably
beat generic eligible-archive averaging for duration or whole-curve estimates.
The new script-102 arm dictionary contains conventional/raw/TTM and context
controls, but not that generic whole-response reference. A peak-only expanding
median is present in the retrieval records; that is not the same comparator.

An improvement over TTM alone therefore does not establish that targeted retrieval
beats a simple archive summary. Reuse the earlier group-balanced archive logic
on each exact EO query/donor population, with the same chronology and storm
constraints. This is a small downstream analysis, not another embedding run.
Retain the distinction between mean individual-donor similarity and the accuracy
of an ensemble-mean trajectory.

### H3. Treat supplemental comparisons as source/support sensitivities, not direct evidence that an encoder improved

The routes change usable dates, spatial masks, complete sequences, donor archives
and in some cases reflectance level or normalization support together.

| Representation availability before donor restrictions | Snapshot | Twelve monthly frames | Four weekly frames |
| --- | ---: | ---: | ---: |
| Main SatMAE | 485 | 380 | 269 |
| Supplemental SatMAE TOA/QA60 | 366 | 78 | 128 |
| Main Copernicus-FM | 485 | 380 | 281 |
| Supplemental Copernicus-FM TOA/QA60 | 366 | 78 | 135 |
| Main CROMA orbit 88 | 576 | 437 | 243 |
| Supplemental CROMA orbit 15 | 16 | 1 | 0 |
| Supplemental CROMA orbit 161 | 56 | 44 | 14 |

Orbit 15 has **14 scored snapshot queries** in its main pooled/all-river/five-donor
EO-only available cohort (7 NL/7 DE), and no scored annual or weekly cohort in
that configuration. Orbit 161's corresponding scored cohorts are NL-only:
55 snapshot, 43 annual and 13 weekly queries. These are support findings,
not performance verdicts and not universal minimum-sample rules.

The TOA annual cohorts are also NL-only in that main available configuration.
The supplemental all-ten weekly intersection is only **19** available events for
the TOA replacements, **0** for orbit 15 and **8** for orbit 161. A completed
supplemental review's 656 unique queries includes unchanged model arms: it does
not mean 656 queries were evaluated with the changed representation.

Required interpretation step: intersect query IDs **and eligible donor pools**
between the main and each supplemental route for a direct contrast. Current
within-run matched comparisons are sound but do not do that cross-run analysis.
If donor pools differ, either replay retrieval on the common pool or report the
result as an end-to-end coverage/application difference. Common query IDs and
equal donor counts alone do not isolate the input change. No encoder rerun is
needed for this distinction. Orbit 15 remains a limited case/support result.

### H4. The claim 'identify when evidence is too uncertain to use' needs an explicit meaning

The chapter already identifies unavailable histories, missing observations,
provisional measurements and weak donor support. Those are defensible evidence
limitations. It also computes donor spreads/ranges and phase shares, but the EO
comparison does not establish a calibrated uncertainty-triggered abstention rule
or an operator's acceptable risk level.

Keep the RQ if 'too uncertain' means documented applicability and reliability
limits. For stronger claims, test spread versus realized error and empirical
coverage using saved outputs, preserving previous distributional-analysis
limitations. Do not call a narrow analogue spread a reliable probability or an
operational safe-to-use criterion. No new human interviews are required.

### H5. Missingness and imagery state are competing explanations

Snapshot all-ten availability is **479/851** eligible events; twelve-month is
**356/851**; four-week is **103/851**, all before chronological donor availability.
The review's 5,656,500 main assessment rows are repeated configurations, not
millions of independent observations. The main review has **656 unique scored
queries across the union of arms/readouts**.

Keeping the full event inventory is good practice, but the scored EO subset is
not the full high-water census and is not necessarily weather-neutral. Cloud,
snow, acquisition cadence and archive year affect inclusion and observed area.
Report availability by country, river, year/season and measurement status;
compare performance on shared cases, not differing model averages. The full
catchment remains the coverage denominator; do not impose an arbitrary area
cutoff merely to hide incomplete scenes.

## Further scientific and reporting findings

### M1. These are complete representation pipelines, not controlled architecture comparisons

Input sensor (SAR/S2/HLS), reflectance level, modality subset, native footprint,
checkpoint size, time support, missing-data handling and pooling differ.
Prithvi's 224 pixels at 30 m cover a **6.72 km** square; Galileo's 32 pixels at
10 m cover **0.32 km**. Exact-area weighting correctly assigns patch contributions,
but cannot remove outside-catchment context already encoded in a patch vector.
Call them observed-area-weighted contextual catchment representations. A winner
is a useful pipeline under this design, not the best universal architecture.

### M2. Raw EO/statistical and seasonal references would strengthen attribution

The practical hydrology benchmark and raw-hydrograph control are valuable, but
neither controls for extra EO input. The area and identity controls also do not
separate spectral information from pretrained representation value. A compact
same-support spectral/index or acquisition/season reference would help if the
chapter claims a specifically learned EO advantage. This can use held inputs;
no additional model zoo or satellite product is required. Until then, describe
EO-route utility without claiming that pretraining caused the gain.

### M3. Absolute embeddings are not measured wetness anomalies

The experiment compares window representations; it does not explicitly compute
departures from a catchment's usual same-season surface state, nor validate a
soil-moisture decoder. Individual axes have no named physical meaning. The older
shortlist's proposed 'departures from usual condition' question is therefore a
hypothesis/idea, not what the completed pipeline directly estimates. Retain the
broader analogue RQ; explain potential mechanisms without claiming they were
identified. A later cached-vector within-catchment seasonal/anomaly diagnostic
is possible if warranted, not a new mandatory modelling programme.

### M4. Query time, retrospectivity and target must remain explicit

Inputs are chronological and prior donor responses must be complete before the
query. This is a substantial safeguard. Nevertheless, full-rating-era p99
normalization/selection is retrospective; completed-image windows are not the
same as historically published products; pretrained models may have seen these
regions/years. None invalidates a retrospective representation study. Together
they prevent claiming a reconstructed as-issued forecast evaluation. Current
warning thresholds applied to historical records do not recreate historical
warning decisions. Q/p99 exceedance is high discharge, not verified inundation.

### M5. Country contrasts are not independent national treatments

There are eight gauges and **six physical river groups**. The two DE sites and
one NL site lie on the Wurm/Worm. Country contrasts are entangled with river
identity, nested network position, archive lengths, measurement/rating histories
and available imagery. Keep pooled/domestic/foreign and other-river contrasts,
but report them as this archive's transfer evidence. The code correctly treats
all Wurm gauges as one physical river for other-river exclusion. More event rows
do not provide more independent catchments or countries.

### M6. Uncertainty intervals are conditional, exploratory and numerous

The main run contains **476,784 paired-interval rows**, spanning metrics,
populations, models, countries, donor rules and two resampling units. These are
not independent confirmations. Query-storm/year block bootstrap is appropriate
for important dependence, but does not propagate all rating uncertainty,
pretraining exposure, reused-donor dependence or the long outcome-informed design
history. Some supplemental strata have one query/cluster; the code correctly
leaves intervals undefined instead of inventing them.

Organize a small reporting hierarchy by hydrological question, show effect sizes
and both bootstrap sensitivities, and identify exploratory comparisons. Do not
select the most favorable model/metric/cohort or claim a prespecified confirmatory
winner after seeing results. Formal preregistration or a new untouched dataset
is not a prerequisite for reporting this explicitly exploratory work.

### M7. Shape, level, duration and flood escalation answer different questions

Peak-normalized shape intentionally removes amplitude; Q/p99 level metrics use
a relative high-flow scale; timing uses a fixed 72 h window. Shapes can match
while severity or mean-trajectory estimates are poor. Peaks can be truncated at
72 h, so describe within-window peaks/duration rather than whole flood duration.
Generic recovery in a p99-triggered sample can look useful without event-specific
information. Keep prior threshold-progression and rainfall-defined nonresponse
work as supporting evidence, not additional competing chapter cores.

### M8. Frozen inference is valid but reduced use of some models

The model-specific review below supports the current configurations as declared
transfer experiments. It does not certify their optimality. Copernicus-FM uses
supported unknown metadata, not its location/time/area capabilities; Presto keeps
only spatial means, unlike some published mean-plus-SD applications. Fixed frame
means for snapshot backbones discard ordering. Poor results in these routes do
not establish that the whole family or full fine-tuning would fail. Conversely,
these optional capabilities are not reasons to require another large extraction.

### M9. Mean imputation plus observed-area weighting is not native missing-token masking

Galileo/OlmoEarth have explicit token-support treatments; Presto uses masks.
Several other adapters place neutral/mean values in unavailable pixels and encode
the whole patch. The resulting feature can depend on the missingness pattern,
even when its catchment weight uses actual observed area. This is documented
input adaptation, not proof of cloud invariance. Coverage/season controls and
actual-match inspection should determine whether useful patterns survive.

### M10. 'Basin-aware' currently means grounded inputs and retrieval constraints, not a learned river network

River grouping, mapped catchments, measurement provenance and country/river donor
policies ground the analysis. The EO/TTM retrieval does not learn a routed river
graph or estimate upstream-to-downstream propagation. Cross-river analogues are
historical precedents, not proof that one tributary caused another's rise. Keep
the separate storm/peer-response work as supporting evidence and explain the
meaning of basin-aware plainly. No GNN, RAG or new Maas main-stem module is
required to make the current retrospective question valid.

### M11. Complete-slot selection is conservative, not the only scientifically valid missing-data policy

The extractor requires a local file in every calendar slot and some observed
pixels in every patch frame. This is transparent and avoids inventing scenes,
but native masked temporal encoders can support some missing observations.
The current complete-slot study is valid for its declared population; do not
state that every rejected sequence is intrinsically impossible to represent.
If support loss becomes the substantive limitation, a separately labelled
mask-aware partial-sequence sensitivity could use existing data, with explicit
nominal time support, actual observation masks and model-specific compatibility.
It must not turn missing imagery into observed values or silently replace the
completed complete-slot result. This is an optional way to broaden evidence,
not a required rerun or another collection gate. Snapshot backbones and temporal
encoders need not have identical missing-sequence capabilities.

## Concrete implementation/documentation findings

### I1. Generated browser provenance text is wrong for supplemental runs

`120_review_eo_analogues.py:input_note` uses one `coherent` flag and hard-coded
text saying additional Azure imagery is not included and three native-product
models are reused. That text appears in **all four supplemental browsers** even
though they use the supplemental archive. It is also inaccurate about reuse in
the main corrected run: only Prithvi and repaired OlmoEarth were reused; CROMA
was re-extracted with its corrected transform.

This is a presentation/provenance defect, not a discovered score-calculation
error. Fix the note from the selected contract and actual sensitivity identity,
then regenerate the review artifacts with new review manifests. Preserve the old
outputs or metadata compatibility record. It does not require rescoring or
re-extracting all models. Do this before sharing the browser externally.

### I2. Published scoring manifests omit some transitively executed numerical sources

Script 102 records scripts 65/84 and selected local modules, but its executed
import chain also reaches scripts 64, 73, 74, 75, 78, 80, 81, 82 and 83. Several
supply metrics, phase evidence and bootstrap behavior; their hashes are absent
from the main scoring input list. Retrieval-cache manifests cover additional
sources but do not replace a complete final run contract. Current tests and
file hashes are clean; this finding is not evidence of altered past results.

Capture the numerical dependency closure in the next run manifest and retain
an audit-time source snapshot for the existing runs, clearly dated. Do not
retroactively label the snapshot as contemporaneous run-time proof.

### I3. Selection-map persistence needed strengthening (addressed in this audit)

`config/limburg_eo_coherent_selected_runs.json` exists locally but is not committed.
The four supplemental maps are under `logs/eo-expansion-comparisons`. Final plans
also retain their selected contracts, so the information is not lost, but the
handoff is more fragile than necessary. This audit versions the existing corrected map and exact byte copies of the four
supplemental maps under `config/limburg_eo_supplemental_selected_runs/`; original
logged maps and completed manifests remain unchanged. None contains raw provider
discharge or imagery.

### I4. Current entry points still narrate earlier execution states

The living one-pager is updated, but README/active-design and source-note sections
still include 'extracting', original-route reuse and predecessor CO2/RAG evidence
questions. Dated history is legitimate; it needs a clear current evidence/reading
map at the top. Do not rewrite historical decisions or reintroduce them as active
requirements. Keep the 91-entry library, but distinguish the active scientific
spine from historical sources in the writing plan.

### I5. Prior failure modes are repaired, not hidden

The NumPy controller environment, fixed empty orbit-test months, singleton/
constant-channel CROMA normalization and retired mixed-day/normalization runs
have explicit records. Both radar routes completed with the versioned support
rule. Preserve original observed versus encoder-usable support in reporting;
mathematical normalization support is not an arbitrary coverage gate. Do not
reuse failed/retired runs. No fresh implementation defect requiring a full
encoder restart was demonstrated by this audit.

## Model-by-model documentation assessment

| Model/checkpoint and executed route | Documentation alignment | Limit to carry into the chapter |
| --- | --- | --- |
| TTM-R2 512-96 backbone, ordered readout plus Q state | Pinned hidden states; forecasting head not used; raw-history control and complete 512-hour input exist. | Retrieval is a new downstream use, not validated by forecasting benchmark scores. Pretraining includes related domains; downstream chronology is not pretraining independence. |
| AlphaEarth annual, prior year | Avoids same-year imagery look-ahead; fixed 64-band catchment descriptor. | Annual context, not hourly storm state; small catchment/year support; annual means lose heterogeneity. |
| OlmoEarth v1.2 Tiny, SAR | Correct version, timestamps, native token masks and pooling; repaired run explicitly reused. | SAR-only/declared cadence, not the full multimodal model; optional modalities are not missing requirements. |
| Galileo Nano, S2 | Published normalizer, month encoding and fully observed token support; metadata file bound. | Climate/static groups absent; conservative token masks and monthly-to-weekly transfer change support. |
| AnySat base, S2 | Correct executable-demo date convention, normalization and metre-valued patch argument. | README/demo date convention conflict is documented; representative patch date is not every pixel's scene time; partial pixels are neutral-filled. |
| Prithvi EO 2.0 Tiny TL, HLS | Six bands/units, coordinates, date input and dynamic frame handling reviewed; no missing trained backbone keys. | Tiny is not the published 300M/600M model; 12-frame transfer is not original four-frame pretraining; large patch context. |
| CROMA base SAR, orbits separate | Corrected publisher stretch/quantization and /255; sample-SD support rule documented for supplemental routes. | Per-patch stretch removes absolute backscatter scale; two orbits supply limited alternate support, not a fused radar series. |
| DOFA v1 base e100, six non-TCI bands | Source/checkpoint matched; wavelength and Satlas-format conversions explicit; no fabricated RGB. | Reduced band route; not DOFA v2 or all-sensor inference; SR transfer does not isolate architecture. |
| Copernicus-FM base, S2 | Supported normalization and patch readout; only documented deterministic output LayerNorm defaults permitted. | Unknown metadata is a reduced configuration; TOA plus QA support differs jointly from main SR. |
| TerraMind 1.0 Tiny, S2 L2A | Selected band weights and external normalization match pinned source; trained keys load strictly. | Single-frame backbone with equal-frame summary; no generative/TiM result or temporal attention claimed. |
| Presto, S2 pixel sequences | Official helper, absent-input masks and actual per-pixel months; batched inference. | Spatial mean omits variation; weekly cadence is transferred, not native monthly training; locations may encode identity. |
| SatMAE multispectral base e199 | Multispectral checkpoint, bands, 96-pixel size and corrected executable transform match. | Not temporal-RGB SatMAE; time mean is order-invariant; TOA/QA60 changes support and input domain. |

## Literature assessment and new useful leads

The literature supports the task, but no source guarantees that an EO embedding
captures hydrological wetness or improves this particular retrieval problem.
Keep the evidence chain explicit: observation -> representation -> retrieval ->
withheld response relevance -> potential future use.

- The [TUM-led foundations perspective](https://doi.org/10.1038/s43247-025-03127-x),
  PANGAEA and [GEO-Bench-2](https://arxiv.org/abs/2511.15658) support capability-aware
  evaluation. Their benchmark rankings do not select the best Limburg encoder.
- [Corley et al., CVPRW 2024](https://openaccess.thecvf.com/content/CVPR2024W/PBVS/html/Corley_Revisiting_Pre-trained_Remote_Sensing_Model_Benchmarks_Resizing_and_Normalization_Matters_CVPRW_2024_paper.html)
  supports checkpoint-specific preprocessing and strong simple image baselines.
- [Liu et al., GRL 2026](https://doi.org/10.1029/2026GL122814) is close precedent
  for spatially pooled embeddings as catchment descriptors. Its learned rainfall–
  runoff model and spatial-transfer design differ from event-analogue retrieval;
  neither its advantages nor its model ranking transfers automatically here.
- [Wendi et al., WRR 2019](https://doi.org/10.1029/2018WR024111) and the held
  flood-process/July-2021/observation-uncertainty studies support hydrograph
  similarity and separate shape/timing/amplitude interpretation. They do not
  imply a numerical p99 crossing is an inundation observation.
- **New:** [Corley et al., 2026 v2, ML4RS workshop](https://arxiv.org/abs/2603.02080v2)
  tests aggregation of fixed pixel embeddings for land-cover classification.
  Distributional pooling helps spatial transfer there. It supports treating our
  mean pooling as a substantive choice, not declaring it invalid or importing
  its gains into hydrology. Its pixel-embedding setting differs from averaging
  contextual patch vectors. The author's older landing page recommends GeM;
  v2 instead emphasizes mean/statistics/covariance tiers. Use the versioned paper.
  PDF and hash receipt saved under `data/raw/foundation_assets/documents/audit-2026-10-27`.
- **New:** [Alam et al., JAWRA 2026](https://doi.org/10.1111/1752-1688.70093)
  provides an event-focused model-agnostic evaluation framework. It reinforces
  event diagnostics beyond average model fit; no adoption of its US data or full
  tooling is needed.
- [Ullrich et al., 2025](https://doi.org/10.1029/2024JH000496) supports broader
  evaluation, provenance and credibility checks; passing unit tests is only one
  part of scientific validation.

The direct literature gap is a task-specific evidence gap about useful/failing
cross-tributary historical precedents with measured context and provenance. The
claim should rest on demonstrated contrasts and event insight, not 'first use of
model X in Limburg' or collecting ten models. The novelty is applied and
comparative; no first-ever or architecture-invention claim is needed.

## Scope and recommended next work

1. Correct browser provenance and preserve the complete small run/source bundle.
2. Produce one support-aware interpretation pass: distinguish model-available,
   all-ten matched and cross-route common populations; inspect genuine useful
   and misleading cases and report small-support alternatives as such.
3. Strengthen the conventional benchmark using its actual required rainfall
   history and restore the generic historical reference on EO populations.
4. Add a compact same-support raw-EO/season/coverage reference only if making an
   EO-specific learned-information claim; otherwise narrow attribution honestly.
5. Consolidate the paper around one retrospective analogue question, with EO and
   cross-border evidence as structured comparisons. Earlier storm/threshold work
   is supporting material. Prediction/training remains a later separately justified
   extension; no new prediction model, fine-tuning, RAG system or dashboard is
   required by this audit.

Most recommendations use saved arrays, selected donors or existing imagery;
none requires new provider permission, a mandatory formal preregistration, more
interviews, or a new basin. Brian retains the actual chapter/article writing.
