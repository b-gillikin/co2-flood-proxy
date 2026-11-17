# DISE design-audit corrections — implementation

16 November 2026. Brian authorized the recommended actions. This is an internal
research/execution record, not dissertation prose. Previous configurations,
source features and benchmark results are preserved under v1. Corrected code
uses `config/limburg_dise_v2.json` and `results/limburg_dise_v2/`.

## Scientific and implementation choices now fixed

### Selection aligns with discharge errors

The primary early-stopping **and** candidate-selection criterion is
river-balanced **RMSE of reconstructed specific discharge in mm/day**. Squaring
native-unit errors makes large errors consequential instead of compressing them
in log space. It is high-flow-sensitive, not a claim of exclusively optimizing
p99 cases. All days remain in training and validation. The fitting target stays
the DISE-inspired log1p residual; a gradient loss need not equal the downstream
validation metric, but their different roles are now explicit.

The candidate grid, training rows and three final seeds are identical across
all four feature sets. Candidate selection aggregates mean squared error across
the fixed inner river groups; its square root is the declared RMSE. Tree count
is selected on past inner validation only and then refitted using permitted
past data. No held Wurm outcome selects configuration or early stopping.

One matched sensitivity retains log-residual early stopping and all-day MAE
selection, labelled `article_faithful`. It is an independent adaptation, not a
reproduction of inaccessible source code. Both policies share the corrected
calendar, conventional descriptors, rows and evaluation. The policy choice was
made in response to the design audit, not chosen for a favourable encoder score.
The archive has been inspected previously; this is not blind confirmation.

### Calendar exclusions removed

January 1–7 is retained in validation/testing when observed/model daily values
are valid. Earlier model/weather predictor history is legitimately available;
it is not label leakage. The main chronological reconstruction does not drop
whole boundary-spanning storms merely to make observations look independent.
Storm/year dependence is represented in evaluation instead.

Across 2021–2025 this restores the previously counted **240 valid gauge-days,
including 18 prior-history-p99 gauge-days**. The corrected held-Wurm fold adds
21 test gauge-days and 28 validation days: 2,723 training, **1,250 validation**
and **1,089 test** rows. Missing verification values remain missing.

### Populations, thresholds and uncertainty are inspectable

Each stratum declares its verification-eligible gauge/river population **before
prediction availability is examined**. Every method receives that same declared
population. A missing contributing gauge or nonfinite prediction makes that
score undefined, with the reason and missing/nonfinite counts saved; no gauge
is silently dropped and absence is not given zero loss.

The scorer retains per-gauge components and equal gauge-within-river,
river-between-river aggregation. P99 thresholds are evaluator-only prior-target
history and now saved numerically, together with the high-water flag in the
prediction table. Native m3/s predictions are retained alongside mm/day.
Clean-high-water support and calibration-matched support are separately named,
with their own declared reference populations; their estimands are not
interchangeable with the full eligible high-water set.

Resampling uses **999 identical year multiplicity vectors across methods**.
Known storms crossing New Year receive a common onset-year block across gauges;
unassigned days retain their calendar-year block. Undefined draws are retained
without retries. A single-year benchmark receives **no between-year interval**;
999 copies of one year do not create replication. Regional river systems and
nested gauges must still be distinguished in the full study. The implementation
does not pretend that a one-year local fold has regional statistical power.

### Conventional information and calibration strengthened

All arms continue to share the same current/lagged weather and model discharge.
H+A/H+A+E now also receive coordinates and prior-forcing precipitation/temperature
summaries. Each row's summaries use dates **strictly before January 1 of that
row's year**, including the 2017 warm-up; no current/future year or observed Q
enters those features. Training rows therefore do not borrow the later
validation-year climate. Common derived relative-humidity/wind-speed features
now match the declared forcing recipe. Daily RH derived from daily-mean inputs
is an approximation, not a new hourly humidity observation.

Regulation is checked against the held public inventory by exact provider ID.
Only Herzogenrath 1 has an exact match in this extract; its zero recorded dams
does not establish absence of weirs or other management. The six unmatched
local sites remain unknown. The register is diagnostic, not a partly future-
dated or zero-filled predictor. No new provider email or regulation-data gate
is introduced.

Two calibration references are executable and their curves/counts are saved:

- **Local monthly FDC mapping:** permitted pre-test clean observed/model pairs
  at the target, monthly curves with annual fallback, ties averaged and positive
  multiplicative upper-tail extrapolation. This uses extra target labels and
  is explicitly a locally calibrated reference.
- **Donor-FDC transfer:** donor selected from conventional descriptors, using
  training-only scaling and same-vintage descriptor snapshots. Donor observed/
  model quantile ratios are transferred through the target's **model-only**
  historical quantiles. No target observed discharge enters donor selection or
  this mapping. It is not labelled a SABER reproduction. Zero donor quantiles
  omitted from ratio estimation are counted; unsupported mappings stay missing.

