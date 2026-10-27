"""Resume the final audited follow-up phase without replaying completed scoring."""

from __future__ import annotations

import fcntl
import json
import os
import runpy
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256

LOG = ROOT / "logs/eo-followup-2026-10-27"


def verify_completed(folder):
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest["status"] != "completed":
        raise ValueError("Cannot resume from incomplete results: " + str(folder))
    aliases = {
        "event_inventory": ROOT / "results/basin_ai_event_interpretation_ready/event_inventory.csv",
        "response": ROOT
        / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet",
    }
    for name, expected in manifest["input_sha256"].items():
        if sha256(aliases.get(name, ROOT / name)) != expected:
            raise ValueError("Changed completed-run input: " + name)
    for name, expected in manifest["outputs_sha256"].items():
        if sha256(folder / name) != expected:
            raise ValueError("Changed completed-run output: " + name)


def main():
    with (LOG / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = LOG / "progress.json"
        state = json.loads(path.read_text())
        if (
            state["tasks"]["rainfall_benchmark"]["status"] != "completed"
            or state["tasks"]["review_rain168"]["status"] != "completed"
        ):
            raise ValueError("This recovery only resumes after completed rainfall scoring/review")
        if shutil.disk_usage(ROOT).free < 60 * 2**30:
            raise RuntimeError("Working reserve still unavailable; no results were restarted")

        def save():
            state["updated_utc"] = datetime.now(timezone.utc).isoformat()
            state["free_gib"] = round(shutil.disk_usage(ROOT).free / 2**30, 1)
            temp = path.with_suffix(".partial")
            temp.write_text(json.dumps(state, indent=2) + "\n")
            temp.replace(path)

        state.setdefault("resume_history", []).append(
            {
                "previous_status": state["status"],
                "previous_error": state.pop("error", None),
                "resumed_utc": datetime.now(timezone.utc).isoformat(),
                "recovery_source_sha256": sha256(Path(__file__)),
            }
        )
        state.update(status="running", pid=os.getpid())
        task = {"status": "verifying_completed_inputs"}
        state["tasks"]["matched_archives_and_routes"] = task
        save()
        try:
            verify_completed(ROOT / "results/eo_analogue_comparison_rain168_v1")
            verify_completed(ROOT / "results/eo_review_provenance_v2/rain168")
            command = [
                str(ROOT / ".venvs-eo/terramind/bin/python"),
                "-u",
                "scripts/137_eo_archive_and_route_followup.py",
            ]
            with (LOG / "matched_archives_and_routes.log").open("a") as log:
                child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                task.update(status="running", worker_pid=child.pid, command=command)
                save()
                if child.wait():
                    raise RuntimeError("Final follow-up phase failed; inspect its log")
            task["status"] = "completed"
            runpy.run_path(str(ROOT / "scripts/138_run_limburg_followup.py"))["write_memo"]()
            state["status"] = "completed"
            save()
        except BaseException as exc:
            task["status"] = "failed"
            state.update(status="failed", error=str(exc))
            save()
            raise


if __name__ == "__main__":
    main()
