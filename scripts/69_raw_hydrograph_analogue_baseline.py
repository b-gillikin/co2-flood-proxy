#!/usr/bin/env python3
"""Compare raw standardized 512-hour hydrograph retrieval with the R0 baseline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "hydrological_analogue_baseline", ROOT / "scripts/65_hydrological_analogue_baseline.py"
)
BASELINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BASELINE)
HISTORY_HOURS = np.arange(-511, 1)
TOP_K = 5
MIN_CANDIDATES = 20
DEFAULT_EVENT_DIR = ROOT / "results/basin_ai_event_library"
DEFAULT_OUT = ROOT / "results/basin_ai_raw_hydrograph"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def standardized_histories(
    event_ids: pd.Series, windows: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    history = windows.loc[
        windows.event_id.isin(event_ids) & windows.relative_hour.between(-511, 0),
        ["event_id", "relative_hour", "target_discharge_m3s"],
    ]
    if history.duplicated(["event_id", "relative_hour"]).any():
        raise ValueError("Duplicate assessment-history observations")
    if len(history) != len(event_ids) * 512:
        raise ValueError("Every eligible event must have exactly 512 history observations")
    raw = history.pivot(
        index="event_id", columns="relative_hour", values="target_discharge_m3s"
    ).reindex(index=event_ids, columns=HISTORY_HOURS)
    values = raw.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("An eligible discharge history is incomplete or non-finite")
    means = values.mean(axis=1)
    scales = values.std(axis=1, ddof=0)
    # A constant history maps to zero and is explicitly flagged; no imputation
    # or extra sample exclusion is introduced by this numerical safeguard.
    safe_scales = np.where(scales == 0, 1.0, scales)
    vectors = pd.DataFrame(
        (values - means[:, None]) / safe_scales[:, None],
        index=pd.Index(event_ids, name="event_id"),
        columns=[f"q_hour_{hour}" for hour in HISTORY_HOURS],
    )
    checks = pd.DataFrame(
        {
            "event_id": event_ids.to_numpy(),
            "history_mean_m3s": means,
            "history_std_m3s": scales,
            "constant_history": scales == 0,
        }
    )
    return vectors, checks


def paired_comparison(conventional: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    if set(conventional.query_event_id) != set(raw.query_event_id):
        raise ValueError("R0 and R1 query samples differ")
    paired = conventional.merge(
        raw, on="query_event_id", suffixes=("_r0", "_r1"), validate="one_to_one"
    )
    for column in ["candidate_count", "candidate_storm_count", "expanding_median_prediction"]:
        if not paired[f"{column}_r0"].eq(paired[f"{column}_r1"]).all():
            raise ValueError(f"R0 and R1 differ in the shared {column}")
    paired["raw_minus_conventional_absolute_error"] = (
        paired.analogue_absolute_error_r1 - paired.analogue_absolute_error_r0
    )
    return paired


def comparison_summary(paired: pd.DataFrame) -> dict:
    return {
        "query_count": len(paired),
        "query_storm_count": int(paired.query_storm_id_r1.nunique()),
        "r0_peak_ratio_mae": float(paired.analogue_absolute_error_r0.mean()),
        "r1_peak_ratio_mae": float(paired.analogue_absolute_error_r1.mean()),
        "historical_median_peak_ratio_mae": float(paired.median_absolute_error_r1.mean()),
        "raw_minus_conventional_mae": float(paired.raw_minus_conventional_absolute_error.mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-dir", type=Path, default=DEFAULT_EVENT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    library_manifest = args.event_dir / "manifest.json"
    manifest = json.loads(library_manifest.read_text())
    if manifest["history_hours"] != 512 or manifest["outcome_hours"] != 72:
        raise ValueError("The library must use the fixed 512-history/72-outcome contract")
    event_path = args.event_dir / "event_index.csv"
    window_path = args.event_dir / "event_windows.parquet"
    events = pd.read_csv(event_path, parse_dates=["onset_utc"])
    windows = pd.read_parquet(window_path)
    signatures = BASELINE.build_signatures(events, windows)
    event_ids = signatures.loc[signatures.common_representation_sample, "event_id"]
    vectors, checks = standardized_histories(event_ids, windows)

    conventional, _ = BASELINE.retrieve_prior_analogues(
        signatures, top_k=TOP_K, min_candidates=MIN_CANDIDATES
    )
    raw, neighbors = BASELINE.retrieve_prior_analogues(
        signatures, top_k=TOP_K, min_candidates=MIN_CANDIDATES, representation_vectors=vectors
    )
    paired = paired_comparison(conventional, raw)
    conventional_quality, _ = BASELINE.retrieve_prior_analogues(
        signatures, top_k=TOP_K, min_candidates=MIN_CANDIDATES, exclude_measurement_concerns=True
    )
    raw_quality, quality_neighbors = BASELINE.retrieve_prior_analogues(
        signatures,
        top_k=TOP_K,
        min_candidates=MIN_CANDIDATES,
        exclude_measurement_concerns=True,
        representation_vectors=vectors,
    )
    paired_quality = paired_comparison(conventional_quality, raw_quality)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    vectors.to_parquet(args.output_dir / "standardized_histories.parquet")
    checks.to_csv(args.output_dir / "history_standardization.csv", index=False)
    raw.to_csv(args.output_dir / "analogue_predictions.csv", index=False)
    neighbors.to_csv(args.output_dir / "analogue_neighbors.csv", index=False)
    paired.to_csv(args.output_dir / "paired_r0_r1.csv", index=False)
    raw_quality.to_csv(args.output_dir / "quality_sensitivity_predictions.csv", index=False)
    quality_neighbors.to_csv(args.output_dir / "quality_sensitivity_neighbors.csv", index=False)
    paired_quality.to_csv(args.output_dir / "quality_sensitivity_paired_r0_r1.csv", index=False)
    by_watercourse = paired.groupby("query_watercourse_r1", as_index=False).agg(
        query_count=("query_event_id", "size"),
        query_storm_count=("query_storm_id_r1", "nunique"),
        r0_mae=("analogue_absolute_error_r0", "mean"),
        r1_mae=("analogue_absolute_error_r1", "mean"),
        historical_median_mae=("median_absolute_error_r1", "mean"),
        raw_minus_conventional_mae=("raw_minus_conventional_absolute_error", "mean"),
    )
    by_watercourse.to_csv(args.output_dir / "comparison_by_watercourse.csv", index=False)
    summary = {
        "status": "R1 raw-hydrograph baseline executed; no TTM or AlphaEarth-effect model fitted",
        "history_observations": 512,
        "history_relative_hours": [-511, 0],
        "standardization": "each event's available history mean and population standard deviation (ddof=0)",
        "constant_history_rule": "standardized vector is zero; flag retained",
        "distance": "Euclidean distance between standardized 512-hour vectors",
        "top_k": TOP_K,
        "minimum_candidate_events": MIN_CANDIDATES,
        "candidate_rule": "donor response complete by query onset; different storm; one selected event per storm",
        "representation_event_count": len(vectors),
        "complete_outcome_event_count": int(signatures.complete_scoring_sample.sum()),
        "constant_history_count": int(checks.constant_history.sum()),
        "main": comparison_summary(paired),
        "quality_sensitivity": comparison_summary(paired_quality),
        "interpretation": "Descriptive paired comparison; uncertainty and relevance review remain for step 6. Retrospective p99 labels do not establish forecast skill.",
        "input_sha256": {
            "event_index": sha256(event_path),
            "event_windows": sha256(window_path),
            "library_manifest": sha256(library_manifest),
            "raw_runner": sha256(Path(__file__)),
            "shared_baseline_code": sha256(ROOT / "scripts/65_hydrological_analogue_baseline.py"),
            "representation_contract": sha256(ROOT / "docs/ai-eval/representation-arms.json"),
        },
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
