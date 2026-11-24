"""Prepare, probe capacity, or explicitly run the held-data C1 benchmark."""

import argparse
import fcntl
import importlib.util
import json
import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.dise import CANDIDATES, feature_columns
from src.dise_corrected import fit_candidate
from src.dise_multiyear import masks
from src.dise_regional import inner_masks
from src.geoglows_experiment import disk_check, sha, write_json

BASE = ROOT / "results/limburg_representation_extension_v1"
OUT = BASE / "c1_held_benchmark_v1"
BASELINE = ROOT / "results/limburg_dise_regional_benchmark_v1/preparation/features.parquet"
FOLDS = ROOT / "results/limburg_dise_multiyear_v1"
SOURCE = BASE / "satellite_c0_multiyear_2020/jobs/held_Wurm_2021_tessera_2020"
AUDIT = BASE / "c1_held_input_audit.json"
ALPHA = BASE / "alphaearth_2020/descriptors_2020.parquet"
TESSERA = BASE / "tessera_census_2020/descriptors_2020.csv"
RUNNER = ROOT / "scripts/276_run_dise_multiyear.py"
CONFIG = ROOT / "config/limburg_dise_multiyear_v1.json"
PLAN = json.loads(CONFIG.read_text())
YEARS = [2018, 2019, 2020, 2021]
ARMS = ("C1", "C1+AlphaEarth", "C1+TESSERA")
EXTRAS = (
    "c1_wet_day_fraction",
    "c1_wet_day_intensity_mm",
    "c1_oct_mar_precip_share",
    "c1_djf_mean_temp_k",
    "c1_jja_mean_temp_k",
    "c1_perimeter_km",
    "c1_compactness",
)
ALPHA_COLUMNS = [f"A{i:02d}" for i in range(64)]
TESSERA_COLUMNS = [f"tessera_{i:03d}" for i in range(128)]
LABELS = ["gauge", "day", "river_group", "source_role", "q_observed", "q_model"]
PROBE_LIMIT = 4500


def candidate_selection():
    """Choose the diagnostic using the archived validation receipts only."""
    selected = json.loads((SOURCE / "selected.json").read_text())["native_rmse__H+A+T"]
    tuning = pd.read_csv(SOURCE / "tuning.csv")
    capped = tuning.loc[
        tuning.policy.eq("native_rmse")
        & tuning.tree_cap_hit
        & tuning.candidate_index.eq(selected["candidate_index"])
    ]
    if len(capped) != 1:
        raise ValueError("Expected one previously capped selected Wurm validation fit")
    return {"candidate_index": selected["candidate_index"], "inner_fold": int(capped.fold.iloc[0])}


def prepare_controls(audit):
    columns = ["gauge", "day", "total_precipitation_sum", "temperature_2m"]
    paths = [
        ROOT / p
        for p in audit["input_sha256"]
        if "/local_daily_" in p and int(Path(p).stem.rsplit("_", 1)[1]) < 2021
    ]
    paths.append(ROOT / "results/limburg_dise_v2/regional_inputs_resolved_v1/weather.parquet")
    weather = pd.concat(
        [
            pd.read_parquet(
                p, columns=columns, filters=[("day", "<", pd.Timestamp("2021-01-01", tz="UTC"))]
            )
            for p in paths
        ]
    )
    weather = weather.reset_index(drop=True)
    rain = weather.total_precipitation_sum.mul(1000)
    month = weather.day.dt.month
    grouped = weather.assign(
        weather_reference_year=weather.day.dt.year,
        rain_mm=rain,
        wet_day=rain.ge(1),
        wet_day_rain_mm=rain.where(rain.ge(1)),
        oct_mar_rain_mm=rain.where(month.isin([10, 11, 12, 1, 2, 3]), 0),
        djf_temp_k=weather.temperature_2m.where(month.isin([12, 1, 2])),
        jja_temp_k=weather.temperature_2m.where(month.isin([6, 7, 8])),
    ).groupby(["gauge", "weather_reference_year"])
    controls = grouped.agg(
        c1_wet_day_fraction=("wet_day", "mean"),
        c1_wet_day_intensity_mm=("wet_day_rain_mm", "mean"),
        c1_djf_mean_temp_k=("djf_temp_k", "mean"),
        c1_jja_mean_temp_k=("jja_temp_k", "mean"),
    )
    controls["c1_oct_mar_precip_share"] = grouped.oct_mar_rain_mm.sum() / grouped.rain_mm.sum()
    controls = controls.reset_index()
    controls["year"] = controls.weather_reference_year + 1
    # Perimeter was checked in the held-input audit. Recalculate from the same geometry.
    import geopandas as gpd

    polygons = gpd.read_file(BASE / "catchments.gpkg").set_index("gauge").geometry
    controls["c1_perimeter_km"] = controls.gauge.map(polygons.length / 1000)
    controls["c1_compactness"] = controls.gauge.map(
        4 * math.pi * polygons.area / polygons.length.pow(2)
    )
    if (
        len(controls) != len(polygons) * len(YEARS)
        or set(controls.year) != set(YEARS)
        or controls[list(EXTRAS)].isna().any().any()
    ):
        raise ValueError("Incomplete prior-year conventional controls")
    return controls.sort_values(["gauge", "year"]).reset_index(drop=True), paths


