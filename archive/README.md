# Archive

Code retired on 2026-08-05 when the chapter was reframed. Kept because it ran,
produced results that are cited in the decisions log, and may be worth reading
if a later chapter revisits any of these questions. Nothing here is imported by
live code, and none of it is expected to run against the current data layout.

See `docs/chapter-direction.md` for the reframing and `docs/decisions.md`
(2026-08-05) for why each piece was withdrawn.

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
