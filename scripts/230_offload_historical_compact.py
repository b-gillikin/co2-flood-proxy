"""Recover 45 GiB from inactive compact imagery using verified existing Azure bytes.

Use Azure CLI's Python. Default is read-only; --run retires verified copies.
No embeddings, current applied imagery, model runtimes or other chapters touched.
"""

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/disk-cleanup-2026-11-10/compact"


def inactive_check():
    commands = subprocess.check_output(["ps", "-axo", "command="], text=True)
    # A historical extraction/stager must not race input retirement. Current
    # applied work has independent imagery and feature caches.
    for line in commands.splitlines():
        if ("python" in line.lower()) and any(
            name in line for name in (
                "96_acquire_limburg_compact_eo.py", "100_extract_limburg",
                "103_stage_limburg", "105_run_limburg_eo", "110_extract_token",
                "118_extract_versioned", "122_run_coherent", "130_extract_eo",
                "131_run_eo", "133_extract_supported", "152_download_monitoring",
                "160_run_individual", "165_run_individual",
            )
        ):
            raise RuntimeError("Historical archive is active: " + line)


def main():
    import fcntl
    import sys

    spec = importlib.util.spec_from_file_location(
        "verified_offload", ROOT / "scripts/177_offload_verified_expansion.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.BASE = ROOT / "data/raw/limburg_compact_eo"
    module.PREFIX = "v1"
    module.OUT = OUT
    module.PRODUCTS = {"hls", "s1_ascending", "s2_10m", "s2_20m"}
    module.check_queue = inactive_check
    inactive_check()
    lock = (module.BASE / ".staging.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if "--run" in sys.argv:
        OUT.mkdir(parents=True, exist_ok=True)
        marker = module.BASE / "OFFLOADED-2026-11-10.json"
        module.atomic(marker, {
            "status": "retirement_in_progress_or_partial",
            "ledger": str((OUT / "removed.jsonl").relative_to(ROOT)),
            "account": "stkerkradeprod01bg",
            "container": "limburg-compact-eo", "prefix": "v1",
            "restore": "python scripts/182_restore_offloaded_expansion.py --ledger results/disk-cleanup-2026-11-10/compact/removed.jsonl --path EXACT_PROJECT_RELATIVE_PATH --restore",
            "full_restage": "python scripts/103_stage_limburg_eo_archive.py --run --reserve-gib 50 --max-local-gb 150",
            "reader_note": "Restore required historical inputs before rerunning extraction. Remove this marker only after all retired paths have been restored and hash-verified. Absence is not no-observation.",
        })
    module.main()


if __name__ == "__main__":
    main()
