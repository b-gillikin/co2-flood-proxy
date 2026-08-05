"""August v1 transfer dry run for South Limburg RIVM sites.

This is deliberately a dry run, not an interpreted transfer result. It trains
simple surrogate classifiers from Kerkrade detector flags, applies them to the
currently cached RIVM/KNMI lane when enough aligned hours exist, and writes
availability tables so missing transfer features stay visible.
"""

from __future__ import annotations

import argparse
import os
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.features import pressure_deltas

PROCESSED_DIR = Path("data/processed")
INTERIM_DIR = Path("data/interim")
RESULTS_DIR = Path("results/transfer")
MODELS_DIR = Path("results/models")
TRANSFER_OUT_DIR = PROCESSED_DIR / "transfer-anomalies"
FIGURE_DIR = Path("results/figures")

SIGNAL_PATH = PROCESSED_DIR / "signal_characterization_frame.csv"
FLAGS_PATH = PROCESSED_DIR / "ensemble_anomaly_flags.csv"
RIVM_PATH = INTERIM_DIR / "rivm_hourly.csv"
KNMI_PATH = INTERIM_DIR / "knmi_hourly.csv"
SOFT_LABELS_PATH = PROCESSED_DIR / "hourly_soft_labels.csv"

SARIMAX_RESIDUALS_PATH = PROCESSED_DIR / "sarimax-residuals.csv"
KALMAN_INNOVATIONS_PATH = PROCESSED_DIR / "kalman-innovations.csv"
IFOREST_SCORES_PATH = PROCESSED_DIR / "iforest-scores.csv"

MIN_TRANSFER_HOURS = 24
FALLBACK_POSITIVE_SHARE = 0.05
KNMI_STATION = "06380"

TRANSFER_SITES = {
    "heerlen_looierstraat_nl10136": {
        "no2_ugm3": "rivm_nl10136_no2_ugm3",
        "pm10_ugm3": "rivm_nl10136_pm10_ugm3",
    },
    "heerlen_jamboreepad_nl10138": {
        "no2_ugm3": "rivm_nl10138_no2_ugm3",
        "o3_ugm3": "rivm_nl10138_o3_ugm3",
        "pm10_ugm3": "rivm_nl10138_pm10_ugm3",
    },
}

BASE_SCHEMA = [
    "temperature_c",
    "relative_humidity_pct",
    "pressure_hpa",
    "precip_mm",
    "pm10_ugm3",
    "pm2_5_ugm3",
    "no2_ugm3",
    "o3_ugm3",
]
PRESSURE_LAGS = (1, 3, 6, 12, 24)
TRANSFER_SCHEMA = [*BASE_SCHEMA, *[f"delta_pressure_{lag}h" for lag in PRESSURE_LAGS]]
DETECTORS = ("sarimax", "kalman", "iforest")


def read_timestamped(path: Path) -> pd.DataFrame:
    """Read a CSV and normalize its hourly UTC timestamp column."""
    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    return frame.sort_values("timestamp_utc").reset_index(drop=True)


