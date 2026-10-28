"""Consolidate all available monitoring-loss cases; no winner-driven reranking."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output
from src.monitoring_review import mean_estimate, paired_interval

OUT = ROOT / "results/limburg_monitoring_2026_10_28"
KEY = ["case", "offset_h", "cap_h", "target_k"]
BLOCK_UNIVERSES = {}
VERIFICATION_LABELS = {}
FIELDS = [
    "crps_specific",
    "crps_h6_specific",
    "crps_h12_specific",
    "crps_h24_specific",
    "rmse_specific",
    "peak_error_specific",
    "peak_time_error_h",
    "coverage80",
    "width80_specific",
]


def prefix(frame, role, label):
    f = frame.loc[
        frame.role.eq(role),
        KEY + FIELDS + ["actual_k", "query_clean", "donors_clean", "member_ids"],
    ].copy()
    if f.duplicated(KEY).any():
        raise ValueError("Duplicate scored opportunity/role")
    return f.rename(columns={c: label + "_" + c for c in f if c not in KEY})


def references(base, meta, aliases, arrays):
    natural = prefix(base, "natural_conventional", "natural")
    fixed = prefix(base, "fixed_conventional", "fixed")
    full = natural[natural.cap_h.eq(natural.offset_h)].drop(columns="cap_h")
    full = full.rename(
        columns={c: "full_" + c.removeprefix("natural_") for c in full if c.startswith("natural_")}
    )
    persistent = (
        base[base.role.eq("persistence")]
        .drop(columns=["target_k", "role"])
        .set_index(["case", "offset_h", "cap_h"])
    )
    generic = (
        base[base.role.eq("generic")]
        .drop(columns=["target_k", "role"])
        .set_index(["case", "offset_h", "cap_h"])
    )
    fallback = persistent.combine_first(generic).reset_index()
    all_reference = []
    for k in [5, 10]:
        nat = natural[natural.target_k.eq(k)].copy()
        f = fallback.copy()
        f["target_k"] = k
        f = f[KEY + FIELDS + ["actual_k", "query_clean", "donors_clean", "member_ids"]]
        f = f.rename(columns={c: "fallback_" + c for c in f if c not in KEY})
        f = f.merge(nat, on=KEY, how="outer", validate="one_to_one")
        for c in FIELDS + ["actual_k", "query_clean", "donors_clean", "member_ids"]:
            f["reference_" + c] = f["natural_" + c].combine_first(f["fallback_" + c])
        all_reference.append(
            f[
                KEY
                + [
                    "reference_" + c
                    for c in FIELDS + ["actual_k", "query_clean", "donors_clean", "member_ids"]
                ]
            ]
        )
    ref = pd.concat(all_reference, ignore_index=True)
    return natural, fixed, full, ref


def add_metadata(f, meta, aliases, arrays):
    f = f.merge(
        meta[["gauge", "country", "storm_id", "cutoff_utc"]].assign(case=meta.index),
        on="case",
        validate="many_to_one",
    )
    f["year"] = f.cutoff_utc.dt.year
    f["fixed_query"] = [
        bool(arrays[f"fixed_valid_{u}"][i]) for i, u in zip(f.case, f.offset_h, strict=True)
    ]
    f["actual_age_h"] = [
        float(arrays[f"q_{u}_{cap}"][i, 5])
        for i, u, cap in zip(f.case, f.offset_h, f.cap_h, strict=True)
    ]
    if VERIFICATION_LABELS:
        f["future_high_water"] = [
            int(VERIFICATION_LABELS[u][i]) for i, u in zip(f.case, f.offset_h, strict=True)
        ]
    return f.merge(aliases, on=["offset_h", "cap_h"], validate="many_to_many")


def summarize(frame, metadata, subset, effects, *, intervals=True, countries=None):
    rows = []
    for country in ["all", "NL", "DE"] if countries is None else countries:
        chosen = frame if country == "all" else frame[frame.country.eq(country)]
        for (scenario, k), g in chosen.groupby(["scenario", "target_k"], sort=True):
            for effect in effects:
                valid = g[g[effect].notna()]
                if valid.empty:
                    continue
                row = {
                    **metadata,
                    "population": subset,
                    "country": country,
                    "scenario": scenario,
                    "target_k": int(k),
                    "effect": effect,
                    "difference": mean_estimate(valid, effect),
                    "case_issues": len(valid),
                    "cases": valid.case.nunique(),
                    "storms": valid.storm_id.nunique(),
                    "gauges": valid.gauge.nunique(),
                    "actual_age_h": mean_estimate(valid, "actual_age_h"),
                    "clean_selected_fraction": float(
                        valid.get("clean_selected", pd.Series(False, index=valid.index)).mean()
                    ),
                }
                for field in [
                    "natural_crps_specific",
                    "matched_crps_specific",
                    "aug_crps_specific",
                    "full_crps_specific",
                    "reference_crps_specific",
                ]:
                    if field in valid:
                        row[field] = mean_estimate(valid, field)
                if intervals and k == 5:
                    for cluster in ["storm_id", "year"]:
                        ci = paired_interval(
                            valid, effect, cluster, block_universe=BLOCK_UNIVERSES.get(cluster)
                        )
                        row.update({cluster + "_" + key: value for key, value in ci.items()})
                rows.append(row)
    return rows


def opportunity_ledger(meta, aliases, arrays, baseline):
    """Every unique information state, including those with no verified prediction."""
    chunks = []
    for (u, cap), group in aliases.groupby(["offset_h", "cap_h"], sort=True):
        f = meta[["case_id", "gauge", "country", "storm_id"]].assign(
            case=meta.index,
            offset_h=u,
            cap_h=cap,
            scenarios="|".join(sorted(group.scenario)),
            outcome_valid=arrays[f"outcome_valid_{u}"],
            input_valid=np.isfinite(arrays[f"q_{u}_{cap}"]).all(axis=1)
            & np.isfinite(arrays[f"rain_{u}"]).all(axis=1),
            fixed_query=arrays[f"fixed_valid_{u}"],
        )
        chunks.append(f)
    ledger = pd.concat(chunks, ignore_index=True)
    key = ["case", "offset_h", "cap_h"]
    for role in ["natural_conventional", "fixed_conventional", "persistence", "generic"]:
        f = baseline[baseline.role.eq(role) & baseline.target_k.isin([0, 5])]
        f = f[key + ["actual_k"]].rename(columns={"actual_k": role + "_members"})
        ledger = ledger.merge(f, on=key, how="left", validate="one_to_one")
    ledger["conventional_status"] = np.select(
        [
            ~ledger.outcome_valid,
            ~ledger.input_valid,
            ledger.natural_conventional_members.isna(),
            ledger.natural_conventional_members.lt(5),
        ],
        [
            "unscored_missing_verification",
            "unavailable_input_history",
            "no_eligible_donors",
            "short_ensemble",
        ],
        default="full_five_members",
    )
    ledger["any_reference"] = (
        ledger[["natural_conventional_members", "persistence_members", "generic_members"]]
        .notna()
        .any(axis=1)
    )
    return ledger


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--wait", action="store_true")
    args = p.parse_args()
    while True:
        status = json.loads((OUT / "execution.json").read_text())
        if status["status"] == "completed":
            break
        if status["status"] == "failed":
            raise ValueError("Scoring failed; do not publish partial findings")
        if not args.wait:
            raise ValueError("Comparison is still running")
        time.sleep(10)
    prep = OUT / "preparation"
    meta = pd.read_parquet(prep / "cases.parquet")
    BLOCK_UNIVERSES.update(
        storm_id=sorted(meta.storm_id.unique()), year=sorted(meta.cutoff_utc.dt.year.unique())
    )
    aliases = pd.read_parquet(prep / "scenario_aliases.parquet")
    with np.load(prep / "inputs.npz") as z:
        arrays = {k: z[k] for k in z.files}
    # Hindsight-only severity strata. Never enter feature scaling or ranking.
    normalizer_path = ROOT / "results/storm_response/hourly_normalizer.parquet"
    normalizer = pd.read_parquet(normalizer_path)
    positions = normalizer.index.get_indexer(meta.cutoff_utc)
    for u in [0, 6, 12, 24]:
        label = np.full(len(meta), -1, dtype=np.int8)
        for gauge in normalizer.columns:
            ids = np.flatnonzero(meta.gauge.eq(gauge))
            values = normalizer[gauge].to_numpy()
            for i in ids:
                pos = positions[i] + u
                if positions[i] < 0 or pos + 24 >= len(values):
                    continue
                y, threshold = arrays[f"outcome_{u}"][i], values[pos + 1 : pos + 25]
                if np.isfinite(y).all() and np.isfinite(threshold).all():
                    label[i] = int((y >= threshold).any())
        VERIFICATION_LABELS[u] = label
    inputs = {
        str(p.relative_to(ROOT)): sha256(p)
        for p in [
            OUT / "execution.json",
            prep / "manifest.json",
            ROOT / "scripts/155_review_monitoring_analogues.py",
            ROOT / "src/monitoring_review.py",
        ]
    }
    inputs[str(normalizer_path.relative_to(ROOT))] = sha256(normalizer_path)
    summaries = []
    applicability = []
    baseline_cache = {}
    from src.eo_comparison import load_script

    runner = load_script("154_run_monitoring_analogues.py", "monitoring_review_expected_jobs")
    expected = {f"baseline__none__{pool}" for pool in ["same_gauge", "other_rivers"]}
    expected |= {
        f"{model}__{kind}__{pool}"
        for model in runner.MODELS
        for kind in ["recent", "monthly_snapshot"]
        for pool in ["same_gauge", "other_rivers"]
    }
    found = {p.name for p in (OUT / "scores").iterdir() if (p / "manifest.json").is_file()}
    if found != expected or status["completed_jobs"] != len(expected):
        raise ValueError("Full 42-job census required for this consolidated review")
    with fresh_output(OUT / "review") as work:
        paired_dir = work / "paired"
        paired_dir.mkdir()
        for pool in ["same_gauge", "other_rivers"]:
            source = OUT / "scores" / f"baseline__none__{pool}"
            base = pd.read_parquet(source / "scores.parquet")
            natural, fixed, full, ref = references(base, meta, aliases, arrays)
            simple = {}
            for role in ["persistence", "generic"]:
                simple[role] = base.loc[
                    base.role.eq(role), ["case", "offset_h", "cap_h", "crps_specific"]
                ].rename(columns={"crps_specific": role + "_crps_specific"})
            ledger = opportunity_ledger(meta, aliases, arrays, base)
            ledger.to_parquet(work / f"opportunity-ledger-{pool}.parquet", index=False)
            ledger.groupby(["country", "gauge", "conventional_status"]).size().rename(
                "unique_information_states"
            ).to_csv(work / f"opportunity-counts-{pool}.csv")
            b = natural.merge(full, on=["case", "offset_h", "target_k"], validate="many_to_one")
            b["degradation"] = b.natural_crps_specific - b.full_crps_specific
            for role in ["persistence", "generic", "natural_no_season"]:
                comparison = base[base.role.eq(role)][KEY + ["crps_specific"]].copy()
                if role != "natural_no_season":
                    comparison = comparison.drop(columns="target_k")
                    join = ["case", "offset_h", "cap_h"]
                else:
                    join = KEY
                comparison = comparison.rename(columns={"crps_specific": role + "_crps_specific"})
                b = b.merge(comparison, on=join, how="left", validate="many_to_one")
                b["conventional_vs_" + role] = b.natural_crps_specific - b[role + "_crps_specific"]
            b = add_metadata(b, meta, aliases, arrays)
            summaries.extend(
                summarize(
                    b[b.fixed_query],
                    {"model": "baseline", "kind": "none", "pool": pool},
                    "fixed_input_queries",
                    [
                        "degradation",
                        "conventional_vs_persistence",
                        "conventional_vs_generic",
                        "conventional_vs_natural_no_season",
                    ],
                )
            )
            baseline_cache[pool] = (natural, fixed, full, ref, simple)
            inputs[str((source / "manifest.json").relative_to(ROOT))] = sha256(
                source / "manifest.json"
            )
        for source in sorted((OUT / "scores").iterdir()):
            spec = json.loads((source / "manifest.json").read_text())
            if spec["model"] == "baseline":
                continue
            model, kind, pool = (spec[k] for k in ["model", "kind", "pool"])
            inputs[str((source / "manifest.json").relative_to(ROOT))] = sha256(
                source / "manifest.json"
            )
            raw = pd.read_parquet(source / "scores.parquet")
            natural, fixed, full, ref, simple = baseline_cache[pool]
            matched = prefix(raw, "matched_conventional", "matched")
            aug = prefix(raw, "eo_augmented", "aug")
            f = (
                aug.merge(matched, on=KEY, validate="one_to_one")
                .merge(natural, on=KEY, validate="one_to_one")
                .merge(fixed, on=KEY, validate="one_to_one")
            )
            f = f.merge(
                full, on=["case", "offset_h", "target_k"], how="left", validate="many_to_one"
            )
            f["representation_increment"] = f.aug_crps_specific - f.matched_crps_specific
            f["total_vs_natural"] = f.aug_crps_specific - f.natural_crps_specific
            for role, comparison in simple.items():
                f = f.merge(
                    comparison, on=["case", "offset_h", "cap_h"], how="left", validate="many_to_one"
                )
                f["eo_vs_" + role] = f.aug_crps_specific - f[role + "_crps_specific"]
            for horizon in [6, 12, 24]:
                f[f"total_h{horizon}"] = (
                    f[f"aug_crps_h{horizon}_specific"] - f[f"natural_crps_h{horizon}_specific"]
                )
            f["eo_archive_restriction"] = f.matched_crps_specific - f.fixed_crps_specific
            f["input_archive_restriction"] = f.fixed_crps_specific - f.natural_crps_specific
            np.testing.assert_allclose(
                f.representation_increment + f.eo_archive_restriction + f.input_archive_restriction,
                f.total_vs_natural,
                atol=1e-12,
                rtol=0,
            )
            f["full_members"] = (
                f[["aug_actual_k", "matched_actual_k", "natural_actual_k", "fixed_actual_k"]].min(
                    axis=1
                )
                >= f.target_k
            )
            f["clean_selected"] = (
                f[
                    [
                        "aug_query_clean",
                        "aug_donors_clean",
                        "matched_donors_clean",
                        "natural_donors_clean",
                        "fixed_donors_clean",
                        "full_donors_clean",
                    ]
                ]
                .eq(True)
                .fillna(False)
                .all(axis=1)
            )
            for field in [
                "aug_member_ids",
                "matched_member_ids",
                "natural_member_ids",
                "fixed_member_ids",
                "full_member_ids",
            ]:
                f["clean_selected"] &= f[field].map(
                    lambda ids: (
                        bool(meta.boundary_known.iloc[ids].all())
                        if isinstance(ids, (list, tuple, np.ndarray))
                        else False
                    )
                )
            f = add_metadata(f, meta, aliases, arrays)
            f.to_parquet(paired_dir / (source.name + ".parquet"), index=False)
            metadata = dict(model=model, kind=kind, pool=pool)
            primary = f[f.full_members & f.fixed_query]
            effects = [
                "representation_increment",
                "total_vs_natural",
                "eo_archive_restriction",
                "input_archive_restriction",
                "eo_vs_persistence",
                "eo_vs_generic",
            ]
            summaries.extend(summarize(primary, metadata, "full_members_fixed_inputs", effects))
            for label, mask in [
                ("future_p99_high_water", primary.future_high_water.eq(1)),
                ("no_future_p99_high_water", primary.future_high_water.eq(0)),
                ("undefined_future_p99", primary.future_high_water.eq(-1)),
            ]:
                summaries.extend(
                    summarize(
                        primary[mask],
                        metadata,
                        label,
                        ["total_vs_natural", "representation_increment"],
                        intervals=False,
                    )
                )
            summaries.extend(
                summarize(
                    primary,
                    metadata,
                    "full_members_horizons",
                    ["total_h6", "total_h12", "total_h24"],
                    intervals=kind == "recent" and pool == "same_gauge",
                    countries=["all"],
                )
            )
            sequence = primary.copy()
            sequence["scenario"] += "_u" + sequence.offset_h.astype(str)
            summaries.extend(
                summarize(
                    sequence,
                    metadata,
                    "issue_sequence_points",
                    effects,
                    intervals=False,
                    countries=["all"],
                )
            )
            summaries.extend(
                summarize(f, metadata, "all_supported_members", effects, intervals=False)
            )
            summaries.extend(
                summarize(
                    primary[primary.clean_selected],
                    metadata,
                    "clean_selected_no_reranking",
                    effects,
                    intervals=False,
                )
            )
            # Direct change in EO increment versus zero delay on the exact same cases/issues.
            zero = primary[primary.scenario.eq("delay_0")][
                ["case", "offset_h", "target_k", "total_vs_natural"]
            ].rename(columns={"total_vs_natural": "zero_delta"})
            interaction = primary.merge(
                zero, on=["case", "offset_h", "target_k"], validate="many_to_one"
            )
            interaction["age_interaction"] = interaction.total_vs_natural - interaction.zero_delta
            summaries.extend(
                summarize(interaction, metadata, "matched_age_interaction", ["age_interaction"])
            )
            # Full available reference: natural matching, else last-Q, else generic history.
            # Unsupported EO genuinely falls back instead of disappearing from the census.
            e = ref.merge(aug, on=KEY, how="left", validate="one_to_one")
            e["used_eo"] = e.aug_crps_specific.notna()
            e["model_crps_specific"] = e.aug_crps_specific.combine_first(e.reference_crps_specific)
            e["end_to_end_increment"] = e.model_crps_specific - e.reference_crps_specific
            e = add_metadata(e, meta, aliases, arrays)
            summaries.extend(
                summarize(e, metadata, "end_to_end_with_fallback", ["end_to_end_increment"])
            )
            for (scenario, k, country), g in e.groupby(["scenario", "target_k", "country"]):
                applicability.append(
                    {
                        **metadata,
                        "scenario": scenario,
                        "target_k": k,
                        "country": country,
                        "case_issues": len(g),
                        "eo_case_issues": int(g.used_eo.sum()),
                        "eo_fraction": float(g.used_eo.mean()),
                        "storms": g.storm_id.nunique(),
                    }
                )
            print("reviewed", source.name, flush=True)
        # Point comparisons on identical all-ten cases, not model-available cohorts.
        for pool in ["same_gauge", "other_rivers"]:
            for kind in ["recent", "monthly_snapshot"]:
                cohort = None
                for model in runner.MODELS:
                    path = paired_dir / f"{model}__{kind}__{pool}.parquet"
                    f = pd.read_parquet(path)
                    keys = pd.MultiIndex.from_frame(
                        f.loc[f.full_members & f.fixed_query, KEY + ["scenario"]]
                    )
                    cohort = keys if cohort is None else cohort.intersection(keys)
                for model in runner.MODELS:
                    f = pd.read_parquet(paired_dir / f"{model}__{kind}__{pool}.parquet")
                    f = f[pd.MultiIndex.from_frame(f[KEY + ["scenario"]]).isin(cohort)]
                    summaries.extend(
                        summarize(
                            f,
                            dict(model=model, kind=kind, pool=pool),
                            "all_ten_intersection",
                            ["representation_increment", "total_vs_natural"],
                            intervals=False,
                        )
                    )
        table = pd.DataFrame(summaries)
        table.to_parquet(work / "contrasts.parquet", index=False)
        table.to_csv(work / "contrasts.csv", index=False)
        pd.DataFrame(applicability).to_csv(work / "applicability.csv", index=False)
        # All encoder estimates; no winner selection in the figure or headline.
        plot = table[
            (table.pool == "same_gauge")
            & (table.kind == "recent")
            & (table.country == "all")
            & (table.target_k == 5)
            & (table.population == "full_members_fixed_inputs")
            & (table.effect == "total_vs_natural")
            & table.scenario.str.startswith("delay_")
        ]
        fig, ax = plt.subplots(figsize=(10, 6))
        for model, g in plot.groupby("model"):
            g = g.assign(age=g.scenario.str.removeprefix("delay_").astype(int)).sort_values("age")
            ax.plot(g.age, g.difference, marker="o", label=model)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set(
            xlabel="Declared delivery delay (hours)",
            ylabel="EO minus natural-archive conventional CRPS (mm/h)",
            title="All ten EO encoders: matched full-member input-complete cases\nNegative = lower error; own-model populations differ",
        )
        ax.legend(fontsize=8, ncol=2)
        fig.tight_layout()
        fig.savefig(work / "eo-delay-curves.png", dpi=150)
        plt.close(fig)
        report = dict(
            status="completed",
            sources_sha256=inputs,
            outputs_sha256={
                str(p.relative_to(work)): sha256(p) for p in work.rglob("*") if p.is_file()
            },
            note="Paired differences; 999 intact-storm/year draws within each matched population. Original gauge/issue weights fixed. Cross-model cohorts differ; no winner inference.",
        )
        (work / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Review completed", flush=True)


if __name__ == "__main__":
    main()
