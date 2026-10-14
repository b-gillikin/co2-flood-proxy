#!/usr/bin/env python3
"""Exploratory cross-river, donor-count, disagreement and matched fusion checks.

No outcomes enter retrieval. Fixed k=3/5/10, equal block weights, same queries
within each donor-availability scenario. Historical assessment, not forecasting.
"""

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
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "strengthen", ROOT / "scripts/75_strengthen_foundation_representations.py"
)
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)
BASE, CENSUS, REVIEW = S.BASE, S.CENSUS, S.REVIEW
OUT = ROOT / "results/basin_ai_cross_river_checks"
METRICS = [
    "mean_peak_scaled_shape_rmse",
    "mean_donor_peak_absolute_error",
    "ensemble_curve_level_rmse",
    "mean_peak_time_difference_h",
]


def assess(scores, donors, response, metadata):
    """Score all selected donors and uncertainty without modifying their ranks."""
    rows, pairs = [], []
    score_index = scores.set_index("query_event_id")
    for qid, group in donors.groupby("query_event_id", sort=True):
        ids = group.analogue_event_id.tolist()
        q = response.loc[qid].to_numpy()
        d = response.loc[ids].to_numpy()
        metrics = CENSUS.response_distances(q, d)
        group = group.reset_index(drop=True).copy()
        for metric in CENSUS.METRICS:
            group[metric] = metrics[metric]
        group["query_river"] = metadata.loc[qid, "physical_river_group"]
        group["analogue_river"] = metadata.loc[ids, "physical_river_group"].to_numpy()
        group["cross_country"] = (
            metadata.loc[ids, "country"].to_numpy() != metadata.loc[qid, "country"]
        )
        peaks = d.max(axis=1)
        # Descriptive donor spread: computable from completed prior outcomes.
        shape = d / peaks[:, None]
        row = {
            "query_event_id": qid,
            **score_index.loc[qid].to_dict(),
            "query_river": metadata.loc[qid, "physical_river_group"],
            "query_country": metadata.loc[qid, "country"],
            "query_measurement_concern": bool(metadata.loc[qid, "measurement_concern"]),
            "mean_donor_peak_absolute_error": abs(peaks.mean() - q.max()),
            "analogue_prediction": float(peaks.mean()),
            "analogue_absolute_error": abs(peaks.mean() - q.max()),
            "ensemble_curve_level_rmse": np.sqrt(np.square(d.mean(axis=0) - q).mean()),
            "peak_spread": peaks.std(ddof=0),
            "curve_spread": np.sqrt(d.var(axis=0, ddof=0).mean()),
            "shape_spread": np.sqrt(shape.var(axis=0, ddof=0).mean()),
            "peak_range_contains_query": bool(peaks.min() <= q.max() <= peaks.max()),
            "same_river_share": group.query_river.eq(group.analogue_river).mean(),
            "cross_country_share": group.cross_country.mean(),
        }
        row.update({f"mean_{metric}": metrics[metric].mean() for metric in CENSUS.METRICS})
        rows.append(row)
        pairs.append(group)
    return pd.DataFrame(rows), pd.concat(pairs, ignore_index=True)


def configurations(arms, samples):
    configs = {}
    for cohort in ["dutch", "pooled", "context"]:
        existing = arms[cohort]
        if cohort == "context":
            configs[cohort] = {
                key: existing[key]
                for key in ["r0", "r1", "r2", "r2_area", "r2_identity", "r3_alphaearth"]
            }
        else:
            keys = ["r1", "raw_state", "ttm_ordered_state"]
            if cohort == "dutch":
                keys.insert(0, "r0")
            configs[cohort] = {key: existing[key] for key in keys}
        if cohort in ["dutch", "context"]:
            # Identical conventional block in both fusion arms; no weight tuning.
            conventional = samples[cohort].set_index("event_id")[BASE.FEATURE_COLUMNS]
            for name, source in [("fusion_raw", "r1"), ("fusion_ttm", "ttm_ordered")]:
                vector = arms["dutch"][source]["representation_vectors"]
                configs[cohort][name] = {
                    "distance_blocks": {"conventional": conventional, "temporal": vector},
                    "robust_distance_blocks": ("conventional",),
                }
    return configs


