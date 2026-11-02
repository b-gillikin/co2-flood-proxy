"""Versioned benchmark and local readouts, called by the durable controller."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    subprocess.run(
        [
            sys.executable,
            "scripts/198_summarize_applied_comparisons.py",
            "--plan",
            str(a.plan),
            "--output",
            str(a.output / "benchmark.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/216_summarize_local_comparisons.py",
            "--plan",
            str(a.plan),
            "--output",
            str(a.output / "local"),
        ],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
