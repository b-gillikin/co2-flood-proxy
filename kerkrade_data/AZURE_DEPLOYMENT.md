# Azure Deployment Plan: Timer-Triggered Function

## Architecture

- Azure Function App (Python, Consumption)
  - Minute-level IoT collection, hourly weather refresh, and hourly historical
    weather backfill retain their independent timer schedules.
  - One summary email is sent daily at 21:05 UTC.
  - Blob creation does not send email or invoke an email handler.
- Azure Storage Account (Standard_LRS)
  - Runtime storage (`AzureWebJobsStorage`)
  - Blob container for persistent `monthly_data` + `.backfill_state.json`
- Azure Communication Services + Email (Azure-managed domain)
  - Sends alert emails from `alerts@ec0e0e9e-5427-451d-959d-23ed199a313b.azurecomm.net`

## Why This Setup

- Lowest-cost option for your very short runs.
- No ACR required.
- Persistent state survives restarts/deployments.
- Local macOS `launchd` scheduling is removed; Azure Timer is the only scheduler.

## Files Added/Used

- `monthly_pull_timer/__init__.py`: timer trigger + blob sync wrapper around `monthly_pull.main()`
- `daily_summary_email_timer/__init__.py`: one consolidated weather/IoT email at 21:05 UTC
- `daily_summary.py`: pure Azure Communication Services message construction
- `knmi_backfill_timer/__init__.py`: timer trigger for resumable KNMI raw-file backfill
- `knmi_backfill.py`: cursor-based KNMI downloader used by the timer trigger
- `requirements.txt`: `azure-functions`, `azure-storage-blob`, `azure-communication-email`
- `host.json`: function host config
- `local.settings.example.json`: local environment sample
- `azure/deploy_function.sh`: end-to-end provisioning and deployment script
- `azure/deploy_knmi_function.sh`: KNMI-only provisioning/deployment script

## One-Time Deploy (US East)

```bash
export SUBSCRIPTION_ID="<subscription-id>"
export RESOURCE_GROUP="rg-kerkrade-prod"
export LOCATION="eastus"
export STORAGE_ACCOUNT="stkerkradeprod01"
export FUNCTION_APP="func-kerkrade-monthly-pull"
export API_KEYS="key1,key2,key3"
# Optional:
export MONTHLY_DATA_CONTAINER="kerkrada-weather-data"

./azure/deploy_function.sh
```

What this script does:
1. Creates resource group + storage account.
2. Creates blob container and uploads current `monthly_data/`.
3. Creates Function App (Consumption, Python).
4. Sets app settings (API keys, storage connection string).
5. Zip-deploys function code.

The deployment zip explicitly excludes local `.python_packages` and the
separate `knmi_backfill_timer` function. Azure remote build is enabled so Linux
dependencies are built on the Function host rather than copied from the
deploying workstation. The packaging step fails before deployment if either
unsafe path enters the zip.

## Monthly Cost Estimate (US East)

Given your workload (about 24 runs/day, runtime under 1 second):

- Azure Functions Consumption compute: effectively near $0/month at this scale (typically within free grants).
- Storage (small blob footprint + light transactions): usually around `$0.05/month` to `$0.30/month`.

Expected total: **~$0.05 to $0.30 per month**.

Email increment:
- One Azure Communication Services email per day is typically only a few cents
  per month. The deployment removes the historical per-blob Event Grid
  subscription, eliminating its notification traffic.

## Schedule and Time Zone

- Daily summary email: `21:05 UTC` (`0 5 21 * * *`).
- This corresponds to 17:05 EDT or 16:05 EST; the UTC schedule itself does not
  move with daylight saving time.

## Notes

- Keep API keys in app settings, not source code.
- `monthly_pull.py` already supports `API_KEYS` and `SAVE_FOLDER` env vars.
- Per-blob alert subscriptions are obsolete. Deployment removes both historical
  subscription names if either still exists.
- For debugging logs:
  - `az functionapp log tail --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP"`

## KNMI Backfill Deploy

Use a dedicated Function App for KNMI so the historical backfill can run without
starting the older weather timers in a fresh app.

```bash
cd kerkrade_data
export SUBSCRIPTION_ID="<subscription-id>"
export RESOURCE_GROUP="rg-kerkrade-prod"
export LOCATION="eastus"
export STORAGE_ACCOUNT="stknmikerkradeprod01"
export FUNCTION_APP="func-kerkrade-knmi-backfill-bg"
export KNMI_API_KEY="<knmi-open-data-api-key>"

# Production forward-maintenance defaults shown explicitly:
export KNMI_CONTAINER="knmi-data"
export KNMI_START="2026-06-24T12:00:00Z"
export KNMI_BACKFILL_DIRECTION="forward"
export KNMI_STATE_BLOB="state/knmi_forward_state.json"
export KNMI_AVAILABILITY_LAG_MINUTES="180"
export KNMI_STATIONS="06380,06377,06392,06370,06375,06350,06356"
export KNMI_MAX_DOWNLOADS_PER_RUN="200"
export KNMI_KEEP_RAW="false"
export KNMI_BACKFILL_SCHEDULE="0 */15 * * * *"

bash azure/deploy_knmi_function.sh
```

The KNMI function downloads raw all-station NetCDF files as temporary input,
keeps broad variables for the selected stations, writes monthly station-slim
gzip CSV files under `knmi-data/slim/10-minute-in-situ/`, and maintains a
direction-specific cursor. Full raw NetCDF persistence is off by default.

The repository defaults now describe the production forward-maintenance job:
continue from the 2026-06-24 archive handoff, use
`state/knmi_forward_state.json`, and remain three hours behind current UTC for
KNMI publication latency. This prevents a routine deployment from switching the
live collector back to the completed historical mode. Monthly slim blobs are
idempotent because rows are deduplicated by UTC timestamp and station.

The historical 2020-to-handoff archive is complete. Only redeploy that mode
deliberately, with all historical settings explicit and without reusing the
forward cursor:

```bash
export KNMI_BACKFILL_DIRECTION="backward"
export KNMI_START="2020-01-01T00:00:00Z"
export KNMI_STATE_BLOB="state/knmi_backfill_state.json"
bash azure/deploy_knmi_function.sh
```

Useful checks:

```bash
az functionapp log tail --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP"
az storage blob list \
  --account-name "$STORAGE_ACCOUNT" \
  --container-name "${KNMI_CONTAINER:-knmi-data}" \
  --prefix slim/10-minute-in-situ/ \
  --query "length(@)" \
  -o tsv
```
