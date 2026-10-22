"""Publish a complete comparison output set without mixing execution generations."""

import fcntl
import json
from contextlib import contextmanager
from pathlib import Path

from src.eo_inputs import sha256
from src.eo_integrity import fresh_output


@contextmanager
def comparison_output(destination, *, executed):
    """Planning cannot replace a scientific receipt; failed writes preserve prior runs."""
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (destination.parent / ("." + destination.name + ".publish.lock")).open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        target = destination if executed else destination / "planning"
        with fresh_output(target) as stage:
            yield stage
            plan = json.loads((stage / "experiment_plan.json").read_text())
            if bool(plan["executed"]) != executed:
                raise ValueError("Comparison plan/publication mode mismatch")
            status = (
                "planned"
                if not executed
                else ("completed" if plan["scored_sets"] else "no_estimable_results")
            )
            report = {
                "status": status,
                "purpose": plan["purpose"],
                "input_sha256": plan["input_sha256"],
                "outputs_sha256": {p.name: sha256(p) for p in stage.iterdir() if p.is_file()},
                "scored_sets": plan["scored_sets"],
            }
            (stage / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
