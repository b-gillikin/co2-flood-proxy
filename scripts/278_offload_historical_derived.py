"""Archive and retire exactly two Brian-authorized historical Limburg caches.

Run with Azure CLI's Python. Default is read-only; --run performs the authorized
verified offload. Requires the saved streaming inventory. No other chapter or
raw observations, model weights, current inputs or compact results are targets.
"""

import argparse
import fcntl
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.derived_cache_offload import ROOTS, atomic, ensure_idle, restore_path, run, sha

OUT = ROOT / "results/disk-cleanup-2026-11-18-derived"
PROTECTED = [
    "config/limburg_current_study.json",
    "config/limburg_representation_extension_v1.json",
    "config/limburg_dise_multiyear_v1.json",
    "results/limburg_dise_multiyear_v1/completion.json",
    "results/limburg_dise_repeatability_v1/manifest.json",
    "results/limburg_dise_regional_benchmark_v1/preparation/features.parquet",
]


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--run", action="store_true")
    p.add_argument("--phase", choices=["tensors", "sequences", "all"], default="all")
    p.add_argument("--restore-path")
    a = p.parse_args()
    OUT.mkdir(exist_ok=True)
    with (OUT / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if a.restore_path:
            ensure_idle()
            print(json.dumps(restore_path(ROOT, OUT, a.restore_path)))
            return
        summary = json.loads((OUT / "inventory-summary.json").read_text())
        if summary["status"] != "complete":
            raise ValueError("Complete inventory required")
        if not a.run:
            print(json.dumps(summary, indent=2))
            return
        ensure_idle()
        os.nice(10)
        protection_path = OUT / "protection.json"
        if protection_path.exists():
            protection = json.loads(protection_path.read_text())
        else:
            protection = {name: sha(ROOT / name) for name in PROTECTED}
            # Current task's configuration and its parent must not depend on
            # these roots; historical documents/configs legitimately still do.
            for name in PROTECTED[:3]:
                if any(base in (ROOT / name).read_text() for base in ROOTS):
                    raise ValueError("Current configuration references offload root")
            atomic(protection_path, protection)
        if a.phase in {"tensors", "all"}:
            run(ROOT, OUT, protection, direct=True)
        if a.phase in {"sequences", "all"}:
            run(ROOT, OUT, protection, direct=False)


if __name__ == "__main__":
    main()
