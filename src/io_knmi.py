"""KNMI reference meteorology loaders."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# KNMI hourly text-file codes are stored in tenths of a unit; the NetCDF 10-min
# in-situ product uses SI names that are already scaled. Scale deterministically
# by the matched source code instead of guessing from the sample median. Codes
# absent here (e.g. lowercase SI names, humidity in whole percent) keep 1.0.
KNMI_UNIT_FACTORS = {
    "T": 0.1,  # 0.1 degC
    "P": 0.1,  # 0.1 hPa
    "RH": 0.1,  # 0.1 mm precipitation
    "R1H": 0.1,  # 0.1 mm hourly precipitation
}

# Plausibility bounds used only to warn when a unit factor looks wrong.
KNMI_VALID_RANGES = {
    "knmi_temperature_c": (-40.0, 50.0),
    "knmi_pressure_hpa": (870.0, 1085.0),
    "knmi_relative_humidity_pct": (0.0, 100.0),
    "knmi_precip_mm": (0.0, 200.0),
}


KNMI_STATION_SETS = {
    "maastricht": {
        "06380": "Maastricht Airport",
    },
    "meuse": {
        "06380": "Maastricht Airport",
        "06377": "Ell",
        "06392": "Horst",
        "06370": "Eindhoven Airport",
        "06375": "Volkel Airport",
        "06350": "Gilze-Rijen Airport",
        "06356": "Herwijnen",
    },
}


def load_knmi(
    raw_dir="data/raw/knmi",
    frequency="h",
    station=None,
    stations=None,
    station_set=None,
    start=None,
    end=None,
):
    """Load cached KNMI reference meteorological files into an hourly frame.

    The loader accepts cached CSV, CSV.GZ, Parquet, JSON, JSONL, or NetCDF files
    and normalizes common KNMI column names into the chapter's UTC convention.
    """
    raw_path = Path(raw_dir)
    files = sorted(
        [
            *raw_path.glob("**/*.csv"),
            *raw_path.glob("**/*.csv.gz"),
            *raw_path.glob("**/*.parquet"),
            *raw_path.glob("**/*.json"),
            *raw_path.glob("**/*.jsonl"),
            *raw_path.glob("**/*.nc"),
            *raw_path.glob("**/*.nc4"),
        ]
    )
    files = [
        path for path in files if path.parent == raw_path or path.name.lower().startswith("knmi")
    ]
    if not files:
        raise FileNotFoundError(f"No cached KNMI table or NetCDF files found in {raw_path}")

    frames = []
    for path in files:
        if path.suffix.lower() in {".nc", ".nc4"}:
            frame = _read_knmi_netcdf(path)
        else:
            frame = _read_table(path)
        if frame.empty:
            continue
        frames.append(_normalize_knmi_frame(frame))

    if not frames:
        raise ValueError(f"KNMI files in {raw_path} did not contain usable rows")

    out = pd.concat(frames, ignore_index=True)
    station_filter = _knmi_station_filter(
        station=station,
        stations=stations,
        station_set=station_set,
    )
    if station_filter is not None and "knmi_station" in out:
        out = out.loc[out["knmi_station"].isin(station_filter)]
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
        out = out.dropna(subset=numeric_columns, how="all")

    return out.sort_values(["knmi_station", "timestamp_utc"])


def knmi_station_set_frame(station_set="meuse"):
    """Return a small station table for a named KNMI station set."""
    if station_set not in KNMI_STATION_SETS:
        known = ", ".join(sorted(KNMI_STATION_SETS))
        raise ValueError(f"Unknown KNMI station set {station_set!r}; choose one of {known}")
    return pd.DataFrame(
        [
            {
                "station_set": station_set,
                "knmi_station": station,
                "station_name": name,
            }
            for station, name in KNMI_STATION_SETS[station_set].items()
        ]
    )


def _read_table(path):
    """Read one cached KNMI table.

    Azure may return a `.csv.gz` blob already decoded because the blob metadata
    uses `contentEncoding=gzip`. Check the magic bytes instead of trusting the
    suffix so local syncs are robust to both cases.
    """
    suffixes = "".join(path.suffixes).lower()
    if suffixes.endswith(".csv.gz"):
        with Path(path).open("rb") as handle:
            is_gzip = handle.read(2) == b"\x1f\x8b"
        return pd.read_csv(path, compression="gzip" if is_gzip else None)
    if suffixes.endswith(".csv"):
        return pd.read_csv(path)
    if suffixes.endswith(".parquet"):
        return pd.read_parquet(path)
    if suffixes.endswith(".jsonl"):
        return pd.read_json(path, lines=True)

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        data = payload
    else:
        data = payload.get("data", payload.get("records", []))
    return pd.DataFrame(data)


def _read_knmi_netcdf(path):
    """Read one KNMI NetCDF/HDF5 file into a flat observation table."""
    try:
        import xarray as xr
    except ImportError as exc:
        raise ValueError(
            "KNMI NetCDF files are cached, but xarray/netCDF4 are not installed. "
            "Run `conda env update -f environment.yml --prune` in the repo root, "
            "then rerun `python scripts/04_ingest_knmi.py`."
        ) from exc

    dataset = xr.open_dataset(path)
    try:
        frame = dataset.to_dataframe().reset_index()
    finally:
        dataset.close()
    frame["knmi_source_file"] = Path(path).name
    return frame


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

    station_col = _first_existing(
        out,
        ["knmi_station", "station", "station_code", "station_id", "STN"],
    )
    out["knmi_station"] = (
        out[station_col].map(_normalize_knmi_station_code) if station_col else "unknown"
    )

    target_columns = {
        "knmi_pressure_hpa": [
            "P",
            "pp",
            "qnh",
            "p0",
            "ps",
            "pres",
            "pressure",
            "pressure_hpa",
            "air_pressure",
        ],
        "knmi_temperature_c": [
            "T",
            "ta",
            "t10",
            "temp",
            "temperature",
            "temperature_c",
        ],
        "knmi_relative_humidity_pct": [
            "U",
            "rh",
            "rh10",
            "humidity",
            "relative_humidity",
            "relative_humidity_pct",
        ],
        "knmi_precip_mm": [
            "RH",
            "R1H",
            "rr",
            "precipitation_amount",
            "precip",
            "precipitation",
            "precip_mm",
        ],
    }

    keep = ["timestamp_utc", "knmi_station"]
    for target, candidates in target_columns.items():
        source_col = _first_knmi_value_column(out, candidates)
        if source_col is None:
            continue
        values = pd.to_numeric(out[source_col], errors="coerce")
        values = values * KNMI_UNIT_FACTORS.get(source_col, 1.0)
        if target == "knmi_precip_mm":
            # KNMI encodes a trace amount (<0.05 mm) as -1; map it to 0.
            values = values.mask(values < 0, 0.0)
        _validate_knmi_range(values, target, source_col)
        out[target] = values
        keep.append(target)

    return out[list(dict.fromkeys(keep))]


def _knmi_station_filter(station=None, stations=None, station_set=None):
    """Resolve station arguments into normalized KNMI station IDs."""
    selected = set()
    if station_set and str(station_set).lower() not in {"none", "all"}:
        selected.update(KNMI_STATION_SETS[str(station_set).lower()])

    station_values = []
    if station is not None:
        station_values.extend(_split_station_values(station))
    if stations is not None:
        station_values.extend(_split_station_values(stations))

    for value in station_values:
        token = str(value).strip()
        lower = token.lower()
        if lower in KNMI_STATION_SETS:
            selected.update(KNMI_STATION_SETS[lower])
        elif lower not in {"", "none", "all"}:
            selected.add(_normalize_knmi_station_code(token))

    return selected or None


def _split_station_values(values):
    """Split station CLI/list values into tokens."""
    if isinstance(values, (list, tuple, set)):
        out = []
        for value in values:
            out.extend(_split_station_values(value))
        return out
    return [value.strip() for value in str(values).split(",")]


def _normalize_knmi_station_code(value):
    """Normalize KNMI station codes across 3-, 4-, and 5-digit forms."""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(char for char in text if char.isdigit())
    if len(digits) == 3:
        return f"06{digits}"
    if len(digits) == 4:
        return digits.zfill(5)
    return digits or text


def _first_existing(frame, candidates):
    """Return the first candidate column present in a frame."""
    columns = {str(column).lower(): column for column in frame.columns}
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
        match = columns.get(str(candidate).lower())
        if match is not None:
            return match
    return None


def _first_knmi_value_column(frame, candidates):
    """Return a KNMI value column, preserving case-sensitive code meanings."""
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    lower_lookup = {str(column).lower(): column for column in frame.columns}
    for candidate in candidates:
        match = lower_lookup.get(str(candidate).lower())
        if match is not None:
            return match
    return None


def _validate_knmi_range(series, target, source_col):
    """Warn when scaled KNMI values fall outside physically plausible bounds.

    This is a backstop for a wrong unit factor: a magnitude error surfaces as a
    loud log warning rather than a silent 10x error in the modelling exog.
    """
    bounds = KNMI_VALID_RANGES.get(target)
    if bounds is None:
        return
    low, high = bounds
    finite = pd.Series(series).dropna()
    if finite.empty:
        return
    out_of_range = float(((finite < low) | (finite > high)).mean())
    if out_of_range > 0:
        logger.warning(
            "KNMI %s (from %r): %.1f%% of values outside plausible range "
            "[%s, %s]; check the unit factor.",
            target,
            source_col,
            100 * out_of_range,
            low,
            high,
        )
