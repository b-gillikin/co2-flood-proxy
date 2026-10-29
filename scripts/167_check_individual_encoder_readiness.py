"""Validate ten experiment designs and inventory held assets; never launches jobs."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_experiment_readiness import inspect_context_support, inspect_readiness, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/reviews/limburg-ten-experiment-readiness-2026-10-29.json",
    )
    parser.add_argument(
        "--with-coverage",
        action="store_true",
        help="Join existing context vectors to the full census; requires EO analysis environment",
    )
    args = parser.parse_args()
    plan_path = ROOT / "config/limburg_individual_encoder_experiments_v1.json"
    receipt = inspect_readiness(ROOT, json.loads(plan_path.read_text()))
    if args.with_coverage:
        receipt["existing_context_support"] = inspect_context_support(
            ROOT, json.loads(plan_path.read_text())
        )
    receipt.update(
        checked_utc=datetime.now(timezone.utc).isoformat(), plan_sha256=sha256(plan_path)
    )
    for source in (Path(__file__), ROOT / "src/eo_experiment_readiness.py"):
        receipt["source_hashes"][str(source.relative_to(ROOT))] = sha256(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"{receipt['designs_validated']}/10 designs checked; this checker launches no work")
    print(f"Free disk: {receipt['disk_free_gib']:.1f} GiB; status: {receipt['status']}")
    for e in receipt["experiments"]:
        print(
            e["id"],
            e["model"],
            e["status"],
            "new encoding" if e["requires_encoding"] else "reuse vectors",
        )


if __name__ == "__main__":
    main()
