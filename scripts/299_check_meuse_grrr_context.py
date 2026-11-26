"""Trace the three modeled outlets and compare two Meuse event hydrographs by day."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

proj_data = Path(sys.base_prefix) / "share" / "proj"
if (proj_data / "proj.db").is_file():
    os.environ.setdefault("PROJ_DATA", str(proj_data))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.geoglows_experiment import sha, write_json  # noqa: E402
from src.grrr_reanalysis import VERSION, read_daily_flow  # noqa: E402

timing = importlib.import_module("297_meuse_peak_timing")
HYDRO = ROOT.parent / "chapter3-peja/data/raw/open/hydrosheds"
RIVERS = HYDRO / "hydrorivers-v1/HydroRIVERS_v10_eu_shp.zip"
BASINS_FOLDER = HYDRO / "hydrobasins-v1c/hybas_eu_lev12_v1c"
BASINS = BASINS_FOLDER / "hybas_eu_lev12_v1c.shp"
CATCHMENT = ROOT / "data/interim/foundation_model_catchments.gpkg"
GRRR = ROOT / "data/raw/open/grrr/distributed_model_2026_11"
CATALOGUE = GRRR / "limburg-outlet-catalogue.json"
FLOW = GRRR / "meuse-2024-reanalysis.npz"
CLOCK = GRRR / "meuse-2024-time-identity.json"
PAIRINGS = {
    "Rimburg": ("subhybas_2121124850", (6.087280, 50.914658), False),
    "Borgharen Dorp": ("subhybas_2120407290", (5.691000, 50.872400), True),
    "Venlo": ("subhybas_2121120730", (6.159406, 51.367387), False),
}


def trace(rivers, first, last):
    reaches = [first]
    while reaches[-1] != last:
        following = int(rivers.loc[reaches[-1], "NEXT_DOWN"])
        if following not in rivers.index or following in reaches:
            raise ValueError(f"Could not trace HydroRIVERS path from {first} to {last}")
        reaches.append(following)
    return reaches


def assess_outlets():
    catalogue = json.loads(CATALOGUE.read_text())
    if catalogue["version"] != VERSION:
        raise ValueError("Unexpected GRRR catalogue release")
    outlets = {row["gauge_id"]: row for row in catalogue["outlets"]}
    bbox = (5.45, 50.60, 6.45, 51.50)
    rivers = (
        gpd.read_file(f"/vsizip/{RIVERS}/HydroRIVERS_v10_eu_shp/HydroRIVERS_v10_eu.shp", bbox=bbox)
        .to_crs(3035)
        .set_index("HYRIV_ID")
    )
    basins = gpd.read_file(BASINS, bbox=bbox).to_crs(3035).set_index("HYBAS_ID")
    rows = {}
    for station, (outlet, gauge_xy, physical_upstream) in PAIRINGS.items():
        record = outlets[outlet]
        if not record["in_reanalysis"]:
            raise ValueError(f"No Google reanalysis for {outlet}")
        basin_id = int(outlet.removeprefix("subhybas_"))
        outlet_xy = (record["longitude"], record["latitude"])
        gauge_point, outlet_point = gpd.GeoSeries(
            [Point(gauge_xy), Point(outlet_xy)], crs=4326
        ).to_crs(3035)
        gauge_reach = int(rivers.distance(gauge_point).idxmin())
        basin_reaches = rivers.loc[rivers.HYBAS_L12.eq(basin_id)]
        distances = basin_reaches.distance(outlet_point)
        # At a junction use the main upstream reach belonging to the outlet's basin.
        junction = basin_reaches.loc[distances.le(distances.min() + 1)]
        model_reach = int(junction.UPLAND_SKM.idxmax())
        first, last = (
            (gauge_reach, model_reach) if physical_upstream else (model_reach, gauge_reach)
        )
        path = trace(rivers, first, last)
        joins = rivers.loc[rivers.NEXT_DOWN.isin(path[1:]) & ~rivers.index.isin(path)]
        rows[station] = {
            "archive_outlet": outlet,
            "physical_wgs84_lon_lat": gauge_xy,
            "archive_wgs84_lon_lat": outlet_xy,
            "straight_line_distance_km": gauge_point.distance(outlet_point) / 1000,
            "modeled_upstream_area_km2": float(basins.loc[basin_id, "UP_AREA"]),
            "physical_nearest_hydrorivers_id": gauge_reach,
            "physical_nearest_hydrorivers_distance_m": rivers.loc[gauge_reach].geometry.distance(
                gauge_point
            ),
            "archive_hydrorivers_id": model_reach,
            "directed_hydrorivers_trace": path,
            "other_routed_reaches_joining_trace": [
                dict(
                    reach=int(i),
                    drains_to=int(r.NEXT_DOWN),
                    area_km2=float(r.UPLAND_SKM),
                    joins_at_google_outlet=bool(r.geometry.distance(outlet_point) < 1),
                )
                for i, r in joins.iterrows()
            ],
        }
    ref = gpd.read_file(CATCHMENT, where="gauge = '18.Q.45'").to_crs(3035).geometry.item()
    google = basins.loc[2121124850].geometry
    overlap = google.intersection(ref).area
    rows["Rimburg"]["fraction_of_reference_polygon_in_google_basin"] = overlap / ref.area
    rows["Rimburg"]["fraction_of_google_basin_in_reference_polygon"] = overlap / google.area
    return rows


def daily_comparison(google):
    series, mainstem, hashes = timing.load_inputs(include_venlo=True)
    events = timing.audit_events(series, mainstem).loc[lambda rows: rows.included]
    traces, peaks = [], []
    for event in events.itertuples(index=False):
        start = (event.anchor_utc - timing.WINDOW).ceil("D")
        stop = (event.anchor_utc + timing.WINDOW).floor("D")
        dates = pd.date_range(start, stop, inclusive="left")
        for gauge in (timing.MAIN, timing.VENLO):
            station = gauge.split(" · ", 1)[1]
            outlet = PAIRINGS[station][0]
            hours = timing.mainstem_hourly(series[gauge], event.anchor_utc)
            by_day = hours.resample("D", closed="right", label="left")
            measured = by_day.mean().where(by_day.count().eq(24))
            frame = pd.DataFrame(
                {
                    "observed_m3s": measured.reindex(dates),
                    "google_m3s": google[outlet].reindex(dates),
                }
            )
            traces.append(
                frame.rename_axis("day").reset_index().assign(event=event.event, station=station)
            )
            paired = frame.dropna()
            modeled = frame.google_m3s.dropna()
            google_peak = modeled.idxmax() if not modeled.empty else None
            peaks.append(
                {
                    "event": event.event,
                    "station": station,
                    "full_utc_days": len(dates),
                    "common_complete_days": len(paired),
                    "observed_max_day_on_common_days": (
                        paired.observed_m3s.idxmax() if not paired.empty else None
                    ),
                    "google_peak_day_on_common_days": (
                        paired.google_m3s.idxmax() if not paired.empty else None
                    ),
                    "observed_max_daily_mean_on_common_days_m3s": paired.observed_m3s.max(),
                    "google_max_daily_mean_on_common_days_m3s": paired.google_m3s.max(),
                    "google_max_day_in_window": google_peak,
                    "google_max_at_window_edge": google_peak in (dates[0], dates[-1]),
                }
            )
    return pd.concat(traces, ignore_index=True), pd.DataFrame(peaks), hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=timing.EXTENDED_OUT / "google_context")
    out = parser.parse_args().output
    rows = assess_outlets()
    days = pd.date_range("2024-10-09", "2024-11-22", tz="UTC")
    google = read_daily_flow(
        FLOW, CLOCK, [PAIRINGS[s][0] for s in ("Borgharen Dorp", "Venlo")], days
    )
    daily, peaks, source_hashes = daily_comparison(google)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "outlet_audit.json", rows)
    daily.to_csv(out / "daily_traces.csv", index=False)
    peaks.to_csv(out / "peak_day_comparison.csv", index=False)
    fig, axes = timing.plt.subplots(2, 2, figsize=(9, 5.5), layout="constrained", sharey=True)
    for ax, ((event, station), group) in zip(
        axes.flat, daily.groupby(["event", "station"]), strict=True
    ):
        for col, label, color in (
            ("observed_m3s", "RWS gauge", "#35383d"),
            ("google_m3s", "Google outlet", "#226a95"),
        ):
            ax.plot(
                group.day.dt.strftime("%d %b"), group[col], color=color, marker="o", label=label
            )
        ax.set(
            title=f"{station} · {pd.Timestamp(event):%d %b %Y} event", ylabel="Daily mean (m³/s)"
        )
        ax.grid(axis="y", alpha=0.2)
    axes[0, 0].legend(frameon=False)
    fig.supxlabel("Nominal UTC day of daily mean")
    fig.savefig(out / "meuse_daily_context.png", dpi=175)
    timing.plt.close(fig)
    write_json(
        out / "manifest.json",
        {
            "status": "completed",
            "release": VERSION,
            "usage": "Approximate river sections; contextual comparison over two fixed windows.",
            "input_sha256": {
                **source_hashes,
                **{
                    str(p): sha(p)
                    for p in (
                        RIVERS,
                        *[BASINS.with_suffix(s) for s in (".shp", ".dbf", ".shx", ".prj")],
                        CATCHMENT,
                        CATALOGUE,
                        FLOW,
                        FLOW.with_suffix(".manifest.json"),
                        CLOCK,
                        Path(__file__),
                        ROOT / "scripts/297_meuse_peak_timing.py",
                        ROOT / "src/grrr_reanalysis.py",
                    )
                },
            },
            "output_sha256": {
                name: sha(out / name)
                for name in (
                    "outlet_audit.json",
                    "daily_traces.csv",
                    "peak_day_comparison.csv",
                    "meuse_daily_context.png",
                )
            },
        },
    )
    print(peaks.to_string(index=False))


if __name__ == "__main__":
    main()