def join_inputs(frame):
    controls = pd.read_parquet(OUT / "conventional_by_gauge_year.parquet").set_index(
        ["gauge", "year"]
    )
    alpha = pd.read_parquet(ALPHA, columns=["gauge", *ALPHA_COLUMNS]).set_index("gauge")
    tessera = pd.read_csv(TESSERA, usecols=["gauge", *TESSERA_COLUMNS]).set_index("gauge")
    model_frame = frame.assign(year=frame.day.dt.year).join(
        controls, on=["gauge", "year"], validate="many_to_one"
    )
    model_frame = model_frame.join(alpha, on="gauge", validate="many_to_one").join(
        tessera, on="gauge", validate="many_to_one"
    )
    if (
        not model_frame.weather_reference_year.eq(model_frame.year - 1).all()
        or model_frame[[*EXTRAS, *ALPHA_COLUMNS, *TESSERA_COLUMNS]].isna().any().any()
    ):
        raise ValueError("Join changed coverage or violated the previous-calendar-year rule")
    return model_frame.drop(columns=["year", "weather_reference_year"])


def arm_columns(frame, arm):
    extras = {"C1": [], "C1+AlphaEarth": ALPHA_COLUMNS, "C1+TESSERA": TESSERA_COLUMNS}
    return feature_columns(frame, "H+A") + list(EXTRAS) + extras[arm]


def verify(path, files):
    for rel, digest in files.items():
        if sha(ROOT / rel) != digest:
            raise ValueError(f"{path}: changed input {rel}")


def prepare():
    audit = json.loads(AUDIT.read_text())
    controls, weather = prepare_controls(audit)
    for p in [BASELINE, BASE / "catchments.gpkg", ALPHA, TESSERA, *weather]:
        rel = str(p.relative_to(ROOT))
        verify(AUDIT, {rel: audit["input_sha256"][rel]})
    selection = candidate_selection()
    assignment = json.loads((FOLDS / "inner_folds.json").read_text())
    original_job = next(
        j for j in json.loads((FOLDS / "jobs.json").read_text()) if j["id"] == "held_Wurm_2021"
    )
    job = dict(original_job, id="held_Wurm_2021_c1_held")
    labels = pd.read_parquet(
        BASELINE, columns=LABELS, filters=[("day", "<", pd.Timestamp("2022-01-01", tz="UTC"))]
    )
    train, validation, test, _ = masks(labels, job, PLAN["external_test_years"])
    inner_counts = []
    for fold in range(PLAN["inner_folds"]):
        it, iv = inner_masks(labels, train, validation, assignment, fold)
        inner_counts.append(dict(train_rows=int(it.sum()), validation_rows=int(iv.sum())))
    if labels.loc[test, ["gauge", "day"]].duplicated().any():
        raise ValueError("Duplicate eligible outer gauge-days")
    files = [
        AUDIT,
        BASELINE,
        ALPHA,
        TESSERA,
        BASE / "catchments.gpkg",
        *weather,
        CONFIG,
        RUNNER,
        Path(__file__),
        FOLDS / "inner_folds.json",
        FOLDS / "jobs.json",
        SOURCE / "tuning.csv",
        SOURCE / "selected.json",
        *[
            ROOT / f"src/{name}.py"
            for name in (
                "dise",
                "dise_corrected",
                "dise_multiyear",
                "dise_regional",
                "dise_capacity",
                "geoglows_experiment",
            )
        ],
    ]
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in files}
    receipt = OUT / "preparation.json"
    sidecar = OUT / "conventional_by_gauge_year.parquet"
    if receipt.exists():
        previous = json.loads(receipt.read_text())
        if previous["inputs"] != inputs or previous["controls_sha256"] != sha(sidecar):
            raise ValueError(
                "Prepared data or code changed. Preserve the run and version the new inputs."
            )
        return previous
    temporary = sidecar.with_suffix(".partial")
    controls.to_parquet(temporary, index=False)
    os.replace(temporary, sidecar)
    record = dict(
        status="prepared",
        job=job,
        arms=ARMS,
        added_controls=EXTRAS,
        inputs=inputs,
        controls_sha256=sha(sidecar),
        control_rows=len(controls),
        original_assignment_sha256=sha(FOLDS / "inner_folds.json"),
        outer_train_rows=int(train.sum()),
        outer_validation_rows=int(validation.sum()),
        outer_test_rows=int(test.sum()),
        inner_fold_sizes=inner_counts,
        probe=selection,
        base_limit=PLAN["tree_limit"],
        probe_limit=PROBE_LIMIT,
    )
    write_json(receipt, record)
    return record


