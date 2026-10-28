"""Report all encoders and inspect real retrieved trajectories, without reranking."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.monitoring_review import mean_estimate

OUT = ROOT / "results/limburg_monitoring_2026_10_28"


def main():
    audit = json.loads((OUT / "audit.json").read_text())
    if audit["status"] != "passed":
        raise ValueError("Complete independent numerical audit before interpretation")
    review = OUT / "review"
    table = pd.read_parquet(review / "contrasts.parquet")
    primary = table[
        (table.population == "full_members_fixed_inputs")
        & (table.pool == "same_gauge")
        & (table.kind == "recent")
        & (table.country == "all")
        & (table.target_k == 5)
        & (table.effect == "total_vs_natural")
    ].copy()
    primary["relative_percent"] = 100 * primary.difference / primary.natural_crps_specific
    primary.to_csv(review / "primary-model-table.csv", index=False)
    meta = pd.read_parquet(OUT / "preparation/cases.parquet")
    arrays = dict(np.load(OUT / "preparation/inputs.npz"))
    cases = []
    per_gauge = []
    # Extremes are explicitly post-hoc diagnostic examples, never population estimates.
    fig, axes = plt.subplots(10, 2, figsize=(13, 31), squeeze=False)
    for ix, model in enumerate(sorted(primary.model.unique())):
        path = review / "paired" / f"{model}__recent__same_gauge.parquet"
        f = pd.read_parquet(path)
        f = f[f.full_members & f.fixed_query & f.scenario.eq("delay_12") & f.target_k.eq(5)].copy()
        for gauge, g in f.groupby("gauge"):
            per_gauge.append(
                dict(
                    model=model,
                    gauge=gauge,
                    country=g.country.iloc[0],
                    cases=g.case.nunique(),
                    case_issues=len(g),
                    storms=g.storm_id.nunique(),
                    difference=mean_estimate(g, "total_vs_natural"),
                    natural_crps=mean_estimate(g, "natural_crps_specific"),
                    augmented_crps=mean_estimate(g, "aug_crps_specific"),
                    note="same-gauge recent delay12 K5; point diagnostic, own-model cohort",
                )
            )
        for col, (label, order) in enumerate([("largest gain", True), ("largest harm", False)]):
            ax = axes[ix, col]
            if f.empty:
                ax.set_visible(False)
                continue
            row = f.sort_values(
                ["total_vs_natural", "case", "offset_h"], ascending=[order, True, True]
            ).iloc[0]
            qi, u, cap = int(row.case), int(row.offset_h), int(row.cap_h)
            site = meta.iloc[qi]
            observed = arrays[f"outcome_{u}"][qi]
            hour = np.arange(1, 25)
            ax.plot(hour, observed, color="black", label="Observed future Q")
            for prefix, color, title in [
                ("natural", "tab:orange", "Conventional"),
                ("aug", "tab:blue", "EO augmented"),
            ]:
                ids = np.asarray(row[prefix + "_member_ids"], int)
                members = arrays[f"outcome_{u}"][ids]
                for member in members:
                    ax.plot(hour, member, color=color, linewidth=0.5, alpha=0.3)
                ax.plot(hour, members.mean(axis=0), color=color, label=title)
            last_q = arrays[f"q_{u}_{cap}"][qi, 0]
            ax.axhline(last_q, color="grey", linestyle=":", label="Last available Q")
            ax.set(
                title=f"{model}: {label}; {site.station}, {site.cutoff_utc:%Y-%m-%d}\n"
                f"issue +{u}h, Q age {row.actual_age_h:g}h; ΔCRPS {row.total_vs_natural:.4g} mm/h",
                xlabel="Hours after issue",
                ylabel="Discharge (m³/s)",
            )
            if ix == 0 and col == 0:
                ax.legend(fontsize=7)
            cases.append(
                dict(
                    model=model,
                    selection=label,
                    case=qi,
                    case_id=site.case_id,
                    station=site.station,
                    country=site.country,
                    cutoff_utc=str(site.cutoff_utc),
                    offset_h=u,
                    cap_h=cap,
                    actual_age_h=float(row.actual_age_h),
                    difference=float(row.total_vs_natural),
                    query_clean=bool(row.aug_query_clean),
                    donors_clean=bool(row.aug_donors_clean),
                    natural_members=json.dumps(row.natural_member_ids.tolist()),
                    augmented_members=json.dumps(row.aug_member_ids.tolist()),
                    observed_peak_m3s=float(observed.max()),
                    natural_peak_m3s=float(
                        arrays[f"outcome_{u}"][row.natural_member_ids].mean(axis=0).max()
                    ),
                    augmented_peak_m3s=float(
                        arrays[f"outcome_{u}"][row.aug_member_ids].mean(axis=0).max()
                    ),
                )
            )
    fig.suptitle(
        "Post-hoc stress illustrations for every encoder: strongest gain and harm at 12h delay\n"
        "K5, same gauge, four-week context; illustrative extremes, not independent tests",
        y=1.0,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(review / "actual-analogue-extremes.png", dpi=120)
    plt.close(fig)
    pd.DataFrame(cases).to_csv(review / "actual-case-selections.csv", index=False)
    pd.DataFrame(per_gauge).to_csv(review / "gauge-diagnostics.csv", index=False)
    lines = [
        "# Monitoring-loss results: numerical readout for Brian",
        "",
        "Exploratory full held-data analysis, 28 October 2026. Research aid, not dissertation prose.",
        "",
        "481 regional rainfall episodes × 8 gauges; all eligible cases included. Four issue times, 26 unique information states, 42 completed scoring jobs. All selected donor members and prepared Q histories passed the independent audit.",
        "",
        "Lower CRPS is better. Negative differences favor EO. Each row compares the same supported full-five-member queries; own-model cohorts differ. Intervals resample whole regional storms and years (999 common-universe draws), not individual masks.",
        "",
        "| Model | Delay (h) | Cases | Storms | EO − conventional (mm/h) | Relative % | Storm 95% interval | Year 95% interval |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in (
        primary[primary.scenario.isin(["delay_0", "delay_12", "delay_24"])]
        .sort_values(["model", "scenario"])
        .itertuples()
    ):
        lines.append(
            f"| {r.model} | {r.scenario.removeprefix('delay_')} | {r.cases} | {r.storms} | {r.difference:.5g} | {r.relative_percent:.2f} | [{r.storm_id_lower:.5g}, {r.storm_id_upper:.5g}] | [{r.year_lower:.5g}, {r.year_upper:.5g}] |"
        )
    lines += [
        "",
        "## Reading the outputs",
        "",
        "`contrasts.csv` separates the representation increment, EO archive loss, input archive restriction and their total. It also includes conventional degradation, simple-fallback comparisons, direct age interactions, horizon diagnostics, countries, all-ten shared cohorts, stopped-feed sequences and full available fallback coverage.",
        "",
        "`actual-case-selections.csv` and its figure show the largest positive and negative EO effects for every encoder at 12h delay. These are selected using outcomes for explanation only. They do not demonstrate operational case-selection skill. Full selected donor traces remain in the scores and paired tables.",
        "",
        "The clean-selected subset does not rerank donors. Missing verification hours remain unscored; unsupported EO uses conventional/persistence/history fallback. No telemetry frequency, warning threshold crossing, inundation skill or avoided damage is established. Historical finalized records and nominal data availability are not an as-issued warning replay.",
        "",
        "TTM, AlphaEarth and the still-downloading soil/snow control have not been added to these 42 core jobs. Current source imagery top-ups are not newly extracted embeddings. No provider email has been sent by this computation.",
    ]
    (review / "results-memo.md").write_text("\n".join(lines) + "\n")
    report = dict(
        status="completed",
        source_sha256=sha256(Path(__file__)),
        outputs_sha256={
            name: sha256(review / name)
            for name in [
                "primary-model-table.csv",
                "actual-analogue-extremes.png",
                "actual-case-selections.csv",
                "gauge-diagnostics.csv",
                "results-memo.md",
            ]
        },
    )
    (review / "case-review-manifest.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
