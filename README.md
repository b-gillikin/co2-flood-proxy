# Pre-High-Water Signal Recurrence and Spatial Extent

Prospective research question:

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and how
> do the direction and magnitude of their event-minus-quiet contrasts change
> with distance from the affected watercourse? If the source data support a
> Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

Status: **data-gated; no new chapter result exists**. ERA5-Land acquisition is
running unattended in Azure, but the repository still lacks the qualifying
long discharge cohort, catchment polygons and RADOLAN catchment rainfall. The
protocol is unlocked and the outcome analysis has not been run.

The dissertation sequence is:

1. Viefhues observes an indoor CO2 response around one exceptional event at
   one Kerkrade house.
2. Eryilmaz shows that public weather explains much of the same-site indoor
   information outside the flood period.
3. This chapter tests which public signals recur before independently defined
   high water and how their contrasts vary with distance across the observed
   tributary network.

Transferability means **spatial extent**, not prediction, gauge substitution,
physical propagation, an operational radius or performance in ungauged basins.

## Read first

| document | role |
| --- | --- |
| `docs/chapter-synthesis.md` | canonical question, contribution, design and status |
| `docs/chapter-scope-and-preregistration.md` | estimator protocol; lock only after gates and approvals |
| `docs/scope-decisions.md` | concise live choices |
| `docs/analysis-inventory.md` | prospective, supporting and stopped work |
| `docs/data-requests.md` | exact blockers and delivery contracts |
| `docs/supervisor-decision-memo.md` | approvals and unresolved numerical floors |
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
python scripts/33_ingest_viefhues_iot.py
```

`--report-only` writes the known failed regional audit without treating it as a
chapter result. Omit that flag only when all six contracted regional inputs
exist. The Kerkrade case is assessed separately.

ERA5-Land now backfills through the dedicated Azure Function documented in
`infrastructure/era5_backfill/README.md`; closing this laptop does not stop it.
The local command is a restart-safe fallback and must not run while the Azure
timer is enabled:

```bash
python scripts/34_fetch_era5_land.py
```

The script writes one validated monthly NetCDF plus a checksum manifest.

Refresh the later Kerkrade IoT record, if needed for the conditional case, with:

```bash
python scripts/01_ingest_iot.py
```

## Planned analysis

The chapter uses one quantity: signal in the pre-event window minus the median
signal at matched quiet times. Local contrasts establish recurrence. Spatial
contrasts are aggregated to one median per ordered receiver-donor pair and one
prespecified line is fitted for each signal:

```text
pair_median_contrast ~ 1 + log(1 + distance_km)
```

Uncertainty resamples complete regional storms. Leave-one-watercourse-out
refits are influence checks. There is no classifier, time-block validation,
mixed-effects model, SARIMAX, Kalman filter or model-family search.

## Verify

```bash
python -m pytest -q
python -m pytest infrastructure_tests -q  # only when legacy collection changes
ruff check .
ruff format --check .
```

## Working conventions

- Hourly UTC; missing hours remain missing and crossings never bridge gaps.
- One predeclared gauge per natural tributary watercourse.
- Receiver flow defines high-water onset and is not its own signal.
- RADOLAN catchment rainfall and donor flow are principal hydrological signals.
- ERA5-Land temperature, humidity and pressure form one fixed atmospheric block.
- Every eligible receiver-donor pair is retained; each ordered pair has equal
  weight in the distance analysis and must have at least 10 complete events.
- Aggregate events within watercourse before describing the network.
- Null and heterogeneous results are final results, not invitations to add
  models, lags or thresholds.
- No flood-prediction, causal, FEWS, alert, monitoring-placement or ungauged-
  basin claim.
