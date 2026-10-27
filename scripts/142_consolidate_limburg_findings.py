"""Consolidate frozen findings and fixed reporting views; no new empirical fits."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_findings import KEYS, collapse_intervals, reverse_contrast
from src.eo_inputs import ROUTES, sha256
from src.eo_integrity import fresh_output

OUT = ROOT / "results/limburg_findings_consolidation_2026_10_27"
KINDS = {
    "monthly_snapshot": "One completed month",
    "monthly": "Twelve completed months",
    "recent": "Four completed weeks",
}


def inputs():
    paths = {
        "rain": ROOT / "results/eo_analogue_comparison_rain168_v1/paired_intervals.csv",
        "main": ROOT / "results/eo_analogue_comparison_coherent_v1/paired_intervals.csv",
        "archive": ROOT / "results/eo_followup_2026_10_27/archive_intervals.parquet",
        "routes": ROOT / "results/eo_followup_2026_10_27/common_route_intervals.parquet",
        "alpha": ROOT / "results/basin_ai_cross_border_completion/paired_intervals.csv",
        "cases": ROOT / "results/eo_actual_case_review_2026_10_27/manifest.json",
    }
    rain, main = pd.read_csv(paths["rain"]), pd.read_csv(paths["main"])
    parts = []
    for f, cohort, family in [
        (rain, "rain_all_ten_matched", "rain_all_ten"),
        (main, "q_only_all_ten_matched", "q_all_ten"),
    ]:
        g = f[f.cohort.eq(cohort)].copy().assign(family=family)
        parts += [
            g,
            reverse_contrast(g[g.reference.eq("ttm_state") & g.challenger.eq("raw_state")]),
        ]
    for f, prefix, family in [
        (rain, "rain_matched_available_", "rain_available"),
        (main, "q_only_available_", "q_available"),
    ]:
        g = f[f.cohort.str.startswith(prefix)].copy()
        model = g.cohort.str.removeprefix(prefix)
        own = g.challenger.eq(model + "_only") | g.challenger.eq(model + "_ttm_state")
        parts.append(g[own].assign(family=family))
    g = main[
        main.cohort.str.startswith("alphaearth_matched_available_")
        & main.reference.eq("ttm_state")
        & main.challenger.eq("alphaearth_ttm_state")
    ]
    parts.append(g.assign(family="alpha_eo_available"))
    a = pd.read_csv(paths["alpha"])
    a = a[
        a.cohort.isin(["context", "q_only"])
        & a.comparison.str.startswith("model:")
        & a.pairing.eq("equal_donor_count")
    ].copy()
    split = a.comparison.str.split(":", n=2, expand=True)
    a["policy"] = split[1]
    names = split[2].str.split("->", expand=True)
    a["reference"], a["challenger"] = names[0], names[1]
    a["reference"] = a.reference.replace({"ttm_ordered_state": "ttm_state"})
    a["challenger"] = a.challenger.replace({"ttm_ordered_state": "ttm_state"})
    a["family"] = np.where(a.cohort.eq("context"), "alpha_full_context", "q_full_history")
    a["kind"] = np.where(a.cohort.eq("context"), "prior_year_annual", "512h_q_history")
    parts.append(a)
    arc = pd.read_parquet(paths["archive"])
    arc = arc[
        (arc.run.eq("main") & arc.cohort.eq("q_only_all_ten_matched"))
        | (arc.run.eq("rain168") & arc.cohort.eq("rain_all_ten_matched"))
    ].copy()
    arc["challenger"], arc["reference"] = arc.arm, "generic_archive"
    arc["family"] = np.where(arc.run.eq("main"), "q_all_ten", "rain_all_ten")
    parts.append(arc)
    routes = pd.read_parquet(paths["routes"])
    names = routes.contrast.str.split("_minus_", expand=True)
    routes["challenger"], routes["reference"] = names[0], names[1]
    routes["family"] = "route:" + routes.variant
    parts.append(routes)
    columns = KEYS + [
        "resampling_unit",
        "difference",
        "lower",
        "upper",
        "query_count",
        "cluster_count",
    ]
    return paths, pd.concat([p[columns] for p in parts], ignore_index=True)


def fixed_view(f):
    return f[
        f.analysis.eq("main")
        & f.policy.eq("pooled")
        & f.target_k.eq(5)
        & f.scenario.eq("all_rivers")
    ].copy()


def sensitivities(f):
    base = fixed_view(f[f.family.eq("rain_all_ten")])
    keys = ["kind", "cohort", "query_country", "reference", "challenger", "metric"]
    output = []
    for name, scenario, analysis, policy, k in [
        ("other_rivers", "other_rivers", "main", "pooled", 5),
        ("quality", "all_rivers", "quality_sensitivity", "pooled", 5),
        ("k10", "all_rivers", "main", "pooled", 10),
        ("domestic", "all_rivers", "main", "domestic", 5),
        ("foreign", "all_rivers", "main", "foreign", 5),
    ]:
        g = f[
            f.family.eq("rain_all_ten")
            & f.scenario.eq(scenario)
            & f.analysis.eq(analysis)
            & f.policy.eq(policy)
            & f.target_k.eq(k)
        ]
        cols = keys + ["difference", "query_count", "nominal_interval_pattern"]
        joined = base[cols].merge(
            g[cols],
            on=keys,
            how="outer",
            suffixes=("_base", "_sensitivity"),
            validate="one_to_one",
            indicator=True,
        )
        output.append(joined.assign(sensitivity=name))
    return pd.concat(output, ignore_index=True)


def figures(f, out):
    arms = ["raw_state", "ttm_state", "area_ttm_state", "identity_ttm_state"] + [
        m + "_ttm_state" for m in sorted(ROUTES)
    ]
    g = fixed_view(f)
    g = g[g.family.eq("rain_all_ten") & g.reference.eq("conventional") & g.challenger.isin(arms)]
    metrics = {
        "mean_peak_scaled_shape_rmse": "Individual response-shape error",
        "ensemble_curve_level_rmse": "Mean-trajectory error (Q/p99)",
    }
    labels = {
        "raw_state": "Raw Q + state",
        "ttm_state": "TTM + state",
        "area_ttm_state": "Area + TTM/state",
        "identity_ttm_state": "Gauge ID + TTM/state",
    }
    labels.update({m + "_ttm_state": m + " + TTM/state" for m in ROUTES})
    for kind, title in KINDS.items():
        fig, axes = plt.subplots(1, 4, figsize=(17, 9), sharey=True)
        for ax, (country, metric) in zip(
            axes, [(c, m) for c in ["NL", "DE"] for m in metrics], strict=True
        ):
            h = g[g.kind.eq(kind) & g.query_country.eq(country) & g.metric.eq(metric)].set_index(
                "challenger"
            )
            if set(h.index) != set(arms):
                raise ValueError("Missing fixed-view forest contrast")
            h, y = h.reindex(arms), np.arange(len(arms))
            for label, offset, color in [
                ("storm", -0.09, "tab:blue"),
                ("year", 0.09, "tab:orange"),
            ]:
                ax.hlines(
                    y + offset,
                    h[label + "_lower"],
                    h[label + "_upper"],
                    color=color,
                    linewidth=1.8,
                    label=label + " blocks",
                )
                ax.plot(h.difference, y + offset, ".", color=color, markersize=4)
            ax.axvline(0, color="black", linewidth=0.8)
            ax.set_title(
                f"{country}: {metrics[metric]}\nn={int(h.query_count.iloc[0])} queries", fontsize=10
            )
            ax.grid(axis="x", alpha=0.2)
            ax.set_xlabel("Error difference vs conventional")
        axes[0].set_yticks(np.arange(len(arms)), [labels[a] for a in arms], fontsize=9)
        axes[0].invert_yaxis()
        axes[-1].legend(fontsize=8, loc="lower right")
        fig.suptitle(
            f"{title}: shared all-ten rainfall-complete population; pooled/all-river, main, k=5\nNegative favours challenger. Nominal 95% intervals; exploratory, numerous dependent comparisons.",
            fontsize=11,
        )
        # Fixed margins keep long arm labels inside every context's canvas.
        fig.subplots_adjust(left=0.18, right=0.985, bottom=0.10, top=0.84, wspace=0.30)
        fig.savefig(out / (kind + "_vs_conventional.png"), dpi=150)
        fig.savefig(out / (kind + "_vs_conventional.pdf"))
        plt.close(fig)


def population_comparison(f):
    """Describe cohort/archive dependence, not a paired test between populations."""
    own = [m + suffix for m in ROUTES for suffix in ["_only", "_ttm_state"]]
    shared = f[
        f.family.eq("rain_all_ten")
        & f.reference.isin(["ttm_state", "conventional"])
        & f.challenger.isin(own)
    ]
    available = f[f.family.eq("rain_available")]
    keys = [k for k in KEYS if k not in ["family", "cohort"]]
    cols = keys + [
        "difference",
        "query_count",
        "nominal_interval_pattern",
        "storm_lower",
        "storm_upper",
        "year_lower",
        "year_upper",
    ]
    return shared[cols].merge(
        available[cols],
        on=keys,
        how="outer",
        suffixes=("_shared", "_available"),
        validate="one_to_one",
    )


def main():
    paths, f = inputs()
    combined = collapse_intervals(f)
    with fresh_output(OUT) as out:
        combined.to_parquet(out / "contrasts.parquet", index=False)
        fixed_view(combined).to_parquet(out / "fixed_reporting_view.parquet", index=False)
        sensitivities(combined).to_parquet(out / "sensitivity_comparison.parquet", index=False)
        population_comparison(combined).to_parquet(
            out / "population_comparison.parquet", index=False
        )
        scorecard = fixed_view(combined)
        scorecard = scorecard[
            scorecard.family.eq("rain_all_ten")
            & scorecard.reference.eq("conventional")
            & scorecard.challenger.isin([m + "_ttm_state" for m in ROUTES])
        ]
        scorecard.groupby(["challenger", "nominal_interval_pattern"]).size().rename(
            "dependent_reporting_cells"
        ).reset_index().to_parquet(out / "model_scorecard.parquet", index=False)
        figures(combined, out)
        manifest = {
            "status": "completed",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "purpose": "post-analysis reporting consolidation; no fitting, reranking, new bootstrap or event sample",
            "interpretation": "Negative favours challenger. Both-interval categories are exploratory nominal descriptions, not multiplicity-adjusted decisions or equivalence tests.",
            "reporting_choice": "Full all-ten Q and corrected-rain cohorts, all three contexts and both countries; fixed main/pooled/all-river/k5 view plus existing sensitivities. More inclusive model-available, AlphaEarth and route results remain separate.",
            "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in paths.values()},
            "source_sha256": {
                str(p.relative_to(ROOT)): sha256(p)
                for p in [Path(__file__), ROOT / "src/eo_findings.py"]
            },
            "contrasts": len(combined),
            "outputs_sha256": {p.name: sha256(p) for p in out.iterdir() if p.is_file()},
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output": str(OUT), "contrasts": len(combined)}))


if __name__ == "__main__":
    main()
