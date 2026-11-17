"""Corrected local fold, calibration references and fixed-population readout.

This is not the full regional comparison; v1 outputs remain untouched.
"""

from __future__ import annotations

import fcntl
import importlib.metadata
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from src.dise import ARMS, CANDIDATES, feature_columns, reconstruct, residual_target
from src.dise_corrected import (
    choose_donor,
    donor_fdc_apply,
    donor_fdc_fit,
    fdc_apply,
    fdc_fit,
    fit_candidate,
    population,
    score,
    split_masks,
    weights,
    year_bootstrap,
)
from src.geoglows_experiment import disk_check, sha, write_json

CONFIG = ROOT / "config/limburg_dise_v2.json"
PLAN = json.loads(CONFIG.read_text())
OUT = ROOT / PLAN["output"]
DEST = OUT / "benchmark_local_wurm_2021"


def calibration(frame, train, validation, test):
    past = train | validation
    before = frame.day.lt(f"{PLAN['benchmark_year']}-01-01") & frame.day.ge("2018-01-01")
    refs = pd.DataFrame(index=frame.index[test], columns=["local_fdc", "donor_fdc"], dtype=float)
    receipts = []
    descriptors = [c for c in frame if c.startswith("a_")]
    for target in sorted(frame.loc[test, "gauge"].unique()):
        query = test & frame.gauge.eq(target).to_numpy()
        local = (
            before & frame.gauge.eq(target) & frame.clean_verification & frame.q_observed.notna()
        )
        history = frame.loc[local]
        curves = fdc_fit(history.q_model, history.q_observed, history.day.dt.month)
        refs.loc[frame.index[query], "local_fdc"] = fdc_apply(
            curves,
            frame.loc[query, "q_model"].to_numpy(),
            frame.loc[query, "day"].dt.month.to_numpy(),
        )
        donor, selection = choose_donor(frame, past, target, descriptors)
        record = dict(
            target=target,
            local_pairs=len(history),
            local_curves=curves,
            local_information_budget="held-target past clean observations, extra-label reference",
            donor=donor,
            donor_selection=selection,
            donor_information_budget="no target observed Q",
        )
        if donor:
            dh = frame.loc[
                past & frame.gauge.eq(donor).to_numpy() & frame.clean_verification.to_numpy()
            ]
            th = frame.loc[
                before & frame.gauge.eq(target)
            ]  # model only; never filter by target observed availability
            dc = donor_fdc_fit(
                dh.q_model, dh.q_observed, dh.day.dt.month, th.q_model, th.day.dt.month
            )
            refs.loc[frame.index[query], "donor_fdc"] = donor_fdc_apply(
                dc,
                frame.loc[query, "q_model"].to_numpy(),
                frame.loc[query, "day"].dt.month.to_numpy(),
            )
            record["donor_curves"] = dc
            record["donor_pairs"] = len(dh)
        receipts.append(record)
    return refs, receipts


