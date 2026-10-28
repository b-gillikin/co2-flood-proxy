"""Wait for scoring, audit it, then publish full-census summaries and case traces."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/limburg_monitoring_2026_10_28"


def main():
    receipt = OUT / "postprocessing.json"

    def record(stage, status, **extra):
        receipt.write_text(
            json.dumps(
                dict(
                    stage=stage,
                    status=status,
                    updated_utc=datetime.now(timezone.utc).isoformat(),
                    **extra,
                ),
                indent=2,
            )
            + "\n"
        )

    record("scoring", "waiting")
    while True:
        status = json.loads((OUT / "execution.json").read_text())
        if status["status"] == "completed":
            break
        if status["status"] != "running":
            record("scoring", "failed", scoring=status)
            raise ValueError("Scoring not valid; do not publish partial findings")
        time.sleep(10)
    for script in [
        "156_audit_monitoring_analogues.py",
        "155_review_monitoring_analogues.py",
        "157_report_monitoring_cases.py",
    ]:
        record(script, "running")
        run = subprocess.run([sys.executable, "-u", str(ROOT / "scripts" / script)], cwd=ROOT)
        if run.returncode:
            record(script, "failed", returncode=run.returncode)
            raise SystemExit(run.returncode)
    record("all", "completed", emails_sent=False)


if __name__ == "__main__":
    main()
