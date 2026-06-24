"""IoT loaders for Kerkrade Blynk/Azure sensor exports."""

from __future__ import annotations

import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd


IOT_COLUMN_MAP = {
    "Temperature": "iot_temperature_c",
    "Humidity": "iot_relative_humidity_pct",
    "Air Pressure": "iot_air_pressure_hpa",
    "PM1": "iot_pm1_ugm3",
    "PM2_5": "iot_pm2_5_ugm3",
    "PM10": "iot_pm10_ugm3",
    "CO2": "iot_co2_ppm",
    "COS Range": "iot_co2_range_ppm",
    "CO2 Range": "iot_co2_range_ppm",
    "CO2 ABC Status": "iot_co2_abc_status",
    "ABC Ticks": "iot_abc_ticks",
    "ABC Counter": "iot_abc_counter",
    "BME Status": "iot_bme_status",
    "CO2 Status": "iot_co2_status",
    "ZH03B Status": "iot_zh03b_status",
    "ABC Status": "iot_abc_status",
}

IOT_METADATA_COLUMNS = {
    "timestamp",
    "iot_source",
    "iot_device_name",
    "iot_device_id",
    "iot_source_file",
    "iot_source_row_count",
}


def load_iot(
    raw_dir="data/raw/iot",
    blynk_export_dir=None,
    frequency="h",
    start=None,
    end=None,
    include_status=True,
):
    """Load Kerkrade IoT observations from Azure blobs and Blynk exports.

    Azure rows are UTC. Blynk exports are local Europe/Amsterdam timestamps and
    are converted to UTC before merging. Hourly aggregation keeps observation,
    device, and source counts so coverage gaps remain visible in QC.
    """
    out = load_iot_observations(
        raw_dir=raw_dir,
        blynk_export_dir=blynk_export_dir,
        include_status=include_status,
    )

    out = out.set_index("timestamp").sort_index()

    if start is not None:
        out = out.loc[out.index >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        out = out.loc[out.index <= pd.Timestamp(end, tz="UTC")]

    sensor_columns = [
        column
        for column in out.columns
        if column not in IOT_METADATA_COLUMNS
    ]

    if frequency:
        observation_count = out["iot_co2_ppm"].resample(frequency).count()
        device_count = out["iot_device_id"].resample(frequency).nunique()
        source_count = out["iot_source"].resample(frequency).nunique()
        out = out.resample(frequency)[sensor_columns].mean()
        out["iot_observation_count"] = observation_count.rename("iot_observation_count")
        out["iot_device_count"] = device_count.rename("iot_device_count")
        out["iot_source_count"] = source_count.rename("iot_source_count")
    else:
        out["iot_observation_count"] = out["iot_co2_ppm"].notna().astype(int)
        out["iot_device_count"] = out["iot_device_id"].notna().astype(int)
        out["iot_source_count"] = out["iot_source"].notna().astype(int)

    return out


def load_iot_observations(
    raw_dir="data/raw/iot",
    blynk_export_dir=None,
    include_status=True,
):
    """Load unaggregated IoT rows with source/device metadata."""
    frames = []
    frames.extend(_load_azure_iot_rows(Path(raw_dir)))

    if blynk_export_dir is not None:
        export_path = Path(blynk_export_dir)
        if export_path.exists():
            frames.extend(_load_blynk_export_rows(export_path))

    if not frames:
        raise FileNotFoundError(
            f"No Kerkrade IoT CSV files found in {raw_dir} or {blynk_export_dir}"
        )

    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["timestamp"])

    if not include_status:
        status_columns = [column for column in out.columns if "status" in column]
        out = out.drop(columns=status_columns)

    sensor_columns = [
        column
        for column in out.columns
        if column not in IOT_METADATA_COLUMNS
    ]
    out[sensor_columns] = out[sensor_columns].apply(pd.to_numeric, errors="coerce")
    out["iot_device_id"] = out["iot_device_id"].fillna("unknown").astype(str)
    out["iot_device_name"] = out["iot_device_name"].fillna("unknown").astype(str)
    out["iot_source_row_count"] = pd.to_numeric(
        out["iot_source_row_count"],
        errors="coerce",
    ).fillna(0)

    out = out.sort_values(
        ["iot_device_id", "timestamp", "iot_source_row_count", "iot_source_file"]
    )
    out = out.drop_duplicates(subset=["iot_device_id", "timestamp"], keep="last")
    return out.sort_values("timestamp").reset_index(drop=True)


def _load_azure_iot_rows(raw_path):
    """Load Azure daily IoT CSV rows before hourly aggregation."""
    csv_paths = sorted(raw_path.glob("air_quality_*.csv"))
    frames = []
    for path in csv_paths:
        frame = pd.read_csv(path)
        frame["timestamp"] = pd.to_datetime(frame["updated"], utc=True)
        frame = frame.drop(columns=["updated"]).rename(columns=IOT_COLUMN_MAP)
        frame["iot_source"] = "azure_blob"
        frame["iot_device_name"] = "kerkrade_air_quality_device_1"
        frame["iot_device_id"] = "air-quality-device-data-1"
        frame["iot_source_file"] = str(path)
        frame["iot_source_row_count"] = len(frame)
        frames.append(frame)
    return frames


def _load_blynk_export_rows(export_path):
    """Load Blynk device export rows with local timestamps converted to UTC."""
    frames = []
    for path in sorted(export_path.glob("*/*_data.csv")):
        metadata = _read_blynk_metadata(path.parent / "metadata.json")
        frame = pd.read_csv(path)
        timestamps = pd.to_datetime(
            frame["Time"],
            format="%m/%d/%y %I:%M:%S %p",
            errors="coerce",
        )
        local_tz = ZoneInfo(metadata.get("timezone", "Europe/Amsterdam"))
        frame["timestamp"] = timestamps.dt.tz_localize(
            local_tz,
            nonexistent="shift_forward",
            ambiguous="NaT",
        ).dt.tz_convert("UTC")
        frame = frame.drop(columns=["Time"]).rename(columns=IOT_COLUMN_MAP)
        frame["iot_source"] = "blynk_export"
        frame["iot_device_name"] = metadata["device_name"]
        frame["iot_device_id"] = metadata["device_id"]
        frame["iot_source_file"] = str(path)
        frame["iot_source_row_count"] = len(frame)
        frames.append(frame)
    return frames


def _read_blynk_metadata(path):
    """Read device metadata next to a Blynk export CSV."""
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = {}
    device = payload.get("device", {})
    return {
        "timezone": payload.get("timezone", "Europe/Amsterdam"),
        "device_name": device.get("name", "unknown"),
        "device_id": _device_id_from_export_path(path.parent),
    }


def _device_id_from_export_path(path):
    """Extract the Blynk numeric device ID from an export folder name."""
    for part in str(path).replace("-", "_").split("_"):
        if part.isdigit() and len(part) >= 5:
            return part
    return "unknown"
