"""Run one DISE held-river benchmark using the existing C0 controls and 2020 descriptors."""

import importlib.util
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/limburg_representation_extension_v1"
OUT = BASE / "satellite_c0_benchmark_2020"
JOB_ID = "held_Geul_2021"


def main():
    spec = importlib.util.spec_from_file_location(
        "dise_multiyear_runner", ROOT / "scripts/276_run_dise_multiyear.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    original = runner.OUT
    prep = runner.PREP
    OUT.mkdir(exist_ok=True)
    runner.OUT = OUT
    runner.PREP = OUT / "preparation"
    runner.PREP.mkdir(exist_ok=True)
    runner.PLAN = dict(runner.PLAN, arms=["H+A", "H+A+E", "H+A+T"])
    runner.SLOTS = (
        len(runner.PLAN["policies"])
        * len(runner.PLAN["arms"])
        * (len(runner.CANDIDATES) * runner.PLAN["inner_folds"] + len(runner.PLAN["seeds"]))
    )
    existing_columns = runner.feature_columns

    def columns(frame, arm):
        if arm == "H+A+T":
            return existing_columns(frame, "H+A") + [f"tessera_{i:03d}" for i in range(128)]
        return existing_columns(frame, arm)

    runner.feature_columns = columns
    paths = [
        prep / "features.parquet",
        BASE / "alphaearth_2020/descriptors_2020.parquet",
        BASE / "tessera_census_2020/descriptors_2020.csv",
        BASE / "alphaearth_2020/quality_2020.json",
        Path(__file__),
    ]
    hashes = {str(path.relative_to(ROOT)): runner.sha(path) for path in paths}
    quality = json.loads(paths[3].read_text())
    if (
        quality["status"] != "complete"
        or quality["year"] != 2020
        or any(
            runner.sha(path) != quality[key]
            for path, key in zip(
                paths[1:3], ["alphaearth_parquet_sha256", "tessera_csv_sha256"], strict=True
            )
        )
    ):
        raise ValueError("Satellite input hashes differ from the completed 2020 audit")
    prepared = runner.PREP / "features.parquet"
    audit = runner.PREP / "audit.json"
    if prepared.exists():
        if json.loads(audit.read_text()) != dict(inputs=hashes, sha256=runner.sha(prepared)):
            raise ValueError("Prepared benchmark inputs changed")
    else:
        runner.disk_check(ROOT, runner.PLAN["reserve_gib"], 2 * 2**30)
        frame = pd.read_parquet(paths[0])
        frame = frame.drop(columns=[c for c in frame if c.startswith("e_")])
        alpha = pd.read_parquet(paths[1])
        bands = [f"A{i:02d}" for i in range(64)]
        alpha = alpha[["gauge", *bands]].rename(columns={band: f"e_{band}" for band in bands})
        tessera = pd.read_csv(paths[2], dtype={"gauge": str})
        tessera = tessera[["gauge", *[f"tessera_{i:03d}" for i in range(128)]]]
        for table in (alpha, tessera):
            if not table.gauge.is_unique or not frame.gauge.isin(table.gauge).all():
                raise ValueError("A model input gauge is missing or duplicated")
            frame = frame.merge(table, on="gauge", validate="many_to_one", sort=False)
        temporary = prepared.with_suffix(".partial")
        frame.to_parquet(temporary, index=False)
        os.replace(temporary, prepared)
        runner.write_json(audit, dict(inputs=hashes, sha256=runner.sha(prepared)))
        del frame
    folds = json.loads((original / "inner_folds.json").read_text())
    jobs = json.loads((original / "jobs.json").read_text())
    job = next(job for job in jobs if job["id"] == JOB_ID)
    runner.write_json(runner.PREP / "inner_folds.json", folds)
    runner.write_json(OUT / "inner_folds.json", folds)
    runner.write_json(OUT / "jobs.json", [job])
    ident = runner.identity()
    manifest = OUT / "preparation.json"
    if manifest.exists() and json.loads(manifest.read_text())["identity"] != ident:
        raise ValueError("Benchmark identity changed")
    runner.write_json(
        manifest,
        {
            "identity": ident,
            "purpose": "one exploratory held-river benchmark using C0",
            "arms": runner.PLAN["arms"],
            "job": job,
            "logical_fits": runner.SLOTS,
            "conventional_attribute_vintage": "existing C0; includes 2017 land-cover fractions",
        },
    )
    print(f"Starting {JOB_ID}: {runner.SLOTS} fits", flush=True)
    runner.worker(job)


if __name__ == "__main__":
    main()
