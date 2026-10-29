"""Model-aware EO diagnostics on the complete initial-landmark event census."""

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
from src.eo_signal_diagnostic import (
    chronology,
    partial_rank_correlation,
    readout_fold,
    validation_splits,
)
from src.scarcity import (
    batch_scores,
    combine_ground,
    partial_history_distances,
    stable_members,
    standard_distances,
)

CONFIG = ROOT / "config/limburg_eo_signal_diagnostic_v1.json"
CFG = json.loads(CONFIG.read_text())
OUT = ROOT / CFG["output"]
STATE = {}
NATIVE = {"anysat", "galileo", "olmoearth", "presto", "prithvi"}


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def initialize():
    source = ROOT / CFG["source"]
    prep = source / "preparation"
    manifest = json.loads((prep / "manifest.json").read_text())
    for name in ["bank.npz", "eo_distance.npy", "cases.parquet", "storms.parquet"]:
        if sha256(prep / name) != manifest["outputs_sha256"][name]:
            raise ValueError("Held diagnostic input changed: " + name)
    STATE.update(
        source=source,
        meta=pd.read_parquet(prep / "cases.parquet"),
        storms=pd.read_parquet(prep / "storms.parquet"),
        bank=dict(np.load(prep / "bank.npz")),
        eo_distance=np.load(prep / "eo_distance.npy", mmap_mode="r"),
        representations=json.loads((prep / "manifest.json").read_text())["representations"],
    )


def raw_features(model, kind):
    path = (
        ROOT / f"results/eo_catchment_representations/coherent_v1/selected/census/{model}.parquet"
    )
    meta = STATE["meta"]
    data = pd.read_parquet(path)
    data = data[data.kind.eq(kind)].set_index(["context_id", "catchment_gauge"])
    if not data.index.is_unique:
        raise ValueError("Duplicate model/context/gauge")
    keys = pd.MultiIndex.from_arrays([meta[kind + "_context_id"], meta.catchment_gauge])
    data = data.reindex(keys)
    columns = [c for c in data if c.startswith("e") and c[1:].isdigit()]
    x = data[columns].to_numpy(dtype=float, copy=True)
    valid = np.isfinite(x).all(axis=1) & (np.linalg.norm(x, axis=1) > 0)
    x[~valid] = np.nan
    return (
        x.reshape(-1, 8, len(columns)),
        data.observed_mean_fraction.to_numpy().reshape(-1, 8),
        valid.reshape(-1, 8),
        path,
    )


def representation_diagnostics(model, kind, eo, coverage, valid):
    s = STATE
    n = len(s["storms"])
    flat = eo.reshape(n * 8, -1)
    ok = valid.ravel()
    x = flat[ok]
    norm = np.linalg.norm(x, axis=1)
    unit = x / norm[:, None]
    centered = unit - unit.mean(axis=0)
    singular = np.linalg.svd(centered, compute_uv=False)
    eigen = singular**2
    probability = eigen[eigen > 1e-16] / eigen.sum() if eigen.sum() > 0 else np.array([1.0])
    meta = s["meta"].loc[ok].reset_index(drop=True)
    groups = pd.get_dummies(meta.gauge, dtype=float).to_numpy()
    day = meta.cutoff_utc.dt.dayofyear.to_numpy()
    season = np.column_stack(
        [
            np.sin(2 * np.pi * day / 365.25),
            np.cos(2 * np.pi * day / 365.25),
            np.sin(4 * np.pi * day / 365.25),
            np.cos(4 * np.pi * day / 365.25),
        ]
    )
    blocks = [
        groups,
        season,
        meta.cutoff_utc.dt.year.to_numpy()[:, None],
        coverage.ravel()[ok, None],
    ]
    variance = float((centered**2).sum())
    explained = {}
    design = np.ones((len(x), 1))
    for name, block in zip(
        ["gauge", "gauge_season", "gauge_season_year", "gauge_season_year_coverage"],
        blocks,
        strict=True,
    ):
        design = np.column_stack([design, np.nan_to_num(block)])
        error = unit - design @ np.linalg.lstsq(design, unit, rcond=None)[0]
        explained[name + "_explained_fraction"] = (
            1 - float((error**2).sum()) / variance if variance > 0 else np.nan
        )
    overview = dict(
        model=model,
        readout=kind,
        dimension=eo.shape[-1],
        supported_cases=int(ok.sum()),
        unique_contexts=int(meta[kind + "_context_id"].nunique()),
        temporal_path="native_sequence" if model in NATIVE else "independent_frame_mean",
        norm_min=float(norm.min()),
        norm_median=float(np.median(norm)),
        norm_max=float(norm.max()),
        effective_rank=float(np.exp(-(probability * np.log(probability)).sum())),
        **explained,
    )
    associations = []
    for gi in range(8):
        ids = np.flatnonzero(valid[:, gi])
        a, b = np.triu_indices(len(ids), k=1)
        i, j = ids[a], ids[b]
        vectors = eo[ids, gi]
        vectors = vectors / np.linalg.norm(vectors, axis=1)[:, None]
        distance = np.maximum(2 - 2 * (vectors @ vectors.T)[a, b], 0)
        dates = s["storms"].cutoff_utc
        doy, year = dates.dt.dayofyear.to_numpy(), dates.dt.year.to_numpy()
        delta = np.abs(doy[i] - doy[j])
        age = s["meta"][kind + "_bin_age_days"].to_numpy().reshape(n, 8)[:, gi]
        controls = np.column_stack(
            [
                np.minimum(delta, 365.25 - delta),
                np.abs(year[i] - year[j]),
                np.abs(coverage[i, gi] - coverage[j, gi]),
                np.abs(age[i] - age[j]),
            ]
        )
        for variable, values in [
            ("antecedent_rain_72h", s["bank"]["rain_0_1_0"][:, gi, 2]),
            ("landmark_local_q", s["bank"]["q_0"][:, gi, -1]),
        ]:
            difference = np.abs(values[i] - values[j])
            correlation, count = partial_rank_correlation(distance, difference, controls)
            associations.append(
                dict(
                    model=model,
                    readout=kind,
                    gauge=s["meta"].gauge.iloc[gi],
                    variable=variable,
                    partial_rank_correlation=correlation,
                    pairs=count,
                    interpretation="descriptive_dependent_pairs_no_pvalues",
                )
            )
    return overview, associations


