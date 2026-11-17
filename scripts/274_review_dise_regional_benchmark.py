"""Read-only scientific review of the frozen first regional DISE fold.

No fits, input changes, re-selection of models, or empirical confidence claims.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd

from src.dise_corrected import population, score, weights
from src.geoglows_experiment import sha, write_json

BASE = ROOT / "results/limburg_dise_regional_benchmark_v1"
SOURCE = BASE / "benchmark_wurm_external_2021"
OUT = BASE / "review_2026_11_17"
A = "native_rmse__H+A"
E = "native_rmse__H+A+E"


def independent_metrics(f, arm):
    errors = f[arm] - f.q_observed
    g = f[["gauge", "river_group"]].assign(absolute=errors.abs(), squared=errors**2, bias=errors)
    v = (
        g.groupby(["river_group", "gauge"])[["absolute", "squared", "bias"]]
        .mean()
        .groupby("river_group")
        .mean()
        .mean()
    )
    return dict(mae=float(v.absolute), rmse=float(np.sqrt(v.squared)), bias=float(v.bias))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    for name, digest in manifest["outputs"].items():
        if sha(SOURCE / name) != digest:
            raise ValueError("Frozen output changed")
    before = sha(SOURCE / "manifest.json")
    p = pd.read_parquet(SOURCE / "predictions.parquet")
    metrics = pd.read_csv(SOURCE / "metrics.csv")
    tuning = pd.read_csv(SOURCE / "tuning.csv")
    selected = json.loads((SOURCE / "selected.json").read_text())
    local = p.source_role.eq("local")
    external = ~local
    scopes = {"local_held_Wurm": local, "external_all": external}
    for group in sorted(p.loc[external, "river_group"].unique()):
        scopes[group] = p.river_group.eq(group)
    scopes.update(
        external_high_overlap=external & p.spatial_view_high_overlap,
        external_high_overlap_location_consistent=external & p.spatial_view_location_consistent,
        external_mapping_stress=external & p.spatial_view_stress,
    )
    conditions = {
        "all_days": pd.Series(True, index=p.index),
        "high_water": p.high_water.fillna(False).astype(bool),
        "clean_high_water": (
            p.high_water.fillna(False) & p.clean_verification.fillna(False)
        ).astype(bool),
    }
    arms = ["q_model", A, E, "native_rmse__H", "native_rmse__H+E"]
    comparison = []
    verified = 0
    for scope, use in scopes.items():
        for stratum, mask in conditions.items():
            f = p.loc[use & mask]
            if len(f) == 0:
                continue
            values = {}
            for arm in arms:
                v = independent_metrics(f, arm)
                row = metrics.loc[
                    metrics.scope.eq(scope) & metrics.stratum.eq(stratum) & metrics.arm.eq(arm)
                ].iloc[0]
                for col in ["mae", "rmse", "bias"]:
                    if not np.isclose(v[col], row[col], rtol=1e-12, atol=1e-12):
                        raise ValueError("Independent metric reconstruction differs")
                values[arm] = v
                verified += 1
            comparison.append(
                dict(
                    scope=scope,
                    stratum=stratum,
                    rows=len(f),
                    gauges=f.gauge.nunique(),
                    calendar_dates=f.day.nunique(),
                    raw_mae=values["q_model"]["mae"],
                    conventional_mae=values[A]["mae"],
                    alpha_added_mae=values[E]["mae"],
                    alpha_substitute_mae=values["native_rmse__H+E"]["mae"],
                    alpha_added_mae_reduction_pct=100 * (1 - values[E]["mae"] / values[A]["mae"]),
                    raw_rmse=values["q_model"]["rmse"],
                    conventional_rmse=values[A]["rmse"],
                    alpha_added_rmse=values[E]["rmse"],
                    alpha_added_rmse_reduction_pct=100
                    * (1 - values[E]["rmse"] / values[A]["rmse"]),
                    correction_vs_raw_mae_reduction_pct=100
                    * (1 - values[E]["mae"] / values["q_model"]["mae"]),
                    correction_vs_raw_rmse_reduction_pct=100
                    * (1 - values[E]["rmse"] / values["q_model"]["rmse"]),
                )
            )
    comparisons = pd.DataFrame(comparison)
    comparisons.to_csv(OUT / "primary_comparisons.csv", index=False)
    sensitivity = []
    for policy in ["native_rmse", "article_faithful"]:
        for scope in ["local_held_Wurm", "external_all"]:
            for stratum in conditions:
                part = metrics.loc[metrics.scope.eq(scope) & metrics.stratum.eq(stratum)]
                conventional = part.loc[part.arm.eq(policy + "__H+A")].iloc[0]
                encoded = part.loc[part.arm.eq(policy + "__H+A+E")].iloc[0]
                defined = conventional.status == "defined" and encoded.status == "defined"
                sensitivity.append(
                    dict(
                        policy=policy,
                        scope=scope,
                        stratum=stratum,
                        conventional_mae=conventional.mae,
                        alpha_mae=encoded.mae,
                        mae_reduction_pct=100 * (1 - encoded.mae / conventional.mae)
                        if defined
                        else None,
                        status="defined" if defined else "undefined",
                    )
                )
    pd.DataFrame(sensitivity).to_csv(OUT / "selection_policy_sensitivity.csv", index=False)
    per_site = []
    peaks = []
    for gauge, f in p.groupby("gauge"):
        for stratum, mask in [
            ("all_days", np.ones(len(f), bool)),
            ("high_water", f.high_water.fillna(False).to_numpy(bool)),
        ]:
            part = f.loc[mask]
            if len(part) == 0:
                continue
            va = independent_metrics(part, A)
            ve = independent_metrics(part, E)
            raw = independent_metrics(part, "q_model")
            per_site.append(
                dict(
                    gauge=gauge,
                    station=f.station.iloc[0],
                    river_group=f.river_group.iloc[0],
                    source_role=f.source_role.iloc[0],
                    overlap_stratum=f.overlap_stratum.iloc[0],
                    location_stratum=f.location_stratum.iloc[0],
                    stratum=stratum,
                    rows=len(part),
                    conventional_mae=va["mae"],
                    alpha_mae=ve["mae"],
                    raw_mae=raw["mae"],
                    mae_reduction_pct=100 * (1 - ve["mae"] / va["mae"]),
                )
            )
        row = f.loc[f.q_observed.idxmax()]
        peaks.append(
            {
                k: row[k]
                for k in [
                    "gauge",
                    "station",
                    "river_group",
                    "source_role",
                    "day",
                    "q_observed",
                    "q_model",
                    A,
                    E,
                    "clean_verification",
                    "overlap_stratum",
                    "location_stratum",
                ]
            }
        )
    sites = pd.DataFrame(per_site)
    sites.to_csv(OUT / "per_gauge_comparisons.csv", index=False)
    pd.DataFrame(peaks).to_csv(OUT / "observed_maximum_daily_flow.csv", index=False)
    # Algorithmic seed variation is not a sampling confidence interval.
    arrays = {}
    for arm in [A, E]:
        arrays[arm] = [
            np.load(SOURCE / f"final_{arm.replace('+', '_')}_{s}.npy") for s in [101, 202, 303]
        ]
        assert np.array_equal(np.mean(arrays[arm], axis=0), p[arm].to_numpy())
    seeds = []
    for scope, use in scopes.items():
        for stratum, mask in conditions.items():
            choose = (use & mask).to_numpy()
            part = p.loc[choose]
            if not len(part):
                continue
            for j, seed in enumerate([101, 202, 303]):
                a = score(part, arrays[A][j][choose], population(part))["mae"]
                e = score(part, arrays[E][j][choose], population(part))["mae"]
                seeds.append(
                    dict(
                        scope=scope,
                        stratum=stratum,
                        seed=seed,
                        conventional_mae=a,
                        alpha_mae=e,
                        mae_reduction_pct=100 * (1 - e / a),
                    )
                )
    pd.DataFrame(seeds).to_csv(OUT / "seed_sensitivity.csv", index=False)
    limits = []
    candidate_scores = []
    for name, settings in selected.items():
        policy, arm = name.split("__")
        allrows = tuning.loc[tuning.policy.eq(policy) & tuning.arm.eq(arm)].copy()
        part = allrows.loc[allrows.candidate_index.eq(settings["candidate_index"])]
        allrows["weighted"] = (
            np.where(policy == "native_rmse", allrows.validation_rmse**2, allrows.validation_mae)
            * allrows.validation_groups
        )
        criteria = (
            allrows.groupby("candidate_index").weighted.sum()
            / allrows.groupby("candidate_index").validation_groups.sum()
        )
        for candidate, value in criteria.items():
            z = allrows.loc[allrows.candidate_index.eq(candidate)]
            candidate_scores.append(
                dict(
                    policy=policy,
                    arm=arm,
                    candidate=int(candidate),
                    criterion=float(value),
                    caps=int(z.tree_cap_hit.sum()),
                    selected=int(candidate) == settings["candidate_index"],
                )
            )
        limits.append(
            dict(
                policy=policy,
                arm=arm,
                selected_candidate=settings["candidate_index"],
                final_trees=settings["trees"],
                selected_fold_caps=int(part.tree_cap_hit.sum()),
                selected_fold_count=len(part),
                best_iteration_min=int(part.best_iteration.min()) + 1,
                best_iteration_max=int(part.best_iteration.max()) + 1,
                all_candidate_caps=int(allrows.tree_cap_hit.sum()),
                criterion=settings["criterion"],
                criterion_scale=settings["criterion_scale"],
            )
        )
    pd.DataFrame(limits).to_csv(OUT / "tree_limit_diagnostics.csv", index=False)
    pd.DataFrame(candidate_scores).to_csv(OUT / "validation_candidate_scores.csv", index=False)
    impacts = []
    symmetric = []
    for _role, f in p.groupby("source_role"):
        high = f.loc[f.high_water.fillna(False)].copy()
        high["raw_to_corrected_weighted_mse_change"] = (
            ((high[E] - high.q_observed) ** 2 - (high.q_model - high.q_observed) ** 2)
            * weights(high)
            / len(high)
        )
        impacts.append(
            high[
                [
                    "day",
                    "gauge",
                    "station",
                    "river_group",
                    "source_role",
                    "q_observed",
                    "q_model",
                    A,
                    E,
                    "clean_verification",
                    "overlap_stratum",
                    "location_stratum",
                    "raw_to_corrected_weighted_mse_change",
                ]
            ]
        )
        all_ = f[
            [
                "day",
                "gauge",
                "station",
                "source_role",
                "river_group",
                "q_observed",
                A,
                E,
                "high_water",
                "clean_verification",
            ]
        ].copy()
        all_["encoder_absolute_error_change"] = (all_[E] - all_.q_observed).abs() - (
            all_[A] - all_.q_observed
        ).abs()
        symmetric.extend(
            [
                all_.nsmallest(6, "encoder_absolute_error_change").assign(
                    selection="largest_improvements"
                ),
                all_.nlargest(6, "encoder_absolute_error_change").assign(selection="largest_harms"),
            ]
        )
    pd.concat(impacts).to_csv(OUT / "high_water_squared_error_contributions.csv", index=False)
    pd.concat(symmetric).to_csv(OUT / "symmetric_daily_examples.csv", index=False)
    plot(p, comparisons, tuning, selected)
    if sha(SOURCE / "manifest.json") != before:
        raise ValueError("Frozen benchmark changed during review")
    summary = dict(
        status="review_completed_without_new_fits",
        frozen_manifest_sha256=before,
        review_code_sha256=sha(Path(__file__)),
        independent_metric_rows_verified=verified,
        tuning_fits=len(tuning),
        capped_tuning_fits=int(tuning.tree_cap_hit.sum()),
        selected_capped_fold_fits=sum(z["selected_fold_caps"] for z in limits),
        selected_fold_fits=sum(z["selected_fold_count"] for z in limits),
        primary_pair_selected_caps={
            z["arm"]: z["selected_fold_caps"]
            for z in limits
            if z["policy"] == "native_rmse" and z["arm"] in ["H+A", "H+A+E"]
        },
        local_high_water_gauge_days=int((local & conditions["high_water"]).sum()),
        local_high_water_calendar_days=int(
            p.loc[local & conditions["high_water"], "day"].nunique()
        ),
        external_high_water_gauge_days=int((external & conditions["high_water"]).sum()),
        external_high_water_calendar_days=int(
            p.loc[external & conditions["high_water"], "day"].nunique()
        ),
        held_external_geometry_support=p.loc[external]
        .groupby(["overlap_stratum", "location_stratum"])
        .gauge.nunique()
        .rename("gauges")
        .reset_index()
        .to_dict("records"),
        no_new_model_fit_or_threshold_selection=True,
        output_hashes={
            q.name: sha(q)
            for q in OUT.iterdir()
            if q.is_file() and q.name != "receipt.json" and q.suffix != ".log"
        },
    )
    write_json(OUT / "receipt.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "output_hashes"}, indent=2))


def plot(p, contrasts, tuning, selected):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
    groups = ["local_held_Wurm", "external:Ahr", "external:Erft", "external:Sieg"]
    for ax, stratum in zip(axes, ["all_days", "high_water"], strict=True):
        sub = contrasts.loc[contrasts.stratum.eq(stratum)].set_index("scope").reindex(groups)
        vals = sub.alpha_added_mae_reduction_pct.to_numpy()
        ax.barh(
            ["Wurm", "Ahr", "Erft", "Sieg"],
            vals,
            color=["#267649" if v >= 0 else "#ae433b" for v in vals],
        )
        ax.axvline(0, color="black", linewidth=0.7)
        ax.set_title(stratum.replace("_", " "))
        ax.set_xlabel("MAE reduction from adding AlphaEarth (%)\nPositive improves; one 2021 fold")
        ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT / "primary_effect_by_river.png", dpi=160)
    plt.close(fig)
    wurm = p.loc[p.source_role.eq("local") & p.day.between("2021-07-08", "2021-07-22")]
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for ax, (_g, f) in zip(axes, wurm.groupby("gauge"), strict=True):
        for col, label, color in [
            ("q_observed", "Provided daily observations", "#111111"),
            ("q_model", "Raw GEOGLOWS", "#999999"),
            (A, "Conventional correction", "#4477aa"),
            (E, "Plus AlphaEarth", "#228844"),
        ]:
            ax.plot(f.day, f[col], label=label, color=color)
        questionable = ~f.clean_verification.fillna(False).astype(bool)
        ax.scatter(
            f.loc[questionable, "day"],
            f.loc[questionable, "q_observed"],
            facecolors="none",
            edgecolors="#b44b42",
            s=45,
            label="Outside inherited strict-clean criteria",
        )
        ax.set_ylabel("mm/day")
        ax.set_title(f.station.iloc[0])
        ax.grid(alpha=0.15)
    axes[0].legend(fontsize=7, ncol=2)
    fig.autofmt_xdate()
    fig.suptitle(
        "Wurm, July 2021: daily reconstruction, not an instantaneous peak or forecast", fontsize=11
    )
    fig.tight_layout()
    fig.savefig(OUT / "wurm_july_2021_daily_flows.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
