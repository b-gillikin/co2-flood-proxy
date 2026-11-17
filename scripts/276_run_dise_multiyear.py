"""Prepare/run the saved Step 2 queue; two CPU jobs, identical scientific budgets.

Each outer job checkpoints individual fits. No new acquisitions or Step 3 run.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from src.dise import CANDIDATES, feature_columns, reconstruct, residual_target
from src.dise_capacity import select_validation
from src.dise_corrected import fit_candidate, weights
from src.dise_multiyear import (
    annotate,
    assert_census,
    calibration,
    coverage,
    evaluation,
    extended_assignment,
    jobs_for,
    masks,
    split_weight_table,
)
from src.dise_regional import inner_masks
from src.geoglows_experiment import disk_check, sha, write_json

CONFIG = ROOT / "config/limburg_dise_multiyear_v1.json"
PLAN = json.loads(CONFIG.read_text())
OUT = ROOT / PLAN["output"]
PREP = ROOT / PLAN["preparation"]
CAP = ROOT / PLAN["capacity_source"]
SLOTS = (
    len(PLAN["policies"])
    * len(PLAN["arms"])
    * (len(CANDIDATES) * PLAN["inner_folds"] + len(PLAN["seeds"]))
)
META = [
    "day",
    "gauge",
    "station",
    "river_group",
    "source_role",
    "reference_area_km2",
    "q_observed",
    "q_model",
    "clean_verification",
    "overlap_stratum",
    "location_stratum",
    "spatial_view_high_overlap",
    "spatial_view_location_consistent",
    "spatial_view_stress",
]


def utc():
    return datetime.now(timezone.utc).isoformat()


def peak_gib():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (
        2**30 if sys.platform == "darwin" else 2**20
    )


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def identity():
    paths = [
        CONFIG,
        Path(__file__),
        ROOT / "src/dise_multiyear.py",
        ROOT / "src/dise.py",
        ROOT / "src/dise_corrected.py",
        ROOT / "src/dise_regional.py",
        ROOT / "src/dise_capacity.py",
        ROOT / "src/geoglows_experiment.py",
        ROOT / "scripts/272_benchmark_dise_regional_fold.py",
        PREP / "features.parquet",
        PREP / "inner_folds.json",
        PREP / "audit.json",
        CAP / "manifest.json",
        OUT / "inner_folds.json",
        OUT / "jobs.json",
    ]
    return dict(
        sources={str(p.relative_to(ROOT)): sha(p) for p in paths},
        packages={
            n: importlib.metadata.version(n) for n in ["numpy", "pandas", "xgboost", "scikit-learn"]
        },
    )


def verify_manifest(path):
    m = json.loads(path.read_text())
    if m["status"] != "completed":
        raise ValueError(f"Incomplete source: {path}")
    for name, h in m["outputs"].items():
        if sha(path.parent / name) != h:
            raise ValueError(f"Changed completed output: {name}")
    return m


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    disk_check(ROOT, PLAN["reserve_gib"], 2 * 2**30)
    cap = verify_manifest(CAP / "manifest.json")
    for name, h in cap["identity"]["sources"].items():
        if sha(ROOT / name) != h:
            raise ValueError(f"Changed capacity scientific input: {name}")
    if list(CANDIDATES) != PLAN["candidates"] or PLAN["threads_per_fit"] != 2:
        raise ValueError("Declared estimator mismatch")
    f = pd.read_parquet(
        PREP / "features.parquet",
        columns=["gauge", "river_group", "source_role", "day", "q_observed", "q_model"],
    )
    if sorted(f.loc[f.source_role.eq("local"), "river_group"].unique()) != sorted(
        PLAN["local_groups"]
    ):
        raise ValueError("Local river-group census changed")
    original = json.loads((PREP / "inner_folds.json").read_text())
    assignment = extended_assignment(f, original, PLAN["inner_folds"], PLAN["fold_seed"])
    for path, value in [
        (OUT / "inner_folds.json", assignment),
        (OUT / "jobs.json", jobs_for(PLAN)),
    ]:
        if path.exists() and json.loads(path.read_text()) != value:
            raise ValueError("Frozen queue/folds changed")
        write_json(path, value)
    ident = identity()
    if ident["packages"] != cap["identity"]["packages"]:
        raise ValueError("Use the pinned DISE environment")
    manifest = OUT / "preparation.json"
    if manifest.exists() and json.loads(manifest.read_text())["identity"] != ident:
        raise ValueError("Queue identity changed: version it instead of overwriting")
    sizes = []
    ledgers = []
    for job in jobs_for(PLAN):
        tr, va, te, targets = masks(f, job, PLAN["external_test_years"])
        if not f.loc[tr | va, "river_group"].isin(assignment).all():
            raise ValueError("Unassigned fitting group")
        for k in range(PLAN["inner_folds"]):
            it, iv = inner_masks(f, tr, va, assignment, k)
            if not it.any() or not iv.any():
                raise ValueError("Empty inner split")
        sizes.append(
            dict(
                **job,
                train_rows=int(tr.sum()),
                validation_rows=int(va.sum()),
                test_rows=int(te.sum()),
                test_gauges=int(f.loc[te, "gauge"].nunique()),
                train_gauges=int(f.loc[tr, "gauge"].nunique()),
                logical_fits=SLOTS,
            )
        )
        ledgers.append(coverage(f, te, targets, job).assign(outer_job=job["id"]))
    pd.DataFrame(sizes).to_csv(OUT / "split_inventory.csv", index=False)
    pd.concat(ledgers, ignore_index=True).to_csv(OUT / "coverage.csv", index=False)
    record = dict(
        status="prepared",
        identity=ident,
        jobs=len(sizes),
        logical_fits=SLOTS * len(sizes),
        reusable_fits=SLOTS,
        expected_prediction_rows=sum(j["test_rows"] for j in sizes),
        original_folds_unchanged=True,
        added_inner_groups=sorted(set(assignment) - set(original)),
        workers=PLAN["concurrent_fits"],
        threads_per_fit=2,
        free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
        prepared_utc=utc(),
    )
    write_json(manifest, record)
    print(json.dumps({k: v for k, v in record.items() if k != "identity"}, indent=2), flush=True)
    return ident


def load_receipt(path, ident):
    r = json.loads(path.read_text())
    if r["identity"] != ident or r["payload_sha256"] != digest(r["payload"]):
        raise ValueError(f"Changed checkpoint: {path}")
    return r["payload"]


def save_receipt(path, ident, payload):
    write_json(path, dict(identity=ident, payload=payload, payload_sha256=digest(payload)))


def worker(job):
    dest = OUT / "jobs" / job["id"]
    dest.mkdir(parents=True, exist_ok=True)
    lock = (dest / "runner.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    ident = dict(**identity(), job=job)
    prepared = json.loads((OUT / "preparation.json").read_text())
    if {k: v for k, v in ident.items() if k != "job"} != prepared["identity"]:
        raise ValueError("Prepared run inputs/code changed")
    if (dest / "manifest.json").exists():
        m = json.loads((dest / "manifest.json").read_text())
        if m["identity"] != ident:
            raise ValueError("Outer-fold identity changed")
        if m["status"] == "completed":
            verify_manifest(dest / "manifest.json")
            return
    write_json(dest / "manifest.json", dict(status="running", identity=ident, started_utc=utc()))
    frame = pd.read_parquet(PREP / "features.parquet")
    tr, va, te, targets = masks(frame, job, PLAN["external_test_years"])
    past = tr | va
    assignment = json.loads((OUT / "inner_folds.json").read_text())
    split_weight_table(frame, tr, va, te, assignment, PLAN["inner_folds"]).to_parquet(
        dest / "split_weights.parquet", index=False
    )
    coverage(frame, te, targets, job).to_csv(dest / "coverage.csv", index=False)
    before = time.monotonic()
    done = 0
    fresh = 0
    reused = 0
    fit_seconds = 0.0
    reuse = job["id"] == "held_Wurm_2021"
    old_predictions = pd.read_parquet(CAP / "predictions.parquet") if reuse else None
    old_local = None
    if reuse:
        old_local = old_predictions.source_role.eq("local").to_numpy()
        pd.testing.assert_frame_equal(
            frame.loc[te, META].reset_index(drop=True),
            old_predictions.loc[old_local, META].reset_index(drop=True),
            check_exact=True,
        )

    def progress(phase, **extra):
        write_json(
            dest / "progress.json",
            dict(
                status="running",
                phase=phase,
                job=job,
                completed_fits=done,
                total_fits=SLOTS,
                percent=100 * done / SLOTS,
                fresh_fits=fresh,
                reused_fits=reused,
                fit_seconds=fit_seconds,
                session_seconds=time.monotonic() - before,
                peak_rss_gib=peak_gib(),
                free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
                updated_utc=utc(),
                **extra,
            ),
        )

    progress("starting")
    predictions = frame.loc[te, META].copy()
    tuning = []
    selected = {}
    for policy in PLAN["policies"]:
        for arm in PLAN["arms"]:
            columns = feature_columns(frame, arm)
            records = []
            for ci, candidate in enumerate(CANDIDATES):
                for fold in range(PLAN["inner_folds"]):
                    key = f"{policy}_{arm.replace('+', '_')}_{ci}_{fold}"
                    path = dest / f"tune_{key}.json"
                    if path.exists():
                        payload = load_receipt(path, ident)
                    else:
                        disk_check(ROOT, PLAN["reserve_gib"], 512 * 2**20)
                        progress("tuning", active_fit=key)
                        if reuse:
                            saved = json.loads((CAP / f"tune_{key}.json").read_text())
                            if sha(CAP / f"tune_{key}.ubj") != saved["model_sha256"]:
                                raise ValueError("Capacity tuning model changed")
                            record = saved["record"]
                            cols = saved["columns"]
                            origin = "reused_capacity_tuning"
                        else:
                            it, iv = inner_masks(frame, tr, va, assignment, fold)
                            model, cols, record = fit_candidate(
                                frame.loc[it],
                                frame.loc[iv],
                                columns,
                                candidate,
                                policy,
                                PLAN["seeds"][0],
                                PLAN["tree_limit"],
                            )
                            record.update(
                                candidate_index=ci,
                                fold=fold,
                                train_rows=int(it.sum()),
                                validation_rows=int(iv.sum()),
                                validation_groups=int(frame.loc[iv, "river_group"].nunique()),
                                tree_cap_hit=model.get_booster().num_boosted_rounds()
                                == PLAN["tree_limit"],
                                fitted_boosting_rounds=model.get_booster().num_boosted_rounds(),
                            )
                            del model
                            origin = "new_multiyear_fit"
                        payload = dict(record=record, columns=cols, origin=origin)
                        if reuse:
                            payload["source_receipt_sha256"] = sha(CAP / f"tune_{key}.json")
                        save_receipt(path, ident, payload)
                    r = payload["record"]
                    records.append(r)
                    tuning.append(dict(arm=arm, origin=payload["origin"], **r))
                    done += 1
                    fit_seconds += r["seconds"]
                    if reuse:
                        reused += 1
                    else:
                        fresh += 1
                    progress("tuning", last_fit=key)
                    print(
                        f"{job['id']} {done}/{SLOTS} ({100 * done / SLOTS:.1f}%) {key}", flush=True
                    )
            name = f"{policy}__{arm}"
            settings = select_validation(records, policy, CANDIDATES)
            selected[name] = settings
            if reuse:
                old = json.loads((CAP / "selected.json").read_text())[name]
                if settings != old:
                    raise ValueError("Capacity selection reuse differs")
            cols = [
                c
                for c in columns
                if np.isfinite(frame.loc[past, c]).any() and frame.loc[past, c].nunique() > 1
            ]
            parts = []
            for seed in PLAN["seeds"]:
                key = f"{name.replace('+', '_')}_{seed}"
                path = dest / f"final_{key}.ubj"
                array = dest / f"final_{key}.npy"
                receipt = dest / f"final_{key}.json"
                if receipt.exists():
                    payload = load_receipt(receipt, ident)
                    if (
                        sha(path) != payload["model_sha256"]
                        or sha(array) != payload["prediction_sha256"]
                    ):
                        raise ValueError("Final checkpoint changed")
                    pred = np.load(array)
                else:
                    disk_check(ROOT, PLAN["reserve_gib"], 512 * 2**20)
                    progress("final_fit", active_fit=key)
                    start = time.monotonic()
                    if reuse:
                        old = json.loads((CAP / f"final_{key}.json").read_text())
                        if (
                            old["columns"] != cols
                            or sha(CAP / f"final_{key}.ubj") != old["model_sha256"]
                        ):
                            raise ValueError("Capacity final specification changed")
                        shutil.copyfile(CAP / f"final_{key}.ubj", path)
                        model = XGBRegressor(n_jobs=2)
                        model.load_model(path)
                    else:
                        model = XGBRegressor(
                            **settings["parameters"],
                            n_estimators=settings["trees"],
                            n_jobs=2,
                            tree_method="hist",
                            subsample=0.8,
                            colsample_bytree=0.8,
                            reg_lambda=10,
                            reg_alpha=0.1,
                            objective="reg:squarederror",
                            random_state=seed,
                        )
                        model.fit(
                            frame.loc[past, cols],
                            residual_target(
                                frame.loc[past, "q_observed"], frame.loc[past, "q_model"]
                            ),
                            sample_weight=weights(frame.loc[past]),
                        )
                        model.save_model(path)
                    pred, clipped = reconstruct(
                        frame.loc[te, "q_model"].to_numpy(), model.predict(frame.loc[te, cols])
                    )
                    del model
                    if reuse and not np.array_equal(
                        pred, np.load(CAP / f"final_{key}.npy")[old_local]
                    ):
                        raise ValueError("Capacity seed predictions differ")
                    np.save(array, pred)
                    payload = dict(
                        columns=cols,
                        seconds=time.monotonic() - start,
                        origin="reused_capacity_final" if reuse else "new_multiyear_fit",
                        model_sha256=sha(path),
                        prediction_sha256=sha(array),
                        negative_reconstructions_floored=clipped,
                    )
                    save_receipt(receipt, ident, payload)
                parts.append(pred)
                done += 1
                fit_seconds += payload["seconds"]
                if reuse:
                    reused += 1
                else:
                    fresh += 1
                progress("final_fit", last_fit=key)
            predictions[name] = np.mean(parts, axis=0)
    refs, calibration_records = calibration(frame, tr, va, te, job["year"])
    write_json(dest / "calibration.json", calibration_records)
    predictions = predictions.join(refs)
    if reuse:
        for c in ["local_fdc", "donor_fdc"]:
            assert np.array_equal(
                predictions[c].to_numpy(),
                old_predictions.loc[old_local, c].to_numpy(),
                equal_nan=True,
            )
    predictions, thresholds = annotate(frame, predictions, job)
    names = ["q_model", "donor_fdc", *[f"{p}__{a}" for p in PLAN["policies"] for a in PLAN["arms"]]]
    metrics, populations = evaluation(predictions, names)
    for name in names + ["local_fdc"]:
        predictions[name + "_m3s"] = predictions[name] * predictions.reference_area_km2 / 86.4
    predictions.to_parquet(dest / "predictions.parquet", index=False)
    pd.DataFrame(tuning).to_csv(dest / "tuning.csv", index=False)
    write_json(dest / "selected.json", selected)
    write_json(
        dest / "thresholds.json",
        dict(
            evaluator_only=True,
            reference=f"held-target history 2018-{job['year'] - 1}, not predictor/tuning information",
            values={g: float(v) if np.isfinite(v) else None for g, v in thresholds.items()},
        ),
    )
    write_json(dest / "populations.json", populations)
    write_json(dest / "metrics.json", metrics)
    pd.DataFrame([{k: v for k, v in r.items() if k != "per_gauge"} for r in metrics]).to_csv(
        dest / "metrics.csv", index=False
    )
    table = pd.DataFrame(tuning)
    write_json(
        dest / "readout.json",
        dict(
            job=job,
            completed_fits=done,
            fresh_fits=fresh,
            reused_fits=reused,
            session_seconds=time.monotonic() - before,
            recorded_fit_seconds=fit_seconds,
            peak_rss_gib=peak_gib(),
            test_rows=int(te.sum()),
            test_gauges=int(predictions.gauge.nunique()),
            capped_tuning_fits=int(table.tree_cap_hit.sum()),
            selected_fold_caps={
                n: int(
                    table.loc[
                        table.policy.eq(n.split("__")[0])
                        & table.arm.eq(n.split("__")[1])
                        & table.candidate_index.eq(s["candidate_index"]),
                        "tree_cap_hit",
                    ].sum()
                )
                for n, s in selected.items()
            },
            uncertainty="Per-year point estimates; dependence-aware pooled uncertainty remains saved Step 3.",
        ),
    )
    if dict(**identity(), job=job) != ident:
        raise ValueError("Scientific inputs/code changed during fitting")
    outputs = {
        p.name: sha(p)
        for p in dest.iterdir()
        if p.is_file()
        and p.name not in ["manifest.json", "progress.json", "runner.lock", "failure.json"]
    }
    write_json(
        dest / "manifest.json",
        dict(status="completed", identity=ident, outputs=outputs, completed_utc=utc()),
    )
    write_json(
        dest / "progress.json",
        dict(
            status="completed",
            phase="complete",
            job=job,
            completed_fits=done,
            total_fits=SLOTS,
            percent=100,
            fresh_fits=fresh,
            reused_fits=reused,
            session_seconds=time.monotonic() - before,
            updated_utc=utc(),
        ),
    )
    (dest / "failure.json").unlink(missing_ok=True)
    print(f"Completed {job['id']}", flush=True)


def aggregate(ident):
    parts = []
    metrics = []
    readouts = []
    for job in jobs_for(PLAN):
        dest = OUT / "jobs" / job["id"]
        m = verify_manifest(dest / "manifest.json")
        if m["identity"] != dict(**ident, job=job):
            raise ValueError("Different job identity")
        parts.append(pd.read_parquet(dest / "predictions.parquet"))
        metrics.append(
            pd.read_csv(dest / "metrics.csv").assign(
                outer_job=job["id"],
                year=job["year"],
                regime="spatial" if job["held"] else "temporal",
            )
        )
        readouts.append(json.loads((dest / "readout.json").read_text()))
    p = pd.concat(parts, ignore_index=True)
    expected = json.loads((OUT / "preparation.json").read_text())["expected_prediction_rows"]
    assert_census(p, expected)
    if p.loc[p.source_role.eq("reserved_external"), "regime"].ne("temporal").any():
        raise ValueError("Repeated external evaluation")
    p.to_parquet(OUT / "predictions.parquet", index=False)
    pd.concat(metrics, ignore_index=True).to_csv(OUT / "metrics_by_job.csv", index=False)
    names = ["q_model", "donor_fdc", *[f"{v}__{a}" for v in PLAN["policies"] for a in PLAN["arms"]]]
    pooled = []
    for regime, f in p.groupby("regime"):
        rows, _ = evaluation(f, names)
        pooled.extend(dict(regime=regime, **r) for r in rows)
    write_json(OUT / "pooled_metrics.json", pooled)
    pd.DataFrame([{k: v for k, v in r.items() if k != "per_gauge"} for r in pooled]).to_csv(
        OUT / "pooled_metrics.csv", index=False
    )
    pd.DataFrame(readouts).to_json(OUT / "job_readouts.json", orient="records", indent=2)
    if identity() != ident:
        raise ValueError("Queue identity changed")
    write_json(
        OUT / "completion.json",
        dict(
            status="completed",
            completed_utc=utc(),
            identity=ident,
            jobs=len(parts),
            logical_fits=len(parts) * SLOTS,
            test_rows=len(p),
            test_gauges=int(p.gauge.nunique()),
            scope="Step 2; Steps 3-4 remain pending",
            outputs={
                p.name: sha(p)
                for p in OUT.iterdir()
                if p.is_file()
                and p.name
                not in ["completion.json", "progress.json", "queue.lock", "queue_failure.json"]
            },
        ),
    )
    update_live("complete", 0)


def update_live(status, workers):
    workflow = ROOT / PLAN["workflow_plan"]
    w = json.loads(workflow.read_text())
    w["current_authorization"] = "Execute Steps 1-2; Steps 3-4 remain saved and unlaunched."
    for step in w["steps"]:
        if step["number"] == 2:
            step.update(
                status=status,
                config=str(CONFIG.relative_to(ROOT)),
                progress=str((OUT / "progress.json").relative_to(ROOT)),
            )
    write_json(workflow, w)
    current = ROOT / "config/limburg_current_study.json"
    c = json.loads(current.read_text())
    c.update(
        status="dise_multiyear_complete" if status == "complete" else "dise_multiyear_running",
        multiyear_config=str(CONFIG.relative_to(ROOT)),
        progress=str((OUT / "progress.json").relative_to(ROOT)),
        active_workers=dict(fitting=workers, threads_per_fit=2 if workers else 0, gpu=0),
        full_regional_comparison_started=True,
        multiyear_completed=status == "complete",
    )
    write_json(current, c)


def run_queue():
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / "queue.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    ident = prepare()
    jobs = jobs_for(PLAN)
    pending = []
    finished = []
    failed = []
    active = {}
    for job in jobs:
        manifest = OUT / "jobs" / job["id"] / "manifest.json"
        if manifest.exists() and json.loads(manifest.read_text())["status"] == "completed":
            m = verify_manifest(manifest)
            if m["identity"] != dict(**ident, job=job):
                raise ValueError("Stale completed job")
            finished.append(job["id"])
        else:
            pending.append(job)
    update_live("in_progress", min(PLAN["concurrent_fits"], len(pending)))
    (OUT / "logs").mkdir(exist_ok=True)
    try:
        while pending or active:
            while pending and len(active) < PLAN["concurrent_fits"]:
                disk_check(ROOT, PLAN["reserve_gib"], 2 * 2**30)
                job = pending.pop(0)
                log = (OUT / "logs" / (job["id"] + ".log")).open("a")
                env = dict(
                    os.environ,
                    OMP_NUM_THREADS="2",
                    OPENBLAS_NUM_THREADS="2",
                    VECLIB_MAXIMUM_THREADS="2",
                )
                child = subprocess.Popen(
                    [sys.executable, str(Path(__file__).resolve()), "worker", "--job", job["id"]],
                    cwd=ROOT,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                active[job["id"]] = (child, log, job)
            for key, (child, log, job) in list(active.items()):
                code = child.poll()
                if code is None:
                    continue
                log.close()
                del active[key]
                if code == 0:
                    finished.append(key)
                else:
                    failed.append(
                        dict(
                            job=job,
                            returncode=code,
                            log=str((OUT / "logs" / (key + ".log")).relative_to(ROOT)),
                        )
                    )
            slots = len(finished) * SLOTS
            details = []
            for key in active:
                path = OUT / "jobs" / key / "progress.json"
                if path.exists():
                    r = json.loads(path.read_text())
                    slots += r["completed_fits"]
                    details.append(r)
            write_json(
                OUT / "progress.json",
                dict(
                    status="running",
                    completed_jobs=len(finished),
                    total_jobs=len(jobs),
                    completed_fits=slots,
                    total_fits=len(jobs) * SLOTS,
                    percent=100 * slots / (len(jobs) * SLOTS),
                    running=details,
                    pending_jobs=len(pending),
                    failures=failed,
                    free_gib=shutil.disk_usage(ROOT).free / 2**30,
                    updated_utc=utc(),
                ),
            )
            time.sleep(5 if active else 0)
        if failed:
            write_json(
                OUT / "queue_failure.json",
                dict(status="incomplete", failures=failed, successful_jobs=finished),
            )
            update_live("in_progress", 0)
            write_json(
                OUT / "progress.json",
                dict(
                    status="incomplete",
                    completed_jobs=len(finished),
                    total_jobs=len(jobs),
                    failures=failed,
                    updated_utc=utc(),
                ),
            )
            raise RuntimeError(
                "Incomplete outer jobs retained; see queue_failure.json. Resume same queue after resolving errors."
            )
        aggregate(ident)
        write_json(
            OUT / "progress.json",
            dict(
                status="completed",
                completed_jobs=len(jobs),
                total_jobs=len(jobs),
                completed_fits=len(jobs) * SLOTS,
                total_fits=len(jobs) * SLOTS,
                percent=100,
                free_gib=shutil.disk_usage(ROOT).free / 2**30,
                updated_utc=utc(),
            ),
        )
        print("Step 2 complete; Steps 3-4 not launched", flush=True)
    finally:
        for child, log, _job in active.values():
            if child.poll() is None:
                child.terminate()
                child.wait()
            log.close()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda _signum, _frame: sys.exit(130))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "run", "worker"])
    parser.add_argument("--job")
    args = parser.parse_args()
    try:
        if args.phase == "prepare":
            prepare()
        elif args.phase == "run":
            run_queue()
        else:
            job = next(j for j in jobs_for(PLAN) if j["id"] == args.job)
            worker(job)
    except Exception as exc:
        if args.phase == "worker" and args.job:
            write_json(
                OUT / "jobs" / args.job / "failure.json",
                dict(status="failed", error=repr(exc), utc=utc()),
            )
        raise
