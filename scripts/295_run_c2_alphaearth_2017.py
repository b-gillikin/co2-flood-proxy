"""Fit the archived 2017 AlphaEarth vectors on the completed C2 design."""

import argparse
import fcntl
import importlib
import json
import subprocess
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

import numpy as np
import pandas as pd

c2 = importlib.import_module("294_run_c2_multiyear")
c1 = c2.c1
runner = c2.runner
ROOT = c2.ROOT
REFERENCE = c2.OUT
ORIGINAL = c1.pilot.FOLDS / "completion.json"
ARCHIVED_FEATURES = c1.pilot.BASELINE
OUT = REFERENCE.with_name("c2_alphaearth_2017_v1")
PREP = OUT / "preparation"
FEATURES = PREP / "features.parquet"
ARM = "C2+AlphaEarth2017"
ARMS = ("C2", "C2+AlphaEarth", ARM)
LABELS = ("C2", "C2+AlphaEarth 2020", "C2+AlphaEarth 2017")
JOBS = c2.JOBS
FITS_PER_FOLD = len(runner.PLAN["policies"]) * (
    len(runner.CANDIDATES) * runner.PLAN["inner_folds"] + len(runner.PLAN["seeds"])
)


def read(path):
    return json.loads(path.read_text())


def use_vintage_worker():
    runner.OUT = OUT
    runner.PREP = PREP
    runner.PLAN = dict(runner.PLAN, arms=(ARM,))
    runner.SLOTS = FITS_PER_FOLD
    runner.feature_columns = lambda frame, arm: c2.columns(frame, "C2+AlphaEarth")


def prepare():
    reference_review = REFERENCE / "completion_review.json"
    reference_predictions = REFERENCE / "paired_predictions.parquet"
    reference_preparation = REFERENCE / "preparation.json"
    reference_features = REFERENCE / "preparation/features.parquet"
    original = read(ORIGINAL)
    review = read(reference_review)
    preparation = read(reference_preparation)
    reference_identity = runner.identity()
    if (
        original["status"] != "completed"
        or review["status"] != "completed"
        or review["folds"] != len(JOBS)
        or review["paired_rows"] != preparation["expected_prediction_rows"]
        or read(REFERENCE / "jobs.json") != JOBS
        or reference_identity != preparation["identity"]
    ):
        raise ValueError("Completed C2 reference or its model design changed")
    inputs = {
        str(path.relative_to(ROOT)): runner.sha(path)
        for path in (
            Path(__file__),
            Path(c2.__file__),
            Path(c1.pilot.__file__),
            ORIGINAL,
            ARCHIVED_FEATURES,
            reference_review,
            reference_predictions,
            reference_preparation,
            c1.REVIEW,
            c1.SETTINGS,
        )
    } | reference_identity["sources"]
    archive_key = str(ARCHIVED_FEATURES.relative_to(ROOT))
    paired_key = str(reference_predictions.relative_to(ROOT))
    if (
        inputs[archive_key] != original["identity"]["sources"][archive_key]
        or inputs[paired_key] != review["paired_predictions_sha256"]
    ):
        raise ValueError("Archived AlphaEarth features or C2 predictions changed")

    PREP.mkdir(parents=True, exist_ok=True)
    audit = PREP / "audit.json"
    if audit.exists():
        saved = read(audit)
        if inputs != saved["inputs"] or runner.sha(FEATURES) != saved["features"]:
            raise ValueError("Prepared 2017 run inputs changed")
    else:
        runner.disk_check(ROOT, runner.PLAN["reserve_gib"], 2 * 2**30)
        bands = c1.pilot.ALPHA_COLUMNS
        archived = [f"e_{band}" for band in bands]
        vectors = (
            pd.read_parquet(ARCHIVED_FEATURES, columns=["gauge", *archived])
            .drop_duplicates()
            .set_index("gauge")
        )
        frame = pd.read_parquet(reference_features)
        if (
            not vectors.index.is_unique
            or set(vectors.index) != set(frame.gauge.unique())
            or not np.isfinite(vectors.to_numpy()).all()
        ):
            raise ValueError("2017 vectors do not cover the exact C2 gauge population")
        for band, old in zip(bands, archived, strict=True):
            frame[band] = frame.gauge.map(vectors[old]).astype(frame[band].dtype)
        c1.save_table(frame, FEATURES)
        runner.write_json(
            audit,
            dict(
                inputs=inputs,
                features=runner.sha(FEATURES),
                rows=len(frame),
                gauges=len(vectors),
                descriptor_year=2017,
                replaced_columns=bands,
            ),
        )

    assignment = read(REFERENCE / "inner_folds.json")
    runner.write_json(OUT / "jobs.json", JOBS)
    runner.write_json(OUT / "inner_folds.json", assignment)
    runner.write_json(PREP / "inner_folds.json", assignment)
    use_vintage_worker()
    runner.write_json(
        OUT / "preparation.json",
        dict(
            identity=runner.identity(),
            expected_prediction_rows=review["paired_rows"],
            arm=ARM,
            descriptor_year=2017,
        ),
    )


