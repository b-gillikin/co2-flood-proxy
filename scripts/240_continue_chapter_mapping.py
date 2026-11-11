#!/usr/bin/env python3
"""Wait for verified final source fits, then resume both external mapping censuses."""

from __future__ import annotations

import fcntl
import importlib.util
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/limburg_chapter_sized_v1"
PYTHON = ROOT / ".venvs-applied/copernicus/bin/python"


def source_queue():
    spec = importlib.util.spec_from_file_location("final_source_queue", ROOT / "scripts/236_run_chapter_final_queue.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def status(state, **details):
    target = OUT / "mapping_queue_status.json"
    temporary = target.with_suffix(".partial")
    record = {"status": state, "unix_time": time.time(), **details}
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(target)
    print(json.dumps(record), flush=True)


def mapping_complete(kind, source):
    path = OUT / "external" / f"{kind}-complete.json"
    if not path.exists():
        return False
    record = json.loads(path.read_text())
    expected = {str(seed): source.sha256(OUT / "final_source" / f"{kind}-{seed}" / "model.pt")
                for seed in (42, 1729, 31415)}
    return (record.get("status") == "full_external_predictions_complete"
            and record.get("jobs") == 2214 and record.get("checkpoints") == expected)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / ".mapping-queue.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    source = source_queue()
    last_complete = None
    while True:
        complete = [f"{kind}-{seed}" for kind, seed in source.JOBS if source.completed(kind, seed)]
        if len(complete) == len(source.JOBS):
            break
        if complete != last_complete:
            status("waiting_for_source_fits", complete_jobs=complete, total_jobs=len(source.JOBS))
            last_complete = complete
        time.sleep(30)
    for kind in ("unet", "native"):
        if mapping_complete(kind, source):
            status("skipped_completed", model=kind)
            continue
        for attempt in range(1, 4):
            status("running", model=kind, attempt=attempt)
            log = OUT / "engineering" / f"external-{kind}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a") as stream:
                result = subprocess.run([str(PYTHON), str(ROOT / "scripts/237_run_chapter_external.py"),
                                         "--model", kind, "--device", "mps"], cwd=ROOT,
                                        stdout=stream, stderr=subprocess.STDOUT)
            if result.returncode == 0 and mapping_complete(kind, source):
                status("completed", model=kind)
                break
            status("retrying" if attempt < 3 else "failed", model=kind,
                   attempt=attempt, exit_code=result.returncode)
            if attempt == 3:
                return
            time.sleep(60)
    status("all_external_mapping_completed")


if __name__ == "__main__":
    main()
