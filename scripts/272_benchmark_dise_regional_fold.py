"""One complete regional outer fold: four arms, fair tuning, three final seeds.

Probe is the first real tuning fit and is reused by run, not an extra experiment.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.metadata
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from src.dise import CANDIDATES, feature_columns, reconstruct, residual_target
from src.dise_corrected import (
    choose_donor,
    donor_fdc_apply,
    donor_fdc_fit,
    fdc_apply,
    fdc_fit,
    fit_candidate,
    population,
    score,
    weights,
    year_bootstrap,
)
from src.dise_regional import inner_masks, regional_masks
from src.geoglows_experiment import disk_check, sha, write_json

CONFIG = ROOT / "config/limburg_dise_regional_benchmark_v1.json"
PLAN = json.loads(CONFIG.read_text())
BASE = ROOT / PLAN["output"]
DEST = BASE / "benchmark_wurm_external_2021"


def peak_memory():
    n = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return n / (2**30 if sys.platform == "darwin" else 2**20)


def calibration(frame, train, validation, test):
    past = train | validation
    before = frame.day.ge("2018-01-01") & frame.day.lt(f"{PLAN['test_year']}-01-01")
    refs = pd.DataFrame(index=frame.index[test], columns=["local_fdc", "donor_fdc"], dtype=float)
    receipts = []
    descriptors = [c for c in frame if c.startswith("a_")]
    donor_descriptors = frame[["gauge", "day", *descriptors]]
    for target in sorted(frame.loc[test, "gauge"].unique()):
        query = test & frame.gauge.eq(target).to_numpy()
        target_frame = frame.loc[query]
        record = dict(target=target, source_role=str(target_frame.source_role.iloc[0]))
        if target_frame.source_role.eq("local").all():
            local = (
                before
                & frame.gauge.eq(target)
                & frame.clean_verification.fillna(False).astype(bool)
                & frame.q_observed.notna()
            )
            h = frame.loc[local]
            curves = fdc_fit(h.q_model, h.q_observed, h.day.dt.month)
            refs.loc[frame.index[query], "local_fdc"] = fdc_apply(
                curves,
                frame.loc[query, "q_model"].to_numpy(),
                frame.loc[query, "day"].dt.month.to_numpy(),
            )
            record.update(
                local_pairs=len(h),
                local_curves=curves,
                local_information_budget="extra held-local historical clean labels; not zero-local-label comparator",
            )
        donor, selection = choose_donor(donor_descriptors, past, target, descriptors)
        record.update(
            donor=donor,
            donor_selection=selection,
            donor_information_budget="same finite historical training/validation labels allowed for learner; no target Q",
            unknown_QA_not_recoded_clean=True,
        )
        if donor:
            dh = frame.loc[past & frame.gauge.eq(donor).to_numpy()]
            th = frame.loc[before & frame.gauge.eq(target)]
            curves = donor_fdc_fit(
                dh.q_model, dh.q_observed, dh.day.dt.month, th.q_model, th.day.dt.month
            )
            refs.loc[frame.index[query], "donor_fdc"] = donor_fdc_apply(
                curves,
                frame.loc[query, "q_model"].to_numpy(),
                frame.loc[query, "day"].dt.month.to_numpy(),
            )
            record.update(
                donor_pairs=len(dh),
                donor_curves=curves,
                donor_quality_values=dh.source_quality.value_counts().to_dict(),
            )
        receipts.append(record)
    write_json(DEST / "calibration.json", receipts)
    return refs


def evaluate(frame, predictions):
    before = frame.day.ge("2018-01-01") & frame.day.lt(f"{PLAN['test_year']}-01-01")
    thresholds = frame.loc[before].groupby("gauge").q_observed.quantile(0.99)
    predictions["p99_reference"] = predictions.gauge.map(thresholds)
    predictions["high_water"] = pd.Series(pd.NA, index=predictions.index, dtype="boolean")
    known = predictions.p99_reference.notna()
    predictions.loc[known, "high_water"] = predictions.loc[known, "q_observed"].ge(
        predictions.loc[known, "p99_reference"]
    )
    predictions["block_year"] = predictions.day.dt.year
    names = [
        "q_model",
        "donor_fdc",
        *[f"{policy}__{arm}" for policy in PLAN["policies"] for arm in PLAN["arms"]],
    ]
    local = predictions.source_role.eq("local").to_numpy()
    external = ~local
    scopes = {"local_held_Wurm": local, "external_all": external}
    for group in sorted(predictions.loc[external, "river_group"].unique()):
        scopes[group] = predictions.river_group.eq(group).to_numpy()
    scopes.update(
        external_high_overlap=external & predictions.spatial_view_high_overlap.to_numpy(),
        external_high_overlap_location_consistent=external
        & predictions.spatial_view_location_consistent.to_numpy(),
        external_mapping_stress=external & predictions.spatial_view_stress.to_numpy(),
    )
    for group in sorted(predictions.loc[external, "overlap_stratum"].unique()):
        scopes["external_overlap:" + group] = (
            external & predictions.overlap_stratum.eq(group).to_numpy()
        )
    masks = {
        "all_days": np.ones(len(predictions), bool),
        "high_water": predictions.high_water.fillna(False).to_numpy(dtype=bool),
        "clean_high_water": (
            predictions.high_water.fillna(False) & predictions.clean_verification.fillna(False)
        ).to_numpy(dtype=bool),
    }
    metrics = []
    populations = {}
    for scope, use in scopes.items():
        for stratum, mask in masks.items():
            part = predictions.loc[use & mask]
            expected = population(part)
            populations[f"{scope}/{stratum}"] = expected
            arms = names + (["local_fdc"] if scope == "local_held_Wurm" else [])
            for arm in arms:
                metrics.append(
                    dict(scope=scope, stratum=stratum, arm=arm, **score(part, part[arm], expected))
                )
    # Save undefined one-year intervals rather than invent daily independent floods.
    uncertainty = {}
    for scope, use in [("local_held_Wurm", local), ("external_all", external)]:
        part = predictions.loc[use & masks["high_water"]]
        paired = ["native_rmse__H+A", "native_rmse__H+A+E"]
        draws, mult, blocks = year_bootstrap(
            part,
            {n: part[n].to_numpy() for n in paired},
            population(part),
            PLAN["bootstrap_draws"],
            PLAN["bootstrap_seed"],
        )
        draws.to_parquet(DEST / f"bootstrap_{scope}.parquet", index=False)
        np.save(DEST / f"bootstrap_{scope}_multiplicities.npy", mult)
        uncertainty[scope] = dict(
            blocks=list(map(int, blocks)),
            draws=len(draws),
            defined_draws=int(draws.notna().all(axis=1).sum()),
            reason="single-year benchmark; no between-year confidence interval, no assumption of independent daily storm observations",
        )
    effects = predictions[
        [
            "gauge",
            "day",
            "station",
            "source_role",
            "river_group",
            "high_water",
            "clean_verification",
            "overlap_stratum",
            "location_stratum",
        ]
    ].copy()
    effects["encoder_error_difference"] = (
        predictions["native_rmse__H+A+E"] - predictions.q_observed
    ).abs() - (predictions["native_rmse__H+A"] - predictions.q_observed).abs()
    effects.to_parquet(DEST / "paired_day_effects.parquet", index=False)
    examples = []
    for _role, part in effects.groupby("source_role"):
        examples.extend(
            [
                part.nsmallest(3, "encoder_error_difference").assign(
                    selection="largest_improvements"
                ),
                part.nlargest(3, "encoder_error_difference").assign(selection="largest_harms"),
            ]
        )
    pd.concat(examples).to_csv(DEST / "symmetric_daily_examples.csv", index=False)
    for name in [*names, "local_fdc"]:
        predictions[name + "_m3s"] = predictions[name] * predictions.reference_area_km2 / 86.4
    predictions.to_parquet(DEST / "predictions.parquet", index=False)
    write_json(
        DEST / "thresholds.json",
        dict(
            evaluator_only=True,
            reference="held-target history 2018-2020, never fitting/tuning inputs",
            values={k: float(v) if np.isfinite(v) else None for k, v in thresholds.items()},
            unknown_threshold_gauges=predictions.loc[~known, "gauge"].unique().tolist(),
        ),
    )
    write_json(DEST / "populations.json", populations)
    write_json(DEST / "metrics.json", dict(metrics=metrics, uncertainty=uncertainty))
    pd.DataFrame([{k: v for k, v in r.items() if k != "per_gauge"} for r in metrics]).to_csv(
        DEST / "metrics.csv", index=False
    )
    return metrics, uncertainty


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["probe", "run"])
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    lock = (DEST / "runner.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    disk_check(ROOT, PLAN["reserve_gib"], 3 * 2**30)
    prep = BASE / "preparation"
    audit = json.loads((prep / "audit.json").read_text())
    if audit["status"] != "regional_preparation_audit_passed":
        raise ValueError("Preparation audit incomplete")
    source_paths = [
        CONFIG,
        Path(__file__),
        ROOT / "src/dise_regional.py",
        ROOT / "src/dise_corrected.py",
        ROOT / "src/dise.py",
        prep / "features.parquet",
        prep / "inner_folds.json",
        prep / "audit.json",
    ]
    pinned = {str(p.relative_to(ROOT)): sha(p) for p in source_paths}
    identity = dict(
        sources=pinned,
        packages={
            n: importlib.metadata.version(n) for n in ["numpy", "pandas", "xgboost", "scikit-learn"]
        },
    )
    manifest = DEST / "manifest.json"
    if manifest.exists():
        old = json.loads(manifest.read_text())
        if old["identity"] != identity:
            raise ValueError("Benchmark identity changed; preserve results and version the run")
        if old["status"] == "completed":
            for name, h in old["outputs"].items():
                if sha(DEST / name) != h:
                    raise ValueError("Completed output changed")
            print("Regional benchmark already complete and verified")
            return
    write_json(manifest, dict(status="in_progress", identity=identity))
    frame = pd.read_parquet(prep / "features.parquet")
    train, validation, test = regional_masks(frame, PLAN["test_year"], PLAN["withheld_local_group"])
    assignment = json.loads((prep / "inner_folds.json").read_text())
    total = (
        len(PLAN["policies"])
        * len(PLAN["arms"])
        * (len(CANDIDATES) * PLAN["inner_folds"] + len(PLAN["seeds"]))
    )
    completed = 0
    start = time.monotonic()
    tuning = []
    selected = {}
    fit_seconds = []
    meta = [
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
    predictions = frame.loc[test, meta].copy()

    def progress(status, **extra):
        write_json(
            DEST / "progress.json",
            dict(
                status=status,
                fits_done=completed,
                fits_expected=total,
                percent=100 * completed / total,
                seconds_this_session=time.monotonic() - start,
                recorded_fit_seconds=sum(fit_seconds),
                peak_rss_gib=peak_memory(),
                free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
                **extra,
            ),
        )

    for policy in PLAN["policies"]:
        for arm in PLAN["arms"]:
            columns = feature_columns(frame, arm)
            records = []
            for ci, candidate in enumerate(CANDIDATES):
                for fold in range(PLAN["inner_folds"]):
                    key = f"{policy}_{arm.replace('+', '_')}_{ci}_{fold}"
                    receipt = DEST / f"tune_{key}.json"
                    model_path = DEST / f"tune_{key}.ubj"
                    it, iv = inner_masks(frame, train, validation, assignment, fold)
                    if receipt.exists():
                        saved = json.loads(receipt.read_text())
                        if (
                            saved["identity"] != identity
                            or sha(model_path) != saved["model_sha256"]
                        ):
                            raise ValueError("Stale tuning checkpoint")
                        record = saved["record"]
                    else:
                        progress("running", active_fit=key)
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
                        model.save_model(model_path)
                        write_json(
                            receipt,
                            dict(
                                identity=identity,
                                record=record,
                                columns=cols,
                                model_sha256=sha(model_path),
                            ),
                        )
                        del model
                    completed += 1
                    fit_seconds.append(record["seconds"])
                    records.append(record)
                    tuning.append(dict(arm=arm, **record))
                    print(
                        f"{completed}/{total} fits ({100 * completed / total:.1f}%) {key}: {record['seconds']:.2f}s, best tree {record['best_iteration'] + 1}",
                        flush=True,
                    )
                    progress("running", last_fit=key)
                    if args.phase == "probe":
                        write_json(
                            DEST / "probe.json",
                            dict(
                                status="completed_first_real_tuning_fit_reusable",
                                fit=key,
                                record=record,
                                peak_rss_gib=peak_memory(),
                                rough_152_fit_minutes_at_this_rate=total * record["seconds"] / 60,
                                not_a_final_eta="Other arms/candidates may stop at different tree counts; checkpoint reused in full benchmark.",
                            ),
                        )
                        progress("probe_completed_full_benchmark_ready")
                        return
            table = pd.DataFrame(records)
            table["weighted_criterion"] = (
                table.validation_rmse**2 if policy == "native_rmse" else table.validation_mae
            ) * table.validation_groups
            criterion = (
                table.groupby("candidate_index").weighted_criterion.sum()
                / table.groupby("candidate_index").validation_groups.sum()
            )
            best = int(criterion.idxmin())
            trees = int(np.median(table.loc[table.candidate_index.eq(best), "best_iteration"])) + 1
            name = f"{policy}__{arm}"
            selected[name] = dict(
                candidate_index=best,
                parameters=CANDIDATES[best],
                trees=trees,
                criterion=float(criterion.loc[best]),
                criterion_scale="MSE" if policy == "native_rmse" else "MAE",
            )
            past = train | validation
            cols = [
                c
                for c in columns
                if np.isfinite(frame.loc[past, c]).any() and frame.loc[past, c].nunique() > 1
            ]
            parts = []
            for seed in PLAN["seeds"]:
                key = f"{name.replace('+', '_')}_{seed}"
                path = DEST / f"final_{key}.ubj"
                rec = DEST / f"final_{key}.json"
                pred_path = DEST / f"final_{key}.npy"
                if rec.exists():
                    old = json.loads(rec.read_text())
                    if (
                        old["identity"] != identity
                        or sha(path) != old["model_sha256"]
                        or sha(pred_path) != old["prediction_sha256"]
                    ):
                        raise ValueError("Stale final fit")
                    p = np.load(pred_path)
                    seconds = old["seconds"]
                else:
                    progress("running", active_fit=key)
                    before = time.monotonic()
                    model = XGBRegressor(
                        **CANDIDATES[best],
                        n_estimators=trees,
                        n_jobs=PLAN["threads_per_fit"],
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
                        residual_target(frame.loc[past, "q_observed"], frame.loc[past, "q_model"]),
                        sample_weight=weights(frame.loc[past]),
                    )
                    p, clipped = reconstruct(
                        frame.loc[test, "q_model"].to_numpy(), model.predict(frame.loc[test, cols])
                    )
                    seconds = time.monotonic() - before
                    model.save_model(path)
                    np.save(pred_path, p)
                    write_json(
                        rec,
                        dict(
                            identity=identity,
                            columns=cols,
                            seconds=seconds,
                            negative_reconstructions_floored=clipped,
                            model_sha256=sha(path),
                            prediction_sha256=sha(pred_path),
                        ),
                    )
                    del model
                parts.append(p)
                completed += 1
                fit_seconds.append(seconds)
                progress("running", last_fit=key)
                print(
                    f"{completed}/{total} fits ({100 * completed / total:.1f}%) final {key}: {seconds:.2f}s",
                    flush=True,
                )
            predictions[name] = np.mean(parts, axis=0)
    predictions = predictions.join(calibration(frame, train, validation, test))
    metrics, uncertainty = evaluate(frame, predictions)
    pd.DataFrame(tuning).to_csv(DEST / "tuning.csv", index=False)
    write_json(DEST / "selected.json", selected)
    write_json(
        DEST / "readout.json",
        dict(
            scope="One regional-training outer Wurm/external fold in 2021, not the full multiyear study",
            fits_completed=completed,
            train_rows=int(train.sum()),
            validation_rows=int(validation.sum()),
            test_rows=int(test.sum()),
            train_gauges=int(frame.loc[train, "gauge"].nunique()),
            test_gauges=int(frame.loc[test, "gauge"].nunique()),
            recorded_fit_seconds=sum(fit_seconds),
            session_seconds=time.monotonic() - start,
            peak_rss_gib=peak_memory(),
            primary_contrast="native_rmse__H+A+E versus native_rmse__H+A",
            uncertainty=uncertainty,
            metric_rows=len(metrics),
        ),
    )
    if {str(p.relative_to(ROOT)): sha(p) for p in source_paths} != pinned:
        raise ValueError("Run inputs/code changed")
    outputs = {
        p.name: sha(p)
        for p in DEST.iterdir()
        if p.is_file()
        and p.name not in ["manifest.json", "progress.json", "runner.lock", "failure.json"]
    }
    write_json(manifest, dict(status="completed", identity=identity, outputs=outputs))
    progress("completed")
    print("Regional first-fold benchmark complete", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        DEST.mkdir(parents=True, exist_ok=True)
        write_json(DEST / "failure.json", dict(status="failed", error=repr(exc)))
        raise
