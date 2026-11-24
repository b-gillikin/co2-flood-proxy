"""Fit 2020 TESSERA and compare with matched 2020 AlphaEarth on the C0 folds."""

import fcntl
import importlib.util
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/limburg_representation_extension_v1"
OUT = BASE / "satellite_c0_multiyear_2020"
VINTAGE = BASE / "alphaearth_vintage_c0"
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
    tessera = BASE / "tessera_census_2020/descriptors_2020.csv"
    paired_vintages = VINTAGE / "paired_predictions.parquet"
    vintage_review = VINTAGE / "completion_review.json"
    quality = BASE / "alphaearth_2020/quality_2020.json"
    audit = json.loads(quality.read_text())
    if (
        audit["status"] != "complete"
        or audit["year"] != 2020
        or runner.sha(tessera) != audit["tessera_csv_sha256"]
    ):
        raise ValueError("2020 TESSERA does not match its quality receipt")
    review = json.loads(vintage_review.read_text())
    if (
        review["status"] != "completed"
        or runner.sha(paired_vintages) != review["paired_predictions_sha256"]
    ):
        raise ValueError("2020 AlphaEarth predictions do not match the completion review")
    source = runner.verify_manifest(original / "completion.json")
    runner.OUT = OUT
    runner.PREP = OUT / "preparation"
    runner.PREP.mkdir(exist_ok=True)
    runner.PLAN = dict(runner.PLAN, arms=["H+A+T"])
    runner.SLOTS = len(runner.PLAN["policies"]) * (
        len(runner.CANDIDATES) * runner.PLAN["inner_folds"] + len(runner.PLAN["seeds"])
    )
    original_columns = runner.feature_columns
    bands = [f"tessera_{i:03d}" for i in range(128)]

    def tessera_columns(frame, arm):
        if arm != "H+A+T":
            raise ValueError(arm)
        return original_columns(frame, "H+A") + bands

    runner.feature_columns = tessera_columns
    features = runner.PREP / "features.parquet"
    receipt = runner.PREP / "audit.json"
    review_script = Path(__file__).with_name("288_review_alphaearth_vintages.py")
    settings_file = ROOT / "config/limburg_dise_repeatability_v1.json"
    inputs = {
        str(p.relative_to(ROOT)): runner.sha(p)
        for p in (
            original_features,
            tessera,
            quality,
            Path(__file__),
            original / "completion.json",
            paired_vintages,
            vintage_review,
            review_script,
            settings_file,
        )
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
        atlas = pd.read_csv(tessera, dtype={"gauge": str})
        if not atlas.gauge.is_unique or not frame.gauge.isin(atlas.gauge).all():
            raise ValueError("Invalid TESSERA catchment membership")
        descriptors = atlas.set_index("gauge")[bands]
        frame = frame.drop(columns=[c for c in frame if c.startswith("e_")])
        frame = frame.join(descriptors, on="gauge", validate="many_to_one")
        temporary = features.with_suffix(".partial")
        frame.to_parquet(temporary, index=False)
        os.replace(temporary, features)
        runner.write_json(receipt, dict(inputs=inputs, sha256=runner.sha(features)))
        del frame
    jobs = json.loads((original / "jobs.json").read_text())
    # The legacy worker reserves this exact name for reuse of 2017 capacity fits.
    execution = [
        dict(job, id="held_Wurm_2021_tessera_2020") if job["id"] == "held_Wurm_2021" else job
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
    prior = pd.read_parquet(paired_vintages)
    runner.assert_census(prior, source["test_rows"])
    for index, (job, target) in enumerate(zip(jobs, execution, strict=True), 1):
        old = original / "jobs" / job["id"]
        runner.verify_manifest(old / "manifest.json")
        if job["id"] == "held_Geul_2021":
            runner.verify_manifest(GEUL / "manifest.json")
            prep = json.loads((GEUL.parents[1] / "preparation/audit.json").read_text())
            for p in (tessera, original_features):
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
        archived = pd.read_parquet(old / "predictions.parquet")
        previous = prior.loc[prior.outer_job.eq(job["id"])].reset_index(drop=True).copy()
        current = pd.read_parquet(new / "predictions.parquet")
        for other in (archived, current):
            left = previous[reference_columns].copy()
            right = other[reference_columns].reset_index(drop=True).copy()
            for data in (left, right):
                data["clean_verification"] = data.clean_verification.astype("boolean")
            pd.testing.assert_frame_equal(left, right, check_exact=True)
        for policy in runner.PLAN["policies"]:
            baseline = f"{policy}__H+A"
            pd.testing.assert_series_equal(previous[baseline], archived[baseline], check_exact=True)
            previous[f"{policy}__H+A+T_2020"] = current[f"{policy}__H+A+T"]
        rows.append(previous)
        print(f"Paired {index}/{len(jobs)}: {job['id']}", flush=True)
    paired = pd.concat(rows, ignore_index=True)
    runner.assert_census(paired, source["test_rows"])
    names = ["q_model", "donor_fdc"]
    for policy in runner.PLAN["policies"]:
        names.extend([f"{policy}__H+A", f"{policy}__H+A+E_2020", f"{policy}__H+A+T_2020"])
    paired.to_parquet(OUT / "paired_predictions.parquet", index=False)
    metrics = []
    for regime, frame in paired.groupby("regime"):
        evaluated, _ = runner.evaluation(frame, names)
        metrics.extend(dict(regime=regime, **r) for r in evaluated)
    pd.DataFrame(metrics).drop(columns="per_gauge").to_csv(OUT / "pooled_metrics.csv", index=False)
    spec = importlib.util.spec_from_file_location("paired_review", review_script)
    paired_review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paired_review)
    points, ranges = paired_review.review(
        paired,
        json.loads(settings_file.read_text()),
        labels=("C0", "AlphaEarth 2020", "TESSERA 2020"),
        features=("H+A", "H+A+E_2020", "H+A+T_2020"),
    )
    runner.write_json(
        OUT / "completion_review.json",
        dict(
            status="completed",
            inputs=inputs,
            paired_rows=len(paired),
            paired_predictions_sha256=runner.sha(OUT / "paired_predictions.parquet"),
            point_estimates=points,
            paired_percentile_ranges=ranges,
        ),
    )
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