def first_available(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    """Return the first available source column from a priority list."""
    for column in columns:
        if column in frame.columns:
            return frame[column]
    return pd.Series(np.nan, index=frame.index)


def add_pressure_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add pressure tendency columns to the normalized transfer schema."""
    if "pressure_hpa" not in frame.columns:
        frame["pressure_hpa"] = np.nan
    return pressure_deltas(frame, lags=PRESSURE_LAGS, pressure_col="pressure_hpa")


def kerkrade_feature_frame() -> pd.DataFrame:
    """Map the Kerkrade signal frame into the shared transfer feature schema."""
    signal = read_timestamped(SIGNAL_PATH)
    out = pd.DataFrame({"timestamp_utc": signal["timestamp_utc"]})
    out["temperature_c"] = first_available(
        signal,
        ["kerkrade_weather_temp_c", "iot_temperature_c"],
    )
    out["relative_humidity_pct"] = first_available(
        signal,
        ["kerkrade_weather_relative_humidity_pct", "iot_relative_humidity_pct"],
    )
    out["pressure_hpa"] = first_available(
        signal,
        ["iot_air_pressure_hpa", "kerkrade_weather_pressure_hpa"],
    )
    out["precip_mm"] = first_available(signal, ["kerkrade_weather_precip_mm"])
    out["pm10_ugm3"] = first_available(signal, ["kerkrade_weather_pm10_ugm3", "iot_pm10_ugm3"])
    out["pm2_5_ugm3"] = first_available(
        signal,
        ["kerkrade_weather_pm2_5_ugm3", "iot_pm2_5_ugm3"],
    )
    out["no2_ugm3"] = first_available(signal, ["kerkrade_weather_no2_ugm3"])
    out["o3_ugm3"] = first_available(signal, ["kerkrade_weather_o3_ugm3"])
    return add_pressure_features(out)


def load_knmi_station() -> pd.DataFrame:
    """Load station 06380 reference meteorology for transfer-site scoring."""
    if not KNMI_PATH.exists():
        return pd.DataFrame(
            columns=[
                "timestamp_utc",
                "temperature_c",
                "relative_humidity_pct",
                "pressure_hpa",
                "precip_mm",
            ]
        )

    knmi = read_timestamped(KNMI_PATH)
    station = knmi["knmi_station"].astype(str).str.zfill(5)
    knmi = knmi.loc[station == KNMI_STATION].copy()
    return knmi.rename(
        columns={
            "knmi_temperature_c": "temperature_c",
            "knmi_relative_humidity_pct": "relative_humidity_pct",
            "knmi_pressure_hpa": "pressure_hpa",
            "knmi_precip_mm": "precip_mm",
        }
    )[
        [
            "timestamp_utc",
            "temperature_c",
            "relative_humidity_pct",
            "pressure_hpa",
            "precip_mm",
        ]
    ]


def transfer_feature_frames() -> dict[str, pd.DataFrame]:
    """Build one normalized transfer feature frame per cached RIVM site."""
    rivm = read_timestamped(RIVM_PATH)
    knmi = load_knmi_station()
    frames: dict[str, pd.DataFrame] = {}

    for site_id, pollutant_map in TRANSFER_SITES.items():
        site = rivm[["timestamp_utc"]].copy()
        for feature in BASE_SCHEMA:
            site[feature] = np.nan
        for feature, source_column in pollutant_map.items():
            if source_column in rivm.columns:
                site[feature] = rivm[source_column]

        site = site.merge(knmi, on="timestamp_utc", how="left", suffixes=("", "_knmi"))
        for feature in ("temperature_c", "relative_humidity_pct", "pressure_hpa", "precip_mm"):
            knmi_column = f"{feature}_knmi"
            if knmi_column in site.columns:
                site[feature] = site[knmi_column]
                site = site.drop(columns=[knmi_column])

        site["site_id"] = site_id
        frames[site_id] = add_pressure_features(site)

    return frames


def feature_availability(
    train_features: pd.DataFrame,
    transfer_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Count non-missing rows for every schema feature at each site."""
    rows = []
    all_frames = {"kerkrade_training": train_features, **transfer_frames}
    for site_id, frame in all_frames.items():
        for feature in TRANSFER_SCHEMA:
            if feature in frame.columns:
                n_non_missing = int(frame[feature].notna().sum())
            else:
                n_non_missing = 0
            rows.append(
                {
                    "site_id": site_id,
                    "feature": feature,
                    "n_rows": len(frame),
                    "n_non_missing": n_non_missing,
                    "share_non_missing": n_non_missing / len(frame) if len(frame) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def deployable_features(availability: pd.DataFrame, min_transfer_hours: int) -> list[str]:
    """Choose features available for Kerkrade training and both RIVM dry-run sites."""
    selected = []
    for feature in TRANSFER_SCHEMA:
        rows = availability.loc[availability["feature"] == feature]
        train_ok = rows.loc[rows["site_id"] == "kerkrade_training", "n_non_missing"].ge(50).any()
        transfer_ok = (
            rows.loc[rows["site_id"].isin(TRANSFER_SITES), "n_non_missing"]
            .ge(min_transfer_hours)
            .all()
        )
        if train_ok and transfer_ok:
            selected.append(feature)
    return selected


def fallback_scores(detector: str) -> pd.DataFrame:
    """Return an extreme-score series for provisional fallback labels."""
    if detector == "sarimax":
        frame = read_timestamped(SARIMAX_RESIDUALS_PATH)
        score = frame["sarimax_residual"].abs()
    elif detector == "kalman":
        frame = read_timestamped(KALMAN_INNOVATIONS_PATH)
        score = frame["standardized_innovation"].abs()
    elif detector == "iforest":
        frame = read_timestamped(IFOREST_SCORES_PATH)
        score = frame["iforest_score"]
    else:
        raise ValueError(f"Unknown detector: {detector}")
    return pd.DataFrame({"timestamp_utc": frame["timestamp_utc"], "fallback_score": score})


def detector_labels(
    detector: str, min_positives: int = 5
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Build the official or fallback training label for one detector."""
    flags = read_timestamped(FLAGS_PATH)
    label_column = f"{detector}_anomaly"
    scored_column = f"{detector}_scored"
    label_columns = ["timestamp_utc", label_column]
    if scored_column in flags.columns:
        label_columns.append(scored_column)
    labels = flags[label_columns].copy()
    if scored_column in labels.columns:
        labels = labels.loc[labels[scored_column].astype(bool)].drop(columns=[scored_column])
    labels[label_column] = labels[label_column].astype(bool)
    official_positive_count = int(labels[label_column].sum())

    metadata: dict[str, object] = {
        "detector": detector,
        "official_positive_count": official_positive_count,
    }
    if official_positive_count >= min_positives:
        labels = labels.rename(columns={label_column: "label"})
        metadata.update(
            {
                "label_source": "official_detector_flag",
                "fallback_score_column": "",
                "fallback_positive_share": np.nan,
            }
        )
        return labels, metadata

    scores = fallback_scores(detector)
    labels = labels.merge(scores, on="timestamp_utc", how="inner")
    n_positive = max(1, int(np.ceil(len(labels) * FALLBACK_POSITIVE_SHARE)))
    labels["label"] = labels["fallback_score"].rank(method="first", ascending=False) <= n_positive
    metadata.update(
        {
            "label_source": f"fallback_top_{int(FALLBACK_POSITIVE_SHARE * 100)}pct_extreme_score",
            "fallback_score_column": "fallback_score",
            "fallback_positive_share": FALLBACK_POSITIVE_SHARE,
        }
    )
    return labels[["timestamp_utc", "label"]], metadata


def fit_transfer_model(
    detector: str,
    train_features: pd.DataFrame,
    features: list[str],
) -> tuple[dict[str, object], pd.DataFrame]:
    """Fit one logistic surrogate from Kerkrade detector labels."""
    labels, label_meta = detector_labels(detector)
    model_frame = train_features.merge(labels, on="timestamp_utc", how="inner")
    model_frame = model_frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[*features, "label"])
    positive_count = int(model_frame["label"].sum())
    negative_count = int((~model_frame["label"]).sum())

    summary = {
        **label_meta,
        "features_used": ", ".join(features),
        "n_features": len(features),
        "n_training_rows": len(model_frame),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "model_status": "fit",
    }

    if len(features) == 0 or positive_count == 0 or negative_count == 0:
        summary["model_status"] = "skipped_insufficient_label_or_feature_variation"
        return summary, model_frame

    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=1000),
    )
    model.fit(model_frame[features], model_frame["label"].astype(int))

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / f"{detector}-transfer.pkl"
    with model_path.open("wb") as handle:
        pickle.dump(
            {
                "model": model,
                "detector": detector,
                "features": features,
                "label_source": summary["label_source"],
                "status": "provisional_august_v1_dry_run",
            },
            handle,
        )
    summary["model_path"] = str(model_path)
    summary["training_start_utc"] = model_frame["timestamp_utc"].min()
    summary["training_end_utc"] = model_frame["timestamp_utc"].max()
    return summary, model_frame


def score_transfer_site(
    detector: str,
    model_payload: dict[str, object],
    site_id: str,
    site_frame: pd.DataFrame,
    min_transfer_hours: int,
) -> dict[str, object]:
    """Apply one fitted surrogate model to one transfer site."""
    features = model_payload["features"]
    model = model_payload["model"]
    complete = site_frame.replace([np.inf, -np.inf], np.nan).dropna(subset=features).copy()
    status = (
        "scored_provisional_dry_run"
        if len(complete) >= min_transfer_hours
        else "insufficient_complete_aligned_hours"
    )

    output_columns = [
        "timestamp_utc",
        "site_id",
        "detector",
        "anomaly_probability",
        "transfer_anomaly_provisional",
        "status",
    ]
    if status != "scored_provisional_dry_run":
        output = pd.DataFrame(columns=output_columns)
        output.to_csv(TRANSFER_OUT_DIR / f"{site_id}-{detector}.csv", index=False)
        return {
            "site_id": site_id,
            "detector": detector,
            "n_complete_scoring_rows": len(complete),
            "score_status": status,
            "score_start_utc": pd.NaT,
            "score_end_utc": pd.NaT,
        }

    probabilities = model.predict_proba(complete[features])[:, 1]
    output = pd.DataFrame(
        {
            "timestamp_utc": complete["timestamp_utc"],
            "site_id": site_id,
            "detector": detector,
            "anomaly_probability": probabilities,
            "transfer_anomaly_provisional": probabilities >= 0.5,
            "status": status,
        }
    )
    out_path = TRANSFER_OUT_DIR / f"{site_id}-{detector}.csv"
    output.to_csv(out_path, index=False)
    write_score_plot(output, site_id, detector)

    return {
        "site_id": site_id,
        "detector": detector,
        "n_complete_scoring_rows": len(output),
        "score_status": status,
        "score_start_utc": output["timestamp_utc"].min(),
        "score_end_utc": output["timestamp_utc"].max(),
        "provisional_flag_count": int(output["transfer_anomaly_provisional"].sum()),
    }


def write_score_plot(scores: pd.DataFrame, site_id: str, detector: str) -> None:
    """Plot provisional transfer anomaly probabilities for a dry-run site."""
    fig, axis = plt.subplots(figsize=(11, 4), constrained_layout=True)
    axis.plot(scores["timestamp_utc"], scores["anomaly_probability"], linewidth=1)
    axis.axhline(0.5, color="black", linestyle="--", linewidth=0.8, alpha=0.6)
    axis.set_title(f"{site_id} {detector} transfer surrogate")
    axis.set_ylabel("Anomaly probability")
    axis.set_xlabel("timestamp_utc")
    axis.grid(True, alpha=0.25)
    fig.savefig(RESULTS_DIR / f"{site_id}-{detector}-scores.png", dpi=160)
    plt.close(fig)


def write_transfer_event_labels(transfer_frames: dict[str, pd.DataFrame]) -> None:
    """Write provisional regional proxy labels aligned to each RIVM dry-run site."""
    soft = read_timestamped(SOFT_LABELS_PATH)
    for site_id, frame in transfer_frames.items():
        events = frame[["timestamp_utc"]].merge(soft, on="timestamp_utc", how="left")
        events.insert(1, "site_id", site_id)
        events.insert(2, "label_source", "regional_south_limburg_proxy")
        events.to_csv(PROCESSED_DIR / f"events-transfer-{site_id}.csv", index=False)


def baseline_availability_table(
    transfer_frames: dict[str, pd.DataFrame],
    features: list[str],
    score_rows: list[dict[str, object]],
    min_transfer_hours: int,
) -> pd.DataFrame:
    """Summarize transfer input windows and scoring availability."""
    score_status = pd.DataFrame(score_rows)
    rows = []
    for site_id, frame in transfer_frames.items():
        complete = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=features)
        row = {
            "site_id": site_id,
            "source": "RIVM/Luchtmeetnet pollutants + KNMI 06380 meteorology",
            "raw_start_utc": frame["timestamp_utc"].min(),
            "raw_end_utc": frame["timestamp_utc"].max(),
            "n_raw_hours": len(frame),
            "n_complete_feature_hours": len(complete),
            "features_used": ", ".join(features),
            "minimum_required_complete_hours": min_transfer_hours,
        }
        if not score_status.empty:
            site_scores = score_status.loc[score_status["site_id"] == site_id]
            row["detectors_scored"] = int(
                (site_scores["score_status"] == "scored_provisional_dry_run").sum()
            )
            row["detectors_insufficient"] = int(
                (site_scores["score_status"] != "scored_provisional_dry_run").sum()
            )
        rows.append(row)
    return pd.DataFrame(rows)


def write_figure_manifest() -> None:
    """Write a lightweight manifest for the current chapter figure candidates."""
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    candidates = [
        ("example_data_window", "results/eda/co2_discharge_soft_labels.png", "draft"),
        ("barometric_fit", "results/baseline/co2_fit_residual.png", "draft"),
        ("eryilmaz_roc", "results/eryilmaz/roc_curves.png", "draft"),
        (
            "residual_lag_heatmap",
            "results/signal/residual_cross_correlation_heatmap.png",
            "provisional",
        ),
        ("sarimax_residuals", "results/sarimax/residual_timeseries.png", "provisional"),
        ("kalman_innovations", "results/kalman/innovations.png", "provisional"),
        ("iforest_scores", "results/iforest/iforest_scores.png", "provisional"),
        ("ensemble_agreement", "results/ensemble/all_three_agreement.png", "provisional"),
        ("knmi_visual_crossing", "results/knmi/knmi_vs_visualcrossing_pressure_temp.png", "draft"),
    ]
    rows = []
    for figure_id, path_text, status in candidates:
        path = Path(path_text)
        rows.append(
            {
                "figure_id": figure_id,
                "artifact_path": path_text,
                "status": status if path.exists() else "missing",
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    pd.DataFrame(rows).to_csv(FIGURE_DIR / "figure_manifest.csv", index=False)


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-transfer-hours", type=int, default=MIN_TRANSFER_HOURS)
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TRANSFER_OUT_DIR.mkdir(parents=True, exist_ok=True)

    train_features = kerkrade_feature_frame()
    transfer_frames = transfer_feature_frames()
    availability = feature_availability(train_features, transfer_frames)
    features = deployable_features(availability, args.min_transfer_hours)

    if not features:
        raise RuntimeError("No deployable transfer features found. Check KNMI/RIVM overlap.")

    training_rows = []
    model_payloads = {}
    for detector in DETECTORS:
        summary, _ = fit_transfer_model(detector, train_features, features)
        training_rows.append(summary)
        if summary["model_status"] == "fit":
            with open(summary["model_path"], "rb") as handle:
                model_payloads[detector] = pickle.load(handle)

    score_rows = []
    for detector, payload in model_payloads.items():
        for site_id, frame in transfer_frames.items():
            score_rows.append(
                score_transfer_site(
                    detector,
                    payload,
                    site_id,
                    frame,
                    args.min_transfer_hours,
                )
            )

    write_transfer_event_labels(transfer_frames)
    baseline = baseline_availability_table(
        transfer_frames,
        features,
        score_rows,
        args.min_transfer_hours,
    )
    write_figure_manifest()

    training_summary = pd.DataFrame(training_rows)
    if score_rows:
        score_summary = pd.DataFrame(score_rows)

        def scored(value):
            return int((value == "scored_provisional_dry_run").sum())

        def insufficient(value):
            return int((value != "scored_provisional_dry_run").sum())

        training_summary = training_summary.merge(
            score_summary.groupby("detector")
            .agg(
                transfer_sites_scored=("score_status", scored),
                transfer_sites_insufficient=("score_status", insufficient),
            )
            .reset_index(),
            on="detector",
            how="left",
        )

    training_summary["august_v1_status"] = (
        "provisional_dry_run_not_official_transfer_interpretation"
    )
    training_summary.to_csv(RESULTS_DIR / "transfer_training_summary.csv", index=False)
    availability.to_csv(RESULTS_DIR / "feature_availability.csv", index=False)
    baseline.to_csv(RESULTS_DIR / "baseline_availability.csv", index=False)

    print(f"deployable features ({len(features)}): {', '.join(features)}")
    print(f"wrote {RESULTS_DIR / 'transfer_training_summary.csv'}")
    print(f"wrote {RESULTS_DIR / 'feature_availability.csv'}")
    print(f"wrote {RESULTS_DIR / 'baseline_availability.csv'}")
    print(f"wrote transfer dry-run outputs under {TRANSFER_OUT_DIR}")
    print("status: provisional dry run; do not interpret transfer success/failure yet")


if __name__ == "__main__":
    main()
