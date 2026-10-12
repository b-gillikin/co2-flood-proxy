"""Render the five protocol figures from the completed Limburg analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.event_study import assign_eras, era_thresholds  # noqa: E402

OUT = ROOT / "results/event_study/real_data_v1"


def read_hourly(path):
    table = pd.read_csv(path)
    table.index = pd.to_datetime(table.pop("timestamp_utc"), utc=True)
    return table


def finish(figure, name):
    figure.tight_layout()
    figure.savefig(OUT / name, dpi=170)
    plt.close(figure)


def network_map(gauges):
    catchments = gpd.read_file(ROOT / "data/interim/event_study_catchments.gpkg")
    features = json.loads(catchments.to_crs(4326).to_json())["features"]
    figure, ax = plt.subplots(figsize=(8, 7))
    colors = plt.cm.Set2(np.linspace(0, 1, len(features)))
    for feature, color in zip(features, colors, strict=True):
        geometry = feature["geometry"]
        polygons = (
            [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        )
        for polygon in polygons:
            exterior = np.asarray(polygon[0])
            ax.add_patch(Polygon(exterior, facecolor=color, edgecolor="0.35", alpha=0.6))
    for row in gauges.itertuples(index=False):
        ax.scatter(row.longitude, row.latitude, color="black", s=20)
        ax.annotate(
            row.watercourse,
            (row.longitude, row.latitude),
            xytext=(3, 3),
            textcoords="offset points",
            fontsize=8,
        )
    ax.autoscale()
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Six representative tributary gauges and cross-border catchments")
    finish(figure, "figure_1_network.png")


def july_trajectory(discharge, rain, gauges, eras):
    start, end = pd.Timestamp("2021-07-13", tz="UTC"), pd.Timestamp("2021-07-16", tz="UTC")
    index = discharge.loc[start:end].index
    figure, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for gauge in gauges.itertuples(index=False):
        series = discharge[gauge.gauge]
        table = eras.loc[eras.gauge.eq(gauge.gauge)]
        labels = assign_eras(series.index, table)
        _, threshold = era_thresholds(series, labels)
        ratio = (series / threshold).loc[index]
        if gauge.watercourse == "Gulp":
            ratio = ratio.where(series.loc[index] <= 3.0)
        if gauge.watercourse in {"Geul", "Worm"}:
            domain = table.drop_duplicates("era_id").set_index("era_id").domain_max_m3s
            bound = labels.loc[index].map(domain)
            ratio = ratio.where(series.loc[index] <= bound)
        axes[0].plot(index, ratio, label=gauge.watercourse)
    axes[0].axhline(1, color="black", linestyle="--", linewidth=0.8)
    axes[0].set_ylabel("Recorded discharge / era p99")
    axes[0].set_title("July 2021: observed trajectories (uncertain high-flow portions omitted)")
    axes[0].legend(ncol=3, fontsize=8)
    axes[1].plot(index, rain.loc[index, gauges.watercourse].mean(axis=1), color="tab:blue")
    axes[1].set_ylabel("Mean catchment rain (mm/h)")
    axes[1].set_xlabel("UTC")
    finish(figure, "figure_2_july_2021.png")


def lag_curves():
    data = pd.read_csv(OUT / "crossbasis_estimates.csv")
    data = data.loc[data.model.eq("primary")]
    figure, ax = plt.subplots(figsize=(9, 5))
    for signal, color in [("warm_rain", "tab:red"), ("cold_rain", "tab:blue")]:
        subset = data.loc[data.signal.eq(signal)].sort_values("lag_hour")
        ax.plot(subset.lag_hour, subset.log_rr_per_unit, color=color, label=signal)
        ax.fill_between(
            subset.lag_hour.to_numpy(),
            subset.lower.to_numpy(),
            subset.upper.to_numpy(),
            color=color,
            alpha=0.18,
        )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Hours before onset")
    ax.set_ylabel("Log rate ratio per 1 mm/h rainfall at that lag")
    ax.set_title("Seasonal distributed-lag rainfall associations")
    ax.legend()
    finish(figure, "figure_3_seasonal_lags.png")


def forest(gauges):
    table = pd.read_csv(OUT / "watercourse_estimates.csv")
    table = table.loc[table.metric.eq("rain_cumulative_log_rr")].copy()
    table["watercourse"] = table.model.str.removeprefix("S3_")
    table = table.set_index("watercourse").reindex(gauges.watercourse)
    figure, ax = plt.subplots(figsize=(8, 5))
    y = np.arange(len(table))
    ax.errorbar(
        table.estimate,
        y,
        xerr=np.vstack([table.estimate - table.lower, table.upper - table.estimate]),
        fmt="o",
        capsize=3,
    )
    ax.axvline(0, color="black", linestyle="--", linewidth=0.8)
    ax.set_yticks(y, table.index)
    ax.invert_yaxis()
    ax.set_xlabel("Cumulative log association at fixed rainfall contrast")
    ax.set_title("Watercourse heterogeneity; joint storms limit independent-site inference")
    finish(figure, "figure_4_watercourse_forest.png")


def network_state(discharge, gauges, eras, events):
    percentile = pd.DataFrame(index=discharge.index)
    for gauge in gauges.itertuples(index=False):
        series = discharge[gauge.gauge]
        labels = assign_eras(series.index, eras.loc[eras.gauge.eq(gauge.gauge)])
        percentile[gauge.watercourse] = series.groupby(labels).rank(pct=True)
    offsets = np.arange(-48, 49)
    trajectories = []
    for event in events.itertuples(index=False):
        if event.review_decision != "include_exact":
            continue
        times = pd.Timestamp(event.onset_utc) + pd.to_timedelta(offsets, unit="h")
        other = percentile.drop(columns=event.watercourse).reindex(times)
        trajectories.append(other.median(axis=1, skipna=True).to_numpy())
    values = np.array(trajectories)
    figure, ax = plt.subplots(figsize=(9, 5))
    ax.plot(offsets, np.nanmedian(values, axis=0), color="tab:purple")
    ax.fill_between(
        offsets,
        np.nanquantile(values, 0.25, axis=0),
        np.nanquantile(values, 0.75, axis=0),
        alpha=0.2,
        color="tab:purple",
    )
    ax.axvline(0, color="black", linestyle="--", linewidth=0.8)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Hours relative to receiver onset")
    ax.set_ylabel("Median within-era percentile of other gauges")
    ax.set_title("Other-gauge network state around observed onsets (descriptive)")
    finish(figure, "figure_5_network_state.png")


def main():
    gauges = pd.read_csv(ROOT / "data/interim/event_study_gauges.csv")
    gauges = gauges.loc[gauges.include_primary & gauges.natural_tributary]
    eras = pd.read_csv(ROOT / "data/interim/event_study_rating_eras.csv")
    discharge = read_hourly(ROOT / "data/interim/event_study_discharge_hourly.csv")
    rain = read_hourly(ROOT / "data/interim/radolan_catchment_hourly.csv")
    events = pd.read_csv(OUT / "events.csv")
    network_map(gauges)
    july_trajectory(discharge, rain, gauges, eras)
    lag_curves()
    forest(gauges)
    network_state(discharge, gauges, eras, events)
    print("Rendered five protocol figures")


if __name__ == "__main__":
    main()
