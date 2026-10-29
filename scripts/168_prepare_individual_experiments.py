"""Prepare complete causal point-reference ledgers; no encoder or head fitting."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_individual_baselines import same_gauge_reference
from src.eo_inputs import sha256
from src.eo_signal_diagnostic import chronology

OUT = ROOT / "results/limburg_individual_experiments_v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        print("Use --run to prepare all 481 episodes, 8 gauges, 4 offsets and 3 scenarios")
        return
    plan_path = ROOT / "config/limburg_individual_encoder_experiments_v1.json"
    plan = json.loads(plan_path.read_text())
    source = ROOT / plan["shared"]["source"] / "preparation"
    meta = pd.read_parquet(source / "cases.parquet")
    storms = pd.read_parquet(source / "storms.parquet")
    bank = np.load(source / "bank.npz")
    counts = len(storms)
    sites = meta.iloc[:8]
    dest = OUT / "preparation"
    dest.mkdir(parents=True, exist_ok=True)
    identity = {
        str(p.relative_to(ROOT)): sha256(p)
        for p in (
            plan_path,
            source / "manifest.json",
            Path(__file__),
            ROOT / "src/eo_individual_baselines.py",
            ROOT / "src/scarcity.py",
        )
    }
    manifest = dest / "manifest.json"
    if manifest.exists():
        saved = json.loads(manifest.read_text())
        old_plan = json.loads((dest / "source_snapshot/plan.executed.json").read_text())
        for field in ["source", "primary_scenarios", "issue_offsets_h"]:
            assert old_plan["shared"][field] == plan["shared"][field], (
                "Frozen reference population changed"
            )
        assert saved["source_hashes"][str((source / "manifest.json").relative_to(ROOT))] == sha256(
            source / "manifest.json"
        ), "Canonical source changed"
        for p, h in saved["outputs"].items():
            assert sha256(dest / p) == h
        print("Verified existing preparation")
        return
    rows = []
    arrays = {}
    audit = []
    started = time.time()
    for scenario in plan["shared"]["primary_scenarios"]:
        for offset in plan["shared"]["issue_offsets_h"]:
            name = f"{scenario}__u{offset}"
            mean = np.full((counts, 8, 24), np.nan)
            median = mean.copy()
            fixed = mean.copy()
            fixed_median = mean.copy()
            traces = np.full((counts, 8, 5), -1, np.int32)
            times = storms.cutoff_utc + pd.Timedelta(hours=offset)
            for qi in range(counts):
                boundary = pd.Timestamp(f"{times.iloc[qi].year}-01-01", tz="UTC")
                closed = chronology(times, storms.end_utc, boundary)
                for gi in range(8):
                    a, b, ids, kind = same_gauge_reference(bank, qi, gi, offset, scenario)
                    c, d, _, _ = same_gauge_reference(bank, qi, gi, offset, scenario, closed)
                    factor = 3.6 / sites.area_km2.iloc[gi]
                    mean[qi, gi] = a * factor
                    median[qi, gi] = b * factor
                    fixed[qi, gi] = c * factor
                    fixed_median[qi, gi] = d * factor
                    traces[qi, gi, : len(ids)] = ids
                    row = meta.iloc[qi * 8 + gi].to_dict()
                    row.update(
                        scenario=scenario,
                        offset_h=offset,
                        issue_utc=times.iloc[qi],
                        response_end_utc=times.iloc[qi] + pd.Timedelta(hours=24),
                        query=qi,
                        site=gi,
                        reference_kind=kind,
                        reference_available=bool(np.isfinite(a).all()),
                        outcome_valid=bool(bank[f"outcome_valid_{offset}"][qi, gi]),
                    )
                    rows.append(row)
                if qi % 100 == 0:
                    print(name, qi, "/", counts, flush=True)
            # Replay held conventional mean trajectories on all recorded donors.
            held = pd.read_parquet(
                ROOT / plan["shared"]["source"] / f"scores/{name}/scores.parquet",
                columns=["case", "method", "target_k", "trace_kind", "trace_members"],
            )
            held = held[held.method.eq("conventional") & held.target_k.eq(5)]
            compared = violations = 0
            for r in held.itertuples():
                qi, gi = divmod(r.case, 8)
                if len(r.trace_members):
                    expected = (
                        bank[f"outcome_{offset}"][r.trace_members, gi].mean(0)
                        * 3.6
                        / sites.area_km2.iloc[gi]
                    )
                    compared += 1
                    violations += int(
                        not np.allclose(expected, mean[qi, gi], rtol=1e-9, atol=1e-10)
                    )
            audit.append(dict(job=name, replayed=compared, mismatches=violations))
            if violations:
                raise ValueError(f"Held conventional reference replay failed: {name}")
            for label, value in [
                ("mean", mean),
                ("median", median),
                ("fixed_mean", fixed),
                ("fixed_median", fixed_median),
                ("donors", traces),
            ]:
                arrays[name + "__" + label] = value
            print("completed", name, flush=True)
    pd.DataFrame(rows).to_parquet(dest / "cases.parquet", index=False)
    with (dest / "reference.npz.partial").open("wb") as f:
        np.savez_compressed(f, **arrays)
    (dest / "reference.npz.partial").replace(dest / "reference.npz")
    (dest / "baseline-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    manifest.write_text(
        json.dumps(
            dict(
                status="completed",
                created_utc=datetime.now(timezone.utc).isoformat(),
                rows=len(rows),
                elapsed_s=time.time() - started,
                source_hashes=identity,
                outputs={
                    n: sha256(dest / n)
                    for n in ["cases.parquet", "reference.npz", "baseline-audit.json"]
                },
            ),
            indent=2,
        )
        + "\n"
    )
    print("Preparation complete:", len(rows), "ledger rows", flush=True)


if __name__ == "__main__":
    main()
