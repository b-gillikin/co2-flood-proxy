"""Week 1 EDA/QC pass for IoT, weather, discharge, and soft labels."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import pandas as pd


INTERIM_DIR = Path("data/interim")
PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/eda")


def load_hourly(path):
    """Read a timestamp-indexed hourly CSV."""
    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    return frame.set_index("timestamp_utc").sort_index()


def build_joined_frame():
    """Join IoT, Kerkrade weather, discharge, and soft labels on the IoT window."""
    iot = load_hourly(INTERIM_DIR / "iot_hourly.csv")
    weather = load_hourly(INTERIM_DIR / "weather_hourly.csv")
    discharge = load_hourly(INTERIM_DIR / "discharge_hourly.csv")
    labels = load_hourly(PROCESSED_DIR / "hourly_soft_labels.csv")

    kerkrade_weather = weather[
        [column for column in weather.columns if column.startswith("kerkrade_")]
    ]

    joined = iot.join(kerkrade_weather, how="left")
    joined = joined.join(discharge, how="left")
    joined = joined.join(labels, how="left")
    return joined


def write_summary(joined):
    """Save compact per-column QC statistics."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary = joined.agg(["count", "mean", "min", "max"]).transpose()
    summary["missing_fraction"] = joined.isna().mean()
    target = PROCESSED_DIR / "week1_eda_summary.csv"
    summary.to_csv(target, index_label="column")
    print(f"wrote {target}")


def save_joined(joined):
    """Save the analysis-ready hourly frame for Week 2+ scripts."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    target = INTERIM_DIR / "analysis_hourly.csv"
    joined.to_csv(target, index_label="timestamp_utc")
    print(f"wrote {target} ({len(joined)} rows, {len(joined.columns)} columns)")


def plot_series(joined, columns, title, filename):
    """Plot available columns as aligned hourly panels."""
    available = [column for column in columns if column in joined.columns]
    if not available:
        return

    fig, axes = plt.subplots(
        len(available),
        1,
        figsize=(12, max(3, 2.4 * len(available))),
        sharex=True,
        constrained_layout=True,
    )
    if len(available) == 1:
        axes = [axes]

    for axis, column in zip(axes, available):
        axis.plot(joined.index, joined[column], linewidth=1)
        axis.set_ylabel(column)
        axis.grid(True, alpha=0.25)

    axes[0].set_title(title)
    axes[-1].set_xlabel("timestamp_utc")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    target = RESULTS_DIR / filename
    fig.savefig(target, dpi=160)
    plt.close(fig)
    print(f"wrote {target}")


def write_plots(joined):
    """Write the three Week 1 QC plots."""
    plot_series(
        joined,
        [
            "iot_co2_ppm",
            "iot_air_pressure_hpa",
            "kerkrade_weather_pressure_hpa",
            "iot_observation_count",
        ],
        "CO2, pressure, and IoT observation coverage",
        "co2_pressure_coverage.png",
    )
    plot_series(
        joined,
        [
            "iot_co2_ppm",
            "iot_temperature_c",
            "kerkrade_weather_temp_c",
            "iot_relative_humidity_pct",
            "kerkrade_weather_relative_humidity_pct",
        ],
        "CO2, temperature, and humidity",
        "co2_temperature_humidity.png",
    )
    plot_series(
        joined,
        [
            "iot_co2_ppm",
            "discharge_wurm_rimburg_m3s",
            "discharge_geul_hommerich_m3s",
            "discharge_geul_meerssen_m3s",
            "any_current_soft_label",
            "any_antecedent_72h_soft_label",
        ],
        "CO2, discharge, and soft labels",
        "co2_discharge_soft_labels.png",
    )


def print_overview(joined):
    """Print the headline QC facts that matter before modelling."""
    print(
        "analysis window:",
        joined.index.min(),
        "to",
        joined.index.max(),
        f"({len(joined)} hourly rows)",
    )
    print("empty IoT hours:", int((joined["iot_observation_count"] == 0).sum()))
    print("CO2 > 1000 ppm hours:", int((joined["iot_co2_ppm"] > 1000).sum()))
    if "any_current_level" in joined:
        print("current soft-label max level:", joined["any_current_level"].max())
    if "any_antecedent_72h_level" in joined:
        print("72h antecedent max level:", joined["any_antecedent_72h_level"].max())


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="write joined frame and summary only",
    )
    return parser.parse_args()


def main():
    """Command-line entry point."""
    args = parse_args()
    joined_frame = build_joined_frame()
    save_joined(joined_frame)
    write_summary(joined_frame)
    if not args.skip_plots:
        write_plots(joined_frame)
    print_overview(joined_frame)


if __name__ == "__main__":
    main()
