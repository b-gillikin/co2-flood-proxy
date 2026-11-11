#!/usr/bin/env python3
"""Run recoverable archive scoring, final paired summaries and map review."""

import fcntl
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venvs-applied/copernicus/bin/python"
OUT = ROOT / "results/limburg_chapter_sized_v1/evaluation"


def state(status, **details):
    record = {"status": status, "unix_time": time.time(), **details}
    path = OUT / "queue_status.json"
    temp = path.with_suffix(".partial")
    temp.write_text(json.dumps(record, indent=2) + "\n")
    temp.replace(path)
    print(json.dumps(record), flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / ".evaluation-queue.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    jobs = [("archive_scoring", "242_score_chapter_archives.py", ["--workers", "2"]),
            ("paired_summary", "244_summarize_chapter_scores.py", []),
            ("map_review", "246_review_chapter_maps.py", [])]
    for name, script, arguments in jobs:
        for attempt in range(1, 4):
            state("running", stage=name, attempt=attempt)
            log = ROOT / f"results/limburg_chapter_sized_v1/engineering/{name}.log"
            with log.open("a") as stream:
                result = subprocess.run([str(PYTHON), str(ROOT / "scripts" / script), *arguments],
                                        cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            if result.returncode == 0:
                state("stage_completed", stage=name)
                break
            state("retrying" if attempt < 3 else "failed", stage=name,
                  attempt=attempt, exit_code=result.returncode)
            if attempt == 3:
                return
            time.sleep(60)
    state("external_evaluation_completed")


if __name__ == "__main__":
    main()
