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
`--auth-mode key`; it does not store Azure connection strings or Blynk tokens
in the repository.

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

Interpretation caveat: the merged later-era hourly IoT frame is a possible
input to the conditional Kerkrade recurrence case, but it is not one
uninterrupted single-device record and does not contain July 2021. Source,
device and coverage-gap reports must travel with any interpretation.

## Delivered Viefhues package

A separate 63 MB thesis package is now held locally at
`Jan Philip Viefhues Thesis Presentation Data and Code/`. It includes the
thesis, presentation, historical analysis code, a cleaned analysis table and
three source-native May-September 2021 Kerkrade exports. The folder is ignored
by Git as external raw material.

The usable source-native record is K4, identified by the supplied R code as the
non-ABC basement sensor. Its extended file contains 169,594 minute rows from
2021-05-15 12:43 CEST through 2021-09-24 07:28 CEST. It supplies all 744 July
2021 civil-time hours. `scripts/33_ingest_viefhues_iot.py` verifies the labelled
Europe/Amsterdam timezone, converts to UTC and writes 2,829 observed hourly
means to `data/interim/viefhues_iot.csv`; absent hours remain absent. The QC
table records 335 absent hours across the full May-September span, 83 source
CO2 readings at 400 ppm and 5,761 readings at the 5,000-ppm ceiling. These
values are documented, not automatically discarded.

The delivered `cleaned_data/2021_flood_data.csv` is **processed thesis output**,
not a substitute for raw input. It spans 2020-08-25 to 2021-09-24 but has 1,333
missing civil-time hours, a duplicated 2020-10-25 02:00 hour and only 550 of
744 July hours because later joins retained complete rows. Its post-15-May CO2
and pressure are almost entirely the K4 hourly means. Before that date, the R
workflow reads `kerkrade3tillJune1.csv`, `kerkrade4tillJune1.csv`,
`metadata.json` and `total_Dataset_with_adjusted_ABC.csv`; none is in the
delivered directory or ZIP. The longer cleaned lineage therefore cannot be
reproduced from this package.

Other unresolved provenance is material. The thesis says both sensors were in
the basement, while the raw K3 filename says `livingroom`. The code labels K3
as ABC-on and K4 as ABC-off, repairs selected K3 values with the K4 pattern and
adds 450 ppm to the combined older record. The thesis describes the same
baseline correction as approximate. Neither thesis nor package gives a sensor
model, serial/device identifier, calibration date/certificate or complete
row-level ABC audit trail.

Consequently, the July K4 trajectory is now reproducible as an observed source
record, but the conditional recurrence case is not yet admissible: sensor-era
metadata, a hydrological pair with onset evidence and later complete events are
still missing. See `data-requests.md` and `student-next-actions.md`.

## Local outputs

- Raw daily CSVs: `data/raw/iot/air_quality_YYYY-MM-DD.csv`
- Hourly aligned output: `data/interim/iot_hourly.csv`
- Source summary: `data/processed/iot_source_summary.csv`
- Hourly CO2 coverage gaps: `data/processed/iot_coverage_gaps.csv`
- Historical K4 hourly output: `data/interim/viefhues_iot.csv`
- Historical K4 QC: `data/processed/viefhues_iot_qc.csv`

Refresh the later IoT stream with:

```bash
python scripts/01_ingest_iot.py
```

Rebuild from cached files, or ignore local Blynk exports, with:

```bash
python scripts/01_ingest_iot.py --skip-download
python scripts/01_ingest_iot.py --skip-download --skip-exports
```

Normalize only the delivered Viefhues K4 source record with:

```bash
python scripts/33_ingest_viefhues_iot.py
```
