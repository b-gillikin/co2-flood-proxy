#!/usr/bin/env python3
"""Reconstruct all responses, donor estimates, peer fits and reported intervals."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "storm_analyse", ROOT / "scripts/93_analyse_storm_responses.py"
)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def check_close(a, b, name, tolerance=1e-8):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if not np.allclose(a, b, atol=tolerance, rtol=tolerance, equal_nan=True):
        raise AssertionError(f"Independent reconstruction failed: {name}")
    finite = np.isfinite(a) & np.isfinite(b)
    return float(np.max(np.abs(a[finite] - b[finite]))) if finite.any() else 0.0


def independent_storms(rain, separation):
    complete = rain.notna().all(axis=1).to_numpy()
    positions = np.where(complete & (rain.to_numpy() >= 0.2).any(axis=1))[0]
    missing = np.cumsum(~complete)
    breaks = np.r_[True, (np.diff(positions) > separation) | (np.diff(missing[positions]) > 0)]
    groups = np.cumsum(breaks)
    found = []
    for label in np.unique(groups):
        where = positions[groups == label]
        first, last = where[0], where[-1]
        values = rain.iloc[first : last + 1].to_numpy()
        if np.sum(values, axis=0).max() >= 10:
            found.append((rain.index[first], rain.index[last]))
    return found


def independent_interval(frame, value):
    frame = frame.dropna(subset=[value])
    per_storm = frame.groupby(["year", "storm_id"])[value].mean()
    annual = [(x.sum(), len(x)) for _, x in per_storm.groupby(level=0)]
    rng = np.random.default_rng(A.SEED)
    picks = rng.integers(0, len(annual), size=(A.DRAWS, len(annual)))
    annual = np.asarray(annual)
    sampled = annual[picks].sum(axis=1)
    values = sampled[:, 0] / sampled[:, 1]
    return [per_storm.mean(), *np.quantile(values, [0.025, 0.975])]


def audit(out):
    errors = {}
    for name in ["catalogue_manifest.json", "analysis_manifest.json"]:
        manifest = json.loads((out / name).read_text())
        for path, expected in manifest["input_sha256"].items():
            if A.B.sha256(ROOT / path) != expected:
                raise AssertionError("Changed source/code: " + path)
        for path, expected in manifest["output_sha256"].items():
            if A.B.sha256(out / path) != expected:
                raise AssertionError("Changed output: " + path)
    rows = A.add_features(pd.read_parquet(out / "storm_gauge_responses.parquet"))
    q = pd.read_parquet(out / "hourly_discharge.parquet")
    rain = pd.read_parquet(out / "hourly_rainfall.parquet")
    scale = pd.read_parquet(out / "hourly_normalizer.parquet")
    meta = rows.set_index("row_id")
    storms = pd.read_csv(out / "storms.csv", parse_dates=["start_utc", "end_utc"])
    core = rows.loc[rows.country.eq("NL"), "gauge"].unique()
    separation = int(storms.dry_separation_h.iloc[0])
    expected = independent_storms(rain[core], separation)
    if expected != list(zip(storms.start_utc, storms.end_utc, strict=True)):
        raise AssertionError("Storm catalogue differs from hourly rainfall reconstruction")
    if len(rows) != len(storms) * 8 or rows.row_id.duplicated().any():
        raise AssertionError("Storm-gauge census is not complete/unique")
    responses = []
    for row in rows.itertuples():
        cutoff = row.start_utc + pd.Timedelta(hours=5)
        dates = pd.date_range(cutoff + pd.Timedelta(hours=1), periods=72, freq="h")
        x = q[row.gauge].reindex(dates)
        baseline = q[row.gauge].reindex([row.start_utc - pd.Timedelta(hours=1)]).iloc[0]
        landmark = q[row.gauge].reindex([cutoff]).iloc[0]
        normalizer = scale[row.gauge].reindex([cutoff]).iloc[0]
        observed = [row.baseline_q, row.landmark_q, row.normalizer_p99, row.response_fraction]
        reconstructed = [baseline, landmark, normalizer, x.notna().mean()]
        check_close(observed, reconstructed, "landmark and scale")
        known = (
            x.notna().all()
            and np.isfinite([baseline, landmark, normalizer]).all()
            and normalizer > 0
        )
        responses.append((x.max() - landmark) / normalizer if known else np.nan)
    errors["response_max"] = check_close(rows[A.OUTCOME], responses, "all 72h outcomes")
    scores = pd.read_csv(out / "matched_event_results.csv")
    donors = pd.read_parquet(out / "matched_event_donors.parquet")
    if not ((donors.donor_followup_end_utc < donors.query_start_utc).all()):
        raise AssertionError("Incomplete prior storm donated")
    if not np.array_equal(donors.query_row_id.map(meta.gauge), donors.donor_row_id.map(meta.gauge)):
        raise AssertionError("Same-gauge matching changed gauge")
    donors["value"] = donors.donor_row_id.map(meta[A.OUTCOME])
    keys = ["query_row_id", "cohort", "quality", "arm"]
    estimates = donors.groupby(keys).value.mean()
    scored = scores.set_index(keys).loc[estimates.index]
    errors["donor_estimates"] = check_close(scored.estimate, estimates, "all donor means")
    errors["matching_errors"] = check_close(
        scored.absolute_error, abs(estimates - scored.observed), "matching absolute errors"
    )
    if donors.duplicated([*keys, "donor_row_id"]).any() or donors.groupby(keys).size().max() > 5:
        raise AssertionError("Duplicated or excessive donors")
    # The separate estimator solves augmented least squares, not the runner's normal equations.
    peers = pd.read_parquet(out / "peer_predictions.parquet")
    folds = pd.read_csv(out / "peer_folds.csv")
    eligible = rows[rows.numeric_usable].dropna(subset=[*A.LOCAL, A.OUTCOME])
    extra_features = [
        "log_rain_total",
        "log_response_rain",
        "wet_area",
        "baseline_ratio",
        "rise_6h",
    ]
    maximum_fit_error = 0.0
    for (target, peer, quality), group in peers.groupby(["target", "peer", "quality"]):
        target_rows = eligible[eligible.gauge.eq(target)]
        peer_rows = rows[rows.gauge.eq(peer) & rows.peer_state_usable]
        extra = peer_rows[["storm_id", "input_measurement_concern", *extra_features]].rename(
            columns={
                **{c: "peer_" + c for c in extra_features},
                "input_measurement_concern": "peer_measurement_concern",
            }
        )
        joined = target_rows.merge(extra, on="storm_id", validate="one_to_one").dropna(
            subset=["peer_" + x for x in extra_features]
        )
        if quality:
            joined = joined[~(joined.measurement_concern | joined.peer_measurement_concern)]
        for year, by_year in group.groupby("year"):
            boundary = pd.Timestamp(f"{year}-01-01", tz="UTC")
            train = joined[
                (joined.year < year)
                & (joined.followup_end_utc < boundary)
                & (joined.end_utc < boundary)
            ]
            for arm, tested in by_year.groupby("arm"):
                features = A.LOCAL + (
                    ["peer_" + x for x in extra_features[:3]]
                    if arm == "peer_rain"
                    else ["peer_" + x for x in extra_features]
                    if arm == "peer_state"
                    else []
                )
                test = joined.set_index("row_id").loc[tested.row_id]
                mean, std = train[features].mean(), train[features].std(ddof=0).replace(0, 1)
                x = np.column_stack(
                    [np.ones(len(train)), ((train[features] - mean) / std).to_numpy()]
                )
                xt = np.column_stack(
                    [np.ones(len(test)), ((test[features] - mean) / std).to_numpy()]
                )
                penalty = np.eye(x.shape[1])[1:]
                beta = np.linalg.lstsq(
                    np.vstack([x, penalty]),
                    np.r_[train[A.OUTCOME].to_numpy(), np.zeros(len(features))],
                    rcond=None,
                )[0]
                prediction = xt @ beta
                maximum_fit_error = max(
                    maximum_fit_error,
                    check_close(tested.estimate, prediction, "all forward-year ridge predictions"),
                )
                check_close(
                    tested.absolute_error, abs(prediction - tested[A.OUTCOME]), "peer errors"
                )
    errors["peer_predictions"] = maximum_fit_error
    intervals = pd.read_csv(out / "paired_intervals.csv")
    peer_contrasts = pd.read_csv(out / "peer_event_contrasts.csv")
    maximum_interval_error = 0.0
    for record in intervals.itertuples():
        if record.kind == "event_matching":
            f = scores[(scores.cohort == record.cohort) & (scores.quality == record.quality)]
            base = f[f.arm.eq(record.reference)].set_index("query_row_id")
            other = f[f.arm.eq(record.challenger)].set_index("query_row_id").loc[base.index]
            contrast = base[["storm_id", "year"]].copy()
            contrast["difference"] = other.absolute_error - base.absolute_error
        else:
            contrast = peer_contrasts[
                (peer_contrasts.target == record.target)
                & (peer_contrasts.peer == record.peer)
                & (peer_contrasts.quality == record.quality)
            ]
            if record.regime.startswith("footprint:"):
                contrast = contrast[contrast.footprint.eq(record.regime.split(":")[1])]
            elif record.regime.startswith("warm:"):
                contrast = contrast[contrast.warm.eq(record.regime.endswith("True"))]
        expected = independent_interval(contrast, "difference")
        maximum_interval_error = max(
            maximum_interval_error,
            check_close(
                [record.estimate, record.lower, record.upper], expected, "paired year intervals"
            ),
        )
    errors["paired_intervals"] = maximum_interval_error
    pulses = pd.read_csv(out / "repeat_pulses.csv", parse_dates=["pulse_start_utc"])
    pulse_differences = []
    for pulse in pulses.itertuples():
        row = meta.loc[pulse.row_id]
        before = pulse.pulse_start_utc - pd.Timedelta(hours=1)
        dates = pd.date_range(pulse.pulse_start_utc, periods=24, freq="h")
        values = q[pulse.gauge].reindex(dates)
        if pd.notna(pulse.rise_next24h):
            pulse_differences.append(
                abs(
                    pulse.rise_next24h
                    - (values.max() - q.loc[before, pulse.gauge]) / row.normalizer_p99
                )
            )
        if pulse.recovery_known:
            if (
                row.rise_6h <= 0.02
                or q[pulse.gauge].loc[row.start_utc - pd.Timedelta(hours=1) : before].isna().any()
            ):
                raise AssertionError("Unobserved initial/recovery state labeled known")
            half = (q.loc[before, pulse.gauge] - row.baseline_q) > (
                row.landmark_q - row.baseline_q
            ) / 2
            if bool(half) != bool(pulse.before_half_recovery):
                raise AssertionError("Incorrect half-recovery label")
    errors["pulse_response"] = max(pulse_differences, default=0)
    # Direct weighted least-squares reconstruction of every reported association.
    coefficients = pd.read_csv(out / "conditional_coefficients.csv")
    enriched = A.add_features(pd.read_parquet(out / "storm_response_analysis.parquet"))
    max_beta_error = 0.0
    for (analysis, outcome), part in coefficients.groupby(["analysis", "outcome"]):
        quality = analysis.endswith("True")
        f = pulses if analysis.startswith("repeat_pulse") else enriched
        f = f[f.numeric_usable & (~f.measurement_concern if quality else True)].copy()
        if analysis.startswith("repeat_pulse"):
            f = f[f.recovery_known]
            f["before_half_recovery"] = f.before_half_recovery.astype(float)
        elif analysis.startswith("repeat_storm"):
            f = f[f.repeat_recovery_known]
        features = part.feature.tolist()
        f = f.dropna(subset=[*features, outcome, "year", "gauge"])
        mean, std = f[features].mean(), f[features].std(ddof=0).replace(0, 1)
        fixed = pd.get_dummies(f.gauge, drop_first=True, dtype=float)
        x = np.column_stack(
            [np.ones(len(f)), ((f[features] - mean) / std).to_numpy(), fixed.to_numpy()]
        )
        weight = np.sqrt(1 / f.groupby("storm_id").storm_id.transform("size").to_numpy())
        beta = np.linalg.lstsq(x * weight[:, None], f[outcome] * weight, rcond=None)[0]
        max_beta_error = max(
            max_beta_error,
            check_close(
                part.estimate_per_unit,
                beta[1 : len(features) + 1] / std,
                "conditional association coefficients",
                tolerance=1e-6,
            ),
        )
    errors["conditional_coefficients"] = max_beta_error
    result = {
        "status": "passed",
        "storm_gauge_rows_reconstructed": len(rows),
        "matched_scores_reconstructed": len(scores),
        "donor_slots": len(donors),
        "peer_scores_reconstructed": len(peers),
        "folds": len(folds),
        "paired_intervals_reconstructed": len(intervals),
        "repeat_pulses_checked": len(pulses),
        "maximum_discrepancies": errors,
    }
    (out / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=A.OUT)
    args = parser.parse_args()
    print(json.dumps(audit(args.output_dir.resolve()), indent=2))


if __name__ == "__main__":
    main()
