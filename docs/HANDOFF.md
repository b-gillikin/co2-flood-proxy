# Session Handoff

Written 2026-08-07. Session state only; do not copy numbers from here into a
manuscript.

Read in this order:

1. `chapter-synthesis.md` — canonical question, contribution, design and state.
2. `chapter-scope-and-preregistration.md` — prospective estimator protocol.
3. `analysis-inventory.md` — prospective, contextual and stopped work.
4. `data-requests.md` — blockers and exact delivery contracts.

## Current chapter

> Which fixed public hydrometeorological signals recur before independently
> defined high-water onset, and do their direction and magnitude transfer to
> unseen Limburg watercourses and periods? At Kerkrade, does
> pressure-adjusted CO2 recur as a local manifestation of that regional state?

The sequence is Viefhues single-event observation -> Eryilmaz same-site public
explanation -> recurrence and spatial transfer. July 2021 is a required
interval-censored anchor.

There is one prospective analysis and no outcome classifier: compare each
fixed pre-event signal with matched quiet times, aggregate event contrasts
within watercourse, learn the reference contrast outside one watercourse and
one period, and compare it with the hidden events. The only fitted equation is
the quiet-period, sensor-era-specific pressure adjustment for Kerkrade CO2.

SARIMAX, Kalman filters, anomaly detection, operational alerts and model-family
search remain out of scope.

## Cleanup completed

- Deleted the unreproducible later-record precursor script. Its input-producing
  exploratory script had already been retired.
- Deleted the three-gauge soft-label catalogue, full-period CO2 baseline and
  their generic evaluation/feature/facade modules and tests.
- Removed the rolling-discharge projection from the Waterschap ingest. The
  rolling network remains source reconnaissance only.
- Simplified `update_data.py` and `01_eda.py` to later-era Kerkrade IoT/weather
  QC plus the Eryilmaz context frame.
- Retained `03_eryilmaz_replication.py` as the only completed analytical script;
  it ran successfully after the cleanup.
- Removed unused RIVM fixtures, stale generated repository maps, a dead shared
  fetching module, unused name helpers and the broken local KNMI launchd path.
- Reduced `environment.yml` to dependencies used by the live root analysis.
- Aligned the README, source notes, inventory, scope, protocol and append-only
  decision history with the contrast-only chapter.

The active analytical code is now `src/event_study.py`, the gate audit, the
small Eryilmaz context script and direct source ingests. The cloud collection
service under `kerkrade_data/` remains operational infrastructure, not chapter
analysis. Retired code remains explicitly isolated under `archive/` or in Git
history.

## Feasibility corrections found in the pass

Two missing contracts would otherwise have allowed post-outcome choices:

1. Temperature, humidity and pressure had no long-record input or prospective
   watercourse assignment. The gate now requires a tidy 10-year weather table
   plus one documented source/assignment row per watercourse. The source and
   rule still need supervisor agreement.
2. The Kerkrade recurrence question had no minimum usable later-event sample.
   The gate now requires at least three exact pair-gauge p99 onsets with every
   CO2 and pressure hour observed from -72 to -1. Fewer events are absence of
   recurrence evidence, not a null result.

Gauge coordinates, non-overlapping metadata for both IoT sensor periods and
explicit July 2021 onset bounds are also now required because the distance-only
donor rule, era-specific adjustment and censored anchor cannot be reproduced
without them.

## Gate state

Run:

```bash
python scripts/31_event_study_gates.py --report-only
```

There are nine contracted inputs. The held later IoT file passes its file gate;
the other eight are absent:

- `data/interim/viefhues_iot.csv`
- `data/interim/kerkrade_iot_eras.csv`
- `data/interim/event_study_discharge_hourly.csv`
- `data/interim/event_study_gauges.csv`
- `data/interim/radolan_catchment_hourly.csv`
- `data/interim/event_study_catchments.gpkg`
- `data/interim/event_study_weather_hourly.csv`
- `data/interim/event_study_weather_sources.csv`

The detailed downstream gate branches cannot run until all files exist. The
rolling Waterschap file, held point rainfall and current city-weather table may
not be renamed into these contracts.

## Next steps, in order

1. Take the exact question, contrast-only estimand, strict gates and planned
   null readings to the supervisor. Also settle the long public-weather source
   and watercourse-assignment rule.
2. In parallel, request the original Viefhues IoT package and full historical
   Waterschap tributary data using `data-requests.md`; complete the current
   sensor-era calibration/ABC record.
3. Inspect the delivered native discharge/QA files, choose one representative
   per natural watercourse without viewing contrasts, and establish the
   Kerkrade pair plus July 2021 lower/upper onset bounds.
4. Only after the cohort is fixed, build and visually verify catchment polygons,
   RADOLAN averages and the chosen public-weather assignment.
5. Populate all nine contracts and run the binding gate without
   `--report-only`. If any gate fails, return to the supervisor rather than
   lowering it.
6. If it passes, record input hashes, supervisor approval, Git commit and lock
   draft 0.2 before inspecting outcomes.
7. Then implement one transparent script:
   `load -> check -> events/controls -> contrasts -> storm uncertainty -> tidy tables -> four figures`.
   Add the remaining RADOLAN spatial/no-data tests against the real format.

Do not implement the outcome script or a guessed RADOLAN parser while the files
are absent. Do not revive the hourly classifier or add time-series model
families to compensate for a failed gate.

## Verification

Named environment:
`/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`

- `python -m pytest -q`: **41 passed**
- `ruff check .`: passed
- `ruff format --check .`: 59 files formatted
- all live CLI `--help` imports: passed
- Azure shell syntax checks: passed
- context refresh and Eryilmaz re-evaluation: ran successfully
- `git diff --check`: passed
- gate audit: expected **FAIL**; later IoT file present, eight contracts absent

The worktree is intentionally uncommitted and also contains pre-existing edits
from the prior sessions, including the bibliography update. Preserve it as one
coherent chapter reset.
