"""One complete local held-Wurm outer fold; not the regional/full comparison."""

from __future__ import annotations

import fcntl
import importlib.metadata
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from src.dise import (
    ARMS,
    CANDIDATES,
    balanced_mae,
    feature_columns,
    fit_candidate,
    reconstruct,
    residual_target,
    split_masks,
    weights,
)
from src.geoglows_experiment import disk_check, sha, write_json

CONFIG = ROOT / "config/limburg_dise_v1.json"
PLAN = json.loads(CONFIG.read_text())
OUT = ROOT / PLAN["output"]
DEST = OUT / "benchmark_local_wurm_2021"


def purge_spanning_storms(frame, year):
    source = ROOT / "results/limburg_scarcity_v2_2026_10_28/preparation/storms.parquet"
    storms = pd.read_parquet(source).drop_duplicates("storm_id")
    starts, ends = pd.to_datetime(storms.start_utc, utc=True), pd.to_datetime(storms.end_utc, utc=True)
    mask = np.zeros(len(frame), bool)
    day = pd.to_datetime(frame.day, utc=True)
    for boundary in [pd.Timestamp(f"{year-1}-01-01", tz="UTC"), pd.Timestamp(f"{year}-01-01", tz="UTC")]:
        for start, end in zip(starts[(starts < boundary) & (ends >= boundary)], ends[(starts < boundary) & (ends >= boundary)], strict=True):
            mask |= day.between(start.floor("D"), end.floor("D")).to_numpy()
    return mask, source


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    lock = (DEST / "runner.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    source = OUT / "local_features.parquet"
    inputs = [CONFIG, source, ROOT / "src/dise.py", Path(__file__)]
    for y in PLAN["weather_years"]:
        path = ROOT / PLAN["raw"] / "weather" / f"local_daily_{y}.parquet"
        receipt = json.loads(path.with_suffix(path.suffix + ".receipt.json").read_text())
        if receipt["sha256"] != sha(path):
            raise ValueError("Forcing file differs from receipt")
    frame = pd.read_parquet(source)
    year, excluded = PLAN["benchmark_year"], PLAN["benchmark_excluded_group"]
    purge, storm_path = purge_spanning_storms(frame, year)
    inputs += [storm_path]
    pinned = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    identity = dict(sources=pinned, year=year, excluded_group=excluded, candidates=CANDIDATES,
                    packages={n: importlib.metadata.version(n) for n in ["xgboost", "scikit-learn", "numpy", "pandas"]})
    train, validation, test = split_masks(frame, year, excluded)
    train &= ~purge
    validation &= ~purge
    test &= ~purge
    if not all(x.any() for x in [train, validation, test]):
        raise ValueError("Outer fold is empty")
    # Four inner held-river validation folds, entirely outside the outer Wurm group.
    groups = sorted(frame.loc[train, "river_group"].unique())
    if excluded in groups:
        raise ValueError("Outer held river entered training")
    n_expected = len(ARMS) * (len(CANDIDATES) * len(groups) + len(PLAN["seeds"]))
    old = DEST / "manifest.json"
    if old.exists():
        rec = json.loads(old.read_text())
        if rec["identity"] != json.loads(json.dumps(identity)):
            raise ValueError("Benchmark inputs changed; use a new versioned output")
        if rec["status"] == "completed":
            for name, digest in rec["outputs"].items():
                if sha(DEST / name) != digest:
                    raise ValueError("Completed benchmark output changed")
            print("Benchmark already complete and verified")
            return
    write_json(old, dict(status="running", identity=identity))
    start_all = time.monotonic()
    completed = 0
    selected = {}
    predictions = frame.loc[test, ["day", "gauge", "station", "river_group", "q_observed", "q_model", "clean_verification"]].copy()
    tuning_rows = []
    timings = []

    def progress(arm, phase):
        write_json(DEST / "progress.json", dict(status="running", arm=arm, phase=phase,
                   fits_done=completed, fits_expected=n_expected, percent=100*completed/n_expected,
                   elapsed_seconds=time.monotonic()-start_all, free_gib=disk_check(ROOT, PLAN["reserve_gib"])))
        print(f"{completed}/{n_expected} fits ({100*completed/n_expected:.1f}%) {arm} {phase}", flush=True)

    for arm in ARMS:
        columns = feature_columns(frame, arm)
        records = []
        for ci, candidate in enumerate(CANDIDATES):
            for group in groups:
                it = train & frame.river_group.ne(group).to_numpy()
                iv = validation & frame.river_group.eq(group).to_numpy()
                if not it.any() or not iv.any():
                    raise ValueError("Empty inner group: cannot silently reduce tuning population")
                checkpoint = DEST / f"tune_{arm.replace('+','_')}_{ci}_{group}.json"
                if checkpoint.exists():
                    saved = json.loads(checkpoint.read_text())
                    if saved["identity"] != json.loads(json.dumps(identity)):
                        raise ValueError("Tuning checkpoint changed")
                    record = saved["record"]
                else:
                    _, _, record = fit_candidate(frame.loc[it], frame.loc[iv], columns, candidate)
                    record.update(candidate_index=ci, inner_group=group, train_rows=int(it.sum()), validation_rows=int(iv.sum()))
                    write_json(checkpoint, dict(identity=identity, record=record))
                records.append(record)
                tuning_rows.append(dict(arm=arm, **record))
                timings.append(record["seconds"])
                completed += 1
                progress(arm, "nested_tuning")
        table = pd.DataFrame(records)
        best = int(table.groupby("candidate_index").validation_mae.mean().idxmin())
        trees = max(1, int(np.median(table.loc[table.candidate_index.eq(best), "best_iteration"])) + 1)
        selected[arm] = dict(parameters=CANDIDATES[best], trees=trees, selection="inner-held-river validation MAE")
        # Refit all allowed pre-test observations with the selected tree count.
        past = train | validation
        cols = [c for c in columns if np.isfinite(frame.loc[past, c]).any() and frame.loc[past, c].nunique() > 1]
        seed_predictions = []
        for seed in PLAN["seeds"]:
            model = XGBRegressor(**CANDIDATES[best], n_estimators=trees, n_jobs=2, tree_method="hist",
                                 subsample=0.8, colsample_bytree=0.8, reg_lambda=10, reg_alpha=0.1,
                                 objective="reg:squarederror", random_state=seed)
            before = time.monotonic()
            model.fit(frame.loc[past, cols], residual_target(frame.loc[past, "q_observed"], frame.loc[past, "q_model"]), sample_weight=weights(frame.loc[past]))
            predicted, clipped = reconstruct(frame.loc[test, "q_model"].to_numpy(), model.predict(frame.loc[test, cols]))
            seed_predictions.append(predicted)
            model.save_model(DEST / f"model_{arm.replace('+','_')}_{seed}.json")
            timings.append(time.monotonic()-before)
            selected[arm][f"floored_test_{seed}"] = clipped
            completed += 1
            progress(arm, "selected_seed_refit")
        predictions[arm] = np.mean(seed_predictions, axis=0)
    predictions.to_parquet(DEST / "predictions.parquet", index=False)
    pd.DataFrame(tuning_rows).to_csv(DEST / "tuning.csv", index=False)
    # Evaluator-only thresholds use held Wurm history; never supplied to fitting.
    evaluator = frame.loc[frame.day.lt(f"{year}-01-01") & frame.day.ge("2018-01-01")]
    thresholds = evaluator.groupby("gauge").q_observed.quantile(0.99)
    predictions["high_water"] = predictions.q_observed.ge(predictions.gauge.map(thresholds))
    metrics = []
    for stratum, part in [("all_days", predictions), ("daily_training_p99", predictions.loc[predictions.high_water])]:
        for arm in ["q_model", *ARMS]:
            metrics.append(dict(stratum=stratum, arm=arm, rows=len(part),
                                mae=balanced_mae(part, part[arm]) if len(part) else None))
    write_json(DEST / "readout.json", dict(scope="local engineering/validity benchmark, not the regional study",
               selected=selected, metrics=metrics, year=year, held_river=excluded,
               training_rivers=groups, train_rows=int(train.sum()), validation_rows=int(validation.sum()),
               test_rows=int(test.sum()), purged_storm_days=int(purge.sum()),
               seconds=time.monotonic()-start_all, fit_seconds_median=float(np.median(timings)),
               fits_completed=completed, feature_input_missing_cells=int(frame[feature_columns(frame, "H+A+E")].isna().sum().sum()),
               regional_scale_eta_not_measured=True))
    if {str(p.relative_to(ROOT)): sha(p) for p in inputs} != pinned:
        raise ValueError("Input/code changed during fitting; do not accept results")
    outputs = {p.name: sha(p) for p in DEST.iterdir() if p.suffix in [".parquet", ".csv", ".json"] and p.name not in ["manifest.json", "progress.json"]}
    write_json(old, dict(status="completed", identity=identity, outputs=outputs))
    write_json(DEST / "progress.json", dict(status="completed", fits_done=completed, fits_expected=n_expected,
               percent=100, elapsed_seconds=time.monotonic()-start_all))
    print("Local outer fold completed; regional donor acquisition/mapping is still separate.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        write_json(DEST / "failure.json", dict(status="failed", error=repr(exc), process=os.getpid()))
        state_path = DEST / "progress.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        write_json(state_path, {**state, "status": "failed", "error": repr(exc)})
        raise
