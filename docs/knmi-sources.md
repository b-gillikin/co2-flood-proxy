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

## Local Landing Zone

The loader accepts cached CSV, JSON, or JSONL files in:

```text
data/raw/knmi/
```

Expected normalized output:

```text
data/interim/knmi_hourly.csv
results/knmi/knmi_visualcrossing_comparison.csv
results/knmi/knmi_vs_visualcrossing_pressure_temp.png
```

The lightweight loader recognizes common KNMI-style columns such as `YYYYMMDD`,
`HH`, `STN`, `T`, `U`, `P`, and `RH`, and converts timestamps to hourly UTC.
If KNMI delivers NetCDF files, export the selected station-hour rows to CSV
first or add a dedicated NetCDF parser later.

## Station Priority

Use Maastricht-Beek as the first reference station if available for the selected
dataset. If not, use the nearest practical station with pressure and temperature
coverage and record that choice in `docs/decisions.md`.
