"""Create task-only overlays without modifying current extraction runtimes.

The held, pinned EO environment supplies unchanged packages through a .pth.
Task installs go in the new overlay. Record full visible versions and the base
path; these overlays are not claimed to be independent copies of their base.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "environments/applied"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for task, base in [("spatial", "terramind"), ("galileo", "galileo"), ("copernicus", "modern")]:
        source = ROOT / ".venvs-eo" / base
        dest = ROOT / ".venvs-applied" / task
        if not (dest / "bin/python").exists():
            subprocess.run([str(source / "bin/python"), "-m", "venv", str(dest)], check=True)
        (visible,) = source.glob("lib/python*/site-packages")
        (target,) = dest.glob("lib/python*/site-packages")
        if target.parent.name != visible.parent.name:
            raise ValueError("Overlay/base Python minor versions differ")
        (target / "held-runtime.pth").write_text(str(visible.resolve()) + "\n")
        versions = subprocess.check_output(
            [str(dest / "bin/python"), "-m", "pip", "freeze"], text=True
        )
        (out / f"{task}-visible-freeze.txt").write_text(versions)
        check = subprocess.run(
            [str(dest / "bin/python"), "-m", "pip", "check"], capture_output=True, text=True
        )
        records.append(
            dict(
                task=task,
                overlay=str(dest.relative_to(ROOT)),
                base=str(source.relative_to(ROOT)),
                python=subprocess.check_output(
                    [str(dest / "bin/python"), "--version"], text=True
                ).strip(),
                dependency_check_returncode=check.returncode,
                dependency_check=check.stdout + check.stderr,
            )
        )
    (out / "runtimes.json").write_text(json.dumps(records, indent=2) + "\n")
    if any(r["dependency_check_returncode"] for r in records):
        raise RuntimeError("Inspect recorded dependency conflicts before task launch")


if __name__ == "__main__":
    main()
