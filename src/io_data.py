"""Data loading and alignment entry points.

The June workflow expects one stable loader per source. Scripts should import
these functions and keep source-specific parsing details here.
"""

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
    "CO2 ABC Status": "iot_co2_abc_status",
    "ABC Ticks": "iot_abc_ticks",
    "ABC Counter": "iot_abc_counter",
    "BME Status": "iot_bme_status",
    "ZH03B Status": "iot_zh03b_status",
    "ABC Status": "iot_abc_status",
}

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

DISCHARGE_SOURCES = {
    "wurm_rimburg": {
        "filename": "wver_wurm_rimburg_discharge.json",
        "format": "wver",
        "encoding": "cp1252",
        "column": "discharge_wurm_rimburg_m3s",
    },
    "geul_hommerich": {
        "filename": "waterstandlimburg_geul_hommerich_discharge.json",
        "format": "waterstandlimburg",
        "encoding": "utf-8",
        "column": "discharge_geul_hommerich_m3s",
    },
    "geul_meerssen": {
        "filename": "waterstandlimburg_geul_meerssen_discharge.json",
        "format": "waterstandlimburg",
        "encoding": "utf-8",
        "column": "discharge_geul_meerssen_m3s",
    },
}


def load_iot(
    raw_dir="data/raw/iot",
    frequency="h",
    start=None,
    end=None,
    include_status=True,
):
    """Load the Kerkrade IoT stream from Azure daily CSV blobs.

    The Azure Function writes the ``updated`` field with
    ``datetime.now(timezone.utc)``, so naive CSV timestamps are interpreted as
    UTC here. Hourly resampling keeps an ``iot_observation_count`` column so
    empty hours stay visible during QC instead of being silently smoothed away.
    """
    raw_path = Path(raw_dir)
    csv_paths = sorted(raw_path.glob("air_quality_*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No Kerkrade IoT CSV files found in {raw_path}")

    frames = []
    for path in csv_paths:
        frame = pd.read_csv(path)
        frame["timestamp"] = pd.to_datetime(frame["updated"], utc=True)
        frame = frame.drop(columns=["updated"]).rename(columns=IOT_COLUMN_MAP)

        numeric_columns = [column for column in frame.columns if column != "timestamp"]
        frame[numeric_columns] = frame[numeric_columns].apply(
            pd.to_numeric,
            errors="coerce",
        )

        frames.append(frame)

    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["timestamp"]).drop_duplicates(subset=["timestamp"])
    out = out.set_index("timestamp").sort_index()

    if not include_status:
        status_columns = [column for column in out.columns if "status" in column]
        out = out.drop(columns=status_columns)

    if start is not None:
        out = out.loc[out.index >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        out = out.loc[out.index <= pd.Timestamp(end, tz="UTC")]

    if frequency:
        observation_count = out["iot_co2_ppm"].resample(frequency).count()
        out = out.resample(frequency).mean()
        out["iot_observation_count"] = observation_count.rename("iot_observation_count")
    else:
        out["iot_observation_count"] = 1

    return out


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

    The stored Visual Crossing CSVs use local civil timestamps without an
    offset. Kerkrade, Maastricht, Aachen, and Liege share the same CET/CEST
    transitions, so the configured timezone is applied before converting to UTC.
    Use ``wide=False`` when you want one row per location-hour; use ``wide=True``
    for the joined modelling shape with location-prefixed columns.
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
    out = out.dropna(subset=["timestamp"]).sort_values(
        ["weather_location", "timestamp"]
    )
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
        prefix = _safe_column_token(location)
        location_wide = location_frame.set_index("timestamp")[numeric_columns].add_prefix(
            f"{prefix}_"
        )
        wide_frames.append(location_wide)

    return pd.concat(wide_frames, axis=1).sort_index()


def load_discharge(
    raw_dir="data/raw/discharge",
    frequency="h",
    sources=None,
    start=None,
    end=None,
):
    """Load Worm/Geul discharge data and return a UTC-indexed wide frame.

    Parameters
    ----------
    raw_dir:
        Directory containing the raw JSON payloads downloaded by
        ``scripts/01_ingest_discharge.py``.
    frequency:
        Pandas resampling frequency. Use ``None`` to keep source resolution.
    sources:
        Optional iterable of source keys from ``DISCHARGE_SOURCES``.
    start, end:
        Optional timestamp bounds applied after parsing.
    """
    raw_path = Path(raw_dir)
    selected_sources = sources or DISCHARGE_SOURCES.keys()
    frames = []

    for source_key in selected_sources:
        source = DISCHARGE_SOURCES[source_key]
        path = raw_path / source["filename"]
        if not path.exists():
            raise FileNotFoundError(f"Missing discharge raw file: {path}")

        if source["format"] == "wver":
            series = _load_wver_series(path, source["encoding"])
        elif source["format"] == "waterstandlimburg":
            series = _load_waterstandlimburg_series(path, source["encoding"])
        else:
            raise ValueError(f"Unknown discharge source format: {source['format']}")

        frames.append(series.rename(source["column"]))

    out = pd.concat(frames, axis=1).sort_index()

    if start is not None:
        out = out.loc[out.index >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        out = out.loc[out.index <= pd.Timestamp(end, tz="UTC")]

    if frequency:
        out = out.resample(frequency).mean()

    return out


def _load_wver_series(path, encoding):
    """Read the public WVER JSON time series into a numeric UTC series."""
    with open(path, encoding=encoding) as handle:
        payload = json.load(handle)

    frame = pd.DataFrame(payload["data"], columns=["timestamp", "value"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame.set_index("timestamp")["value"].dropna()


def _load_waterstandlimburg_series(path, encoding):
    """Read Waterstand Limburg OData-style measurements into a UTC series."""
    with open(path, encoding=encoding) as handle:
        payload = json.load(handle)

    frame = pd.DataFrame(payload["value"])
    frame["timestamp"] = pd.to_datetime(frame["DateTime"], utc=True)
    frame["value"] = pd.to_numeric(frame["Value"], errors="coerce")
    return frame.set_index("timestamp")["value"].dropna()


def _safe_column_token(value):
    """Make a stable, lowercase token for location-prefixed weather columns."""
    return "".join(
        char.lower() if char.isalnum() else "_" for char in str(value)
    ).strip("_")


def load_knmi(*args, **kwargs):
    """Load cached KNMI reference meteorological files into an hourly frame.

    The KNMI Data Platform is file-based. This loader intentionally keeps the
    parsing side simple: it accepts cached CSV or JSON exports and normalizes
    common KNMI column names into the chapter's UTC hourly convention. If a raw
    NetCDF file is present, convert/export it to CSV first or add an xarray-based
    parser later.
    """
    raw_dir = kwargs.pop("raw_dir", args[0] if args else "data/raw/knmi")
    frequency = kwargs.pop("frequency", "h")
    station = kwargs.pop("station", None)
    start = kwargs.pop("start", None)
    end = kwargs.pop("end", None)
    if kwargs:
        raise TypeError(f"Unexpected load_knmi arguments: {sorted(kwargs)}")

    raw_path = Path(raw_dir)
    files = sorted(
        [
            *raw_path.glob("*.csv"),
            *raw_path.glob("*.json"),
            *raw_path.glob("*.jsonl"),
        ]
    )
    if not files:
        netcdf_files = sorted([*raw_path.glob("*.nc"), *raw_path.glob("*.nc4")])
        if netcdf_files:
            raise ValueError(
                "KNMI NetCDF files are present, but this lightweight loader "
                "expects CSV/JSON exports. Convert the selected station-hour "
                "records to CSV and rerun."
            )
        raise FileNotFoundError(f"No cached KNMI CSV/JSON files found in {raw_path}")

    frames = []
    for path in files:
        frame = _read_table(path)
        if frame.empty:
            continue
        frames.append(_normalize_knmi_frame(frame))

    if not frames:
        raise ValueError(f"KNMI files in {raw_path} did not contain usable rows")

    out = pd.concat(frames, ignore_index=True)
    if station is not None and "knmi_station" in out:
        out = out.loc[out["knmi_station"].astype(str).isin({str(station)})]
    out = out.dropna(subset=["timestamp_utc"]).drop_duplicates(
        subset=["timestamp_utc", "knmi_station"],
        keep="last",
    )

    if start is not None:
        out = out.loc[out["timestamp_utc"] >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        out = out.loc[out["timestamp_utc"] <= pd.Timestamp(end, tz="UTC")]

    numeric_columns = [
        column
        for column in out.columns
        if column not in {"timestamp_utc", "knmi_station", "knmi_source_file"}
    ]
    out[numeric_columns] = out[numeric_columns].apply(pd.to_numeric, errors="coerce")

    if frequency:
        out = (
            out.set_index("timestamp_utc")
            .groupby("knmi_station")
            .resample(frequency)[numeric_columns]
            .mean()
            .reset_index()
        )

    return out.sort_values(["knmi_station", "timestamp_utc"])


def load_rivm(
    raw_dir="data/raw/transfer/rivm",
    frequency="h",
    stations=None,
    components=None,
    wide=True,
    start=None,
    end=None,
):
    """Load cached RIVM/Luchtmeetnet measurements into UTC hourly data.

    The public API returns JSON objects with ``station_number``, ``formula``,
    ``value``, and ``timestamp_measured``. This loader accepts any cached JSON
    payloads that contain those records and returns either a long measurement
    table or a wide modelling frame.
    """
    raw_path = Path(raw_dir)
    json_files = sorted(raw_path.glob("measurements*.json"))
    csv_files = sorted([*raw_path.glob("portal_*.csv"), *raw_path.glob("20??_??_*.csv")])
    files = [*json_files, *csv_files]
    if not files:
        raise FileNotFoundError(f"No cached RIVM measurement files found in {raw_path}")

    rows = []
    frames = []
    for path in json_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        data = payload if isinstance(payload, list) else payload.get("data", [])
        for row in data:
            if {"station_number", "formula", "value", "timestamp_measured"} <= set(row):
                rows.append(row)
    if rows:
        frame = pd.DataFrame(rows)
        frames.append(
            pd.DataFrame(
                {
                    "timestamp_utc": pd.to_datetime(
                        frame["timestamp_measured"],
                        utc=True,
                    ),
                    "station_number": frame["station_number"].astype(str),
                    "formula": frame["formula"].astype(str).str.upper(),
                    "value": pd.to_numeric(frame["value"], errors="coerce"),
                }
            )
        )

    for path in csv_files:
        frame = pd.read_csv(path, sep=";", comment="#")
        required = {"meetlocatie_id", "component", "begindatumtijd", "waarde"}
        if not required <= set(frame.columns):
            continue
        frames.append(
            pd.DataFrame(
                {
                    "timestamp_utc": pd.to_datetime(
                        frame["begindatumtijd"],
                        utc=True,
                    ),
                    "station_number": frame["meetlocatie_id"].astype(str),
                    "formula": frame["component"].astype(str).str.upper(),
                    "value": pd.to_numeric(frame["waarde"], errors="coerce"),
                }
            )
        )

    if not frames:
        raise ValueError(f"RIVM files in {raw_path} did not contain measurement rows")

    out = pd.concat(frames, ignore_index=True)
    if stations is not None:
        out = out.loc[out["station_number"].isin({str(station) for station in stations})]
    if components is not None:
        out = out.loc[out["formula"].isin({str(component).upper() for component in components})]
    if start is not None:
        out = out.loc[out["timestamp_utc"] >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        out = out.loc[out["timestamp_utc"] <= pd.Timestamp(end, tz="UTC")]

    out = out.dropna(subset=["timestamp_utc", "value"])
    if frequency:
        out = (
            out.set_index("timestamp_utc")
            .groupby(["station_number", "formula"])["value"]
            .resample(frequency)
            .mean()
            .rename("value")
            .reset_index()
        )

    if not wide:
        return out.sort_values(["station_number", "formula", "timestamp_utc"])

    out["series"] = (
        "rivm_"
        + out["station_number"].map(_safe_column_token)
        + "_"
        + out["formula"].map(_safe_column_token)
        + "_ugm3"
    )
    wide_frame = out.pivot_table(
        index="timestamp_utc",
        columns="series",
        values="value",
        aggfunc="mean",
    )
    return wide_frame.sort_index()


def _read_table(path):
    """Read one cached CSV/JSON table."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() == ".jsonl":
        return pd.read_json(path, lines=True)

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        data = payload
    else:
        data = payload.get("data", payload.get("records", []))
    return pd.DataFrame(data)


def _normalize_knmi_frame(frame):
    """Normalize common KNMI station-observation columns."""
    out = frame.copy()
    out.columns = [str(column).strip() for column in out.columns]

    timestamp_col = _first_existing(
        out,
        ["timestamp_utc", "timestamp", "datetime", "time", "valid_time", "date"],
    )
    if timestamp_col is not None:
        out["timestamp_utc"] = pd.to_datetime(out[timestamp_col], utc=True, errors="coerce")
    elif {"YYYYMMDD", "HH"} <= set(out.columns):
        hour = pd.to_numeric(out["HH"], errors="coerce").fillna(1).astype(int)
        base = pd.to_datetime(out["YYYYMMDD"].astype(str), format="%Y%m%d", errors="coerce")
        out["timestamp_utc"] = (base + pd.to_timedelta(hour - 1, unit="h")).dt.tz_localize("UTC")
    else:
        raise ValueError("KNMI file is missing a recognizable timestamp column")

    station_col = _first_existing(out, ["knmi_station", "station", "station_code", "STN"])
    out["knmi_station"] = out[station_col].astype(str) if station_col else "unknown"

    column_map = {
        "P": "knmi_pressure_hpa",
        "pressure": "knmi_pressure_hpa",
        "pressure_hpa": "knmi_pressure_hpa",
        "air_pressure": "knmi_pressure_hpa",
        "T": "knmi_temperature_c",
        "temp": "knmi_temperature_c",
        "temperature": "knmi_temperature_c",
        "temperature_c": "knmi_temperature_c",
        "U": "knmi_relative_humidity_pct",
        "humidity": "knmi_relative_humidity_pct",
        "relative_humidity": "knmi_relative_humidity_pct",
        "relative_humidity_pct": "knmi_relative_humidity_pct",
        "RH": "knmi_precip_mm",
        "precip": "knmi_precip_mm",
        "precipitation": "knmi_precip_mm",
        "precip_mm": "knmi_precip_mm",
    }

    keep = ["timestamp_utc", "knmi_station"]
    for source, target in column_map.items():
        if source in out:
            out[target] = pd.to_numeric(out[source], errors="coerce")
            keep.append(target)

    for column in ["knmi_pressure_hpa", "knmi_temperature_c", "knmi_precip_mm"]:
        if column in out:
            out[column] = _auto_scale_knmi_units(out[column], column)

    return out[list(dict.fromkeys(keep))]


def _first_existing(frame, candidates):
    """Return the first candidate column present in a frame."""
    return next((column for column in candidates if column in frame.columns), None)


def _auto_scale_knmi_units(series, column):
    """Scale common KNMI tenths-units into ordinary chapter units."""
    median = series.abs().median(skipna=True)
    if pd.isna(median):
        return series
    if column == "knmi_pressure_hpa" and median > 2000:
        return series / 10
    if column == "knmi_temperature_c" and median > 80:
        return series / 10
    if column == "knmi_precip_mm" and median > 100:
        return series / 10
    return series