def intervals(sets):
    rows = []
    comparisons = {
        "dutch": [
            ("raw_state", "ttm_ordered_state"),
            ("r0", "ttm_ordered_state"),
            ("r0", "fusion_raw"),
            ("r0", "fusion_ttm"),
            ("fusion_raw", "fusion_ttm"),
        ],
        "pooled": [("raw_state", "ttm_ordered_state")],
        "context": [
            ("r2", "r3_alphaearth"),
            ("r2_area", "r3_alphaearth"),
            ("r2_identity", "r3_alphaearth"),
            ("r0", "r3_alphaearth"),
            ("r0", "fusion_ttm"),
            ("fusion_raw", "fusion_ttm"),
        ],
    }
    for (cohort, scenario, analysis), group in sets.groupby(["cohort", "scenario", "analysis"]):
        contrasts = [(5, a, 5, b) for a, b in comparisons[cohort]]
        contrasts += [(5, arm, k, arm) for arm in group.arm.unique() for k in [3, 10]]
        for rk, reference, tk, challenger in contrasts:
            ref = group.loc[group.arm.eq(reference) & group.k.eq(rk)].set_index("query_event_id")
            test = group.loc[group.arm.eq(challenger) & group.k.eq(tk)].set_index("query_event_id")
            if set(ref.index) != set(test.index):
                raise ValueError("Paired comparison changes query identities")
            test = test.loc[ref.index]
            delta = ref[["query_storm_id", "query_onset_utc"]].copy()
            first = delta.groupby("query_storm_id").query_onset_utc.transform("min")
            delta["storm_year"] = pd.to_datetime(first, utc=True).dt.year
            for metric in METRICS:
                delta["difference"] = test[metric] - ref[metric]
                for unit in ["query_storm_id", "storm_year"]:
                    rows.append(
                        {
                            "cohort": cohort,
                            "scenario": scenario,
                            "analysis": analysis,
                            "reference": reference,
                            "challenger": challenger,
                            "reference_k": rk,
                            "challenger_k": tk,
                            "metric": metric,
                            "resampling_unit": unit,
                            **REVIEW.cluster_interval(delta, unit),
                        }
                    )
    return pd.DataFrame(rows)


