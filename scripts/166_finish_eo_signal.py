"""Run and independently review the authorized model-specific EO diagnostics."""

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

ROOT = Path(__file__).resolve().parents[1]
OUT = (
    ROOT / json.loads((ROOT / "config/limburg_eo_signal_diagnostic_v1.json").read_text())["output"]
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "environment.json").write_text(
        json.dumps(
            dict(
                python=sys.version,
                platform=platform.platform(),
                numpy=np.__version__,
                pandas=pd.__version__,
                scipy=scipy.__version__,
            ),
            indent=2,
        )
        + "\n"
    )
    receipt = OUT / "pipeline.json"
    for script in ["164_diagnose_eo_signal.py", "165_review_eo_signal.py"]:
        record = dict(
            stage=script, status="running", updated_utc=datetime.now(timezone.utc).isoformat()
        )
        receipt.write_text(json.dumps(record, indent=2) + "\n")
        result = subprocess.run([sys.executable, "-u", str(ROOT / "scripts" / script)], cwd=ROOT)
        if result.returncode:
            record.update(status="failed", returncode=result.returncode)
            receipt.write_text(json.dumps(record, indent=2) + "\n")
            raise SystemExit(result.returncode)
    receipt.write_text(
        json.dumps(
            dict(
                status="completed",
                updated_utc=datetime.now(timezone.utc).isoformat(),
                emails_sent=False,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
