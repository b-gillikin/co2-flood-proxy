"""Run ten isolated real-imagery engineering checks, then verify cache resume."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    results = []
    for model, (_, _, env) in ROUTES.items():
        command = [
            str(ROOT / f".venvs-eo/{env}/bin/python"),
            str(ROOT / "scripts/98_extract_limburg_eo_embeddings.py"),
            "--model",
            model,
            "--smoke",
        ]
        if not args.run:
            print(" ".join(command))
            continue
        record = {"model": model, "runtime": env}
        for phase in ("real_forward", "resume"):
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=300)
            log = ROOT / f"logs/eo-engineering/{model}-{phase}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(result.stdout + result.stderr)
            lines = [
                json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")
            ]
            record[phase] = {"exit_code": result.returncode, "result": lines[-1] if lines else None}
            if result.returncode:
                break
        run = record.get("resume", {}).get("result", {}).get("run")
        if run:
            receipts = list(
                (ROOT / "data/processed/limburg_eo_embeddings" / model / run / "images").rglob(
                    "*.json"
                )
            )
            if len(receipts) == 1:
                saved = json.loads(receipts[0].read_text())
                record["embedding"] = {
                    k: saved.get(k) for k in ("status", "dimension", "repeatable", "sha256")
                }
                record["embedding"]["valid_fraction"] = saved["identity"]["metadata"][
                    "valid_fraction"
                ]
        record["passed"] = bool(
            record.get("resume", {}).get("result", {}).get("resumed") == 1
            and record["real_forward"]["exit_code"] == 0
            and record.get("embedding", {}).get("repeatable") is True
        )
        print(json.dumps(record), flush=True)
        results.append(record)
    if args.run:
        output = ROOT / "docs/reviews/limburg-eo-real-input-checks-2026-10-16.json"
        output.write_text(
            json.dumps(
                {
                    "checked_utc": datetime.now(timezone.utc).isoformat(),
                    "purpose": "Engineering only; one named real composite fixture per model, no scientific performance comparison",
                    "results": results,
                },
                indent=2,
            )
            + "\n"
        )
        return int(not all(r["passed"] for r in results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
