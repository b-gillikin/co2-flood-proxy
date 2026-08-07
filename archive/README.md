# Archive

Code retired in two rounds — 2026-08-05 when the chapter was reframed, and
2026-08-06 when the reframe was carried through the tree. Kept because it ran,
produced results that are cited in the decisions log, and may be worth reading
if a later chapter revisits any of these questions. Nothing here is imported by
live code, and none of it is expected to run against the current data layout.
`archive` is excluded from ruff for the same reason.

`archive/results/` holds the outputs of retired code. They are kept as a record
of what was run, not as findings; none should be cited.

See `docs/chapter-direction.md` for the reframing and `docs/decisions.md` for
why each piece was withdrawn.

---

# Retired 2026-08-06

## Duplicate discharge ingest

`scripts/01_ingest_discharge.py`, `src/io_discharge.py`

A second pull against the same Waterschap endpoint as
`scripts/22_ingest_waterschap_gauges.py`, covering three of the same gauges and
writing `data/interim/discharge_hourly.csv` for the CO2 lane.

**Retired because two pipelines over one source had drifted apart.** The zero
sentinel fix landed in `22_` and not here, so the same gauge carried different
values depending on which file a script happened to read. That is the failure
mode duplication produces, and no test would have caught it.

`22_` now writes `discharge_hourly.csv` itself as a three-column projection.
The records agreed at r = 1.00000 on their overlap and the projection is a
strict superset — Wurm at Rimburg gains 7,684 hours, because this path took it
from the WVER feed, a rolling ten-day window rather than an archive.

Downstream consequence, verified rather than assumed: the longer record shifts
the event thresholds, so `18_precursor_skill.py` moved from 19 episodes to 20
and rainfall AUROC from 0.835 to 0.872. **The conclusion is unchanged** — every
CO2 predictor still spans 0.5.

## State-space detectors

`scripts/05_sarimax.py`, `scripts/06_kalman.py`, `src/detectors.py`,
`tests/test_detectors.py`, `results/sarimax/`, `results/kalman/`,
`results/models/`

The SARIMAX and Kalman residual detectors, and the 701-line detector library
they shared. Retired with the rest of the anomaly-detection lane below; these
two survived the first round only because they were imported from a different
module. `src/detectors.py` had no reader outside these two scripts and their
test.

## Distributed-lag antecedent-wetness test

`scripts/12_distributed_lag.py`, `results/distributed_lag/`

Tested whether the barometric CO2 residual co-moves with antecedent
precipitation at a multi-week lead. The preregistered rule returned
`NOT SUPPORTED`: the primary coefficient was not significant, the bootstrap
interval included zero, block replication was unavailable, and the future-rain
placebo failed. The result stands as a null and is recorded; the machinery
belongs to the retired CO2-as-hydrological-proxy framing.

## Weekly readiness reporting

`scripts/14_weekly_readiness.py`, `tests/test_weekly_readiness.py`,
`results/readiness/`, `results/evaluation/`

Project tracking rather than analysis. It read
`results/evaluation/evaluation_windows.csv`, written by the already-retired
`scripts/10_evaluation.py`, so it had no live input left.

## Barometric response function — RESTORED, only the outputs stay archived

`results/barometric_response/{barometric_response.txt, impulse_response.csv,
windowed_response.csv}`

`scripts/19_barometric_response.py` was archived here on 2026-08-06 and **moved
back to `scripts/` the same day.** Archiving it silently broke
`scripts/21_forward_gain_model.py`, which loads it by path
(`spec_from_file_location`) and whose detectability bound is a live result. The
breakage was invisible to the test suite and to ruff; it surfaced only on
running the script.

The distinction that matters, now recorded in that script's own docstring: the
response **shape** is withdrawn — 49 correlated lags under plain OLS, and it
rings — but the response **sum** is not. Script 21 uses only
`cumsum(impulse)[-1]`, a static gain, which is far better conditioned than any
individual coefficient. Its bound is unaffected.

The three output files above stay archived, because they report the shape.

Anyone quoting the shape needs regularisation first — ridge, or a constrained
lag form. The barometric *efficiency* estimate (0.20-0.34) is a separate and
sound result from `scripts/05b_barometric_efficiency.py` and is unaffected.

**Lesson for future archiving passes:** grep for `spec_from_file_location` and
path-based imports before moving a script. Import graphs built from `import`
statements alone will not see them.

---

# Retired 2026-08-05

## Ensemble anomaly detection

`scripts/07_isolation_forest.py`, `scripts/08_ensemble_agreement.py`,
`scripts/09_synthetic_injection.py`, `scripts/10_evaluation.py`

Three detector families scored the pressure-separated residual, with
cross-detector agreement on common coverage, synthetic-injection recovery
tests, and rolling-origin evaluation.

Retired because anomaly detection answers a different question than the chapter
asks. Detectors look for abrupt departures; the hydrological exposure is a slow
seasonal ramp with no events in it, and no adjudicated event labels exist to
validate a flag against. Once the chapter acquired labelled high-flow episodes
and a defined pre-event window, it became a detection problem with a ground
truth, which needs a forecasting comparison rather than an unsupervised
detector ensemble. See `scripts/18_precursor_skill.py`.

The engineering here was sound and the fits converged; it was aimed at the
wrong target.

## Cross-site transfer

`scripts/11_transfer_stress_test.py`, `scripts/04_ingest_rivm.py`,
`src/io_rivm.py`

Transfer of a site-fitted model to RIVM air-quality stations. Always secondary
and explicitly unable to block chapter completion. Under the reframed question
it has no role, and RIVM data existed only to serve it.

## Locked direct-state analysis

`scripts/16_direct_state.py`, `src/direct_state.py`

The confirmatory daily regression of residual CO2 on groundwater level, with
its prespecified criteria.

Retired for two reasons. The framing changed. And two of the criteria were
defective: the future-water placebo omitted the contemporaneous term, so with
an autocorrelated exposure it would have rejected a true association; and the
block-replication criterion could not be satisfied by an unbroken record,
because blocks break at any gap over one hour. Those criteria were generated
scaffolding rather than author decisions, but they had been implemented with
passing tests, which lent them the appearance of choices.

The groundwater loader `src/io_groundwater.py` is **not** archived. It
normalizes the BRO data the chapter still uses.

## Chapter draft checker

`scripts/17_check_chapter_draft.py`, `src/chapter.py`, `tests/test_chapter.py`

Validated `chapter/chapter-draft.md` against the four-branch claim structure and
its frozen-field tokens. Both the draft and the claim machinery are superseded;
the draft is retained only as a record of what was scaffolded.
