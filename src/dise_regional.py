"""Common daily features and leakage-safe regional folds for the accepted DISE study."""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

WEATHER = dict(
    zip(
        [
            "total_precipitation_sum",
            "temperature_2m",
            "dewpoint_temperature_2m",
            "surface_pressure",
            "u_component_of_wind_10m",
            "v_component_of_wind_10m",
            "surface_solar_radiation_downwards_sum",
            "surface_thermal_radiation_downwards_sum",
        ],
        [
            "h_precip_m",
            "h_temp_k",
            "h_dewpoint_k",
            "h_pressure_pa",
            "h_u10",
            "h_v10",
            "h_shortwave_j",
            "h_longwave_j",
        ],
        strict=True,
    )
)


def gauge_features(frame, metadata, attributes, embedding):
    """Predictor histories cross year boundaries; observed Q never creates a feature."""
    f = frame.sort_values("day").reset_index(drop=True).copy()
    if f.day.duplicated().any() or not f.day.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("A gauge needs a complete, unique daily calendar before shifting")
    for col in ["h_precip_m", "h_shortwave_j", "h_longwave_j"]:
        f[col] = f[col].where(f[col].ge(0))
    f["h_q_model"] = f.q_model
    f["h_season_sin"] = np.sin(2 * np.pi * f.day.dt.dayofyear / 365.25)
    f["h_season_cos"] = np.cos(2 * np.pi * f.day.dt.dayofyear / 365.25)
    f["h_wind_speed"] = np.hypot(f.h_u10, f.h_v10)
    t, d = f.h_temp_k - 273.15, f.h_dewpoint_k - 273.15
    f["h_relative_humidity"] = 100 * np.exp(17.625 * d / (243.04 + d) - 17.625 * t / (243.04 + t))
    lags = {
        f"{col}_lag{k}": f[col].shift(k)
        for col in ["h_q_model", *WEATHER.values(), "h_wind_speed", "h_relative_humidity"]
        for k in range(1, 8)
    }
    static = {c: attributes[c] for c in attributes.index if c.startswith("a_")}
    static.update(
        a_log_area_km2=np.log(metadata.reference_area_km2),
        a_latitude=metadata.gauge_lat,
        a_longitude=metadata.gauge_lon,
        h_mapping_area_ratio=metadata.model_outlet_area_km2 / metadata.reference_area_km2,
        h_mapping_overlap=metadata.reference_covered,
    )
    static.update({f"e_A{i:02d}": embedding[f"A{i:02d}"] for i in range(64)})
    for year in sorted(f.day.dt.year.unique()):
        past = f.loc[f.day.lt(f"{year}-01-01")]
        use = f.day.dt.year.eq(year)
        f.loc[use, "a_past_precip_mean_m"] = past.h_precip_m.mean()
        f.loc[use, "a_past_temp_mean_k"] = past.h_temp_k.mean()
        f.loc[use, "a_past_temp_sd_k"] = past.h_temp_k.std()
    f = pd.concat(
        [f, pd.DataFrame(lags), pd.DataFrame({k: [v] * len(f) for k, v in static.items()})], axis=1
    )
    return f.loc[f.day.ge("2018-01-01")].reset_index(drop=True)


def fold_assignments(groups, count, seed):
    groups = sorted(set(groups), key=lambda g: hashlib.sha256(f"{seed}:{g}".encode()).hexdigest())
    return {g: i % count for i, g in enumerate(groups)}


def regional_masks(frame, year, held):
    good = np.isfinite(frame[["q_observed", "q_model"]]).all(axis=1).to_numpy()
    allowed = (
        frame.source_role.isin(["regional_donor", "local"]).to_numpy()
        & frame.river_group.ne(held).to_numpy()
    )
    train = (
        allowed
        & frame.day.ge("2018-01-01").to_numpy()
        & frame.day.lt(f"{year - 1}-01-01").to_numpy()
        & good
    )
    valid = (
        allowed
        & frame.day.ge(f"{year - 1}-01-01").to_numpy()
        & frame.day.lt(f"{year}-01-01").to_numpy()
        & good
    )
    test_population = frame.source_role.eq("reserved_external") | (
        frame.source_role.eq("local") & frame.river_group.eq(held)
    )
    test = test_population.to_numpy() & frame.day.dt.year.eq(year).to_numpy() & good
    if set(frame.loc[train | valid, "gauge"]) & set(frame.loc[test, "gauge"]):
        raise ValueError("Outer target gauge leaked into training/validation")
    return train, valid, test


def inner_masks(frame, train, validation, assignment, fold):
    member = frame.river_group.map(assignment).eq(fold).to_numpy()
    a, b = train & ~member, validation & member
    if set(frame.loc[a, "river_group"]) & set(frame.loc[b, "river_group"]):
        raise ValueError("Inner fold splits a river group")
    return a, b
