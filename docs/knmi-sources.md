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

For unattended catch-up while the laptop is awake, use the bounded hourly job.
Store the API key outside the repo:

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

The loader accepts cached CSV, JSON, JSONL, or KNMI NetCDF files in:

```text
data/raw/knmi/
```

Expected normalized output:

```text
data/interim/knmi_hourly.csv
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
