# Discharge Source Status

This note separates source reconnaissance from the prospective chapter input.
The binding delivery contract is in `data-requests.md`.

| live script | source role | limitation |
| --- | --- | --- |
| `25_ingest_lanuk_nrw.py` | acquire long German gauge records for the documented feasibility route | held archive does not pass the draft cohort gate |
| `32_lanuk_feasibility.py` | audit metadata, density, gaps, p99 episodes and watercourse identity | input QA only; no signal outcomes |
| `35_audit_waterschap_delivery.py` | audit the delivered 2010–2025 Dutch grid | raw availability plus separate source QA; fixed GMT+1 and true-zero semantics confirmed 2026-09-29 |

The public rolling Waterschap pull and RWS main-stem validation were removed
from the live tree. Neither can produce the qualifying ten-year natural-
tributary cohort. Their code remains in Git history.

Waterschap Limburg delivered 15 quarter-hour series columns on an exact
2010--2025 grid. The value-equivalent CSV is the simple audit source; the XLSX,
EML and rendered mailbox PDF remain preserved native artifacts. All six cohort
gauges (D3, 2026-09-18) pass the provisional availability rule
(`data/processed/waterschap_discharge_qc.csv`). The 2026-09-07 follow-up
defines trailing 15-minute means and blank semantics, supplies rating curves
and documents July 2021 failures and range exceedances. It also confirms that
no validation flags exist. René's 2026-09-29 reply resolves fixed UTC+1 and
genuine-zero semantics.
Availability does not establish usability on its own; see
`waterschap-source-metadata.md`.

The analytical input is `data/interim/event_study_discharge_hourly.csv`.
`scripts/45_build_event_study_discharge.py` built it after source semantics
were verified. Do not rename a raw delivery or rolling public export to
satisfy that contract.

The older public-archive German-route decision is in `lanuk-feasibility.md`;
its sparse-record conclusion does not apply to the four continuous 15-minute
exports delivered 2026-09-23. See `cross-tributary-pilot-2026-10-03.md` for
their preliminary compatibility audit. Official
HYGON metadata place `herzogenrath_2` on Broicher Bach and `honsdorf` on
Beeckflies. The Wurm stations are `herzogenrath_1` and `randerath`; they are
nested observations of one watercourse, not two independent tributaries. The
old public-archive gaps are not onset-censoring bounds; assess the new
quarter-hour deliveries on their own terms.
