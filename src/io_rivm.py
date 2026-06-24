"""RIVM/Luchtmeetnet transfer-site loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


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

    The live API returns JSON rows with station, component, value, and measured
    timestamp fields. The RIVM data portal provides semicolon CSV files with the
    same information under Dutch column names.
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


def _safe_column_token(value):
    """Make a stable lowercase token for RIVM wide-column names."""
    return "".join(
        char.lower() if char.isalnum() else "_" for char in str(value)
    ).strip("_")
