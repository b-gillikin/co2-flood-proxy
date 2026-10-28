"""Finish the corrected scarcity census, audit it and produce the evidence review."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / json.loads((ROOT / "config/limburg_scarcity_v1.json").read_text())["output"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = OUT / "pipeline.json"
    for script, arguments in [
        ("159_prepare_scarcity.py", []),
        ("161_audit_scarcity.py", ["--preparation-only"]),
        ("160_run_scarcity.py", ["--workers", "2"]),
        ("161_audit_scarcity.py", []),
        ("162_review_scarcity.py", []),
    ]:
        record = dict(
            stage=script, status="running", updated_utc=datetime.now(timezone.utc).isoformat()
        )
        receipt.write_text(json.dumps(record, indent=2) + "\n")
        result = subprocess.run(
            [sys.executable, "-u", str(ROOT / "scripts" / script), *arguments], cwd=ROOT
        )
        if result.returncode:
            record.update(status="failed", returncode=result.returncode)
            receipt.write_text(json.dumps(record, indent=2) + "\n")
            raise SystemExit(result.returncode)
    receipt.write_text(
        json.dumps(
            dict(
                status="completed",
                emails_sent=False,
                updated_utc=datetime.now(timezone.utc).isoformat(),
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