def conventional_inputs(gi, scenario, coverage, kind):
    bank, meta, storms = STATE["bank"], STATE["meta"], STATE["storms"]
    q = bank["q_0"].copy()
    if scenario == "local_q_absent":
        q[:, gi] = np.nan
    elif scenario == "all_q_absent":
        q[:] = np.nan
    age = meta[kind + "_bin_age_days"].to_numpy().reshape(-1, 8)[:, gi]
    day = storms.cutoff_utc.dt.dayofyear.to_numpy()
    harmonics = np.column_stack(
        [f(2 * np.pi * k * day / 365.25) for k in [2, 3, 4] for f in [np.sin, np.cos]]
    )
    return np.column_stack(
        [
            q.reshape(len(q), -1),
            bank["rain_0_1_0"][:, gi],
            storms.cutoff_utc.dt.year,
            coverage[:, gi],
            age,
            harmonics,
        ]
    )


def existing_point_fallback(scenario):
    bank = STATE["bank"]
    n = len(STATE["storms"])
    prediction = np.full((n, 8, 24), np.nan)
    frame = pd.read_parquet(STATE["source"] / f"scores/{scenario}__u0/scores.parquet")
    frame = frame[frame.method.eq("conventional") & frame.target_k.eq(5)]
    for row in frame.itertuples():
        qi, gi = divmod(row.case, 8)
        ids = row.trace_members
        if len(ids):
            prediction[qi, gi] = bank["outcome_0"][ids, gi].mean(axis=0)
        elif row.trace_kind == "persistence":
            measured = bank["q_0"][qi, gi]
            if np.isfinite(measured).any():
                prediction[qi, gi] = measured[np.flatnonzero(np.isfinite(measured))[-1]]
        elif np.isfinite(row.trace_crps):
            prior = bank["prior_0_0"][qi] & bank["outcome_valid_0"][:, gi]
            if prior.any():
                prediction[qi, gi] = bank["outcome_0"][prior, gi].mean(axis=0)
    areas = STATE["meta"].area_km2.to_numpy().reshape(n, 8)[0]
    return prediction * (3.6 / areas)[None, :, None]


