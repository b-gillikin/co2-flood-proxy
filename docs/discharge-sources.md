# Discharge Source Status

This note preserves the distinction between source reconnaissance and the
prospective chapter input. The binding delivery contract is in
`data-requests.md`.

| live ingest | source role | limitation |
| --- | --- | --- |
| `22_ingest_waterschap_gauges.py` | public Waterschap inventory and rolling discharge reconnaissance | roughly 2024–2026; cannot pass the 10-year gate |
| `25_ingest_lanuk_nrw.py` | long German gauge reconnaissance | irregular timestamp semantics remain unverified; held archive does not pass the draft cohort gate |
| `32_lanuk_feasibility.py` | metadata, density, gap, p99-episode and watercourse audit | input QA only; no signal outcomes |
| `26_ingest_rws_maas.py` | Maas main-stem source validation | main stem is outside the primary tributary population |

The retired three-gauge WVER/Waterschap ingest and soft-label catalogue no
longer have a downstream reader. Their code and results remain in Git history
and the decisions log. No live script writes `data/interim/discharge_hourly.csv`.

The eventual analytical input is
`data/interim/event_study_discharge_hourly.csv`, built only after the requested
historical files and their metadata have been inspected. Do not rename a
rolling public export to satisfy that contract.

The reproducible German-route decision is in `lanuk-feasibility.md`. In
particular, official HYGON metadata place `herzogenrath_2` on Broicher Bach and
`honsdorf` on Beeckflies. The held Wurm series are `herzogenrath_1` and
`randerath`, neither of which supplies the July 2021 event window in the held
archive or overlaps the later IoT era. Archive gaps alone are not
onset-censoring bounds.
