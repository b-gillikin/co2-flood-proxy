#!/usr/bin/env python3
"""Independent full-record episode, representation, pair/set and summary audit."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "definition_audit", ROOT / "scripts/88_event_definition_sensitivity.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def direct_pairs(q, a):
    qp, ap = q.max(axis=1), a.max(axis=1)
    return {
        "level_rmse_p99": np.sqrt(((q - a) ** 2).mean(axis=1)),
        "peak_scaled_shape_rmse": np.sqrt(((q / qp[:, None] - a / ap[:, None]) ** 2).mean(axis=1)),
        "peak_time_difference_h": abs(q.argmax(axis=1) - a.argmax(axis=1)),
        "high_water_duration_difference_h": abs((q >= 1).sum(axis=1) - (a >= 1).sum(axis=1)),
        "excess_area_difference_p99_h": abs(
            np.maximum(q - 1, 0).sum(axis=1) - np.maximum(a - 1, 0).sum(axis=1)
        ),
        "terminal_peak_ratio_difference": abs(
            q[:, -24:].mean(axis=1) / qp - a[:, -24:].mean(axis=1) / ap
        ),
    }


def check(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=0, equal_nan=True)
    difference = np.abs(np.asarray(actual, float) - np.asarray(expected, float))
    return float(np.nanmax(difference)) if np.isfinite(difference).any() else 0.0


def catalogue_check(source, census, quantile, gap):
    q, labels, literal = source["q"], source["eras"], source["literal"]
    table = source["table"].drop_duplicates("era_id").set_index("era_id")
    values = {
        era: np.quantile(q[labels.eq(era)].dropna().to_numpy(), quantile)
        for era in labels.dropna().unique()
        if q[labels.eq(era)].notna().any()
    }
    threshold = labels.map(values).astype(float)
    lower = labels.map(table.domain_min_m3s).astype(float).fillna(-np.inf)
    upper = labels.map(table.domain_max_m3s).astype(float).fillna(np.inf)
    admissible = (
        q.notna()
        & labels.notna()
        & (
            (q.ge(lower) & q.le(upper))
            | (q.lt(lower) & lower.le(threshold))
            | (q.gt(upper) & upper.ge(threshold))
        )
    )
    above = q.gt(threshold) & q.notna() & threshold.notna()
    previous_above = above.shift(1, fill_value=False)
    adjacent = literal.eq(literal.shift(1)).fillna(False) & q.shift(1).notna()
    exact = above & ~previous_above & adjacent & admissible & admissible.shift(1, fill_value=False)
    continuing = above & previous_above & adjacent
    entry = above & ~continuing & ~exact
    positions = np.flatnonzero((exact | entry).to_numpy())
    groups = np.cumsum(np.r_[True, np.diff(positions) > gap]) if len(positions) else []
    expected = []
    for group in np.unique(groups):
        members = positions[np.asarray(groups) == group]
        first, last = q.index[members[0]], q.index[members[-1]]
        expected.append(
            dict(
                event_id=f"{source['gauge']}|{first.isoformat()}",
                onset_utc=first,
                last_crossing_utc=last,
                n_crossings=len(members),
                onset_censored=bool(entry.loc[first]),
            )
        )
    actual = census[census.gauge.eq(source["gauge"])].set_index("event_id").sort_index()
    if not expected:
        assert actual.empty
        return 0
    expected = pd.DataFrame(expected).set_index("event_id").sort_index()
    pd.testing.assert_index_equal(actual.index, expected.index)
    for field in ["onset_utc", "last_crossing_utc"]:
        assert pd.to_datetime(actual[field], utc=True).equals(
            pd.to_datetime(expected[field], utc=True)
        )
    assert actual.n_crossings.equals(expected.n_crossings)
    assert actual.onset_censored.equals(expected.onset_censored)
    return len(expected)


def curve_check(observations, index, raw, state, response):
    maximum = 0.0
    for source in observations:
        events = index[index.gauge.eq(source["gauge"])]
        q = source["q"]
        norms = {
            era: np.quantile(q[source["eras"].eq(era)].dropna().to_numpy(), 0.99)
            for era in source["eras"].dropna().unique()
            if q[source["eras"].eq(era)].notna().any()
        }
        for event in events.itertuples():
            maximum = max(
                maximum,
                check(event.p99_m3s, norms[source["eras"].loc[pd.Timestamp(event.onset_utc)]]),
            )
            times = pd.date_range(
                pd.Timestamp(event.onset_utc) - pd.Timedelta(hours=511), periods=584, freq="h"
            )
            values = q.reindex(times).to_numpy()
            maximum = max(
                maximum, check(response.loc[event.event_id], values[512:] / event.p99_m3s)
            )
            if event.event_id in raw.index:
                history = values[:512]
                sd = history.std()
                standardized = (history - history.mean()) / (sd if sd else 1)
                maximum = max(maximum, check(raw.loc[event.event_id], standardized))
                maximum = max(
                    maximum,
                    check(
                        state.loc[event.event_id],
                        [
                            history[-1] / event.p99_m3s,
                            history.mean() / event.p99_m3s,
                            sd / event.p99_m3s,
                        ],
                    ),
                )
    return maximum


def selected_set_check(donors, rows, response):
    keys = ["cohort", "scenario", "analysis", "policy", "arm", "query_event_id"]
    maximum = 0.0
    for k in [5, 10]:
        selected = donors[donors["rank"].le(k)]
        ids = pd.MultiIndex.from_frame(selected[keys])
        codes, unique = pd.factorize(ids, sort=False)
        unique = unique.set_names(keys)
        sums = np.zeros((len(unique), 72))
        for start in range(0, len(selected), 10000):
            g = selected.iloc[start : start + 10000]
            np.add.at(
                sums, codes[start : start + len(g)], response.loc[g.analogue_event_id].to_numpy()
            )
        counts = np.bincount(codes)
        mean = sums / counts[:, None]
        meta = unique.to_frame(index=False)
        query = response.loc[meta.query_event_id].to_numpy()
        actual = rows[rows.target_k.eq(k)].set_index(keys).loc[unique]
        maximum = max(maximum, check(actual.actual_donor_count, counts))
        maximum = max(
            maximum,
            check(actual.ensemble_curve_level_rmse, np.sqrt(((mean - query) ** 2).mean(axis=1))),
        )
        peak = selected.analogue_event_id.map(response.max(axis=1)).to_numpy()
        peak_mean = np.bincount(codes, weights=peak) / counts
        maximum = max(
            maximum,
            check(actual.mean_donor_peak_absolute_error, abs(peak_mean - query.max(axis=1))),
        )
        durations = selected.analogue_event_id.map(response.ge(1).sum(axis=1)).to_numpy()
        expected_duration = np.bincount(codes, weights=durations) / counts
        maximum = max(maximum, check(actual.estimated_high_water_hours, expected_duration))
        maximum = max(
            maximum,
            check(
                actual.duration_estimate_absolute_error_h,
                abs(expected_duration - (query >= 1).sum(axis=1)),
            ),
        )
        maximum = max(
            maximum,
            check(
                actual.final_24h_level_absolute_error,
                abs(mean[:, -24:].mean(axis=1) - query[:, -24:].mean(axis=1)),
            ),
        )
        pair_means = selected.groupby(keys)[M.C.CENSUS.METRICS].mean().loc[unique]
        for metric in M.C.CENSUS.METRICS:
            maximum = max(maximum, check(actual["mean_" + metric], pair_means[metric]))
    return maximum


def archive_reference_check(rows, sample, raw, state, ordered, years, response):
    cohorts = M.cohort_inputs(sample, raw, state, ordered, years)
    maximum = 0.0
    for config, group in rows.groupby(["cohort", "scenario", "analysis"]):
        cohort, scenario, analysis = config
        frame = cohorts[cohort][0]
        eligible = frame[
            frame.complete_scoring_sample
            & (~frame.measurement_concern if analysis == "quality_sensitivity" else True)
        ]
        for row in group.drop_duplicates("query_event_id").itertuples():
            query = eligible[eligible.event_id.eq(row.query_event_id)].iloc[0]
            prior = eligible[
                (eligible.onset_utc + pd.Timedelta(hours=72)).le(query.onset_utc)
                & eligible.storm_id.ne(query.storm_id)
            ]
            if scenario == "other_rivers":
                prior = prior[prior.physical_river_group.ne(query.physical_river_group)]
            assert len(prior) == row.candidate_count
            assert prior.storm_id.nunique() == row.candidate_storm_count
            weights = (
                1 / prior.storm_id.map(prior.storm_id.value_counts()) / prior.storm_id.nunique()
            ).to_numpy()
            a = response.loc[prior.event_id].to_numpy()
            q = response.loc[row.query_event_id].to_numpy()
            curve = weights @ a
            peak = a.max(axis=1)
            expected = dict(
                archive_curve_level_rmse=np.sqrt(np.mean((curve - q) ** 2)),
                archive_mean_individual_shape_rmse=weights
                @ np.sqrt(np.mean((a / peak[:, None] - q / q.max()) ** 2, axis=1)),
                archive_duration_absolute_error_h=abs(
                    weights @ (a >= 1).sum(axis=1) - (q >= 1).sum()
                ),
                archive_final_24h_level_absolute_error=abs(curve[-24:].mean() - q[-24:].mean()),
                archive_mean_peak_absolute_error=abs(weights @ peak - q.max()),
            )
            for field, value in expected.items():
                maximum = max(maximum, check(getattr(row, field), value))
    return maximum


def map_catalogues(baseline, alternative):
    """Map each original onset to its containing lower/longer episode chain.

    Lower-threshold exceedance at a p99 onset guarantees a preceding p95 entry.
    The latest alternative episode start identifies that entry's pooled chain;
    it does not imply independent meteorological storms or forecast lead time.
    """
    records = []
    for gauge, old in baseline.groupby("gauge"):
        new = alternative[alternative.gauge.eq(gauge)].copy()
        new["onset_utc"] = pd.to_datetime(new.onset_utc, utc=True)
        new = new.sort_values("onset_utc")
        starts = pd.DatetimeIndex(new.onset_utc).as_unit("ns").asi8
        for row in old.itertuples():
            t = pd.Timestamp(row.onset_utc)
            position = int(np.searchsorted(starts, t.value, side="right") - 1)
            assert position >= 0
            target = new.iloc[position]
            assert target.onset_utc <= t
            shift = (t - target.onset_utc) / pd.Timedelta(hours=1)
            records.append(
                dict(
                    baseline_event_id=row.event_id,
                    alternative_event_id=target.event_id,
                    gauge=gauge,
                    country=row.country,
                    baseline_onset_utc=t,
                    alternative_onset_utc=target.onset_utc,
                    assessment_start_shift_h=shift,
                    response_window_overlap_h=max(0.0, 72 - shift),
                    alternative_onset_censored=bool(target.onset_censored),
                )
            )
    return pd.DataFrame(records)


def main():
    out = M.OUT
    manifest = json.loads((out / "manifest.json").read_text())
    for collection, base in [
        ("input_sha256", ROOT),
        ("source_sha256", ROOT),
        ("outputs_sha256", out),
    ]:
        for name, digest in manifest[collection].items():
            assert M.S.TTM.sha256(base / name) == digest, name
    observations, _ = M.held_observations()
    receipts = []
    for name, (quantile, gap) in M.CONFIGS.items():
        folder = out / name
        census = pd.read_csv(folder / "candidate_episodes.csv")
        checked_events = sum(
            catalogue_check(source, census, quantile, gap) for source in observations
        )
        index = pd.read_csv(folder / "event_inventory.csv")
        raw = pd.read_parquet(folder / "raw_histories.parquet")
        state = pd.read_parquet(folder / "discharge_state.parquet")
        response = pd.read_parquet(folder / "response_p99.parquet")
        maximum = curve_check(observations, index, raw, state, response)
        rows = pd.read_csv(folder / "event_assessments.csv", float_precision="round_trip")
        donors = pd.read_csv(
            folder / "selected_donors.csv", float_precision="round_trip", low_memory=False
        )
        meta = index.set_index("event_id")
        assert (
            pd.to_datetime(donors.analogue_onset_utc, utc=True) + pd.Timedelta(hours=72)
            <= pd.to_datetime(donors.query_onset_utc, utc=True)
        ).all()
        assert (
            donors.analogue_event_id.map(meta.storm_id)
            .ne(donors.query_event_id.map(meta.storm_id))
            .all()
        )
        assert not donors.duplicated(
            ["cohort", "scenario", "analysis", "arm", "query_event_id", "analogue_storm_id"]
        ).any()
        for scenario, g in donors.groupby("scenario"):
            if scenario == "other_rivers":
                assert (
                    g.analogue_event_id.map(meta.physical_river_group)
                    .ne(g.query_event_id.map(meta.physical_river_group))
                    .all()
                )
        for start in range(0, len(donors), 10000):
            group = donors.iloc[start : start + 10000]
            q = response.loc[group.query_event_id].to_numpy()
            a = response.loc[group.analogue_event_id].to_numpy()
            for metric, expected in direct_pairs(q, a).items():
                maximum = max(maximum, check(group[metric], expected))
        maximum = max(maximum, selected_set_check(donors, rows, response))
        sample = pd.read_csv(folder / "signatures.csv", parse_dates=["onset_utc"])
        years = pd.read_parquet(
            ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet"
        )
        maximum = max(
            maximum,
            archive_reference_check(
                rows,
                sample,
                raw,
                state,
                pd.read_parquet(folder / "ordered_TTM.parquet"),
                years,
                response,
            ),
        )

        expected = rows.groupby(M.KEYS)[M.METRICS].mean().sort_index()
        reported = (
            pd.read_csv(folder / "summary_by_country.csv").set_index(M.KEYS)[M.METRICS].sort_index()
        )
        maximum = max(maximum, check(expected, reported))
        intervals = pd.read_csv(folder / "paired_intervals.csv")
        assert intervals.loc[intervals.status.eq("estimated"), "finite_draws"].eq(9999).all()
        composition = []
        for country, g in sample[sample.complete_scoring_sample].groupby("country"):
            composition.append(
                dict(
                    country=country,
                    scorable_responses=len(g),
                    response_peak_reaches_p99=int(g.outcome_peak_over_p99_72h.ge(1).sum()),
                    response_peak_at_first_hour=int(g.outcome_time_to_peak_h.eq(1).sum()),
                    median_response_peak_over_p99=float(g.outcome_peak_over_p99_72h.median()),
                )
            )
        receipts.append(
            dict(
                response_composition=composition,
                run=name,
                independently_checked_episodes=checked_events,
                input_histories=len(raw),
                checked_pair_slots=len(donors),
                checked_event_scores=len(rows),
                maximum_numeric_difference=maximum,
            )
        )
        print(json.dumps(receipts[-1]), flush=True)
    # Baseline outputs reproduce the held pooled analysis, not merely its means.
    current = pd.read_csv(out / "p99_72/event_assessments.csv", float_precision="round_trip")
    held = pd.read_csv(M.X.OUT / "event_assessments.csv", float_precision="round_trip")
    held = held[held.policy.eq("pooled")]
    keys = [*M.KEYS, "query_event_id"]
    a, b = current.set_index(keys).sort_index(), held.set_index(keys).sort_index()
    pd.testing.assert_index_equal(a.index, b.index)
    check(a[M.METRICS], b[M.METRICS])
    audit_out = out.parent / "basin_ai_event_definition_audit"
    audit_out.mkdir(exist_ok=True)
    baseline_census = pd.read_csv(out / "p99_72/candidate_episodes.csv")
    mappings = []
    for name in ["p95_72", "p99_120"]:
        mapped = map_catalogues(baseline_census, pd.read_csv(out / name / "candidate_episodes.csv"))
        mapped["alternative_run"] = name
        mappings.append(mapped)
    mapping_path = audit_out / "baseline_episode_mapping.csv"
    pd.concat(mappings, ignore_index=True).to_csv(mapping_path, index=False)
    receipt = dict(
        derived_sha256={str(mapping_path.relative_to(ROOT)): M.S.TTM.sha256(mapping_path)},
        runs=receipts,
        hashes_match=True,
        baseline_reproduces_held_pooled_results=True,
        source_sha256=M.S.TTM.sha256(Path(__file__)),
        manifest_sha256=M.S.TTM.sha256(out / "manifest.json"),
    )
    (out / "independent_audit.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
