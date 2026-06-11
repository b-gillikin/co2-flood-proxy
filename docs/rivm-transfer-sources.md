# RIVM/Luchtmeetnet Transfer-Site Data

Purpose: provide nearby public air-quality time series for transfer-site and
background-air-quality checks. These data are not CO2 substitutes; they help
separate broader air-quality/weather structure from the Kerkrade indoor CO2
residual.

## Sources

- API docs: https://api-docs.luchtmeetnet.nl/
- API base: https://api.luchtmeetnet.nl/open_api
- Data portal: https://data.rivm.nl/data/luchtmeetnet/

The public API does not require authentication, but it was returning `502 Bad
Gateway` during the 2026-06-11 run. The implemented fallback uses official
current-year CSV files from the RIVM data portal.

## Current Local Pull

Command:

```bash
python scripts/04_ingest_rivm.py --use-portal
```

Raw cached files:

```text
data/raw/transfer/rivm/portal_luchtmeetnet_meetlocaties.csv
data/raw/transfer/rivm/portal_2026_03_*.csv
data/raw/transfer/rivm/portal_2026_04_*.csv
```

Outputs:

```text
results/rivm/candidate_stations.csv
data/interim/rivm_hourly.csv
```

The current candidate search uses Maastricht, Roermond, and Heerlen as place
keywords. In the March-April 2026 component files, the usable nearby transfer
series are Heerlen stations `NL10136` and `NL10138`, with NO2, O3, and PM10
coverage in the normalized hourly output.

## Notes

- Maastricht candidate stations are present in metadata, but the sampled
  March-April 2026 PM files did not provide the same immediate usable coverage
  as Heerlen.
- Rerun the script after the RIVM API recovers; the API path caches JSON
  payloads, while `--use-portal` caches official CSV files.
- Keep these data as context/transfer features. Do not interpret them as direct
  indoor CO2 measurements.
