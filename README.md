# Pre-High-Water Signals Across Limburg Tributaries

Prospective research question (protocol draft 0.9):

> Across natural Limburg tributaries, how are public hydrometeorological
> signals in the 72 hours before independently defined high-water onset
> associated with that onset, and does the timing of that association differ
> between warm-season and cold-season events?

Design: a **time-stratified case-crossover study**, analysed with conditional
quasi-Poisson distributed-lag models. The draft 0.8 distance slope and
conditional Kerkrade CO2 case were dropped on 2026-09-18; see `decisions.md`.
The repository keeps its historical `chapter1-co2` name.

Status: **data-gated; no chapter result exists**. The 2001--2025 ERA5-Land
archive is complete and audited. The 2010--2025 Waterschap discharge delivery
has passed an outcome-blind availability audit. Timezone, zero semantics,
coordinates and cohort classification remain open. Radar rainfall and
cross-border catchments are not yet acquired. The protocol is unlocked and no
outcome analysis has been run.

Viefhues's Kerkrade CO2 observation and Eryilmaz's public-weather explanation
motivate the question. The chapter analyses no CO2.

## Read first

| document | role |
| --- | --- |
| `docs/chapter-synthesis.md` | canonical question, contribution, design and status |
| `docs/chapter-scope-and-preregistration.md` | draft 0.9 case-crossover protocol; lock only after gates pass and floors are recorded |
| `docs/scope-decisions.md` | concise live choices |
| `docs/analysis-inventory.md` | prospective, supporting and stopped work |
| `docs/data-requests.md` | exact blockers and delivery contracts |
| `docs/supervisor-decision-memo.md` | 2026-08 supervisor response (historical record) |
| `docs/student-next-actions.md` | student tasks and send-ready requests |
| `docs/literature-source-notes.md` | source-by-source notes without synthesis |
| `docs/literature-evidence-matrix.csv` | evidence-question/source relationships |
| `docs/chapter-references.bib` | verified retained bibliography |
| `docs/dissertation-research-and-code-guidelines.md` | reusable scoping, evidence and data-science coding standard for all chapters |
| `docs/HANDOFF.md` | current session state only |

`chapter-prework/` retains the two supplied predecessor PDFs and its README.
The Viefhues delivery is external raw material and is ignored by Git.

## Run the input audits

```bash
conda env create -f environment.yml
conda activate chapter1-co2
python scripts/31_event_study_gates.py --report-only
python scripts/32_lanuk_feasibility.py
python scripts/35_audit_waterschap_delivery.py
```

`--report-only` writes the known failed regional audit without treating it as a
chapter result. Omit that flag only when all six contracted regional inputs
exist. The gate script still encodes the draft 0.8 floors until it is updated
to draft 0.9 (see `docs/draft-0.9-implementation-plan.md`).

ERA5-Land was backfilled through the dedicated Azure Function documented in
`infrastructure/era5_backfill/README.md`. The archive is complete and the timer
is disabled because the backfill-only Function App is stopped. A complete
ignored working copy is in `data/raw/era5_land/`; its
small checksum manifest is versioned as `data/processed/era5_land_manifest.csv`.
The local command remains a restart-safe fallback:

```bash
python scripts/34_fetch_era5_land.py
```

The script writes one validated monthly NetCDF plus a checksum manifest.

The Kerkrade IoT and Viefhues ingests (`01_ingest_iot.py`,
`33_ingest_viefhues_iot.py`) belonged to the retired conditional CO2 case. They
remain in the repository as provenance for the motivating observation and are
not part of the draft 0.9 analysis.

## Planned analysis

High-water onsets are adjacent-hour crossings of each watercourse's own p99.
Each onset hour is compared with at-risk hours from the same watercourse, year,
month and hour of day. For each exposure, a conditional quasi-Poisson model with
a distributed-lag cross-basis over lags 1–72 hours estimates how the onset rate
relates to the signal at each preceding hour. The primary estimand is the
warm-minus-cold-season difference in the rainfall lag-response. Uncertainty
comes from a calendar year-month block bootstrap.

There is no classifier, predictive validation, SARIMAX, Kalman filter,
model-family search or degree-of-freedom search.

## Verify

```bash
python -m pytest -q
python -m pytest infrastructure_tests -q  # only when legacy collection changes
ruff check .
ruff format --check .
```

## Working conventions

- Hourly UTC; missing hours remain missing and crossings never bridge gaps.
- One predeclared gauge per natural, hydrologically independent watercourse;
  branches of one split system count once.
- Receiver flow defines onset and is never its own signal.
- Hourly catchment rainfall is the principal exposure; ERA5-Land relative
  humidity and six-hour pressure change form the atmospheric block.
- Every hydrological quantity is a within-gauge, within-rating-era rank.
- Censor an onset only when the onset hour itself is missing, failed or outside
  the rating domain.
- Null and heterogeneous results are final results, not invitations to add
  models, lags or thresholds.
- No flood-prediction, causal, FEWS, warning-lead, trigger, monitoring-placement
  or ungauged-basin claim.
