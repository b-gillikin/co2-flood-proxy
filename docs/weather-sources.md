# Visual Crossing Weather Source Notes

## Azure source

Task 1.2 currently uses the Visual Crossing weather CSVs already collected into
Azure Blob Storage, rather than calling the Visual Crossing API directly.

- Subscription: Azure for Students
- Resource group: `rg-kerkrade-prod`
- Storage account: `stkerkradeprod01bg`
- Containers:
  - `kerkrada-weather-data`
  - `maastricht-weather-data`
  - `aachen-weather-data`
  - `liege-weather-data`

The local ingestion script pulls monthly `weather_*.csv` blobs from each
container. It then performs a direct Kerkrade Visual Crossing catch-up for the
current month and, when missing locally, the previous month. These files contain
local civil timestamps without an explicit offset, so ingestion localizes them
to Europe/Amsterdam time before converting to UTC. Kerkrade, Maastricht,
Aachen, and Liege share the same CET/CEST transitions.

On 2026-06-06, Kerkrade May 2026 and June 2026 through 2026-06-06 were pulled
directly from the Visual Crossing API with the same hourly element set used by
the Azure Function code, because those months were not yet present in the Azure
weather blob container.

## Local outputs

- Raw monthly CSVs: `data/raw/weather/<container>/weather_<Location>_YYYY-MM.csv`
- Long hourly output: `data/interim/weather_hourly_long.csv`
- Wide hourly output: `data/interim/weather_hourly.csv`

Run all available refreshes with:

```bash
python scripts/update_data.py
```

Rebuild normalized files from already downloaded raw files with:

```bash
python scripts/update_data.py --skip-download
```