def review(predictions, frame):
    # Thresholds are evaluator-only: all held-target labels stay outside fitting.
    before = frame.day.lt(f"{PLAN['benchmark_year']}-01-01") & frame.day.ge("2018-01-01")
    thresholds = frame.loc[before].groupby("gauge").q_observed.quantile(0.99)
    predictions["p99_reference"] = predictions.gauge.map(thresholds)
    predictions["high_water"] = predictions.q_observed.ge(predictions.p99_reference)
    predictions["block_year"] = predictions.day.dt.year
    # A storm spanning New Year receives one onset-year label across all gauges.
    storms = pd.read_parquet(
        ROOT / "results/limburg_scarcity_v2_2026_10_28/preparation/storms.parquet"
    ).drop_duplicates("storm_id")
    predictions["storm_id"] = ""
    for row in storms.itertuples():
        start, end = pd.Timestamp(row.start_utc), pd.Timestamp(row.end_utc)
        use = predictions.day.between(start.floor("D"), end.floor("D"))
        predictions.loc[use, "block_year"] = start.year
        predictions.loc[use, "storm_id"] = row.storm_id
    arms = [
        "q_model",
        "local_fdc",
        "donor_fdc",
        *[f"{p}__{a}" for p in ["native_rmse", "article_faithful"] for a in ARMS],
    ]
    metrics = []
    populations = {}
    masks = {
        "all_days": np.ones(len(predictions), bool),
        "high_water": predictions.high_water.to_numpy(),
        "clean_high_water": (predictions.high_water & predictions.clean_verification).to_numpy(),
    }
    for stratum, mask in masks.items():
        part = predictions.loc[mask]
        expected = population(part)  # fixed from verification, before any model availability
        populations[stratum] = expected
        for arm in arms:
            metrics.append(dict(stratum=stratum, arm=arm, **score(part, part[arm], expected)))
    # A separate matched support table prevents unsupported calibration from
    # silently changing the main four-arm encoder comparison.
    common = np.isfinite(predictions[arms]).all(axis=1)
    for stratum, mask in masks.items():
        part = predictions.loc[mask & common]
        expected = population(predictions.loc[mask])
        for arm in arms:
            metrics.append(
                dict(
                    stratum=stratum + "_calibration_matched",
                    arm=arm,
                    **score(part, part[arm], expected),
                )
            )
    high = predictions.loc[predictions.high_water]
    names = ["native_rmse__H+A", "native_rmse__H+A+E"]
    draws, mult, blocks = year_bootstrap(
        high,
        {a: high[a].to_numpy() for a in names},
        populations["high_water"],
        PLAN["bootstrap_draws"],
        PLAN["bootstrap_seed"],
    )
    draws.to_parquet(DEST / "bootstrap.parquet", index=False)
    np.save(DEST / "bootstrap_multiplicities.npy", mult)
    delta = (draws[names[1]] - draws[names[0]]).dropna()
    uncertainty = dict(
        blocks=list(map(int, blocks)),
        draws=len(draws),
        defined_draws=len(delta),
        undefined_draws=len(draws) - len(delta),
        reason="single_year_no_between_year_interval"
        if len(blocks) < 2
        else "fixed_population_shared_block_draws",
        delta_interval=None if len(delta) == 0 else np.quantile(delta, [0.025, 0.975]).tolist(),
    )
    # Native units and daily/peak distinction remain available per gauge/day.
    for arm in arms:
        predictions[f"{arm}_m3s"] = predictions[arm] * predictions.reference_area_km2 / 86.4
    predictions.to_parquet(DEST / "predictions.parquet", index=False)
    write_json(
        DEST / "thresholds.json",
        dict(
            reference="held-target observed history 2018 through test-year minus one; evaluator only",
            values=thresholds.to_dict(),
        ),
    )
    write_json(DEST / "populations.json", populations)
    write_json(DEST / "metrics.json", dict(metrics=metrics, uncertainty=uncertainty))
    # Paired full-census day effects, with symmetric helped/harmed examples.
    effects = predictions[
        ["day", "gauge", "station", "storm_id", "high_water", "clean_verification"]
    ].copy()
    effects["encoder_error_difference"] = np.abs(
        predictions["native_rmse__H+A+E"] - predictions.q_observed
    ) - np.abs(predictions["native_rmse__H+A"] - predictions.q_observed)
    effects.to_csv(DEST / "paired_day_effects.csv", index=False)
    examples = pd.concat(
        [
            effects.nsmallest(3, "encoder_error_difference").assign(
                selection="three_largest_improvements"
            ),
            effects.nlargest(3, "encoder_error_difference").assign(selection="three_largest_harms"),
        ]
    )
    examples.to_csv(DEST / "symmetric_daily_examples.csv", index=False)
    return metrics, uncertainty


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    lock = (DEST / "runner.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    source = OUT / "local_features.parquet"
    inputs = [
        CONFIG,
        source,
        ROOT / "src/dise_corrected.py",
        ROOT / "src/dise.py",
        Path(__file__),
        ROOT / "results/limburg_scarcity_v2_2026_10_28/preparation/storms.parquet",
    ]
    pinned = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
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
            raise ValueError(
                "Changed corrected benchmark inputs; preserve results and use a new version"
            )
        if old["status"] == "completed":
            for n, h in old["outputs"].items():
                if sha(DEST / n) != h:
                    raise ValueError("Output changed")
            print("Corrected benchmark already completed and verified")
            return
    write_json(manifest, dict(status="running", identity=identity))
    frame = pd.read_parquet(source)
    train, val, test = split_masks(frame, PLAN["benchmark_year"], PLAN["benchmark_excluded_group"])
    groups = sorted(frame.loc[train, "river_group"].unique())
    n_expected = len(ARMS) * (len(CANDIDATES) * len(groups) + len(PLAN["seeds"])) * 2
    completed = 0
    before = time.monotonic()
    selected = {}
    predictions = frame.loc[
        test,
        [
            "day",
            "gauge",
            "station",
            "river_group",
            "reference_area_km2",
            "q_observed",
            "q_model",
            "clean_verification",
        ],
    ].copy()
    tuning = []
    for policy in ["native_rmse", "article_faithful"]:
        for arm in ARMS:
            columns = feature_columns(frame, arm)
            records = []
            for ci, candidate in enumerate(CANDIDATES):
                for group in groups:
                    it = train & frame.river_group.ne(group).to_numpy()
                    iv = val & frame.river_group.eq(group).to_numpy()
                    checkpoint = DEST / f"tune_{policy}_{arm.replace('+', '_')}_{ci}_{group}.json"
                    if checkpoint.exists():
                        saved = json.loads(checkpoint.read_text())
                        if saved["identity"] != identity:
                            raise ValueError("Stale corrected tuning checkpoint")
                        record = saved["record"]
                    else:
                        _, _, record = fit_candidate(
                            frame.loc[it], frame.loc[iv], columns, candidate, policy
                        )
                        record.update(
                            candidate_index=ci,
                            inner_group=group,
                            train_rows=int(it.sum()),
                            validation_rows=int(iv.sum()),
                        )
                        write_json(checkpoint, dict(identity=identity, record=record))
                    records.append(record)
                    tuning.append(dict(arm=arm, **record))
                    completed += 1
                    write_json(
                        DEST / "progress.json",
                        dict(
                            status="running",
                            fits_done=completed,
                            fits_expected=n_expected,
                            percent=100 * completed / n_expected,
                            policy=policy,
                            arm=arm,
                            free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
                        ),
                    )
            table = pd.DataFrame(records)
            criterion = (
                table.assign(criterion=table.validation_rmse**2)
                .groupby("candidate_index")
                .criterion.mean()
                if policy == "native_rmse"
                else table.groupby("candidate_index").validation_mae.mean()
            )
            best = int(criterion.idxmin())
            trees = int(np.median(table.loc[table.candidate_index.eq(best), "best_iteration"])) + 1
            name = f"{policy}__{arm}"
            selected[name] = dict(parameters=CANDIDATES[best], trees=trees, criterion=policy)
            past = train | val
            cols = [
                c
                for c in columns
                if np.isfinite(frame.loc[past, c]).any() and frame.loc[past, c].nunique() > 1
            ]
            parts = []
            for seed in PLAN["seeds"]:
                model = XGBRegressor(
                    **CANDIDATES[best],
                    n_estimators=trees,
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
                    residual_target(frame.loc[past, "q_observed"], frame.loc[past, "q_model"]),
                    sample_weight=weights(frame.loc[past]),
                )
                p, clipped = reconstruct(
                    frame.loc[test, "q_model"].to_numpy(), model.predict(frame.loc[test, cols])
                )
                parts.append(p)
                model.save_model(DEST / f"model_{name.replace('+', '_')}_{seed}.json")
                selected[name][f"floored_{seed}"] = clipped
                completed += 1
            predictions[name] = np.mean(parts, axis=0)
            print(
                f"{completed}/{n_expected} fits ({100 * completed / n_expected:.1f}%) {name}",
                flush=True,
            )
    refs, calibration_receipts = calibration(frame, train, val, test)
    predictions = predictions.join(refs)
    write_json(DEST / "calibration.json", calibration_receipts)
    metrics, uncertainty = review(predictions, frame)
    pd.DataFrame(tuning).to_csv(DEST / "tuning.csv", index=False)
    write_json(
        DEST / "readout.json",
        dict(
            scope="corrected local benchmark only; regional training pending",
            train_rows=int(train.sum()),
            validation_rows=int(val.sum()),
            test_rows=int(test.sum()),
            removed_calendar_buffer_days=0,
            selected=selected,
            fits_completed=completed,
            seconds=time.monotonic() - before,
            metrics=metrics,
            uncertainty=uncertainty,
        ),
    )
    if {str(p.relative_to(ROOT)): sha(p) for p in inputs} != pinned:
        raise ValueError("Input or code changed during corrected fitting")
    outputs = {
        p.name: sha(p)
        for p in DEST.iterdir()
        if p.is_file() and p.name not in ["manifest.json", "progress.json", "runner.lock"]
    }
    write_json(manifest, dict(status="completed", identity=identity, outputs=outputs))
    write_json(
        DEST / "progress.json",
        dict(
            status="completed",
            fits_done=completed,
            fits_expected=n_expected,
            percent=100,
            seconds=time.monotonic() - before,
        ),
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        write_json(DEST / "failure.json", dict(status="failed", error=repr(exc)))
        raise
