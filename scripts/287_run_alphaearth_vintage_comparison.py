"""Refit the AlphaEarth arm using 2020 imagery on the original DISE folds."""

import fcntl
import importlib.util
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/limburg_representation_extension_v1"
OUT = BASE / "alphaearth_vintage_c0"
GEUL = BASE / "satellite_c0_benchmark_2020/jobs/held_Geul_2021"


def main():
    spec = importlib.util.spec_from_file_location(
        "dise_runner", ROOT / "scripts/276_run_dise_multiyear.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    OUT.mkdir(exist_ok=True)
    with (OUT / "queue.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(runner)


def run(runner):
    original = runner.OUT
    original_features = runner.PREP / "features.parquet"
    alpha = BASE / "alphaearth_2020/descriptors_2020.parquet"
    quality = BASE / "alphaearth_2020/quality_2020.json"
    audit = json.loads(quality.read_text())
    if (
        audit["status"] != "complete"
        or audit["year"] != 2020
        or runner.sha(alpha) != audit["alphaearth_parquet_sha256"]
    ):
        raise ValueError("2020 AlphaEarth does not match its quality receipt")
    source = runner.verify_manifest(original / "completion.json")
    runner.OUT = OUT
    runner.PREP = OUT / "preparation"
    runner.PREP.mkdir(exist_ok=True)
    runner.PLAN = dict(runner.PLAN, arms=["H+A+E"])
    runner.SLOTS = len(runner.PLAN["policies"]) * (
        len(runner.CANDIDATES) * runner.PLAN["inner_folds"] + len(runner.PLAN["seeds"])
    )
    features = runner.PREP / "features.parquet"
    receipt = runner.PREP / "audit.json"
    inputs = {
        str(p.relative_to(ROOT)): runner.sha(p)
        for p in (original_features, alpha, quality, Path(__file__), original / "completion.json")
    }
    if (
        source["identity"]["sources"][str(original_features.relative_to(ROOT))]
        != inputs[str(original_features.relative_to(ROOT))]
    ):
        raise ValueError("Original fit used different daily inputs")
    if receipt.exists():
        if json.loads(receipt.read_text()) != dict(inputs=inputs, sha256=runner.sha(features)):
            raise ValueError("Prepared inputs no longer match the receipt")
    else:
        runner.disk_check(ROOT, runner.PLAN["reserve_gib"], 2 * 2**30)
        frame = pd.read_parquet(original_features)
        atlas = pd.read_parquet(alpha)
        bands = [f"A{i:02d}" for i in range(64)]
        if (
            not atlas.embedding_year.eq(2020).all()
            or not atlas.gauge.is_unique
            or not frame.gauge.isin(atlas.gauge).all()
        ):
            raise ValueError("Invalid descriptor year or catchment membership")
        by_gauge = atlas.set_index("gauge")
        for band in bands:
            frame[f"e_{band}"] = frame.gauge.map(by_gauge[band])
        temporary = features.with_suffix(".partial")
        frame.to_parquet(temporary, index=False)
        os.replace(temporary, features)
        runner.write_json(receipt, dict(inputs=inputs, sha256=runner.sha(features)))
        del frame
    jobs = json.loads((original / "jobs.json").read_text())
    # The legacy worker reserves this exact name for reuse of 2017 capacity fits.
    execution = [
        dict(job, id="held_Wurm_2021_alphaearth_2020") if job["id"] == "held_Wurm_2021" else job
        for job in jobs
    ]
    assignment = json.loads((original / "inner_folds.json").read_text())
    runner.write_json(OUT / "inner_folds.json", assignment)
    runner.write_json(runner.PREP / "inner_folds.json", assignment)
    runner.write_json(OUT / "jobs.json", execution)
    ident = runner.identity()
    manifest = OUT / "preparation.json"
    if manifest.exists() and json.loads(manifest.read_text())["identity"] != ident:
        raise ValueError("Run identity changed")
    runner.write_json(manifest, dict(identity=ident, reference_year=2020, jobs=len(jobs)))
    rows = []
    reference_columns = [
        "day",
        "gauge",
        "q_observed",
        "q_model",
        "high_water",
        "clean_verification",
    ]
    for index, (job, target) in enumerate(zip(jobs, execution, strict=True), 1):
        old = original / "jobs" / job["id"]
        runner.verify_manifest(old / "manifest.json")
        if job["id"] == "held_Geul_2021":
            runner.verify_manifest(GEUL / "manifest.json")
            prep = json.loads((GEUL.parents[1] / "preparation/audit.json").read_text())
            for p in (alpha, original_features):
                if prep["inputs"][str(p.relative_to(ROOT))] != inputs[str(p.relative_to(ROOT))]:
                    raise ValueError("Geul benchmark used different source inputs")
            new = GEUL
        else:
            new = OUT / "jobs" / target["id"]
            runner.write_json(
                OUT / "progress.json",
                dict(
                    status="running",
                    completed_jobs=index - 1,
                    total_jobs=len(jobs),
                    active_job=target["id"],
                ),
            )
            runner.worker(target)
        previous = pd.read_parquet(old / "predictions.parquet")
        current = pd.read_parquet(new / "predictions.parquet")
        pd.testing.assert_frame_equal(previous[reference_columns], current[reference_columns])
        for policy in runner.PLAN["policies"]:
            col = f"{policy}__H+A+E"
            previous[f"{col}_2017"] = previous[col]
            previous[f"{col}_2020"] = current[col]
        rows.append(previous)
        print(f"Paired {index}/{len(jobs)}: {job['id']}", flush=True)
    paired = pd.concat(rows, ignore_index=True)
    runner.assert_census(paired, source["test_rows"])
    names = ["q_model", "donor_fdc"]
    for policy in runner.PLAN["policies"]:
        names.extend([f"{policy}__H+A", f"{policy}__H+A+E_2017", f"{policy}__H+A+E_2020"])
    paired.to_parquet(OUT / "paired_predictions.parquet", index=False)
    metrics = []
    for regime, frame in paired.groupby("regime"):
        evaluated, _ = runner.evaluation(frame, names)
        metrics.extend(dict(regime=regime, **r) for r in evaluated)
    pd.DataFrame(metrics).drop(columns="per_gauge").to_csv(OUT / "pooled_metrics.csv", index=False)
    runner.write_json(
        OUT / "progress.json",
        dict(
            status="completed",
            completed_jobs=len(jobs),
            total_jobs=len(jobs),
            paired_rows=len(paired),
        ),
    )


if __name__ == "__main__":
    main()
