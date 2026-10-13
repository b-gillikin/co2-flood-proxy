#!/usr/bin/env python3
"""Census fixed retrieved analogues as event sets and complete hydrograph shapes.

Exploratory extension authorized after the peak-only results. Outcomes describe
relevance; they never rerank donors or alter retrieval. No sampled reference
events, model fitting, imputation or automated human relevance verdicts.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "step6", ROOT / "scripts/73_analogue_uncertainty_review.py"
)
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)
OUT = ROOT / "results/basin_ai_analogue_census"
METRICS = [
    "level_rmse_p99",
    "peak_scaled_shape_rmse",
    "peak_time_difference_h",
    "high_water_duration_difference_h",
    "excess_area_difference_p99_h",
    "terminal_peak_ratio_difference",
]
PAGE_ROWS = 12


def response_signatures(response):
    """Rows are complete hourly Q/p99, ordered hours 1–72 (onset excluded)."""
    values = np.asarray(response, dtype=float)
    if values.ndim != 2 or values.shape[1] != 72 or not np.isfinite(values).all():
        raise ValueError("Require complete finite hours 1–72")
    peak = values.max(axis=1)
    if (peak <= 0).any() or (values < 0).any():
        raise ValueError("Require nonnegative discharge and a positive response peak")
    return {
        "peak_ratio": peak,
        "peak_time_h": values.argmax(axis=1) + 1,
        "high_water_duration_h": (values >= 1).sum(axis=1),
        "excess_area_p99_h": np.maximum(values - 1, 0).sum(axis=1),
        "terminal_peak_ratio": values[:, -24:].mean(axis=1) / peak,
        "peak_scaled": values / peak[:, None],
    }


def response_distances(query, donors):
    query = np.asarray(query, dtype=float).reshape(1, 72)
    donors = np.asarray(donors, dtype=float)
    q = response_signatures(query)
    d = response_signatures(donors)
    return pd.DataFrame(
        {
            "level_rmse_p99": np.sqrt(np.square(donors - query).mean(axis=1)),
            "peak_scaled_shape_rmse": np.sqrt(
                np.square(d["peak_scaled"] - q["peak_scaled"]).mean(axis=1)
            ),
            "peak_time_difference_h": np.abs(d["peak_time_h"] - q["peak_time_h"]),
            "high_water_duration_difference_h": np.abs(
                d["high_water_duration_h"] - q["high_water_duration_h"]
            ),
            "excess_area_difference_p99_h": np.abs(d["excess_area_p99_h"] - q["excess_area_p99_h"]),
            "terminal_peak_ratio_difference": np.abs(
                d["terminal_peak_ratio"] - q["terminal_peak_ratio"]
            ),
        }
    )


def storm_weights(storm_ids):
    storms = pd.Series(storm_ids)
    weights = 1.0 / storms.map(storms.value_counts()).to_numpy(dtype=float)
    return weights / weights.sum()


def weighted_percentiles(reference, weights, selected):
    """Half-weight ties; lower means closer than more of the eligible archive."""
    reference = np.asarray(reference, dtype=float)
    weights = np.asarray(weights, dtype=float)
    order = np.argsort(reference, kind="stable")
    reference, weights = reference[order], weights[order]
    cumulative = np.r_[0.0, np.cumsum(weights)]
    left = np.searchsorted(reference, selected, side="left")
    right = np.searchsorted(reference, selected, side="right")
    return (cumulative[left] + cumulative[right]) / 2 / cumulative[-1]


def load_curves(index, windows):
    if windows.duplicated(["event_id", "relative_hour"]).any():
        raise ValueError("Duplicate event/hour observations")
    q = windows.pivot(index="event_id", columns="relative_hour", values="target_discharge_m3s")
    q = q.reindex(index=index.event_id, columns=np.arange(-511, 73))
    scale = index.set_index("event_id").p99_m3s
    if scale.isna().any() or scale.le(0).any():
        raise ValueError("Every episode needs its positive rating-era p99")
    response = q.loc[:, 1:72].div(scale, axis=0)
    history = q.loc[:, -511:0]
    mean, std = history.mean(axis=1), history.std(axis=1, ddof=0).replace(0, 1)
    standardized = history.sub(mean, axis=0).div(std, axis=0)
    rain = windows.pivot(index="event_id", columns="relative_hour", values="catchment_rainfall_mm")
    rain = rain.reindex(index=index.event_id, columns=np.arange(-511, 73))
    coverage = index.copy().set_index("event_id")
    coverage["observed_response_hours"] = response.notna().sum(axis=1)
    coverage["observed_history_hours"] = history.notna().sum(axis=1)
    coverage["exact_response_admissible"] = (
        coverage.outcome_score_admissible & coverage.observed_response_hours.eq(72)
    )
    for phase, start, end in [
        ("antecedent_rain_24h_mm", -23, 0),
        ("antecedent_rain_72h_mm", -71, 0),
        ("response_rain_24h_mm", 1, 24),
        ("response_rain_72h_mm", 1, 72),
    ]:
        coverage[phase] = rain.loc[:, start:end].sum(axis=1, min_count=end - start + 1)
    admissible = coverage.exact_response_admissible
    descriptors = response_signatures(response.loc[admissible].to_numpy())
    for column, values in descriptors.items():
        if column != "peak_scaled":
            coverage.loc[admissible, column] = values
    coverage["ends_above_p99"] = response[72].ge(1).where(admissible)
    coverage["peak_at_response_boundary"] = coverage.peak_time_h.isin([1, 72]).where(admissible)
    return response, standardized, coverage


def review_all_sets(pairs, samples, response, history, coverage):
    reviewed, pools, sets = [], [], []
    for (cohort, analysis), group in pairs.groupby(["cohort", "analysis"], sort=True):
        eligible = samples[cohort].loc[samples[cohort].complete_scoring_sample].copy()
        if analysis == "quality_sensitivity":
            eligible = eligible.loc[~eligible.measurement_concern]
        if cohort == "dutch":
            eligible = eligible.dropna(subset=REVIEW.BASE.FEATURE_COLUMNS)
        for query_id, query_pairs in group.groupby("query_event_id", sort=False):
            query = eligible.set_index("event_id").loc[query_id]
            prior = eligible.loc[
                eligible.onset_utc.add(pd.Timedelta(hours=72)).le(query.onset_utc)
                & eligible.onset_utc.lt(query.onset_utc)
                & eligible.storm_id.ne(query.storm_id)
                & eligible.event_id.ne(query_id)
            ]
            if len(prior) < 20 or prior.storm_id.nunique() < 5:
                raise ValueError("Previously scored query has an inadequate original donor pool")
            donor_ids = prior.event_id.to_list()
            q = response.loc[query_id].to_numpy()
            distances = response_distances(q, response.loc[donor_ids].to_numpy())
            distances.index = donor_ids
            weights = storm_weights(prior.storm_id)
            pool = {
                "cohort": cohort,
                "analysis": analysis,
                "query_event_id": query_id,
                "candidate_events": len(prior),
                "candidate_storms": prior.storm_id.nunique(),
                "same_gauge_candidate_events": int(prior.gauge.eq(query.gauge).sum()),
            }
            for metric in METRICS:
                pool[f"pool_mean_{metric}"] = np.average(distances[metric], weights=weights)
            pools.append(pool)
            for arm, selected in query_pairs.groupby("arm", sort=True):
                selected = selected.copy()
                ids = selected.analogue_event_id.to_list()
                if len(ids) != 5 or selected.analogue_storm_id.nunique() != 5:
                    raise ValueError("Expected five distinct-storm selected events")
                if not set(ids).issubset(donor_ids):
                    raise ValueError("Selected event outside original eligible prior pool")
                # Column order follows saved donor rank; no outcome-based reranking.
                values = distances.loc[ids].reset_index(drop=True)
                for metric in METRICS:
                    selected[metric] = values[metric].to_numpy()
                    selected[f"pool_percentile_{metric}"] = weighted_percentiles(
                        distances[metric], weights, values[metric]
                    )
                selected["history_shape_rmse"] = np.sqrt(
                    np.square(history.loc[ids].to_numpy() - history.loc[query_id].to_numpy()).mean(
                        axis=1
                    )
                )
                for column in [
                    "antecedent_rain_24h_mm",
                    "antecedent_rain_72h_mm",
                    "response_rain_24h_mm",
                    "response_rain_72h_mm",
                ]:
                    selected[f"absolute_difference_{column}"] = np.abs(
                        coverage.loc[ids, column].to_numpy() - coverage.loc[query_id, column]
                    )
                reviewed.append(selected)
                donor_curves = response.loc[ids].to_numpy()
                peaks = donor_curves.max(axis=1)
                observed_peak = q.max()
                row = {
                    **pool,
                    "arm": arm,
                    "query_onset_utc": query.onset_utc,
                    "query_watercourse": query.watercourse,
                    "query_gauge": query.gauge,
                    "query_country": coverage.loc[query_id, "country"],
                    "query_storm_id": query.storm_id,
                    "query_measurement_concern": query.measurement_concern,
                    "query_peak_ratio": observed_peak,
                    "query_peak_time_h": int(q.argmax() + 1),
                    "query_high_water_hours": int((q >= 1).sum()),
                    "query_ends_above_p99": bool(q[-1] >= 1),
                    "donor_peak_range_contains_query": bool(
                        peaks.min() <= observed_peak <= peaks.max()
                    ),
                    "mean_donor_peak_absolute_error": abs(peaks.mean() - observed_peak),
                    "mean_individual_peak_absolute_error": np.abs(peaks - observed_peak).mean(),
                    "ensemble_curve_level_rmse": np.sqrt(
                        np.square(donor_curves.mean(axis=0) - q).mean()
                    ),
                    "same_gauge_share": selected.same_gauge.mean(),
                    "same_river_share": selected.same_river.mean(),
                    "cross_country_share": selected.cross_country.mean(),
                    "flagged_pair_share": selected.measurement_concern_pair.mean(),
                    "history_shape_rmse": selected.history_shape_rmse.mean(),
                }
                for metric in METRICS:
                    row[f"mean_{metric}"] = selected[metric].mean()
                    row[f"best_selected_{metric}"] = selected[metric].min()
                    row[f"mean_pool_percentile_{metric}"] = selected[
                        f"pool_percentile_{metric}"
                    ].mean()
                for column in selected.columns:
                    if column.startswith("absolute_difference_"):
                        row[column] = selected[column].mean()
                        row[f"observed_pairs_{column}"] = selected[column].notna().sum()
                sets.append(row)
        print(f"Reviewed all {cohort}/{analysis} sets", flush=True)
    return pd.concat(reviewed, ignore_index=True), pd.DataFrame(pools), pd.DataFrame(sets)


def summarize_sets(sets):
    identifiers = ["cohort", "analysis", "arm"]
    measures = [
        c for c in sets if c.startswith(("mean_", "best_selected_", "absolute_difference_"))
    ]
    measures += [
        "ensemble_curve_level_rmse",
        "history_shape_rmse",
        "same_gauge_share",
        "cross_country_share",
        "flagged_pair_share",
        "donor_peak_range_contains_query",
    ]
    summary = sets.groupby(identifiers)[measures].mean().reset_index()
    counts = (
        sets.groupby(identifiers)
        .agg(query_sets=("query_event_id", "size"), query_storms=("query_storm_id", "nunique"))
        .reset_index()
    )
    return summary.merge(counts, on=identifiers, validate="one_to_one")


def paired_metric_intervals(sets):
    rows, query_contrasts = [], []
    for cohort, (_, _, contrasts) in REVIEW.COHORTS.items():
        for analysis in ["main", "quality_sensitivity"]:
            sample = sets.loc[sets.cohort.eq(cohort) & sets.analysis.eq(analysis)]
            for reference, challenger in contrasts:
                ref = sample.loc[sample.arm.eq(reference)].set_index("query_event_id")
                test = sample.loc[sample.arm.eq(challenger)].set_index("query_event_id")
                if set(ref.index) != set(test.index):
                    raise ValueError("Census contrasts require identical query events")
                test = test.loc[ref.index]
                if not ref.query_storm_id.eq(test.query_storm_id).all():
                    raise ValueError("Paired query storm labels differ")
                contrast = ref[
                    ["query_storm_id", "query_onset_utc", "query_watercourse", "query_country"]
                ].copy()
                contrast = contrast.assign(
                    cohort=cohort, analysis=analysis, reference=reference, challenger=challenger
                )
                for metric in METRICS:
                    difference = ref[["query_storm_id", "query_onset_utc"]].copy()
                    difference["difference"] = test[f"mean_{metric}"] - ref[f"mean_{metric}"]
                    contrast[f"difference_{metric}"] = difference.difference
                    first = difference.groupby("query_storm_id").query_onset_utc.transform("min")
                    difference["storm_year"] = pd.to_datetime(first, utc=True).dt.year
                    for unit in ["query_storm_id", "storm_year"]:
                        rows.append(
                            {
                                "cohort": cohort,
                                "analysis": analysis,
                                "reference": reference,
                                "challenger": challenger,
                                "metric": metric,
                                "resampling_unit": unit,
                                **REVIEW.cluster_interval(difference, unit),
                            }
                        )
                query_contrasts.append(contrast.reset_index())
    return pd.DataFrame(rows), pd.concat(query_contrasts, ignore_index=True)


def plot_census_summary(summary, sets, out):
    main = summary.loc[summary.analysis.eq("main")]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    labels = main.cohort + ": " + main.arm
    for ax, column, title in [
        (
            axes[0],
            "mean_pool_percentile_peak_scaled_shape_rmse",
            "Shape relative to the whole prior pool",
        ),
        (axes[1], "mean_peak_time_difference_h", "Mean individual-donor peak-time mismatch"),
        (axes[2], "mean_high_water_duration_difference_h", "Mean high-water-duration mismatch"),
    ]:
        ax.barh(labels, main[column], color="#2878b5")
        ax.set_title(title, fontsize=10)
        ax.grid(axis="x", alpha=0.2)
    axes[0].axvline(0.5, color="black", ls="--", lw=0.8)
    axes[0].set_xlabel("Weighted percentile; lower is closer")
    for ax in axes[1:]:
        ax.set_xlabel("Hours; lower is closer")
    fig.tight_layout()
    fig.savefig(out / "census_overview.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(15, 8), sharex=False)
    for ax, (cohort, group) in zip(
        axes, sets.loc[sets.analysis.eq("main")].groupby("cohort", sort=True), strict=True
    ):
        arm = REVIEW.COHORTS[cohort][1][-1]
        matrix = group.loc[group.arm.eq(arm)].sort_values(["query_onset_utc", "query_event_id"])
        columns = [f"mean_pool_percentile_{metric}" for metric in METRICS]
        data = matrix[columns].to_numpy().T
        ax.imshow(data, aspect="auto", vmin=0, vmax=1, cmap="coolwarm", interpolation="nearest")
        ax.set_yticks(range(len(METRICS)), [m.replace("_", " ") for m in METRICS], fontsize=7)
        ax.set_title(
            f"{cohort}/{arm}: every query chronologically ({len(matrix)}); blue=closer than prior pool",
            fontsize=10,
        )
        ax.set_xlabel("Query index", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "all_query_relevance.png", dpi=160)
    plt.close(fig)


def make_atlas(pairs, sets, response, out):
    atlas = out / "atlas"
    atlas.mkdir(exist_ok=True)
    pages, query_links = [], []
    for cohort, group in sets.loc[sets.analysis.eq("main")].groupby("cohort", sort=True):
        ids = group.sort_values(["query_onset_utc", "query_event_id"]).query_event_id.unique()
        arms = REVIEW.COHORTS[cohort][1]
        for page, start in enumerate(range(0, len(ids), PAGE_ROWS), start=1):
            selected_ids = ids[start : start + PAGE_ROWS]
            fig, axes = plt.subplots(
                len(selected_ids), len(arms), figsize=(16, len(selected_ids) * 2.1), squeeze=False
            )
            for row, event_id in enumerate(selected_ids):
                observations = response.loc[event_id].to_numpy()
                all_values = [observations]
                donor_arrays = {}
                for arm in arms:
                    donors = pairs.loc[
                        pairs.cohort.eq(cohort)
                        & pairs.analysis.eq("main")
                        & pairs.arm.eq(arm)
                        & pairs.query_event_id.eq(event_id)
                    ]
                    donor_arrays[arm] = response.loc[donors.analogue_event_id].to_numpy()
                    all_values.extend(donor_arrays[arm])
                upper = np.nanmax(all_values) * 1.05
                for column, arm in enumerate(arms):
                    ax = axes[row, column]
                    for curve in donor_arrays[arm]:
                        ax.plot(np.arange(1, 73), curve, color="#2878b5", alpha=0.3, lw=0.65)
                    ax.plot(np.arange(1, 73), observations, color="black", lw=1.3)
                    ax.axhline(1, color="grey", ls=":", lw=0.5)
                    ax.set_ylim(0, upper)
                    ax.set_xlim(1, 72)
                    record = group.loc[group.query_event_id.eq(event_id) & group.arm.eq(arm)].iloc[
                        0
                    ]
                    name = f"{record.query_watercourse} {record.query_gauge} {str(record.query_onset_utc)[:16]}"
                    ax.set_title(
                        f"{name} | {arm}\nshape {record.mean_peak_scaled_shape_rmse:.3f}; time {record.mean_peak_time_difference_h:.1f}h; flags {record.flagged_pair_share:.0%}",
                        fontsize=7,
                    )
                    ax.tick_params(labelsize=6)
                    if column == 0:
                        ax.set_ylabel("Q / own-era p99", fontsize=7)
                    if row == len(selected_ids) - 1:
                        ax.set_xlabel("Hours 1–72 after onset", fontsize=7)
                query_links.append(
                    {
                        "cohort": cohort,
                        "query_event_id": event_id,
                        "atlas_page": f"atlas/{cohort}_{page:03d}.png",
                        "page_row": row + 1,
                    }
                )
            fig.suptitle(
                f"{cohort}: complete chronological census, page {page} | black=query; blue=each actual donor",
                fontsize=11,
            )
            fig.tight_layout(rect=(0, 0, 1, 0.985))
            path = atlas / f"{cohort}_{page:03d}.png"
            fig.savefig(path, dpi=120)
            plt.close(fig)
            pages.append(
                {
                    "cohort": cohort,
                    "page": page,
                    "path": str(path.relative_to(out)),
                    "queries": len(selected_ids),
                }
            )
            print(f"Atlas {cohort} {page}", flush=True)
    pd.DataFrame(pages).to_csv(out / "atlas_pages.csv", index=False)
    links = pd.DataFrame(query_links)
    links.to_csv(out / "atlas_query_index.csv", index=False)
    table = sets.loc[sets.analysis.eq("main")].merge(
        links, on=["cohort", "query_event_id"], validate="many_to_one"
    )
    table["plot"] = table.atlas_page.map(lambda x: f'<a href="{html.escape(x)}">plot</a>')
    columns = [
        "cohort",
        "query_onset_utc",
        "query_watercourse",
        "query_gauge",
        "arm",
        "plot",
        "page_row",
        "mean_peak_scaled_shape_rmse",
        "mean_pool_percentile_peak_scaled_shape_rmse",
        "mean_peak_time_difference_h",
        "query_high_water_hours",
        "flagged_pair_share",
    ]
    content = '<!doctype html><meta charset="utf-8"><title>Limburg analogue census</title><style>body{font:14px sans-serif;margin:24px}td,th{padding:5px;border-bottom:1px solid #ddd}th{position:sticky;top:0;background:white}</style><h1>All retrieved main-run analogue sets</h1><p>Use browser Find for a date, gauge or river. Each linked plot shows the query and all five actual donors. Chronological census; no hand-picked cases. Metrics are exploratory diagnostics, not human relevance verdicts.</p>'
    (out / "index.html").write_text(
        content
        + table[columns].to_html(index=False, escape=False, float_format=lambda x: f"{x:.3f}")
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument(
        "--no-atlas", action="store_true", help="Reproduce tables without rendering plots"
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    samples, _, index, windows = REVIEW.load_inputs()
    pairs_path = ROOT / "results/basin_ai_step6/all_pair_provenance.csv"
    pairs = pd.read_csv(pairs_path, low_memory=False)
    response, history, coverage = load_curves(index, windows)
    assessed, pools, sets = review_all_sets(pairs, samples, response, history, coverage)
    assert len(assessed) == len(pairs)
    coverage["retrieved_as_query"] = coverage.index.isin(pairs.query_event_id)
    coverage["retrieved_as_donor"] = coverage.index.isin(pairs.analogue_event_id)
    coverage.to_csv(args.output_dir / "event_coverage.csv")
    assessed.to_csv(args.output_dir / "all_selected_pair_diagnostics.csv", index=False)
    pools.to_csv(args.output_dir / "complete_prior_pool_reference.csv", index=False)
    sets.to_csv(args.output_dir / "all_query_set_diagnostics.csv", index=False)
    summary = summarize_sets(sets)
    summary.to_csv(args.output_dir / "cohort_summary.csv", index=False)
    intervals, contrasts = paired_metric_intervals(sets)
    intervals.to_csv(args.output_dir / "paired_metric_intervals.csv", index=False)
    contrasts.to_csv(args.output_dir / "paired_query_diagnostics.csv", index=False)
    plot_census_summary(summary, sets, args.output_dir)
    for name, columns in [
        ("river_summary", ["query_watercourse"]),
        ("country_summary", ["query_country"]),
        ("query_quality_summary", ["query_measurement_concern"]),
    ]:
        keys = ["cohort", "analysis", "arm"] + columns
        quantities = [c for c in summary if c.startswith(("mean_", "best_selected_"))]
        grouped = sets.groupby(keys)[quantities].mean().reset_index()
        counts = sets.groupby(keys).size().rename("query_sets").reset_index()
        grouped.merge(counts, on=keys).to_csv(args.output_dir / f"{name}.csv", index=False)
    if not args.no_atlas:
        make_atlas(assessed, sets, response, args.output_dir)
    paths = [Path(__file__), pairs_path]
    paths.extend(
        ROOT / "scripts" / filename
        for filename in [
            "65_hydrological_analogue_baseline.py",
            "69_raw_hydrograph_analogue_baseline.py",
            "70_ttm_analogue_comparison.py",
            "71_alphaearth_analogue_increment.py",
            "73_analogue_uncertainty_review.py",
        ]
    )
    for directory in [
        "basin_ai_event_library",
        "basin_ai_german_extension",
        "basin_ai_alphaearth",
        "basin_ai_raw_hydrograph",
        "basin_ai_ttm",
    ]:
        for pattern in ["*.csv", "*.parquet"]:
            paths.extend(sorted((ROOT / "results" / directory).glob(pattern)))
    manifest = {
        "status": "complete numerical census; qualitative/human judgments are separate",
        "scope": "exploratory after peak-only results; fixed existing retrievals; no reranking",
        "episodes": len(index),
        "selected_slots": len(pairs),
        "unique_query_events": pairs.query_event_id.nunique(),
        "unique_selected_query_donor_pairs": len(
            pairs[["query_event_id", "analogue_event_id"]].drop_duplicates()
        ),
        "evaluated_query_sets": len(sets),
        "prior_pool_queries": len(pools),
        "reference_candidate_slots": int(pools.candidate_events.sum()),
        "pool_weighting": "equal total weight per prior storm; equal events within storm; percentile ties half weight",
        "outcome_window": "hours 1–72; fixed onset-centered segment, not necessarily an entire flood",
        "metrics": METRICS,
        "human_validation": False,
        "input_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
    }
    (args.output_dir / "summary.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "input_sha256"}, indent=2))


if __name__ == "__main__":
    main()
