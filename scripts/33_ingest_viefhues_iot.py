"""Normalize the source-native Viefhues K4 record to hourly UTC data.

The delivered thesis package also contains a longer cleaned analysis table.
That table is not used here because its pre-May source files and intermediate
ABC-adjusted file were not delivered.  K4 is the non-ABC sensor and covers the
complete July 2021 anchor at minute resolution.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "Jan Philip Viefhues Thesis Presentation Data and Code"
DEFAULT_SOURCE = (
    PACKAGE / "masterthesis-main" / "raw_data" / "2021-05-15_2021-09-29_K4_basement.csv"
)
DEFAULT_OUTPUT = ROOT / "data" / "interim" / "viefhues_iot.csv"
DEFAULT_QC = ROOT / "data" / "processed" / "viefhues_iot_qc.csv"

FIELDS = {
    "field1": "iot_co2_ppm",
    "field6": "iot_air_pressure_hpa",
}


def read_k4(source: Path) -> pd.DataFrame:
    """Read K4 and convert its labelled Dutch civil time to UTC."""
    raw = pd.read_csv(source)
    required = {"created_at", *FIELDS}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Missing K4 columns: {sorted(missing)}")

    suffix = raw["created_at"].str.extract(r" (CEST|CET)$", expand=False)
    if suffix.isna().any():
        raise ValueError("Every K4 timestamp must end in CEST or CET")

    local_clock = pd.to_datetime(
        raw["created_at"].str.replace(r" (CEST|CET)$", "", regex=True),
        errors="raise",
    )
    local_time = local_clock.dt.tz_localize(
        "Europe/Amsterdam", ambiguous="raise", nonexistent="raise"
    )
    if not suffix.eq(local_time.dt.strftime("%Z")).all():
        raise ValueError("Timestamp suffix disagrees with Europe/Amsterdam time")

    values = raw[list(FIELDS)].apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any():
        raise ValueError("K4 CO2 or pressure contains missing/non-numeric values")

    return pd.DataFrame(
        {
            "timestamp_utc": local_time.dt.tz_convert("UTC"),
            **{new: values[old] for old, new in FIELDS.items()},
        }
    )


def hourly_mean(raw: pd.DataFrame) -> pd.DataFrame:
    """Average minute observations within UTC hours; never fill absent hours."""
    if raw["timestamp_utc"].duplicated().any():
        raise ValueError("K4 has duplicate source timestamps")

    hourly = (
        raw.assign(timestamp_utc=raw["timestamp_utc"].dt.floor("h"))
        .groupby("timestamp_utc", as_index=False)
        .agg(
            iot_co2_ppm=("iot_co2_ppm", "mean"),
            iot_air_pressure_hpa=("iot_air_pressure_hpa", "mean"),
            source_rows=("iot_co2_ppm", "size"),
        )
    )
    hourly.insert(1, "sensor_era", "viefhues_k4_no_abc_2021")
    return hourly


def qc_table(source: Path, raw: pd.DataFrame, hourly: pd.DataFrame) -> pd.DataFrame:
    """Return compact provenance and coverage checks for the normalized record."""
    full_hours = pd.date_range(
        hourly["timestamp_utc"].min(), hourly["timestamp_utc"].max(), freq="h"
    )
    july = hourly["timestamp_utc"].between(
        "2021-07-01 00:00:00+02:00",
        "2021-07-31 23:59:59+02:00",
    )
    metrics = [
        ("source_sha256", hashlib.sha256(source.read_bytes()).hexdigest(), "record"),
        ("source_rows", len(raw), "record"),
        ("source_start_utc", raw["timestamp_utc"].min().isoformat(), "record"),
        ("source_end_utc", raw["timestamp_utc"].max().isoformat(), "record"),
        ("hourly_rows", len(hourly), "record"),
        ("missing_hours_within_span", len(full_hours) - len(hourly), "record"),
        ("hours_with_fewer_than_50_rows", int(hourly["source_rows"].lt(50).sum()), "record"),
        ("july_2021_hours", int(july.sum()), "pass if 744"),
        ("source_co2_at_400", int(raw["iot_co2_ppm"].eq(400).sum()), "record"),
        ("source_co2_at_5000", int(raw["iot_co2_ppm"].eq(5000).sum()), "record"),
    ]
    return pd.DataFrame(metrics, columns=["metric", "value", "reading"])


def main() -> None:
    raw = read_k4(DEFAULT_SOURCE)
    hourly = hourly_mean(raw)
    qc = qc_table(DEFAULT_SOURCE, raw, hourly)

    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_QC.parent.mkdir(parents=True, exist_ok=True)
    hourly.to_csv(DEFAULT_OUTPUT, index=False)
    qc.to_csv(DEFAULT_QC, index=False)
    print(f"Wrote {len(hourly):,} hours to {DEFAULT_OUTPUT}")
    print(qc.to_string(index=False))


if __name__ == "__main__":
    main()
