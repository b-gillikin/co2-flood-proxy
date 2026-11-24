# Limburg — learned catchment information for discharge reconstruction

Living research aid, updated 23 November 2026. Brian writes dissertation prose.
Independent DISE-inspired adaptation accepted; local preparation/benchmark
completed, audit corrections implemented in v2; first regional fold and capacity
check completed. The multiyear comparison and Step 3 repeatability review are
complete. The [AlphaEarth evidence pack](limburg-dise-alphaearth-consolidation-2026-11-18.md)
completes Step 4 and provides comparison tables, figures and paired event
examples. The matched 2020 AlphaEarth and TESSERA descriptors are validated
for all 394 gauge records. The held Geul 2021 benchmark with the existing C0
controls and the held-Wurm 2021 C1 benchmark are complete. The full C1 and C2
comparisons and C2 imagery-year sensitivity are also complete. StefaLand and
Basin2Vec remain conditional on compatible artifacts.

| Comparison | Satellite reference year | Discharge evaluation | Conventional controls |
| --- | --- | --- | --- |
| Completed AlphaEarth multiyear study | 2017 AlphaEarth | Local 2021–2025; external 2021–2024 | C0, includes 2017 land-cover fractions |
| Completed satellite benchmark | 2020 AlphaEarth and 2020 TESSERA | Geul, 2021 | Same C0 |
| Completed matched satellite comparison | 2020 AlphaEarth and 2020 TESSERA | All 30 original temporal and river-held folds | Same C0 |
| Completed held-data C1 benchmark | 2020 AlphaEarth and 2020 TESSERA | Held Wurm, 2021 | C0 plus prior-year weather and catchment shape |
| Completed C1 comparison | 2020 AlphaEarth and TESSERA | Same 30 folds | C0 plus prior-year weather and catchment shape |
| Completed C2 comparison and imagery-year sensitivity | 2020 AlphaEarth and TESSERA, plus 2017 AlphaEarth sensitivity | Same 30 folds | C1 plus WorldCover, elevation relief, clay, prior-day soil moisture and snow |

