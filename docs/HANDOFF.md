# Session Handoff

Written 2026-08-08. Session state only; use the synthesis and protocol for
chapter claims.

Read in this order:

1. `chapter-synthesis.md` — canonical question, contribution, design and state.
2. `chapter-scope-and-preregistration.md` — draft 0.5 estimator protocol.
3. `supervisor-decision-memo.md` — choices requiring supervisor approval.
4. `data-requests.md` and `external-request-drafts.md` — blockers and messages.
5. `lanuk-feasibility.md` — reproducible decision on the held German route.
6. `analysis-inventory.md` — live, secondary and stopped work.

## Current chapter

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and how
> does their event-minus-quiet signal change with distance from the affected
> watercourse? If the source data support a Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

The sequence is Viefhues's July 2021 observation -> Eryilmaz's same-site public
weather explanation -> this chapter's recurrence and spatial-extent test.

Transferability now means **spatial extent**. The chapter has two linked
estimands from the same matched event study:

1. local event-minus-quiet contrasts establish which fixed public signals
   recur at the affected watercourse;
2. all-donor contrasts evaluate those signals at every other eligible
   watercourse and estimate how magnitude changes with
   `log(1 + distance_km)`.

One prespecified mixed-effects model per signal uses receiver, donor and
regional-storm random intercepts. It reports the curve at empirical distance
quartiles and validates
fixed-effect magnitude at crossed held-out receiver-period intersections. It
does not estimate physical travel time, a maximum reach, gauge substitution or
an ungauged-basin effect. There is no classifier, alert evaluation,
SARIMAX/Kalman lane or model-family search.

## Implemented state

- `scripts/31_event_study_gates.py` separates the binding six-file regional
  core from the conditional Kerkrade case.
- The core gate now enumerates every ordered receiver-donor pair, calculates
  great-circle distance, verifies near/middle/far support and audits complete
  donor-flow windows overall, by receiver and by distance third.
- The unused nearest-donor/sign-concordance helper and tests were removed.
  Outcome mixed-model code has deliberately not been written before the data
  gate and protocol lock.
- Five dated review passes were moved from live `docs/` to
  `archive/docs/reviews/`. Live documents now have distinct operational roles;
  the append-only decisions log remains in place.
- A 63 MB Viefhues package is held locally and ignored by Git. It contains a
  cleaned hourly table spanning 2020-08-25 to 2021-09-24, raw May–September
  2021 Kerkrade files and the historical ABC-processing code. The cleaned
  pre-May provenance, calibration and device history still require audit.

## Current audit state

Run:

```bash
python scripts/31_event_study_gates.py --report-only
```

Expected result:

- **Core regional chapter: FAIL** — all six contracted network files are absent.
- **Conditional Kerkrade CO2 case: NOT AVAILABLE** — the later IoT file exists,
  but the delivered historical package has not been normalised to
  `viefhues_iot.csv` and the sensor-era contract is absent.

The source delivery is progress on a conditional case; it does not change the
binding regional stop. Do not lower the ten-year cohort gate or inspect public-
signal outcomes before approval and lock.

## Student actions now

1. Take `supervisor-decision-memo.md` to the supervisor and approve or revise:
   the all-donor spatial-gradient estimand, study population, density and
   all-donor availability floors, public-weather source/assignment, held-out
   occupancy rule and July 2021 regional treatment.
2. Personalise and send the Waterschap and LANUK drafts in
   `external-request-drafts.md`; preserve the native replies and metadata.
3. Use the Viefhues follow-up draft only for device, calibration, ABC or source-
   provenance questions that cannot be resolved from the delivered package.
4. Do not lock draft 0.5 until the core gate passes and the supervisor decisions
   are recorded.

## Agent work after those actions

1. Normalise and audit the delivered Viefhues package without changing its raw
   files; reconstruct the pre-May provenance before declaring the case usable.
2. Inspect native discharge deliveries before writing their ingest; resolve
   timezone, units, rating curves, sampling semantics, natural/managed status
   and July 2021 reliability.
3. Fix the cohort, build and visually verify catchment polygons, RADOLAN
   averages and the approved public-weather assignment, then rerun the strict
   gate.
4. If the core passes, record input hashes and supervisor approval, lock the
   protocol, and only then implement the concise contrast/distance analysis and
   its synthetic decay, flat, null, heterogeneous and held-out tests.
5. Add the Kerkrade recurrence section only if its separate gate passes; missing
   case evidence is not a null CO2 result.

## Verification

Named interpreter:
`/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`

- full test suite: **53 passed**;
- `ruff check .`: passed;
- `ruff format --check .`: 62 files already formatted;
- split gate report regenerated: regional core **FAIL**, conditional case
  **NOT AVAILABLE**;
- raw Viefhues package remains untracked by design;
- this state is committed on `main`; use `git log -1` for the commit identifier.
