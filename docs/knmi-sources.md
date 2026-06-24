# KNMI Reference Meteorology

Purpose: provide an official reference meteorological series for checking the
Kerkrade Visual Crossing weather lane, especially pressure and temperature.

## Source

- Portal: https://developer.dataplatform.knmi.nl/
- API documentation: https://developer.dataplatform.knmi.nl/open-data-api
- Current script default dataset: `10-minute-in-situ-meteorological-observations`
- Script: `python scripts/04_ingest_knmi.py`

## API Key

KNMI live downloads require an Open Data API key.

1. Register or log in at the KNMI Developer Portal.
2. Open the API Catalogue.
3. Request an Open Data API key.
4. Store it only in your shell, not in the repo:

```bash
export KNMI_API_KEY="your-key"
python scripts/04_ingest_knmi.py
```

For the current Kerkrade IoT analysis window, pull matching 10-minute NetCDF
files directly by filename:

```bash
python scripts/04_ingest_knmi.py \
  --start 2026-03-16T00:00:00Z \
  --end 2026-04-14T00:00:00Z \
  --max-files 5000
```

This requests 4,177 expected 10-minute files. The script defaults to a 3.7
second pause between KNMI API URL requests for date-window downloads, keeping
the registered-key usage under the 1,000 requests/hour quota.

## Azure Backfill Collector

The preferred long-running KNMI collector is now an Azure Timer Function. The
local launchd route is fragile on macOS because Desktop/privacy permissions can
block unattended scripts even when the same script works in an interactive
terminal.

The Azure function downloads bounded batches of raw 10-minute NetCDF files,
extracts the selected station rows, keeps a broad set of KNMI variables, and
then discards the raw all-station file. It stores a cursor blob so each run
resumes from the next missing timestamp. Raw NetCDF persistence is off by
default and should only be enabled temporarily with `KNMI_KEEP_RAW=true`.

Deploy from `kerkrade_data/` with Azure CLI credentials:

```bash
cd kerkrade_data
export SUBSCRIPTION_ID="<subscription-id>"
export RESOURCE_GROUP="<resource-group>"
export LOCATION="eastus"
export STORAGE_ACCOUNT="<globally-unique-storage-account>"
export FUNCTION_APP="<globally-unique-function-app>"
export KNMI_API_KEY="<knmi-open-data-api-key>"

bash azure/deploy_knmi_function.sh
```

Useful optional settings:

```bash
export KNMI_CONTAINER="knmi-data"
export KNMI_START="2020-01-01T00:00:00Z"
export KNMI_BACKFILL_DIRECTION="backward"
export KNMI_STATIONS="06380,06377,06392,06370,06375,06350,06356"
export KNMI_MAX_DOWNLOADS_PER_RUN="200"
export KNMI_KEEP_RAW="false"
export KNMI_BACKFILL_SCHEDULE="0 */15 * * * *"
```

Blob layout:

```text
knmi-data/slim/10-minute-in-situ/year=2020/month=01/knmi_meuse_10min_2020_01.csv.gz
knmi-data/state/knmi_backfill_state.json
```

Monitor with:

```bash
az functionapp log tail --resource-group "$RESOURCE_GROUP" --name "$FUNCTION_APP"
az storage blob show \
  --account-name "$STORAGE_ACCOUNT" \
  --container-name "${KNMI_CONTAINER:-knmi-data}" \
  --name state/knmi_backfill_state.json \
  --auth-mode login
```

At the current 200 files every 15 minutes, the collector attempts up to 19,200
10-minute files per day. A full 2020-to-current backfill should take roughly
18 days if the timer runs steadily and the KNMI API remains cooperative.

Storage policy: keep station-slim monthly gzip CSVs for the selected
Meuse/Maas stations and broad KNMI variables. Do not keep the full all-station
raw NetCDF archive in Azure unless debugging requires a short temporary raw
sample.

Backfill policy: run backward from the current UTC 10-minute file toward
`KNMI_START` so recent KNMI coverage becomes available for chapter modelling
before the older historical archive finishes.

## Azure-to-Local Sync

The Azure collector stores the compact station-slim monthly blobs; analysis
still runs from this repository's local `data/` tree. Sync the collected blobs
and rebuild the local hourly KNMI table with:

