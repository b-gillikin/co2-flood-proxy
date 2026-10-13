#!/usr/bin/env python3
"""Paired archive-conditional uncertainty, river influence and analogue provenance."""

from __future__ import annotations

import argparse
import hashlib
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
    "context_increment", ROOT / "scripts/71_alphaearth_analogue_increment.py"
)
CONTEXT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTEXT)
BASE = CONTEXT.TTM.RAW.BASELINE
OUT = ROOT / "results/basin_ai_step6"
SEED = 20261013
DRAWS = 9999
COHORTS = {
    "dutch": ("basin_ai_ttm", ["r0", "r1", "r2"], [("r1", "r2"), ("r0", "r2")]),
    "context": (
        "basin_ai_alphaearth_increment",
        ["r2", "r2_area", "r3_alphaearth"],
        [("r2", "r3_alphaearth"), ("r2_area", "r3_alphaearth")],
    ),
    "pooled": ("basin_ai_german_extension", ["r1", "r2"], [("r1", "r2")]),
}


def paired_errors(reference, challenger):
    keys = ["query_event_id", "query_storm_id", "query_onset_utc", "query_watercourse"]
    if set(reference.query_event_id) != set(challenger.query_event_id):
        raise ValueError("Paired scores require identical query IDs")
    result = reference.merge(
        challenger, on="query_event_id", suffixes=("_ref", "_test"), validate="one_to_one"
    )
    for column in keys[1:] + [
        "candidate_count",
        "candidate_storm_count",
        "observed_peak_over_p99_72h",
    ]:
        if not result[f"{column}_ref"].eq(result[f"{column}_test"]).all():
            raise ValueError(f"Paired scores differ in {column}")
    result["difference"] = result.analogue_absolute_error_test - result.analogue_absolute_error_ref
    for key in keys[1:]:
        result[key] = result[f"{key}_ref"]
    return result[keys + ["difference"]]


def cluster_interval(frame, cluster, draws=DRAWS, seed=SEED):
    """Resample intact query clusters, preserving the event-weighted mean difference."""
    if frame.empty or frame.difference.isna().any() or frame[cluster].isna().any():
        raise ValueError("Complete paired differences and cluster labels required")
    grouped = frame.groupby(cluster, sort=True).difference.agg(["sum", "size"])
    if len(grouped) < 2:
        raise ValueError("At least two query clusters required for a sampling interval")
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, len(grouped), size=(draws, len(grouped)))
    values = grouped["sum"].to_numpy()[picks].sum(axis=1) / grouped["size"].to_numpy()[picks].sum(
        axis=1
    )
    return {
        "difference": float(frame.difference.mean()),
        "lower": float(np.quantile(values, 0.025)),
        "upper": float(np.quantile(values, 0.975)),
        "query_count": len(frame),
        "cluster_count": len(grouped),
        "draws": draws,
        "finite_draws": int(np.isfinite(values).sum()),
    }


def read_predictions(directory, analysis, arm):
    return pd.read_csv(
        ROOT / "results" / directory / f"{analysis}_{arm}_predictions.csv",
        parse_dates=["query_onset_utc"],
    )


def all_uncertainty(out):
    intervals, by_river, paired = [], [], []
    for cohort, (directory, arms, contrasts) in COHORTS.items():
        for analysis in ["main", "quality_sensitivity"]:
            predictions = {arm: read_predictions(directory, analysis, arm) for arm in arms}
            median = predictions[arms[0]].copy()
            median["analogue_absolute_error"] = median.median_absolute_error
            predictions["historical_median"] = median
            for reference, challenger in contrasts + [("historical_median", arm) for arm in arms]:
                errors = paired_errors(predictions[reference], predictions[challenger])
                # Assign a boundary-spanning storm wholly to its first query year.
                first = errors.groupby("query_storm_id").query_onset_utc.transform("min")
                errors["storm_year"] = first.dt.year
                identifiers = {
                    "cohort": cohort,
                    "analysis": analysis,
                    "reference": reference,
                    "challenger": challenger,
                }
                for cluster in ["query_storm_id", "storm_year"]:
                    intervals.append(
                        {
                            **identifiers,
                            "resampling_unit": cluster,
                            **cluster_interval(errors, cluster),
                        }
                    )
                paired.append(errors.assign(**identifiers))
                for watercourse, group in errors.groupby("query_watercourse"):
                    by_river.append(
                        {
                            **identifiers,
                            "watercourse": watercourse,
                            "queries": len(group),
                            "storms": group.query_storm_id.nunique(),
                            "difference": group.difference.mean(),
                        }
                    )
    pd.DataFrame(intervals).to_csv(out / "paired_intervals.csv", index=False)
    pd.DataFrame(by_river).to_csv(out / "differences_by_watercourse.csv", index=False)
    pd.concat(paired, ignore_index=True).to_csv(out / "paired_errors.csv", index=False)
    return pd.DataFrame(intervals)


