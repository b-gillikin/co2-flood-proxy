"""July Week 3 cross-detector anomaly agreement."""

from __future__ import annotations

import os
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import cohen_kappa_score


PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/ensemble")

SARIMAX_PATH = PROCESSED_DIR / "sarimax-anomalies.csv"
KALMAN_PATH = PROCESSED_DIR / "kalman-anomalies.csv"
IFOREST_PATH = PROCESSED_DIR / "iforest-anomalies.csv"
ANALYSIS_PATH = Path("data/interim/analysis_hourly.csv")

FLAGS_PATH = PROCESSED_DIR / "ensemble_anomaly_flags.csv"
PAIRWISE_PATH = RESULTS_DIR / "pairwise_agreement.csv"
SUMMARY_PATH = RESULTS_DIR / "agreement_summary.csv"

DETECTORS = {
    "sarimax": (SARIMAX_PATH, "sarimax_anomaly"),
    "kalman": (KALMAN_PATH, "kalman_anomaly"),
    "iforest": (IFOREST_PATH, "iforest_anomaly"),
}


def read_detector(name, path, column):
    """Read one detector's official anomaly flag."""
    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    return frame[["timestamp_utc", column]].rename(columns={column: f"{name}_anomaly"})


def jaccard(a, b):
    """Binary Jaccard agreement for anomaly flags."""
    a = pd.Series(a).astype(bool)
    b = pd.Series(b).astype(bool)
    union = (a | b).sum()
    if union == 0:
        return 1.0
    return float((a & b).sum() / union)


def agreement_tables(flags):
    """Compute count and pairwise detector agreement tables."""
    detector_cols = [f"{name}_anomaly" for name in DETECTORS]
    summary = (
        flags["detector_count"]
        .value_counts()
        .rename_axis("detectors_firing")
        .reset_index(name="n_hours")
        .sort_values("detectors_firing")
    )
    summary["share_hours"] = summary["n_hours"] / len(flags)

    rows = []
    for left, right in combinations(detector_cols, 2):
        rows.append(
            {
                "detector_a": left.removesuffix("_anomaly"),
                "detector_b": right.removesuffix("_anomaly"),
                "jaccard": jaccard(flags[left], flags[right]),
                "cohen_kappa": cohen_kappa_score(flags[left], flags[right]),
                "both_anomaly_hours": int((flags[left] & flags[right]).sum()),
            }
        )
    return summary, pd.DataFrame(rows)


def write_plot(flags):
    """Plot CO2 with all-three agreement windows highlighted."""
    analysis = pd.read_csv(ANALYSIS_PATH, parse_dates=["timestamp_utc"])
    plot = analysis[["timestamp_utc", "iot_co2_ppm"]].merge(
        flags[["timestamp_utc", "all_three_anomaly", "detector_count"]],
        on="timestamp_utc",
        how="inner",
    )

    fig, axis = plt.subplots(figsize=(12, 5), constrained_layout=True)
    axis.plot(plot["timestamp_utc"], plot["iot_co2_ppm"], linewidth=1, label="CO2")
    axis.scatter(
        plot.loc[plot["all_three_anomaly"], "timestamp_utc"],
        plot.loc[plot["all_three_anomaly"], "iot_co2_ppm"],
        color="tab:red",
        s=30,
        label="All three detectors",
    )
    axis.set_ylabel("CO2 ppm")
    axis.set_title("Cross-detector anomaly agreement")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="upper right")
    fig.savefig(RESULTS_DIR / "all_three_agreement.png", dpi=160)
    plt.close(fig)


def main():
    """Command-line entry point."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    frames = [
        read_detector(name, path, column)
        for name, (path, column) in DETECTORS.items()
    ]
    flags = frames[0]
    for frame in frames[1:]:
        flags = flags.merge(frame, on="timestamp_utc", how="inner")

    detector_cols = [f"{name}_anomaly" for name in DETECTORS]
    for column in detector_cols:
        flags[column] = flags[column].astype(bool)
    flags["detector_count"] = flags[detector_cols].sum(axis=1)
    flags["all_three_anomaly"] = flags["detector_count"] == 3

    summary, pairwise = agreement_tables(flags)
    flags.to_csv(FLAGS_PATH, index=False)
    summary.to_csv(SUMMARY_PATH, index=False)
    pairwise.to_csv(PAIRWISE_PATH, index=False)
    write_plot(flags)

    print(f"wrote {FLAGS_PATH} ({len(flags)} rows)")
    print(f"wrote {SUMMARY_PATH}")
    print(f"wrote {PAIRWISE_PATH}")
    print(f"all-three anomaly hours: {int(flags['all_three_anomaly'].sum())}")


if __name__ == "__main__":
    main()
