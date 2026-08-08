# Session Handoff

Written 2026-08-08. Session state only; use the synthesis and protocol for
chapter claims.

Read in this order:

1. `chapter-synthesis.md` — canonical question, contribution, design and state.
2. `chapter-scope-and-preregistration.md` — draft 0.3 estimator protocol.
3. `lanuk-feasibility.md` — reproducible decision on the held German route.
4. `supervisor-decision-memo.md` — choices that require supervisor approval.
5. `external-request-drafts.md` — prepared messages; none has been sent.
6. `analysis-inventory.md` and `data-requests.md` — live work and blockers.

## Current chapter

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and do
> their direction and magnitude remain visible at an unseen watercourse and
> period? At Kerkrade, does pressure-adjusted CO2 recur as a local
> manifestation of that regional state?

The sequence is Viefhues's July 2021 observation -> Eryilmaz's same-site public
weather explanation -> this chapter's recurrence and spatial-transfer test.
The sole prospective estimand is an event-minus-matched-quiet signal contrast.
There is no classifier, alert evaluation, SARIMAX/Kalman lane or model-family
search. July 2021 remains a required interval-censored anchor.

## Work completed on 2026-08-08

- Hardened the input gate against endpoint-only records: events and storms are
  counted within the joint period, every primary series has draft 80% overall
  and 70% annual density requirements, July 2021 must lie in the joint period,
  catchment polygons are opened and checked, and each distance-selected donor
  must have complete level/change inputs for 80% of receiver events.
- Made the analysis definitions match the protocol: the 72-hour episode rule
  exposes single-linkage chain diagnostics, controls explicitly respect the
  held time block and require at least three valid matches, transfer inputs must
  carry fold-specific thresholds/scaling/event construction, and every empty or
  sparse fold remains visible.
- Added a reproducible LANUK feasibility audit using official station and HYGON
  metadata. Under the draft density plus 20-episode rule, the best held decades
  (2014–2023 and 2015–2024) contain only 3 passing gauges across 2 verified
  watercourses. The held German archive is source reconnaissance, not a
  qualifying cohort.
- Corrected the Kerkrade pairing. `herzogenrath_2` is Broicher Bach and
  `honsdorf` is Beeckflies. The held Wurm gauges are `herzogenrath_1` and
  `randerath`; neither covers July 2021 or overlaps the later IoT era. The 2 and
  1 later complete windows on the former gauges are not Wurm recurrence.
- Reworked the retained Eryilmaz context script. Its expanding tests are now
  calendar-defined before complete-case filtering; each fold reports dates,
  coverage, positives and the longest outage. Random hourly folds and a mean
  AUROC headline were removed. This remains predecessor context, not chapter
  evidence.
- Prepared but did not send requests for the original Viefhues data, historical
  Waterschap Limburg discharge and LANUK timestamp semantics.
- Prepared a supervisor memo covering transferability, population, density,
  fold occupancy, public-weather assignment and July 2021 evidence.
- Marked the prework DOCX files as historical. Moved ignored outputs from the
  retired baseline, precursor, soft-label and hourly-classifier lanes to
  `archive/results/retired_2026_08_08/`; they remain recoverable.
- Preserved both independent chapter reviews in `docs/` and appended new
  decisions rather than rewriting the historical log.

## Gate state

Run:

```bash
python scripts/31_event_study_gates.py --report-only
```

The expected result is **FAIL**. Only the later IoT contract exists. These eight
inputs are absent:

- `data/interim/viefhues_iot.csv`
- `data/interim/kerkrade_iot_eras.csv`
- `data/interim/event_study_discharge_hourly.csv`
- `data/interim/event_study_gauges.csv`
- `data/interim/radolan_catchment_hourly.csv`
- `data/interim/event_study_catchments.gpkg`
- `data/interim/event_study_weather_hourly.csv`
- `data/interim/event_study_weather_sources.csv`

This is a data and design-approval stop. Do not rename rolling or point-source
files to satisfy the contracts, lower the gate from outcome results, or build
the event-contrast script before the protocol is locked.

## Student actions now

1. Take `supervisor-decision-memo.md` to the supervisor and record decisions on
   the question, whether the crossed contrast qualifies as transferability,
   the population, density, fold occupancy, public-weather source/assignment
   and the evidence required for the July 2021 interval.
2. Personalise and send the three messages in `external-request-drafts.md`.
   Preserve the sent text, attachments and raw replies.
3. Assemble the known metadata for the current 2025–2026 IoT era: device ID,
   calibration/replacement history, ABC processing and source resolution.
4. Do not lock draft 0.3 yet. The density, donor-availability and fold-occupancy
   numbers are recommendations pending approval.

## Work after the replies

1. Inspect native deliveries before writing ingests; resolve timezone, units,
   rating curves, missingness semantics, natural/managed status and July 2021
   reliability.
2. Rebuild the candidate cohort and rerun the strict feasibility gate. Return
   to the supervisor if fewer than ten watercourses, ten common years, twenty
   episodes each, forty storms or three later Kerkrade-pair events remain.
3. After the cohort is fixed, build and visually verify catchment polygons,
   RADOLAN averages and the approved public-weather assignment.
4. Populate all nine contracts, run the binding gate without `--report-only`,
   record hashes/approval/commit and lock the protocol before inspecting signal
   outcomes.
5. Only then implement one transparent analysis script:
   `load -> define events/controls -> contrasts -> storm uncertainty -> tidy tables -> four figures`.

## Verification

Named interpreter:
`/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`

- full test suite: **54 passed**;
- `ruff check .`: passed;
- `ruff format --check .`: **67 files** already formatted;
- `git diff --check`: passed;
- LANUK audit regenerated successfully;
- Eryilmaz context analysis regenerated successfully;
- hard-gate report regenerated with the expected eight missing contracts.
