# ERA5-Land Azure backfill

This is collection infrastructure, not chapter analysis. A dedicated timer
Function submits one CDS month, stores its request ID in Blob Storage, polls on
later invocations and uploads only a validated NetCDF file. The design keeps
every Consumption-plan invocation below the ten-minute limit.

Azure resources:

- resource group: `rg-kerkrade-prod`;
- Function App: `func-kerkrade-era5-backfill-bg`;
- storage account: `stkerkradeprod01bg`;
- container: `era5-land`;
- source blobs: `source/era5_land_limburg_YYYY_MM.nc`;
- state: `_state.json`;
- checksum manifest: `manifest.csv`.

The app was deployed on 2026-08-11 and completed all 300 months through
December 2025 on 2026-08-14. A final audit downloaded and reopened every
NetCDF, recomputed every byte count and SHA-256, and reproduced `manifest.csv`
byte for byte. The archive contains 300 unique months and hashes with no
missing or extra period. `ERA5_ENABLED=false` and
`AzureWebJobs.era5_backfill_timer.Disabled=true`; the timer no longer runs.

Deployment requires Azure CLI, `curl`, `jq`, `zip` and the chapter Python
environment. It always leaves the timer paused and, by default, seeds locally
completed monthly files first:

```bash
PYTHON_BIN=/path/to/chapter1-co2/bin/python ./infrastructure/era5_backfill/deploy.sh
```

For a code-only redeployment after the source files are already seeded, set
`SEED_LOCAL_FILES=false`. Deployment temporarily opens SCM basic publishing,
waits for the remote build, closes SCM again and explicitly synchronizes the
timer trigger.

Enable only after the local pull is stopped and its final completed month has
been seeded:

```bash
az functionapp config appsettings set \
  --subscription c7729fd0-7b35-4ec4-b1a3-ec7079b776fa \
  --resource-group rg-kerkrade-prod \
  --name func-kerkrade-era5-backfill-bg \
  --settings \
    ERA5_ENABLED=true \
    AzureWebJobs.era5_backfill_timer.Disabled=false \
  -o none
```

Disable after completion with both the safety flag and trigger setting:

```bash
az functionapp config appsettings set \
  --subscription c7729fd0-7b35-4ec4-b1a3-ec7079b776fa \
  --resource-group rg-kerkrade-prod \
  --name func-kerkrade-era5-backfill-bg \
  --settings \
    ERA5_ENABLED=false \
    AzureWebJobs.era5_backfill_timer.Disabled=true \
  -o none
```

The timer allows one outstanding CDS request. Three failed submissions for one
month set a visible `blocked` state rather than silently skipping it. Restart by
fixing the cause and removing `blocked`/resetting that month's attempt count in
`_state.json`.