def disagreement_audit(sets, response, coverage, donors, out):
    """Census of differences; illustrations explicitly outcome-selected."""
    rows = []
    comparisons = {
        "dutch": ("r0", "ttm_ordered_state"),
        "pooled": ("raw_state", "ttm_ordered_state"),
        "context": ("r0", "r3_alphaearth"),
    }
    for (cohort, scenario, analysis), group in sets.loc[sets.k.eq(5)].groupby(
        ["cohort", "scenario", "analysis"]
    ):
        a, b = comparisons[cohort]
        ref = group.loc[group.arm.eq(a)].set_index("query_event_id")
        test = group.loc[group.arm.eq(b)].set_index("query_event_id").loc[ref.index]
        delta = ref[
            [
                "query_storm_id",
                "query_onset_utc",
                "query_river",
                "query_country",
                "query_measurement_concern",
            ]
        ].copy()
        for metric in METRICS:
            delta[f"difference_{metric}"] = test[metric] - ref[metric]
        for col in [
            "peak_time_h",
            "high_water_duration_h",
            "ends_above_p99",
            "antecedent_rain_72h_mm",
            "response_rain_72h_mm",
        ]:
            delta[col] = coverage.loc[delta.index, col]
        d = delta.difference_mean_peak_scaled_shape_rmse
        delta["shape_direction"] = np.where(
            np.isclose(d, 0), "tie", np.where(d < 0, "challenger_better", "reference_better")
        )
        delta["cohort"], delta["scenario"], delta["analysis"] = cohort, scenario, analysis
        delta["reference"], delta["challenger"] = a, b
        rows.append(delta.reset_index())
    audit = pd.concat(rows, ignore_index=True)
    audit.to_csv(out / "all_disagreements.csv", index=False)
    columns = ["cohort", "scenario", "analysis", "shape_direction"]
    audit.groupby(columns).agg(
        queries=("query_event_id", "size"),
        mean_query_peak_time=("peak_time_h", "mean"),
        mean_high_water_hours=("high_water_duration_h", "mean"),
        flagged_share=("query_measurement_concern", "mean"),
        mean_antecedent_rain_72h=("antecedent_rain_72h_mm", "mean"),
    ).reset_index().to_csv(out / "disagreement_summary.csv", index=False)
    # Two extremal shape disagreements per cohort/scenario; no relevance-success sample.
    cards = []
    for (cohort, scenario), group in audit.loc[audit.analysis.eq("main")].groupby(
        ["cohort", "scenario"]
    ):
        for direction, ascending in [("challenger_better", True), ("reference_better", False)]:
            chosen = group.sort_values(
                ["difference_mean_peak_scaled_shape_rmse", "query_event_id"],
                ascending=[ascending, True],
            ).iloc[0]
            qid = chosen.query_event_id
            fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), sharey=True)
            for ax, arm in zip(axes, [chosen.reference, chosen.challenger], strict=True):
                selected = donors.loc[
                    donors.cohort.eq(cohort)
                    & donors.scenario.eq(scenario)
                    & donors.analysis.eq("main")
                    & donors.k.eq(5)
                    & donors.arm.eq(arm)
                    & donors.query_event_id.eq(qid)
                ]
                for eid in selected.analogue_event_id:
                    ax.plot(
                        np.arange(1, 73),
                        response.loc[eid],
                        color="steelblue",
                        alpha=0.5,
                        linewidth=1,
                    )
                ax.plot(
                    np.arange(1, 73), response.loc[qid], color="black", linewidth=2, label="query"
                )
                ax.axhline(1, color="grey", linewidth=0.7, linestyle=":")
                ax.set_title(arm)
                ax.set_xlabel("Hours after onset")
            axes[0].set_ylabel("Q / own rating-era p99")
            fig.suptitle(
                f"{cohort}, {scenario}: {qid}\nOutcome-selected illustration: {direction}",
                fontsize=9,
            )
            fig.tight_layout()
            file = f"disagreement_{cohort}_{scenario}_{direction}.png"
            fig.savefig(out / file, dpi=140)
            plt.close(fig)
            cards.append(
                {
                    **chosen.to_dict(),
                    "figure": file,
                    "selection": "extremal signed shape difference; illustrative only",
                }
            )
    pd.DataFrame(cards).to_csv(out / "illustrative_cards.csv", index=False)


def spread_audit(sets):
    rows = []
    for key, group in sets.groupby(["cohort", "scenario", "analysis", "arm", "k"]):
        for spread, error in [
            ("peak_spread", "mean_donor_peak_absolute_error"),
            ("curve_spread", "ensemble_curve_level_rmse"),
            ("shape_spread", "mean_peak_scaled_shape_rmse"),
        ]:
            rho = float(spearmanr(group[spread], group[error]).statistic)
            # Bootstrap whole query storms; dependence on reused donors remains.
            grouped = [
                g[[spread, error]].to_numpy() for _, g in group.groupby("query_storm_id", sort=True)
            ]
            rng = np.random.default_rng(20261013)
            draws = []
            for _ in range(999):
                sample = np.concatenate(
                    [grouped[i] for i in rng.integers(0, len(grouped), len(grouped))]
                )
                draws.append(float(spearmanr(sample[:, 0], sample[:, 1]).statistic))
            if not np.isfinite(draws).all():
                raise ValueError("Undefined donor-spread bootstrap correlation")
            median = group[spread].median()
            low, high = (
                group.loc[group[spread].le(median), error],
                group.loc[group[spread].gt(median), error],
            )
            rows.append(
                dict(zip(["cohort", "scenario", "analysis", "arm", "k"], key, strict=True))
                | {
                    "spread": spread,
                    "error": error,
                    "spearman_rho": rho,
                    "lower": float(np.quantile(draws, 0.025)),
                    "upper": float(np.quantile(draws, 0.975)),
                    "draws": 999,
                    "finite_draws": len(draws),
                    "queries": len(group),
                    "low_spread_mean_error": low.mean(),
                    "high_spread_mean_error": high.mean(),
                }
            )
    return pd.DataFrame(rows)


