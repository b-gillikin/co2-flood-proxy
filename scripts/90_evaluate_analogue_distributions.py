#!/usr/bin/env python3
"""Evaluate specified empirical discharge distributions from saved analogue sets.

Retrospective full-era p99, finalized records, inherited 72h scoring cohorts.
No retrieval, fitting, calibration, forecast claim or new human verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analogue_distributions import (
    cluster_intervals,
    eligible_archive,
    group_weights,
    score_distribution,
)

OUT = ROOT / "results/basin_ai_analogue_distributions"
SOURCE = ROOT / "results/basin_ai_cross_border_completion"
READY = ROOT / "results/basin_ai_event_interpretation_ready"
DEFINITION = ROOT / "results/basin_ai_event_definition_sensitivity"
ARMS = {
    "q_only": ["r1", "raw_state", "ttm_ordered_state"],
    "rain_matched": ["r0", "r1", "raw_state", "ttm_ordered_state"],
    "context": ["temporal", "area", "identity", "static_2017", "alphaearth"],
}
CONFIG = ["cohort", "scenario", "analysis"]
SET_KEYS = [*CONFIG, "target_k", "query_event_id", "method"]
CRPS_METRICS = ["crps_mean_24h", "crps_h6", "crps_h12", "crps_h24"]
SEED, DRAWS = 20261013, 9999


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    """Verify saved artifacts, rebuild cohort masks, check replayed source curves."""
    hashes = {}

    def bind(path, expected=None):
        digest = sha256(path)
        if expected is not None and digest != expected:
            raise ValueError("Changed input: " + str(path))
        hashes[str(path.relative_to(ROOT))] = digest

    manifest = json.loads((SOURCE / "manifest.json").read_text())
    bind(SOURCE / "manifest.json")
    for name in [
        "selected_donors.csv",
        "event_assessments.csv",
        "archive_coverage.csv",
        "rainfall_event_coverage.csv",
        "context_event_coverage.csv",
    ]:
        bind(SOURCE / name, manifest["outputs_sha256"][name])
    for name in ["event_inventory.csv", "q_only_signatures.csv"]:
        path = READY / name
        bind(path, manifest["input_sha256"][str(path.relative_to(ROOT))])
    meta = pd.read_csv(
        READY / "event_inventory.csv", float_precision="round_trip", parse_dates=["onset_utc"]
    )
    sig = pd.read_csv(
        READY / "q_only_signatures.csv", float_precision="round_trip", parse_dates=["onset_utc"]
    )
    if meta.event_id.duplicated().any() or sig.event_id.duplicated().any():
        raise ValueError("Duplicate event identifiers")
    for field in ["country", "physical_river_group", "p99_m3s"]:
        sig[field] = sig.event_id.map(meta.set_index("event_id")[field])
    sig["eligible_q_only"] = sig.complete_scoring_sample & sig.outcome_peak_over_p99_72h.notna()
    rain = pd.read_csv(SOURCE / "rainfall_event_coverage.csv").set_index("event_id")
    # These ten features are precisely script 65's conventional signatures.
    features = [
        "rain_sum_6h_mm",
        "rain_sum_24h_mm",
        "rain_sum_72h_mm",
        "rain_sum_168h_mm",
        "rain_max_1h_24h_mm",
        "q_over_p99_m24",
        "q_over_p99_m6",
        "q_over_p99_onset",
        "q_change_6h_over_p99",
        "q_change_24h_over_p99",
    ]
    sig["eligible_rain_matched"] = (
        sig.eligible_q_only
        & sig.event_id.map(rain.complete_scoring_sample)
        & sig.event_id.map(rain[features].notna().all(axis=1))
    )
    context = pd.read_csv(SOURCE / "context_event_coverage.csv").set_index("event_id")
    sig["eligible_context"] = (
        sig.eligible_q_only
        & sig.common_representation_sample
        & sig.event_id.map(context.context_available)
    )
    response_path = DEFINITION / "p99_72/response_p99.parquet"
    dm = json.loads((DEFINITION / "manifest.json").read_text())
    bind(DEFINITION / "manifest.json")
    bind(response_path, dm["outputs_sha256"]["p99_72/response_p99.parquet"])
    response = pd.read_parquet(response_path).reindex(meta.event_id)
    frames = []
    for relative in [
        "results/basin_ai_event_library/event_windows.parquet",
        "results/basin_ai_german_extension/german_event_windows.parquet",
    ]:
        bind(ROOT / relative, manifest["input_sha256"][relative])
        frames.append(
            pd.read_parquet(
                ROOT / relative, columns=["event_id", "relative_hour", "target_discharge_m3s"]
            )
        )
    windows = pd.concat(frames, ignore_index=True)
    if windows.duplicated(["event_id", "relative_hour"]).any():
        raise ValueError("Duplicate source event/hour")
    original = windows.pivot(
        index="event_id", columns="relative_hour", values="target_discharge_m3s"
    )
    normalized = original.reindex(index=meta.event_id, columns=range(1, 73)).div(
        meta.set_index("event_id").p99_m3s, axis=0
    )
    np.testing.assert_allclose(response, normalized, atol=1e-12, rtol=0, equal_nan=True)
    if not response.columns.equals(pd.Index(range(1, 73), name=response.columns.name)):
        raise ValueError("Response hour labels changed")
    donors = pd.read_csv(SOURCE / "selected_donors.csv", float_precision="round_trip")
    donors = donors.loc[donors.policy.eq("pooled")].copy()
    saved = pd.read_csv(SOURCE / "event_assessments.csv", float_precision="round_trip")
    saved = saved.loc[saved.policy.eq("pooled") & saved.target_k.eq(10)].copy()
    sentinels_path = ROOT / "results/basin_ai_information_review/outcome_blind_sentinels.csv"
    bind(sentinels_path)
    sentinels = pd.read_csv(sentinels_path)
    return sig, meta, response, donors, saved, sentinels, hashes


def event_summary(hourly):
    fields = [
        "crps",
        "median_absolute_error",
        "mean_squared_error",
        "coverage50",
        "coverage80",
        "width50",
        "width80",
        "below50",
        "above50",
        "below80",
        "above80",
    ]
    result = {f"{name}_mean_24h": float(hourly[name].mean()) for name in fields}
    for h in [6, 12, 24]:
        row = hourly.loc[hourly.lead_hour.eq(h)].iloc[0]
        for name in fields:
            result[f"{name}_h{h}"] = float(row[name])
    return result


def config_tag(cohort, scenario, analysis):
    return dict(cohort=cohort, scenario=scenario, analysis=analysis)


def evaluate(out, sig, meta, response, donors, saved):
    events, coverage, archive_sets, all_members = [], [], [], []
    details = []
    metadata = meta.set_index("event_id")
    earliest = meta.groupby("storm_id").onset_utc.min().dt.year
    for cohort, arms in ARMS.items():
        for scenario in ["all_rivers", "other_rivers"]:
            for analysis in ["main", "quality_sensitivity"]:
                tags = config_tag(cohort, scenario, analysis)
                name = "__".join(tags.values())
                eligibility = sig[f"eligible_{cohort}"] & (
                    ~sig.measurement_concern if analysis == "quality_sensitivity" else True
                )
                pool = sig.loc[eligibility].copy()
                d = donors.loc[
                    donors.cohort.eq(cohort)
                    & donors.scenario.eq(scenario)
                    & donors.analysis.eq(analysis)
                ]
                old = saved.loc[
                    saved.cohort.eq(cohort)
                    & saved.scenario.eq(scenario)
                    & saved.analysis.eq(analysis)
                ].set_index(["arm", "query_event_id"])
                sets = {
                    (arm, eid): g.sort_values("rank")
                    for (arm, eid), g in d.groupby(["arm", "query_event_id"], sort=True)
                }
                available = {eid for arm, eid in sets if arm == arms[0]}
                for arm in arms:
                    if {eid for a, eid in sets if a == arm} != available:
                        raise ValueError("Mismatched saved query populations")
                memberships, hour_rows = [], []
                for query in pool.itertuples(index=False):
                    eid = query.event_id
                    prior = eligible_archive(pool, query, scenario == "other_rivers")
                    n, groups = len(prior), prior.storm_id.nunique()
                    if bool(n) != (eid in available):
                        raise ValueError("Saved archive availability mismatch")
                    coverage.append(
                        dict(
                            **tags,
                            query_event_id=eid,
                            query_country=query.country,
                            inherited_scoring_eligible=True,
                            candidate_events=n,
                            candidate_groups=groups,
                            status="available" if n else "no_completed_prior_group",
                        )
                    )
                    if not n:
                        continue
                    q = response.loc[eid, 1:24].to_numpy(float)
                    if not np.isfinite(q).all():
                        raise ValueError("Unexpected incomplete verification response")
                    archive_id = f"{name}|{eid}"
                    weights = group_weights(prior.storm_id)
                    archive_values = response.loc[prior.event_id, 1:24].to_numpy(float)
                    archive = score_distribution(q, archive_values, weights)
                    persistence = score_distribution(
                        q, np.full((1, 24), query.q_over_p99_onset), [1]
                    )
                    membership = pd.DataFrame(
                        {
                            "archive_id": archive_id,
                            "query_event_id": eid,
                            "candidate_event_id": prior.event_id.to_numpy(),
                            "candidate_storm_id": prior.storm_id.to_numpy(),
                            "weight": weights,
                        }
                    )
                    memberships.append(membership)
                    archive_sets.append(
                        dict(
                            **tags,
                            archive_id=archive_id,
                            query_event_id=eid,
                            candidate_events=n,
                            candidate_groups=groups,
                        )
                    )
                    for arm in arms:
                        group = sets[arm, eid]
                        reference = old.loc[(arm, eid)]
                        if (
                            int(reference.candidate_count) != n
                            or int(reference.candidate_storm_count) != groups
                        ):
                            raise ValueError("Original candidate counts do not reproduce")
                        if not group["rank"].tolist() == list(range(1, min(10, groups) + 1)):
                            raise ValueError("Nonconsecutive or unexpected saved donor ranks")
                        if group.analogue_storm_id.duplicated().any():
                            raise ValueError("Multiple donors from one regional group")
                        if not set(group.analogue_event_id).issubset(set(prior.event_id)):
                            raise ValueError("Selected donor outside eligible archive")
                    for k in [5, 10]:
                        support = min(k, groups)
                        category = "1-4" if support < 5 else "5-9" if support < 10 else "10"
                        common = dict(
                            **tags,
                            target_k=k,
                            query_event_id=eid,
                            query_storm_id=query.storm_id,
                            storm_year=int(earliest.loc[query.storm_id]),
                            query_onset_utc=query.onset_utc,
                            query_country=query.country,
                            query_river=query.physical_river_group,
                            query_gauge=query.gauge,
                            measurement_concern=bool(query.measurement_concern),
                            selected_donor_count=support,
                            donor_count_category=category,
                            archive_id=archive_id,
                            candidate_events=n,
                            candidate_groups=groups,
                            p99_m3s=float(metadata.loc[eid, "p99_m3s"]),
                        )
                        methods = {"archive": (archive, n), "persistence": (persistence, 1)}
                        for arm in arms:
                            ranked = sets[arm, eid]
                            selected = ranked.loc[ranked["rank"].le(k)]
                            x = response.loc[selected.analogue_event_id, 1:24].to_numpy(float)
                            methods[arm] = (score_distribution(q, x, np.ones(len(x))), len(x))
                        for method, (scores, count) in methods.items():
                            item = dict(**common, method=method, actual_member_count=count)
                            events.append({**item, **event_summary(scores)})
                            # Persist interval scores, quantiles and verification values in p99 units.
                            hourly = scores.copy()
                            for field in [*CONFIG, "target_k", "query_event_id", "method"]:
                                hourly[field] = item[field]
                            hour_rows.append(hourly)
                for query in sig.loc[~eligibility].itertuples(index=False):
                    coverage.append(
                        dict(
                            **tags,
                            query_event_id=query.event_id,
                            query_country=query.country,
                            inherited_scoring_eligible=False,
                            candidate_events=np.nan,
                            candidate_groups=np.nan,
                            status="measurement_quality_exclusion"
                            if analysis == "quality_sensitivity" and query.measurement_concern
                            else "outside_inherited_scoring_cohort",
                        )
                    )
                hourly = pd.concat(hour_rows, ignore_index=True)
                membership = pd.concat(memberships, ignore_index=True)
                hourly.to_parquet(out / "hourly_scores" / f"{name}.parquet", index=False)
                membership.to_parquet(out / "archive_membership" / f"{name}.parquet", index=False)
                all_members.append(len(membership))
                details.append(len(hourly))
                print(
                    f"{name}: {len(pool)} inherited cases, {len(available)} with archive; "
                    f"{len(hourly)} hourly scores",
                    flush=True,
                )
    return (
        pd.DataFrame(events),
        pd.DataFrame(coverage),
        pd.DataFrame(archive_sets),
        dict(archive_membership_rows=sum(all_members), hourly_score_rows=sum(details)),
    )


def summarize(events):
    statistical = [
        c
        for c in events
        if c.endswith("_mean_24h") or any(c.endswith(f"_h{h}") for h in [6, 12, 24])
    ]
    rows = events.copy()
    rows["population"] = rows.query_country
    rows = pd.concat([rows, events.assign(population="ALL")], ignore_index=True)
    keys = [*CONFIG, "target_k", "method", "population"]

    def aggregate(frame, columns):
        means = frame.groupby(columns, sort=True)[statistical].mean()
        counts = frame.groupby(columns, sort=True).agg(
            queries=("query_event_id", "size"),
            regional_groups=("query_storm_id", "nunique"),
            min_selected_donors=("selected_donor_count", "min"),
            max_selected_donors=("selected_donor_count", "max"),
        )
        return counts.join(means).reset_index()

    summary = aggregate(rows, keys)
    by_river = aggregate(events, [*CONFIG, "target_k", "method", "query_country", "query_river"])
    by_count = aggregate(rows, [*keys, "donor_count_category"])
    # No pooling of cubic metres/second across gauges of different discharge scale.
    units = events.copy()
    for field in statistical:
        if field.startswith(("crps_", "median_absolute_error_", "width")):
            units[field] *= units.p99_m3s
        elif field.startswith("mean_squared_error_"):
            units[field] *= units.p99_m3s**2
    by_gauge = aggregate(units, [*CONFIG, "target_k", "method", "query_country", "query_gauge"])
    return summary, by_river, by_count, by_gauge


def paired_intervals(events):
    records, differences = [], []
    for config, group in events.groupby([*CONFIG, "target_k"], sort=True):
        tags = dict(zip([*CONFIG, "target_k"], config, strict=True))
        arms = ARMS[tags["cohort"]]
        comparisons = [("archive", a) for a in arms]
        comparisons += (
            [("raw_state", "ttm_ordered_state")]
            if tags["cohort"] != "context"
            else [(a, "alphaearth") for a in ["temporal", "area", "identity", "static_2017"]]
        )
        if tags["cohort"] == "rain_matched":
            comparisons += [("r0", "ttm_ordered_state"), ("r0", "raw_state")]
        for population in ["ALL", "NL", "DE"]:
            sub = group if population == "ALL" else group.loc[group.query_country.eq(population)]
            reference = sub.loc[sub.method.eq("archive")].set_index("query_event_id").sort_index()
            if reference.empty:
                continue
            values, columns = [], []
            for ref, test in comparisons:
                a = sub.loc[sub.method.eq(ref)].set_index("query_event_id").sort_index()
                b = sub.loc[sub.method.eq(test)].set_index("query_event_id").sort_index()
                pd.testing.assert_index_equal(a.index, reference.index)
                pd.testing.assert_index_equal(a.index, b.index)
                np.testing.assert_array_equal(a.selected_donor_count, b.selected_donor_count)
                delta = b[CRPS_METRICS].to_numpy() - a[CRPS_METRICS].to_numpy()
                values.append(delta)
                columns.extend([(ref, test, metric) for metric in CRPS_METRICS])
                if population == "ALL":
                    for j, metric in enumerate(CRPS_METRICS):
                        diff = reference[
                            ["query_storm_id", "storm_year", "query_country"]
                        ].reset_index()
                        diff["difference"] = delta[:, j]
                        differences.append(
                            diff.assign(**tags, reference=ref, challenger=test, metric=metric)
                        )
            matrix = np.column_stack(values)
            for unit in ["query_storm_id", "storm_year"]:
                draws = cluster_intervals(matrix, reference[unit], DRAWS, SEED)
                for j, (ref, test, metric) in enumerate(columns):
                    estimate = dict(
                        **tags,
                        population=population,
                        reference=ref,
                        challenger=test,
                        metric=metric,
                        resampling_unit=unit,
                        difference=float(matrix[:, j].mean()),
                        queries=len(reference),
                        clusters=reference[unit].nunique(),
                        seed=SEED,
                    )
                    if draws is None:
                        estimate.update(
                            status="too_few_clusters",
                            lower=np.nan,
                            upper=np.nan,
                            draws=0,
                            finite_draws=0,
                        )
                    else:
                        lower, upper = np.quantile(draws[:, j], [0.025, 0.975])
                        estimate.update(
                            status="estimated",
                            lower=lower,
                            upper=upper,
                            draws=DRAWS,
                            finite_draws=int(np.isfinite(draws[:, j]).sum()),
                        )
                    records.append(estimate)
    return pd.DataFrame(records), pd.concat(differences, ignore_index=True)


def figures(out, summary, events, sentinels, response, donors):
    colors = {
        "archive": "#555555",
        "persistence": "#e69f00",
        "r0": "#009e73",
        "r1": "#56b4e9",
        "raw_state": "#0072b2",
        "ttm_ordered_state": "#cc79a7",
        "temporal": "#cc79a7",
        "alphaearth": "#d55e00",
        "area": "#8b6d31",
        "identity": "#9b9b9b",
        "static_2017": "#882255",
    }
    profiles = []
    countries = events.drop_duplicates("query_event_id").set_index("query_event_id").query_country
    for cohort in ARMS:
        frame = pd.read_parquet(out / f"hourly_scores/{cohort}__all_rivers__main.parquet")
        frame = frame.loc[frame.target_k.eq(5)].copy()
        frame["population"] = frame.query_event_id.map(countries)
        frame = pd.concat([frame, frame.assign(population="ALL")], ignore_index=True)
        profiles.append(
            frame.groupby(["cohort", "method", "population", "lead_hour"], sort=True)
            .agg(
                crps=("crps", "mean"),
                coverage80=("coverage80", "mean"),
                width80=("width80", "mean"),
                queries=("query_event_id", "size"),
            )
            .reset_index()
        )
    profile = pd.concat(profiles, ignore_index=True)
    profile.to_csv(out / "lead_profiles.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    for ax, cohort in zip(axes, ARMS, strict=True):
        data = profile.loc[profile.cohort.eq(cohort) & profile.population.eq("ALL")]
        for method, curve in data.groupby("method", sort=True):
            ax.plot(curve.lead_hour, curve.crps, color=colors[method], label=method)
        ax.set(
            title=cohort.replace("_", " "), xlabel="Response hour", ylabel="CRPS (Q / own era-p99)"
        )
        ax.legend(fontsize=7)
    fig.suptitle("Retrospective analogue distributions: matched populations differ across panels")
    fig.savefig(out / "crps_lead_profile.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    for ax, cohort in zip(axes, ARMS, strict=True):
        data = summary.loc[
            summary.cohort.eq(cohort)
            & summary.scenario.eq("all_rivers")
            & summary.analysis.eq("main")
            & summary.target_k.eq(5)
            & summary.population.eq("ALL")
            & summary.method.ne("persistence")
        ]
        for row in data.itertuples():
            ax.scatter(
                row.width80_h24, row.coverage80_h24, color=colors[row.method], label=row.method
            )
        ax.axhline(0.8, color="gray", ls="--")
        ax.set(
            title=cohort.replace("_", " "),
            xlabel="Mean 80% interval width (Q/p99)",
            ylabel="Observed coverage at +24h",
            ylim=(0, 1),
        )
        ax.legend(fontsize=7)
    fig.suptitle("Nominal 80% pointwise ranges: empirical quantiles are coarse with five donors")
    fig.savefig(out / "coverage_width.png", dpi=160)
    plt.close(fig)
    keep = events.loc[
        events.cohort.eq("q_only")
        & events.scenario.eq("all_rivers")
        & events.analysis.eq("main")
        & events.target_k.eq(5)
        & events.method.eq("ttm_ordered_state")
    ]
    illustrated = sentinels.loc[sentinels.query_event_id.isin(keep.query_event_id)].copy()
    illustrated.to_csv(out / "illustrated_sentinels.csv", index=False)
    sentinel_scores = pd.read_parquet(out / "hourly_scores/q_only__all_rivers__main.parquet")
    sentinel_scores = sentinel_scores.loc[sentinel_scores.target_k.eq(5)]
    for page, first in enumerate(range(0, len(illustrated), 6), start=1):
        fig, axes = plt.subplots(3, 2, figsize=(13, 11), constrained_layout=True)
        for ax, sentinel in zip(
            axes.flat, illustrated.iloc[first : first + 6].itertuples(), strict=False
        ):
            eid = sentinel.query_event_id
            part = sentinel_scores.loc[sentinel_scores.query_event_id.eq(eid)]
            for method, color in [("archive", "#a66b00"), ("ttm_ordered_state", "#176fa8")]:
                s = part.loc[part.method.eq(method)].sort_values("lead_hour")
                ax.fill_between(s.lead_hour, s.lower80, s.upper80, color=color, alpha=0.13)
                ax.plot(s.lead_hour, s["median"], color=color, label=method + " median / 80% range")
            ids = donors.loc[
                donors.cohort.eq("q_only")
                & donors.scenario.eq("all_rivers")
                & donors.analysis.eq("main")
                & donors.arm.eq("ttm_ordered_state")
                & donors.query_event_id.eq(eid)
                & donors["rank"].le(5),
                "analogue_event_id",
            ]
            for candidate in ids:
                ax.plot(
                    range(1, 25), response.loc[candidate, 1:24], color="#176fa8", alpha=0.18, lw=0.6
                )
            ax.plot(
                range(1, 25),
                response.loc[eid, 1:24],
                color="black",
                lw=1.6,
                label="Observed verification",
            )
            ax.set(title=eid, xlabel="Response hour", ylabel="Q / own era-p99")
            ax.legend(fontsize=6)
        for ax in list(axes.flat)[len(illustrated.iloc[first : first + 6]) :]:
            ax.set_visible(False)
        fig.suptitle(
            "Existing outcome-independent sentinels; AI illustration, not human validation"
        )
        fig.savefig(out / "sentinel_pages" / f"page_{page:02d}.png", dpi=140)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    for name in ["hourly_scores", "archive_membership", "sentinel_pages"]:
        (out / name).mkdir(exist_ok=True)
    sig, meta, response, donors, saved, sentinels, hashes = load_inputs()
    sig.to_csv(out / "cohort_inventory.csv", index=False)
    meta.to_csv(out / "event_metadata.csv", index=False)
    response.to_parquet(out / "response_p99.parquet")
    donors.to_parquet(out / "selected_donor_references.parquet", index=False)
    events, coverage, archives, counts = evaluate(out, sig, meta, response, donors, saved)
    if events.duplicated(SET_KEYS).any():
        raise ValueError("Duplicate distribution score sets")
    events.to_parquet(out / "event_scores.parquet", index=False)
    coverage.to_csv(out / "query_coverage.csv", index=False)
    archives.to_csv(out / "archive_sets.csv", index=False)
    summary, river, count, gauge = summarize(events)
    for name, frame in [
        ("summary", summary),
        ("summary_by_river", river),
        ("summary_by_donor_count", count),
        ("summary_by_gauge_m3s", gauge),
    ]:
        frame.to_csv(out / f"{name}.csv", index=False)
    print("Computing joint paired group/year intervals", flush=True)
    intervals, differences = paired_intervals(events)
    intervals.to_csv(out / "paired_intervals.csv", index=False)
    differences.to_parquet(out / "paired_differences.parquet", index=False)
    figures(out, summary, events, sentinels, response, donors)
    validation = dict(
        **counts,
        held_events=len(meta),
        event_score_sets=len(events),
        reconstructed_archives=len(archives),
        original_candidate_counts_match=True,
        source_response_replay=True,
        cohort_pairing_checked=True,
        interval_rows=len(intervals),
        estimated_intervals=int(intervals.status.eq("estimated").sum()),
        bootstrap_failures=0,
        sampled_events=0,
        trained_models=0,
        human_labels_assigned=0,
    )
    (out / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    manifest = dict(
        input_sha256=hashes,
        code_version=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        source_sha256={
            str(p.relative_to(ROOT)): sha256(p)
            for p in [Path(__file__), ROOT / "src/analogue_distributions.py"]
        },
        seed=SEED,
        bootstrap_draws=DRAWS,
        response_hours=list(range(1, 25)),
        readouts=[6, 12, 24],
        primary_metric="mean exact empirical CRPS over response hours 1-24",
        primary_setting="pooled / all_rivers / main / target_k=5",
        normalizer="existing full-rating-era p99; retrospective",
        eligibility="unchanged inherited complete-72h outcome cohorts",
        archive_weighting="equal regional group mass / equal within-group event mass",
        quantiles="left inverse weighted empirical CDF; tolerance 1e-14; closed coverage",
        year_blocks="year of earliest full-inventory onset in each regional group",
        model_selection="none; all saved arms and fixed 5/10 donor settings",
        versions=dict(python=sys.version.split()[0], numpy=np.__version__, pandas=pd.__version__),
        outputs_sha256={
            str(p.relative_to(out)): sha256(p)
            for p in sorted(out.rglob("*"))
            if p.is_file() and p.name not in {"manifest.json", "independent_audit.json"}
        },
    )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(validation), flush=True)


if __name__ == "__main__":
    main()