def load_inputs():
    dutch = pd.read_csv(
        ROOT / "results/basin_ai_event_library/event_index.csv", parse_dates=["onset_utc"]
    )
    windows = pd.read_parquet(ROOT / "results/basin_ai_event_library/event_windows.parquet")
    signatures = BASE.build_signatures(dutch, windows)
    raw = pd.read_parquet(ROOT / "results/basin_ai_raw_hydrograph/standardized_histories.parquet")
    ttm = pd.read_parquet(ROOT / "results/basin_ai_ttm/event_embeddings.parquet")
    joined = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/event_embeddings.parquet")
    context_ids = joined.loc[joined.alphaearth_input_sample]
    blocks = CONTEXT.context_blocks(context_ids, ttm)
    pooled = pd.read_csv(
        ROOT / "results/basin_ai_german_extension/pooled_event_index.csv", parse_dates=["onset_utc"]
    )
    german_windows = pd.read_parquet(
        ROOT / "results/basin_ai_german_extension/german_event_windows.parquet"
    )
    combined_windows = pd.concat([windows, german_windows], ignore_index=True)
    pooled_signatures = BASE.build_signatures(pooled, combined_windows)
    for frame in [signatures, pooled_signatures]:
        frame["river_group"] = frame.watercourse.replace({"Worm": "Wurm/Worm", "Wurm": "Wurm/Worm"})
    samples = {
        "dutch": signatures,
        "context": signatures.loc[signatures.event_id.isin(context_ids.event_id)].copy(),
        "pooled": pooled_signatures,
    }
    representations = {
        "dutch": {
            "r0": {},
            "r1": {"representation_vectors": raw},
            "r2": {"representation_vectors": ttm},
        },
        "context": {
            "r2": {"distance_blocks": {"ttm": blocks["ttm"]}},
            "r2_area": {"distance_blocks": {k: blocks[k] for k in ["ttm", "area"]}},
            "r3_alphaearth": {"distance_blocks": {k: blocks[k] for k in ["ttm", "alphaearth"]}},
        },
        "pooled": {
            "r1": {
                "representation_vectors": pd.concat(
                    [
                        raw,
                        pd.read_parquet(
                            ROOT
                            / "results/basin_ai_german_extension/german_standardized_histories.parquet"
                        ),
                    ]
                )
            },
            "r2": {
                "representation_vectors": pd.concat(
                    [
                        ttm,
                        pd.read_parquet(
                            ROOT / "results/basin_ai_german_extension/german_ttm_embeddings.parquet"
                        ),
                    ]
                )
            },
        },
    }
    return samples, representations, pooled, combined_windows


def river_influence(samples, representations, out):
    rows = []
    predictions = []
    for cohort, signatures in samples.items():
        directory, arms, contrasts = COHORTS[cohort]
        for analysis in ["main", "quality_sensitivity"]:
            full = {arm: read_predictions(directory, analysis, arm) for arm in arms}
            for removed in sorted(signatures.river_group.unique()):
                reduced = signatures.loc[signatures.river_group.ne(removed)]
                fitted = {}
                for arm in arms:
                    prediction, _ = BASE.retrieve_prior_analogues(
                        reduced,
                        top_k=5,
                        min_candidates=20,
                        exclude_measurement_concerns=analysis == "quality_sensitivity",
                        **representations[cohort][arm],
                    )
                    fitted[arm] = prediction
                    predictions.append(
                        prediction.assign(
                            cohort=cohort, analysis=analysis, removed_river=removed, arm=arm
                        )
                    )
                for reference, challenger in contrasts:
                    errors = paired_errors(fitted[reference], fitted[challenger])
                    ids = set(errors.query_event_id)
                    original = paired_errors(
                        full[reference].loc[full[reference].query_event_id.isin(ids)],
                        full[challenger].loc[full[challenger].query_event_id.isin(ids)],
                    )
                    if len(original) != len(errors):
                        raise ValueError("Reduced query set must be a subset of the full run")
                    rows.append(
                        {
                            "cohort": cohort,
                            "analysis": analysis,
                            "removed_river": removed,
                            "reference": reference,
                            "challenger": challenger,
                            "queries": len(errors),
                            "storms": errors.query_storm_id.nunique(),
                            "refit_difference": errors.difference.mean(),
                            "full_library_same_query_difference": original.difference.mean(),
                            "lost_queries": len(full[reference]) - len(errors),
                        }
                    )
                print(f"{cohort}/{analysis}: removed {removed}", flush=True)
    pd.DataFrame(rows).to_csv(out / "leave_one_river_out.csv", index=False)
    pd.concat(predictions, ignore_index=True).to_csv(
        out / "leave_one_river_predictions.csv", index=False
    )