def additional_checks(sets, donors, response, history, coverage, out):
    keys = ["cohort", "scenario", "analysis", "arm", "query_event_id"]
    if not donors.groupby(keys + ["k"]).size().eq(donors.groupby(keys + ["k"])["k"].first()).all():
        raise ValueError("Wrong prefix size")
    if (
        not donors.groupby(keys + ["k"])
        .analogue_storm_id.nunique()
        .eq(donors.groupby(keys + ["k"])["k"].first())
        .all()
    ):
        raise ValueError("Repeated donor storm")
    for _, group in donors.groupby(keys, sort=False):
        largest = group.loc[group.k.eq(10)].sort_values("rank").analogue_event_id.tolist()
        for k in [3, 5]:
            if (
                group.loc[group.k.eq(k)].sort_values("rank").analogue_event_id.tolist()
                != largest[:k]
            ):
                raise ValueError("Neighborhood is not a nested prefix")
    quality = donors.loc[donors.analysis.eq("quality_sensitivity")]
    for role in ["query_event_id", "analogue_event_id"]:
        if coverage.loc[quality[role], "measurement_concern"].any():
            raise ValueError("Measurement-concern leak into sensitivity")
    if (
        donors.loc[donors.scenario.eq("other_rivers")]
        .query_river.eq(donors.loc[donors.scenario.eq("other_rivers")].analogue_river)
        .any()
    ):
        raise ValueError("Cross-river leak")
    # Original five-neighbor controls still reproduce on the eligible overlap.
    original = pd.read_csv(ROOT / "results/basin_ai_representation_checks/all_predictions.csv")
    replay = []
    for (cohort, analysis, arm), frame in sets.loc[
        sets.scenario.eq("all_rivers") & sets.k.eq(5)
    ].groupby(["cohort", "analysis", "arm"]):
        old = original.loc[
            original.cohort.eq(cohort) & original.analysis.eq(analysis) & original.arm.eq(arm)
        ].set_index("query_event_id")
        if old.empty:
            continue
        new = frame.set_index("query_event_id")
        for col in [
            "candidate_count",
            "candidate_storm_count",
            "analogue_absolute_error",
            "median_absolute_error",
        ]:
            np.testing.assert_allclose(new[col], old.loc[new.index, col], rtol=0, atol=1e-12)
        replay.append(
            {
                "cohort": cohort,
                "analysis": analysis,
                "arm": arm,
                "queries_replayed": len(new),
                "status": "exact within 1e-12",
            }
        )
    pd.DataFrame(replay).to_csv(out / "original_control_replay.csv", index=False)
    # Availability effects require paired queries, not unrelated aggregate means.
    availability = []
    archive = []
    for (cohort, analysis, arm, k), group in sets.groupby(["cohort", "analysis", "arm", "k"]):
        ref = group.loc[group.scenario.eq("all_rivers")].set_index("query_event_id")
        test = group.loc[group.scenario.eq("other_rivers")].set_index("query_event_id")
        ids = ref.index.intersection(test.index)
        ref, test = ref.loc[ids], test.loc[ids]
        delta = ref[["query_storm_id", "query_onset_utc"]].copy()
        delta["storm_year"] = pd.to_datetime(
            delta.groupby("query_storm_id").query_onset_utc.transform("min"), utc=True
        ).dt.year
        for metric in METRICS:
            delta["difference"] = test[metric] - ref[metric]
            for unit in ["query_storm_id", "storm_year"]:
                availability.append(
                    {
                        "cohort": cohort,
                        "analysis": analysis,
                        "arm": arm,
                        "k": k,
                        "metric": metric,
                        "resampling_unit": unit,
                        "all_rivers_mean_on_overlap": ref[metric].mean(),
                        "other_rivers_mean_on_overlap": test[metric].mean(),
                        **REVIEW.cluster_interval(delta, unit),
                    }
                )
    pd.DataFrame(availability).to_csv(out / "availability_intervals.csv", index=False)
    benchmarks = []
    for key, group in sets.groupby(["cohort", "scenario", "analysis", "arm", "k"]):
        delta = group[["query_storm_id", "query_onset_utc"]].copy()
        delta["storm_year"] = pd.to_datetime(
            delta.groupby("query_storm_id").query_onset_utc.transform("min"), utc=True
        ).dt.year
        delta["difference"] = group.analogue_absolute_error - group.median_absolute_error
        for unit in ["query_storm_id", "storm_year"]:
            benchmarks.append(
                dict(zip(["cohort", "scenario", "analysis", "arm", "k"], key, strict=True))
                | {
                    "reference": "expanding_prior_pool_median",
                    "resampling_unit": unit,
                    "analogue_mean_peak_error": group.analogue_absolute_error.mean(),
                    "median_peak_error": group.median_absolute_error.mean(),
                    **REVIEW.cluster_interval(delta, unit),
                }
            )
    pd.DataFrame(benchmarks).to_csv(out / "historical_median_intervals.csv", index=False)
    # Explain full-archive versus context-sample differences on identical queries.
    for (scenario, analysis, arm, k), group in sets.loc[
        sets.cohort.isin(["dutch", "context"])
    ].groupby(["scenario", "analysis", "arm", "k"]):
        full = group.loc[group.cohort.eq("dutch")].set_index("query_event_id")
        limited = group.loc[group.cohort.eq("context")].set_index("query_event_id")
        ids = full.index.intersection(limited.index)
        if len(ids) == 0:
            continue
        for metric in METRICS:
            archive.append(
                {
                    "scenario": scenario,
                    "analysis": analysis,
                    "arm": arm,
                    "k": k,
                    "metric": metric,
                    "paired_queries": len(ids),
                    "full_archive_mean": full.loc[ids, metric].mean(),
                    "context_archive_mean": limited.loc[ids, metric].mean(),
                }
            )
    pd.DataFrame(archive).to_csv(out / "common_query_archive_summary.csv", index=False)
    spread_rows = []
    for key, group in sets.loc[sets.k.eq(5)].groupby(
        ["cohort", "scenario", "analysis", "arm", "query_river"]
    ):
        for spread, error in [
            ("peak_spread", "mean_donor_peak_absolute_error"),
            ("curve_spread", "ensemble_curve_level_rmse"),
        ]:
            valid = len(group) >= 2 and group[spread].nunique() > 1 and group[error].nunique() > 1
            spread_rows.append(
                dict(
                    zip(["cohort", "scenario", "analysis", "arm", "query_river"], key, strict=True)
                )
                | {
                    "spread": spread,
                    "error": error,
                    "queries": len(group),
                    "spearman_rho": float(spearmanr(group[spread], group[error]).statistic)
                    if valid
                    else None,
                    "status": "descriptive within-river association"
                    if valid
                    else "undefined; retained",
                }
            )
    pd.DataFrame(spread_rows).to_csv(out / "within_river_spread_associations.csv", index=False)
    cards = pd.read_csv(out / "illustrative_cards.csv")
    for card in cards.itertuples(index=False):
        qid = card.query_event_id
        fig, axes = plt.subplots(2, 2, figsize=(11, 6), sharey="row")
        for column, arm in enumerate([card.reference, card.challenger]):
            chosen = donors.loc[
                donors.cohort.eq(card.cohort)
                & donors.scenario.eq(card.scenario)
                & donors.analysis.eq("main")
                & donors.k.eq(5)
                & donors.arm.eq(arm)
                & donors.query_event_id.eq(qid)
            ]
            for eid in chosen.analogue_event_id:
                axes[0, column].plot(
                    np.arange(-511, 1),
                    history.loc[eid],
                    color="steelblue",
                    alpha=0.45,
                    linewidth=0.7,
                )
                axes[1, column].plot(
                    np.arange(1, 73),
                    response.loc[eid],
                    color="steelblue",
                    alpha=0.45,
                    linewidth=0.9,
                )
            axes[0, column].plot(np.arange(-511, 1), history.loc[qid], color="black", linewidth=1.3)
            axes[1, column].plot(np.arange(1, 73), response.loc[qid], color="black", linewidth=1.8)
            axes[0, column].set_title(arm)
            axes[0, column].set_xlabel("Observed assessment hours")
            axes[1, column].set_xlabel("Withheld response hours")
            axes[1, column].axhline(1, color="grey", linestyle=":", linewidth=0.7)
        axes[0, 0].set_ylabel("Within-history standardized Q")
        axes[1, 0].set_ylabel("Q / own-era p99")
        rain = coverage.loc[qid, "antecedent_rain_72h_mm"]
        rain_text = f"{rain:.1f} mm" if np.isfinite(rain) else "unavailable"
        fig.suptitle(
            f"{card.cohort}, {card.scenario}: {qid}\nBlack=query, blue=5 donors; antecedent 72h rain: {rain_text}; concern flag: {card.query_measurement_concern}",
            fontsize=8,
        )
        fig.tight_layout()
        fig.savefig(out / ("history_" + card.figure), dpi=140)
        plt.close(fig)
    # One scientific figure shows the averaging-versus-individual-relevance tradeoff.
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    main = sets.loc[
        sets.cohort.eq("dutch") & sets.scenario.eq("other_rivers") & sets.analysis.eq("main")
    ]
    for arm in ["r0", "raw_state", "ttm_ordered_state", "fusion_ttm"]:
        frame = main.loc[main.arm.eq(arm)].groupby("k")[METRICS].mean()
        axes[0].plot(frame.index, frame.mean_donor_peak_absolute_error, marker="o", label=arm)
        axes[1].plot(frame.index, frame.mean_peak_scaled_shape_rmse, marker="o", label=arm)
    for ax in axes:
        ax.set_xlabel("Distinct prior-storm donors")
        ax.set_xticks([3, 5, 10])
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Mean-donor peak absolute error (p99 units)")
    axes[1].set_ylabel("Mean individual-donor shape RMSE")
    axes[1].legend(fontsize=7)
    fig.suptitle("Dutch cross-river retrieval: fixed paired queries; exploratory point estimates")
    fig.tight_layout()
    fig.savefig(out / "donor_count_tradeoff.png", dpi=150)
    plt.close(fig)
    (out / "validation.json").write_text(
        json.dumps(
            {
                "nested_prefixes_verified": True,
                "distinct_prior_storms_verified": True,
                "cross_river_and_quality_filters_verified": True,
                "original_control_configurations_replayed": len(replay),
                "paired_interval_rows": len(pd.read_csv(out / "paired_intervals.csv")),
                "input_history_cards": len(cards),
            },
            indent=2,
        )
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument(
        "--audit-existing",
        action="store_true",
        help="Verify hashed results and add paired availability/input-history audits without repeating retrieval",
    )
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    samples, representations, index, windows = REVIEW.load_inputs()
    arms = S.build_arms(
        samples, representations, index, windows, ROOT / "results/basin_ai_representation_checks"
    )
    configs = configurations(arms, samples)
    meta = index.set_index("event_id")
    for cohort in samples:
        samples[cohort]["physical_river_group"] = samples[cohort].event_id.map(
            meta.physical_river_group
        )
        if samples[cohort].physical_river_group.isna().any():
            raise ValueError("Unmapped physical river")
    response, history, coverage = CENSUS.load_curves(index, windows)
    if args.audit_existing:
        manifest = json.loads((out / "manifest.json").read_text())
        for name, expected in manifest["outputs_sha256"].items():
            if hashlib.sha256((out / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f"Changed result file: {name}")
        sets = pd.read_csv(out / "query_diagnostics.csv")
        donors = pd.read_csv(out / "selected_donors.csv")
        additional_checks(sets, donors, response, history, coverage, out)
        manifest["postprocessing_source_sha256"] = hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest()
        manifest["outputs_sha256"] = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*.csv"))
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print("Hashed retrieval outputs verified; additional audits completed")
        return
    sets, selected, eligibility = [], [], []
    for cohort, configurations_ in configs.items():
        for scenario in ["all_rivers", "other_rivers"]:
            for quality in [False, True]:
                analysis = "quality_sensitivity" if quality else "main"
                expected = None
                for arm, settings in configurations_.items():
                    # Retrieve top ten once; nested prefixes preserve ranks and common queries.
                    scores, donors = BASE.retrieve_prior_analogues(
                        samples[cohort],
                        top_k=10,
                        min_candidates=20,
                        min_candidate_storms=10,
                        exclude_same_river=scenario == "other_rivers",
                        exclude_measurement_concerns=quality,
                        **settings,
                    )
                    if expected is None:
                        expected = set(scores.query_event_id)
                    elif expected != set(scores.query_event_id):
                        raise ValueError("Arm eligibility mismatch")
                    if donors.analogue_storm_id.eq(donors.query_storm_id).any():
                        raise ValueError("Same-storm donor")
                    if (
                        pd.to_datetime(donors.analogue_onset_utc, utc=True) + pd.Timedelta(hours=72)
                        > pd.to_datetime(donors.query_onset_utc, utc=True)
                    ).any():
                        raise ValueError("Unfinished donor outcome")
                    for k in [3, 5, 10]:
                        evaluated, pairs = assess(
                            scores, donors.loc[donors["rank"].le(k)], response, meta
                        )
                        if (
                            scenario == "other_rivers"
                            and pairs.query_river.eq(pairs.analogue_river).any()
                        ):
                            raise ValueError("Own-physical-river donor leaked")
                        for frame in [evaluated, pairs]:
                            (
                                frame["cohort"],
                                frame["scenario"],
                                frame["analysis"],
                                frame["arm"],
                                frame["k"],
                            ) = cohort, scenario, analysis, arm, k
                        sets.append(evaluated)
                        selected.append(pairs)
                    eligibility.append(
                        {
                            "cohort": cohort,
                            "scenario": scenario,
                            "analysis": analysis,
                            "arm": arm,
                            "queries": len(scores),
                            "storms": scores.query_storm_id.nunique(),
                        }
                    )
                    print(f"{cohort}/{scenario}/{analysis}/{arm}: {len(scores)}", flush=True)
    sets, donors = pd.concat(sets, ignore_index=True), pd.concat(selected, ignore_index=True)
    sets.to_csv(out / "query_diagnostics.csv", index=False)
    donors.to_csv(out / "selected_donors.csv", index=False)
    pd.DataFrame(eligibility).to_csv(out / "eligibility.csv", index=False)
    keys = ["cohort", "scenario", "analysis", "arm", "k"]
    summary = sets.groupby(keys)[
        METRICS
        + [
            "peak_range_contains_query",
            "same_river_share",
            "cross_country_share",
            "candidate_count",
            "candidate_storm_count",
        ]
    ].mean()
    summary.join(sets.groupby(keys).size().rename("queries")).reset_index().to_csv(
        out / "summary.csv", index=False
    )
    sets.groupby(keys + ["query_river"])[METRICS].mean().join(
        sets.groupby(keys + ["query_river"]).size().rename("queries")
    ).reset_index().to_csv(out / "river_summary.csv", index=False)
    intervals(sets).to_csv(out / "paired_intervals.csv", index=False)
    print("Paired intervals complete", flush=True)
    disagreement_audit(sets, response, coverage, donors, out)
    spread_audit(sets).to_csv(out / "spread_error_associations.csv", index=False)
    additional_checks(sets, donors, response, history, coverage, out)
    paths = [
        ROOT / "scripts" / name
        for name in [
            "65_hydrological_analogue_baseline.py",
            "75_strengthen_foundation_representations.py",
            Path(__file__).name,
        ]
    ]
    manifest = {
        "status": "exploratory checks completed",
        "k": [3, 5, 10],
        "minimum_candidates": 20,
        "minimum_prior_storms": 10,
        "fusion": "equal conventional and temporal blocks; prior-only scaling; matched raw versus ordered TTM",
        "cross_river": "exclude full physical river donors, retain query history; not ungauged prediction",
        "intervals": "9999 paired query-storm/year draws; 999 spread-correlation storm draws; fixed donor archive; unadjusted exploratory",
        "limitations": "retrospective era-p99; reused donor uncertainty not resampled; cards outcome-selected, not independent validation",
        "query_sets": len(sets),
        "selected_slots": len(donors),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
        "upstream_manifest_sha256": hashlib.sha256(
            (ROOT / "results/basin_ai_representation_checks/summary.json").read_bytes()
        ).hexdigest(),
        "outputs_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*.csv"))
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
