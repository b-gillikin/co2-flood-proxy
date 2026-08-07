# Discharge Source Status

This note preserves the distinction between source reconnaissance and the
prospective chapter input. The binding delivery contract is in
`data-requests.md`.

| live ingest | source role | limitation |
| --- | --- | --- |
| `22_ingest_waterschap_gauges.py` | public Waterschap inventory and rolling discharge reconnaissance | roughly 2024–2026; cannot pass the 10-year gate |
| `25_ingest_lanuk_nrw.py` | long German gauge reconnaissance and possible Wurm/Rur inputs | does not by itself provide the Limburg tributary cohort |
| `26_ingest_rws_maas.py` | Maas main-stem source validation | main stem is outside the primary tributary population |

The retired three-gauge WVER/Waterschap ingest and soft-label catalogue no
longer have a downstream reader. Their code and results remain in Git history
and the decisions log. No live script writes `data/interim/discharge_hourly.csv`.

The eventual analytical input is
`data/interim/event_study_discharge_hourly.csv`, built only after the requested
historical files and their metadata have been inspected. Do not rename a
rolling public export to satisfy that contract.
