"""Run the declared C1 sensitivity on all original folds and review paired results."""

import argparse
import fcntl
import importlib.util
import json
import os
import subprocess
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pilot = load("c1_pilot", ROOT / "scripts/291_prepare_c1_benchmark.py")
runner = load("dise_worker", pilot.RUNNER)
OUT = pilot.BASE / "c1_held_multiyear_v1"
PREP = OUT / "preparation"
REFERENCE = pilot.BASE / "satellite_c0_multiyear_2020"
PILOT = pilot.OUT / "fit/jobs/held_Wurm_2021_c1_held"
REVIEW = ROOT / "scripts/288_review_alphaearth_vintages.py"
SETTINGS = ROOT / "config/limburg_dise_repeatability_v1.json"
KEYS = ["regime", "gauge", "day"]
MATCH = [*KEYS, "q_observed", "q_model", "p99_reference", "high_water", "clean_verification"]
JOBS = json.loads((pilot.FOLDS / "jobs.json").read_text())
JOBS = [dict(job, id=f"{job['id']}_c1") for job in JOBS]
REFERENCE_FEATURES = ("H+A", "H+A+E_2020", "H+A+T_2020")
runner.OUT = OUT
runner.PREP = PREP
runner.PLAN = dict(runner.PLAN, arms=pilot.ARMS)
runner.feature_columns = pilot.arm_columns
runner.SLOTS = (
    len(pilot.ARMS)
    * len(runner.PLAN["policies"])
    * (len(runner.CANDIDATES) * runner.PLAN["inner_folds"] + len(runner.PLAN["seeds"]))
)


