"""Validate compact regional input tables without changing the verification cohort."""

from __future__ import annotations

import numpy as np
import pandas as pd


def selected_mapping(ledger, roles):
    table = ledger.loc[ledger.resolved_role.isin(roles)].sort_values("gauge_id").copy()
    if table.gauge_id.duplicated().any() or table.best_river_id.isna().any():
        raise ValueError("Each selected gauge needs one recorded model-reach correspondence")
    if not np.isfinite(table.reference_area_km2).all() or not table.reference_area_km2.gt(0).all():
        raise ValueError("Reference areas must be positive")
    table["best_river_id"] = table.best_river_id.astype("int64")
    return table


def check_ids(frame, expected):
    if frame.gauge.duplicated().any() or set(frame.gauge) != set(expected):
        raise ValueError("Spatial rows must preserve every requested gauge exactly once")


def weather_table(features, year, bands, expected):
    dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", tz="UTC")
    rows = []
    for item in features:
        p = item["properties"]
        area = p.get("sampled_area_m2")
        if area is None or not np.isfinite(area) or area <= 0:
            raise ValueError(f"No native weather-grid support for {p.get('gauge')}")
        for day in dates:
            row = dict(gauge=p["gauge"], day=day, sampled_area_m2=area)
            for band in bands:
                value = p.get(f"{day:%Y%m%d}_{band}")
                row[band] = np.nan if value is None else value / area
            rows.append(row)
    frame = pd.DataFrame(rows)
    if frame.duplicated(["gauge", "day"]).any():
        raise ValueError("Duplicate weather gauge/day")
    if set(frame.gauge) != set(expected) or not frame.groupby("gauge").size().eq(len(dates)).all():
        raise ValueError("Weather calendar or gauge population differs from request")
    return frame


def spatial_table(features, expected, kind, bands):
    frame = pd.DataFrame([f["properties"] for f in features])
    check_ids(frame, expected)
    if kind == "alphaearth":
        for band in bands:
            frame[band] = frame[f"{band}_mean"]
        counts = frame[[f"{b}_count" for b in bands]]
        if not counts.ge(0).all().all() or not counts.eq(counts.iloc[:, 0], axis=0).all().all():
            raise ValueError("Embedding axes have inconsistent spatial support")
        frame["valid_pixel_count"] = counts.iloc[:, 0]
        frame["coverage_status"] = np.where(
            frame.valid_pixel_count.gt(0), "supported", "no_valid_pixels"
        )
        cols = ["gauge", "geometry_sha256", "valid_pixel_count", "coverage_status", *bands]
        return frame.reindex(columns=cols)
    if kind == "attributes":
        area = pd.to_numeric(frame["area_m2"], errors="coerce")
        for band in bands:
            frame[band] = pd.to_numeric(frame.get(band), errors="coerce") / area.where(area.gt(0))
        frame["coverage_status"] = np.where(area.gt(0), "supported", "no_common_valid_pixels")
        return frame.reindex(
            columns=["gauge", "geometry_sha256", "area_m2", "coverage_status", *bands]
        )
    raise ValueError(kind)
