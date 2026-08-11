# Discharge Source Status

This note separates source reconnaissance from the prospective chapter input.
The binding delivery contract is in `data-requests.md`.

| live script | source role | limitation |
| --- | --- | --- |
| `25_ingest_lanuk_nrw.py` | acquire long German gauge records for the documented feasibility route | held archive does not pass the draft cohort gate |
| `32_lanuk_feasibility.py` | audit metadata, density, gaps, p99 episodes and watercourse identity | input QA only; no signal outcomes |

The public rolling Waterschap pull and RWS main-stem validation were removed
from the live tree. Neither can produce the qualifying ten-year natural-
tributary cohort. Their code remains in Git history.

The eventual analytical input is
`data/interim/event_study_discharge_hourly.csv`, built only after the requested
historical files and metadata are inspected. Do not rename a rolling public
export to satisfy that contract.

The reproducible German-route decision is in `lanuk-feasibility.md`. Official
HYGON metadata place `herzogenrath_2` on Broicher Bach and `honsdorf` on
Beeckflies. The held Wurm series are `herzogenrath_1` and `randerath`; neither
provides both the July 2021 event window and later-IoT overlap. Archive gaps
alone are not onset-censoring bounds.
