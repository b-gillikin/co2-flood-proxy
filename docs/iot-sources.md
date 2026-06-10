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

## Local outputs

- Raw daily CSVs: `data/raw/iot/air_quality_YYYY-MM-DD.csv`
- Hourly aligned output: `data/interim/iot_hourly.csv`

Run all available refreshes with:

```bash
python scripts/update_data.py
```

Rebuild normalized files from already downloaded raw files with:

```bash
python scripts/update_data.py --skip-download
```
