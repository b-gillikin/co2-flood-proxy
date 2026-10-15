#!/usr/bin/env python3
"""Independently reconstruct membership, finite-distribution scores and summaries.

The score uses CDF-gap integration, not the runner's weighted order-statistic
identity. No import of the runner or its scoring helpers is needed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "results/basin_ai_analogue_distributions"
SOURCE = ROOT / "results/basin_ai_cross_border_completion"
READY = ROOT / "results/basin_ai_event_interpretation_ready"
CONFIG = ["cohort", "scenario", "analysis"]
KEYS = [*CONFIG, "target_k", "query_event_id", "method"]
FIELDS = [
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


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=0, equal_nan=True)
    delta = np.abs(np.asarray(actual, float) - np.asarray(expected, float))
    return float(np.nanmax(delta)) if np.isfinite(delta).any() else 0.0


def cdf_scores(observed, trajectories, probabilities):
    """CRPS via integral F(x)(1-F(x)) dx for the half-pairwise term."""
    x, y = np.asarray(trajectories, float), np.asarray(observed, float)
    w = np.asarray(probabilities, float)
    w = w / w.sum()
    order = np.argsort(x, axis=0, kind="stable")
    z = np.take_along_axis(x, order, axis=0)
    mass = w[order]
    cdf = mass.cumsum(axis=0)
    spread = (np.diff(z, axis=0) * cdf[:-1] * (1 - cdf[:-1])).sum(axis=0)
    result = {
        "observed": y,
        "mean": (x * w[:, None]).sum(axis=0),
        "crps": (np.abs(x - y) * w[:, None]).sum(axis=0) - spread,
    }
    for name, probability in [
        ("median", 0.5),
        ("lower50", 0.25),
        ("upper50", 0.75),
        ("lower80", 0.1),
        ("upper80", 0.9),
    ]:
        # Search leads independently; explicitly include the complete final mass.
        values = []
        for h in range(x.shape[1]):
            cumulative = cdf[:, h].copy()
            cumulative[-1] = 1
            values.append(z[np.searchsorted(cumulative, probability - 1e-14, side="left"), h])
        result[name] = np.asarray(values)
    result["median_absolute_error"] = np.abs(result["median"] - y)
    result["mean_squared_error"] = (result["mean"] - y) ** 2
    for level in [50, 80]:
        lo, hi = result[f"lower{level}"], result[f"upper{level}"]
        result[f"coverage{level}"] = (y >= lo) & (y <= hi)
        result[f"width{level}"] = hi - lo
        result[f"below{level}"] = y < lo
        result[f"above{level}"] = y > hi
    return result


def original_pools():
    sig = pd.read_csv(
        READY / "q_only_signatures.csv", float_precision="round_trip", parse_dates=["onset_utc"]
    )
    meta = pd.read_csv(
        READY / "event_inventory.csv", float_precision="round_trip", parse_dates=["onset_utc"]
    ).set_index("event_id")
    rain = pd.read_csv(SOURCE / "rainfall_event_coverage.csv").set_index("event_id")
    context = pd.read_csv(SOURCE / "context_event_coverage.csv").set_index("event_id")
    fields = [
        c for c in rain if c not in {"country", "rain_history_fraction", "complete_scoring_sample"}
    ]
    sig["country"] = sig.event_id.map(meta.country)
    sig["physical_river_group"] = sig.event_id.map(meta.physical_river_group)
    sig["eligible_q_only"] = sig.complete_scoring_sample & sig.outcome_peak_over_p99_72h.notna()
    sig["eligible_rain_matched"] = sig.eligible_q_only & sig.event_id.map(
        rain.complete_scoring_sample & rain[fields].notna().all(axis=1)
    )
    sig["eligible_context"] = (
        sig.eligible_q_only
        & sig.common_representation_sample
        & sig.event_id.map(context.context_available)
    )
    return sig, meta


def audit_sets(out, response, events):
    sig, meta = original_pools()
    inventory = pd.read_csv(out / "cohort_inventory.csv").set_index("event_id")
    for cohort in ["q_only", "rain_matched", "context"]:
        np.testing.assert_array_equal(
            inventory.loc[sig.event_id, f"eligible_{cohort}"], sig[f"eligible_{cohort}"]
        )
    # Reconstruct all normalized responses independently from the original Q observations.
    source = pd.concat(
        [
            pd.read_parquet(ROOT / p, columns=["event_id", "relative_hour", "target_discharge_m3s"])
            for p in [
                "results/basin_ai_event_library/event_windows.parquet",
                "results/basin_ai_german_extension/german_event_windows.parquet",
            ]
        ],
        ignore_index=True,
    )
    original = source.pivot(
        index="event_id", columns="relative_hour", values="target_discharge_m3s"
    )
    maximum = check(
        response,
        original.reindex(index=response.index, columns=range(1, 73)).div(meta.p99_m3s, axis=0),
    )
    donors = pd.read_parquet(out / "selected_donor_references.parquet")
    original_donors = pd.read_csv(SOURCE / "selected_donors.csv", float_precision="round_trip")
    pd.testing.assert_frame_equal(
        donors.reset_index(drop=True),
        original_donors.loc[original_donors.policy.eq("pooled")].reset_index(drop=True),
    )
    old = pd.read_csv(SOURCE / "event_assessments.csv", float_precision="round_trip")
    old = old.loc[old.policy.eq("pooled") & old.target_k.eq(10)]
    coverage = pd.read_csv(out / "query_coverage.csv").set_index([*CONFIG, "query_event_id"])
    sets = pd.read_csv(out / "archive_sets.csv").set_index("archive_id")
    event_index = events.set_index(KEYS).sort_index()
    counts = dict(
        archives=0, membership_rows=0, hourly_rows=0, event_sets=0, excluded_inventory_rows=0
    )
    for path in sorted((out / "archive_membership").glob("*.parquet")):
        cohort, scenario, analysis = path.stem.split("__")
        eligibility = sig[f"eligible_{cohort}"] & (
            ~sig.measurement_concern if analysis != "main" else True
        )
        pool = sig.loc[eligibility]
        hour = (
            pd.read_parquet(out / "hourly_scores" / path.name)
            .set_index(["query_event_id", "target_k", "method", "lead_hour"])
            .sort_index()
        )
        if hour.index.has_duplicates:
            raise ValueError("Duplicate query/method/hour scores")
        membership = pd.read_parquet(path)
        grouped_members = {eid: g for eid, g in membership.groupby("query_event_id")}
        d = donors.loc[
            donors.cohort.eq(cohort) & donors.scenario.eq(scenario) & donors.analysis.eq(analysis)
        ]
        groups = {
            (eid, arm): g.sort_values("rank")
            for (eid, arm), g in d.groupby(["query_event_id", "arm"])
        }
        arms = sorted(d.arm.unique())
        source_counts = old.loc[
            old.cohort.eq(cohort) & old.scenario.eq(scenario) & old.analysis.eq(analysis)
        ].set_index(["query_event_id", "arm"])
        for query in pool.itertuples(index=False):
            eid = query.event_id
            eligible = pool.loc[
                (pool.onset_utc + pd.Timedelta(hours=72) <= query.onset_utc)
                & (pool.onset_utc < query.onset_utc)
                & (pool.storm_id != query.storm_id)
                & (pool.event_id != eid)
            ]
            if scenario == "other_rivers":
                eligible = eligible.loc[eligible.physical_river_group != query.physical_river_group]
            row = coverage.loc[(cohort, scenario, analysis, eid)]
            assert row.inherited_scoring_eligible
            assert row.candidate_events == len(eligible)
            assert row.candidate_groups == eligible.storm_id.nunique()
            if eligible.empty:
                assert row.status == "no_completed_prior_group" and eid not in grouped_members
                continue
            assert row.status == "available"
            actual = grouped_members[eid].set_index("candidate_event_id").sort_index()
            expected = eligible.set_index("event_id").sort_index()
            assert actual.index.tolist() == expected.index.tolist()
            assert actual.candidate_storm_id.tolist() == expected.storm_id.tolist()
            w = (
                1
                / expected.storm_id.map(expected.storm_id.value_counts())
                / expected.storm_id.nunique()
            ).to_numpy()
            maximum = max(maximum, check(actual.weight, w))
            archive_id = actual.archive_id.unique().item()
            assert sets.loc[archive_id, "candidate_events"] == len(expected)
            y = response.loc[eid, 1:24].to_numpy()
            archive = cdf_scores(y, response.loc[expected.index, 1:24].to_numpy(), w)
            persistence = cdf_scores(y, np.full((1, 24), query.q_over_p99_onset), [1.0])
            for arm in arms:
                g = groups[eid, arm]
                assert source_counts.loc[(eid, arm), "candidate_count"] == len(expected)
                assert (
                    source_counts.loc[(eid, arm), "candidate_storm_count"]
                    == expected.storm_id.nunique()
                )
                assert g.analogue_storm_id.nunique() == len(g)
                assert set(g.analogue_event_id).issubset(expected.index)
                assert g["rank"].tolist() == list(
                    range(1, min(10, expected.storm_id.nunique()) + 1)
                )
            for k in [5, 10]:
                scores = {"archive": (archive, len(expected)), "persistence": (persistence, 1)}
                for arm in arms:
                    g = groups[eid, arm]
                    ids = g.loc[g["rank"].le(k), "analogue_event_id"]
                    scores[arm] = (
                        cdf_scores(y, response.loc[ids, 1:24].to_numpy(), np.ones(len(ids))),
                        len(ids),
                    )
                for method, (computed, size) in scores.items():
                    h = hour.loc[(eid, k, method)]
                    assert h.index.tolist() == list(range(1, 25))
                    for field, values in computed.items():
                        maximum = max(maximum, check(h[field], values))
                    e = event_index.loc[(cohort, scenario, analysis, k, eid, method)]
                    assert e.actual_member_count == size
                    assert e.selected_donor_count == min(k, expected.storm_id.nunique())
                    assert e.query_storm_id == query.storm_id
                    for field in FIELDS:
                        maximum = max(
                            maximum, check(e[f"{field}_mean_24h"], computed[field].mean())
                        )
                        for lead in [6, 12, 24]:
                            maximum = max(
                                maximum, check(e[f"{field}_h{lead}"], computed[field][lead - 1])
                            )
                    counts["event_sets"] += 1
                    counts["hourly_rows"] += len(h)
            counts["archives"] += 1
            counts["membership_rows"] += len(actual)
        for query in sig.loc[~eligibility].itertuples(index=False):
            c = coverage.loc[(cohort, scenario, analysis, query.event_id)]
            assert not c.inherited_scoring_eligible and pd.isna(c.candidate_events)
            assert c.status == (
                "measurement_quality_exclusion"
                if analysis != "main" and query.measurement_concern
                else "outside_inherited_scoring_cohort"
            )
            counts["excluded_inventory_rows"] += 1
        print("Audited", path.stem, flush=True)
    assert counts["event_sets"] == len(events)
    assert counts["hourly_rows"] == sum(
        len(pd.read_parquet(p, columns=["lead_hour"]))
        for p in (out / "hourly_scores").glob("*.parquet")
    )
    assert counts["archives"] == len(sets)
    return maximum, counts


def audit_summaries(out, events):
    maximum = 0.0
    metrics = [
        c
        for c in events
        if c.endswith("_mean_24h") or any(c.endswith(f"_h{h}") for h in [6, 12, 24])
    ]
    population = pd.concat(
        [events.assign(population=events.query_country), events.assign(population="ALL")]
    )
    base = [*CONFIG, "target_k", "method"]
    units = events.copy()
    for field in metrics:
        if field.startswith(("crps_", "median_absolute_error_", "width")):
            units[field] *= units.p99_m3s
        elif field.startswith("mean_squared_error_"):
            units[field] *= units.p99_m3s**2
    configurations = [
        ("summary", population, [*base, "population"]),
        ("summary_by_donor_count", population, [*base, "population", "donor_count_category"]),
        ("summary_by_river", events, [*base, "query_country", "query_river"]),
        ("summary_by_gauge_m3s", units, [*base, "query_country", "query_gauge"]),
    ]
    rows = 0
    for name, source, keys in configurations:
        actual = (
            pd.read_csv(out / f"{name}.csv", float_precision="round_trip")
            .set_index(keys)
            .sort_index()
        )
        grouped = source.groupby(keys, sort=True)
        expected = grouped[metrics].mean()
        pd.testing.assert_index_equal(actual.index, expected.index)
        maximum = max(maximum, check(actual[metrics], expected))
        np.testing.assert_array_equal(actual.queries, grouped.size())
        np.testing.assert_array_equal(actual.regional_groups, grouped.query_storm_id.nunique())
        np.testing.assert_array_equal(
            actual.min_selected_donors, grouped.selected_donor_count.min()
        )
        np.testing.assert_array_equal(
            actual.max_selected_donors, grouped.selected_donor_count.max()
        )
        rows += len(actual)
    profiles = []
    countries = events.drop_duplicates("query_event_id").set_index("query_event_id").query_country
    for cohort in ["q_only", "rain_matched", "context"]:
        hourly = pd.read_parquet(out / f"hourly_scores/{cohort}__all_rivers__main.parquet")
        hourly = hourly.loc[hourly.target_k.eq(5)].copy()
        hourly["population"] = hourly.query_event_id.map(countries)
        hourly = pd.concat([hourly, hourly.assign(population="ALL")])
        grouped = hourly.groupby(["cohort", "method", "population", "lead_hour"], sort=True)
        expected = grouped[["crps", "coverage80", "width80"]].mean()
        expected["queries"] = grouped.size()
        profiles.append(expected)
    expected = pd.concat(profiles).sort_index()
    actual = (
        pd.read_csv(out / "lead_profiles.csv", float_precision="round_trip")
        .set_index(["cohort", "method", "population", "lead_hour"])
        .sort_index()
    )
    pd.testing.assert_index_equal(actual.index, expected.index)
    maximum = max(maximum, check(actual[expected.columns], expected))
    rows += len(expected)
    return maximum, rows


def audit_intervals(out, events, manifest):
    """Independent multinomial-count replay of every joint bootstrap interval."""
    pairs = pd.read_parquet(out / "paired_differences.parquet")
    scores = events.set_index(KEYS).sort_index()
    maximum = 0.0
    for metric, part in pairs.groupby("metric"):
        a = pd.MultiIndex.from_frame(
            part[[*CONFIG, "target_k", "query_event_id", "reference"]].rename(
                columns={"reference": "method"}
            )
        )
        b = pd.MultiIndex.from_frame(
            part[[*CONFIG, "target_k", "query_event_id", "challenger"]].rename(
                columns={"challenger": "method"}
            )
        )
        maximum = max(
            maximum,
            check(
                part.difference,
                scores.reindex(b)[metric].to_numpy() - scores.reindex(a)[metric].to_numpy(),
            ),
        )
    intervals = pd.read_csv(out / "paired_intervals.csv", float_precision="round_trip")
    labels = (
        events.loc[events.method.eq("archive")]
        .set_index([*CONFIG, "target_k", "query_event_id"])
        .sort_index()
    )
    seed, draws = manifest["seed"], manifest["bootstrap_draws"]
    count = 0
    for config, part in pairs.groupby([*CONFIG, "target_k"], sort=True):
        for population in ["ALL", "NL", "DE"]:
            subset = part if population == "ALL" else part.loc[part.query_country.eq(population)]
            if subset.empty:
                continue
            matrix = subset.pivot(
                index="query_event_id",
                columns=["reference", "challenger", "metric"],
                values="difference",
            ).sort_index()
            assert matrix.notna().all().all()
            query = labels.loc[config].loc[matrix.index]
            for unit in ["query_storm_id", "storm_year"]:
                target = (
                    intervals.loc[
                        np.logical_and.reduce(
                            [
                                intervals[field].eq(value).to_numpy()
                                for field, value in zip([*CONFIG, "target_k"], config, strict=True)
                            ]
                        )
                        & intervals.population.eq(population)
                        & intervals.resampling_unit.eq(unit)
                    ]
                    .set_index(["reference", "challenger", "metric"])
                    .reindex(matrix.columns)
                )
                codes, clusters = pd.factorize(query[unit], sort=True)
                assert (
                    target.queries.eq(len(matrix)).all() and target.clusters.eq(len(clusters)).all()
                )
                maximum = max(maximum, check(target.difference, matrix.mean().to_numpy()))
                if len(clusters) < 2:
                    assert target.status.eq("too_few_clusters").all() and target.draws.eq(0).all()
                else:
                    rng = np.random.default_rng(seed)
                    counts = np.zeros((draws, len(clusters)))
                    picks = rng.integers(len(clusters), size=(draws, len(clusters)))
                    np.add.at(counts, (np.arange(draws)[:, None], picks), 1)
                    sums = np.zeros((len(clusters), matrix.shape[1]))
                    np.add.at(sums, codes, matrix.to_numpy())
                    values = counts @ sums / (counts @ np.bincount(codes))[:, None]
                    assert np.isfinite(values).all()
                    lower, upper = np.quantile(values, [0.025, 0.975], axis=0)
                    maximum = max(maximum, check(target.lower, lower), check(target.upper, upper))
                    assert target.status.eq("estimated").all()
                    assert target.draws.eq(draws).all() and target.finite_draws.eq(draws).all()
                count += len(target)
    assert count == len(intervals)
    return maximum, count, len(pairs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT)
    out = parser.parse_args().output_dir
    manifest = json.loads((out / "manifest.json").read_text())
    for label, base in [("input_sha256", ROOT), ("source_sha256", ROOT), ("outputs_sha256", out)]:
        for name, expected in manifest[label].items():
            assert digest(base / name) == expected, (label, name)
    events = pd.read_parquet(out / "event_scores.parquet")
    assert not events.duplicated(KEYS).any()
    response = pd.read_parquet(out / "response_p99.parquet")
    maximum, counts = audit_sets(out, response, events)
    discrepancy, summary_rows = audit_summaries(out, events)
    maximum = max(maximum, discrepancy)
    discrepancy, intervals, pair_rows = audit_intervals(out, events, manifest)
    maximum = max(maximum, discrepancy)
    result = dict(
        status="pass",
        input_output_source_hashes_match=True,
        **counts,
        summary_rows=summary_rows,
        interval_rows=intervals,
        paired_rows=pair_rows,
        bootstrap_intervals_independently_replayed=True,
        maximum_absolute_discrepancy=maximum,
        audit_source_sha256=digest(__file__),
        manifest_sha256=digest(out / "manifest.json"),
    )
    (out / "independent_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
