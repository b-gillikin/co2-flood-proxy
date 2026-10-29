"""Audit completed EO diagnostics and summarize signal, placebo and learned-use results."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_comparison import load_script
from src.eo_inputs import ROUTES, sha256
from src.eo_integrity import fresh_output
from src.eo_signal_diagnostic import chronology
from src.scarcity_review import joint_summary

CFG = json.loads((ROOT / "config/limburg_eo_signal_diagnostic_v1.json").read_text())
OUT = ROOT / CFG["output"]
SOURCE = ROOT / CFG["source"]


def audit_job(path, meta, storms, bank, representations):
    manifest = json.loads((path / "manifest.json").read_text())
    for name, digest in manifest["sources_sha256"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError("Changed diagnostic source: " + name)
    for name, digest in manifest["outputs_sha256"].items():
        if sha256(path / name) != digest:
            raise ValueError("Changed diagnostic output: " + name)
    model, kind = manifest["model"], manifest["readout"]
    j = next(i for i, rep in enumerate(representations) if rep == dict(model=model, kind=kind))
    valid = bank["eo_valid"][j]
    years = storms.cutoff_utc.dt.year.to_numpy()
    quarter = storms.cutoff_utc.dt.quarter.to_numpy() - 1
    n = len(storms)
    data = dict(np.load(path / "predictions.npz"))
    folds = json.loads((path / "folds.json").read_text())
    tuning = pd.read_parquet(path / "tuning.parquet")
    if len(folds) != len(CFG["scenarios"]) * 8 * len(np.unique(years)):
        raise ValueError("Missing outer-fold census")
    for fold in folds:
        scenario = fold["scenario"]
        gi = int(np.flatnonzero(meta.gauge.to_numpy()[:8] == fold["gauge"])[0])
        expected = np.flatnonzero(
            chronology(storms.cutoff_utc, storms.end_utc, fold["boundary_utc"])
            & bank["outcome_valid_0"][:, gi]
        )
        np.testing.assert_array_equal(expected, fold["train_ids"])
        train = expected[valid[expected, gi]]
        np.testing.assert_array_equal(train, fold["eo_train_ids"])
        test = np.flatnonzero(years == fold["year"])
        np.testing.assert_array_equal(test, fold["test_ids"])
        source = data[scenario + "_null_sources"][:, test, gi]
        if not np.isin(source[source >= 0], train).all():
            raise ValueError("Null readout consulted a nontraining vector")
        actual = data[scenario + "_eo_supported"][test, gi]
        np.testing.assert_array_equal(actual, valid[test, gi] & (len(train) >= 2))
        params = tuning[
            (tuning.scenario == scenario)
            & (tuning.gauge == fold["gauge"])
            & (tuning.year == fold["year"])
            & (tuning.arm == "ground_real")
        ]
        if len(params) and params.weight.iloc[0] == 0:
            np.testing.assert_allclose(
                data[scenario + "_predictions"][2, test, gi],
                data[scenario + "_predictions"][1, test, gi],
                equal_nan=True,
                atol=2e-7,
            )
    compared = 0
    for scenario in CFG["scenarios"]:
        predictions = data[scenario + "_predictions"]
        if predictions.shape != (3 + CFG["permutations"], n, 8, 24):
            raise ValueError("Prediction census changed")
        crps, source = data[scenario + "_retrieval_crps"], data[scenario + "_retrieval_sources"]
        for replication, qi, gi in np.argwhere(source >= 0):
            di = source[replication, qi, gi]
            if not (bank["prior_0_0"][qi, di] and valid[di, gi] and quarter[di] == quarter[qi]):
                raise ValueError("Noncausal or wrong-quarter retrieval placebo")
        old = pd.read_parquet(SOURCE / f"scores/{scenario}__u0/scores.parquet")
        for arm, label in [(0, "matched"), (1, "augmented")]:
            f = old[old.method.eq(f"{model}__{kind}__{label}") & old.target_k.eq(5)].set_index(
                "case"
            )
            for case, value in zip(
                np.flatnonzero(np.isfinite(crps[arm].ravel())),
                crps[arm].ravel()[np.isfinite(crps[arm].ravel())],
                strict=True,
            ):
                np.testing.assert_allclose(
                    value, f.loc[case, "crps_specific"], rtol=2e-6, atol=2e-8
                )
                compared += 1
    return (
        data,
        tuning,
        dict(
            job=path.name,
            folds=len(folds),
            retrieval_scores_replayed=compared,
            cases_per_scenario=n * 8,
            status="passed",
        ),
    )


def score_points(predictions, y):
    finite = np.isfinite(predictions).all(axis=-1) & np.isfinite(y).all(axis=-1)[None]
    mae = np.mean(np.abs(predictions - y[None]), axis=-1)
    rmse = np.sqrt(np.mean((predictions - y[None]) ** 2, axis=-1))
    return np.where(finite, mae, np.nan), np.where(finite, rmse, np.nan)


def summarize_effect(values, reference, years, metadata):
    result = joint_summary(values, years, random_masks=len(values) > 1)
    baseline = joint_summary(
        np.where(np.isfinite(values), reference, np.nan), years, random_masks=False, draws=0
    )["estimate"]
    result["reference_mean_error"] = baseline
    result["relative_difference_pct"] = (
        100 * result["estimate"] / baseline if baseline > 0 else np.nan
    )
    return dict(**metadata, **result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    paths = sorted(
        p
        for p in (OUT / "jobs").glob("*")
        if not p.name.startswith(".") and (p / "manifest.json").exists()
    )
    expected = len(CFG["models"]) * len(CFG["readouts"])
    if not args.benchmark and len(paths) != expected:
        raise ValueError("Full diagnostics require all declared models/readouts")
    if not args.benchmark and {p.name for p in paths} != {
        m + "__" + k for m in CFG["models"] for k in CFG["readouts"]
    }:
        raise ValueError("Model/readout inventory differs from the declared diagnostic")
    prep = SOURCE / "preparation"
    bank = dict(np.load(prep / "bank.npz"))
    meta, storms = pd.read_parquet(prep / "cases.parquet"), pd.read_parquet(prep / "storms.parquet")
    representations = json.loads((prep / "manifest.json").read_text())["representations"]
    years = storms.cutoff_utc.dt.year.to_numpy()
    n = len(storms)
    area = meta.area_km2.to_numpy().reshape(n, 8)[0]
    y = bank["outcome_0"] * (3.6 / area)[None, :, None]
    legacy = load_script("164_diagnose_eo_signal.py", "signal_review_legacy_point")
    legacy.STATE.update(bank=bank, meta=meta, storms=storms, source=SOURCE)
    legacy_mae = {
        scenario: score_points(legacy.existing_point_fallback(scenario)[None], y)[0]
        for scenario in CFG["scenarios"]
    }
    ledger_path = SOURCE / "review/coverage-ledger.parquet"
    labels = pd.read_parquet(
        ledger_path, columns=["scenario", "offset_h", "case", "future_p99", "verification_clean"]
    )
    labels = labels[(labels.scenario == "rich_basin") & labels.offset_h.eq(0)].sort_values("case")
    high = labels.future_p99.to_numpy().reshape(n, 8)
    clean = labels.verification_clean.to_numpy().reshape(n, 8)
    reports, summary, overviews, associations, choices, opportunities = [], [], [], [], [], []
    inputs = {
        str(p.relative_to(ROOT)): sha256(p)
        for p in [
            Path(__file__),
            ROOT / "src/scarcity_review.py",
            ROOT / "scripts/164_diagnose_eo_signal.py",
            ledger_path,
            ROOT / "src/analogue_bootstrap.py",
        ]
    }
    # These saved trajectories are used for the early-record fallback and the
    # contextual point-mean benchmark, in addition to the immutable input bank.
    for scenario in CFG["scenarios"]:
        path = SOURCE / f"scores/{scenario}__u0/scores.parquet"
        inputs[str(path.relative_to(ROOT))] = sha256(path)
    for path in paths:
        data, tuning, audit = audit_job(path, meta, storms, bank, representations)
        reports.append(audit)
        manifest = json.loads((path / "manifest.json").read_text())
        inputs[str((path / "manifest.json").relative_to(ROOT))] = sha256(path / "manifest.json")
        model, kind = manifest["model"], manifest["readout"]
        overview = json.loads((path / "representation.json").read_text())
        overview["input_product"] = ROUTES[model][0]
        overview["patch_pixels"] = ROUTES[model][1]
        overviews.append(overview)
        associations.append(pd.read_csv(path / "representation-associations.csv"))
        for scenario in CFG["scenarios"]:
            pred = data[scenario + "_predictions"]
            mae, rmse = score_points(pred, y)
            supported = data[scenario + "_eo_supported"]
            active = data[scenario + "_eo_active"]
            crps = data[scenario + "_retrieval_crps"]
            populations = {
                "all": np.ones((n, 8), bool),
                "eo_supported": supported,
                "eo_active": active,
                "future_p99": high == 1,
                "clean_verification": clean,
            }
            for population, mask in populations.items():
                for score_name, values in [("MAE", mae), ("RMSE", rmse)]:
                    if score_name == "RMSE" and population != "all":
                        continue
                    effects = [
                        ("learned_real_minus_matched", values[2:3] - values[1:2], values[1:2]),
                        ("learned_real_minus_broad", values[2:3] - values[0:1], values[0:1]),
                        ("learned_matched_minus_broad", values[1:2] - values[0:1], values[0:1]),
                        ("learned_real_minus_shuffled", values[2:3] - values[3:], values[3:]),
                    ]
                    if score_name == "MAE":
                        effects.append(
                            (
                                "learned_real_minus_legacy_point_mean",
                                values[2:3] - legacy_mae[scenario],
                                legacy_mae[scenario],
                            )
                        )
                    for effect, difference, reference in effects:
                        v = np.where(mask[None], difference, np.nan).transpose(0, 2, 1)
                        ref = np.broadcast_to(reference, difference.shape).transpose(0, 2, 1)
                        metadata = dict(
                            model=model,
                            readout=kind,
                            scenario=scenario,
                            population=population,
                            metric=score_name,
                            effect=effect,
                        )
                        summary.append(summarize_effect(v, ref, years, metadata))
                if population in ["all", "future_p99"]:
                    for effect, difference, reference in [
                        ("retrieval_real_minus_matched", crps[1:2] - crps[0:1], crps[0:1]),
                        ("retrieval_real_minus_shuffled", crps[1:2] - crps[3:], crps[3:]),
                    ]:
                        v = np.where(mask[None], difference, np.nan).transpose(0, 2, 1)
                        ref = np.broadcast_to(reference, difference.shape).transpose(0, 2, 1)
                        summary.append(
                            summarize_effect(
                                v,
                                ref,
                                years,
                                dict(
                                    model=model,
                                    readout=kind,
                                    scenario=scenario,
                                    population=population,
                                    metric="empirical_CRPS",
                                    effect=effect,
                                ),
                            )
                        )
            opportunity = meta[["case_id", "gauge", "country", "storm_id", "cutoff_utc"]].copy()
            opportunity["model"], opportunity["readout"], opportunity["scenario"] = (
                model,
                kind,
                scenario,
            )
            opportunity["verification_available"] = bank["outcome_valid_0"].ravel()
            opportunity["learned_ground_prediction_available"] = (
                np.isfinite(pred[0]).all(axis=-1).ravel()
            )
            opportunity["eo_supported"] = supported.ravel()
            opportunity["eo_active"] = active.ravel()
            opportunity["future_p99"] = high.ravel()
            opportunity["real_MAE"] = mae[2].ravel()
            opportunity["matched_MAE"] = mae[1].ravel()
            opportunity["broad_MAE"] = mae[0].ravel()
            opportunity["legacy_mean_trajectory_MAE"] = legacy_mae[scenario][0].ravel()
            opportunity["shuffled_mean_MAE"] = mae[3:].mean(axis=0).ravel()
            opportunities.append(opportunity)
            choices.append(
                dict(
                    model=model,
                    readout=kind,
                    scenario=scenario,
                    eo_supported_cases=int(supported.sum()),
                    eo_active_cases=int(active.sum()),
                    active_fraction_of_supported=float(active.sum() / supported.sum())
                    if supported.any()
                    else np.nan,
                    scored_cases=int(np.isfinite(mae[2]).sum()),
                )
            )
        print("audited/reviewed", path.name, flush=True)
    target = OUT / ("benchmark_review" if args.benchmark else "review")
    with fresh_output(target) as work:
        frame = pd.DataFrame(summary)
        frame.to_csv(work / "paired-effects.csv", index=False)
        pd.DataFrame(choices).to_csv(work / "learned-weight-use.csv", index=False)
        pd.DataFrame(overviews).to_csv(work / "model-representation-inventory.csv", index=False)
        pd.concat(associations, ignore_index=True).to_csv(
            work / "representation-associations.csv", index=False
        )
        pd.concat(opportunities, ignore_index=True).to_parquet(
            work / "coverage-and-case-scores.parquet", index=False
        )
        (work / "audit.json").write_text(
            json.dumps(dict(status="passed", complete=not args.benchmark, jobs=reports), indent=2)
            + "\n"
        )
        primary = frame[
            (frame.metric == "MAE")
            & frame.population.eq("eo_supported")
            & frame.effect.eq("learned_real_minus_matched")
        ]
        lines = [
            "# Model-specific EO diagnostics",
            "",
            "Negative paired differences favor real EO. Point-head MAE and empirical-ensemble CRPS are different endpoints.",
            "Exploratory year-block intervals; the same historical outcomes were already inspected in earlier work.",
            "Per-gauge chronological fits control gauge identity; season/year/coverage metadata is shared across matched arms.",
            "The null controls preserve training quarters and draw test vectors only from earlier training archives.",
            "No encoder was trained or re-extracted. Native temporal and independent-frame-mean routes remain distinct.",
            "The original conventional ensemble mean is also scored as a point trajectory; do not compare its CRPS directly with head MAE.",
            "Model inventories describe heterogeneous held sensor/checkpoint/footprint routes, not an architecture-only leaderboard.",
            "",
            "| Model | Readout | Scenario | EO-supported MAE difference (%) | Interval (native normalized error) |",
            "| --- | --- | --- | ---: | --- |",
        ]
        for row in primary.itertuples():
            lines.append(
                f"| {row.model} | {row.readout} | {row.scenario} | {row.relative_difference_pct:.2f} | [{row.lower:.6g}, {row.upper:.6g}] |"
            )
        lines += [
            "",
            "Inspect real-minus-shuffled alongside real-minus-matched, absolute errors, support and zero-weight frequency.",
            "A learned increment does not establish a physical mechanism or operational warning benefit.",
            "A null result concerns the held pooled representation and these learned/fixed interfaces; it does not evaluate all fine-tuning or spatial pooling alternatives.",
        ]
        (work / "results-memo.md").write_text("\n".join(lines) + "\n")
        (work / "manifest.json").write_text(
            json.dumps(
                dict(
                    status="benchmark_only" if args.benchmark else "completed",
                    sources_sha256=inputs,
                    outputs_sha256={p.name: sha256(p) for p in work.iterdir()},
                    emails_sent=False,
                ),
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
