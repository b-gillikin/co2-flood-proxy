"""Discharge loaders for Wurm/Geul source streams."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

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


def load_discharge(
    raw_dir="data/raw/discharge",
    frequency="h",
    sources=None,
    start=None,
    end=None,
):
    """Load Wurm/Geul discharge data and return a UTC-indexed wide frame."""
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
