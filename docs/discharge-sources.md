# Discharge Sources

Task 1.3 uses three public discharge gauges:

| Source | Gauge | Variable | Raw file | Notes |
| --- | --- | --- | --- | --- |
| WVER | Wurm, Rimburg NL | Abfluss, m3/s | `data/raw/discharge/wver_wurm_rimburg_discharge.json` | WVER chart JSON, Windows-1252 encoded. Current payload starts 2025-04-23. |
| Waterstand Limburg | Geul, Hommerich (`10.Q.30`, ID `233`) | Afvoer, m3/s | `data/raw/discharge/waterstandlimburg_geul_hommerich_discharge.json` | Public OData-style measurements endpoint. |
| Waterstand Limburg | Geul, Meerssen (`10.Q.36`, ID `1394`) | Afvoer, m3/s | `data/raw/discharge/waterstandlimburg_geul_meerssen_discharge.json` | Public OData-style measurements endpoint. |

The normalized hourly file is `data/interim/discharge_hourly.csv`, produced by:

```bash
python scripts/01_ingest_discharge.py
```

For routine updates, use the top-level data refresh command:

```bash
python scripts/update_data.py
```

Update behavior:

- WVER Rimburg is refreshed by replacing the compact public JSON payload.
- Waterstand Limburg Geul gauges are incrementally appended from the latest local timestamp.
- `data/interim/discharge_hourly.csv` is rebuilt after every update.

Raw and interim data are intentionally gitignored. Record major source decisions in `docs/decisions.md`.
