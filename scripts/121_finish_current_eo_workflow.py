"""Finish the authorized case review after the already-running EO comparison.

Waits on its publication lock, rejects old/failed results, then runs script 120.
Never launches duplicate scoring, retries a failed analysis, or changes inputs.
"""

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--not-before", required=True, help="UTC start bound for this execution")
    args = parser.parse_args()
    bound = datetime.fromisoformat(args.not_before)
    out = ROOT / "results/eo_analogue_comparison"
    status_path = ROOT / "logs/eo-current-archive-workflow-2026-10-22.json"
    state = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "comparison_not_before_utc": args.not_before,
        "pid": os.getpid(),
        "step_1": "verified_and_merged_all_ten",
        "step_2": "running",
        "step_3": "queued_after_comparison",
    }

    def save(**updates):
        state.update(updates, updated_utc=datetime.now(timezone.utc).isoformat())
        temp = status_path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.replace(status_path)

    save(status="waiting_for_comparison")
    try:
        with (out.parent / ("." + out.name + ".publish.lock")).open("r+") as lock:
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    save(
                        cached_retrieval_configurations=sum(
                            1
                            for _ in (ROOT / "data/processed/eo_retrieval_cache").glob(
                                "*/manifest.json"
                            )
                        )
                    )
                    time.sleep(20)
            plan = json.loads((out / "experiment_plan.json").read_text())
            receipt = json.loads((out / "manifest.json").read_text())
            if (
                datetime.fromisoformat(plan["created_utc"]) < bound
                or receipt["status"] != "completed"
                or not plan["executed"]
                or plan["partial_model_population"]
            ):
                raise ValueError("The current complete ten-model comparison did not publish")
            save(
                status="reviewing_actual_analogues",
                step_2="completed",
                step_3="running",
                comparison_manifest_sha256=sha256(out / "manifest.json"),
            )
            with (ROOT / "logs/eo-actual-analogue-review-2026-10-22.log").open("w") as log:
                subprocess.run(
                    [sys.executable, str(ROOT / "scripts/120_review_eo_analogues.py")],
                    cwd=ROOT,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
            review = ROOT / "results/eo_analogue_review/manifest.json"
            if json.loads(review.read_text())["status"] != "completed":
                raise ValueError("Actual analogue review did not complete")
            save(status="completed", step_3="completed", review_manifest_sha256=sha256(review))
    except BaseException as exc:
        save(status="failed", error=str(exc))
        raise
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
