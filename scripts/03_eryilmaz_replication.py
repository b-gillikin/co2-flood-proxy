"""Re-evaluate Eryilmaz's same-site feature substitution on the held record.

Eryilmaz compared indoor IoT variables with public outdoor weather for predicting
hours above 1,000 ppm CO2.  This script repeats that comparison on the later
2025--2026 record.  It is a temporal re-evaluation, not an exact replication:
the observation window differs, and the paper does not specify shuffled folds.

AUROC is computed inside each fold. Probabilities from separately fitted folds
are never pooled into one ranking.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

INPUT_PATH = Path("data/interim/analysis_hourly.csv")
OUTPUT_DIR = Path("results/eryilmaz")

CO2_THRESHOLD_PPM = 1000
N_SPLITS = 5
RANDOM_STATE = 42

FEATURES = {
    "indoor_iot": [
        "iot_temperature_c",
        "iot_relative_humidity_pct",
        "iot_air_pressure_hpa",
        "iot_delta_pressure_6h",
    ],
    "public_weather": [
        "kerkrade_weather_temp_c",
        "kerkrade_weather_relative_humidity_pct",
        "kerkrade_weather_pressure_hpa",
        "weather_delta_pressure_6h",
    ],
}


def observed_change(series, hours):
    """Difference an hourly series without treating a coverage gap as elapsed data."""
    elapsed = series.index.to_series().diff(hours)
    complete_span = elapsed.eq(pd.Timedelta(hours=hours)).to_numpy()
    return series.diff(hours).where(complete_span)


def analysis_frame():
    frame = pd.read_csv(INPUT_PATH, parse_dates=["timestamp_utc"]).set_index("timestamp_utc")
    frame["iot_delta_pressure_6h"] = observed_change(frame.iot_air_pressure_hpa, 6)
    frame["weather_delta_pressure_6h"] = observed_change(frame.kerkrade_weather_pressure_hpa, 6)
    required = [column for columns in FEATURES.values() for column in columns]
    frame = frame.dropna(subset=["iot_co2_ppm", *required]).copy()
    frame["high_co2"] = frame.iot_co2_ppm.gt(CO2_THRESHOLD_PPM).astype("int8")
    return frame


def splits(frame, scheme):
    if scheme == "random_five_fold":
        cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
        return cv.split(frame, frame.high_co2)
    return TimeSeriesSplit(n_splits=N_SPLITS).split(frame)


def fold_metrics(frame, scheme):
    rows = []
    for fold, (train_index, test_index) in enumerate(splits(frame, scheme), start=1):
        train, test = frame.iloc[train_index], frame.iloc[test_index]
        if train.high_co2.nunique() < 2 or test.high_co2.nunique() < 2:
            continue
        for model_name, columns in FEATURES.items():
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=500, solver="lbfgs"),
            )
            model.fit(train[columns], train.high_co2)
            scores = model.predict_proba(test[columns])[:, 1]
            rows.append(
                {
                    "scheme": scheme,
                    "fold": fold,
                    "model": model_name,
                    "n_test_hours": len(test),
                    "n_positive_hours": int(test.high_co2.sum()),
                    "test_start": test.index.min(),
                    "test_end": test.index.max(),
                    "auroc": roc_auc_score(test.high_co2, scores),
                }
            )
    return rows


def paired_comparison(metrics):
    keys = ["scheme", "fold"]
    wide = metrics.pivot(index=keys, columns="model", values="auroc").reset_index()
    wide["gap_indoor_minus_public"] = wide.indoor_iot - wide.public_weather
    return wide


def write_summary(frame, metrics, comparison):
    lines = ["# Eryilmaz temporal re-evaluation", ""]
    lines.append(
        f"Target: hourly indoor CO2 > {CO2_THRESHOLD_PPM} ppm; "
        f"{len(frame):,} complete-case hours, {int(frame.high_co2.sum()):,} positive hours."
    )
    lines.append(
        "This is not an exact replication: it uses a later sensor record, and random shuffling "
        "is a project specification rather than a documented detail of the paper."
    )
    lines.append("")
    for scheme, group in comparison.groupby("scheme"):
        lines.append(f"## {scheme}")
        lines.append("")
        model_means = metrics[metrics.scheme.eq(scheme)].groupby("model").auroc.mean()
        gaps = group.gap_indoor_minus_public
        lines.append(
            f"Mean within-fold AUROC: indoor {model_means.indoor_iot:.3f}; "
            f"public weather {model_means.public_weather:.3f}; mean paired gap {gaps.mean():+.3f}."
        )
        lines.append(
            f"Fold gaps (indoor - public): {', '.join(f'{value:+.3f}' for value in gaps)}."
        )
        lines.append("")
    lines.append(
        "The schemes use different test periods and training sizes; their absolute AUROCs are "
        "not a numerical estimate of a leakage penalty."
    )
    (OUTPUT_DIR / "summary.md").write_text("\n".join(lines) + "\n")


def plot_folds(comparison):
    schemes = list(comparison.scheme.unique())
    fig, axes = plt.subplots(1, len(schemes), figsize=(9, 4), sharey=True)
    if len(schemes) == 1:
        axes = [axes]
    for axis, scheme in zip(axes, schemes, strict=True):
        data = comparison[comparison.scheme.eq(scheme)]
        for row in data.itertuples(index=False):
            axis.plot(
                ["Indoor IoT", "Public weather"],
                [row.indoor_iot, row.public_weather],
                marker="o",
                alpha=0.7,
            )
        axis.set_title(scheme.replace("_", " "))
        axis.set_ylim(0.5, 1.0)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("AUROC within test fold")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fold_auroc.png", dpi=180)
    plt.close(fig)


def main():
    frame = analysis_frame()
    rows = []
    for scheme in ("random_five_fold", "forward_chaining"):
        rows.extend(fold_metrics(frame, scheme))
    metrics = pd.DataFrame(rows)
    comparison = paired_comparison(metrics)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(OUTPUT_DIR / "fold_metrics.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / "paired_comparison.csv", index=False)
    write_summary(frame, metrics, comparison)
    plot_folds(comparison)
    print((OUTPUT_DIR / "summary.md").read_text())


if __name__ == "__main__":
    main()
