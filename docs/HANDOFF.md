# Limburg handoff — DISE-inspired reconstruction

Updated 24 November 2026. Brian writes dissertation prose and sends all emails.

## Current extension status — 20 November 2026

The completed multiyear study used **2017 AlphaEarth**, with discharge
evaluation in 2021–2025 locally and 2021–2024 externally. The extension
uses **2020 AlphaEarth and 2020 TESSERA** on the same 394 processing polygons.
Both descriptor tables passed validation. The 2018 TESSERA extraction is
retained as an alternate.

The 2020 satellite benchmark completed 114 fresh fits for the held Geul 2021
fold. It uses C0, including 2017 Copernicus land-cover fractions. The 2020
embeddings describe a fixed pretest snapshot applied retrospectively to earlier
fitting rows. See the [living one-pager](chapter-one-pager.md) for the comparison
and year table.

The imagery-year sensitivity completed all 30 folds, with 81,857 paired
gauge-days verified. Withheld local river all-day MAE fell 13.86% with
2017 AlphaEarth and 2.58% with 2020 AlphaEarth relative to C0.

The matched 2020 satellite comparison completed all 30 C0 folds, with 81,857
paired gauge-days verified. On held local rivers, all-day MAE improved 2.58%
with AlphaEarth and 0.56% with TESSERA. High-water MAE worsened 2.11% and
6.47%, respectively. The [completion readout](reviews/limburg-alphaearth-vintage-readiness-2026-11-19.md#matched-2020-satellite-comparison--completed-20-november-2026)
records the paired uncertainty, river and year differences, and case examples.

The [release audit](limburg-representation-correct-use-review-2026-11-18.md#release-check--20-november-2026)
found no usable public release for either additional encoder. The StefaLand
runoff-free 2020 export and the Basin2Vec checkpoint and input recipe are
outstanding. Both need artifact and coverage checks before testing.

The [encoder pilot preparation](data-needs.md#stefaland-and-basin2vec-pilot-preparation--22-november-2026)
records the European input crosswalk, StefaLand forcing inventory and verified
2020 Cottessen source sample. Use it for the first artifact and coverage checks.

1. [Held inputs audited](data-needs.md#held-input-audit-for-c1--20-november-2026).
   Daily weather, geometry and existing terrain/land/soil summaries cover all
   394 gauges. The held soil/snow, hourly temperature and GLO-30 grids have
   limited geographic coverage. Use the audit to specify the held-data
   benchmark and refine downloads after the model recipes are known.
2. [Held-data C1 benchmark completed and audited](data-needs.md#matched-results-and-chapter-implications).
   In Wurm 2021, C1 raised MAE relative to C0. Adding AlphaEarth to C1 reduced
   all-day MAE and raised high-water MAE. Adding TESSERA raised both. All 114
   fits completed and the selected fits stopped below the cap. Treat the fold
   as a robustness check alongside the completed multiyear evidence.
3. As each artifact arrives, verify its provenance and extraction recipe. If
   weights arrive, reproduce a reference vector and pilot one European
   catchment. If vectors arrive, verify the polygon, year and feature schema.
   Use the verified raw input families to finalize C1, then run one matched
   fold before scheduling the full comparison. If the artifacts remain
   unavailable, a defined C1 comparison with AlphaEarth and TESSERA is feasible.

### Multiyear C1 and a stronger conventional comparison

Brian approved the multiyear C1 run and a separate C2 comparison on 20 November.
The [C1 runner](../scripts/292_run_c1_multiyear.py) launched all 30 original
folds with two CPU workers and the verified Wurm 2021 fold reused. It runs
the remaining Wurm years first, then the other spatial and temporal folds.
The held weather calendar covers all 394 gauges through 2025. The existing
held-Wurm split has 4,368 additional eligible gauge-days in 2022–2025,
including 52 high-water and 19 clean high-water gauge-days. Extend the exact
held-data C1 recipe first, keeping the 2020 embeddings, prior-year weather
rule, splits, tuning policy and scoring populations fixed. Wurm across years
tests year sensitivity. Applying that same recipe to the other held rivers
tests geographic sensitivity. The expanded 3,152-row control table exactly
reproduced the pilot-year features. The matched C0 archive provides the
reference. On completion the queue verifies matched observations, thresholds,
and flags across all 81,857 rows and writes paired estimates and uncertainty
for the chapter's evidence summary. All 30 folds completed on 21 November
with 81,857 paired verification rows. See
`results/limburg_representation_extension_v1/c1_held_multiyear_v1/progress.json`.

At the next run design, revisit CPU concurrency. Compare two and three
workers on representative jobs and check completed fits per hour, memory
pressure and swap before choosing the worker count.

Separately, use a physically richer conventional control to test how much of
the embedding gain remains once hydrologically relevant information is shared.
The [C2 queue](../scripts/294_run_c2_multiyear.py) was launched on 21 November.
It [acquires and audits](../scripts/293_acquire_c2_controls.py) full cross-border
inputs first, then fits C2 alone and with each fixed 2020 embedding using the
same 30 folds, rows, tuning policies and information cutoff as C1. Follow
`results/limburg_representation_extension_v1/c2_multiyear_v1/progress.json`.
Acquisition and fitting are separate stages, with checksum-verified batch and
fit receipts for restarting. Report paired high-water MAE first, then clean
high-water and all-day scores, and retain RMSE and regional transfer strata.

On 22 November, the matched 2020 C2 comparison completed all 30 folds and
verified 81,857 paired gauge-days. The [2017 AlphaEarth sensitivity runner](../scripts/295_run_c2_alphaearth_2017.py)
reuses the archived 2017 vectors and the completed C2 inputs, splits and tuning
policy. It refits only the 2017 AlphaEarth arm and pairs its predictions with
the saved C2 and C2 + 2020 AlphaEarth predictions. All 30 folds completed.
The [consolidated results and episode attribution](reviews/limburg-c2-findings-2026-11-23.md)
are the current evidence summary for C0, C1, C2 and the imagery-year comparison.

## Discussion plan — 24 November 2026

Plan for about five pages for Discussion and Conclusion together, including
the Meuse figure and its interpretation. Use this as a working allowance from
the [dissertation scope audit](../../dissertation-manuscript/docs/reviews/chapter-scope-benchmark-audit-2026-11-11.md#main-text-structure-recommendation).
Organize the discussion around one question: **What can we learn about high
water from a corrected global discharge record when local evidence is limited?**

1. **Answer the model question.** Lead with the matched all-season daily p99
   comparison and the difference between known and held-out rivers. Explain
   what conventional inputs contribute and how much confidence the existing
   results support in the additional embedding gains. Use all-day performance
   to explain why high water deserves separate evaluation.
2. **Interpret the errors with river evidence.** Use the observed seasonal
   pulse to distinguish a large flow from an unusual flow for the season.
   Rimburg provides one concrete example: the two global products differ in
   typical accuracy and both strongly underestimate the largest measured
   daily flow. Bring in measurement qualifications where they affect the
   interpretation. Keep the detailed seasonal tables, Google comparison and
   July 2021 case notes available as supporting evidence.
3. **Show why location matters.** Close with the two observed Meuse events
   and the Borgharen–Venlo figure. Use the change in crest timing and magnitude
   to explain why local high-water accuracy and downstream conditions are
   distinct questions. End with the evidence an agency would need to assess
   a transferred model for its own high-water use.

The existing evidence supports this structure. Keep the suggested full 2024
storm diagnosis and all-gauge calendar benchmark in the research notes for
possible follow-up. Revisit a targeted check if it would resolve a specific
uncertainty in the chapter's interpretation.

## Closing section — From tributary high water to the Meuse

Allow about one page and one figure within the Discussion and Conclusion plan.
Ask whether the timing of a high-water peak on a smaller tributary carries through
to the larger tributary and the Meuse. Credit the mainstem-first event selection
and peak comparison in [De Jong et al. (2022), Appendix G.4](https://publications.deltares.nl/11208036_012.pdf#page=168).
Use their rules where the gauge records permit and document differences in stations,
coverage and peak selection.

- Use Borgharen Dorp as the timing reference for the comparison with the published
  study. The initial screen identified four candidate windows on **11 October 2024,
  20 November 2024, 13 February 2026 and 23 February 2026** (UTC crest dates).
  Borgharen had discharge with RWS quality code `00` around those crests, and
  both Meerssen (Geul) and Stah (Roer) had readings over the windows. Confirm
  the event separation, gauge identities, and quality and timing of each tributary
  peak before plotting. Two January 2025 candidates relied on interpolated
  Borgharen discharge in the held archive.
- Readiness check. Both 2024 windows have controlled Borgharen discharge and
  readings around interior peaks at the gauges in both chains. In both February
  2026 windows, the held Borgharen code-`00` observations are marked uncontrolled.
  The 13 February Gulp and Stah maxima are also near the right edge of the
  comparison window, and the 23 February Gulp record ends during the window.
  Use the two 2024 events for the primary figure and retain the 2026 cases in
  the audit. Geleenbeek, Voer and Eyserbeek have readings in both 2024
  windows for the companion table.
- Plot a row per supported event and one column each for **Gulp → Geul → Meuse**
  and **Wurm → Roer → Meuse**. Align the traces to the Borgharen crest, show a
  three-day window on either side, mark the gauge peaks and leave gaps visible.
  Report when each peak occurred relative to Borgharen. Include Geleenbeek, Voer
  and Eyserbeek in a compact companion timing table where observations support it.
  For Voer, note its confluence upstream of Sint Pieter when interpreting the
  Borgharen comparison.
- Interpret the figure as a comparison of timing in a few observed events. A
  gauge peak is tied to its location. The differences do not estimate travel time
  or a tributary's contribution to downstream discharge. Brian writes the section.

### Completed timing comparison — 23 November 2026

The [runner](../scripts/297_meuse_peak_timing.py) verifies the six previously
screened candidate windows, rather than rebuilding De Jong et al.'s historical
event census. The two supported crests exceeded 1,000 m³/s at Borgharen Dorp,
occurred more than a day apart, and had an observed intervening drop of
1,043.9 m³/s below the smaller crest. Inputs are RWS 10-minute F006 discharge
with code `00` and controlled status, and 5- or 15-minute Waterstand Limburg
discharge records with explicit UTC timestamps. The public tributary extracts
do not expose row-level validation flags. The audit distinguishes interpolated
January 2025 crests from unchecked February 2026 crests and excludes both.

| Borgharen crest date | Gulp at Azijnfabriek | Geul at Meerssen | Wurm at Randerath | Roer at Stah |
| --- | ---: | ---: | ---: | ---: |
| 11 October 2024 | 30 h earlier | 21 h earlier | 25 h earlier | 21 h earlier |
| 20 November 2024 | 16 h earlier | 5 h earlier | 13 h earlier | 8 h earlier |

Both chains showed the smaller tributary peaking first and the Meuse peaking
last. The larger tributaries peaked closer to the Meuse in November. At Stah
in November, the first and last records within 1% of its maximum bracketed
the Borgharen crest. The first maximum alone conceals that overlap. The
Geleenbeek companion record also shows why gauge location matters. The
November maximum at Brommelen preceded Borgharen by about 20 hours, while
the Oud Roosteren maximum followed it by about seven hours.

Gaps and abrupt changes at Meerssen are visible in the figure. The plotted
markers are observed maxima with data on both sides. The upstream Hommerich
record had an earlier maximum than Meerssen in both windows. Randerath's
LANUK export and public feed placed both maxima within 15 minutes of each
other after UTC alignment. Fully sampled hourly means preserved the order
within each plotted chain. All 20 tabulated peak times were within one hour
of the native-resolution times. The figure scales each trace to its own
observed window maximum, and the table retains actual discharge. A second
run reproduced both figures and the timing CSV byte for byte.

Outputs in `results/meuse_peak_timing_2026_11_23/` include
`meuse_peak_timing.pdf`, `meuse_peak_timing.png`, `gauge_peak_timing.csv`,
`event_audit.csv` and the input and output hashes. Reproduce with
`.venv-dise/bin/python scripts/297_meuse_peak_timing.py audit` followed by
the same command with `run` in place of `audit`.

### Two follow-up designs — 23 November 2026

#### Rimburg: is the high-water error specific to the discharge product?

Compare checked daily discharge at Wurm–Rimburg (Waterschap Limburg, `18.Q.45`)
with raw GEOGLOWS v2 reach `230393243` and Google's November 2026 distributed
GRRR reanalysis at `subhybas_2121124850`. The Google outlet is on the modeled
Wurm about 2.4 km upstream of the gauge. Its catalogued area is 184.7 km²,
versus 189.29 km² for the gauge reference basin and 204.0 km² for the held
GEOGLOWS reach. Document the routed connections, intervening inflows or
diversions, available basin overlap and the Google training-data lineage before
interpreting the comparison. Treat both matches as spatial approximations.
Report unresolved training membership explicitly.

1. Use the existing Rimburg river-withheld verification rows and raw GEOGLOWS
   daily means. From 1 January 2021 through 30 December 2025, there are 1,805
   quality-screened candidate days, including 25 days at or above observed
   daily p99 across 16 existing episodes. These counts precede the Google
   data join. Keep the saved year-specific observed p99 labels and episode
   membership. Repeat the comparison on the broader 1,809-day eligible set
   to show the effect of the four qualified days.
2. Extract the single Google reanalysis series and record its product release,
   outlet metadata, units, hashes and source day convention. Check the nominal
   daily support against the archive's issue-day lead-zero identity. Join by
   daily start on complete common UTC days with finite values for both products
   and the physical gauge. Report days and episodes lost during matching. Use
   m³/s, the original flows and the documented timestamps throughout.
3. Report each product's high-water MAE, their paired MAE difference and
   signed bias. Add all-day MAE and episode-level errors on the peak day
   selected from the observations before matching. Record any missing peak-day
   comparison. Show how the paired result changes when each episode is omitted
   in turn. Deliver coverage and score tables and daily hydrographs for the
   largest observed episode and the episode with the greatest influence on the
   paired result. If both products miss the same peaks, the difficulty extends beyond
   raw GEOGLOWS at this station. Different errors show sensitivity to the whole
   product, including its spatial support and forcing. The comparison estimates
   retrospective product performance at Rimburg. Encoder benefits with a
   different base product would require a separate fitted comparison.

[Nearing et al. (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10954541/)
provide a precedent for matching global products to the same gauges and
checking basin support. Their Google–GloFAS comparison used a different model
generation, forecast endpoint and a ≥500 km² drainage-area screen for GloFAS.
[Kuipers et al. (2026)](https://onlinelibrary.wiley.com/doi/10.1111/jfr3.70247)
provide a local verification precedent from Mali using station discharge and
impact data. The [OCHA Somalia application](https://ocha-dap.github.io/ds-aa-som-floods/trigger-single-model/summary.html)
considered GEOGLOWS alongside Google and GloFAS and found that model suitability
varied by river and season. Rimburg applies the same principle to two pinned
daily reanalyses and a small cross-border tributary with checked discharge.

#### Meuse: does the crest change downstream of Borgharen?

Extend the two 2024 rows of the closing figure with one shared-scale column
showing measured Borgharen Dorp and Venlo discharge in m³/s. Keep both
normalized tributary-chain panels and the existing ±72-hour Borgharen anchor.
Venlo is about 91.5 river km downstream; the new panel tests whether the
observed crest was later and how its magnitude and shape changed over this
reach in those two cases.

1. Use RWS 10-minute discharge (`F006` at Borgharen Dorp, `F103` at Venlo),
   screened to code `00` and `Gecontroleerd`. Check both station methods and
   continuous observations near each peak. Keep the common 21 November 2024
   14:50 UTC rejected slot visible. Recheck peak order and differences in
   fully supported hourly means, accounting for each method's time support.
2. Mark both crests and report Venlo minus Borgharen peak time and magnitude.
   The read-only preflight put Venlo **27 h later and 221 m³/s lower** in
   October and **12 h 20 min later and 221 m³/s lower** in November. Use the
   plotted shape to show sustained high flow and flag any flat or tied crest.
   These are differences between station maxima in two cases. Confluence
   inflows, storage, regulation and measurement can all affect them. Their
   separate contributions and operational warning lead times are outside
   what these observations identify.
3. For an optional supplement, extract the same GRRR release at candidate
   Meuse outlets `subhybas_2120407290` (about 4.5 km from Borgharen Dorp) and
   `subhybas_2121120730` (about 2.9 km from Venlo). First verify the throughgoing
   channel and which confluences, branches and diversions lie between each
   gauge and modeled outlet. If the matches support comparison, show a daily
   hydrograph for each pair using complete common nominal UTC days. Report
   broad timing and peak-day agreement at daily resolution. The measured
   10-minute panel carries the evidence on within-day crest order.

[De Jong et al. (2022), Appendix G.4](https://publications.deltares.nl/11208036_012.pdf#page=168)
provides the starting point for the tributary timing, using a 1988–2016 Meuse
event census and the same ±3-day comparison window. The mainstem comparison
also has direct precedent. [Rijkswaterstaat](https://open.rijkswaterstaat.nl/open-overheid/onderzoeksrapporten/@56388/topafvoeren-hoogwater-maas-juli-2021/)
reported measured crests at Borgharen and Venlo for July 2021. [Asselman et al.
(2022)](https://www.sciencedirect.com/science/article/pii/S2468312422000050)
and [Strijker et al. (2023)](https://doi.org/10.59490/jcrfr.2023.0006)
show why peak attenuation and wave shape matter on this reach. [Geertsema et
al. (2018)](https://hess.copernicus.org/articles/22/5599/2018/) show why the
duration of high flow can matter more than the precise order of peaks at a
Meuse-basin confluence. The contribution here is a recent, local extension
that puts the two tributary chains and the observed mainstem response on one
clock.

Inputs already held cover the physical-gauge figure. The [Google archive
reader](../../chapter3-peja/scripts/google_grrr.py) can fetch the few relevant
series using a Limburg cache. Both designs are lightweight CPU work and sit
within Limburg 1. The existing C0–C2 interpretation still rests on the
completed matched comparisons.

### Completed Rimburg and Venlo checks — 23 November 2026

At Rimburg, all 1,805 quality-screened gauge days matched both products. The
same is true of the 25 high-water days, grouped into 16 episodes. Google MAE
was 0.78 m³/s across all days versus 1.53 for GEOGLOWS. On high-water days
it was 5.44 versus 8.58 m³/s, a 36.6% reduction, with signed biases of
−5.44 and −8.22 m³/s, respectively. Google underestimated all 25 high-water
days. Google was closer on the observed daily peak in 13 of 16 episodes.
Omitting each episode in turn left Google's high-water MAE advantage between
2.73 and 3.54 m³/s. The four qualified days in the broader sample gave the
same direction. GEOGLOWS had lower high-water MAE in 2022 (two days).

On 3 May 2024, the largest observed daily-flow episode in this check, the
gauge recorded 19.28 m³/s. Google gave 6.34 m³/s and GEOGLOWS gave 4.38 m³/s.
The smaller average error therefore coexists with a large error on the most
severe observed day. The crosswalk traces the Google outlet to the gauge on
the Wurm, with 93.2% of the reference basin covered by the Google basin and
95.2% of the Google basin in the reference. A modeled 42.1 km² tributary
joins at the Google outlet. A wastewater discharge to the Worm is documented
at Rimburg, with its position relative to the gauge unresolved in this audit.
The exact training membership of the evaluated station or its neighbors in
this Google release remains unknown. These are local comparisons of published
products, with differences in forcing, training, routing and drainage support.
[Waterschap's 2023 treatment report](https://www.waterschaplimburg.nl/publish/pages/9711/technologisch_jaarverslag_2023.pdf)
and [Google's documented training sources](https://support.google.com/flood-hub/answer/15637389?hl=en)
support those qualifications.

The extended Meuse figure confirms a later and lower measured crest at Venlo
in both events. October had a 27-hour offset and a 220.80 m³/s difference
(1578.43 at Borgharen and 1357.63 at Venlo). November had a 12-hour-20-minute
offset and a 220.71 m³/s difference (1051.90 and 831.19). Fully supported
hourly means preserved the sign and gave offsets of 27 and 14 hours. Their
downstream maxima were each about 223 m³/s lower. The raw comparison uses
station maxima in the same windows and the hourly check uses common hours.
The same rejected 10-minute slot in both records is visible as a gap.

The Google supplement confirms directed main-channel connections for its
two Meuse proxies, with extra modeled inflows between Borgharen and its outlet.
These remain approximate supports in a regulated reach. In October, the
Google Borgharen proxy reached its daily maximum on 12 October versus the
observed 11 October (877 versus 1502 m³/s). At Venlo, the modeled maximum
in the window was 880 m³/s on the last complete day, 13 October, while the
observed maximum was 1324 m³/s on 12 October. The November daily comparison
lacks the 21st at both physical gauges under the complete-day rule. Both
Google series had their largest values at the end of the window, so the
supplement leaves their November crest timing unresolved. Keep the daily
plots as context for interpretation. The measured 10-minute panel is the
primary closing figure.
[Rijkswaterstaat's description of the Meuse structures](https://www.rijkswaterstaat.nl/water/waterbeheer/bescherming-tegen-het-water/waterkeringen/dammen-sluizen-en-stuwen/de-7-maasstuwen)
and the [water-management description of the Julianakanaal](https://iplo.nl/publish/pages/188994/watersystemen-zuidelijk-deel-maas-en-julianakanaal.pdf)
provide the operational context.

Reproduce with the held archives and `.venv-dise/bin/python`:

- `scripts/298_compare_rimburg_discharge_products.py` produces the score,
  coverage and episode tables and hydrographs in
  `results/rimburg_discharge_products_2026_11_23/`.
- `scripts/297_meuse_peak_timing.py audit --include-venlo`, then the same
  command with `run`, produces the extended figure and tables in
  `results/meuse_peak_timing_with_venlo_2026_11_23/`.
- `scripts/299_check_meuse_grrr_context.py` produces the outlet audit and
  daily supplement under `google_context/` in the extended results. It uses
  the held HydroSHEDS geometries and the local GRRR receipts under
  `data/raw/open/grrr/distributed_model_2026_11/`. The source-internal archive
  date check matched 47 Rimburg and 90 Meuse outlet-day values to the next
  day's lead-zero fields. Google archive timestamps are nominal UTC.

## Completed multiyear evidence — 18 November 2026

The 30-job comparison and repeatability analysis cover 81,857 verification
rows. The [AlphaEarth evidence pack](limburg-dise-alphaearth-consolidation-2026-11-18.md)
contains the tables, figures and paired event examples.

Adding AlphaEarth reduces local river-withheld all-day MAE 13.86%, repeating
across all five test years and four of five rivers; Voer worsens. Historical-
target-label temporal all-day performance worsens 1.44%. External all-day gains
are 4.67% and Erft-driven. **Added high-water benefit remains unestablished**:
the primary MAE contrast slightly worsens in all three regimes, with intervals
spanning gains and losses. Keep this outcome distinct from the secondary
all-day finding. Provider QA, sparse verification, nested gauges and shared
rolling training histories limit claims.

[Step 3 readout](limburg-dise-repeatability-2026-11-18.md). Configuration:
`config/limburg_dise_repeatability_v1.json`; runner:
`scripts/277_assess_dise_repeatability.py`. Outputs:
`results/limburg_dise_repeatability_v1/`, including `manifest.json`,
`verification.json`, paired/annual/river/gauge/influence tables, every gauge-year
maximum, episode/documentary ledgers and compressed complete draw arrays.
All 576 nonempty Step 2 metric records reproduce independently; 72 real-data
resampled-score checks agree with explicit weighting. Sixteen relevant tests
and Ruff pass. Output occupies about 49 MiB; roughly 77 GiB remains free.
No source data or other chapter was changed.

The dated preparation and launch records below document earlier states.

## Current direction and state

Independent DISE-inspired adaptation accepted; audit corrections implemented in v2. [Design](limburg-dise-research-design-2026-11-16.md),
[configuration](../config/limburg_dise_v2.json), [preparation report](limburg-dise-preparation-2026-11-16.md).
Daily reconstruction is a deliberate outcome change from the completed next-24h
assessment. The source authors' code returned 404; it is not a dependency.

Local daily inputs, seven-gauge weather and common-source descriptors are ready.
The corrected local held-Wurm 2021 benchmark completed **152 fits in 32.19 s**,
including the article-faithful sensitivity. All valid January days are restored;
reconstructed-discharge RMSE (mm/day) drives primary early stopping/selection. Fixed scoring
populations, saved p99 flags/thresholds and local/donor calibration are implemented.
The original benchmark remains under v1. See the
[implementation record](limburg-dise-audit-corrections-2026-11-16.md).

Regional topology screening yields 336 provisional donors, 50 reserved external
records, four local connected-section exclusions and one source-network gap.
44 geometry/coverage flags remain explicit; proximity alone does not approve a
model identity. Source clock is verified from the primary paper: UTC hour-end
means. Provider quality remains qualified, not inferred from finite values.

All **386 mapped nonlocal source records are acquired and checksum-verified**,
with zero failed transfers and 821,400 complete daily observations in 2018–2024.
Twelve records have no complete daily overlap in that period; these are coverage
cases, not transfer failures. Raw snapshots use 3.66 GiB; daily tables use 84 MiB.
The observation-only acquisition is complete. **Matched regional model/weather/
AlphaEarth and conventional-control inputs are complete and hash-verified**.
All acquisition workers have finished; the first regional-fold benchmark is complete. Input-acquisition progress is
`results/limburg_dise_v2/regional_inputs/progress.json`. The observation receipt
remains under `regional_acquisition_progress.json`. Data location:
`data/raw/limburg_dise_v2/camels_timeseries/`, daily records under
`results/limburg_dise_v2/regional_observations/`. Disk reserve remains 50 GiB;
74.8 GiB was free at verification; no other-chapter data were changed or Azure
job started. See the [verification receipt](reviews/limburg-dise-corrections-verification-2026-11-16.json).

## Spatial review completed and next work

[Spatial resolution and strata](limburg-dise-spatial-resolution-2026-11-16.md)
completes the original 44-flag review: 32 directional/partial cases are stratified,
11 remain explicitly uncertain, and the search-boundary case is recovered as a
high-overlap proxy. Eight additional station/reference-location conflicts were
identified. All cases remain represented; uncertainty is not a blanket stop.

The current resolved pool is **387 gauges** (337 provisional donors, 50 external),
with 344 high-overlap and 331 high-overlap/location-consistent sensitivity records.
One added gauge shares an existing model reach; original matched IDs/holdout roles
are unchanged. The resolved input tables are under
`results/limburg_dise_v2/regional_inputs_resolved_v1/`; original 386-record receipts
above remain historical acquisition evidence. The first regional-fold benchmark
is complete; no full multi-year comparison has launched.

[Regional preparation and benchmark](limburg-dise-regional-benchmark-2026-11-16.md):
1,151,268 feature rows, actual local-recipe parity audited, 51 tests passing.
The Wurm/external 2021 fold completed 152 fits; no worker is active.
Progress: `results/limburg_dise_regional_benchmark_v1/benchmark_wurm_external_2021/progress.json`.
The completed run is frozen; preserve its inputs/code identity and outputs.
The first-fold review and capacity check are now complete; see the authorized
continuation below. A favourable result is not a gate for the saved next steps.

## Commands

Use `.venv-dise` (XGBoost 3.1.2/scikit-learn 1.7.2); prior environments are
unchanged. `scripts/264_prepare_dise_corrections.py` handles corrected features
and regional physical screening; `scripts/265_benchmark_dise_corrected.py`
verifies/reuses its corrected benchmark; `scripts/266_acquire_dise_observations.py`
handles resumable source acquisition; completed records are verified and reused.
The old scripts 262/263 retain their v1 roles and are not the active continuation.

## Completed earlier work

GEOGLOWS seven-target v2 finished all four fits and review on 14 November 2026;
[qualified results](limburg-geoglows-first-results-2026-11-14.md) and all source
configurations remain. Earlier analogue, scarcity, model-specific correction and
mapping results are retained in their original directories and dated records.
Do not restart those queues or compare their next-24h scores directly with daily
reconstruction. The canonical current-study pointer is
`config/limburg_current_study.json`.


Completion update — 17 November 2026: the first regional-fold benchmark finished
all **152 fits**, calibration and scoring in **39.3 minutes**. Input/output hashes
reverify; 303 metric records and the prediction/calibration tables are available.
No workers remain active. This is one 2021 fold; the results and capacity review
is now complete, with a fair capacity extension recommended before full scaling.


## Reviewed first-fold results — 17 November 2026

[Results, spatial strata and tree limits](limburg-dise-regional-results-review-2026-11-17.md).
All-day Wurm E gain is substantial (23.1%); external mean is small (2.9%) and
Erft-driven. High-water gains are small and selection/measurement-sensitive;
corrections worsen some severe errors relative to raw GEOGLOWS. 26/128 tuning
fits are capped, including selected H+E/article-faithful cases and a close
primary H+A+E runner-up. Recommended one fair 3,000-tree capacity check, then a
locked multi-year comparison. Review artifacts are
under `results/limburg_dise_regional_benchmark_v1/review_2026_11_17/`.

## Authorized continuation — 17 November 2026

The [four-step plan](limburg-dise-four-step-plan-2026-11-17.md) is saved in
`config/limburg_dise_four_step_plan_v1.json`. **Step 1 is complete; Step 2 is
running; Steps 3–4 remain pending.**
The capacity run uses `scripts/275_run_dise_capacity_check.py` and
`config/limburg_dise_capacity_v1.json`, with results/progress under
`results/limburg_dise_capacity_v1/`. The fixed 3,000-tree reuse control matches
the original stopping point and validation predictions exactly. All 26 previously
capped jobs were refit from scratch; 101 verified early stops were reused. Four
selected specifications changed, requiring 12 new final fits; 12 were reused.
The original benchmark is preserved. The run finished in 22.1 minutes with one
CPU fitting worker/two threads. No workers were active at that completion. No GPU, download
or cloud task was used. Fifty-four relevant tests and Ruff pass.

The same test populations and raw/FDC controls reverify. No selected candidate/fold
fit remains capped; three unselected sensitivity fits do. Primary AlphaEarth
all-day MAE gains are now 21.3% Wurm/2.3% external; high-water MAE changes are
−2.5%/+1.7% improvement, respectively. [Results and verification](limburg-dise-capacity-check-2026-11-17.md)
explain the distinct RMSE results and continuing measurement/one-year limitations.
Rerunning the capacity command verifies completed outputs without refitting.
The machine-readable plan/current-study status was updated. No further cap
increase was launched. The separately authorized Step 2 follows below.

## Active Step 2 queue — 17 November 2026

[Multiyear design/run record](limburg-dise-multiyear-run-2026-11-17.md).
`scripts/276_run_dise_multiyear.py` uses `config/limburg_dise_multiyear_v1.json`.
Two CPU workers/two threads each; no GPU or new download. The queue has 30 outer
jobs/4,560 fit slots, including 152 verified slots reused from the 2021 Wurm
capacity result. Sixty-three relevant tests and complete reuse verification pass.
Fresh jobs retain the same four arms, policies, candidates, seeds and 3,000-tree
budget. Do not change pinned code/config while they run.

All 81,857 verification rows are retained across the separate regimes. External
gauges have no fitting-label access and are evaluated once per 2021–2024 year
using the temporal model; spatial jobs evaluate only the held local river.
Coverage ledgers retain missing-verification gauge/years. Donor FDC explicitly
excludes the target river in temporal jobs, preventing self-donor label leakage.

Progress: `results/limburg_dise_multiyear_v1/progress.json`; individual jobs under
`jobs/`, worker logs under `logs/`. Each fit checkpoints; job manifests preserve
inputs/code/output hashes. The same `run` command resumes completed work after
interruption. The coordinator aggregates point estimates and marks Step 2
complete on success. It does not launch Step 3 or send emails. Keep the existing
50-GiB disk reserve; estimated new output is 2–6 GiB, with about 81 GiB free at
launch. No cleanup/offload or other-chapter changes were needed.
