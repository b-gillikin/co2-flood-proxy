#!/usr/bin/env python3
"""Test prior-year catchment context on a fixed, paired Dutch TTM subset."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ttm_analogues", ROOT / "scripts/70_ttm_analogue_comparison.py"
)
TTM = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TTM)
DEFAULT_OUT = ROOT / "results/basin_ai_alphaearth_increment"


def context_blocks(joined, temporal):
    indexed = joined.set_index("event_id")
    context = indexed[[f"A{i:02d}" for i in range(64)]].astype(float)
    norms = np.linalg.norm(context.to_numpy(), axis=1)
    if not np.isfinite(norms).all() or (norms == 0).any():
        raise ValueError("Undefined AlphaEarth catchment mean")
    context = context.div(norms, axis=0)
    area = indexed[["catchment_area_km2"]].astype(float)
    if not np.isfinite(area.to_numpy()).all() or area.le(0).any().any():
        raise ValueError("Catchment area must be positive and observed")
    return {"ttm": temporal.loc[indexed.index], "area": np.log(area), "alphaearth": context}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    event_dir = TTM.RAW.DEFAULT_EVENT_DIR
    event_path = event_dir / "event_index.csv"
    window_path = event_dir / "event_windows.parquet"
    join_path = ROOT / "results/basin_ai_alphaearth/event_embeddings.parquet"
    vector_path = TTM.DEFAULT_OUT / "event_embeddings.parquet"
    joined = pd.read_parquet(join_path)
    signatures = TTM.RAW.BASELINE.build_signatures(
        pd.read_csv(event_path, parse_dates=["onset_utc"]), pd.read_parquet(window_path)
    )
    common = joined.loc[joined.alphaearth_input_sample].copy()
    signatures = signatures.loc[signatures.event_id.isin(common.event_id)].copy()
    score_ids = set(joined.loc[joined.alphaearth_scoring_sample, "event_id"])
    if set(signatures.loc[signatures.complete_scoring_sample, "event_id"]) != score_ids:
        raise ValueError("AlphaEarth and temporal scoring samples differ")
    vectors = pd.read_parquet(vector_path)
    blocks = context_blocks(common, vectors)
    arms = {
        "r2": {"ttm": blocks["ttm"]},
        "r2_area": {k: blocks[k] for k in ["ttm", "area"]},
        "r3_alphaearth": {k: blocks[k] for k in ["ttm", "alphaearth"]},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = {}
    scores = []
    for quality in [False, True]:
        label = "quality_sensitivity" if quality else "main"
        outputs = {}
        for arm, distance_blocks in arms.items():
            predictions, neighbors = TTM.RAW.BASELINE.retrieve_prior_analogues(
                signatures,
                top_k=5,
                min_candidates=20,
                exclude_measurement_concerns=quality,
                distance_blocks=distance_blocks,
            )
            outputs[arm] = predictions
            predictions.to_csv(args.output_dir / f"{label}_{arm}_predictions.csv", index=False)
            neighbors.to_csv(args.output_dir / f"{label}_{arm}_neighbors.csv", index=False)
            scores.append(predictions.assign(analysis=label, arm=arm))
        for reference in ["r2", "r2_area"]:
            TTM.compare_arms(
                outputs[reference], outputs["r3_alphaearth"], reference, "r3_alphaearth"
            ).to_csv(args.output_dir / f"{label}_{reference}_r3_paired.csv", index=False)
        summaries[label] = {
            "queries": len(outputs["r2"]),
            "storms": int(outputs["r2"].query_storm_id.nunique()),
            **{f"{arm}_mae": float(p.analogue_absolute_error.mean()) for arm, p in outputs.items()},
            "historical_median_mae": float(outputs["r2"].median_absolute_error.mean()),
        }
    pd.concat(scores).groupby(["analysis", "arm", "query_watercourse"], as_index=False).agg(
        queries=("query_event_id", "size"),
        storms=("query_storm_id", "nunique"),
        mae=("analogue_absolute_error", "mean"),
    ).to_csv(args.output_dir / "scores_by_watercourse.csv", index=False)
    summary = {
        "status": "bounded AlphaEarth increment executed",
        "event_backbone": "fixed frozen TTM-R2; not selected from performance",
        "distance": "equal-weight RMS of blocks; each block scaled by unique prior candidates' RMS pair distance",
        "context": "L2-normalized 64-dimensional prior-year catchment mean; simple control is log area",
        "inputs": len(common),
        "complete_outcomes": len(score_ids),
        "catchments": int(common.gauge.nunique()),
        "catchment_years": int(common[["gauge", "embedding_year"]].drop_duplicates().shape[0]),
        "results": summaries,
        "input_sha256": {
            str(p.relative_to(ROOT)): TTM.sha256(p)
            for p in [
                event_path,
                window_path,
                join_path,
                vector_path,
                Path(__file__),
                ROOT / "scripts/65_hydrological_analogue_baseline.py",
            ]
        },
        "interpretation": "Descriptive paired errors; event counts do not constitute independent catchment support. Step 6 uncertainty/relevance remain.",
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
