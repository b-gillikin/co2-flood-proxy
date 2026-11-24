"""Compare two uncorrected daily discharge products against the held Rimburg record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.geoglows_experiment import sha, write_json  # noqa: E402
from src.grrr_reanalysis import VERSION, read_daily_flow  # noqa: E402

BASE = ROOT / "results/limburg_representation_extension_v1/c2_alphaearth_2017_v1"
PAIRED = BASE / "paired_predictions.parquet"
RECEIPT = BASE / "completion_review.json"
EPISODES = ROOT / "results/limburg_dise_repeatability_v1/episode_membership.csv"
GRRR = ROOT / "data/raw/open/grrr/distributed_model_2026_11"
FLOW = GRRR / "rimburg-reanalysis.npz"
FLOW_RECEIPT = FLOW.with_suffix(".manifest.json")
CLOCK = GRRR / "rimburg-time-identity.json"
OUT = ROOT / "results/rimburg_discharge_products_2026_11_23"
GAUGE = "18.Q.45"
OUTLET = "subhybas_2121124850"
DAYS = pd.date_range("2021-01-01", "2025-12-30", tz="UTC")
MODELS = ["geoglows_m3s", "google_m3s"]


def daily_series():
    review = json.loads(RECEIPT.read_text())
    if review["status"] != "completed" or sha(PAIRED) != review["paired_predictions_sha256"]:
        raise ValueError("C2 paired archive failed its completion receipt")
    frame = pd.read_parquet(
        PAIRED,
        columns=[
            "gauge",
            "regime",
            "source_role",
            "day",
            "q_observed",
            "q_model_m3s",
            "reference_area_km2",
            "clean_verification",
            "high_water",
            "p99_reference",
        ],
    )
    local = frame.loc[
        frame.gauge.eq(GAUGE) & frame.regime.eq("spatial") & frame.source_role.eq("local")
    ]
    local = local.set_index("day").sort_index()
    if (
        len(frame) != review["paired_rows"]
        or not local.index.isin(DAYS).all()
        or not local.index.is_unique
        or local.empty
    ):
        raise ValueError("Unexpected Rimburg verification population")
    local["observed_m3s"] = local.q_observed * local.reference_area_km2 / 86.4
    local = local.rename(columns={"q_model_m3s": "geoglows_m3s"})
    if not local.high_water.eq(local.q_observed.ge(local.p99_reference)).all():
        raise ValueError("Saved high-water labels disagree with their reference cutoffs")

    google = read_daily_flow(FLOW, CLOCK, [OUTLET], DAYS)[OUTLET].rename("google_m3s")
    return local.join(google, how="outer").rename_axis("day")


def episode_peaks(frame, episodes):
    high = frame.loc[frame.high_water.fillna(False)]
    assignments = pd.Series(0, index=high.index)
    records = []
    for e in episodes.itertuples(index=False):
        days = high.loc[e.start : e.end]
        if days.empty:
            continue
        assignments.loc[days.index] += 1
        peak = frame.loc[e.start : e.end].observed_m3s.idxmax()
        q = frame.loc[peak]
        matched = days[MODELS].notna().all(axis=1)
        matched_peak = q[MODELS].notna().all()
        records.append(
            {
                "episode": e.episode,
                "start": e.start,
                "end": e.end,
                "observed_peak_day": peak,
                "observed_peak_m3s": q.observed_m3s,
                "high_water_days": len(days),
                "matched_high_water_days": int(matched.sum()),
                "geoglows_peak_day_error_m3s": q.geoglows_m3s - q.observed_m3s
                if matched_peak
                else np.nan,
                "google_peak_day_error_m3s": q.google_m3s - q.observed_m3s
                if matched_peak
                else np.nan,
            }
        )
    if not assignments.eq(1).all():
        raise ValueError("A high-water day lacked unique inherited episode membership")
    return pd.DataFrame(records)


def scores(rows):
    paired = rows.dropna(subset=["observed_m3s", *MODELS])
    errors = paired[MODELS].sub(paired.observed_m3s, axis=0)
    result = {"available_gauge_days": len(rows), "paired_days": len(paired)}
    for column in MODELS:
        name = column.removesuffix("_m3s")
        result[f"{name}_mae_m3s"] = errors[column].abs().mean()
        result[f"{name}_bias_m3s"] = errors[column].mean()
    result["google_minus_geoglows_mae_m3s"] = result["google_mae_m3s"] - result["geoglows_mae_m3s"]
    return result


def hydrographs(frame, picks, out):
    fig, axes = plt.subplots(
        len(picks), 1, squeeze=False, figsize=(8, 2.9 * len(picks)), layout="constrained"
    )
    for ax, e in zip(axes[:, 0], picks.itertuples(index=False), strict=True):
        pad = pd.Timedelta(days=3)
        dates = pd.date_range(e.start - pad, e.end + pad, freq="D")
        data = frame.reindex(dates)
        for name, label, color in zip(
            ["observed_m3s", *MODELS],
            ["Waterschap gauge", "GEOGLOWS v2", "Google GRRR"],
            ["#33383f", "#cc7036", "#226a95"],
            strict=True,
        ):
            ax.plot(data.index, data[name], color=color, marker="o", markersize=2.5, label=label)
        ax.axvline(e.observed_peak_day, color="#666666", linestyle=":", linewidth=0.9)
        ax.set(
            title=f"Observed peak day {e.observed_peak_day:%d %B %Y}",
            ylabel="Daily mean discharge (m³/s)",
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.grid(axis="y", alpha=0.2)
    axes[0, 0].legend(frameon=False)
    fig.supxlabel("Nominal UTC day of daily mean")
    fig.savefig(out / "episode_hydrographs.png", dpi=175)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    out = parser.parse_args().output
    joined = daily_series()
    episodes = pd.read_csv(EPISODES, parse_dates=["start", "end"])
    episodes = episodes.loc[episodes.gauge.eq(GAUGE) & episodes.dataset.eq("local_spatial")]
    measures, peaks, influence, coverage = [], [], [], []
    for year, rows in joined.groupby(joined.index.year):
        coverage.append(
            {
                "year": year,
                "calendar_days": len(rows),
                "held_gauge_days": int(rows.observed_m3s.notna().sum()),
                "geoglows_days_in_held_census": int(rows.geoglows_m3s.notna().sum()),
                "google_days": int(rows.google_m3s.notna().sum()),
                "clean_paired_days": int(
                    rows.loc[rows.clean_verification.fillna(False), ["observed_m3s", *MODELS]]
                    .notna()
                    .all(axis=1)
                    .sum()
                ),
            }
        )
    eligible = joined.dropna(subset=["observed_m3s"])
    clean = eligible.loc[eligible.clean_verification.fillna(False)]
    for population, sample in (("quality_screened", clean), ("broader_eligible", eligible)):
        high = sample.loc[sample.high_water.fillna(False)]
        p = episode_peaks(sample, episodes)
        peaks.append(p.assign(population=population))
        for subset, rows in (("all_days", sample), ("high_water", high)):
            measures.append(dict(population=population, subset=subset, **scores(rows)))
            for year, x in rows.groupby(rows.index.year):
                measures.append(dict(population=population, subset=subset, year=year, **scores(x)))
        full = scores(high)["google_minus_geoglows_mae_m3s"]
        for e in p.itertuples(index=False):
            remainder = high.loc[~high.index.to_series().between(e.start, e.end)]
            delta = scores(remainder)["google_minus_geoglows_mae_m3s"]
            influence.append(
                dict(
                    population=population,
                    episode=e.episode,
                    paired_mae_difference_without_episode_m3s=delta,
                    change_from_all_episodes_m3s=delta - full,
                )
            )

    out.mkdir(parents=True, exist_ok=True)
    tables = {
        "coverage.csv": pd.DataFrame(coverage),
        "scores.csv": pd.DataFrame(measures),
        "episode_peak_errors.csv": pd.concat(peaks),
        "episode_influence.csv": pd.DataFrame(influence),
    }
    for name, table in tables.items():
        table.to_csv(out / name, index=False)
    largest = peaks[0].observed_peak_m3s.idxmax()
    primary_influence = tables["episode_influence.csv"].query("population == 'quality_screened'")
    strongest = primary_influence.loc[
        primary_influence.change_from_all_episodes_m3s.abs().idxmax(), "episode"
    ]
    picks = peaks[0].loc[[largest]]
    hydrographs(
        clean,
        pd.concat([picks, peaks[0].loc[peaks[0].episode.eq(strongest)]]).drop_duplicates("episode"),
        out,
    )
    write_json(
        out / "manifest.json",
        {
            "status": "completed",
            "gauge": GAUGE,
            "geoglows_reach": 230393243,
            "google_release": VERSION,
            "google_outlet": OUTLET,
            "clock": "nominal UTC with source-internal T to T+1 lead-zero check",
            "sign": "model minus observed for bias; Google minus GEOGLOWS for MAE contrast",
            "inputs_sha256": {
                str(p.relative_to(ROOT)): sha(p)
                for p in (
                    Path(__file__),
                    ROOT / "src/grrr_reanalysis.py",
                    PAIRED,
                    RECEIPT,
                    EPISODES,
                    FLOW,
                    FLOW_RECEIPT,
                    CLOCK,
                )
            },
            "outputs_sha256": {
                name: sha(out / name) for name in (*tables, "episode_hydrographs.png")
            },
        },
    )
    print(tables["scores.csv"].loc[lambda x: x.year.isna()].to_string(index=False))


if __name__ == "__main__":
    main()
