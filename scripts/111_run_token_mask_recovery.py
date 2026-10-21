"""Serial MPS recovery queue, separate from the unchanged running Presto queue."""

import fcntl
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs/eo-token-recovery"


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / ".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = {"pid": os.getpid(), "models": {}, "order": ["olmoearth", "galileo"]}

        def update():
            state["updated_utc"] = datetime.now(timezone.utc).isoformat()
            temp = LOGS / "progress.partial"
            temp.write_text(json.dumps(state, indent=2) + "\n")
            temp.replace(LOGS / "progress.json")

        for model, env in [("olmoearth", "modern"), ("galileo", "galileo")]:
            python = ROOT / f".venvs-eo/{env}/bin/python"
            state["active_model"] = model
            state["models"][model] = {"status": "extracting"}
            update()
            with (LOGS / f"{model}.log").open("a") as log:
                result = subprocess.run(
                    [
                        str(python),
                        "-u",
                        "scripts/110_extract_token_consistent_sequences.py",
                        "--model",
                        model,
                        "--run",
                    ],
                    cwd=ROOT,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env={**os.environ, "PYTORCH_ENABLE_MPS_FALLBACK": "0"},
                )
                state["models"][model]["extraction_exit"] = result.returncode
                state["models"][model]["status"] = (
                    "extract_failed" if result.returncode else "aggregating"
                )
                update()
                if result.returncode:
                    continue
                result = subprocess.run(
                    [
                        str(ROOT / ".venvs-eo/terramind/bin/python"),
                        "-u",
                        "scripts/101_aggregate_limburg_eo_catchments.py",
                        "--model",
                        model,
                        "--sequences",
                        "data/processed/limburg_eo_token_consistent_sequences",
                        "--out",
                        f"results/eo_catchment_representations/per_model/{model}/token_consistent",
                    ],
                    cwd=ROOT,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                state["models"][model]["aggregation_exit"] = result.returncode
                state["models"][model]["status"] = (
                    "aggregate_failed" if result.returncode else "completed"
                )
                update()
        state["active_model"] = None
        state["status"] = "finished"
        update()


if __name__ == "__main__":
    main()
