"""Full-census scarcity scoring, with vectorized common masks and frozen EO."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output
from src.scarcity import (
    SCORE_FIELDS,
    batch_scores,
    combine_ground,
    measured_donor_support,
    partial_history_distances,
    persistence_scores,
    scenario_keep,
    stable_members,
    standard_distances,
)

OUT = ROOT / json.loads((ROOT / "config/limburg_scarcity_v1.json").read_text())["output"]
STATE = {}


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = path.with_name(path.name + f".{os.getpid()}.tmp")
    stage.write_text(json.dumps(value, indent=2) + "\n")
    stage.replace(path)


def initialize():
    prep = OUT / "preparation"
    state = STATE
    state["config"] = json.loads((prep / "config.json").read_text())
    state["meta"] = pd.read_parquet(prep / "cases.parquet")
    state["storms"] = pd.read_parquet(prep / "storms.parquet")
    state["groups"] = {g["name"]: g for g in json.loads((prep / "groups.json").read_text())}
    state["bank"] = dict(np.load(prep / "bank.npz"))
    state["eo"] = np.load(prep / "eo_distance.npy", mmap_mode="r")
    state["epochs"] = np.load(prep / "source_epoch_hours.npy")
    state["source_rain"] = pd.read_parquet(ROOT / "results/storm_response/hourly_rainfall.parquet")
    state["representations"] = json.loads((prep / "manifest.json").read_text())["representations"]
    state["sources"] = {
        str(p.relative_to(ROOT)): sha256(p)
        for p in [
            Path(__file__),
            ROOT / "src/scarcity.py",
            prep / "manifest.json",
            ROOT / "config/limburg_scarcity_v1.json",
        ]
    }


def summarize_scores(values):
    valid = np.isfinite(values)
    counts = valid.sum(axis=0)
    mean = np.divide(
        np.nansum(values, axis=0), counts, out=np.full(values.shape[1], np.nan), where=counts > 0
    )
    centered = np.where(valid, values - mean, 0)
    variance = np.divide(
        (centered * centered).sum(axis=0), counts, out=np.full_like(mean, np.nan), where=counts > 0
    )
    return mean, np.sqrt(variance), counts


def fallback(scores, counts, persistent, generic, generic_count):
    scores, counts = scores.copy(), counts.copy()
    missing = ~np.isfinite(scores[:, 0])
    use_persistence = missing & np.isfinite(persistent[:, 0])
    scores[use_persistence] = persistent[use_persistence]
    counts[use_persistence] = 1
    use_generic = ~np.isfinite(scores[:, 0]) & np.isfinite(generic[0])
    scores[use_generic] = generic
    counts[use_generic] = generic_count
    return scores, counts


def actual_rain_ages(spec, u):
    """Age of last finite completed rainfall report, including natural gaps."""
    bank = STATE["bank"]
    positions = bank[f"positions_{u}"][:, -1]
    raw = STATE["source_rain"]
    period = spec.get("hours", 1) if spec["family"] == "rain" else 1
    phases = range(period) if spec["family"] == "rain" else [0]
    rates = raw.rolling(period, min_periods=period).mean().to_numpy()
    index = np.arange(len(raw))[:, None]
    ages = []
    for phase in phases:
        finite = np.isfinite(rates) & (STATE["epochs"][:, None] % period == phase)
        last = np.maximum.accumulate(np.where(finite, index, -1), axis=0)[positions]
        ages.append(np.where(last >= 0, positions[:, None] - last, np.nan))
    result = np.stack(ages)
    if spec["family"] != "rain":
        result = np.broadcast_to(result, (spec["replicas"], *result.shape[1:]))
    return result


def run_job(job):
    name, u = job
    s = STATE
    spec = s["groups"][name]
    target = OUT / "scores" / f"{name}__u{u}"
    if (target / "manifest.json").exists():
        saved = json.loads((target / "manifest.json").read_text())
        if saved["sources_sha256"] != s["sources"]:
            raise ValueError("Completed scarcity job changed; version a new run")
        for filename, digest in saved["outputs_sha256"].items():
            if sha256(target / filename) != digest:
                raise ValueError("Completed scarcity output changed")
        return target.name, "reused"
    bank, meta = s["bank"], s["meta"]
    n = len(s["storms"])
    r = spec["replicas"]
    years = spec.get("years", 0)
    key = f"{u}_{years}"
    prior = bank[f"prior_{key}"]
    q = bank[f"q_{u}"]
    donors = bank[f"donor_q_{u}"]
    outcomes = bank[f"outcome_{u}"]
    truth = bank[f"outcome_valid_{u}"]
    packed = (
        np.load(OUT / "preparation" / (spec.get("mask_name", name) + ".npy"), mmap_mode="r")
        if spec["family"] in ["missing", "combined_missing"]
        else None
    )
    m = len(s["representations"])
    # Primary paired effects retain every replication, target and storm; all
    # other metrics retain case moments and exact first-replication traces.
    paired = np.full((r, 8, n, m, 2, 3), np.nan, dtype="float32")
    conventional = np.full((r, 8, n, 2), np.nan, dtype="float32")
    local_present = np.zeros((r, 8, n), bool)
    target_selected = np.zeros((r, 8, n), bool)
    local_age = np.full((r, 8, n), np.nan, dtype="float32")
    clean_pairs = np.zeros((r, 8, n, m, 2), bool)
    eo_used = np.zeros((r, 8, n, m), bool)
    rows = []
    began = time.monotonic()
    areas = meta.area_km2.to_numpy().reshape(n, 8)[0]
    rain_ages = actual_rain_ages(spec, u)

    for qi in range(n):
        positions = bank[f"positions_{u}"][qi]
        epochs = s["epochs"][positions]
        for gi in range(8):
            if not truth[qi, gi]:
                continue
            case = qi * 8 + gi
            keep = scenario_keep(spec, positions, epochs, packed, gi, q.shape[-1])
            selected = keep[:, gi].any(axis=1)
            available = keep & np.isfinite(q[qi])[None]
            local = available[:, gi]
            local_present[:, gi, qi] = local.any(axis=1)
            target_selected[:, gi, qi] = selected
            index = np.arange(q.shape[-1])
            last_index = np.where(local, index, -1).max(axis=1)
            last = q[qi, gi, np.maximum(last_index, 0)]
            last = np.where(last_index >= 0, last, np.nan)
            age = np.where(last_index >= 0, q.shape[-1] - 1 - last_index, np.nan)
            local_age[:, gi, qi] = age
            persistent = persistence_scores(outcomes[qi, gi], last)
            generic = bank[f"generic_{key}"][qi, gi]
            generic_count = int(bank[f"generic_count_{key}"][qi, gi])
            allowed = prior[qi] & truth[:, gi]
            if spec["family"] == "rain":
                rain = np.stack([bank[f"rain_{u}_{spec['hours']}_{p}"][qi, gi] for p in range(r)])
                rain_age = rain_ages[:, qi, gi]
            else:
                rain = np.broadcast_to(bank[f"rain_{u}_1_0"][qi, gi], (r, 7)).copy()
                rain_age = rain_ages[:, qi, gi]
                if spec["family"] == "rain_absent":
                    rain[:, :5] = np.nan
                    rain_age = np.full(r, np.nan)
            rain_d = standard_distances(
                rain,
                bank[f"rain_{u}_1_0"][:, gi],
                bank[f"rain_mean_{key}"][qi, gi],
                bank[f"rain_var_{key}"][qi, gi],
            )
            # In rain-coarsening scenes, project donor rain to the same reporting
            # schedule/phase too; preprocessing still fits only earlier inputs.
            if spec["family"] == "rain":
                rain_d = np.concatenate(
                    [
                        standard_distances(
                            rain[p : p + 1],
                            bank[f"rain_{u}_{spec['hours']}_{p}"][:, gi],
                            bank[f"rain_mean_{key}"][qi, gi],
                            bank[f"rain_var_{key}"][qi, gi],
                        )
                        for p in range(r)
                    ]
                )
            if spec.get("measured_support"):
                fraction = s["config"]["donor_support_sensitivity"][
                    "minimum_measured_fraction_per_active_channel"
                ]
                allowed = allowed[None] & measured_donor_support(
                    q[qi], q, keep, rain, bank[f"rain_{u}_1_0"][:, gi], fraction
                )
            active = available.reshape(r, -1).astype(float)
            total = active.sum(axis=1)[:, None]
            raw_finite = np.isfinite(q).reshape(n, -1)
            held_finite = np.isfinite(donors).reshape(n, -1)

            def fraction_map(mask, _active=active, _total=total):
                return np.divide(_active @ mask.T, _total, out=np.zeros((r, n)), where=_total > 0)

            measured = fraction_map(raw_finite)
            held_fraction = fraction_map(held_finite & ~raw_finite)
            mean_fraction = fraction_map(~held_finite)
            donor_good = fraction_map(bank[f"input_quality_{u}"].reshape(n, -1))
            donor_clean = ((donor_good >= 1 - 1e-12) | (total == 0)) & bank[f"outcome_quality_{u}"][
                :, gi
            ][None]
            rich_last = np.where(np.isfinite(q[qi, gi]), np.arange(q.shape[-1]), -1).max()
            rich_age = q.shape[-1] - 1 - rich_last if rich_last >= 0 else np.nan
            base_state = dict(
                case=case,
                storm=qi,
                offset_h=u,
                scenario=name,
                gauge=meta.gauge.iloc[case],
                country=meta.country.iloc[case],
                storm_id=meta.storm_id.iloc[case],
                replicas=r,
                input_observed_mean=float(local.sum(axis=1).mean()),
                observation_age_mean_h=float(np.nanmean(age)) if np.isfinite(age).any() else np.nan,
                target_selected_fraction=float(selected.mean()),
                local_present_fraction=float(local_present[:, gi, qi].mean()),
                available_station_mean=float(available.any(axis=-1).sum(axis=1).mean()),
                rain_report_age_mean_h=float(np.nanmean(rain_age))
                if np.isfinite(rain_age).any()
                else np.nan,
                rain_feature_observed_fraction=float(np.isfinite(rain[:, :5]).mean()),
                retained_q_clean_fraction=float(
                    (available & bank[f"input_quality_{u}"][qi][None]).sum() / available.sum()
                )
                if available.any()
                else np.nan,
                outcome_clean=bool(bank[f"outcome_quality_{u}"][qi, gi]),
                boundary_known=bool(meta.boundary_known.iloc[case]),
                prior_storms=float(np.asarray(allowed).sum(axis=-1).mean()),
                target_retained=bool(selected[0]),
                trace_observing_channels=np.flatnonzero(available[0].any(axis=-1)).tolist(),
                measured_support_sensitivity=bool(spec.get("measured_support", False)),
                input_age_equal_rich_fraction=float(np.mean(age == rich_age)),
            )

            def append(
                method,
                k,
                scores,
                counts,
                ids=None,
                used=None,
                _persistent=persistent,
                _base_state=base_state,
                _factor=3.6 / areas[gi],
                _donor_maps=(
                    ("measured", measured),
                    ("held", held_fraction),
                    ("mean_filled", mean_fraction),
                    ("clean", donor_clean),
                ),
            ):
                mean, sd, valid = summarize_scores(scores)
                trace_ids = [] if ids is None else ids[0, ids[0] >= 0].tolist()
                trace_kind = "analogue" if trace_ids else "none"
                if method == "generic":
                    trace_kind = "generic"
                elif method == "persistence" or (not trace_ids and np.isfinite(_persistent[0, 0])):
                    trace_kind = "persistence"
                if not np.isfinite(scores[0, 0]):
                    trace_kind = "none"
                row = dict(
                    **_base_state,
                    method=method,
                    target_k=k,
                    valid_replicas=int(valid[0]),
                    full_member_fraction=float((counts >= k).mean()),
                    actual_members_mean=float(counts.mean()),
                    eo_used_fraction=float(np.mean(used)) if used is not None else 0.0,
                    trace_members=trace_ids,
                    trace_kind=trace_kind,
                    trace_crps=float(scores[0, 0]),
                )
                if ids is not None:
                    valid_ids = ids >= 0
                    count_ids = valid_ids.sum(axis=1)
                    for label, values in _donor_maps:
                        selected_values = np.take_along_axis(values, np.maximum(ids, 0), axis=1)
                        fractions = np.divide(
                            (selected_values * valid_ids).sum(axis=1),
                            count_ids,
                            out=np.full(r, np.nan),
                            where=count_ids > 0,
                        )
                        row["donor_" + label + "_fraction"] = (
                            float(np.nanmean(fractions)) if np.isfinite(fractions).any() else np.nan
                        )
                for j, field in enumerate(SCORE_FIELDS):
                    row[field] = float(mean[j])
                    row[field + "_sd"] = float(sd[j])
                    row[field + "_valid_replicas"] = int(valid[j])
                    if field not in ["peak_time_error_h", "coverage80"]:
                        row[field + "_specific"] = float(mean[j] * _factor)
                rows.append(row)

            qd, support = partial_history_distances(
                q[qi], donors, bank[f"q_mean_{key}"][qi], bank[f"q_pairvar_{key}"][qi], keep
            )
            distance = combine_ground(qd, support, rain_d, gi)
            broad_ids = stable_members(distance, allowed)
            held, held_support = partial_history_distances(
                q[qi],
                donors,
                bank[f"q_mean_{key}"][qi],
                bank[f"q_pairvar_{key}"][qi],
                keep,
                held=True,
            )
            held_ids = stable_members(combine_ground(held, held_support, rain_d, gi), allowed)
            broad_scores = []
            broad_counts = []
            for ki, k in enumerate([5, 10]):
                b, counts = batch_scores(outcomes[qi, gi], outcomes[:, gi], broad_ids[:, :k])
                b, counts = fallback(b, counts, persistent, generic, generic_count)
                broad_scores.append(b)
                broad_counts.append(counts)
                conventional[:, gi, qi, ki] = b[:, 0] * 3.6 / areas[gi]
                append("conventional", k, b, counts, broad_ids[:, :k])
                h, hc = batch_scores(outcomes[qi, gi], outcomes[:, gi], held_ids[:, :k])
                h, hc = fallback(h, hc, persistent, generic, generic_count)
                append("causal_hold", k, h, hc, held_ids[:, :k])
                append("persistence", k, persistent, np.where(np.isfinite(persistent[:, 0]), 1, 0))
                append(
                    "generic",
                    k,
                    np.broadcast_to(generic, (r, len(SCORE_FIELDS))),
                    np.full(r, generic_count),
                )
            matched_cache = {}
            for j, rep in enumerate(s["representations"]):
                valid = bank["eo_valid"][j, :, gi]
                eligible = allowed & valid
                query_supported = bool(valid[qi] and eligible.any())
                label = f"{rep['model']}__{rep['kind']}"
                if query_supported:
                    cache_key = np.packbits(eligible).tobytes()
                    if cache_key not in matched_cache:
                        matched_cache[cache_key] = stable_members(distance, eligible)
                    match_ids = matched_cache[cache_key]
                    eo = s["eo"][j, gi, qi] / bank[f"eo_pair_{key}"][j, gi, qi]
                    aug_ids = stable_members(0.5 * distance + 0.5 * eo[None], eligible)
                else:
                    match_ids = aug_ids = np.full_like(broad_ids, -1)
                for ki, k in enumerate([5, 10]):
                    b, bc = broad_scores[ki], broad_counts[ki]
                    match, mc = batch_scores(outcomes[qi, gi], outcomes[:, gi], match_ids[:, :k])
                    aug, ac = batch_scores(outcomes[qi, gi], outcomes[:, gi], aug_ids[:, :k])
                    used = np.isfinite(aug[:, 0])
                    eo_used[:, gi, qi, j] = used
                    for score, count in [(match, mc), (aug, ac)]:
                        unsupported = ~np.isfinite(score[:, 0])
                        score[unsupported] = b[unsupported]
                        count[unsupported] = bc[unsupported]
                    factor = 3.6 / areas[gi]
                    paired[:, gi, qi, j, ki] = (
                        np.stack(
                            [aug[:, 0] - b[:, 0], aug[:, 0] - match[:, 0], match[:, 0] - b[:, 0]],
                            axis=-1,
                        )
                        * factor
                    )
                    clean = []
                    for selected_ids in [broad_ids[:, :k], match_ids[:, :k], aug_ids[:, :k]]:
                        present = selected_ids >= 0
                        good = np.take_along_axis(donor_clean, np.maximum(selected_ids, 0), axis=1)
                        clean.append(present.any(axis=1) & (good | ~present).all(axis=1))
                    clean_pairs[:, gi, qi, j, ki] = clean[0] & clean[1] & clean[2] & used
                    for arm, score, count, ids in [
                        ("matched", match, mc, match_ids),
                        ("augmented", aug, ac, aug_ids),
                    ]:
                        trace = ids[:, :k].copy()
                        trace[~used] = broad_ids[~used, :k]
                        append(label + "__" + arm, k, score, count, trace, used)
        if qi % 12 == 0:
            atomic_json(
                OUT / "progress" / (target.name + ".json"),
                dict(
                    status="running",
                    storm_issues=qi + 1,
                    total_storm_issues=n,
                    percent_complete=100 * (qi + 1) / n,
                    elapsed_s=time.monotonic() - began,
                    rows=len(rows),
                ),
            )
    with fresh_output(target) as work:
        pd.DataFrame(rows).to_parquet(work / "scores.parquet", index=False)
        np.savez_compressed(
            work / "paired_replicates.npz",
            paired=paired,
            conventional=conventional,
            local_present=local_present,
            target_selected=target_selected,
            local_age=local_age,
            clean_pairs=clean_pairs,
            eo_used=eo_used,
        )
        report = dict(
            status="completed",
            group=spec,
            offset_h=u,
            rows=len(rows),
            elapsed_s=time.monotonic() - began,
            sources_sha256=s["sources"],
            outputs_sha256={p.name: sha256(p) for p in work.iterdir()},
        )
        (work / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    atomic_json(
        OUT / "progress" / (target.name + ".json"),
        dict(
            status="completed",
            percent_complete=100,
            elapsed_s=time.monotonic() - began,
            rows=len(rows),
        ),
    )
    return target.name, "completed"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers", type=int, choices=[1, 2], default=2)
    p.add_argument("--group", default="all")
    p.add_argument("--offset", default="all", choices=["all", "0", "6", "12", "24"])
    args = p.parse_args()
    config = json.loads((OUT / "preparation/config.json").read_text())
    groups = json.loads((OUT / "preparation/groups.json").read_text())
    selected = groups if args.group == "all" else [g for g in groups if g["name"] == args.group]
    if not selected:
        raise ValueError("Unknown group")
    offsets = config["issue_offsets_h"] if args.offset == "all" else [int(args.offset)]
    jobs = [(g["name"], u) for g in selected for u in offsets]
    status = OUT / (
        "execution.json" if args.group == args.offset == "all" else "benchmark_execution.json"
    )
    done = []

    def record(state, **extra):
        atomic_json(
            status,
            dict(
                status=state,
                pid=os.getpid(),
                updated_utc=datetime.now(timezone.utc).isoformat(),
                planned_jobs=len(jobs),
                completed_jobs=len(done),
                percent_complete=100 * len(done) / len(jobs),
                jobs=done,
                **extra,
            ),
        )

    record("running")
    with ProcessPoolExecutor(max_workers=args.workers, initializer=initialize) as executor:
        pending = {executor.submit(run_job, job): job for job in jobs}
        for future in as_completed(pending):
            try:
                result = future.result()
            except Exception as exc:
                for f in pending:
                    f.cancel()
                record("failed", failed_job=pending[future], error=str(exc))
                raise
            done.append(result)
            record("running")
            print(result, flush=True)
    record("completed")


if __name__ == "__main__":
    main()
