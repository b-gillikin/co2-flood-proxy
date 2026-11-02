"""Offload inactive Limburg embedding-extraction inputs with verified recovery.

All ten embedding/discharge experiments are complete. Spatial v5 uses separate
applied-task rasters and frozen caches, not this expansion tree. The original
verified-pair/intent-ledger/unlink implementation is reused without changing it.
"""

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/disk-cleanup-2026-11-02/expansion"


def inactive_check():
    processes = subprocess.check_output(["ps", "-axo", "command="], text=True)
    prohibited = [
        "126_stage_eo_expansion.py",
        "130_run_eo_expansion",
        "131_run_eo_expansion",
        "160_run_individual",
        "165_run_individual",
    ]
    for line in processes.splitlines():
        if ("python" in line or "Python" in line) and any(name in line for name in prohibited):
            raise RuntimeError("Expansion staging/extraction requires a fresh dependency check")
    # The current standalone extraction queue is historical, but a resumed
    # extraction cannot silently lose its input path.
    f = ROOT / "results/limburg_individual_experiments_v1/queue/progress.json"
    state = json.loads(f.read_text())
    tasks = state.get("tasks", {})
    if isinstance(tasks, dict):
        for name, record in tasks.items():
            if name.startswith("extract_") and record.get("status") == "running":
                raise RuntimeError("An extraction remains marked running: " + name)


def main():
    path = ROOT / "scripts/177_offload_verified_expansion.py"
    spec = importlib.util.spec_from_file_location("verified_expansion_offload", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    jobs = json.loads((module.BASE / "jobs.json").read_text())
    # Explicit known products; unsupported source layouts still fail candidate().
    module.PRODUCTS = {
        "s2_toa_10m",
        "s2_toa_20m",
        "s2_toa_qa60",
        "s1_descending_139",
        "s1_descending_37",
        "landsat8_sr",
        "landsat7_sr",
        "landsat9_sr",
        "s1_ascending_15",
        "s1_ascending_161",
        "landsat5_sr",
        "s1_descending_141",
        "s1_descending_39",
    }
    if set(j["product"] for j in jobs) - module.PRODUCTS:
        raise ValueError("New products require checking before offload")
    inactive_check()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "dependency-check.json").write_text(
        json.dumps(
            dict(
                status="inactive_expansion_only",
                wrapper_sha256=module.sha(__file__),
                implementation_sha256=module.sha(path),
                protected=[
                    "data/raw/limburg_applied_tasks",
                    "data/processed/limburg_tensor_cache_v1",
                    "data/processed/limburg_terramind_encoder_v1",
                    "data/processed/limburg_copernicus_spatial_v1",
                    "data/processed/limburg_applied_galileo_spatial_v2",
                ],
                restore="scripts/182_restore_offloaded_expansion.py --ledger results/disk-cleanup-2026-11-02/expansion/removed.jsonl --path EXACT_PATH --restore",
                all_other_chapters="untouched",
            ),
            indent=2,
        )
        + "\n"
    )
    module.OUT = OUT
    module.check_queue = inactive_check
    module.main()


if __name__ == "__main__":
    main()
