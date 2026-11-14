"""Prepare, fit or review the paired GEOGLOWS study; phases never auto-chain."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import runpy
import subprocess
import sys
import time
from pathlib import Path

# Two workers must not each spawn a full twelve-core BLAS team.
for name in [
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
]:
    os.environ[name] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.eo_event_inputs import completed_windows, context_id
from src.eo_individual_baselines import same_gauge_reference
from src.eo_individual_evaluation import (
    assessment_scores,
    common_context,
    feature_matrix,
    prediction_status,
)
from src.eo_individual_readout import prequential_heads
from src.eo_individual_review import paired_summary
from src.geoglows_experiment import (
    closed_before,
    disk_check,
    paired_summary_table,
    qm_apply,
    qm_fit,
    replace_histories,
    sha,
    write_json,
)

CONFIG = ROOT / "config/limburg_geoglows_stages12_v1.json"


def source_identity(plan):
    files = [
        CONFIG,
        Path(__file__),
        ROOT / "scripts/260_setup_geoglows_comparison.py",
        ROOT / "src/geoglows_experiment.py",
        ROOT / "src/eo_individual_baselines.py",
        ROOT / "src/eo_individual_readout.py",
        ROOT / "src/eo_individual_evaluation.py",
        ROOT / "src/eo_individual_review.py",
        ROOT / "src/scarcity.py",
        ROOT / "src/eo_event_inputs.py",
        ROOT / "scripts/162_review_scarcity.py",
        ROOT / "config/limburg_geoglows_reaches_v1.json",
        ROOT / plan["raw"] / "download_manifest.json",
        ROOT / plan["raw"] / "mapping_audit.json",
        ROOT / plan["raw"] / "hourly_discharge.parquet",
        ROOT / plan["source"] / "bank.npz",
        ROOT / plan["source"] / "cases.parquet",
        ROOT / plan["source"] / "source_epoch_hours.npy",
        ROOT / "results/storm_response/hourly_discharge.parquet",
        ROOT / "results/storm_response/hourly_normalizer.parquet",
        ROOT / "results/storm_response/hourly_strict.parquet",
        ROOT / "results/storm_response/hourly_domain.parquet",
        ROOT / "results/flood_case_review_2026_10_27/register.parquet",
    ]
    for site in ["sint_pieter", "venlo"]:
        files.append(ROOT / f"results/meuse_context_2026_10_27/{site}_hourly.parquet")
    for model in plan["models"]:
        d = ROOT / "results/limburg_individual_experiments_v1/features" / model
        files.extend([d / "manifest.json", d / "context_features.parquet"])
    return {str(p.relative_to(ROOT)): sha(p) for p in files}


def verify_receipt(path):
    record = json.loads(path.read_text())
    for name, digest in record["outputs"].items():
        if sha(path.parent / name) != digest:
            raise ValueError(f"Output changed: {path.parent / name}")
    for name, digest in record["source_hashes"].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f"Input/code changed: {name}; version the experiment")
    return record


def prepare(plan):
    dest = ROOT / plan["output"] / "preparation"
    dest.mkdir(parents=True, exist_ok=True)
    final = dest / "manifest.json"
    if final.exists():
        verify_receipt(final)
        print("Verified existing paired preparation")
        return
    identity = source_identity(plan)
    source = ROOT / plan["source"]
    all_bank = dict(np.load(source / "bank.npz"))
    names = [
        f"{prefix}_{u}"
        for u in plan["issue_offsets_h"]
        for prefix in [
            "q",
            "donor_q",
            "positions",
            "outcome",
            "outcome_valid",
            "outcome_quality",
            "input_quality",
        ]
    ]
    names += [
        f"{prefix}_{u}_0"
        for u in plan["issue_offsets_h"]
        for prefix in ["prior", "q_mean", "q_pairvar", "rain_mean", "rain_var"]
    ]
    names += [f"rain_{u}_1_0" for u in plan["issue_offsets_h"]]
    bank = {name: all_bank[name] for name in names}
    epochs = np.load(source / "source_epoch_hours.npy")
    hourly = pd.read_parquet(ROOT / plan["raw"] / "hourly_discharge.parquet")
    hourly.columns = range(10)
    alternate = replace_histories(bank, hourly, epochs, plan["issue_offsets_h"])
    # Reference hourly calibration observations are never model input in Stage 2.
    observed = pd.read_parquet(ROOT / "results/storm_response/hourly_discharge.parquet")
    strict = pd.read_parquet(ROOT / "results/storm_response/hourly_strict.parquet").fillna(False)
    domain = pd.read_parquet(ROOT / "results/storm_response/hourly_domain.parquet").fillna(False)
    observed = observed.where(strict & domain)
    for site in ["sint_pieter", "venlo"]:
        observed[site] = pd.read_parquet(
            ROOT / f"results/meuse_context_2026_10_27/{site}_hourly.parquet"
        ).q_strict.reindex(observed.index)
    observed.columns = range(10)
    observed.to_parquet(dest / "calibration_observed.parquet")
    np.save(dest / "epochs.npy", epochs)
    for name, values in [("observed", bank), ("geoglows", alternate)]:
        with (dest / f"{name}_bank.npz").open("wb") as stream:
            np.savez_compressed(stream, **values)
    meta = pd.read_parquet(source / "cases.parquet")
    label_fn = runpy.run_path(str(ROOT / "scripts/162_review_scarcity.py"))["labels"]
    normalizer = pd.read_parquet(ROOT / "results/storm_response/hourly_normalizer.parquet")
    register = pd.read_parquet(ROOT / "results/flood_case_review_2026_10_27/register.parquet")
    frames = []
    for u in plan["issue_offsets_h"]:
        frame = meta.copy()
        frame["query"] = np.arange(len(frame)) // 8
        frame["site"] = np.arange(len(frame)) % 8
        frame["offset_h"] = u
        frame["issue_utc"] = frame.cutoff_utc + pd.Timedelta(hours=u)
        frame["response_end_utc"] = frame.issue_utc + pd.Timedelta(hours=24)
        frame["assessment_id"] = [f"u{u}__{v}" for v in frame.case_id]
        frame["outcome_valid"] = bank[f"outcome_valid_{u}"].ravel()
        frame["local_model_reach_mapped"] = frame.site.isin(plan["mapped_target_channels"])
        labels = label_fn(all_bank, meta, u, normalizer, register)
        for column in ["future_p99", "verification_clean", "documented_flood_overlap"]:
            frame[column] = labels[column].to_numpy()
        for stage, values in [("observed", bank), ("geoglows", alternate)]:
            q = values[f"q_{u}"]
            frame[f"{stage}_local_history_fraction"] = np.isfinite(q[:, :8]).mean(2).ravel()
            frame[f"{stage}_network_history_fraction"] = np.repeat(np.isfinite(q).mean((1, 2)), 8)
        frames.append(frame)
        for prefix in ["outcome", "outcome_valid", "outcome_quality", "rain"]:
            key = f"{prefix}_{u}_1_0" if prefix == "rain" else f"{prefix}_{u}"
            np.testing.assert_array_equal(bank[key], alternate[key])
    cases = pd.concat(frames, ignore_index=True)
    if not cases.assessment_id.is_unique or len(cases) != len(meta) * 4:
        raise ValueError("Paired census incomplete or duplicated")
    cases.to_parquet(dest / "cases.parquet", index=False)
    cases.groupby(["gauge", "country"]).agg(
        assessments=("assessment_id", "size"),
        verification=("outcome_valid", "sum"),
        model_history_fraction=("geoglows_local_history_fraction", "mean"),
    ).to_csv(dest / "coverage.csv")
    write_json(
        final,
        dict(
            status="prepared_not_fitted",
            rows=len(cases),
            storms=cases.storm_id.nunique(),
            source_hashes=identity,
            outputs={p.name: sha(p) for p in dest.iterdir() if p.is_file() and p != final},
            git_commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            clock=plan["clock"],
            no_new_empirical_result=True,
        ),
    )
    print("Prepared", len(cases), "matched opportunities per stage, no fitting")


def calibrated_bank(bank, curves, epochs, offsets):
    from src.scarcity import forward_hold

    result = dict(bank)
    for u in offsets:
        q = bank[f"q_{u}"]
        months = (
            pd.to_datetime(epochs[bank[f"positions_{u}"]].ravel(), unit="h", utc=True)
            .month.to_numpy()
            .reshape(q.shape[0], 72)
        )
        corrected = np.full_like(q, np.nan)
        for channel in range(10):
            for month in np.unique(months):
                use = months == month
                corrected[:, channel][use] = qm_apply(
                    q[:, channel][use], int(month), curves[(channel, int(month))]
                )
        result[f"q_{u}"] = corrected
        result[f"donor_q_{u}"] = forward_hold(corrected)
    return result


def baselines(plan, stage, prep, cases):
    """Fixed-year archive for all arms; prior labels/normalization only."""
    dest = ROOT / plan["output"] / "baselines" / stage
    dest.mkdir(parents=True, exist_ok=True)
    final = dest / "manifest.json"
    if final.exists():
        verify_receipt(final)
        return
    bank = dict(np.load(prep / f"{stage}_bank.npz"))
    epochs = np.load(prep / "epochs.npy")
    hourly = pd.read_parquet(ROOT / plan["raw"] / "hourly_discharge.parquet")
    hourly.columns = range(10)
    observed_calibration = pd.read_parquet(prep / "calibration_observed.parquet")
    observed_calibration.columns = range(10)
    n = len(cases)
    values = {
        name: np.full((n, 24), np.nan)
        for name in [
            "conventional_mean",
            "conventional_median",
            "input_persistence",
            "monthly_qm_persistence",
            "monthly_qm_analogue",
        ]
    }
    donors = np.full((n, 5), -1, dtype=np.int32)
    kinds, calibration_log = [], []
    began = time.monotonic()
    for year in sorted(cases.issue_utc.dt.year.unique()):
        disk_check(ROOT, plan["free_space_reserve_gib"])
        boundary = pd.Timestamp(f"{year}-01-01", tz="UTC")
        curves = (
            qm_fit(hourly, observed_calibration, range(1, 13), boundary)
            if stage == "geoglows"
            else None
        )
        cb = calibrated_bank(bank, curves, epochs, plan["issue_offsets_h"]) if curves else bank
        if curves:
            for (channel, month), curve in curves.items():
                calibration_log.append(
                    dict(
                        year=int(year),
                        channel=channel,
                        month=month,
                        available=curve is not None,
                        **(
                            {
                                k: v.tolist() if isinstance(v, np.ndarray) else v
                                for k, v in curve.items()
                            }
                            if curve
                            else {}
                        ),
                    )
                )
        for u in plan["issue_offsets_h"]:
            subset = cases[cases.offset_h.eq(u)]
            prior = closed_before(subset.iloc[::8], int(year))
            ids = cases.index[cases.issue_utc.dt.year.eq(year) & cases.offset_h.eq(u)]
            for i in ids:
                row = cases.loc[i]
                qi, gi = int(row.query), int(row.site)
                a, b, selected, kind = same_gauge_reference(bank, qi, gi, u, "rich_basin", prior)
                c, _, _, _ = same_gauge_reference(cb, qi, gi, u, "rich_basin", prior)
                factor = 3.6 / row.area_km2
                values["conventional_mean"][i] = a * factor
                values["conventional_median"][i] = b * factor
                values["monthly_qm_analogue"][i] = c * factor
                donors[i, : len(selected)] = selected
                # Strict latest-hour persistence: no silent hold through a gap.
                values["input_persistence"][i] = bank[f"q_{u}"][qi, gi, -1] * factor
                values["monthly_qm_persistence"][i] = cb[f"q_{u}"][qi, gi, -1] * factor
                kinds.append(dict(assessment_id=row.assessment_id, reference_kind=kind))
        write_json(
            dest / "progress.json",
            dict(status="running", completed_year=int(year), elapsed_s=time.monotonic() - began),
        )
        print(stage, "baselines through", year, flush=True)
    np.savez_compressed(dest / "predictions.npz", **values, donors=donors)
    pd.DataFrame(kinds).to_parquet(dest / "reference_modes.parquet", index=False)
    write_json(dest / "calibration.json", calibration_log)
    write_json(
        final,
        dict(
            status="completed",
            source_hashes=source_identity(plan),
            outputs={
                name: sha(dest / name)
                for name in ["predictions.npz", "reference_modes.parquet", "calibration.json"]
            },
            elapsed_s=time.monotonic() - began,
        ),
    )


def score(plan, stage, model):
    prep = ROOT / plan["output"] / "preparation"
    verify_receipt(prep / "manifest.json")
    dest = ROOT / plan["output"] / "scores" / f"{stage}__{model}"
    dest.mkdir(parents=True, exist_ok=True)
    final = dest / "manifest.json"
    if final.exists():
        verify_receipt(final)
        return
    cases = pd.read_parquet(prep / "cases.parquet")
    bank = dict(np.load(prep / f"{stage}_bank.npz"))
    baseline_path = ROOT / plan["output"] / "baselines" / stage
    verify_receipt(baseline_path / "manifest.json")
    predictions = {
        k: v for k, v in dict(np.load(baseline_path / "predictions.npz")).items() if k != "donors"
    }
    n = len(cases)
    observed = np.full((n, 24), np.nan)
    for i, row in enumerate(cases.itertuples()):
        observed[i] = bank[f"outcome_{row.offset_h}"][row.query, row.site] * 3.6 / row.area_km2
    feature_dir = ROOT / "results/limburg_individual_experiments_v1/features" / model
    features = pd.read_parquet(feature_dir / "context_features.parquet").set_index(
        ["context_id", "catchment_gauge"]
    )
    if not features.index.is_unique:
        raise ValueError("Duplicate encoder context")
    kind = "monthly" if model == "presto" else "recent"
    contexts = cases.cutoff_utc.map(lambda t: context_id(kind, completed_windows(t, kind)))
    aligned = features.reindex(
        pd.MultiIndex.from_arrays([contexts, cases.catchment_gauge])
    ).reset_index(drop=True)
    raw = feature_matrix(aligned, ["raw", "context", "climate", "terrain"])
    encoded = feature_matrix(aligned, ["primary"])
    if not encoded.shape[1] or not raw.shape[1]:
        raise ValueError("Missing declared raw/encoder features")
    raw_ok = np.isfinite(raw).any(1)
    eo_ok = np.isfinite(encoded).any(1) & (np.nansum(encoded**2, axis=1) > 0)
    # Coverage and age are shared by both satellite arms; hydro-only sees neither.
    area_cols = [c for c in aligned if "_area_" in c]
    coverage = aligned[area_cols].to_numpy(float) / (cases.area_km2.to_numpy()[:, None] * 1e6)
    ages = [
        (
            r.issue_utc - pd.Timestamp(completed_windows(r.cutoff_utc, kind)[-1]["end"])
        ).total_seconds()
        / 86400
        for r in cases.itertuples()
    ]
    raw = np.column_stack([raw, coverage, ages, raw_ok, eo_ok])
    predictions.update(
        {
            k: predictions["conventional_mean"].copy()
            for k in ["hydro_correction", "raw_correction", "encoder_correction"]
        }
    )
    tuning = []
    modes = dict(
        training_count=np.zeros(n, int),
        raw_prediction_mode=np.full(n, "conventional", object),
        encoder_prediction_mode=np.full(n, "conventional", object),
    )
    began = time.monotonic()
    for gi in range(8):
        ids = np.flatnonzero(cases.site.eq(gi))
        local = cases.iloc[ids].reset_index(drop=True)
        zeros = np.zeros(len(ids), bool)
        common, rain24 = common_context(bank, local, "rich_basin", None, zeros, zeros)
        base = predictions["conventional_mean"][ids]
        common = np.column_stack([common, base])
        conditions = np.column_stack([rain24, np.mean(base, axis=1)])
        years = local.issue_utc.dt.year.to_numpy()
        ready = local.outcome_valid.to_numpy(bool) & np.isfinite(observed[ids]).all(1)
        args = (
            conditions,
            observed[ids],
            base,
            years,
            ready,
            lambda y, rows=local: closed_before(rows, y),
            local.storm_id.to_numpy(),
        )
        empty = np.empty((len(ids), 0))
        hydro, _, records = prequential_heads(
            common,
            empty,
            empty,
            *args,
            np.ones(len(ids), bool),
            np.zeros(len(ids), bool),
            eo_weights=(),
        )
        r, e, extra = prequential_heads(
            common, raw[ids], encoded[ids], *args, raw_ok[ids], eo_ok[ids]
        )
        predictions["hydro_correction"][ids] = hydro
        predictions["raw_correction"][ids] = r
        predictions["encoder_correction"][ids] = e
        for key, values in prediction_status(extra, years, raw_ok[ids], eo_ok[ids]).items():
            modes[key][ids] = values
        tuning.extend([dict(gauge=str(local.gauge.iloc[0]), arm="hydro", **x) for x in records])
        tuning.extend([dict(gauge=str(local.gauge.iloc[0]), arm="satellite", **x) for x in extra])
        write_json(
            dest / "progress.json",
            dict(
                status="running",
                gauges_done=gi + 1,
                gauges_total=8,
                elapsed_s=time.monotonic() - began,
            ),
        )
        print(stage, model, gi + 1, "/8 gauges", flush=True)
    cases["raw_available"] = raw_ok
    cases["encoder_available"] = eo_ok
    for key, values in modes.items():
        cases[key] = values
    cases.to_parquet(dest / "cases.parquet", index=False)
    frames = []
    for method, prediction in predictions.items():
        f = cases.copy()
        # Unsupported/invalid observed outcomes are unscored, never zero loss.
        scored_y = np.where(cases.outcome_valid.to_numpy()[:, None], observed, np.nan)
        for name, value in assessment_scores(scored_y, prediction).items():
            f[name] = value
        for field in ["mae", "rmse", "peak_error"]:
            f[field + "_m3s"] = f[field] * f.area_km2 / 3.6
        f["method"] = method
        frames.append(f)
    pd.concat(frames, ignore_index=True).to_parquet(dest / "scores.parquet", index=False)
    np.savez_compressed(dest / "predictions.npz", observed=observed, **predictions)
    write_json(dest / "tuning.json", tuning)
    identity = source_identity(plan)
    for path in [prep / "manifest.json", baseline_path / "manifest.json"]:
        identity[str(path.relative_to(ROOT))] = sha(path)
    write_json(
        final,
        dict(
            status="completed",
            stage=stage,
            model=model,
            rows=n,
            elapsed_s=time.monotonic() - began,
            source_hashes=identity,
            outputs={
                p: sha(dest / p)
                for p in ["cases.parquet", "scores.parquet", "predictions.npz", "tuning.json"]
            },
        ),
    )


def review(plan):
    out = ROOT / plan["output"]
    cases = pd.read_parquet(out / "preparation/cases.parquet")
    years = sorted(cases.cutoff_utc.dt.year.unique())
    rng = np.random.default_rng(plan["seed"])
    draws = np.stack(
        [
            np.bincount(rng.integers(len(years), size=len(years)), minlength=len(years))
            for _ in range(plan["bootstrap_draws"])
        ]
    )
    review_dir = out / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    summaries, changes, interactions, event_rows = [], [], [], []
    for model in plan["models"]:
        stage_losses = {}
        for stage in plan["stages"]:
            path = out / "scores" / f"{stage}__{model}"
            verify_receipt(path / "manifest.json")
            p = dict(np.load(path / "predictions.npz"))
            local = pd.read_parquet(path / "cases.parquet")
            if not local.assessment_id.equals(cases.assessment_id):
                raise ValueError("Stage/model assessment order changed")
            table = paired_summary_table(local, p, years, draws)
            table["stage"], table["model"] = stage, model
            summaries.append(table)
            losses = {}
            for method, pred in p.items():
                if method == "observed":
                    continue
                use = (
                    np.isfinite(pred).all(1)
                    & np.isfinite(p["observed"]).all(1)
                    & cases.outcome_valid.to_numpy(bool)
                )
                loss = np.where(use, np.abs(pred - p["observed"]).mean(1), np.nan)
                losses[method] = loss
                f = cases[
                    [
                        "assessment_id",
                        "gauge",
                        "storm_id",
                        "issue_utc",
                        "future_p99",
                        "documented_flood_overlap",
                    ]
                ].copy()
                f["mae_mm_h"], f["method"], f["stage"], f["model"] = loss, method, stage, model
                f["mae_m3s"] = loss * cases.area_km2.to_numpy() / 3.6
                event_rows.append(f)
            stage_losses[stage] = losses
        for method in stage_losses["observed"]:
            difference = stage_losses["geoglows"][method] - stage_losses["observed"][method]
            mapped = cases.local_model_reach_mapped.to_numpy(bool)
            for subset, mask in [
                ("mapped_targets_primary", mapped),
                ("whole_network_pipeline", np.ones(len(cases), bool)),
                ("unmapped_eys_coverage_case", ~mapped),
                ("mapped_high_water", mapped & cases.future_p99.eq(1).to_numpy()),
            ]:
                changes.append(
                    dict(
                        model=model,
                        method=method,
                        subset=subset,
                        **paired_summary(cases, np.where(mask, difference, np.nan), years, draws),
                    )
                )
        # Compare encoder increments themselves on four-arm paired support;
        # different significance labels in separate stages are not interaction.
        increment = {
            stage: losses["encoder_correction"] - losses["raw_correction"]
            for stage, losses in stage_losses.items()
        }
        delta = increment["geoglows"] - increment["observed"]
        for subset, mask in [
            ("mapped_targets", cases.local_model_reach_mapped.to_numpy(bool)),
            ("whole_network_pipeline", np.ones(len(cases), bool)),
        ]:
            interactions.append(
                dict(
                    model=model,
                    subset=subset,
                    **paired_summary(cases, np.where(mask, delta, np.nan), years, draws),
                )
            )
    pd.concat(summaries, ignore_index=True).to_csv(
        review_dir / "within_stage_effects.csv", index=False
    )
    pd.DataFrame(changes).to_csv(review_dir / "source_effects.csv", index=False)
    pd.DataFrame(interactions).to_csv(review_dir / "source_by_encoder_interaction.csv", index=False)
    pd.concat(event_rows, ignore_index=True).to_parquet(
        review_dir / "all_event_errors.parquet", index=False
    )
    np.savez_compressed(review_dir / "bootstrap.npz", years=years, multiplicities=draws)
    review_inputs = source_identity(plan)
    for stage in plan["stages"]:
        for model in plan["models"]:
            path = out / "scores" / f"{stage}__{model}" / "manifest.json"
            review_inputs[str(path.relative_to(ROOT))] = sha(path)
    write_json(
        review_dir / "manifest.json",
        dict(
            status="completed",
            source_hashes=review_inputs,
            outputs={
                p.name: sha(p)
                for p in review_dir.iterdir()
                if p.is_file() and p.name != "manifest.json"
            },
            interpretation="Retrospective information-content comparison, not as-issued warning skill",
        ),
    )


def audit(plan):
    """Full-census input audit plus a timed baseline check, no model fitting."""
    prep = ROOT / plan["output"] / "preparation"
    verify_receipt(prep / "manifest.json")
    cases = pd.read_parquet(prep / "cases.parquet")
    source = dict(np.load(ROOT / plan["source"] / "bank.npz"))
    banks = {stage: dict(np.load(prep / f"{stage}_bank.npz")) for stage in plan["stages"]}
    epochs = np.load(prep / "epochs.npy")
    hourly = pd.read_parquet(ROOT / plan["raw"] / "hourly_discharge.parquet")
    expected = hourly.reindex(pd.to_datetime(epochs, unit="h", utc=True)).to_numpy(float)
    verified = 0
    for u in plan["issue_offsets_h"]:
        local = cases[cases.offset_h.eq(u)].iloc[::8]
        positions = source[f"positions_{u}"]
        issue = (
            local.issue_utc.dt.as_unit("ns").astype("int64").to_numpy()
            // pd.Timedelta(hours=1).value
        )
        np.testing.assert_array_equal(epochs[positions][:, -1], issue)
        np.testing.assert_array_equal(
            np.diff(epochs[positions], axis=1), np.ones((len(local), 71), int)
        )
        np.testing.assert_array_equal(
            banks["geoglows"][f"q_{u}"], expected[positions].transpose(0, 2, 1)
        )
        np.testing.assert_array_equal(banks["observed"][f"q_{u}"], source[f"q_{u}"])
        assert np.isnan(banks["geoglows"][f"q_{u}"][:, 0]).all(), "Eys must remain unmapped"
        for prefix in ["outcome", "outcome_valid", "outcome_quality"]:
            np.testing.assert_array_equal(
                banks["observed"][f"{prefix}_{u}"], banks["geoglows"][f"{prefix}_{u}"]
            )
        np.testing.assert_array_equal(
            banks["observed"][f"rain_{u}_1_0"], banks["geoglows"][f"rain_{u}_1_0"]
        )
        verified += len(local) * 8
    # Timed, deterministic engineering checks; no scores or model selection.
    began = time.monotonic()
    checked = 0
    for i in np.linspace(0, len(cases) - 1, 16, dtype=int):
        row = cases.iloc[i]
        subset = cases[cases.offset_h.eq(row.offset_h)].iloc[::8]
        prior = closed_before(subset, row.issue_utc.year)
        old = same_gauge_reference(
            source, int(row.query), int(row.site), int(row.offset_h), "rich_basin", prior
        )
        new = same_gauge_reference(
            banks["observed"], int(row.query), int(row.site), int(row.offset_h), "rich_basin", prior
        )
        for a, b in zip(old[:3], new[:3], strict=True):
            np.testing.assert_array_equal(a, b)
        same_gauge_reference(
            banks["geoglows"], int(row.query), int(row.site), int(row.offset_h), "rich_basin", prior
        )
        checked += 2
    elapsed = time.monotonic() - began
    write_json(
        ROOT / plan["output"] / "setup_audit.json",
        dict(
            status="passed",
            assessed_opportunities_per_stage=verified,
            baseline_checks=checked,
            baseline_check_elapsed_s=elapsed,
            rough_uncalibrated_baseline_projection_s=elapsed / checked * len(cases) * 2,
            fitted_models=0,
            all_outcomes_and_rain_unchanged=True,
            all_ten_stage2_channels_checked=True,
            no_future_hour_in_inputs=True,
            unmapped_eys_not_substituted=True,
            preparation_sha256=sha(prep / "manifest.json"),
            note="Timing check is engineering only; no held-out performance claim.",
        ),
    )
    print("Full input audit passed:", verified, "opportunities per stage; no models fitted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "audit", "run", "review", "score"])
    parser.add_argument("--stage", choices=["observed", "geoglows"])
    parser.add_argument("--model", choices=["presto", "anysat"])
    args = parser.parse_args()
    plan = json.loads(CONFIG.read_text())
    disk_check(ROOT, plan["free_space_reserve_gib"], 2 * 2**30)
    out = ROOT / plan["output"]
    out.mkdir(parents=True, exist_ok=True)
    # One controller; child scoring jobs have disjoint output directories.
    with (
        out / (f".{args.stage}_{args.model}.lock" if args.phase == "score" else ".controller.lock")
    ).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.phase == "prepare":
            prepare(plan)
        elif args.phase == "audit":
            audit(plan)
        elif args.phase == "review":
            review(plan)
        elif args.phase == "score":
            if not args.stage or not args.model:
                parser.error("score requires --stage and --model")
            score(plan, args.stage, args.model)
        else:
            verify_receipt(out / "preparation/manifest.json")
            cases = pd.read_parquet(out / "preparation/cases.parquet")
            for stage in plan["stages"]:
                baselines(plan, stage, out / "preparation", cases)
            # Two CPU jobs, no GPU extraction; complete both models/stages.
            jobs = [(stage, model) for stage in plan["stages"] for model in plan["models"]]
            log_dir = ROOT / "logs/limburg_geoglows_stages12_v1"
            log_dir.mkdir(parents=True, exist_ok=True)
            for start in range(0, len(jobs), plan["max_cpu_workers"]):
                running = []
                for stage, model in jobs[start : start + plan["max_cpu_workers"]]:
                    stream = (log_dir / f"{stage}__{model}.log").open("a")
                    child = subprocess.Popen(
                        [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "score",
                            "--stage",
                            stage,
                            "--model",
                            model,
                        ],
                        cwd=ROOT,
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                    )
                    running.append((child, stream))
                codes = []
                for child, stream in running:
                    codes.append(child.wait())
                    stream.close()
                if any(codes):
                    raise RuntimeError(f"Scoring worker failed, outputs retained: {codes}")
            print("All Stages 1–2 fits complete. Run review explicitly.")


if __name__ == "__main__":
    main()
