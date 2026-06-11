"""Week 4 exploratory characterization of the barometric CO2 residual."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


INTERIM_DIR = Path("data/interim")
PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/signal")

ANALYSIS_PATH = INTERIM_DIR / "analysis_hourly.csv"
RESIDUAL_PATH = PROCESSED_DIR / "co2-residual-barometric.csv"
FRAME_PATH = PROCESSED_DIR / "signal_characterization_frame.csv"

RESIDUAL_COL = "co2_residual_barometric_ppm"
HYDRO_TARGET_COL = "any_antecedent_72h_level"
LAGS_HOURS = range(-24, 337)
MIN_OVERLAP = 24
RANDOM_STATE = 42
RF_TREES = 300
PERMUTATION_REPEATS = 10

ENVIRONMENTAL_FEATURES = [
    "iot_temperature_c",
    "iot_relative_humidity_pct",
    "iot_pm2_5_ugm3",
    "iot_pm10_ugm3",
    "kerkrade_weather_temp_c",
    "kerkrade_weather_relative_humidity_pct",
    "kerkrade_weather_precip_mm",
    "kerkrade_weather_wind_speed_kph",
    "kerkrade_weather_cloud_cover_pct",
    "kerkrade_weather_pm2_5_ugm3",
    "kerkrade_weather_pm10_ugm3",
]

HYDROLOGICAL_FEATURES = [
    "discharge_wurm_rimburg_m3s",
    "discharge_geul_hommerich_m3s",
    "discharge_geul_meerssen_m3s",
    "any_current_level",
    "any_antecedent_24h_level",
    "any_antecedent_72h_level",
    "any_antecedent_168h_level",
]


def load_signal_frame():
    """Join the Week 1 analysis frame to Week 2 residuals."""
    analysis = pd.read_csv(ANALYSIS_PATH, parse_dates=["timestamp_utc"])
    residual = pd.read_csv(RESIDUAL_PATH, parse_dates=["timestamp_utc"])
    residual = residual[["timestamp_utc", RESIDUAL_COL, "co2_fitted_barometric_ppm"]]

    frame = analysis.merge(residual, on="timestamp_utc", how="inner")
    frame = frame.set_index("timestamp_utc").sort_index()
    return frame


def available(columns, frame):
    """Keep requested columns that are present in the current analysis frame."""
    return [column for column in columns if column in frame.columns]


def feature_deltas(frame, columns, lags=(1, 3, 6, 12, 24)):
    """Add simple tendency features for non-pressure environmental channels."""
    out = frame.copy()
    for column in columns:
        for lag in lags:
            out[f"{column}_delta_{lag}h"] = out[column] - out[column].shift(lag)
    return out


def delta_feature_columns(frame):
    """Find tendency columns created by ``feature_deltas``."""
    suffixes = ("delta_1h", "delta_3h", "delta_6h", "delta_12h", "delta_24h")
    return [column for column in frame.columns if column.endswith(suffixes)]


def cross_correlations(frame, feature_cols):
    """Compute residual-feature correlations across hourly lags.

    Positive lag means the feature is earlier than the residual by that many
    hours. Negative lag means the residual is earlier than the feature.
    """
    rows = []
    residual = frame[RESIDUAL_COL]
    for feature in feature_cols:
        series = frame[feature]
        for lag in LAGS_HOURS:
            shifted = series.shift(lag)
            paired = pd.concat([residual, shifted], axis=1).dropna()
            rows.append(
                {
                    "feature": feature,
                    "lag_hours": lag,
                    "n_overlap": len(paired),
                    "correlation": (
                        paired.iloc[:, 0].corr(paired.iloc[:, 1])
                        if len(paired) >= MIN_OVERLAP
                        else float("nan")
                    ),
                    "low_overlap": len(paired) < MIN_OVERLAP,
                }
            )
    return pd.DataFrame(rows)


def top_cross_correlations(correlations):
    """Keep the strongest lagged correlations for quick reading."""
    out = correlations.dropna(subset=["correlation"]).copy()
    out["abs_correlation"] = out["correlation"].abs()
    return (
        out.sort_values(["feature", "abs_correlation"], ascending=[True, False])
        .groupby("feature")
        .head(3)
        .sort_values("abs_correlation", ascending=False)
    )


def random_forest_importance(frame, target_col, feature_cols, label):
    """Fit an exploratory random forest and return permutation importance."""
    model_frame = frame[[target_col, *feature_cols]].dropna()
    x = model_frame[feature_cols]
    y = model_frame[target_col]

    model = RandomForestRegressor(
        n_estimators=RF_TREES,
        min_samples_leaf=5,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    model.fit(x, y)
    permutation = permutation_importance(
        model,
        x,
        y,
        n_repeats=PERMUTATION_REPEATS,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    importance = pd.DataFrame(
        {
            "analysis": label,
            "feature": feature_cols,
            "permutation_importance_mean": permutation.importances_mean,
            "permutation_importance_std": permutation.importances_std,
            "gini_importance": model.feature_importances_,
            "target": target_col,
            "n_rows": len(model_frame),
            "training_r2": model.score(x, y),
        }
    )
    return importance.sort_values("permutation_importance_mean", ascending=False)


def pca_summary(frame, feature_cols):
    """Run PCA on standardized residual and environmental variables."""
    pca_cols = [RESIDUAL_COL, *feature_cols]
    model_frame = frame[pca_cols].dropna()
    pipeline = make_pipeline(StandardScaler(), PCA(n_components=min(5, len(pca_cols))))
    scores = pipeline.fit_transform(model_frame)
    pca = pipeline.named_steps["pca"]

    loadings = pd.DataFrame(
        pca.components_.T,
        index=pca_cols,
        columns=[f"pc{i}" for i in range(1, pca.n_components_ + 1)],
    ).reset_index(names="feature")
    explained = pd.DataFrame(
        {
            "component": [f"pc{i}" for i in range(1, pca.n_components_ + 1)],
            "explained_variance_ratio": pca.explained_variance_ratio_,
            "cumulative_explained_variance_ratio": pca.explained_variance_ratio_.cumsum(),
        }
    )
    scores = pd.DataFrame(
        scores[:, :2],
        index=model_frame.index,
        columns=["pc1_score", "pc2_score"],
    ).reset_index()
    return loadings, explained, scores


def write_cross_correlation_plot(correlations):
    """Plot lagged correlations as a compact feature-by-lag heatmap."""
    matrix = correlations.pivot(index="feature", columns="lag_hours", values="correlation")
    fig, axis = plt.subplots(figsize=(13, max(5, 0.35 * len(matrix))), constrained_layout=True)
    image = axis.imshow(matrix, aspect="auto", cmap="coolwarm", vmin=-1, vmax=1)
    axis.set_yticks(range(len(matrix.index)))
    axis.set_yticklabels(matrix.index)
    tick_positions = list(range(0, len(matrix.columns), 48))
    axis.set_xticks(tick_positions)
    axis.set_xticklabels([matrix.columns[position] for position in tick_positions], rotation=45)
    axis.set_xlabel("Lag hours; positive means feature leads residual")
    axis.set_title("Barometric residual cross-correlation scan")
    fig.colorbar(image, ax=axis, label="Pearson r")
    fig.savefig(RESULTS_DIR / "residual_cross_correlation_heatmap.png", dpi=160)
    plt.close(fig)


def write_importance_plot(importance):
    """Plot the strongest random-forest permutation importances."""
    top = importance.head(12).sort_values("permutation_importance_mean")
    fig, axis = plt.subplots(figsize=(8, 6), constrained_layout=True)
    axis.barh(top["feature"], top["permutation_importance_mean"])
    axis.set_xlabel("Permutation importance")
    axis.set_title(f"Random forest importance: {top['analysis'].iloc[0]}")
    fig.savefig(RESULTS_DIR / f"{top['analysis'].iloc[0]}_rf_feature_importance.png", dpi=160)
    plt.close(fig)


def write_pca_plot(scores):
    """Plot the first two PCA scores through time."""
    fig, axis = plt.subplots(figsize=(9, 7), constrained_layout=True)
    axis.scatter(scores["pc1_score"], scores["pc2_score"], s=18, alpha=0.8)
    axis.axhline(0, color="black", linewidth=0.8, alpha=0.4)
    axis.axvline(0, color="black", linewidth=0.8, alpha=0.4)
    axis.set_xlabel("PC1 score")
    axis.set_ylabel("PC2 score")
    axis.set_title("PCA scores for residual/environmental frame")
    fig.savefig(RESULTS_DIR / "pca_scores.png", dpi=160)
    plt.close(fig)


def write_summary(frame, correlations, residual_importance, hydro_importance, explained):
    """Write a short text summary for the Week 4 exploratory pass."""
    top_corr = top_cross_correlations(correlations).head(10)
    lines = [
        "Week 4 Signal Characterization",
        "",
        f"Rows in residual analysis frame: {len(frame)}",
        f"Analysis window: {frame.index.min()} to {frame.index.max()}",
        f"Cross-correlation lags: {min(LAGS_HOURS)}h to {max(LAGS_HOURS)}h",
        f"Minimum overlap for reported correlation: {MIN_OVERLAP} rows",
        "",
        "Top absolute residual-feature cross-correlations:",
    ]
    for _, row in top_corr.iterrows():
        lines.append(
            f"  {row['feature']} at lag {int(row['lag_hours'])}h: "
            f"r={row['correlation']:.3f}, n={int(row['n_overlap'])}"
        )

    lines.extend(
        [
            "",
            "Top residual random-forest features:",
            *[
                f"  {row.feature}: {row.permutation_importance_mean:.4f}"
                for row in residual_importance.head(8).itertuples()
            ],
            "",
            f"Top hydrology-target random-forest features ({HYDRO_TARGET_COL}):",
            *[
                f"  {row.feature}: {row.permutation_importance_mean:.4f}"
                for row in hydro_importance.head(8).itertuples()
            ],
            "",
            "PCA explained variance:",
            *[
                f"  {row.component}: {row.explained_variance_ratio:.3f}"
                for row in explained.itertuples()
            ],
            "",
            "Interpretation note: this is exploratory because the current IoT/residual window is short.",
        ]
    )
    (RESULTS_DIR / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Command-line entry point."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    frame = load_signal_frame()
    env_cols = available(ENVIRONMENTAL_FEATURES, frame)
    hydro_cols = available(HYDROLOGICAL_FEATURES, frame)
    frame = feature_deltas(frame, env_cols)
    delta_cols = delta_feature_columns(frame)

    corr_cols = env_cols + hydro_cols
    correlations = cross_correlations(frame, corr_cols)
    top_correlations = top_cross_correlations(correlations)

    residual_features = env_cols + delta_cols + hydro_cols
    hydro_features = [RESIDUAL_COL, *env_cols, *delta_cols]
    residual_importance = random_forest_importance(
        frame,
        RESIDUAL_COL,
        residual_features,
        "residual_structure",
    )
    hydro_importance = random_forest_importance(
        frame,
        HYDRO_TARGET_COL,
        hydro_features,
        "hydrology_proxy",
    )
    loadings, explained, scores = pca_summary(frame, env_cols)

    frame.to_csv(FRAME_PATH, index_label="timestamp_utc")
    correlations.to_csv(RESULTS_DIR / "cross_correlation.csv", index=False)
    top_correlations.to_csv(RESULTS_DIR / "top_cross_correlations.csv", index=False)
    residual_importance.to_csv(RESULTS_DIR / "rf_residual_importance.csv", index=False)
    hydro_importance.to_csv(RESULTS_DIR / "rf_hydrology_importance.csv", index=False)
    loadings.to_csv(RESULTS_DIR / "pca_loadings.csv", index=False)
    explained.to_csv(RESULTS_DIR / "pca_explained_variance.csv", index=False)
    scores.to_csv(RESULTS_DIR / "pca_scores.csv", index=False)

    write_cross_correlation_plot(correlations)
    write_importance_plot(residual_importance)
    write_importance_plot(hydro_importance)
    write_pca_plot(scores)
    write_summary(frame, correlations, residual_importance, hydro_importance, explained)

    print(f"Week 4 signal frame rows: {len(frame)}")
    print(f"Analysis window: {frame.index.min()} to {frame.index.max()}")
    print(f"Features scanned for cross-correlation: {len(corr_cols)}")
    print(f"wrote {RESULTS_DIR}")


if __name__ == "__main__":
    main()
