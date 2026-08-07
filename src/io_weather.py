"""Visual Crossing weather loaders."""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

WEATHER_COLUMN_MAP = {
    "temp": "weather_temp_c",
    "dew": "weather_dewpoint_c",
    "humidity": "weather_relative_humidity_pct",
    "precip": "weather_precip_mm",
    "precipprob": "weather_precip_probability_pct",
    "snow": "weather_snow_mm",
    "snowdepth": "weather_snow_depth_mm",
    "windgust": "weather_wind_gust_kph",
    "windspeed": "weather_wind_speed_kph",
    "winddir": "weather_wind_dir_deg",
    "sealevelpressure": "weather_pressure_hpa",
    "pressure": "weather_pressure_hpa",
    "cloudcover": "weather_cloud_cover_pct",
    "visibility": "weather_visibility_km",
    "solarradiation": "weather_solar_radiation_wm2",
    "solarenergy": "weather_solar_energy_mj_m2",
    "uvindex": "weather_uv_index",
    "cape": "weather_cape",
    "cin": "weather_cin",
    "pm1": "weather_pm1_ugm3",
    "pm2p5": "weather_pm2_5_ugm3",
    "pm10": "weather_pm10_ugm3",
    "no2": "weather_no2_ugm3",
    "o3": "weather_o3_ugm3",
    "co": "weather_co_ugm3",
    "aqieur": "weather_aqi_eu",
}


def safe_token(value):
    """Convert a free-form location name to a stable column prefix."""
    characters = [char.lower() if char.isalnum() else "_" for char in str(value)]
    return "_".join(part for part in "".join(characters).split("_") if part)


def load_weather(
    raw_dir="data/raw/weather",
    frequency="h",
    locations=None,
    wide=True,
    timezone="Europe/Amsterdam",
    start=None,
    end=None,
):
    """Load Visual Crossing weather CSVs pulled from Azure Blob Storage.

    Stored Visual Crossing CSVs use local civil timestamps without an offset.
    The configured timezone is applied before conversion to UTC. Use
    ``wide=False`` for one row per location-hour or ``wide=True`` for the joined
    analysis shape with location-prefixed columns.
    """
    raw_path = Path(raw_dir)
    csv_paths = sorted(raw_path.glob("*/*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No weather CSV files found in {raw_path}")

    selected_locations = (
        {location.lower() for location in locations} if locations is not None else None
    )
    local_tz = ZoneInfo(timezone)
    frames = []

    for path in csv_paths:
        frame = pd.read_csv(path)
        if frame.empty:
            continue

        location = str(frame["name"].dropna().iloc[0] if "name" in frame else path.parent.name)
        if selected_locations is not None and location.lower() not in selected_locations:
            continue

        timestamps = pd.to_datetime(frame["datetime"], errors="coerce")
        frame["timestamp"] = timestamps.dt.tz_localize(
            local_tz,
            nonexistent="shift_forward",
            ambiguous="NaT",
        ).dt.tz_convert("UTC")
        frame["weather_location"] = location

        keep_columns = [
            "timestamp",
            "weather_location",
            "conditions",
            "source",
            *[column for column in WEATHER_COLUMN_MAP if column in frame.columns],
        ]
        frame = frame[keep_columns].rename(columns=WEATHER_COLUMN_MAP)

        for column in WEATHER_COLUMN_MAP.values():
            if column in frame:
                frame[column] = pd.to_numeric(frame[column], errors="coerce")

        frames.append(frame)

    if not frames:
        raise FileNotFoundError(f"No weather CSV files matched locations={locations}")

    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["timestamp"]).sort_values(["weather_location", "timestamp"])
    out = out.drop_duplicates(subset=["weather_location", "timestamp"], keep="last")

    if start is not None:
        out = out.loc[out["timestamp"] >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        out = out.loc[out["timestamp"] <= pd.Timestamp(end, tz="UTC")]

    numeric_columns = [
        column
        for column in out.columns
        if column.startswith("weather_") and column != "weather_location"
    ]

    if frequency:
        out = (
            out.set_index("timestamp")
            .groupby("weather_location")
            .resample(frequency)[numeric_columns]
            .mean()
            .reset_index()
        )

    if not wide:
        return out.sort_values(["weather_location", "timestamp"])

    wide_frames = []
    for location, location_frame in out.groupby("weather_location"):
        prefix = safe_token(location)
        location_wide = location_frame.set_index("timestamp")[numeric_columns].add_prefix(
            f"{prefix}_"
        )
        wide_frames.append(location_wide)

    return pd.concat(wide_frames, axis=1).sort_index()
