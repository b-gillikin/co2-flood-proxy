"""Matched local-reference comparisons, only where all learners are available.

No model selection; fold/seed groups retain separate dependent July2021 cases.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_execution import atomic


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    plan = json.loads(a.plan.read_text())
    groups = {}
    physical = {}
    for j in plan["jobs"]:
        if j["learner"] == "physical" or j["budget"] != 1.0:
            continue
        groups.setdefault((j["task"], j["fold"], j["seed"]), {})[j["learner"]] = ROOT / j["output"]
        path = ROOT / j["output"] / "local-physical/manifest.json"
        if path.exists():
            physical[(j["task"], j["fold"])] = path
    ledger = []
    for (task, fold, seed), models in sorted(groups.items()):
        missing = [m for m, d in models.items() if not (d / "local/complete.json").exists()]
        phy = physical.get((task, fold))
        if missing or phy is None:
            ledger.append(
                dict(
                    task=task,
                    fold=fold,
                    seed=seed,
                    status="pending",
                    missing_learners=missing,
                    physical_available=phy is not None,
                )
            )
            continue
        entries = []
        for m, d in models.items():
            rows = json.loads((d / "local/manifest.json").read_text())
            entries += [dict(r, model=m) for r in rows]
        entries += [dict(r, model="physical") for r in json.loads(phy.read_text())]
        name = f"{task}-{fold}-{seed}"
        mp = a.output / f"{name}-manifest.json"
        atomic(mp, entries)
        out = a.output / f"{name}-reference-agreement.json"
        cache_root = ROOT / "results/applied_study_v3/local-comparison-cache"
        cache_root.mkdir(exist_ok=True)
        key = hashlib.sha256(
            mp.read_bytes()
            + b"".join((d / "local/complete.json").read_bytes() for d in models.values())
        ).hexdigest()
        cached = cache_root / f"{name}-{key}.json"
        if cached.exists():
            out.write_bytes(cached.read_bytes())
        else:
            subprocess.run(
                [
                    str(ROOT / ".venv-foundation/bin/python"),
                    "scripts/195_score_local_reference_agreement.py",
                    str(mp),
                    "--output",
                    str(out),
                ],
                cwd=ROOT,
                check=True,
            )
            cached.write_bytes(out.read_bytes())
        ledger.append(
            dict(
                task=task,
                fold=fold,
                seed=seed,
                status="matched_complete",
                output=str(out.relative_to(ROOT)),
            )
        )
    atomic(
        a.output / "ledger.json",
        dict(
            groups=ledger,
            interpretation="All planned full-label fold/seed groups retained. Pending groups are not a smaller final sample. Same-case common pixels, source/QA coverage and time offsets explicit. Local dates/granules are not independent floods; no country ranking.",
        ),
    )


if __name__ == "__main__":
    main()