def probe(preparation):
    receipt = OUT / "capacity_probe.json"
    if receipt.exists():
        data = json.loads(receipt.read_text())
        if data["preparation_sha256"] != sha(OUT / "preparation.json"):
            raise ValueError("Existing capacity probe belongs to another preparation")
        return data
    frame = pd.read_parquet(
        BASELINE,
        filters=[
            ("day", "<", pd.Timestamp("2021-01-01", tz="UTC")),
            ("source_role", "!=", "reserved_external"),
            ("river_group", "!=", "Wurm"),
        ],
    )
    frame = join_inputs(frame.drop(columns=[c for c in frame if c.startswith("e_")]))
    eligible = np.isfinite(frame.q_observed) & np.isfinite(frame.q_model)
    assignment = json.loads((FOLDS / "inner_folds.json").read_text())
    fold = preparation["probe"]["inner_fold"]
    train, val = inner_masks(
        frame,
        eligible & frame.day.dt.year.lt(2020),
        eligible & frame.day.dt.year.eq(2020),
        assignment,
        fold,
    )
    size = preparation["inner_fold_sizes"][fold]
    if int(train.sum()) != size["train_rows"] or int(val.sum()) != size["validation_rows"]:
        raise ValueError("Capacity probe disagrees with prepared inner validation census")
    fit, validation = frame.loc[train], frame.loc[val]
    cap = preparation["base_limit"]

    def fit_arm(arm):
        model, _, record = fit_candidate(
            fit,
            validation,
            arm_columns(frame, arm),
            CANDIDATES[preparation["probe"]["candidate_index"]],
            "native_rmse",
            PLAN["seeds"][0],
            PROBE_LIMIT,
        )
        curve = model.evals_result()["validation_0"]["native_rmse"]
        best_through_cap = min(curve[:cap])
        return dict(
            arm=arm,
            **record,
            fitted_rounds=len(curve),
            best_round=record["best_iteration"] + 1,
            best_rmse_through_3000=best_through_cap,
            best_rmse_in_probe=min(curve),
            gain_beyond_3000=best_through_cap - min(curve),
            capped_at_probe_limit=len(curve) == PROBE_LIMIT,
        )

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(fit_arm, ARMS))
    budget = PROBE_LIMIT if any(r["best_round"] > cap for r in results) else cap
    result = dict(
        status="validation_probe_complete",
        preparation_sha256=sha(OUT / "preparation.json"),
        probe=preparation["probe"],
        train_rows=int(train.sum()),
        validation_rows=int(val.sum()),
        recommended_shared_limit=budget,
        arm_results=results,
        outer_scored=False,
        scope="One stress candidate and inner split across all ready arms. All candidates and folds remain scheduled for the benchmark.",
    )
    write_json(receipt, result)
    return result


def run_fold(preparation):
    capacity = json.loads((OUT / "capacity_probe.json").read_text())
    if capacity["preparation_sha256"] != sha(OUT / "preparation.json"):
        raise ValueError("Capacity probe does not match the prepared data")
    spec = importlib.util.spec_from_file_location("dise_multiyear_runner", RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.OUT = OUT / "fit"
    runner.PREP = runner.OUT / "preparation"
    runner.PREP.mkdir(parents=True, exist_ok=True)
    runner.PLAN = dict(PLAN, arms=ARMS, tree_limit=capacity["recommended_shared_limit"])
    runner.SLOTS = (
        len(ARMS)
        * len(PLAN["policies"])
        * (len(CANDIDATES) * PLAN["inner_folds"] + len(PLAN["seeds"]))
    )
    runner.feature_columns = arm_columns
    fit_frame = runner.PREP / "features.parquet"
    fit_receipt = runner.PREP / "audit.json"
    identity = dict(
        preparation=sha(OUT / "preparation.json"),
        probe=sha(OUT / "capacity_probe.json"),
        tree_limit=runner.PLAN["tree_limit"],
    )
    if fit_receipt.exists():
        if json.loads(fit_receipt.read_text()) != dict(identity, sha256=sha(fit_frame)):
            raise ValueError("Prepared fit matrix identity changed")
    else:
        disk_check(ROOT, PLAN["reserve_gib"], 2 * 2**30)
        frame = pd.read_parquet(
            BASELINE, filters=[("day", "<", pd.Timestamp("2022-01-01", tz="UTC"))]
        )
        frame = join_inputs(frame.drop(columns=[c for c in frame if c.startswith("e_")]))
        temporary = fit_frame.with_suffix(".partial")
        frame.to_parquet(temporary, index=False)
        os.replace(temporary, fit_frame)
        write_json(fit_receipt, dict(identity, sha256=sha(fit_frame)))
    assignment = json.loads((FOLDS / "inner_folds.json").read_text())
    write_json(runner.PREP / "inner_folds.json", assignment)
    write_json(runner.OUT / "inner_folds.json", assignment)
    write_json(runner.OUT / "jobs.json", [preparation["job"]])
    write_json(runner.OUT / "preparation.json", dict(identity=runner.identity(), **identity))
    runner.worker(preparation["job"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "probe", "run"))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "runner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        preparation = prepare()
        if args.stage == "probe":
            print(json.dumps(probe(preparation), indent=2))
        elif args.stage == "run":
            run_fold(preparation)
        else:
            print(OUT / "preparation.json")


if __name__ == "__main__":
    main()
