"""Uniform 3000-tree capacity check, reusing only empirically verified early stops.

Reselect on validation only. Preserve the original fold and launch no later plan step.
"""

from __future__ import annotations

import fcntl
import importlib.metadata
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from src.dise import CANDIDATES, feature_columns, reconstruct, residual_target
from src.dise_capacity import reuse_early_stopped, same_final_spec, select_validation
from src.dise_corrected import fit_candidate, weights
from src.dise_regional import inner_masks, regional_masks
from src.geoglows_experiment import disk_check, sha, write_json

CONFIG = ROOT / "config/limburg_dise_capacity_v1.json"
PLAN = json.loads(CONFIG.read_text())
OUT = ROOT / PLAN["output"]
OLD = ROOT / PLAN["base_benchmark"]
PREP = ROOT / PLAN["preparation"]


def key_for(policy, arm, candidate, fold):
    return f"{policy}_{arm.replace('+', '_')}_{candidate}_{fold}"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / "runner.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    disk_check(ROOT, PLAN["reserve_gib"], 2 * 2**30)
    start = time.monotonic()
    original = json.loads((OLD / "manifest.json").read_text())
    if original["status"] != "completed":
        raise ValueError("Original benchmark incomplete")
    for name, h in original["identity"]["sources"].items():
        if sha(ROOT / name) != h:
            raise ValueError(f"Original scientific input/code changed: {name}")
    for name, h in original["outputs"].items():
        if sha(OLD / name) != h:
            raise ValueError(f"Original output changed: {name}")
    runtime = {n: importlib.metadata.version(n) for n in original["identity"]["packages"]}
    if runtime != original["identity"]["packages"]:
        raise ValueError("Different runtime; use a separate explicitly reviewed comparison")
    sources = [
        CONFIG,
        Path(__file__),
        ROOT / "src/dise_capacity.py",
        ROOT / "scripts/272_benchmark_dise_regional_fold.py",
        ROOT / "src/dise.py",
        ROOT / "src/dise_corrected.py",
        ROOT / "src/dise_regional.py",
        PREP / "features.parquet",
        PREP / "inner_folds.json",
        OLD / "manifest.json",
    ]
    pinned = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    identity = dict(sources=pinned, packages=runtime)
    manifest = OUT / "manifest.json"
    if manifest.exists():
        m = json.loads(manifest.read_text())
        if m["identity"] != identity:
            raise ValueError("Capacity identity changed; preserve/version instead of overwriting")
        if m["status"] == "completed":
            for name, h in m["outputs"].items():
                if sha(OUT / name) != h:
                    raise ValueError("Capacity output changed")
            print("Capacity check complete and verified")
            return
    write_json(manifest, dict(status="running", identity=identity))
    spec = importlib.util.spec_from_file_location(
        "frozen_regional_evaluator", ROOT / "scripts/272_benchmark_dise_regional_fold.py"
    )
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    evaluator.DEST = OUT
    evaluator.PLAN = PLAN
    frame = pd.read_parquet(PREP / "features.parquet")
    train, validation, test = regional_masks(frame, PLAN["test_year"], PLAN["withheld_local_group"])
    assignment = json.loads((PREP / "inner_folds.json").read_text())
    base_predictions = pd.read_parquet(OLD / "predictions.parquet")
    assert np.array_equal(frame.loc[test, "gauge"], base_predictions.gauge) and np.array_equal(
        frame.loc[test, "day"], base_predictions.day
    )
    assert np.array_equal(frame.loc[test, "q_observed"], base_predictions.q_observed)
    old_selected = json.loads((OLD / "selected.json").read_text())
    old_table = pd.read_csv(OLD / "tuning.csv")
    old_records = {}
    for r in old_table.itertuples(index=False):
        key = key_for(r.policy, r.arm, r.candidate_index, r.fold)
        saved = json.loads((OLD / f"tune_{key}.json").read_text())
        if (
            saved["identity"] != original["identity"]
            or sha(OLD / f"tune_{key}.ubj") != saved["model_sha256"]
        ):
            raise ValueError("Unverified old tuning fit")
        old_records[key] = saved
    new_tuning_done = 0
    slots = 0
    new_final_done = 0
    new_final_total = None
    required_new = None
    new_seconds = 0.0
    reused_finals = 0

    def progress(phase, **extra):
        write_json(
            OUT / "progress.json",
            dict(
                status="running",
                phase=phase,
                tuning_slots_done=slots,
                tuning_slots_total=128,
                new_tuning_refits_done=new_tuning_done,
                new_tuning_refits_total=required_new,
                tuning_refit_percent=100 * new_tuning_done / required_new if required_new else None,
                final_refits_done=new_final_done,
                final_refits_total=new_final_total,
                final_refit_percent=100 * new_final_done / new_final_total
                if new_final_total
                else None,
                reused_final_fits=reused_finals,
                seconds_this_session=time.monotonic() - start,
                new_fit_seconds=new_seconds,
                peak_rss_gib=evaluator.peak_memory(),
                free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
                **extra,
            ),
        )

    def fresh(policy, arm, ci, fold):
        it, iv = inner_masks(frame, train, validation, assignment, fold)
        model, cols, record = fit_candidate(
            frame.loc[it],
            frame.loc[iv],
            feature_columns(frame, arm),
            CANDIDATES[ci],
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
            tree_cap_hit=model.get_booster().num_boosted_rounds() == PLAN["tree_limit"],
            fitted_boosting_rounds=model.get_booster().num_boosted_rounds(),
        )
        return model, cols, record, it, iv

    # One fixed control checks the declared reuse shortcut, not test skill.
    control = PLAN["parity_control"]
    control_key = key_for(
        control["policy"], control["arm"], control["candidate_index"], control["fold"]
    )
    cp = OUT / "parity_control.json"
    cm = OUT / "parity_control.ubj"
    if cp.exists():
        parity = json.loads(cp.read_text())
        if parity["identity"] != identity or sha(cm) != parity["model_sha256"]:
            raise ValueError("Changed parity control")
    else:
        progress("parity_control", active_fit=control_key)
        model, cols, record, it, iv = fresh(
            control["policy"], control["arm"], control["candidate_index"], control["fold"]
        )
        old = old_records[control_key]
        if not reuse_early_stopped(old["record"], PLAN["old_tree_limit"]):
            raise ValueError("Fixed parity control was not originally early-stopped")
        loaded = XGBRegressor(n_jobs=PLAN["threads_per_fit"])
        loaded.load_model(OLD / f"tune_{control_key}.ubj")
        left = loaded.predict(frame.loc[iv, old["columns"]])
        right = model.predict(frame.loc[iv, cols])
        same = (
            cols == old["columns"]
            and record["best_iteration"] == old["record"]["best_iteration"]
            and record["fitted_boosting_rounds"] == old["record"]["fitted_boosting_rounds"]
            and np.array_equal(left, right)
        )
        model.save_model(cm)
        parity = dict(
            identity=identity,
            control=control,
            record=record,
            columns=cols,
            model_sha256=sha(cm),
            bitwise_prediction_parity=bool(np.array_equal(left, right)),
            maximum_residual_prediction_difference=float(np.max(np.abs(left - right))),
            same_stopping_and_predictions=bool(same),
            reuse_validated=bool(same),
            fallback="Refit all 128 at 3000 if parity fails",
        )
        write_json(cp, parity)
        del model, loaded
    reuse = parity["reuse_validated"]
    required_new = (
        sum(
            not reuse_early_stopped(r["record"], PLAN["old_tree_limit"])
            for r in old_records.values()
        )
        + 1
        if reuse
        else 128
    )
    assert required_new in [27, 128]
    new_seconds += parity["record"]["seconds"]
    print(
        "Parity control:", reuse, "fresh tuning fits including control:", required_new, flush=True
    )
    records = []
    selections = {}
    fresh_keys = {control_key}
    reused_keys = []
    for policy in PLAN["policies"]:
        for arm in PLAN["arms"]:
            group = []
            for ci in range(len(CANDIDATES)):
                for fold in range(PLAN["inner_folds"]):
                    key = key_for(policy, arm, ci, fold)
                    path = OUT / f"tune_{key}.ubj"
                    receipt = OUT / f"tune_{key}.json"
                    old = old_records[key]
                    if receipt.exists():
                        saved = json.loads(receipt.read_text())
                        if saved["identity"] != identity or sha(path) != saved["model_sha256"]:
                            raise ValueError("Changed capacity tuning checkpoint")
                    else:
                        if key == control_key:
                            shutil.copyfile(cm, path)
                            record = parity["record"]
                            cols = parity["columns"]
                            origin = "fresh_parity_control"
                        elif reuse and reuse_early_stopped(old["record"], PLAN["old_tree_limit"]):
                            shutil.copyfile(OLD / f"tune_{key}.ubj", path)
                            record = old["record"]
                            cols = old["columns"]
                            origin = "reused_verified_early_stop"
                        else:
                            progress("tuning", active_fit=key)
                            model, cols, record, _, _ = fresh(policy, arm, ci, fold)
                            model.save_model(path)
                            origin = "fresh_capacity_refit"
                            del model
                        saved = dict(
                            identity=identity,
                            record=record,
                            columns=cols,
                            model_sha256=sha(path),
                            origin=origin,
                            original_receipt_sha256=sha(OLD / f"tune_{key}.json"),
                        )
                        write_json(receipt, saved)
                    record = saved["record"]
                    group.append(record)
                    records.append(dict(arm=arm, origin=saved["origin"], **record))
                    slots += 1
                    if saved["origin"].startswith("fresh"):
                        fresh_keys.add(key)
                        if key != control_key:
                            new_seconds += record["seconds"]
                    else:
                        reused_keys.append(key)
                    new_tuning_done = len(fresh_keys)
                    progress("tuning", last_fit=key)
                    if saved["origin"].startswith("fresh"):
                        print(
                            f"Tuning refits {new_tuning_done}/{required_new}: {key}, {record['seconds']:.1f}s, cap={record['tree_cap_hit']}",
                            flush=True,
                        )
            selections[f"{policy}__{arm}"] = select_validation(group, policy, CANDIDATES)
    pd.DataFrame(records).to_csv(OUT / "tuning.csv", index=False)
    write_json(OUT / "selected.json", selections)
    affected = [
        name for name, new in selections.items() if not same_final_spec(old_selected[name], new)
    ]
    new_final_total = len(affected) * len(PLAN["seeds"])
    write_json(
        OUT / "selection_changes.json",
        dict(affected=affected, old=old_selected, new=selections, new_final_fits=new_final_total),
    )
    print("Affected ensembles:", affected, "new final fits:", new_final_total, flush=True)
    metadata = [
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
    predictions = frame.loc[test, metadata].copy()
    past = train | validation
    for name, settings in selections.items():
        policy, arm = name.split("__")
        columns = feature_columns(frame, arm)
        cols = [
            c
            for c in columns
            if np.isfinite(frame.loc[past, c]).any() and frame.loc[past, c].nunique() > 1
        ]
        parts = []
        for seed in PLAN["seeds"]:
            key = f"{name.replace('+', '_')}_{seed}"
            path = OUT / f"final_{key}.ubj"
            array = OUT / f"final_{key}.npy"
            receipt = OUT / f"final_{key}.json"
            if receipt.exists():
                record = json.loads(receipt.read_text())
                if (
                    record["identity"] != identity
                    or sha(path) != record["model_sha256"]
                    or sha(array) != record["prediction_sha256"]
                ):
                    raise ValueError("Changed capacity final checkpoint")
                pred = np.load(array)
            elif name not in affected:
                old = json.loads((OLD / f"final_{key}.json").read_text())
                if old["columns"] != cols or old["identity"] != original["identity"]:
                    raise ValueError("Different final feature specification")
                shutil.copyfile(OLD / f"final_{key}.ubj", path)
                shutil.copyfile(OLD / f"final_{key}.npy", array)
                pred = np.load(array)
                record = dict(
                    identity=identity,
                    origin="reused_unchanged_final_spec",
                    seconds=0,
                    original_seconds=old["seconds"],
                    columns=cols,
                    model_sha256=sha(path),
                    prediction_sha256=sha(array),
                    original_receipt_sha256=sha(OLD / f"final_{key}.json"),
                )
                write_json(receipt, record)
            else:
                progress("final_refits", active_fit=key)
                before = time.monotonic()
                model = XGBRegressor(
                    **settings["parameters"],
                    n_estimators=settings["trees"],
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
                pred, clipped = reconstruct(
                    frame.loc[test, "q_model"].to_numpy(), model.predict(frame.loc[test, cols])
                )
                seconds = time.monotonic() - before
                model.save_model(path)
                np.save(array, pred)
                record = dict(
                    identity=identity,
                    origin="fresh_changed_final_spec",
                    seconds=seconds,
                    columns=cols,
                    negative_reconstructions_floored=clipped,
                    model_sha256=sha(path),
                    prediction_sha256=sha(array),
                )
                write_json(receipt, record)
                del model
            parts.append(pred)
            if record["origin"].startswith("fresh"):
                new_final_done += 1
                new_seconds += record["seconds"]
            else:
                reused_finals += 1
            progress("final_refits", last_fit=key)
            print(
                f"Final refits {new_final_done}/{new_final_total}; reused finals {reused_finals}: {key}",
                flush=True,
            )
        predictions[name] = np.mean(parts, axis=0)
    predictions["local_fdc"] = base_predictions.local_fdc.to_numpy()
    predictions["donor_fdc"] = base_predictions.donor_fdc.to_numpy()
    shutil.copyfile(OLD / "calibration.json", OUT / "calibration.json")
    evaluator.evaluate(frame, predictions)
    compare_and_finish(
        identity,
        pinned,
        selections,
        old_selected,
        records,
        parity,
        reused_keys,
        fresh_keys,
        new_final_done,
        reused_finals,
        new_seconds,
        time.monotonic() - start,
    )


def compare_and_finish(
    identity,
    pinned,
    selections,
    old_selected,
    records,
    parity,
    reused_keys,
    fresh_keys,
    new_finals,
    reused_finals,
    new_seconds,
    elapsed,
):
    old = pd.read_csv(OLD / "metrics.csv")
    new = pd.read_csv(OUT / "metrics.csv")
    comparison = old.merge(
        new, on=["scope", "stratum", "arm"], suffixes=("_1500", "_3000"), validate="one_to_one"
    )
    assert len(comparison) == len(old) == len(new)
    assert comparison.rows_1500.eq(comparison.rows_3000).all()
    for arm in ["q_model", "donor_fdc", "local_fdc"]:
        baseline = comparison.loc[comparison.arm.eq(arm)]
        for col in ["mae", "rmse", "bias"]:
            assert np.allclose(
                baseline[col + "_1500"],
                baseline[col + "_3000"],
                rtol=1e-12,
                atol=1e-12,
                equal_nan=True,
            )
    comparison["mae_change_3000_minus_1500"] = comparison.mae_3000 - comparison.mae_1500
    comparison.to_csv(OUT / "budget_comparison.csv", index=False)
    primary = []
    for scope in [
        "local_held_Wurm",
        "external_all",
        "external_high_overlap",
        "external_high_overlap_location_consistent",
        "external_mapping_stress",
    ]:
        for stratum in ["all_days", "high_water", "clean_high_water"]:
            rows = {}
            for budget, data in [(1500, old), (3000, new)]:
                f = data.loc[data.scope.eq(scope) & data.stratum.eq(stratum)]
                a = f.loc[f.arm.eq("native_rmse__H+A")].iloc[0]
                e = f.loc[f.arm.eq("native_rmse__H+A+E")].iloc[0]
                rows[budget] = dict(
                    conventional_mae=a.mae,
                    alpha_mae=e.mae,
                    mae_reduction_pct=100 * (1 - e.mae / a.mae)
                    if a.status == "defined" and e.status == "defined"
                    else None,
                )
            primary.append(
                dict(
                    scope=scope,
                    stratum=stratum,
                    **{
                        f"{key}_{budget}": value
                        for budget, values in rows.items()
                        for key, value in values.items()
                    },
                )
            )
    pd.DataFrame(primary).to_csv(OUT / "primary_budget_comparison.csv", index=False)
    table = pd.DataFrame(records)
    selected_cap = {
        name: int(
            table.loc[
                table.policy.eq(name.split("__")[0])
                & table.arm.eq(name.split("__")[1])
                & table.candidate_index.eq(s["candidate_index"]),
                "tree_cap_hit",
            ].sum()
        )
        for name, s in selections.items()
    }
    summary = dict(
        status="completed",
        scope="Four-step plan Step 1 only",
        tree_limit=PLAN["tree_limit"],
        old_tree_limit=PLAN["old_tree_limit"],
        parity_control=parity["same_stopping_and_predictions"],
        parity_maximum_prediction_difference=parity["maximum_residual_prediction_difference"],
        fresh_tuning_fits=len(fresh_keys),
        reused_tuning_fits=len(reused_keys),
        fresh_final_fits=new_finals,
        reused_final_fits=reused_finals,
        remaining_tuning_cap_hits=int(table.tree_cap_hit.sum()),
        selected_cap_hits=selected_cap,
        selection_changes={
            k: dict(
                original=old_selected[k],
                expanded=v,
                final_spec_changed=not same_final_spec(old_selected[k], v),
            )
            for k, v in selections.items()
        },
        seconds=elapsed,
        new_fit_seconds=new_seconds,
        original_benchmark_manifest_sha256=sha(OLD / "manifest.json"),
        unchanged_test_rows_and_controls=True,
        no_step2_launched=True,
        free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
    )
    write_json(OUT / "capacity_summary.json", summary)
    lines = [
        "# Step 1 capacity check — completed",
        "",
        f"Fresh tuning fits: {len(fresh_keys)}; reused early stops: {len(reused_keys)}.",
        f"Fresh final fits: {new_finals}; reused final fits: {reused_finals}.",
        f"Remaining 3000-tree tuning cap hits: {summary['remaining_tuning_cap_hits']}.",
        "",
        "Primary paired MAE reduction from adding AlphaEarth (positive improves):",
        "",
        "| Population | Outcome | 1500-tree budget | 3000-tree budget |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in primary:
        if row["scope"] not in ["local_held_Wurm", "external_all"]:
            continue
        a, b = row["mae_reduction_pct_1500"], row["mae_reduction_pct_3000"]
        if a is not None and b is not None:
            lines.append(f"| {row['scope']} | {row['stratum']} | {a:.2f}% | {b:.2f}% |")
    lines += [
        "",
        "This remains one 2021 fold. Original results, populations and controls are preserved.",
        "No further cap escalation or multi-year run was launched.",
    ]
    (OUT / "readout.md").write_text("\n".join(lines) + "\n")
    if {name: sha(ROOT / name) for name in pinned} != pinned:
        raise ValueError("Capacity inputs/code changed during run")
    outputs = {
        p.name: sha(p)
        for p in OUT.iterdir()
        if p.is_file()
        and p.name not in ["manifest.json", "progress.json", "runner.lock", "failure.json"]
    }
    write_json(OUT / "manifest.json", dict(status="completed", identity=identity, outputs=outputs))
    write_json(
        OUT / "progress.json",
        dict(
            status="completed",
            phase="comparison_complete",
            percent=100,
            new_tuning_refits_done=len(fresh_keys),
            new_tuning_refits_total=len(fresh_keys),
            final_refits_done=new_finals,
            final_refits_total=new_finals,
            reused_tuning_fits=len(reused_keys),
            reused_final_fits=reused_finals,
            seconds=elapsed,
            free_gib=summary["free_gib"],
        ),
    )
    workflow = ROOT / PLAN["workflow_plan"]
    w = json.loads(workflow.read_text())
    for step in w["steps"]:
        if step["number"] == 1:
            step.update(
                status="complete", result="results/limburg_dise_capacity_v1/capacity_summary.json"
            )
    write_json(workflow, w)
    current = ROOT / "config/limburg_current_study.json"
    c = json.loads(current.read_text())
    if c.get("capacity_config") == "config/limburg_dise_capacity_v1.json":
        c.update(
            status="dise_capacity_check_complete",
            active_workers={"fitting": 0, "threads_per_fit": 0, "gpu": 0},
            new_queue_started=False,
            capacity_completed=True,
        )
        c.pop("capacity_pid", None)
        c.pop("capacity_managed_session", None)
        write_json(current, c)
    print(
        json.dumps({k: v for k, v in summary.items() if k != "selection_changes"}, indent=2),
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        write_json(OUT / "failure.json", dict(status="failed", error=repr(exc)))
        raise