def retrieval_controls(gi, j, scenario, eo_valid, contexts, quarter, *, seed):
    bank = STATE["bank"]
    n = len(STATE["storms"])
    scores = np.full((3 + CFG["permutations"], n), np.nan)
    sources = np.full((CFG["permutations"], n), -1, int)
    rng = np.random.default_rng(seed)
    keep = np.ones((1, 10, 72), bool)
    if scenario == "local_q_absent":
        keep[:, gi] = False
    if scenario == "all_q_absent":
        keep[:] = False
    for qi in range(n):
        if not bank["outcome_valid_0"][qi, gi]:
            continue
        allowed = bank["prior_0_0"][qi] & bank["outcome_valid_0"][:, gi] & eo_valid[:, gi]
        if not eo_valid[qi, gi] or not allowed.any():
            continue
        qd, support = partial_history_distances(
            bank["q_0"][qi],
            bank["donor_q_0"],
            bank["q_mean_0_0"][qi],
            bank["q_pairvar_0_0"][qi],
            keep,
        )
        rain = standard_distances(
            bank["rain_0_1_0"][qi, gi],
            bank["rain_0_1_0"][:, gi],
            bank["rain_mean_0_0"][qi, gi],
            bank["rain_var_0_0"][qi, gi],
        )
        conventional = combine_ground(qd, support, rain, gi)
        scale = bank["eo_pair_0_0"][j, gi, qi]
        real = STATE["eo_distance"][j, gi, qi] / scale
        ids = stable_members(
            np.concatenate([conventional, 0.5 * conventional + 0.5 * real[None]]), allowed
        )[:, :5]
        scores[:2, qi] = batch_scores(bank["outcome_0"][qi, gi], bank["outcome_0"][:, gi], ids)[0][
            :, 0
        ]
        candidates = np.flatnonzero(allowed & (quarter == quarter[qi]) & (contexts != contexts[qi]))
        if not len(candidates):
            continue
        selected = rng.choice(
            candidates, size=CFG["permutations"], replace=len(candidates) < CFG["permutations"]
        )
        sources[:, qi] = selected
        null = STATE["eo_distance"][j, gi, selected] / scale
        null_ids = stable_members(0.5 * conventional + 0.5 * null, allowed)[:, :5]
        scores[3:, qi] = batch_scores(
            bank["outcome_0"][qi, gi], bank["outcome_0"][:, gi], null_ids
        )[0][:, 0]
    return scores, sources