def metadata_with_review(pooled):
    review = pd.read_csv(ROOT / "results/event_study/real_data_v1/event_analysis_status.csv")
    extra = [
        "event_id",
        "era_id",
        "peak_outside_rating_domain",
        "nearby_gap",
        "nearby_era_change",
        "provider_july_concern",
        "gulp_above_documented_calibration",
        "review_flags",
        "decision_basis",
    ]
    meta = pooled.merge(review[extra], on="event_id", how="left", validate="one_to_one").set_index(
        "event_id"
    )
    meta["rating_identity"] = meta.rating_era.fillna(meta.era_id)
    return meta


def read_neighbors(cohort, directory, analysis, arm):
    if cohort == "dutch" and arm in ["r0", "r1"]:
        base = "basin_ai_analogue_baseline" if arm == "r0" else "basin_ai_raw_hydrograph"
        name = (
            "analogue_neighbors.csv" if analysis == "main" else "quality_sensitivity_neighbors.csv"
        )
        result = pd.read_csv(ROOT / "results" / base / name)
    else:
        result = pd.read_csv(ROOT / "results" / directory / f"{analysis}_{arm}_neighbors.csv")
    queries = read_predictions(directory, analysis, arm)
    if set(result.query_event_id) != set(queries.query_event_id):
        raise ValueError("Neighbor file differs from evaluated query cohort")
    if not result.groupby("query_event_id").size().eq(5).all():
        raise ValueError("Every evaluated query needs five selected donors")
    return result


