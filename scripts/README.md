# Scripts

The live scripts are data acquisition, input QA or small transparent analyses.
New chapter code should read as:

`load -> check -> define events/controls -> estimate -> tidy tables -> figures`

There is no analysis framework or model registry.

| script/module | purpose | state |
| --- | --- | --- |
| `01_ingest_iot.py` | normalise later Kerkrade IoT for the conditional case | implemented |
| `25_ingest_lanuk_nrw.py` | acquire the held German discharge source used by the feasibility audit | implemented; source does not pass |
| `31_event_study_gates.py` | audit the six binding regional inputs and all-donor support | implemented; regional gate fails |
| `32_lanuk_feasibility.py` | audit German metadata, gaps, density and episode counts without signal outcomes | implemented; German route fails |
| `33_ingest_viefhues_iot.py` | normalise source-native July 2021 K4 CO2/pressure and write QC | implemented |
| `34_fetch_era5_land.py` | local fallback for the fixed 2001–2025 weather grid | implemented; archive complete, fallback only |
| `src/event_study.py` | definitions for episodes, storms, controls, censoring and conditional CO2 adjustment | implemented and unit-tested |
| event-contrast script | local recurrence, pair medians, distance slopes and four figures | not written or run before gates and lock |

Safe input-only commands:

```bash
python scripts/31_event_study_gates.py --report-only
python scripts/32_lanuk_feasibility.py
python scripts/33_ingest_viefhues_iot.py
```

The ERA5-Land Azure backfill completed and its timer is disabled. Do not start
`34_fetch_era5_land.py` without first confirming that no cloud request is
active; both paths use the same CDS account and fixed monthly request sequence.

The eventual outcome script should be one direct pandas/statsmodels-style
analysis, split only if the figures make it unreadable. Add helpers only for a
scientific definition reused in more than one place or requiring an isolated
check. Comment choices such as censoring and window completeness, not obvious
syntax.

## Retired from the live tree

The later-era Eryilmaz re-fit, Visual Crossing join, rolling two-year Dutch
gauge pull, Maas main-stem validation and DWD point-rain sensitivity were
removed. The Eryilmaz paper remains predecessor evidence; those extra pipelines
did not answer the prospective chapter question. Older prediction matrices,
classifiers, filters, anomaly detectors and generic substitution machinery were
already retired. Git history and `docs/decisions.md` preserve the audit trail.

## Verification boundary

`pytest -q` covers scientific definitions and input semantics. The older IoT
collection checks live in `infrastructure_tests/` and run only when that
collection machinery changes. New parsers should first be checked against the
delivered file and a tidy QC artifact; do not add fixture tests by default.
