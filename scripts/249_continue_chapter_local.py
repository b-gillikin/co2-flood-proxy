#!/usr/bin/env python3
"""Continue the local receiving-case maps after checked triplet acquisition."""

import fcntl
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/limburg_chapter_sized_v1/local"
INPUT = ROOT / "data/raw/limburg_chapter_local_triplets_v1"


def state(status, **details):
    value = {"status": status, "unix_time": time.time(), **details}
    path = OUT / "queue_status.json"
    partial = path.with_suffix(".partial")
    partial.write_text(json.dumps(value, indent=2) + "\n")
    partial.replace(path)
    print(json.dumps(value), flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / ".local-queue.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state("waiting_for_local_triplets")
    while not (INPUT / "complete.json").exists():
        time.sleep(30)
    for attempt in range(1, 4):
        state("running", attempt=attempt)
        log = ROOT / "results/limburg_chapter_sized_v1/engineering/local-mapping.log"
        with log.open("a") as stream:
            result = subprocess.run([str(ROOT / ".venvs-applied/copernicus/bin/python"),
                                     str(ROOT / "scripts/248_run_chapter_local.py")], cwd=ROOT,
                                    stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode == 0 and (OUT / "complete.json").exists():
            state("completed")
            return
        state("retrying" if attempt < 3 else "failed", attempt=attempt, exit_code=result.returncode)
        if attempt < 3:
            time.sleep(60)


if __name__ == "__main__":
    main()
