"""Plot the completed DISE comparison and paired event examples."""

import hashlib
import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/limburg_dise_repeatability_v1"
PREDICTIONS = ROOT / "results/limburg_dise_multiyear_v1/predictions.parquet"
FIGURES = ROOT / "docs/figures"
DATASETS = {
    "local_temporal": "Local, earlier target labels allowed",
    "local_spatial": "Local, whole river withheld",
    "external_transfer": "Reserved external rivers",
}
CASES = (
    ("local_spatial", "Wurm|2021-07-14", "2828300000200", "Herzogenrath 1 · July 2021"),
    ("local_spatial", "Wurm|2021-07-14", "2828900000200", "Randerath · July 2021"),
    ("external_transfer", "external:Sieg|2023-01-12", "DEA13190", "Kaiserau · January 2023"),
    ("external_transfer", "external:Sieg|2023-12-21", "DEA13190", "Kaiserau · December 2023"),
)


def verify_sources():
    manifest = json.loads((RESULTS / "manifest.json").read_text())
    expected = {ROOT / path: value for path, value in manifest["inputs"].items()}
    expected.update({RESULTS / path: value for path, value in manifest["output_hashes"].items()})
    for path, digest in expected.items():
        with path.open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != digest:
                raise ValueError(f"Source differs from the completed run: {path}")
    return len(expected)


def save_svg(figure, filename):
    svg = io.StringIO()
    figure.savefig(svg, format="svg", metadata={"Date": None})
    lines = svg.getvalue().splitlines()
    (FIGURES / filename).write_text(
        "\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8"
    )
    plt.close(figure)


def plot_effects():
    points = pd.read_csv(RESULTS / "paired_effects.csv")
    draws = pd.read_csv(RESULTS / "paired_intervals.csv")
    keys = ["dataset", "scope", "stratum", "contrast", "metric"]
    rows = points.merge(draws.loc[draws.scheme.eq("moving_30d")], on=keys, validate="one_to_one")
    rows = rows[
        rows.scope.isin(["local_all", "external_all"])
        & rows.contrast.eq("alpha_added")
        & rows.metric.eq("mae")
    ].set_index(["stratum", "dataset"])
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 5), sharex=True, layout="constrained")
    for ax, stratum, title in zip(
        axes,
        ["high_water", "all_days"],
        ["Daily p99 high water (primary)", "All valid days (secondary)"],
        strict=True,
    ):
        for y, dataset in enumerate(DATASETS):
            row = rows.loc[stratum, dataset]
            ax.hlines(y, row.reduction_pct_low, row.reduction_pct_high, color="#14677b", lw=2)
            ax.scatter(row.reduction_pct, y, color="#14677b", zorder=3)
            ax.text(18.8, y, f"{int(row.defined_draws)}/999", ha="left", va="center", fontsize=9)
        ax.set_yticks(range(len(DATASETS)), list(DATASETS.values()))
        ax.set_ylim(2.6, -0.6)
        ax.set_xlim(-9.5, 24)
        ax.set_xticks([-5, 0, 5, 10, 15])
        ax.axvline(0, color="#636363", lw=1, ls="--")
        ax.set_title(title, loc="left")
    axes[-1].set_xlabel("MAE reduction after adding AlphaEarth (%) · positive means lower error")
    fig.suptitle(
        "AlphaEarth added to the conventional GEOGLOWS correction\n"
        "95% paired 30-day ranges | Defined draws at right",
        fontsize=13,
    )
    save_svg(fig, "limburg-dise-alphaearth-effects.svg")


def plot_events():
    predictions = pd.read_parquet(PREDICTIONS)
    episodes = pd.read_csv(RESULTS / "episodes.csv", dtype={"gauge": str})
    index = pd.read_csv(RESULTS / "symmetric_case_review_index.csv", dtype={"gauge": str})
    fig, axes = plt.subplots(2, 2, figsize=(10.4, 6.6), layout="constrained")
    for ax, (dataset, episode, gauge, title) in zip(axes.flat, CASES, strict=True):
        case = index.set_index(["dataset", "episode", "gauge"]).loc[dataset, episode, gauge]
        event = episodes[
            episodes.dataset.eq(dataset)
            & episodes.episode.eq(episode)
            & episodes.gauge.eq(gauge)
            & episodes.arm.eq("q_model")
        ].iloc[0]
        dates = pd.date_range(
            pd.Timestamp(event.start) - pd.Timedelta(days=3),
            pd.Timestamp(event.end) + pd.Timedelta(days=3),
        )
        external = dataset == "external_transfer"
        frame = (
            predictions[
                predictions.gauge.eq(gauge)
                & predictions.regime.eq("temporal" if external else "spatial")
                & predictions.source_role.eq("reserved_external" if external else "local")
            ]
            .set_index("day")
            .reindex(dates)
        )
        if frame.q_observed.count() != event.rows or len(dates) != event.expected_days:
            raise ValueError(f"Event window does not reproduce the saved ledger: {episode}/{gauge}")
        high_water = frame.high_water.fillna(False)
        ax.scatter(
            dates[high_water], frame.loc[high_water, "q_observed"], color="#242424", s=12, zorder=4
        )
        for col, label, color, style in (
            ("q_observed", "Supplied observation", "#242424", "-"),
            ("q_model", "Raw GEOGLOWS", "#777777", "--"),
            ("native_rmse__H+A", "Conventional correction", "#ac5311", "-"),
            ("native_rmse__H+A+E", "With AlphaEarth", "#14677b", "-"),
        ):
            ax.plot(dates, frame[col], label=label, color=color, ls=style, lw=1.5)
        ax.set_title(
            f"{title}\nWindow MAE {case.available_day_mae_conventional:.2f} → "
            f"{case.available_day_mae_alpha:.2f} mm/day",
            loc="left",
            fontsize=10,
        )
        ax.set_ylabel("Daily discharge (mm/day)")
        ax.set_ylim(bottom=0)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.tick_params(labelsize=8)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=4, fontsize=9)
    fig.suptitle("Selected high-water windows · dots mark observed daily p99 exceedances")
    save_svg(fig, "limburg-dise-alphaearth-cases.svg")


if __name__ == "__main__":
    print(f"Verified {verify_sources()} source and output hashes from the completed run.")
    plt.rcParams.update({"svg.fonttype": "none", "svg.hashsalt": "limburg-dise-consolidation"})
    FIGURES.mkdir(exist_ok=True)
    plot_effects()
    plot_events()