def audit_neighbors(metadata, out):
    all_pairs, summaries = [], []
    for cohort, (directory, arms, _) in COHORTS.items():
        for analysis in ["main", "quality_sensitivity"]:
            for arm in arms:
                neighbors = read_neighbors(cohort, directory, analysis, arm)
                for role, column in [
                    ("query", "query_event_id"),
                    ("analogue", "analogue_event_id"),
                ]:
                    for attribute in [
                        "gauge",
                        "country",
                        "physical_river_group",
                        "rating_identity",
                        "measurement_concern",
                        "provider_status",
                        "peak_outside_rating_domain",
                        "nearby_gap",
                        "provisional_high_flow",
                        "p99_m3s",
                        "rain_sum_24h_mm",
                        "rain_sum_72h_mm",
                        "outcome_peak_over_p99_72h",
                        "outcome_time_to_peak_h",
                    ]:
                        neighbors[f"{role}_{attribute}"] = neighbors[column].map(
                            metadata[attribute]
                        )
                neighbors["same_gauge"] = neighbors.query_gauge.eq(neighbors.analogue_gauge)
                neighbors["same_river"] = neighbors.query_physical_river_group.eq(
                    neighbors.analogue_physical_river_group
                )
                neighbors["cross_country"] = neighbors.query_country.ne(neighbors.analogue_country)
                neighbors["measurement_concern_pair"] = (
                    neighbors.query_measurement_concern | neighbors.analogue_measurement_concern
                )
                neighbors["provisional_pair"] = neighbors.query_provisional_high_flow.fillna(
                    False
                ).astype(bool) | neighbors.analogue_provisional_high_flow.fillna(False).astype(bool)
                counts = neighbors.analogue_storm_id.value_counts()
                summaries.append(
                    {
                        "cohort": cohort,
                        "analysis": analysis,
                        "arm": arm,
                        "pairs": len(neighbors),
                        "unique_query_storms": neighbors.query_storm_id.nunique(),
                        "unique_donor_storms": len(counts),
                        "largest_donor_storm_slots": int(counts.max()),
                        "largest_donor_storm_slot_fraction": counts.max() / len(neighbors),
                        "same_gauge_pairs": int(neighbors.same_gauge.sum()),
                        "same_river_pairs": int(neighbors.same_river.sum()),
                        "cross_country_pairs": int(neighbors.cross_country.sum()),
                        "measurement_concern_pairs": int(neighbors.measurement_concern_pair.sum()),
                        "provisional_pairs": int(neighbors.provisional_pair.sum()),
                    }
                )
                all_pairs.append(neighbors.assign(cohort=cohort, analysis=analysis, arm=arm))
    pairs = pd.concat(all_pairs, ignore_index=True)
    pairs.to_csv(out / "all_pair_provenance.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "provenance_summary.csv", index=False)
    pairs.groupby(["cohort", "analysis", "arm", "analogue_storm_id"], as_index=False).size().rename(
        columns={"size": "donor_slots"}
    ).to_csv(out / "donor_storm_reuse.csv", index=False)
    return pairs


def choose_cases(paired, metadata):
    ordered = paired.sort_values(["query_onset_utc", "query_event_id"]).copy()
    selected = []
    for reason in [
        "largest_improvement",
        "largest_deterioration",
        "median_difference",
        "measurement_concern",
    ]:
        remaining = ordered.loc[
            ~ordered.query_event_id.isin([x["query_event_id"] for x in selected])
        ].copy()
        if reason == "largest_improvement":
            row = remaining.sort_values("difference", kind="stable").iloc[0]
        elif reason == "largest_deterioration":
            row = remaining.sort_values("difference", ascending=False, kind="stable").iloc[0]
        elif reason == "median_difference":
            row = (
                remaining.assign(
                    deviation=(remaining.difference - ordered.difference.median()).abs()
                )
                .sort_values("deviation", kind="stable")
                .iloc[0]
            )
        else:
            flagged = remaining.loc[remaining.query_event_id.map(metadata.measurement_concern)]
            row = flagged.iloc[0] if not flagged.empty else remaining.iloc[0]
            reason = reason if not flagged.empty else "earliest_remaining"
        selected.append(
            {
                "query_event_id": row.query_event_id,
                "selection_reason": reason,
                "difference": row.difference,
            }
        )
    return pd.DataFrame(selected)


def review_packet(pairs, metadata, windows, out):
    cases = []
    plots = out / "review_plots"
    plots.mkdir(exist_ok=True)
    window_groups = {
        key: group.sort_values("relative_hour") for key, group in windows.groupby("event_id")
    }
    for cohort, (directory, _, contrasts) in COHORTS.items():
        reference, challenger = contrasts[0]
        errors = paired_errors(
            read_predictions(directory, "main", reference),
            read_predictions(directory, "main", challenger),
        )
        selected = choose_cases(errors, metadata)
        if cohort == "pooled":
            # The initial global examples are all NL. Include two explicitly
            # illustrative DE cases so the cross-border review covers both sides.
            german = errors.loc[errors.query_event_id.map(metadata.country).eq("DE")].copy()
            german = german.sort_values(["query_onset_utc", "query_event_id"])
            median = (
                german.assign(deviation=(german.difference - german.difference.median()).abs())
                .sort_values("deviation", kind="stable")
                .iloc[0]
            )
            extreme = (
                german.loc[german.query_event_id.ne(median.query_event_id)]
                .assign(magnitude=lambda x: x.difference.abs())
                .sort_values("magnitude", ascending=False, kind="stable")
                .iloc[0]
            )
            selected = pd.concat(
                [
                    selected,
                    pd.DataFrame(
                        [
                            {
                                "query_event_id": median.query_event_id,
                                "selection_reason": "German_median_difference",
                                "difference": median.difference,
                            },
                            {
                                "query_event_id": extreme.query_event_id,
                                "selection_reason": "German_largest_absolute_difference",
                                "difference": extreme.difference,
                            },
                        ]
                    ),
                ],
                ignore_index=True,
            )
        for number, case in enumerate(selected.itertuples(), start=1):
            case_id = f"{cohort}_{number:02d}"
            fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
            axes[2].sharey(axes[1])

            def q_array(event_id, history=False):
                frame = window_groups[event_id]
                values = frame.target_discharge_m3s.to_numpy(dtype=float)
                if history:
                    hist = values[frame.relative_hour.le(0)]
                    return frame.relative_hour.to_numpy(), (values - hist.mean()) / (
                        hist.std() or 1.0
                    )
                return frame.relative_hour.to_numpy(), values / float(
                    metadata.loc[event_id, "p99_m3s"]
                )

            hx, hy = q_array(case.query_event_id, True)
            rx, ry = q_array(case.query_event_id)
            axes[0].plot(hx[hx <= 0], hy[hx <= 0], color="black", lw=1.8, label="Query")
            for ax in axes[1:]:
                ax.plot(rx[(rx >= 0)], ry[rx >= 0], color="black", lw=2, label="Query")
                ax.axhline(1.0, color="grey", ls=":", lw=0.8)
            for index, (arm, color) in enumerate(
                [(reference, "#2878b5"), (challenger, "#d95f02")], start=1
            ):
                donors = pairs.loc[
                    pairs.cohort.eq(cohort)
                    & pairs.analysis.eq("main")
                    & pairs.arm.eq(arm)
                    & pairs.query_event_id.eq(case.query_event_id)
                ]
                histories, responses = [], []
                for donor in donors.itertuples():
                    _, history = q_array(donor.analogue_event_id, True)
                    _, response = q_array(donor.analogue_event_id)
                    histories.append(history)
                    responses.append(response)
                    axes[index].plot(
                        rx[rx >= 0], response[rx >= 0], color=color, alpha=0.25, lw=0.8
                    )
                axes[0].plot(
                    hx[hx <= 0],
                    np.mean(histories, axis=0)[hx <= 0],
                    color=color,
                    label=f"{arm}: donor mean",
                )
                axes[index].plot(
                    rx[rx >= 0],
                    np.mean(responses, axis=0)[rx >= 0],
                    color=color,
                    lw=1.6,
                    label="Donor curve mean",
                )
                axes[index].set_title(f"{arm}: five earlier storms")
                prediction = (
                    read_predictions(directory, "main", arm)
                    .set_index("query_event_id")
                    .loc[case.query_event_id]
                )
                axes[index].text(
                    0.02,
                    0.97,
                    f"Mean donor peak={prediction.analogue_prediction:.2f}\nObserved peak={prediction.observed_peak_over_p99_72h:.2f}",
                    transform=axes[index].transAxes,
                    va="top",
                    fontsize=8,
                )
            axes[0].set(
                title="Standardized 512-hour histories",
                ylabel="Within-history standard deviations",
                xlabel="Hours relative to onset",
            )
            for ax in axes[1:]:
                ax.set(xlabel="Hours after onset", ylabel="Discharge / own rating-era p99")
            for ax in axes:
                ax.legend(fontsize=7, loc="lower right")
                ax.grid(alpha=0.15)
            title = f"{case_id} | {metadata.loc[case.query_event_id, 'watercourse']} | {metadata.loc[case.query_event_id, 'onset_utc']} | {case.selection_reason}"
            fig.suptitle(title, fontsize=10)
            fig.tight_layout()
            fig.savefig(plots / f"{case_id}.png", dpi=150)
            plt.close(fig)
            cases.append(
                {
                    "case_id": case_id,
                    "cohort": cohort,
                    "reference": reference,
                    "challenger": challenger,
                    "query_event_id": case.query_event_id,
                    "selection_reason": case.selection_reason,
                    "paired_error_difference": case.difference,
                    "query_watercourse": metadata.loc[case.query_event_id, "watercourse"],
                    "query_measurement_concern": metadata.loc[
                        case.query_event_id, "measurement_concern"
                    ],
                    "figure": f"review_plots/{case_id}.png",
                    "human_relevance_verdict": "",
                    "human_reason": "",
                    "reviewer": "",
                    "review_date": "",
                }
            )
    case_table = pd.DataFrame(cases)
    review_path = out / "human_review_cases.csv"
    if review_path.exists():
        previous = pd.read_csv(review_path).fillna("")
        human_columns = ["human_relevance_verdict", "human_reason", "reviewer", "review_date"]
        written = previous.loc[previous[human_columns].ne("").any(axis=1)]
        if not written.empty:
            keys = ["cohort", "query_event_id"]
            if not set(map(tuple, written[keys].to_numpy())).issubset(
                set(map(tuple, case_table[keys].to_numpy()))
            ):
                raise ValueError(
                    "Case selection changed: preserve completed human reviews before regenerating"
                )
            case_table = (
                case_table.drop(columns=human_columns)
                .merge(written[keys + human_columns], on=keys, how="left", validate="one_to_one")
                .fillna("")
            )
    case_table.to_csv(review_path, index=False)
    pair_subset = pairs.merge(
        pd.DataFrame(cases)[["cohort", "query_event_id", "case_id"]],
        on=["cohort", "query_event_id"],
        how="inner",
    )
    pair_subset.loc[pair_subset.analysis.eq("main")].to_csv(
        out / "review_case_pairs.csv", index=False
    )


def plot_intervals(intervals, out):
    focus = intervals.loc[
        intervals.analysis.eq("main") & intervals.reference.ne("historical_median")
    ].copy()
    labels = focus[["cohort", "reference", "challenger"]].drop_duplicates()
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, row in enumerate(labels.itertuples()):
        subset = focus.loc[
            focus.cohort.eq(row.cohort)
            & focus.reference.eq(row.reference)
            & focus.challenger.eq(row.challenger)
        ]
        for offset, unit, color in [
            (-0.1, "query_storm_id", "#2878b5"),
            (0.1, "storm_year", "#d95f02"),
        ]:
            value = subset.loc[subset.resampling_unit.eq(unit)].iloc[0]
            ax.plot([value.lower, value.upper], [i + offset] * 2, color=color, lw=2)
            ax.plot(value.difference, i + offset, "o", color=color, label=unit if i == 0 else None)
    ax.axvline(0, color="black", lw=0.7)
    ax.set_yticks(
        range(len(labels)),
        [f"{r.cohort}: {r.challenger} minus {r.reference}" for r in labels.itertuples()],
    )
    ax.set_xlabel(
        "Paired MAE difference; negative favors challenger\n95% percentile intervals conditional on the held archive"
    )
    ax.legend()
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / "paired_uncertainty.png", dpi=180)
    fig.savefig(out / "paired_uncertainty.svg")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    intervals = all_uncertainty(args.output_dir)
    samples, representations, pooled, windows = load_inputs()
    river_influence(samples, representations, args.output_dir)
    metadata = metadata_with_review(pooled)
    metadata = metadata.join(
        samples["pooled"].set_index("event_id")[
            [
                "rain_sum_24h_mm",
                "rain_sum_72h_mm",
                "outcome_peak_over_p99_72h",
                "outcome_time_to_peak_h",
            ]
        ]
    )
    pairs = audit_neighbors(metadata, args.output_dir)
    review_packet(pairs, metadata, windows, args.output_dir)
    plot_intervals(intervals, args.output_dir)
    paths = [
        Path(__file__),
        ROOT / "scripts/65_hydrological_analogue_baseline.py",
        ROOT / "scripts/71_alphaearth_analogue_increment.py",
        ROOT / "docs/ai-eval/basin-graph.json",
        ROOT / "results/event_study/real_data_v1/event_analysis_status.csv",
    ]
    for directory, _, _ in COHORTS.values():
        paths.extend(sorted((ROOT / "results" / directory).glob("*.csv")))
        paths.append(ROOT / "results" / directory / "summary.json")
    for directory in [
        "basin_ai_event_library",
        "basin_ai_analogue_baseline",
        "basin_ai_raw_hydrograph",
    ]:
        paths.extend(sorted((ROOT / "results" / directory).glob("*.csv")))
    for directory in [
        "basin_ai_event_library",
        "basin_ai_alphaearth",
        "basin_ai_raw_hydrograph",
        "basin_ai_ttm",
        "basin_ai_german_extension",
    ]:
        paths.extend(sorted((ROOT / "results" / directory).glob("*.parquet")))
    summary = {
        "status": "paired uncertainty, river exclusion refits and automated pair review executed; human verdicts pending",
        "seed": SEED,
        "draws": DRAWS,
        "interval_scope": "fixed-archive query sampling; donor/measurement/pretraining uncertainty not covered",
        "leave_one_river": "remove both queries and donors; refit distances/scales; compare common surviving queries",
        "review_selection": "14 outcome-informed illustrations including two German examples; cannot estimate relevance accuracy",
        "input_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(summary["status"], flush=True)


if __name__ == "__main__":
    main()