def run_job(job):
    model, kind = job
    name = model + "__" + kind
    target = OUT / "jobs" / name
    eo, coverage, valid, path = raw_features(model, kind)
    selected = json.loads((ROOT / "config/limburg_eo_coherent_selected_runs.json").read_text())[
        "models"
    ][model]
    files = [
        CONFIG,
        Path(__file__),
        ROOT / "src/eo_signal_diagnostic.py",
        ROOT / "src/scarcity.py",
        ROOT / "docs/limburg-eo-signal-diagnostic-2026-10-29.md",
        STATE["source"] / "preparation/manifest.json",
        path,
        ROOT / selected["run"] / "manifest.json",
        ROOT / "config/limburg_eo_coherent_selected_runs.json",
    ]
    fingerprints = {str(p.relative_to(ROOT)): sha256(p) for p in files}
    if (target / "manifest.json").exists():
        saved = json.loads((target / "manifest.json").read_text())
        if saved["sources_sha256"] != fingerprints:
            raise ValueError("Version changed diagnostic output instead of overwriting")
        for p, digest in saved["outputs_sha256"].items():
            if sha256(target / p) != digest:
                raise ValueError("Diagnostic output changed")
        return name, "reused"
    bank, meta, storms = STATE["bank"], STATE["meta"], STATE["storms"]
    n = len(storms)
    j = next(
        i for i, rep in enumerate(STATE["representations"]) if rep == dict(model=model, kind=kind)
    )
    np.testing.assert_array_equal(valid, bank["eo_valid"][j])
    overview, associations = representation_diagnostics(model, kind, eo, coverage, valid)
    contract = json.loads((ROOT / selected["run"] / "manifest.json").read_text())
    overview.update(
        checkpoint=contract["checkpoint"],
        selected_temporal_readout=contract["temporal_readout"],
        adapter_contract=contract["input_contract"],
    )
    years = storms.cutoff_utc.dt.year.to_numpy()
    quarter = storms.cutoff_utc.dt.quarter.to_numpy() - 1
    areas = meta.area_km2.to_numpy().reshape(n, 8)[0]
    y = bank["outcome_0"] * (3.6 / areas)[None, :, None]
    outputs, tuning, folds = {}, [], []
    began = time.monotonic()
    total = len(CFG["scenarios"]) * 8 * len(np.unique(years))
    done = 0
    for si, scenario in enumerate(CFG["scenarios"]):
        predictions = np.full((3 + CFG["permutations"], n, 8, 24), np.nan, dtype="float32")
        null_sources = np.full((CFG["permutations"], n, 8), -1, dtype="int32")
        used = np.zeros((n, 8), bool)
        active = np.zeros((n, 8), bool)
        fallback = existing_point_fallback(scenario)
        retrieved = np.full((3 + CFG["permutations"], n, 8), np.nan, dtype="float32")
        retrieved_sources = np.full((CFG["permutations"], n, 8), -1, dtype="int32")
        for gi in range(8):
            ground = conventional_inputs(gi, scenario, coverage, kind)
            for year in np.unique(years):
                boundary = pd.Timestamp(f"{year}-01-01", tz="UTC")
                closed = chronology(storms.cutoff_utc, storms.end_utc, boundary)
                full = np.flatnonzero(closed & bank["outcome_valid_0"][:, gi])
                train = full[valid[full, gi]]
                test = np.flatnonzero(years == year)
                validation_full = validation_splits(storms.cutoff_utc, storms.end_utc, years, full)
                validation = validation_splits(storms.cutoff_utc, storms.end_utc, years, train)
                pred, params, sources = readout_fold(
                    ground,
                    eo[:, gi],
                    y[:, gi],
                    full,
                    train,
                    test,
                    validation_full,
                    validation,
                    quarter,
                    CFG,
                    seed=CFG["seed"] + gi * 1009 + int(year) * 101,
                )
                supported = np.isfinite(pred[2]).all(axis=-1)
                used[test, gi] = supported
                real_parameters = [p for p in params if p["arm"] == "ground_real"]
                active[test, gi] = supported & bool(
                    real_parameters and real_parameters[0]["weight"] > 0
                )
                pred[0] = np.where(np.isfinite(pred[0]), pred[0], fallback[test, gi])
                for arm in range(1, len(pred)):
                    pred[arm] = np.where(np.isfinite(pred[arm]), pred[arm], pred[0])
                predictions[:, test, gi] = pred
                null_sources[:, test, gi] = sources
                for parameter in params:
                    tuning.append(
                        dict(
                            model=model,
                            readout=kind,
                            scenario=scenario,
                            gauge=meta.gauge.iloc[gi],
                            year=int(year),
                            **parameter,
                        )
                    )
                folds.append(
                    dict(
                        scenario=scenario,
                        gauge=meta.gauge.iloc[gi],
                        year=int(year),
                        train_ids=full.tolist(),
                        eo_train_ids=train.tolist(),
                        test_ids=test.tolist(),
                        boundary_utc=boundary.isoformat(),
                    )
                )
                done += 1
                atomic_json(
                    OUT / "progress" / (name + ".json"),
                    dict(
                        status="running",
                        percent_complete=100 * done / total,
                        completed_folds=done,
                        total_folds=total,
                        elapsed_s=time.monotonic() - began,
                    ),
                )
            contexts = meta[kind + "_context_id"].to_numpy().reshape(n, 8)[:, gi]
            crps, source = retrieval_controls(
                gi, j, scenario, valid, contexts, quarter, seed=CFG["seed"] + gi * 1009 + si * 10007
            )
            retrieved[:, :, gi] = crps * 3.6 / areas[gi]
            retrieved_sources[:, :, gi] = source
        outputs[scenario + "_predictions"] = predictions
        outputs[scenario + "_null_sources"] = null_sources
        outputs[scenario + "_eo_supported"] = used
        outputs[scenario + "_eo_active"] = active
        outputs[scenario + "_retrieval_crps"] = retrieved
        outputs[scenario + "_retrieval_sources"] = retrieved_sources
    with fresh_output(target) as work:
        np.savez_compressed(work / "predictions.npz", **outputs)
        pd.DataFrame(tuning).to_parquet(work / "tuning.parquet", index=False)
        pd.DataFrame(associations).to_csv(work / "representation-associations.csv", index=False)
        (work / "representation.json").write_text(json.dumps(overview, indent=2) + "\n")
        (work / "folds.json").write_text(json.dumps(folds, indent=2) + "\n")
        record = dict(
            status="completed",
            model=model,
            readout=kind,
            elapsed_s=time.monotonic() - began,
            sources_sha256=fingerprints,
            outputs_sha256={p.name: sha256(p) for p in work.iterdir()},
        )
        (work / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    atomic_json(
        OUT / "progress" / (name + ".json"),
        dict(status="completed", percent_complete=100.0, elapsed_s=time.monotonic() - began),
    )
    return name, "completed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["all", *CFG["models"]], default="all")
    parser.add_argument("--kind", choices=["all", *CFG["readouts"]], default="all")
    args = parser.parse_args()
    jobs = [
        (m, k)
        for m in CFG["models"]
        for k in CFG["readouts"]
        if args.model in ["all", m] and args.kind in ["all", k]
    ]
    completed = []
    state_path = OUT / (
        "execution.json" if args.model == args.kind == "all" else "benchmark_execution.json"
    )

    def record(status, **extra):
        atomic_json(
            state_path,
            dict(
                status=status,
                pid=os.getpid(),
                planned_jobs=len(jobs),
                completed_jobs=len(completed),
                percent_complete=100 * len(completed) / len(jobs),
                jobs=completed,
                updated_utc=datetime.now(timezone.utc).isoformat(),
                **extra,
            ),
        )

    record("running")
    with ProcessPoolExecutor(max_workers=CFG["workers"], initializer=initialize) as pool:
        pending = {pool.submit(run_job, job): job for job in jobs}
        for future in as_completed(pending):
            try:
                result = future.result()
            except Exception as exc:
                record("failed", failed_job=pending[future], error=str(exc))
                raise
            completed.append(result)
            record("running")
            print(result, flush=True)
    record("completed")


if __name__ == "__main__":
    main()
