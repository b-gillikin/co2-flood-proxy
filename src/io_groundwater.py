"""Canonical normalization and locked selection for direct-state water data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

READING_COLUMNS = ("timestamp", "series_id", "water_level_value")
METADATA_COLUMNS = (
    "series_id",
    "provider",
    "measurement_name",
    "unit",
    "datum",
    "source_tier",
    "site_relationship",
    "higher_value_means_higher_water",
    "operational_notes",
)


def _required(frame, columns, label):
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


def _boolean(value):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    token = str(value).strip().lower()
    if token in {"true", "1", "yes", "y"}:
        return True
    if token in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def validate_series_metadata(metadata):
    """Validate and normalize the source metadata needed before modelling."""
    metadata = pd.DataFrame(metadata).copy()
    _required(metadata, METADATA_COLUMNS, "Groundwater metadata")
    metadata = metadata.loc[:, METADATA_COLUMNS]
    if metadata["series_id"].duplicated().any():
        duplicates = metadata.loc[metadata["series_id"].duplicated(), "series_id"].tolist()
        raise ValueError("Duplicate groundwater series metadata: " + ", ".join(duplicates))
    metadata["source_tier"] = pd.to_numeric(metadata["source_tier"], errors="raise").astype(int)
    if not metadata["source_tier"].isin((1, 2)).all():
        raise ValueError("source_tier must be 1 (direct mine/shaft) or 2 (nearby groundwater)")
    metadata["higher_value_means_higher_water"] = metadata["higher_value_means_higher_water"].map(
        _boolean
    )
    blank = metadata[["series_id", "provider", "measurement_name", "unit", "datum"]].apply(
        lambda column: column.astype(str).str.strip().eq("")
    )
    if blank.any(axis=None):
        raise ValueError(
            "Groundwater identity, provider, measurement, unit, and datum cannot be blank"
        )
    return metadata


def normalize_groundwater(readings, metadata, source_timezone="UTC"):
    """Normalize source readings to observed UTC days without interpolation.

    ``hydrologic_level`` is oriented so larger values always mean higher water.
    Source-native ``water_level_value`` remains available for auditability.
    """
    readings = pd.DataFrame(readings).copy()
    metadata = validate_series_metadata(metadata)
    _required(readings, READING_COLUMNS, "Groundwater readings")
    unknown = sorted(set(readings["series_id"].dropna()) - set(metadata["series_id"]))
    if unknown:
        raise ValueError("Readings lack metadata for series: " + ", ".join(unknown))

    timestamps = pd.to_datetime(readings["timestamp"], errors="coerce")
    if timestamps.isna().any():
        raise ValueError("Groundwater timestamps contain unparseable values")
    if timestamps.dt.tz is None:
        timestamps = timestamps.dt.tz_localize(
            source_timezone,
            ambiguous="raise",
            nonexistent="raise",
        )
    readings["timestamp_utc"] = timestamps.dt.tz_convert("UTC")
    readings["water_level_value"] = pd.to_numeric(readings["water_level_value"], errors="coerce")
    readings["is_usable"] = readings["is_usable"].map(_boolean) if "is_usable" in readings else True
    readings["quality_flag"] = (
        readings["quality_flag"].fillna("").astype(str) if "quality_flag" in readings else ""
    )
    readings = readings.merge(
        metadata[["series_id", "higher_value_means_higher_water"]],
        on="series_id",
        how="left",
        validate="many_to_one",
    )
    readings["date_utc"] = readings["timestamp_utc"].dt.floor("D")
    direction = np.where(readings["higher_value_means_higher_water"], 1.0, -1.0)
    readings["hydrologic_level"] = readings["water_level_value"] * direction

    rows = []
    for (date_utc, series_id), group in readings.groupby(["date_utc", "series_id"]):
        usable = group.loc[group["is_usable"] & group["water_level_value"].notna()]
        rows.append(
            {
                "date_utc": date_utc,
                "series_id": series_id,
                "water_level_value": usable["water_level_value"].mean(),
                "hydrologic_level": usable["hydrologic_level"].mean(),
                "source_observations": len(group),
                "usable_observations": len(usable),
                "quality_flags": "|".join(
                    sorted(flag for flag in group["quality_flag"].unique() if flag)
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(["series_id", "date_utc"]).reset_index(drop=True)


def select_primary_series(daily, metadata, eligible_dates):
    """Apply the locked tier-then-IoT-overlap hierarchy without using outcomes."""
    daily = pd.DataFrame(daily).copy()
    metadata = validate_series_metadata(metadata)
    _required(daily, ("date_utc", "series_id", "hydrologic_level"), "Groundwater daily data")
    daily["date_utc"] = pd.to_datetime(daily["date_utc"], utc=True).dt.floor("D")
    eligible_dates = set(pd.to_datetime(pd.Index(eligible_dates), utc=True).floor("D"))
    rows = []
    for item in metadata.itertuples(index=False):
        observed = daily.loc[
            daily["series_id"].eq(item.series_id) & daily["hydrologic_level"].notna(),
            "date_utc",
        ]
        rows.append(
            {
                "series_id": item.series_id,
                "source_tier": item.source_tier,
                "provider": item.provider,
                "measurement_name": item.measurement_name,
                "site_relationship": item.site_relationship,
                "iot_overlap_days": len(set(observed) & eligible_dates),
                "observed_days": observed.nunique(),
            }
        )
    audit = pd.DataFrame(rows).sort_values(
        ["source_tier", "iot_overlap_days", "series_id"],
        ascending=[True, False, True],
    )
    candidates = audit.loc[audit["iot_overlap_days"] > 0]
    if candidates.empty:
        raise ValueError("No groundwater series overlaps an eligible IoT day")
    best_tier = candidates["source_tier"].min()
    primary = candidates.loc[candidates["source_tier"].eq(best_tier)].iloc[0]["series_id"]
    audit["selected_primary"] = audit["series_id"].eq(primary)
    audit["selection_reason"] = np.where(
        audit["selected_primary"],
        "lowest source tier, then greatest IoT overlap",
        "sensitivity or non-overlapping series",
    )
    return primary, audit.reset_index(drop=True)


def load_groundwater(daily_path, metadata_path):
    """Load normalized daily values and their required series metadata."""
    daily = pd.read_csv(Path(daily_path), parse_dates=["date_utc"])
    daily["date_utc"] = pd.to_datetime(daily["date_utc"], utc=True)
    metadata = validate_series_metadata(pd.read_csv(Path(metadata_path)))
    return daily, metadata
