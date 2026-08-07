# Kerkrade IoT Source Notes

## Azure source

Task 1.1 uses the production Azure storage account and container already fed by
the Kerkrade Blynk polling function.

- Subscription: Azure for Students
- Resource group: `rg-kerkrade-prod`
- Function app: `func-kerkrade-monthly-pull-bg`
- Storage account: `stkerkradeprod01bg`
- Container: `air-quality-device-data-1`
- Blob prefix: `air_quality`

The function app stores Blynk readings as daily CSV blobs named
`air_quality_YYYY-MM-DD.csv`. The source function writes the `updated` field
with `datetime.now(timezone.utc)`, so ingestion treats these timestamps as UTC.

The local ingestion script uses the Azure CLI login on this machine and
`--auth-mode key`; it does not store Azure connection strings, Blynk tokens, or
Visual Crossing API keys in the repository.

## Local Blynk exports

Additional Blynk device exports can be placed in `iot-device-data/`. The folder
is treated as raw local data, is ignored by git, and is merged by
`scripts/01_ingest_iot.py` when present.

The current local export set adds two pre-Azure device windows:

| Source | Device | Device ID | Coverage |
| --- | --- | --- | --- |
| Blynk export | Mantingh Basement 1 | `455022` | 2025-01-31 00:00 to 2025-02-27 16:09 UTC |
| Blynk export | Mantingh Basement 2 | `455025` | 2025-06-26 15:00 to 2025-10-08 13:00 UTC |
| Azure blob | Kerkrade air-quality device 1 | `air-quality-device-data-1` | 2026-03-16 21:58 to 2026-04-13 02:36 UTC |

Blynk export timestamps are local Europe/Amsterdam civil time in the CSVs. The
loader converts them to UTC before hourly aggregation. Duplicate rows within a
device/timestamp are resolved by preferring the more detailed source file.

Interpretation caveat: the merged hourly IoT frame is the input for the retained
Eryilmaz context check, but it is not one uninterrupted single-device record and
does not contain July 2021. Source, device, and coverage-gap reports should
travel with any interpretation. The event study additionally requires
`kerkrade_iot_eras.csv`; see `data-requests.md`.

## Local outputs

- Raw daily CSVs: `data/raw/iot/air_quality_YYYY-MM-DD.csv`
- Hourly aligned output: `data/interim/iot_hourly.csv`
- Source summary: `data/processed/iot_source_summary.csv`
- Hourly CO2 coverage gaps: `data/processed/iot_coverage_gaps.csv`

Run all available refreshes with:

```bash
python scripts/update_data.py
```

Rebuild normalized files from already downloaded raw files with:

```bash
python scripts/update_data.py --skip-download
```

To rebuild the IoT stream directly from cached raw files plus local exports:

```bash
python scripts/01_ingest_iot.py --skip-download
```

For an Azure-only rebuild that ignores `iot-device-data/`:

```bash
python scripts/01_ingest_iot.py --skip-download --skip-exports
```
