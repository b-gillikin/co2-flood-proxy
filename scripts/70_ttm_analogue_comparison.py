#!/usr/bin/env python3
"""Extract frozen TTM backbone embeddings and run the paired temporal comparison."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import inspect
import json
import subprocess
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "raw_analogues", ROOT / "scripts/69_raw_hydrograph_analogue_baseline.py"
)
RAW = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RAW)
MODEL_DIR = ROOT / "data/raw/foundation_assets/models/granite-timeseries-ttm-r2"
DEFAULT_OUT = ROOT / "results/basin_ai_ttm"
CODE_ARCHIVE = ROOT / "data/raw/foundation_assets/code/granite-tsfm-fe7a356.tar.gz"
CODE_REVISION = "fe7a35697723e2a2f5246ae979474bfc554e26c0"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pool_patch_states(hidden, pooling="mean"):
    """Keep the original mean readout or preserve ordered patch positions."""
    import torch

    if hidden.ndim != 4 or hidden.shape[1] != 1:
        raise ValueError(f"Unexpected backbone shape: {tuple(hidden.shape)}")
    if pooling == "mean":
        pooled = hidden.mean(dim=2).squeeze(1)
    elif pooling == "ordered":
        pooled = hidden.squeeze(1).flatten(start_dim=1)
    else:
        raise ValueError("Use mean or ordered pooling")
    norms = torch.linalg.vector_norm(pooled, dim=1, keepdim=True)
    if not torch.isfinite(pooled).all() or (norms == 0).any():
        raise ValueError("Undefined frozen TTM representation")
    return pooled / norms


def extract_embeddings(histories: pd.DataFrame, model_dir=MODEL_DIR, batch_size=32, pooling="mean"):
    import torch
    from tsfm_public import TinyTimeMixerForPrediction

    receipt = json.loads(CODE_ARCHIVE.with_suffix(".gz.receipt.json").read_text())
    if sha256(CODE_ARCHIVE) != receipt["sha256"]:
        raise ValueError("Pinned TTM source archive checksum mismatch")
    installed = Path(inspect.getfile(TinyTimeMixerForPrediction)).resolve()
    expected = CODE_ARCHIVE.parent / "unpacked" / f"granite-tsfm-{CODE_REVISION}"
    if not installed.is_relative_to(expected):
        raise ValueError("TTM must be imported from the pinned, locally unpacked source")
    with tarfile.open(CODE_ARCHIVE) as archive:
        for name in ["modeling_tinytimemixer.py", "configuration_tinytimemixer.py"]:
            path = installed.parent / name
            member = archive.extractfile(
                f"granite-tsfm-{CODE_REVISION}/{path.relative_to(expected)}"
            )
            if member is None or path.read_bytes() != member.read():
                raise ValueError(f"Installed TTM source differs from its archive: {name}")
    if histories.shape[1] != 512 or not np.isfinite(histories.to_numpy()).all():
        raise ValueError("TTM requires finite, unpadded 512-hour histories")
    for name in ["config.json", "model.safetensors"]:
        path = Path(model_dir) / name
        receipt = json.loads(path.with_suffix(path.suffix + ".receipt.json").read_text())
        if sha256(path) != receipt["sha256"]:
            raise ValueError(f"Pinned TTM asset checksum mismatch: {name}")
    torch.manual_seed(20261013)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    model, loading = TinyTimeMixerForPrediction.from_pretrained(
        str(model_dir), local_files_only=True, output_loading_info=True
    )
    if any(
        loading.get(key)
        for key in ["missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs"]
    ):
        raise ValueError(f"TTM checkpoint did not load completely: {loading}")
    if model.config.context_length != 512 or model.config.prediction_length != 96:
        raise ValueError("Loaded checkpoint differs from the pinned 512-96 contract")
    model.eval().requires_grad_(False)
    values = histories.to_numpy(dtype=np.float32, copy=True)
    vectors = []
    with torch.inference_mode():
        for start in range(0, len(values), batch_size):
            batch = torch.from_numpy(values[start : start + batch_size, :, None])
            # Call only the backbone. The forecasting decoder/head and any
            # withheld outcomes have no role in this representation.
            hidden = model.backbone(past_values=batch, return_dict=True).last_hidden_state
            vectors.append(pool_patch_states(hidden, pooling).numpy())
    result = pd.DataFrame(np.concatenate(vectors), index=histories.index)
    result.columns = [f"ttm_{i:03d}" for i in range(result.shape[1])]
    return result, {
        "seed": 20261013,
        "pooling": pooling,
        "runtime_versions": {
            p: importlib.metadata.version(p)
            for p in ["torch", "transformers", "granite-tsfm", "numpy", "pandas", "pyarrow"]
        },
        "code_revision": CODE_REVISION,
        "code_archive_sha256": sha256(CODE_ARCHIVE),
        "loading_info": loading,
        "hidden_shape": list(hidden.shape[1:]),
        "model_parameters": sum(p.numel() for p in model.parameters()),
        "device": "cpu",
        "checkpoint_scaling": model.config.scaling,
        "training": model.training,
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
    }


def compare_arms(reference, challenger, reference_id, challenger_id):
    paired = RAW.paired_comparison(reference, challenger)
    rename = {}
    for column in paired:
        if column.endswith("_r0"):
            rename[column] = column[:-3] + f"_{reference_id}"
        elif column.endswith("_r1"):
            rename[column] = column[:-3] + f"_{challenger_id}"
    rename["raw_minus_conventional_absolute_error"] = "challenger_minus_reference_error"
    return paired.rename(columns=rename)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-dir", type=Path, default=RAW.DEFAULT_EVENT_DIR)
    parser.add_argument("--raw-dir", type=Path, default=RAW.DEFAULT_OUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    events = pd.read_csv(args.event_dir / "event_index.csv", parse_dates=["onset_utc"])
    windows = pd.read_parquet(args.event_dir / "event_windows.parquet")
    signatures = RAW.BASELINE.build_signatures(events, windows)
    histories = pd.read_parquet(args.raw_dir / "standardized_histories.parquet")
    rebuilt, _ = RAW.standardized_histories(
        signatures.loc[signatures.common_representation_sample, "event_id"], windows
    )
    pd.testing.assert_frame_equal(histories, rebuilt)
    vectors, model_info = extract_embeddings(histories)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    vectors.to_parquet(args.output_dir / "event_embeddings.parquet")
    estimates = []
    summaries = {}
    for quality in [False, True]:
        label = "quality_sensitivity" if quality else "main"
        outputs = {}
        for arm, representation in [("r0", None), ("r1", histories), ("r2", vectors)]:
            predictions, neighbors = RAW.BASELINE.retrieve_prior_analogues(
                signatures,
                top_k=5,
                min_candidates=20,
                exclude_measurement_concerns=quality,
                representation_vectors=representation,
            )
            outputs[arm] = predictions
            predictions.assign(arm=arm, analysis=label).to_csv(
                args.output_dir / f"{label}_{arm}_predictions.csv", index=False
            )
            if arm == "r2":
                neighbors.to_csv(args.output_dir / f"{label}_r2_neighbors.csv", index=False)
            estimates.append(predictions.assign(arm=arm, analysis=label))
        for reference in ["r0", "r1"]:
            compare_arms(outputs[reference], outputs["r2"], reference, "r2").to_csv(
                args.output_dir / f"{label}_{reference}_r2_paired.csv", index=False
            )
        summaries[label] = {
            "query_count": len(outputs["r2"]),
            "query_storm_count": outputs["r2"].query_storm_id.nunique(),
            **{
                f"{arm}_mae": float(table.analogue_absolute_error.mean())
                for arm, table in outputs.items()
            },
            "historical_median_mae": float(outputs["r2"].median_absolute_error.mean()),
        }
    all_estimates = pd.concat(estimates, ignore_index=True)
    all_estimates.groupby(["analysis", "arm", "query_watercourse"], as_index=False).agg(
        query_count=("query_event_id", "size"),
        storm_count=("query_storm_id", "nunique"),
        mae=("analogue_absolute_error", "mean"),
    ).to_csv(args.output_dir / "scores_by_watercourse.csv", index=False)
    summary = {
        "status": "frozen TTM representation evaluated; no fine-tuning or forecast head used",
        "representation": "last backbone hidden layer; patch mean; L2 normalization",
        "model_info": model_info,
        "representation_events": len(vectors),
        "dimensions": vectors.shape[1],
        "results": summaries,
        "seed": 20261013,
        "runtime_versions": {
            p: importlib.metadata.version(p)
            for p in ["torch", "transformers", "granite-tsfm", "numpy", "pandas"]
        },
        "input_sha256": {
            "histories": sha256(args.raw_dir / "standardized_histories.parquet"),
            "event_index": sha256(args.event_dir / "event_index.csv"),
            "event_windows": sha256(args.event_dir / "event_windows.parquet"),
            "weights": sha256(MODEL_DIR / "model.safetensors"),
            "config": sha256(MODEL_DIR / "config.json"),
            "runner": sha256(__file__),
            "retrieval_code": sha256(ROOT / "scripts/65_hydrological_analogue_baseline.py"),
        },
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "interpretation": "Descriptive paired MAE; storm uncertainty and relevance review remain step 6.",
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
