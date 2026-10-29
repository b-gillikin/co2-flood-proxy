"""Fit and audit model-specific residual probes on the complete prepared census."""

from __future__ import annotations

import argparse
import json
import runpy
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_event_inputs import completed_windows, context_id
from src.eo_individual_evaluation import (
    assessment_scores,
    common_context,
    feature_matrix,
    prediction_status,
)
from src.eo_individual_readout import prequential_heads
from src.eo_inputs import sha256

OUT = ROOT / "results/limburg_individual_experiments_v1"


def atomic_json(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_suffix(".tmp")
    t.write_text(json.dumps(value, indent=2) + "\n")
    t.replace(p)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--engineering",
        action="store_true",
        help="Isolated full-ledger plumbing check using one-patch features; never scientific results",
    )
    parser.add_argument(
        "--ablation",
        action="store_true",
        help="Matched configuration comparison, primary scenario only",
    )
    parser.add_argument(
        "--scenario", choices=["rich_basin", "local_q_absent", "all_q_absent"], required=True
    )
    args = parser.parse_args()
    if args.model == "dofa":
        from src.eo_individual_transfer import run_transfer

        assert not args.engineering, "DOFA uses the tested transfer exclusion fixture"
        assert not args.ablation, "DOFA has no configuration ablation"
        return run_transfer(ROOT, args.scenario)
    plan_path = ROOT / "config/limburg_individual_encoder_experiments_v1.json"
    plan = json.loads(plan_path.read_text())
    prep = OUT / "preparation"
    manifest = json.loads((prep / "manifest.json").read_text())
    for p, h in manifest["outputs"].items():
        assert sha256(prep / p) == h, "Prepared references changed"
    feature_root = OUT / "features" / args.model
    if args.engineering:
        candidates = list((OUT / "engineering" / args.model).glob("*/smoke.json"))
        assert candidates, "Run the model conformance fixture first"
        feature_root = max(candidates, key=lambda p: p.stat().st_mtime_ns).parent
    feature_receipt = feature_root / ("smoke.json" if args.engineering else "manifest.json")
    fm = json.loads(feature_receipt.read_text())
    feature_path = feature_root / "context_features.parquet"
    assert fm["status"] == "completed"
    if not args.engineering:
        assert sha256(feature_path) == fm["outputs"]["context_features.parquet"]
    job_name = f"{args.model}__{args.scenario}" + ("__ablation" if args.ablation else "")
    dest = OUT / ("engineering_scores" if args.engineering else "scores") / job_name
    dest.mkdir(parents=True, exist_ok=True)
    source = ROOT / plan["shared"]["source"] / "preparation"
    paths = [
        plan_path,
        prep / "manifest.json",
        feature_receipt,
        feature_path,
        Path(__file__),
        ROOT / "src/eo_individual_readout.py",
        ROOT / "src/eo_individual_evaluation.py",
        ROOT / "scripts/162_review_scarcity.py",
        ROOT / "results/storm_response/hourly_normalizer.parquet",
        ROOT / "results/flood_case_review_2026_10_27/register.parquet",
        source / "manifest.json",
    ]
    identity = {str(p.relative_to(ROOT)): sha256(p) for p in paths}
    final = dest / "manifest.json"
    if final.exists():
        saved = json.loads(final.read_text())
        assert saved["source_hashes"] == identity, (
            "Use a versioned score path for changed code/features"
        )
        for p, h in saved["outputs"].items():
            assert sha256(dest / p) == h
        print("Verified existing job")
        return
    cases = pd.read_parquet(prep / "cases.parquet")
    cases = cases[cases.scenario.eq(args.scenario)].copy().reset_index(drop=True)
    bank = dict(np.load(source / "bank.npz"))
    refs = dict(np.load(prep / "reference.npz"))
    features = pd.read_parquet(feature_path)
    features = features.set_index(["context_id", "catchment_gauge"])
    assert features.index.is_unique
    kind = fm.get("kind") or (
        "monthly"
        if args.model in ["presto", "galileo"]
        else "monthly_snapshot"
        if args.model == "satmae"
        else "recent"
    )
    window_end = cases.cutoff_utc.map(lambda t: pd.Timestamp(completed_windows(t, kind)[-1]["end"]))
    cases["eo_context_age_days"] = (cases.issue_utc - window_end).dt.total_seconds() / 86400
    assert (cases.eo_context_age_days >= 0).all()
    if kind == "monthly":
        contexts = cases.cutoff_utc.map(lambda t: context_id(kind, completed_windows(t, kind)))
    else:
        contexts = cases[kind + "_context_id"]
    aligned = features.reindex(
        pd.MultiIndex.from_arrays([contexts, cases.catchment_gauge])
    ).reset_index(drop=True)
    primary = feature_matrix(
        aligned, ["paired_primary" if args.ablation and args.model == "galileo" else "primary"]
    )
    ablated = feature_matrix(aligned, ["ablation"]) if args.ablation else None
    if args.ablation:
        assert args.scenario == "local_q_absent", (
            "One declared ablation, not another scenario sweep"
        )
        assert ablated.shape[1] and primary.shape[1], "Declared ablation features missing"
    raw = feature_matrix(aligned, ["raw", "context", "climate", "terrain"])
    rarea = [c for c in aligned if c.startswith(("raw_area_", "climate_area_", "terrain_area_"))]
    raw_available = (
        np.nan_to_num(aligned[rarea].to_numpy(float), nan=0).max(1) > 0
        if rarea
        else np.zeros(len(cases), bool)
    )
    eo_available = np.isfinite(primary).any(1) & (np.nansum(primary**2, axis=1) > 0)
    paired_support = eo_available.copy()
    if args.ablation:
        paired_support &= np.isfinite(ablated).any(1) & (np.nansum(ablated**2, axis=1) > 0)
        raw_available &= paired_support
        eo_available = paired_support.copy()
    cover_columns = sorted(c for c in aligned if "_area_" in c)
    coverage = (
        aligned[cover_columns].to_numpy(float) / (cases.area_km2.to_numpy()[:, None] * 1e6)
        if cover_columns
        else None
    )
    n = len(cases)
    observed = np.full((n, 24), np.nan)
    prediction = {
        name: np.full((n, 24), np.nan)
        for name in [
            "conventional_mean",
            "conventional_median",
            "fixed_year_mean",
            "fixed_year_median",
            "raw_correction",
            "encoder_correction",
        ]
    }
    if args.ablation:
        prediction["ablation_correction"] = np.full((n, 24), np.nan)
    for i, row in enumerate(cases.itertuples()):
        qi, gi, u = int(row.query), int(row.site), int(row.offset_h)
        key = f"{args.scenario}__u{u}"
        observed[i] = bank[f"outcome_{u}"][qi, gi] * 3.6 / row.area_km2
        for label, suffix in [
            ("conventional_mean", "mean"),
            ("conventional_median", "median"),
            ("fixed_year_mean", "fixed_mean"),
            ("fixed_year_median", "fixed_median"),
        ]:
            prediction[label][i] = refs[key + "__" + suffix][qi, gi]
    # Quality/high-water/flood labels are added only after predictor construction.
    baseline = prediction["conventional_mean"]
    tuning = []
    ledger = dict(
        training_count=np.zeros(n, int),
        raw_prediction_mode=np.full(n, "conventional", object),
        encoder_prediction_mode=np.full(n, "conventional", object),
    )
    began = time.time()
    for gi in range(8):
        ids = np.flatnonzero(cases.site.eq(gi).to_numpy())
        local = cases.iloc[ids].reset_index(drop=True)
        common, rain24 = common_context(
            bank,
            local,
            args.scenario,
            None,
            raw_available[ids],
            eo_available[ids],
            coverage[ids] if coverage is not None else None,
        )
        common = np.column_stack([common, baseline[ids]])
        conditions = np.column_stack([rain24, np.mean(baseline[ids], axis=1)])
        issues = pd.to_datetime(local.issue_utc, utc=True)
        years = issues.dt.year.to_numpy()
        ends = pd.to_datetime(local.end_utc, utc=True) + pd.Timedelta(hours=12)
        labels_end = pd.to_datetime(local.response_end_utc, utc=True)

        def closed_before(year, ends=ends, labels_end=labels_end):
            boundary = pd.Timestamp(f"{year}-01-01", tz="UTC")
            return ((ends <= boundary) & (labels_end <= boundary)).to_numpy()

        ready = local.outcome_valid.to_numpy(bool) & np.isfinite(observed[ids]).all(1)

        def report_fold(record, gauge=str(local.gauge.iloc[0]), gi=gi):
            atomic_json(
                dest / "progress.json",
                dict(
                    status="running",
                    model=args.model,
                    scenario=args.scenario,
                    gauge=gauge,
                    year=record["year"],
                    gauges_done=gi,
                    gauges_total=8,
                    elapsed_s=time.time() - began,
                ),
            )

        r, e, records = prequential_heads(
            common,
            raw[ids],
            primary[ids],
            conditions,
            observed[ids],
            baseline[ids],
            years,
            ready,
            closed_before,
            local.storm_id.to_numpy(),
            raw_available[ids],
            eo_available[ids],
            progress=report_fold,
        )
        if args.ablation:
            ar, ae, ablation_records = prequential_heads(
                common,
                raw[ids],
                ablated[ids],
                conditions,
                observed[ids],
                baseline[ids],
                years,
                ready,
                closed_before,
                local.storm_id.to_numpy(),
                raw_available[ids],
                eo_available[ids],
                progress=report_fold,
            )
            np.testing.assert_allclose(ar, r, rtol=1e-10, atol=1e-12, equal_nan=True)
            prediction["ablation_correction"][ids] = ae
            for record in ablation_records:
                record.update(gauge=str(local.gauge.iloc[0]), variant="ablation")
                tuning.append(record)
        for key, values in prediction_status(
            records, years, raw_available[ids], eo_available[ids]
        ).items():
            ledger[key][ids] = values
        prediction["raw_correction"][ids] = r
        prediction["encoder_correction"][ids] = e
        for record in records:
            record.update(gauge=str(local.gauge.iloc[0]), variant="primary")
            tuning.append(record)
        atomic_json(
            dest / "progress.json",
            {
                "status": "running",
                "model": args.model,
                "scenario": args.scenario,
                "gauges_done": gi + 1,
                "gauges_total": 8,
                "elapsed_s": time.time() - began,
            },
        )
        print(args.model, args.scenario, "gauges", gi + 1, "/8", flush=True)
    label_function = runpy.run_path(str(ROOT / "scripts/162_review_scarcity.py"))["labels"]
    meta = pd.read_parquet(source / "cases.parquet")
    normalizer = pd.read_parquet(ROOT / "results/storm_response/hourly_normalizer.parquet")
    register = pd.read_parquet(ROOT / "results/flood_case_review_2026_10_27/register.parquet")
    label_lookup = {
        u: label_function(bank, meta, u, normalizer, register).set_index("case")
        for u in plan["shared"]["issue_offsets_h"]
    }
    for name in ["future_p99", "documented_flood_overlap", "verification_clean"]:
        cases[name] = [
            label_lookup[int(r.offset_h)].loc[int(r.query) * 8 + int(r.site), name]
            for r in cases.itertuples()
        ]
    for key, values in ledger.items():
        cases[key] = values
    cases["prediction_available"] = np.isfinite(prediction["encoder_correction"]).all(1)
    cases["raw_available"] = raw_available
    cases["encoder_available"] = eo_available
    cases["ablation_paired_support"] = paired_support if args.ablation else False
    cases["model"] = args.model
    cases["assessment_id"] = [
        f"{args.scenario}__u{r.offset_h}__{r.case_id}" for r in cases.itertuples()
    ]
    assert cases.assessment_id.is_unique
    scores = []
    for method, p in prediction.items():
        f = cases.copy()
        for k, v in assessment_scores(observed, p).items():
            f[k] = v
        f["method"] = method
        scores.append(f)
    pd.concat(scores, ignore_index=True).to_parquet(dest / "scores.parquet", index=False)
    cases.to_parquet(dest / "cases.parquet", index=False)
    np.savez_compressed(dest / "predictions.npz", observed=observed, **prediction)
    atomic_json(dest / "tuning.json", tuning)
    atomic_json(
        final,
        {
            "status": "completed",
            "model": args.model,
            "scenario": args.scenario,
            "ablation": args.ablation,
            "engineering_only": args.engineering,
            "rows": n,
            "source_hashes": identity,
            "outputs": {
                p: sha256(dest / p)
                for p in ["scores.parquet", "cases.parquet", "predictions.npz", "tuning.json"]
            },
            "elapsed_s": time.time() - began,
            "selection": "earlier-year only; same-gauge heads; complete census with explicit fallback",
        },
    )
    atomic_json(
        dest / "progress.json",
        {
            "status": "completed",
            "model": args.model,
            "scenario": args.scenario,
            "gauges_done": 8,
            "gauges_total": 8,
        },
    )


if __name__ == "__main__":
    main()