```bash
python scripts/04_sync_knmi_azure.py
```

This downloads Azure blobs under:

```text
data/raw/knmi/azure_slim/slim/10-minute-in-situ/
data/raw/knmi/azure_slim/_state/
```

Then it calls `scripts/04_ingest_knmi.py --skip-download` to write:

```text
data/interim/knmi_hourly.csv
data/interim/knmi_hourly.parquet
```

The Parquet file is the preferred local analysis table because it is typed and
compressed. The CSV mirror remains useful for quick inspection and compatibility
with existing scripts.

## Local Fallback

For a short unattended catch-up while the laptop is awake, the bounded launchd
job is still available. Store the API key outside the repo:

```bash
printf '%s' "$KNMI_API_KEY" > ~/.knmi_api_key
chmod 600 ~/.knmi_api_key
```

Install the launchd job:

```bash
mkdir -p ~/Library/LaunchAgents
cp ops/com.briangillikin.chapter1-co2.knmi.plist ~/Library/LaunchAgents/
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.briangillikin.chapter1-co2.knmi.plist
launchctl kickstart -k "gui/$(id -u)/com.briangillikin.chapter1-co2.knmi"
```

The wrapper runs:

```bash
scripts/run_knmi_hourly_job.sh
```

By default each hourly run backfills from `2020-01-01T00:00:00Z` through the
current UTC time, requests at most 800 missing files, sleeps 4 seconds between
KNMI URL requests, then rebuilds `data/interim/knmi_hourly.csv` for the curated
Dutch Meuse/Maas station set. Logs are written under `logs/`, which is ignored
by git. The script uses a lock directory so overlapping hourly runs exit
quietly.

Override the defaults for a shorter or slower run if needed:

```bash
KNMI_START=2025-01-01T00:00:00Z \
KNMI_MAX_DOWNLOADS=200 \
KNMI_DOWNLOAD_SLEEP_SECONDS=4.0 \
KNMI_STATION_SET=meuse \
scripts/run_knmi_hourly_job.sh
```

Stop the job with:

```bash
launchctl bootout "gui/$(id -u)" ~/Library/LaunchAgents/com.briangillikin.chapter1-co2.knmi.plist
```

## Local Landing Zone

The loader accepts cached CSV, CSV.GZ, Parquet, JSON, JSONL, or KNMI NetCDF
files in:

```text
data/raw/knmi/
```

Expected normalized output:

```text
data/interim/knmi_hourly.csv
data/interim/knmi_hourly.parquet
results/knmi/knmi_station_set.csv
results/knmi/knmi_visualcrossing_comparison.csv
results/knmi/knmi_vs_visualcrossing_pressure_temp.png
```

The loader recognizes common KNMI-style CSV columns such as `YYYYMMDD`, `HH`,
`STN`, `T`, `U`, `P`, and `RH`, and NetCDF variables such as `pp`, `ta`, `rh`,
and `R1H`. Timestamps are converted to hourly UTC.

## Station Policy

Keep the curated Dutch Meuse/Maas station set in the normalized hourly file so
future basin/catchment analyses can use more than a single local reference
station without retaining the full KNMI station corpus.

Current `meuse` station set:

| Station | Name | Role |
| --- | --- | --- |
| `06380` | Maastricht Airport | Primary Kerkrade/South Limburg reference and transfer meteorology station. |
| `06377` | Ell | Limburg/Maas corridor sensitivity station. |
| `06392` | Horst | North Limburg/Maas corridor station. |
| `06370` | Eindhoven Airport | North Brabant catchment/corridor station. |
| `06375` | Volkel Airport | North Brabant/Maas corridor station. |
| `06350` | Gilze-Rijen Airport | Western North Brabant context station. |
| `06356` | Herwijnen | Lower Maas/Rhine-Meuse delta context station. |

`scripts/04_ingest_knmi.py` defaults to `--station-set meuse`. Use
`--station-set maastricht` for the old single-station behavior, or
`--station-set none --station 06380,06377` for a custom station list.

The Visual Crossing comparison plot still uses `06380` by default because it is
the closest KNMI reference station for Kerkrade.
