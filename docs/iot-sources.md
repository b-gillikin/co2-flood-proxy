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

Interpretation caveat: the merged later-era hourly IoT frame is the input for
the retained Eryilmaz context check, but it is not one uninterrupted
single-device record and does not contain July 2021. Source, device and
coverage-gap reports should travel with any interpretation.

## Delivered Viefhues package

A separate 63 MB thesis package is now held locally at
`Jan Philip Viefhues Thesis Presentation Data and Code/`. It includes the
thesis, presentation, historical analysis code, a cleaned hourly flood table
spanning 2020-08-25 to 2021-09-24 and raw Kerkrade CSVs including a basement
record dated 2021-05-15 to 2021-09-24. The code identifies K4 as the non-ABC
basement sensor and contains the historical ABC-adjustment procedure, but the
cleaned pre-May record's provenance still needs reconstruction. The folder is
ignored by Git as external raw material.

This delivery has not yet been normalised into `viefhues_iot.csv` or audited for
timezone, device identity, calibration, ABC processing, duplicates,
aggregation and missingness. It therefore changes the request state, not the
case-gate result. The event study still requires `kerkrade_iot_eras.csv`; see
`data-requests.md`.

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