The matched 2020 run verified 81,857 paired gauge-days across 30 folds.
On held local rivers, all-day MAE fell 2.58% with AlphaEarth and 0.56% with
TESSERA relative to C0. High-water MAE rose 2.11% and 6.47%, respectively.
The [matched readout](reviews/limburg-alphaearth-vintage-readiness-2026-11-19.md#matched-2020-satellite-comparison--completed-20-november-2026)
records the uncertainty, river differences and case examples.

On the [matched held-Wurm C1 fold](data-needs.md#matched-results-and-chapter-implications),
the additional conventional features raised MAE versus C0. AlphaEarth improved
all-day MAE by 12.38% versus C1 and raised high-water MAE by 3.22%. TESSERA
raised both. The high-water subset has 21 gauge-days across nine dates.

The 2018 TESSERA extraction served as an intermediate coverage and extraction
check. The fixed 2020 landscape snapshot predates held discharge evaluation and
is also assigned to earlier fitting rows in the retrospective benchmark.

## Research Question(s)

Can learned catchment information make a global discharge model more
accurate during high water, including on other rivers?

Characterize source errors; test AlphaEarth's incremental value beyond common
weather and conventional catchment descriptors; test whether that value depends
on the representation; evaluate transfer without local target-river calibration.

## Motivation

Assess when globally available satellite information can supplement local
hydrological modelling and monitoring capacity. Identify prerequisites, costs,
severe errors and transfer limitations relevant to agency investment. This is
daily retrospective reconstruction, not a demonstration of forecast lead time,
operational warnings or avoided flood losses.

## Data

René/Jens observations and provider qualifications, verified GEOGLOWS discharge,
2017 AlphaEarth catchment means, and newly acquired gauge-specific ERA5-Land
weather for 2017–2025. Consistent conventional descriptors use SRTM terrain,
2017 Copernicus fractional land cover and a surface field-capacity proxy;
regulation coverage remains incomplete; a no-dam inventory entry does not rule
out other controls or management. Seven local gauges represent five
river groups; Eys remains excluded and the Meuse is not added as a new target.

CAMELS-DE-1h observations and matched predictors now cover 387 regional gauges:
337 provisional donors and 50 reserved external records in Ahr/Erft/Sieg. There
are 823,956 complete observed daily values in 2018–2024. UTC hour-end timing is
verified from the primary paper. These are not independent or uniformly
quality-verified populations. The spatial review preserves all records with
explicit overlap/location strata; high-overlap and location-consistent
sensitivity views contain 344 and 331 gauges. One search-boundary gauge was
recovered; eight additional station/reference conflicts were identified.
Regional observations end in 2024; 2025 predictors do not create 2025 labels.

Extension inputs: the matched 2020 satellite descriptors and C2 inputs are held.
A 2020 runoff-free StefaLand catchment product and a Basin2Vec checkpoint with
an inference recipe compatible with European inputs are outstanding. See
[data needs](data-needs.md) and the [release audit](limburg-representation-correct-use-review-2026-11-18.md#release-check--20-november-2026).

## Method

One pooled XGBoost log-residual correction of daily GEOGLOWS discharge. Compare
weather/model history alone, plus conventional attributes, plus AlphaEarth, and
plus both. Use observed Q as verification, never current observed Q as an input
to reconstruct itself. Keep raw GEOGLOWS and appropriate calibration references.

For the extension, retain this completed baseline and fit a common enriched
conventional control, then add each of AlphaEarth, TESSERA, StefaLand and
Basin2Vec separately. Keep native descriptors, matched tuning budgets and the
same outcome/splits. Different upstream sources prevent a pure architecture
comparison; new results are exploratory because existing test outcomes are known.

Stage 1 establishes the local daily reference. Stage 2 trains with permitted
historical local/regional donor data and tests the same seven local gauges.
Stage 3 tests reserved external rivers without their calibration labels.

## Methodology

All eligible days; identical cohorts and tuning budgets across feature sets;
chronological test years 2021–2025, nested river-group withholding and
reconstructed-discharge RMSE (mm/day) for primary early stopping and selection. All three
Wurm gauges leave together. Prior-landscape descriptors, train-only transforms,
common weather definitions, quality/missingness records and paired high-water
and all-day evaluation. Report measurement/geometry limitations and river/storm
dependence. Current local data have informed prior experiments; do not claim
blind confirmation or historical as-issued foundation-model availability.

## Findings / current status

The contribution is a matched comparison of when catchment embeddings
add value to daily discharge correction. On known rivers, C2 cut all-day
MAE by 8.25% versus C1 and 5.49% versus C0. C0 had slightly lower high-water
MAE than C2 there. Neither embedding gave a clear additional gain under
30-day paired resampling. On held-out local rivers, C2 alone performed worse
on all days than C1. Adding 2020 AlphaEarth to C2 still improved on C1 by
about 3.5%. The same was not true for TESSERA.

For held-out local high water, 2020 AlphaEarth cut MAE by 2.86% versus C2 and
TESSERA raised it by 4.58%. Neither direction depends on a single river or
episode. Geul and Gulp drove the AlphaEarth improvement and Geleenbeek drove
most of the TESSERA harm. Some gains come from observations with measurement
caveats. On the strict-clean subset, the AlphaEarth gain shrank to 1.71%
and its 30-day range crossed zero. On external high water, the C2 arms
reduced MAE versus raw GEOGLOWS. Raw GEOGLOWS had the lowest RMSE.

AlphaEarth 2017 beats 2020 on all days in held-out local rivers and loses on
high water. This shows why average discharge performance alone is an inadequate
selection criterion for high-water use. The result concerns this reconstruction
and evaluation design. Operational delivery, warning thresholds and decisions
require further evidence.

[Consolidated evidence and event review](reviews/limburg-c2-findings-2026-11-23.md)
includes the baseline contrasts, full high-water attribution and literature,
data, split and reproducibility audit.
Earlier C0 findings and gauge-year maxima remain in the
[original evidence pack](limburg-dise-alphaearth-consolidation-2026-11-18.md).

The [seasonality check](reviews/limburg-c2-findings-2026-11-23.md#seasonal-pulse-and-high-water-sensitivity)
retains the all-season daily p99. It puts 134 of 226 high-water gauge-days in
November–April and 92 in May–October. Another 143 gauge-days were unusually
high for their half-year alone, with 104 in 2024. On the seasonal-p99 subset
with clean verification, adding 2020 AlphaEarth to C2 gave about the same
error as C2 alone, while TESSERA increased it. The seasonal ranks describe
how unusual flows were for the time of year.

The closing analysis, [From tributary high water to the Meuse](HANDOFF.md#completed-rimburg-and-venlo-checks--23-november-2026),
adapts the published Borgharen timing comparison to two quality-supported
2024 events. In both river chains the smaller tributary peaked first and the
Meuse last. The November Roer was near its maximum both before and after the
Borgharen crest. At Venlo the Meuse crested later and about 221 m³/s lower
in both cases. The measured figure has a daily Google comparison as supporting
context. A separate Rimburg comparison found smaller daily high-water MAE with
Google than with raw GEOGLOWS, 5.44 versus 8.58 m³/s on 25 matched days. Both
substantially underestimated the largest observed daily flow.

### Earlier preparation and first-fold records

The completed earlier next-24h GEOGLOWS experiment found conventional correction
value but no dependable incremental Presto/AnySat gain. Its outcome differs
from this daily reconstruction study; results are preserved separately.

Current preparation has 20,454 local gauge-days for 2018–2025, including 19,538
complete observed/model pairs. The corrected local held-Wurm 2021 nested benchmark completed
152 fits, including one selection-policy sensitivity, in 32.19 seconds. It verifies local feasibility, not the
regional research claim. Thirty-seven relevant tests, Ruff, dependency checks and
input/output receipt verification pass. All regional observation transfers and
source/daily checksums are verified. All matched regional inputs are assembled:
1,272,069 model and weather gauge-days each, plus 387 embedding/control rows.
No model/weather cells are missing; every spatial row has valid support. All
acquisition workers have finished. Regional feature assembly/audit is complete
(1,151,268 rows); the first full 152-fit regional-fold benchmark is complete.
Its 2021 test census has 17,637 eligible days across 51 contributing gauges;
two additional external gauges lack 2021 verification, explicitly recorded.
No GPU job, full regional fitting queue, Azure offload or other-chapter cleanup
was started; 74.8 GiB was free at verification, above the 50-GiB reserve.

The [design audit](reviews/limburg-dise-research-design-audit-2026-11-16.md)
supports retaining this study. Its corrections to model selection, calendar
exclusions, conventional references and population-aware scoring are now
[implemented](limburg-dise-audit-corrections-2026-11-16.md).
Daily-flow improvement remains distinct from flood-peak or warning improvement.

[Design](limburg-dise-research-design-2026-11-16.md) ·
[Preparation, audit and next work](limburg-dise-preparation-2026-11-16.md) ·
[Completed GEOGLOWS results](limburg-geoglows-first-results-2026-11-14.md).

[Completed spatial review and current input locations](limburg-dise-spatial-resolution-2026-11-16.md).

[Regional preparation and current benchmark](limburg-dise-regional-benchmark-2026-11-16.md).


Completion update — 17 November 2026: the first regional-fold benchmark finished
all **152 fits**, calibration and scoring in **39.3 minutes**. Input/output hashes
reverify; 303 metric records and the prediction/calibration tables are available.
No workers remain active. This is one 2021 fold; the results and capacity review
is now complete, with a fair capacity extension recommended before full scaling.


Results review — 17 November 2026: in the first 2021 regional fold, adding
AlphaEarth to the conventional model reduces all-day Wurm MAE by 23.1% and
external MAE by 2.9%; high-water gains are only 1.6%/1.7% and do not hold
consistently under measurement/selection sensitivities. High-water RMSE is worse
than raw GEOGLOWS. External gains persist in high-overlap views but vary by river.
Selected primary H+A/HA+E fits are uncapped; other selected and near-tied tuning
candidates hit the limit. A fair capacity check was recommended before full
scaling. [Full review](limburg-dise-regional-results-review-2026-11-17.md).

Current continuation — 17 November 2026: the [four-step plan](limburg-dise-four-step-plan-2026-11-17.md)
is saved. **Step 1 is complete** with a common 3,000-tree maximum. All 26 originally
capped tuning jobs were refit; the reuse control matched exactly. Four selected
specifications changed, requiring 12 new final seed fits. None of the selected
candidate/fold fits remains capped; three unselected sensitivity fits do.
The updated primary all-day MAE gains from AlphaEarth are **21.3% on Wurm and
2.3% externally**. High-water MAE worsens by 2.5% on Wurm and improves by 1.7%
externally; high-water evidence remains mixed. This is still one 2021 fold.
[Capacity results and verification](limburg-dise-capacity-check-2026-11-17.md).
Steps 2–4 were pending at capacity completion; original results are retained.

Step 2 update — 17 November 2026: the [multiyear comparison](limburg-dise-multiyear-run-2026-11-17.md)
is running on two CPU workers/two threads each. Thirty outer jobs cover local
2021–2025 temporal and whole-river-withheld tests, plus external 2021–2024 tests
scored once yearly. The full census has 81,857 verification rows across the
separate regimes; temporal and spatial local days are not pooled together.
The 2021 Wurm capacity models/predictions are verified and reused. No acquisition
or encoder extraction is needed. Sixty-three relevant tests and the full reuse
path pass. These jobs do not yet establish whether the first-year result repeats;
Steps 3–4 remain pending. Progress is
`results/limburg_dise_multiyear_v1/progress.json`.

TESSERA extension update — 18 November 2026: the scale-only 2017/2018 scan
favoured 2018 on coverage alone. The full native 128-dimensional 2018
TESSERA extraction then completed for all 394 polygons. Descriptor coverage
matches the scan to machine precision; every mean is finite. Runtime was 3 h
25 min, peak RSS 2.08 GiB, and free disk remained about 132 GiB. The original
2017 H+A/AlphaEarth analysis is unchanged. The later coverage scan selected 2020 for the matched extension. See the
current year table above.
[Extraction and validation record](limburg-tessera-census-2026-11-18.md).
