#!/usr/bin/env python3
"""Resumable frozen EO patch extraction from verified local compact archive files.

Default is inventory only. --smoke tests one real, maximally observed patch from
an explicitly named engineering fixture. --run traverses all available patches.
Neither mode fits models or evaluates flood-event performance.
"""

import argparse
import hashlib
import json
import runpy
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES, get_patch, patch_origins, read_tile, sha256

# No torch import for dry-run inventory.


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.partial")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def valid_cached(path, identity):
    receipt = path.with_suffix(".json")
    if not path.exists() or not receipt.exists():
        return False
    try:
        saved = json.loads(receipt.read_text())
        return saved["identity"] == identity and saved["sha256"] == sha256(path)
    except (ValueError, KeyError, OSError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=list(ROUTES))
    parser.add_argument("--archive", type=Path, default=ROOT / "data/raw/limburg_compact_eo")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "data/processed/limburg_eo_embeddings"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument(
        "--fixture",
        default="monthly_20180901_20181001/297600_5625600",
        help="Window/tile for engineering smoke only",
    )
    args = parser.parse_args()
    jobs = json.loads((args.archive / "jobs.json").read_text())
    companions = {(j["window"]["id"], tuple(j["bounds"]), j["product"]): j for j in jobs}
    product, size, env = ROUTES[args.model]
    selected = [j for j in jobs if j["product"] == product]

    def exists(j):
        p = args.archive / j["relative_path"]
        return p.exists() and p.with_suffix(".receipt.json").exists()

    available = []
    for j in selected:
        if not exists(j):
            continue
        if product == "s2_10m":
            other = companions.get((j["window"]["id"], tuple(j["bounds"]), "s2_20m"))
            if not other or not exists(other):
                continue
        available.append(j)
    print(
        json.dumps(
            {
                "model": args.model,
                "runtime": env,
                "primary_jobs": len(selected),
                "available_with_companions": len(available),
                "pending": len(selected) - len(available),
                "patch_size": size,
            }
        ),
        flush=True,
    )
    if not args.smoke and not args.run:
        return 0
    pending_jobs = len(selected) - len(available)
    if args.smoke:
        window, tile = args.fixture.split("/")
        available = [
            j
            for j in available
            if j["window"]["id"] == window and Path(j["relative_path"]).stem == tile
        ]
        if len(available) != 1:
            raise ValueError("Named fixture is not locally complete")
    # Bind cache to actual weights, relevant source tree, adapters and environment.
    manifest = json.loads((ROOT / "config/limburg_eo_model_assets.json").read_text())
    asset = next(a for a in manifest["models"] if a["id"] == args.model)
    modelroot = ROOT / manifest["destination"] / "models" / args.model
    verify = runpy.run_path(str(ROOT / "scripts/97_download_limburg_eo_models.py"))["verify"]
    weight_hashes = {a["path"]: verify(modelroot / a["path"], a) for a in asset["assets"]}
    code_paths = [ROOT / asset["source"]["path"]] if asset.get("source") else [modelroot]
    if args.model == "terramind":
        code_paths.append(ROOT / manifest["destination"] / "code/terratorch")
    source_hashes = {
        str(p.relative_to(ROOT)): sha256(p)
        for directory in code_paths
        for p in sorted(directory.rglob("*.py"))
    }
    lock = ROOT / "environments/eo-screen" / f"{env}-macos-arm64.lock.txt"
    context = {
        "model": {
            k: asset.get(k)
            for k in (
                "id",
                "checkpoint",
                "hf_repository",
                "weight_revision",
                "source",
                "assets",
                "support_sources",
                "input_contract",
            )
        },
        "weights": weight_hashes,
        "source_hashes": source_hashes,
        "adapters": {
            str(p.relative_to(ROOT)): sha256(p)
            for p in [
                Path(__file__).resolve(),
                ROOT / "src/eo_inputs.py",
                ROOT / "src/eo_encoders.py",
                ROOT / "environments/eo-screen/check_load.py",
            ]
        },
        "environment_lock_sha256": sha256(lock),
        "python": sys.version,
        "installed_packages": {
            d.metadata["Name"]: d.version
            for d in __import__("importlib.metadata", fromlist=["distributions"]).distributions()
        },
        "seed": 1729,
        "purpose": "engineering_fixture" if args.smoke else "available_archive_patch_census",
        "missingness": "Masks retained; non-mask-aware models use normalized mean imputation. Not a claim of invariance to missing coverage.",
        "composites": "Single completed composite frame, not single acquisition or full temporal model evaluation",
    }
    run_id = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
    target = args.output / args.model / run_id
    atomic_json(target / "manifest.json", context)
    import numpy as np

    from src.eo_encoders import Encoder

    encoder = Encoder(args.model)
    counts = {
        "written": 0,
        "resumed": 0,
        "no_observation": 0,
        "errors": 0,
        "pending_jobs": pending_jobs,
    }
    for job in available:
        try:
            tile = read_tile(args.archive, job, companions)
            origins = patch_origins(tile, size)
            if args.smoke:
                origins = [
                    max(
                        origins,
                        key=lambda rc: int(
                            tile.valid[rc[0] : rc[0] + size, rc[1] : rc[1] + size].sum()
                        ),
                    )
                ]
            for row, col in origins:
                patch = get_patch(tile, row, col, size)
                relative = Path(job["relative_path"]).with_suffix("")
                path = target / relative / f"{row}_{col}.npz"
                identity = {"run": run_id, "metadata": patch["metadata"]}
                if not patch["valid"].any():
                    atomic_json(
                        path.with_suffix(".json"),
                        {"identity": identity, "status": "no_observation"},
                    )
                    counts["no_observation"] += 1
                    continue
                if valid_cached(path, identity):
                    counts["resumed"] += 1
                    continue
                vector = encoder(patch)
                repeatable = None
                if args.smoke:
                    repeat = encoder(patch)
                    repeatable = bool(np.array_equal(vector, repeat))
                    if not repeatable:
                        raise ValueError("Frozen real-input inference is not repeatable")
                path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(
                    dir=path.parent, suffix=".npz", delete=False
                ) as output:
                    temporary = Path(output.name)
                    np.savez_compressed(
                        output, embedding=vector, valid=patch["valid"], acquired_day=patch["days"]
                    )
                temporary.replace(path)
                atomic_json(
                    path.with_suffix(".json"),
                    {
                        "identity": identity,
                        "status": "finite_embedding",
                        "sha256": sha256(path),
                        "dimension": len(vector),
                        "repeatable": repeatable,
                    },
                )
                counts["written"] += 1
        except Exception as error:
            counts["errors"] += 1
            atomic_json(
                target / "errors" / Path(job["relative_path"]).with_suffix(".json"),
                {"job": job, "error": f"{type(error).__name__}: {error}"},
            )
            print(f"ERROR {job['relative_path']}: {type(error).__name__}: {error}", flush=True)
    counts["completed_utc"] = datetime.now(timezone.utc).isoformat()
    atomic_json(target / "status.json", counts)
    print(json.dumps({"run": run_id, **counts}), flush=True)
    return int(counts["errors"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
