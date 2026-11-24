"""Run C2 and both satellite additions on the same folds and rows as C1."""

import argparse
import fcntl
import importlib
import json
import subprocess
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
c = importlib.import_module("293_acquire_c2_controls")
c1 = importlib.import_module("292_run_c1_multiyear")
runner = c1.runner
OUT = c.OUT
PREP = OUT / "preparation"
REFERENCE = c1.OUT
ARMS = ("C2", "C2+AlphaEarth", "C2+TESSERA")
JOBS = [dict(job, id=job["id"].removesuffix("_c1") + "_c2") for job in c1.JOBS]
runner.OUT = OUT
runner.PREP = PREP
runner.PLAN = dict(runner.PLAN, arms=ARMS)


def columns(frame, arm):
    return c1.pilot.arm_columns(frame, arm.replace("C2", "C1", 1)) + list(c.STATIC + c.STATE)


runner.feature_columns = columns


def join_controls(base, landscape, states):
    states = states.assign(day=states.source_day + pd.Timedelta(days=1))
    result = base.merge(
        landscape[["gauge", *c.STATIC]],
        on="gauge",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    if not result.pop("_merge").eq("both").all():
        raise ValueError("Missing C2 catchment records")
    result = result.merge(
        states[["gauge", "day", "source_day", *c.STATE]],
        on=["gauge", "day"],
        how="left",
        validate="one_to_one",
    )
    if not (result.day - result.source_day).eq(pd.Timedelta(days=1)).all():
        raise ValueError("Missing antecedent record or non-previous-UTC-day join")
    pd.testing.assert_frame_equal(result[base.columns], base, check_exact=True)
    return result.drop(columns="source_day")


def prepare():
    source_path = OUT / "source_audit.json"
    source_audit = json.loads(source_path.read_text())
    raw = [OUT / "inputs" / name for name in ("landscape.parquet", "antecedent_state.parquet")]
    if source_audit["status"] != "completed" or any(
        runner.sha(p) != source_audit["files"][p.name] for p in raw
    ):
        raise ValueError("Changed or incomplete C2 source data")
    c1_path = REFERENCE / "preparation/features.parquet"
    c1_audit = REFERENCE / "preparation/audit.json"
    c1_readout = REFERENCE / "completion_review.json"
    c1_paired = REFERENCE / "paired_predictions.parquet"
    reference = json.loads(c1_readout.read_text())
    if (
        runner.sha(c1_path) != json.loads(c1_audit.read_text())["features"]
        or reference["status"] != "completed"
        or runner.sha(c1_paired) != reference["paired_predictions_sha256"]
    ):
        raise ValueError("Changed C1 preparation or paired reference")
    inputs = [
        Path(__file__),
        Path(c.__file__),
        Path(c1.__file__),
        Path(c1.pilot.__file__),
        c1_path,
        c1_audit,
        c1_readout,
        c1_paired,
        source_path,
        *raw,
        c1.REVIEW,
        c1.SETTINGS,
        REFERENCE / "jobs.json",
        REFERENCE / "inner_folds.json",
    ]
    hashes = {str(path.relative_to(ROOT)): runner.sha(path) for path in inputs}
    path = PREP / "features.parquet"
    receipt = PREP / "audit.json"
    PREP.mkdir(parents=True, exist_ok=True)
    if receipt.exists():
        audit = json.loads(receipt.read_text())
        if hashes != audit["inputs"] or runner.sha(path) != audit["features"]:
            raise ValueError("Prepared C2 data or code changed")
    else:
        runner.disk_check(ROOT, runner.PLAN["reserve_gib"], 3 * 2**30)
        landscape, states = [pd.read_parquet(p) for p in raw]
        original = pd.read_parquet(c1_path)
        features = join_controls(original, landscape, states)
        missing = (
            features.assign(year=features.day.dt.year)
            .groupby(["source_role", "year"])[list(c.STATIC + c.STATE)]
            .agg(lambda col: int(col.isna().sum()))
        )
        c1.save_table(features, path)
        runner.write_json(
            receipt,
            dict(
                inputs=hashes,
                features=runner.sha(path),
                rows=len(features),
                gauges=features.gauge.nunique(),
                missing_by_role_year=missing.reset_index().to_dict(orient="records"),
            ),
        )
    assignment = json.loads((REFERENCE / "inner_folds.json").read_text())
    for path, value in (
        (OUT / "jobs.json", JOBS),
        (OUT / "inner_folds.json", assignment),
        (PREP / "inner_folds.json", assignment),
    ):
        runner.write_json(path, value)
    runner.write_json(
        OUT / "preparation.json",
        dict(
            identity=runner.identity(),
            expected_prediction_rows=reference["paired_rows"],
            arms=ARMS,
            added_controls=c.STATIC + c.STATE,
        ),
    )


def consolidate():
    source = pd.read_parquet(REFERENCE / "paired_predictions.parquet").set_index(c1.KEYS)
    fits, caps = [], []
    for job in JOBS:
        folder = OUT / "jobs" / job["id"]
        manifest = runner.verify_manifest(folder / "manifest.json")
        if manifest["identity"] != dict(**runner.identity(), job=job):
            raise ValueError("C2 output has an unexpected fit identity")
        data = pd.read_parquet(folder / "predictions.parquet")
        fits.append(data.assign(outer_job=job["id"].removesuffix("_c2")))
        readout = json.loads((folder / "readout.json").read_text())
        caps.append(dict(job=job["id"], **readout["selected_fold_caps"]))
    fits = pd.concat(fits, ignore_index=True)
    runner.assert_census(fits, len(source))
    fits = fits.set_index(c1.KEYS).reindex(source.index)
    cols = [x for x in c1.MATCH if x not in c1.KEYS] + ["outer_job"]
    for frame in (source, fits):
        for col in ("high_water", "clean_verification"):
            frame[col] = frame[col].astype("boolean")
    pd.testing.assert_frame_equal(source[cols], fits[cols], check_exact=True)
    added = [f"{policy}__{arm}" for policy in runner.PLAN["policies"] for arm in ARMS]
    paired = source.join(fits[added], validate="one_to_one").reset_index()
    path = OUT / "paired_predictions.parquet"
    c1.save_table(paired, path)
    review = c1.load("c2_review", c1.REVIEW)
    settings = json.loads(c1.SETTINGS.read_text())
    points, ranges = review.review(paired, settings, labels=ARMS, features=ARMS)
    for old, new in zip(c1.pilot.ARMS, ARMS, strict=True):
        p, r = review.review(
            paired, settings, labels=(old, new, "History baseline"), features=(old, new, "H")
        )
        points.extend(row for row in p if row["candidate"] == new and row["reference"] == old)
        ranges.extend(row for row in r if row["candidate"] == new and row["reference"] == old)
    runner.write_json(
        OUT / "completion_review.json",
        dict(
            status="completed",
            folds=len(JOBS),
            paired_rows=len(paired),
            paired_predictions_sha256=runner.sha(path),
            point_estimates=points,
            paired_percentile_ranges=ranges,
            selected_fold_caps=caps,
        ),
    )


def run(workers):
    progress = OUT / "progress.json"
    finished = []

    def record(status, **fields):
        runner.write_json(
            progress, dict(status=status, total=len(JOBS), finished=finished, **fields)
        )

    def fit(job):
        runner.disk_check(ROOT, runner.PLAN["reserve_gib"], 2 * 2**30)
        with (OUT / "logs" / (job["id"] + ".log")).open("a") as log:
            subprocess.run(
                [sys.executable, "-u", __file__, "worker", "--job", job["id"]],
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )
        return job["id"]

    try:
        record("preparing")
        if not (OUT / "source_audit.json").exists():
            record("acquiring")
            with (OUT / "acquisition.log").open("a") as log:
                subprocess.run(
                    [sys.executable, "-u", c.__file__],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
        record("preparing")
        prepare()
        (OUT / "logs").mkdir(exist_ok=True)
        ident = runner.identity()
        ordered = sorted(JOBS, key=lambda job: (job["held"] != "Wurm", job["year"]))
        for job in ordered:
            path = OUT / "jobs" / job["id"] / "manifest.json"
            if path.exists() and json.loads(path.read_text())["status"] == "completed":
                if runner.verify_manifest(path)["identity"] != dict(**ident, job=job):
                    raise ValueError("Cannot resume a different C2 fit identity")
                finished.append(job["id"])
        pending = iter(job for job in ordered if job["id"] not in finished)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            active = {
                pool.submit(fit, job): job["id"]
                for job in (next(pending, None) for _ in range(workers))
                if job is not None
            }
            while active:
                record("running", active=list(active.values()), workers=len(active))
                done, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in done:
                    finished.append(future.result())
                    del active[future]
                for job in (next(pending, None) for _ in done):
                    if job is not None:
                        active[pool.submit(fit, job)] = job["id"]
        record("reviewing")
        consolidate()
        record("completed")
    except Exception as exc:
        record("failed", error=str(exc))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["prepare", "run", "worker"])
    parser.add_argument("--workers", type=int, choices=[1, 2, 3], default=2)
    parser.add_argument("--job")
    args = parser.parse_args()
    if args.stage == "worker":
        runner.worker(next(job for job in JOBS if job["id"] == args.job))
        return
    OUT.mkdir(exist_ok=True)
    with (OUT / "queue.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.stage == "prepare":
            prepare()
        else:
            run(args.workers)


if __name__ == "__main__":
    main()
