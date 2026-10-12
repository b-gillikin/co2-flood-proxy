"""Check matched rainfall support and render selected Limburg hydrographs.

This diagnostic adds no new model, variable, or exclusion. Its block bootstrap
quantifies uncertainty in descriptive case-minus-matched-hour differences.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.event_study import assign_eras, era_thresholds  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "real_study", ROOT / "scripts/47_run_real_event_study.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)

OUT = ROOT / "results/event_study/real_data_v1"
SEED = 20260929
REPLICATES = 999
WINDOWS = ["rain_1_24_mm", "rain_25_72_mm"]


def overlap(cases: pd.DataFrame, controls: pd.DataFrame) -> pd.DataFrame:
    """Case rain relative to the observed range of its own matched controls."""
    result = cases.copy()
    by_stratum = controls.groupby("stratum")
    for window in WINDOWS:
        maximum = by_stratum[window].max()
        p90 = by_stratum[window].quantile(0.9)
        result[f"above_control_max_{window}"] = result[window] > result.stratum.map(maximum)
        result[f"above_control_p90_{window}"] = result[window] > result.stratum.map(p90)
    return result


def block_interval(cases: pd.DataFrame, blocks: np.ndarray) -> pd.DataFrame:
    """Joint year-month bootstrap of paired median differences, by season."""
    rng = np.random.default_rng(SEED)
    block_index = {int(block): i for i, block in enumerate(blocks)}
    samples = rng.integers(0, len(blocks), size=(REPLICATES, len(blocks)))
    counts = np.asarray([np.bincount(sample, minlength=len(blocks)) for sample in samples])
    rows = []
    for season, warm in [("cold", False), ("warm", True)]:
        subset = cases.loc[cases.warm.eq(warm)]
        subset_blocks = np.array([block_index[int(block)] for block in subset.block])
        for window in WINDOWS:
            column = f"case_minus_control_{window}"
            values = subset[column].to_numpy()
            observed = float(np.median(values))
            draws = []
            for count in counts:
                pooled = np.repeat(values, count[subset_blocks])
                draws.append(float(np.median(pooled)) if len(pooled) else np.nan)
            valid = np.asarray(draws)[np.isfinite(draws)]
            rows.append(
                {
                    "season": season,
                    "window": window,
                    "onsets": len(subset),
                    "paired_median_mm": observed,
                    "bootstrap_lower_95_mm": float(np.quantile(valid, 0.025)),
                    "bootstrap_upper_95_mm": float(np.quantile(valid, 0.975)),
                    "successful_draws": len(valid),
                }
            )
    return pd.DataFrame(rows)


def plot_overlap(frame: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    colors = {"warm": "tab:red", "cold": "tab:blue"}
    for ax, window, title in zip(
        axes,
        WINDOWS,
        ["Rainfall in lags 1–24 h", "Rainfall in lags 25–72 h"],
        strict=True,
    ):
        for season, warm in [("cold", False), ("warm", True)]:
            for onset, linestyle, label in [
                (1, "-", "onset"),
                (0, "--", "matched hour"),
            ]:
                values = np.sort(
                    frame.loc[frame.warm.eq(warm) & frame.onset.eq(onset), window].to_numpy()
                )
                ax.step(
                    values,
                    np.arange(1, len(values) + 1) / len(values),
                    where="post",
                    color=colors[season],
                    linestyle=linestyle,
                    label=f"{season} {label}",
                )
        ax.set_title(title)
        ax.set_xlabel("Catchment rainfall (mm)")
        ax.set_ylabel("Empirical cumulative fraction")
        ax.grid(alpha=0.2)
    axes[0].legend(fontsize=8)
    fig.suptitle("Observed histories in informative matched strata; descriptive")
    fig.tight_layout()
    fig.savefig(OUT / "figure_6_observed_rainfall_overlap.png", dpi=180)
    plt.close(fig)


def plot_selected_hydrographs() -> None:
    selected = [
        ("Geul", "2010-02-04 17:00:00+00:00"),
        ("Geleenbeek", "2021-07-04 19:00:00+00:00"),
        ("Geleenbeek", "2021-07-13 19:00:00+00:00"),
        ("Gulp", "2021-07-13 17:00:00+00:00"),
    ]
    discharge = study.review_module.read_hourly(study.FILES["discharge"])
    rainfall = study.review_module.read_hourly(study.FILES["rainfall"])
    gauges = pd.read_csv(study.FILES["gauges"]).set_index("watercourse")
    eras = pd.read_csv(study.FILES["rating_eras"])
    fig, axes = plt.subplots(4, 1, figsize=(11, 11))
    for ax, (site, timestamp) in zip(axes, selected, strict=True):
        onset = pd.Timestamp(timestamp)
        start = onset - pd.Timedelta(hours=72)
        end = onset + pd.Timedelta(hours=24)
        gauge = gauges.loc[site, "gauge"]
        q = discharge[gauge].loc[start:end]
        era_table = eras.loc[eras.gauge.eq(gauge)]
        labels = assign_eras(q.index, era_table)
        _, p99 = era_thresholds(discharge[gauge], assign_eras(discharge.index, era_table))
        ratio = (q / p99.loc[q.index]).copy()
        domain = era_table.drop_duplicates("era_id").set_index("era_id").domain_max_m3s
        ratio = ratio.where(q <= labels.map(domain))
        if site == "Gulp":
            ratio = ratio.where(q <= 3.0)
        ax.plot(q.index, ratio, color="tab:blue", label="discharge / era p99")
        ax.axhline(1, color="black", linestyle="--", linewidth=0.8)
        ax.axvline(onset, color="tab:red", linewidth=1, label="onset")
        ax.set_ylabel("Q / p99")
        ax.set_title(f"{site} — {onset:%Y-%m-%d %H:%M} UTC")
        twin = ax.twinx()
        twin.bar(
            rainfall.loc[start:end].index,
            rainfall.loc[start:end, site],
            width=0.035,
            color="tab:cyan",
            alpha=0.35,
            label="rainfall",
        )
        twin.set_ylabel("Rain (mm/h)")
    fig.suptitle("Selected onsets: 72 h before and 24 h after; out-of-domain flow masked")
    fig.tight_layout()
    fig.savefig(OUT / "figure_7_selected_onset_hydrographs.png", dpi=180)
    plt.close(fig)


def main() -> None:
    frame = pd.read_csv(OUT / "observed_rainfall_windows_matched_rows.csv")
    cases = pd.read_csv(OUT / "observed_rainfall_windows_onsets.csv")
    controls = frame.loc[frame.onset.eq(0)]
    supported = overlap(cases, controls)
    columns = [
        "timestamp_utc",
        "watercourse",
        "warm",
        "stratum",
        "block",
        *WINDOWS,
        *[f"above_control_max_{window}" for window in WINDOWS],
        *[f"above_control_p90_{window}" for window in WINDOWS],
    ]
    supported[columns].to_csv(OUT / "observed_window_case_support.csv", index=False)
    records = []
    for warm, group in supported.groupby("warm"):
        for window in WINDOWS:
            records.append(
                {
                    "season": "warm" if warm else "cold",
                    "window": window,
                    "onsets": len(group),
                    "case_above_all_controls": int(group[f"above_control_max_{window}"].sum()),
                    "fraction_above_all_controls": float(
                        group[f"above_control_max_{window}"].mean()
                    ),
                    "fraction_above_control_p90": float(
                        group[f"above_control_p90_{window}"].mean()
                    ),
                }
            )
    summary = pd.DataFrame(records)
    summary.to_csv(OUT / "observed_window_support_summary.csv", index=False)
    all_blocks = pd.read_csv(OUT / "observed_window_all_blocks.csv").block.to_numpy()
    intervals = block_interval(cases, all_blocks)
    intervals.to_csv(OUT / "observed_window_paired_bootstrap.csv", index=False)
    plot_overlap(frame)
    plot_selected_hydrographs()
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(intervals.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