def save_table(frame, path):
    temporary = path.with_suffix(".partial")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def extended_controls(audit):
    """Compute the same calendar-year summaries as the pilot, through 2024."""
    sources = [ROOT / p for p in audit["input_sha256"] if "/local_daily_" in p]
    sources.append(ROOT / "results/limburg_dise_v2/regional_inputs_resolved_v1/weather.parquet")
    paths = [p for p in sources if p.stem != "local_daily_2025"]
    weather = pd.concat(
        [
            pd.read_parquet(
                p,
                columns=["gauge", "day", "total_precipitation_sum", "temperature_2m"],
                filters=[("day", "<", pd.Timestamp("2025-01-01", tz="UTC"))],
            )
            for p in paths
        ],
        ignore_index=True,
    )
    rain = weather.total_precipitation_sum.mul(1000)
    month = weather.day.dt.month
    groups = weather.assign(
        weather_reference_year=weather.day.dt.year,
        rain_mm=rain,
        wet_day=rain.ge(1),
        wet_day_rain_mm=rain.where(rain.ge(1)),
        oct_mar_rain_mm=rain.where(month.isin([10, 11, 12, 1, 2, 3]), 0),
        djf_temp_k=weather.temperature_2m.where(month.isin([12, 1, 2])),
        jja_temp_k=weather.temperature_2m.where(month.isin([6, 7, 8])),
    ).groupby(["gauge", "weather_reference_year"])
    c = groups.agg(
        c1_wet_day_fraction=("wet_day", "mean"),
        c1_wet_day_intensity_mm=("wet_day_rain_mm", "mean"),
        c1_djf_mean_temp_k=("djf_temp_k", "mean"),
        c1_jja_mean_temp_k=("jja_temp_k", "mean"),
    )
    c["c1_oct_mar_precip_share"] = groups.oct_mar_rain_mm.sum() / groups.rain_mm.sum()
    c = c.reset_index()
    c["year"] = c.weather_reference_year + 1
    old = pd.read_parquet(pilot.OUT / "conventional_by_gauge_year.parquet")
    c = c.join(
        old.drop_duplicates("gauge").set_index("gauge")[["c1_perimeter_km", "c1_compactness"]],
        on="gauge",
        validate="many_to_one",
    )
    c = c[old.columns].sort_values(["gauge", "year"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(
        c.loc[c.year.le(2021)].reset_index(drop=True), old, check_exact=True
    )
    if c.groupby("year").size().to_dict() != dict.fromkeys(range(2018, 2026), 394):
        raise ValueError("Incomplete expanded C1 control calendar")
    return c, paths


def prepare():
    PREP.mkdir(parents=True, exist_ok=True)
    core = json.loads(pilot.AUDIT.read_text())["input_sha256"]
    audit = {"input_sha256": core}
    checked = {
        p: h for p, h in core.items() if "/local_daily_" in p or p.endswith("/weather.parquet")
    }
    checked.update(
        {
            str(p.relative_to(ROOT)): core[str(p.relative_to(ROOT))]
            for p in (pilot.BASELINE, pilot.ALPHA, pilot.TESSERA)
        }
    )
    pilot.verify(pilot.AUDIT, checked)
    fold_preparation = json.loads((pilot.OUT / "preparation.json").read_text())
    old_controls = pilot.OUT / "conventional_by_gauge_year.parquet"
    if runner.sha(old_controls) != fold_preparation["controls_sha256"]:
        raise ValueError("Changed pilot controls")
    pilot_manifest = runner.verify_manifest(PILOT / "manifest.json")
    pilot.verify(PILOT, pilot_manifest["identity"]["sources"])
    reference = json.loads((REFERENCE / "completion_review.json").read_text())
    if (
        reference["status"] != "completed"
        or runner.sha(REFERENCE / "paired_predictions.parquet")
        != reference["paired_predictions_sha256"]
    ):
        raise ValueError("Changed C0 paired reference")
    inputs = {
        str(p.relative_to(ROOT)): runner.sha(p)
        for p in (
            Path(__file__),
            Path(pilot.__file__),
            pilot.AUDIT,
            old_controls,
            pilot.FOLDS / "inner_folds.json",
            pilot.FOLDS / "jobs.json",
            PILOT / "manifest.json",
            REFERENCE / "completion_review.json",
            REVIEW,
            SETTINGS,
        )
    } | checked
    controls_file = OUT / "conventional_by_gauge_year.parquet"
    fit_file = PREP / "features.parquet"
    receipt = PREP / "audit.json"
    if receipt.exists():
        if json.loads(receipt.read_text()) != dict(
            inputs=inputs, controls=runner.sha(controls_file), features=runner.sha(fit_file)
        ):
            raise ValueError("Prepared C1 data or code changed")
    else:
        runner.disk_check(ROOT, runner.PLAN["reserve_gib"], 3 * 2**30)
        controls, _ = extended_controls(audit)
        save_table(controls, controls_file)
        pilot.OUT = OUT
        frame = pd.read_parquet(pilot.BASELINE)
        frame = pilot.join_inputs(frame.drop(columns=[c for c in frame if c.startswith("e_")]))
        save_table(frame, fit_file)
        runner.write_json(
            receipt,
            dict(inputs=inputs, controls=runner.sha(controls_file), features=runner.sha(fit_file)),
        )
    assignment = json.loads((pilot.FOLDS / "inner_folds.json").read_text())
    for path, obj in (
        (OUT / "jobs.json", JOBS),
        (OUT / "inner_folds.json", assignment),
        (PREP / "inner_folds.json", assignment),
    ):
        runner.write_json(path, obj)
    runner.write_json(
        OUT / "preparation.json",
        dict(identity=runner.identity(), expected_prediction_rows=reference["paired_rows"]),
    )


def consolidate():
    source = pd.read_parquet(REFERENCE / "paired_predictions.parquet")
    fit_parts = []
    caps = []
    for job in JOBS:
        folder = PILOT if job["id"] == "held_Wurm_2021_c1" else OUT / "jobs" / job["id"]
        runner.verify_manifest(folder / "manifest.json")
        frame = pd.read_parquet(folder / "predictions.parquet")
        frame["outer_job"] = job["id"].removesuffix("_c1")
        fit_parts.append(frame)
        readout = json.loads((folder / "readout.json").read_text())
        caps.append(dict(job=job["id"], **readout["selected_fold_caps"]))
    fit = pd.concat(fit_parts, ignore_index=True)
    runner.assert_census(fit, len(source))
    source = source.set_index(KEYS)
    fit = fit.set_index(KEYS).reindex(source.index)
    cols = [c for c in MATCH if c not in KEYS] + ["outer_job"]
    for f in (source, fit):
        for col in ("high_water", "clean_verification"):
            f[col] = f[col].astype("boolean")
    pd.testing.assert_frame_equal(source[cols], fit[cols], check_exact=True)
    added = [f"{policy}__{arm}" for policy in runner.PLAN["policies"] for arm in pilot.ARMS]
    paired = source.join(fit[added], validate="one_to_one").reset_index()
    save_table(paired, OUT / "paired_predictions.parquet")
    reviewer = load("dise_review", REVIEW)
    settings = json.loads(SETTINGS.read_text())
    estimates, intervals = reviewer.review(paired, settings, labels=pilot.ARMS, features=pilot.ARMS)
    for c0, c1 in zip(REFERENCE_FEATURES, pilot.ARMS, strict=True):
        # Retain the original C0 arm as the matched reference for each C1 arm.
        ref, interval = reviewer.review(
            paired, settings, labels=(c0, c1, "History baseline"), features=(c0, c1, "H")
        )
        estimates.extend(r for r in ref if r["candidate"] == c1 and r["reference"] == c0)
        intervals.extend(r for r in interval if r["candidate"] == c1 and r["reference"] == c0)
    runner.write_json(
        OUT / "completion_review.json",
        dict(
            status="completed",
            folds=len(JOBS),
            paired_rows=len(paired),
            paired_predictions_sha256=runner.sha(OUT / "paired_predictions.parquet"),
            point_estimates=estimates,
            paired_percentile_ranges=intervals,
            selected_fold_caps=caps,
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["prepare", "run", "worker"])
    parser.add_argument("--job")
    args = parser.parse_args()
    if args.stage == "worker":
        runner.worker(next(job for job in JOBS if job["id"] == args.job))
        return
    OUT.mkdir(exist_ok=True)
    with (OUT / "queue.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prepare()
        if args.stage == "prepare":
            return
        log_dir = OUT / "logs"
        log_dir.mkdir(exist_ok=True)
        ordered = sorted(JOBS, key=lambda j: (j["held"] != "Wurm", j["year"]))
        workers = 2

        def run_job(job):
            runner.disk_check(ROOT, runner.PLAN["reserve_gib"], 2 * 2**30)
            with (log_dir / f"{job['id']}.log").open("a") as log:
                subprocess.run(
                    [sys.executable, "-u", __file__, "worker", "--job", job["id"]],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
            return job["id"]

        completed = ["held_Wurm_2021_c1"]
        identity = runner.identity()
        for job in ordered:
            manifest = OUT / "jobs" / job["id"] / "manifest.json"
            if manifest.exists() and json.loads(manifest.read_text())["status"] == "completed":
                if runner.verify_manifest(manifest)["identity"] != dict(**identity, job=job):
                    raise ValueError(f"Changed run identity at {manifest}")
                completed.append(job["id"])
        progress = OUT / "progress.json"
        try:
            pending = iter(job for job in ordered if job["id"] not in completed)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                active = {
                    pool.submit(run_job, job): job["id"]
                    for job in (next(pending, None) for _ in range(workers))
                    if job is not None
                }
                while active:
                    runner.write_json(
                        progress,
                        dict(
                            status="running",
                            finished=completed,
                            total=len(JOBS),
                            active=list(active.values()),
                            workers=len(active),
                        ),
                    )
                    done, _ = wait(active, return_when=FIRST_COMPLETED)
                    for future in done:
                        job_id = future.result()
                        del active[future]
                        completed.append(job_id)
                        print(f"{len(completed)}/{len(JOBS)} complete: {job_id}", flush=True)
                    for job in (next(pending, None) for _ in done):
                        if job is not None:
                            active[pool.submit(run_job, job)] = job["id"]
            runner.write_json(
                progress, dict(status="reviewing", finished=completed, total=len(JOBS))
            )
            consolidate()
        except Exception as exc:
            runner.write_json(
                progress, dict(status="failed", finished=completed, total=len(JOBS), error=str(exc))
            )
            raise
        runner.write_json(progress, dict(status="completed", finished=completed, total=len(JOBS)))


if __name__ == "__main__":
    main()
