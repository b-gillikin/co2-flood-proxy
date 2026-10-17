"""Run all ten frozen EO extractions and catchment aggregates, sequentially.

No model fitting/scoring, sampling, cloud compute or raw-data deletion. Each
model uses its pinned runtime and full held contexts. Reruns verify/resume patches.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES, sha256

ORDER = [
    "prithvi",
    "croma",
    "satmae",
    "dofa",
    "copernicus_fm",
    "terramind",
    "olmoearth",
    "galileo",
    "anysat",
    "presto",
]


def atomic_json(path, data):
    tmp = path.with_suffix(".json.partial")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def merge_aggregates(base, models):
    import pandas as pd

    target = base / "census"
    target.mkdir(parents=True, exist_ok=True)
    expected = {f"{model}.parquet" for model in models} | {
        "coverage.parquet",
        "patch_areas.parquet",
    }
    if {p.name for p in target.glob("*.parquet")} - expected:
        raise ValueError("Unexpected stale model outputs in merged census")
    source_manifests = [
        json.loads((base / "per_model" / model / "census/manifest.json").read_text())
        for model in models
    ]
    if len({m["catchments_sha256"] for m in source_manifests}) != 1:
        raise ValueError("Catchment geometries differ across models")
    coverage, areas, manifests = [], [], []
    for model in models:
        folder = base / "per_model" / model / "census"
        manifest = json.loads((folder / "manifest.json").read_text())
        for name, digest in manifest["outputs_sha256"].items():
            if sha256(folder / name) != digest:
                raise ValueError("Aggregate checksum mismatch")
        manifests.append(manifest)
        source = folder / f"{model}.parquet"
        if source.exists():
            (target / source.name).write_bytes(source.read_bytes())
        for name, frames in [("coverage.parquet", coverage), ("patch_areas.parquet", areas)]:
            frame = pd.read_parquet(folder / name)
            if len(frame):
                frames.append(frame)
    for name, frames in [("coverage.parquet", coverage), ("patch_areas.parquet", areas)]:
        (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()).to_parquet(
            target / name, index=False
        )
    geometry_hashes = {m["catchments_sha256"] for m in manifests}
    if len(geometry_hashes) != 1:
        raise ValueError("Catchment geometries differ across models")
    merged = dict(manifests[0])
    merged.update(
        created_utc=datetime.now(timezone.utc).isoformat(),
        contexts_by_model={k: v for m in manifests for k, v in m["contexts_by_model"].items()},
        source_sha256={k: v for m in manifests for k, v in m["source_sha256"].items()},
        errors=[e for m in manifests for e in m["errors"]],
        outputs_sha256={p.name: sha256(p) for p in target.glob("*.parquet")},
    )
    atomic_json(target / "manifest.json", merged)


def main():
    logdir = ROOT / "logs/eo-census"
    logdir.mkdir(parents=True, exist_ok=True)
    lock = (logdir / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    staging = json.loads((ROOT / "data/raw/limburg_compact_eo/staging-progress.json").read_text())
    if staging["status"] != "completed" or staging["failures"]:
        raise ValueError("Full local staging required for this census run")
    if set(ORDER) != set(ROUTES):
        raise ValueError("Queue omits a configured model")
    state = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "order": ORDER,
        "models": {},
        "scope": "Frozen extraction and exact-area aggregation only; no analogue scoring.",
    }
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = "/tmp/limburg-eo-matplotlib"
    base = ROOT / "results/eo_catchment_representations"
    completed = []
    for model in ORDER:
        state["current_model"] = model
        state["updated_utc"] = datetime.now(timezone.utc).isoformat()
        atomic_json(logdir / "progress.json", state)
        runtime = ROOT / f".venvs-eo/{ROUTES[model][2]}/bin/python"
        with (logdir / f"{model}.log").open("a") as output:
            extraction = subprocess.run(
                [
                    str(runtime),
                    "-u",
                    "scripts/100_extract_limburg_eo_sequences.py",
                    "--model",
                    model,
                    "--run",
                ],
                cwd=ROOT,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
            )
            if extraction.returncode == 75:
                state["status"] = "paused_free_space"
                atomic_json(logdir / "progress.json", state)
                return 75
            aggregation = subprocess.run(
                [
                    str(ROOT / ".venvs-eo/terramind/bin/python"),
                    "-u",
                    "scripts/101_aggregate_limburg_eo_catchments.py",
                    "--model",
                    model,
                    "--out",
                    str(base / "per_model" / model),
                ],
                cwd=ROOT,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
            )
        state["models"][model] = {
            "extraction_exit": extraction.returncode,
            "aggregation_exit": aggregation.returncode,
        }
        if aggregation.returncode == 0:
            completed.append(model)
        state["updated_utc"] = datetime.now(timezone.utc).isoformat()
        atomic_json(logdir / "progress.json", state)
    if completed:
        merge_aggregates(base, completed)
    state["status"] = (
        "completed"
        if all(v["extraction_exit"] == v["aggregation_exit"] == 0 for v in state["models"].values())
        else "completed_with_errors"
    )
    state["updated_utc"] = datetime.now(timezone.utc).isoformat()
    atomic_json(logdir / "progress.json", state)
    return int(state["status"] != "completed")


if __name__ == "__main__":
    raise SystemExit(main())
