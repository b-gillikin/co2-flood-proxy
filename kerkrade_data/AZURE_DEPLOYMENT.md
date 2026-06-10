# Azure Deployment Plan: Timer-Triggered Function

## Architecture

- Azure Function App (Python, Consumption)
  - Timer trigger schedule (UTC): `0 0 * * * *` (hourly, on the hour)
  - Runs `monthly_pull.py`
  - Event Grid trigger sends email when a new blob is created in `kerkrada-weather-data`
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
- `blob_created_email_alert/__init__.py`: Event Grid blob-created trigger that emails alerts
- `requirements.txt`: `azure-functions`, `azure-storage-blob`, `azure-communication-email`
- `host.json`: function host config
- `local.settings.example.json`: local environment sample
- `azure/deploy_function.sh`: end-to-end provisioning and deployment script

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

## Monthly Cost Estimate (US East)

Given your workload (about 24 runs/day, runtime under 1 second):

- Azure Functions Consumption compute: effectively near $0/month at this scale (typically within free grants).
- Storage (small blob footprint + light transactions): usually around `$0.05/month` to `$0.30/month`.

Expected total: **~$0.05 to $0.30 per month**.

Email alert increment:
- Event Grid + alert email traffic at this volume is typically near-zero to low cents/month.

## Schedule and Time Zone

- Current schedule is UTC:
  - `00:00, 09:00, 12:00, 15:00, 18:00, 21:00`
- If you want Eastern local clock times year-round, we should adjust cron for DST behavior.

## Notes

- Keep API keys in app settings, not source code.
- `monthly_pull.py` already supports `API_KEYS` and `SAVE_FOLDER` env vars.
- Blob alert subscription: `es-kerkrada-weather-data-blobcreated-email`.
- For debugging logs:
  - `az functionapp log tail --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP"`