def consolidate(identity):
    reference_path = REFERENCE / "paired_predictions.parquet"
    inputs = read(PREP / "audit.json")["inputs"]
    for path in (reference_path, c1.REVIEW, c1.SETTINGS):
        if runner.sha(path) != inputs[str(path.relative_to(ROOT))]:
            raise ValueError(f"Review input changed during fitting: {path.name}")
    reference = pd.read_parquet(reference_path).set_index(c1.KEYS)
    predictions, caps = [], []
    for job in JOBS:
        folder = OUT / "jobs" / job["id"]
        if runner.verify_manifest(folder / "manifest.json")["identity"] != dict(identity, job=job):
            raise ValueError(f"Unexpected fit identity: {job['id']}")
        predictions.append(
            pd.read_parquet(folder / "predictions.parquet").assign(
                outer_job=job["id"].removesuffix("_c2")
            )
        )
        caps.append(dict(job=job["id"], **read(folder / "readout.json")["selected_fold_caps"]))
    fitted = pd.concat(predictions, ignore_index=True)
    runner.assert_census(fitted, len(reference))
    fitted = fitted.set_index(c1.KEYS)
    if not reference.index.is_unique or not fitted.index.difference(reference.index).empty:
        raise ValueError("2017 predictions do not use the exact C2 gauge-days")
    fitted = fitted.reindex(reference.index)
    matched = [column for column in c1.MATCH if column not in c1.KEYS]
    matched += ["source_role", "river_group", "test_year", "outer_job"]
    for frame in (reference, fitted):
        for column in ("high_water", "clean_verification"):
            frame[column] = frame[column].astype("boolean")
    pd.testing.assert_frame_equal(reference[matched], fitted[matched], check_exact=True)

    columns = [f"{policy}__{ARM}" for policy in runner.PLAN["policies"]]
    paired = reference.join(fitted[columns], validate="one_to_one").reset_index()
    path = OUT / "paired_predictions.parquet"
    c1.save_table(paired, path)
    reviewer = c1.load("c2_alphaearth_vintage_review", c1.REVIEW)
    estimates, ranges = reviewer.review(paired, read(c1.SETTINGS), labels=LABELS, features=ARMS)
    runner.write_json(
        OUT / "completion_review.json",
        dict(
            status="completed",
            folds=len(JOBS),
            paired_rows=len(paired),
            paired_predictions_sha256=runner.sha(path),
            point_estimates=estimates,
            paired_percentile_ranges=ranges,
            selected_fold_caps=caps,
        ),
    )


def fit(job):
    runner.disk_check(ROOT, runner.PLAN["reserve_gib"], 512 * 2**20)
    with (OUT / "logs" / f"{job['id']}.log").open("a") as log:
        subprocess.run(
            [sys.executable, "-u", str(Path(__file__).resolve()), "worker", "--job", job["id"]],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )


def run(workers):
    finished = []

    def progress(status, **details):
        runner.write_json(
            OUT / "progress.json",
            dict(
                status=status,
                total=len(JOBS),
                finished=finished,
                fits_per_fold=FITS_PER_FOLD,
                updated_utc=runner.utc(),
                **details,
            ),
        )

    try:
        progress("preparing")
        prepare()
        identity = read(OUT / "preparation.json")["identity"]
        (OUT / "logs").mkdir(exist_ok=True)
        pending = []
        for job in JOBS:
            manifest = OUT / "jobs" / job["id"] / "manifest.json"
            if manifest.exists() and read(manifest)["status"] == "completed":
                if runner.verify_manifest(manifest)["identity"] != dict(identity, job=job):
                    raise ValueError(f"Stale completed fold: {job['id']}")
                finished.append(job["id"])
            else:
                pending.append(job)

        remaining = iter(pending)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            active = {}
            while True:
                for job in (next(remaining, None) for _ in range(workers - len(active))):
                    if job is not None:
                        active[pool.submit(fit, job)] = job["id"]
                if not active:
                    break
                progress("running", active=list(active.values()), workers=len(active))
                done, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in done:
                    future.result()
                    finished.append(active.pop(future))

        progress("reviewing")
        consolidate(identity)
        progress("completed")
    except Exception as error:
        progress("failed", error=str(error))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "worker"))
    parser.add_argument("--workers", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--job", choices=[job["id"] for job in JOBS])
    args = parser.parse_args()
    if args.stage == "worker":
        if args.job is None:
            parser.error("worker requires --job")
        use_vintage_worker()
        runner.worker(next(job for job in JOBS if job["id"] == args.job))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "queue.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.stage == "prepare":
            prepare()
        else:
            run(args.workers)


if __name__ == "__main__":
    main()
