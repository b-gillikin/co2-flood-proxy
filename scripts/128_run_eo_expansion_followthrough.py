"""Stage and audit supplemental observations without competing for the model GPU."""

import fcntl
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "logs/eo-expansion-followthrough"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = {"pid": os.getpid(), "started_utc": datetime.now(timezone.utc).isoformat()}

        def save(status, **extra):
            state.update(status=status, updated_utc=datetime.now(timezone.utc).isoformat(), **extra)
            p = OUT / "progress.partial"
            p.write_text(json.dumps(state, indent=2) + "\n")
            p.replace(OUT / "progress.json")

        env = {
            **os.environ,
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "GDAL_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        commands = [
            (
                "staging",
                [
                    "/opt/homebrew/opt/azure-cli/libexec/bin/python",
                    "scripts/126_stage_eo_expansion.py",
                    "--run",
                ],
            ),
            (
                "auditing",
                [
                    str(ROOT / ".venvs-eo/terramind/bin/python"),
                    "scripts/127_audit_eo_expansion_pixels.py",
                ],
            ),
        ]
        for phase, command in commands:
            save(phase, command=command)
            with (OUT / (phase + ".log")).open("a") as log:
                code = subprocess.run(
                    command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
                ).returncode
            if code:
                save("failed", failed_phase=phase, exit_code=code)
                return
        save(
            "staged_and_audited",
            next_action="Build validated per-product model input adapters and catchment coverage; extraction/scoring not yet run",
        )


if __name__ == "__main__":
    main()
