"""Check potentially freezing RADOLAN episodes with already-held ERA5-Land t2m.

Temperature is a coarse precipitation-phase indicator, not an observation of
rain versus snow. This is a sensitivity, not an added main-model covariate.
Run with the chapter1-co2 Python environment, which has xarray/netCDF4.
"""

from __future__ import annotations

import hashlib
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load_script("53_cross_tributary_rain_episodes")
weather_builder = load_script("40_build_event_study_weather")
model = load_script("55_fit_cross_tributary_footprint")
OUT = core.OUT


def temperature_table(months, sites):
    frames = []
    for year, month in months:
        path = weather_builder.ERA5 / f"era5_land_limburg_{year:04d}_{month:02d}.nc"
        if not path.exists():
            raise FileNotFoundError(path)
        with xr.open_dataset(path) as ds:
            if ds.t2m.attrs.get("units") != "K":
                raise ValueError(f"Unexpected temperature units: {path}")
            times = pd.to_datetime(ds.valid_time.to_numpy(), utc=True)
            frame = pd.DataFrame(index=times)
            for site in sites.itertuples(index=False):
                point = ds.t2m.sel(
                    latitude=site.centroid_lat, longitude=site.centroid_lon, method="nearest"
                )
                frame[site.watercourse] = point.to_numpy() - 273.15
            frames.append(frame)
    result = pd.concat(frames).sort_index()
    if result.index.has_duplicates or not result.index.is_monotonic_increasing:
        raise ValueError("ERA5-Land temperature axis is not unique and ordered")
    return result


def phase_audit(episodes, rain, temperature):
    rows = []
    for event in episodes.itertuples(index=False):
        rainfall = rain.loc[event.rain_start_utc : event.rain_end_utc].max(axis=1)
        thermal = temperature.loc[event.rain_start_utc : event.rain_end_utc]
        if not rainfall.index.equals(thermal.index) or thermal.isna().any().any():
            raise ValueError(f"Incomplete temperature for {event.episode_id}")
        wet = rainfall.ge(core.WET_MM_H)
        median_t = thermal.median(axis=1)
        peak_time = rainfall.idxmax()
        rows.append(
            {
                "episode_id": event.episode_id,
                "rain_year": event.rain_year,
                "n_wet_hours": int(wet.sum()),
                "n_wet_hours_median_temp_le_0c": int((wet & median_t.le(0)).sum()),
                "n_wet_hours_median_temp_le_2c": int((wet & median_t.le(2)).sum()),
                "rain_weighted_median_temp_c": float(
                    np.average(median_t[wet], weights=rainfall[wet])
                ),
                "median_temp_at_peak_rain_c": float(median_t.loc[peak_time]),
            }
        )
    return pd.DataFrame(rows)


def main():
    episodes = pd.read_csv(
        OUT / "rain_episodes.csv", parse_dates=["rain_start_utc", "rain_end_utc"]
    )
    rain = core.read_hourly(core.DATA / "radolan_catchment_hourly.csv")[list(core.SITES)]
    months = sorted(
        {
            (stamp.year, stamp.month)
            for event in episodes.itertuples(index=False)
            for stamp in pd.period_range(
                event.rain_start_utc.tz_localize(None).to_period("M"),
                event.rain_end_utc.tz_localize(None).to_period("M"),
                freq="M",
            ).to_timestamp()
        }
    )
    sites = weather_builder.centroids()
    sites = sites.loc[sites.watercourse.isin(core.SITES)]
    if set(sites.watercourse) != set(core.SITES) or len(sites) != len(core.SITES):
        raise ValueError("Temperature centroids do not match the six-site cohort")
    temperature = temperature_table(months, sites)
    audit = phase_audit(episodes, rain, temperature)
    audit.to_csv(OUT / "precipitation_phase_audit.csv", index=False)

    frame = pd.read_csv(OUT / "model_primary_events.csv")
    frame = frame.merge(audit, on=["episode_id", "rain_year"], validate="one_to_one")
    candidates = {
        "phase_no_freezing_wet_hour": frame.loc[frame.n_wet_hours_median_temp_le_0c.eq(0)],
        "phase_rain_weighted_above_2c": frame.loc[frame.rain_weighted_median_temp_c.gt(2)],
    }
    summaries = []
    for name, subset in candidates.items():
        summary, draws, _ = model.summarize_fit(name, subset)
        summaries.append(summary)
        draws.to_csv(OUT / f"model_draws_{name}.csv", index=False)
    pd.DataFrame(summaries).to_csv(OUT / "precipitation_phase_model_sensitivity.csv", index=False)
    manifest = {
        "status": "temperature-based precipitation-phase sensitivity, not phase observation",
        "temperature_source": "held ERA5-Land t2m at catchment-centroid nearest cells",
        "n_temperature_months": len(months),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "precipitation_phase_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
