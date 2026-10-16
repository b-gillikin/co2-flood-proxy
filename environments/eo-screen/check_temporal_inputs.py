"""Engineering checks on two real frames for ten models and twelve for native models."""

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES  # noqa: E402

NATIVE = {"olmoearth", "galileo", "prithvi", "anysat", "presto"}


def check(model):
    runtime = ROUTES[model][2]
    record = {"model": model, "runtime": runtime, "checks": {}}
    for kind in ["two", "monthly"] if model in NATIVE else ["two"]:
        command = [
            str(ROOT / f".venvs-eo/{runtime}/bin/python"),
            str(ROOT / "scripts/100_extract_limburg_eo_sequences.py"),
            "--model",
            model,
            "--smoke",
            "--smoke-kind",
            kind,
        ]
        phases = {}
        for phase in ["forward", "resume"]:
            env = {**os.environ, "MPLCONFIGDIR": "/private/tmp/limburg-mpl"}
            result = subprocess.run(
                command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=900
            )
            log = ROOT / f"logs/eo-temporal/{model}-{kind}-{phase}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(result.stdout + result.stderr)
            values = [
                json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")
            ]
            phases[phase] = {
                "exit_code": result.returncode,
                "result": values[-1] if values else None,
            }
            if result.returncode:
                break
        last = (
            phases.get("resume", {}).get("result") or phases.get("forward", {}).get("result") or {}
        )
        run = last.get("run")
        if run:
            paths = list(
                (
                    ROOT
                    / "data/processed/limburg_eo_sequences"
                    / model
                    / run
                    / f"engineering_{kind}_real_months"
                ).glob("*/*.json")
            )
            finite = [
                json.loads(p.read_text())
                for p in paths
                if json.loads(p.read_text()).get("status") == "finite_sequence"
            ]
            if len(finite) == 1:
                phases["embedding"] = {
                    k: finite[0][k] for k in ["dimension", "repeatable", "sha256"]
                }
                phases["frames"] = len(finite[0]["identity"]["frames"])
        phases["passed"] = bool(
            phases.get("resume", {}).get("exit_code") == 0
            and last.get("resumed") == 1
            and phases.get("embedding", {}).get("repeatable")
        )
        record["checks"][kind] = phases
    record["passed"] = all(r["passed"] for r in record["checks"].values())
    print(json.dumps(record), flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        print(
            "Ten two-frame checks and five native twelve-month checks; each repeated and resumed."
        )
        return 0
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(check, ROUTES))
    report = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Engineering only; held imagery, no outcomes or model ranking",
        "results": results,
    }
    (ROOT / "docs/reviews/limburg-eo-temporal-checks-2026-10-16.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    return int(not all(r["passed"] for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