Calibration is not assumed to help. The corrected local fold contains a large
upper-tail local-calibration overestimate on 14 July 2021 at Herzogenrath 1,
whose verification carries the inherited non-clean flag. No cap was introduced
after seeing it and no affected case was removed. Curves and adverse results
remain available for event review. This is a failure case to interpret, not an
established regional finding or proof that all calibration fails.

### Daily scope and policy framing retained

The outcome is **daily high-flow reconstruction**. Hourly/documented-flood
records contextualize the loss of sub-daily peak information. Daily predictions
are not scored against hourly maxima as if they predicted those peaks. Saved
paired day effects include symmetrically selected three largest improvements
and three largest harms; these are examples, not independent storm counts.

Policy interpretation concerns the trustworthiness and prerequisites of global
hydrological information where local calibration is unavailable: severe errors,
donor information, mapping limitations, measurement qualifications and cost.
Same-day retrospective reconstruction does not demonstrate warning lead time,
operator benefit, avoided losses or an optimal gauge-investment budget.

## Regional preparation and source audit

The physical screening evaluates up to eight nearby model segments against full
upstream contributing polygons; prediction errors are never used to choose a
reach. Direct upstream/downstream section relations identify nested groups and
local-label overlaps; distant tributaries are not collapsed solely because they
eventually share a downstream outlet.

The completed register has **336 provisional regional donors**, **50 reserved
external records**, four local connected-section exclusions and one source-network
coverage gap. Donor nesting forms 152 section components; external nesting has
11 section components within the **three reserved river systems**. Those 11 are
not 11 independent external river systems. The register carries **44 geometry-
review flags**, including unresolved/coverage cases. Low Dice scores can reflect
reference delineation errors, model representativeness or the wrong section;
neither a nearby line nor a finite discharge value proves identity. Flags are
not automatic outcome-selected exclusions or approvals. All candidate evidence
is saved for resolution and mapping-quality sensitivity.

The provisional reserved outlets are traced from named mainstem stations up to
an obvious large-area confluence jump. That boundary screen remains explicitly
reviewable; it does not prove river-name identity by itself. No weakly matched
case is silently certified as an exact gauge/model pair.

The primary CAMELS-DE-1h paper (§4–4.1) confirms **UTC and preceding-hour means**.
There is no second CET conversion. It also states that the release mixes provider
quality regimes and did not receive exhaustive direct QA. Thus a finite exported
value is not automatically independently verified. These limitations are recorded
in the [source audit](reviews/limburg-dise-source-qa-2026-11-16.json).

Two resumable workers acquired all **386 nonlocal, mapped source records**
for source QA, including flagged cases; zero transfers failed. All raw and daily
file hashes were independently reverified. There are **821,400 complete daily
observations in 2018–2024**; twelve source records have no complete daily overlap
and remain documented coverage cases. Raw snapshots occupy 3.66 GiB and daily
tables 84 MiB. Acquisition completed in 13.45 minutes; no workers remain active.
Raw member bytes are retained in gzip
with archive ETag/member CRC/uncompressed and compressed hashes; incomplete
daily windows stay missing. Individual record acquisition does not approve its
model mapping. No weather-forecast archive or full global ZIP is downloaded.

## Verification and execution state

- **37 tests pass**, including restored January dates, fixed populations,
  no future climate/target-label leakage, native-unit early stopping, calibration
  tail/zero handling, donor transfer and undefined bootstrap support.
- Ruff and the isolated dependency check pass.
- The corrected local fold completed **152 fits in 32.19 seconds**, with three
  seeds for each feature set under both selection policies.
- Original v1 code, configuration and outputs are unchanged. New output receipts
  pin code, configuration and data separately.
- Regional source acquisition is complete and resumable by file.
  Global model series/forcing/embedding acquisition for the regional pool and
  physical resolution of flagged identities still precede the full comparison.
  No full regional fit, GPU job, Azure offload or email was launched.

Commands use `.venv-dise`:

```sh
.venv-dise/bin/python scripts/264_prepare_dise_corrections.py features
.venv-dise/bin/python scripts/264_prepare_dise_corrections.py regional
.venv-dise/bin/python scripts/265_benchmark_dise_corrected.py
.venv-dise/bin/python scripts/266_acquire_dise_observations.py
```

Configuration: `config/limburg_dise_v2.json`. Completed benchmark:
`results/limburg_dise_v2/benchmark_local_wurm_2021/`. Acquisition status:
`results/limburg_dise_v2/regional_acquisition_progress.json`.

Final [verification receipt](reviews/limburg-dise-corrections-verification-2026-11-16.json)
records 74.8 GiB free against the 50-GiB reserve. Regional observations are source
data, not evidence that all candidate mappings or measurements are valid.
