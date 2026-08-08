"""Re-evaluate Eryilmaz's same-site feature substitution on the held record.

Eryilmaz compared indoor IoT variables with public outdoor weather for predicting
hours above 1,000 ppm CO2.  This script repeats that comparison on the later
2025--2026 record.  It is a temporal re-evaluation, not an exact replication:
the observation window differs. Five expanding-window evaluations use contiguous
calendar blocks on the full hourly axis; complete cases are selected only after
the blocks are defined.

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
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

INPUT_PATH = Path("data/interim/analysis_hourly.csv")
OUTPUT_DIR = Path("results/eryilmaz")

CO2_THRESHOLD_PPM = 1000
N_SPLITS = 5

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
    full_start = frame.index.min()
    full_end = frame.index.max()
    frame["iot_delta_pressure_6h"] = observed_change(frame.iot_air_pressure_hpa, 6)
    frame["weather_delta_pressure_6h"] = observed_change(frame.kerkrade_weather_pressure_hpa, 6)
    required = [column for columns in FEATURES.values() for column in columns]
    frame = frame.dropna(subset=["iot_co2_ppm", *required]).copy()
    frame["high_co2"] = frame.iot_co2_ppm.gt(CO2_THRESHOLD_PPM).astype("int8")
    frame.attrs.update(full_start=full_start, full_end=full_end)
    return frame


def calendar_splits(frame):
    """Expanding training sets and contiguous tests on the full calendar axis."""
    start = frame.attrs.get("full_start", frame.index.min())
    end = frame.attrs.get("full_end", frame.index.max()) + pd.Timedelta(hours=1)
    boundaries = pd.date_range(start, end, periods=N_SPLITS + 2)
    for fold in range(1, N_SPLITS + 1):
        test_start, test_end = boundaries[fold], boundaries[fold + 1]
        train = frame.index < test_start
        test = (frame.index >= test_start) & (frame.index < test_end)
        yield fold, train, test, test_start, test_end


def hourly_grid(start, end):
    """Hourly timestamps inside a left-closed, right-open interval."""
    return pd.date_range(start.ceil("h"), (end - pd.Timedelta(nanoseconds=1)).floor("h"), freq="h")


def longest_missing_run(index, start, end):
    """Longest complete-case outage inside one planned hourly test block."""
    expected = hourly_grid(start, end)
    missing = ~expected.isin(index)
    if not missing.any():
        return 0
    groups = pd.Series(missing).ne(pd.Series(missing).shift(fill_value=False)).cumsum()
    return int(pd.Series(missing).groupby(groups).sum().max())


def fold_metrics(frame):
    rows = []
    for fold, train_mask, test_mask, test_start, test_end in calendar_splits(frame):
        train, test = frame.loc[train_mask], frame.loc[test_mask]
        status = "eligible"
        if test.empty:
            status = "no_complete_cases"
        elif train.high_co2.nunique() < 2 or test.high_co2.nunique() < 2:
            status = "single_class"
        calendar_hours = len(hourly_grid(test_start, test_end))
        for model_name, columns in FEATURES.items():
            auroc = float("nan")
            if status == "eligible":
                model = make_pipeline(
                    StandardScaler(),
                    LogisticRegression(max_iter=500, solver="lbfgs"),
                )
                model.fit(train[columns], train.high_co2)
                scores = model.predict_proba(test[columns])[:, 1]
                auroc = roc_auc_score(test.high_co2, scores)
            rows.append(
                {
                    "fold": fold,
                    "model": model_name,
                    "fold_status": status,
                    "n_train_hours": len(train),
                    "n_test_hours": len(test),
                    "n_positive_hours": int(test.high_co2.sum()),
                    "test_start": test_start,
                    "test_end_exclusive": test_end,
                    "first_complete_case": test.index.min() if len(test) else pd.NaT,
                    "last_complete_case": test.index.max() if len(test) else pd.NaT,
                    "complete_case_coverage": len(test) / calendar_hours if calendar_hours else 0,
                    "longest_complete_case_outage_hours": longest_missing_run(
                        test.index, test_start, test_end
                    ),
                    "auroc": auroc,
                }
            )
    return rows


def paired_comparison(metrics):
    keys = ["fold"]
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
        "This is not an exact replication: it uses a later sensor record and imposes "
        "calendar-forward evaluation because the paper does not document its fold structure."
    )
    lines.extend(["", "## Calendar-forward folds", ""])
    diagnostics = metrics.drop_duplicates("fold").set_index("fold")
    scores = comparison.set_index("fold")
    for fold, row in diagnostics.iterrows():
        line = (
            f"- Fold {fold}: {row.test_start:%Y-%m-%d} to "
            f"{row.test_end_exclusive:%Y-%m-%d}; {row.n_test_hours:,} complete hours "
            f"({row.complete_case_coverage:.1%}), {row.n_positive_hours} positives, "
            f"longest outage {row.longest_complete_case_outage_hours} h; "
            f"status `{row.fold_status}`"
        )
        score = scores.loc[fold]
        if pd.notna(score.indoor_iot) and pd.notna(score.public_weather):
            line += (
                f"; AUROC indoor {score.indoor_iot:.3f}, public {score.public_weather:.3f}, "
                f"gap {score.gap_indoor_minus_public:+.3f}"
            )
        lines.append(line + ".")
        lines.append("")
    lines.append(
        "No mean is reported: folds differ materially in calendar coverage and positive count. "
        "This later-record check is descriptive predecessor context, not chapter evidence."
    )
    (OUTPUT_DIR / "summary.md").write_text("\n".join(lines) + "\n")


def plot_folds(comparison):
    fig, axis = plt.subplots(figsize=(5, 4))
    for row in comparison.dropna(subset=["indoor_iot", "public_weather"]).itertuples(index=False):
        axis.plot(
            ["Indoor IoT", "Public weather"],
            [row.indoor_iot, row.public_weather],
            marker="o",
            alpha=0.7,
            label=f"fold {row.fold}",
        )
    axis.set_title("Calendar-forward folds")
    axis.set_ylim(0.5, 1.0)
    axis.set_ylabel("AUROC within test fold")
    axis.grid(axis="y", alpha=0.25)
    if axis.lines:
        axis.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fold_auroc.png", dpi=180)
    plt.close(fig)


def main():
    frame = analysis_frame()
    metrics = pd.DataFrame(fold_metrics(frame))
    comparison = paired_comparison(metrics)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(OUTPUT_DIR / "fold_metrics.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / "paired_comparison.csv", index=False)
    write_summary(frame, metrics, comparison)
    plot_folds(comparison)
    print((OUTPUT_DIR / "summary.md").read_text())


if __name__ == "__main__":
    main()
