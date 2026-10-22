"""Retire Brian-authorized superseded EO caches; preserve sources and reusable runs.

Default lists the exact bounded targets. --retire preserves run records and full
catchment aggregates, verifies the preserved files, then deletes regenerable
per-patch outputs for the eight replaced models. No raw imagery/weights or other
chapter is a target. Historical per-patch receipts are regenerated from the held
sources if ever needed; this intentionally does not retain millions of them.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256

MODELS = {"croma", "dofa", "copernicus_fm", "terramind", "satmae", "anysat", "galileo", "presto"}
ROOTS = [
    "limburg_eo_sequences",
    "limburg_eo_mps_sequences",
    "limburg_eo_token_consistent_sequences",
    "limburg_eo_presto_torch291_sequences",
]
DEST = ROOT / "data/processed/limburg_eo_retired_2026-10-22"
PROGRESS = ROOT / "logs/eo-retirement-2026-10-22/progress.json"


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def targets():
    found = []
    for name in ROOTS:
        for model in sorted(MODELS):
            base = ROOT / "data/processed" / name / model
            for manifest in sorted(base.glob("*/manifest.json")):
                run = manifest.parent
                if run.is_symlink() or run.resolve().parent != base.resolve():
                    raise ValueError("Unexpected target: " + str(run))
                saved = json.loads(manifest.read_text())
                if saved.get("model") != model:
                    raise ValueError("Manifest/model mismatch: " + str(run))
                found.append(run)
    return found


def require_idle():
    commands = subprocess.check_output(["ps", "-axo", "pid=,command="], text=True)
    scripts = [
        "100_extract_limburg_eo_sequences.py",
        "101_aggregate_limburg_eo_catchments.py",
        "102_connect_limburg_eo_experiments.py",
        "118_extract_versioned_eo_sequences.py",
        "121_finish_current_eo_workflow.py",
        "122_run_coherent_eo_correction.py",
    ]
    active = [line.strip() for line in commands.splitlines() if any(s in line for s in scripts)]
    if active:
        raise ValueError("Owning workflow must be idle: " + "\n".join(active))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retire", action="store_true")
    args = parser.parse_args()
    runs = targets()
    selection_path = ROOT / "config/limburg_eo_selected_runs.json"
    selection = json.loads(selection_path.read_text())
    if not args.retire:
        print(json.dumps({"runs": [str(p.relative_to(ROOT)) for p in runs]}, indent=2))
        return
    require_idle()
    if PROGRESS.exists() and json.loads(PROGRESS.read_text()).get("status") == "completed":
        print("Retirement already completed; no files changed.")
        return
    DEST.mkdir(parents=True, exist_ok=True)
    state = {
        "status": "preserving",
        "pid": os.getpid(),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "authorization": "Brian requested scrapping the eight superseded first-run caches and restarting after corrections.",
        "archive": str(DEST.relative_to(ROOT)),
        "free_bytes_before": shutil.disk_usage(ROOT).free,
        "runs": [],
        "preserved": [],
        "protected": {},
    }

    def update(**values):
        state.update(values, updated_utc=datetime.now(timezone.utc).isoformat())
        atomic_json(PROGRESS, state)
        print(json.dumps({k: state[k] for k in ["status", "updated_utc"]} | values), flush=True)

    def preserve_file(path, dest):
        digest = sha256(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        if sha256(dest) != digest:
            raise ValueError("Preservation checksum mismatch: " + str(path))
        state["preserved"].append(
            {
                "original": str(path.relative_to(ROOT)),
                "archive": str(dest.relative_to(ROOT)),
                "sha256": digest,
            }
        )

    # Small records of reusable runs provide an independent post-delete check.
    for model in ["prithvi", "olmoearth"]:
        item = selection["models"][model]
        for path in [
            ROOT / item["run"] / "manifest.json",
            ROOT / item["run"] / "status.json",
            ROOT / item["aggregate"] / "manifest.json",
            ROOT / item["aggregate"] / (model + ".parquet"),
        ]:
            state["protected"][str(path.relative_to(ROOT))] = sha256(path)
    for path in [
        selection_path,
        ROOT / "data/raw/limburg_compact_eo/jobs.json",
        ROOT / "results/eo_comparison_preparation/contexts.json",
        ROOT / "config/limburg_eo_model_assets.json",
        ROOT / "src/eo_encoders.py",
        ROOT / "src/eo_inputs.py",
        ROOT / "src/eo_mps.py",
        ROOT / "environments/eo-screen/check_load.py",
    ]:
        preserve_file(path, DEST / "provenance" / path.relative_to(ROOT))
    state["git_revision"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    for run in runs:
        if (run / "retirement.json").exists():
            state["runs"].append({"path": str(run.relative_to(ROOT)), "status": "already_retired"})
            continue
        for name in ["manifest.json", "status.json"]:
            path = run / name
            if path.exists():
                preserve_file(path, DEST / "run_records" / run.relative_to(ROOT) / name)
        state["runs"].append({"path": str(run.relative_to(ROOT)), "status": "preserved"})
    update()
    # Rename the complete small scientific summaries; do not silently delete the
    # evidence of what the retired run actually produced or promote it as current.
    for model in sorted(MODELS):
        folder = ROOT / selection["models"][model]["aggregate"]
        dest = DEST / "retired_aggregates" / model
        if folder.exists():
            hashes = {f.name: sha256(f) for f in folder.iterdir() if f.is_file()}
            if dest.exists():
                raise ValueError("Archive destination already exists: " + str(dest))
            dest.parent.mkdir(parents=True, exist_ok=True)
            folder.rename(dest)
            if any(sha256(dest / name) != digest for name, digest in hashes.items()):
                raise ValueError("Aggregate changed during retirement: " + model)
            state["preserved"].append(
                {
                    "retired_aggregate": model,
                    "archive": str(dest.relative_to(ROOT)),
                    "files_sha256": hashes,
                }
            )
    (DEST / "README.md").write_text(
        "# Retired EO first-run material\n\n"
        "Superseded input versions, not current scientific results. CROMA and SatMAE have "
        "confirmed scaling errors; the other six routes are replaced for documented "
        "input corrections. Full catchment summaries and extraction manifests/statuses "
        "are preserved. Per-patch vectors, masks, date arrays and receipts are retired; "
        "held raw imagery, weights, population ledgers, source code and Git history "
        "allow regeneration. Prithvi and repaired OlmoEarth are retained separately.\n"
    )
    update(status="removing_patch_outputs")
    for run, record in zip(runs, state["runs"], strict=True):
        if record["status"] == "already_retired":
            continue
        update(current_run=record["path"])
        for child in run.iterdir():
            if child.name in {"manifest.json", "status.json", "retirement.json"}:
                continue
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        marker = {
            "status": "retired_superseded_inputs",
            "retired_utc": datetime.now(timezone.utc).isoformat(),
            "archive": str(DEST.relative_to(ROOT)),
            "reason": "Replaced by consolidated corrected extraction; per-patch cache deliberately retired.",
        }
        atomic_json(run / "retirement.json", marker)
        status_path = run / "status.json"
        status = json.loads(status_path.read_text()) if status_path.exists() else {"run": run.name}
        status.update(marker)
        atomic_json(status_path, status)
        record["status"] = "retired"
        update(free_bytes_now=shutil.disk_usage(ROOT).free)
    # Cache is derivable, and contains predictions made from superseded vectors.
    cache = ROOT / "data/processed/eo_retrieval_cache"
    if cache.exists():
        shutil.rmtree(cache)
    for path, digest in state["protected"].items():
        if sha256(ROOT / path) != digest:
            raise ValueError("Protected reusable output changed: " + path)
    state["free_bytes_after"] = shutil.disk_usage(ROOT).free
    state["free_space_increase_bytes"] = state["free_bytes_after"] - state["free_bytes_before"]
    update(status="completed", protected_hashes_unchanged=True)
    atomic_json(DEST / "retirement-receipt.json", state)


if __name__ == "__main__":
    main()
