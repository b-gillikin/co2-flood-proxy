"""Independent timestamp/member/score audit of the complete monitoring census."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_comparison import load_script
from src.eo_inputs import sha256

OUT = ROOT / "results/limburg_monitoring_2026_10_28"


def independent_crps(y, members):
    """Direct quadratic empirical definition, independent of production helper."""
    return np.abs(members - y).mean(axis=0) - 0.5 * np.abs(
        members[:, None] - members[None, :]
    ).mean(axis=(0, 1))


def main():
    status = json.loads((OUT / "execution.json").read_text())
    if status["status"] != "completed" or status["completed_jobs"] != 42:
        raise ValueError("Audit requires all 42 completed jobs")
    runner = load_script("154_run_monitoring_analogues.py", "monitoring_audit_runner")
    prep = OUT / "preparation"
    meta = pd.read_parquet(prep / "cases.parquet")
    z = dict(np.load(prep / "inputs.npz"))
    cutoff = meta.cutoff_utc.dt.as_unit("ns").astype("int64").to_numpy()
    ends = meta.end_utc.dt.as_unit("ns").astype("int64").to_numpy()
    storms = meta.storm_id.to_numpy()
    gauges = meta.gauge.to_numpy()
    rivers = meta.physical_river.to_numpy()
    areas = meta.area_km2.to_numpy(float)
    hour = pd.Timedelta(hours=1).value
    checks = []
    if meta.case_id.duplicated().any():
        raise ValueError("Duplicate gauge-storm case")
    # Compare prepared Q signatures with source values for every opportunity.
    q = pd.read_parquet(ROOT / "results/storm_response/hourly_discharge.parquet")
    positions = q.index.get_indexer(meta.cutoff_utc)
    for u in [0, 6, 12, 24]:
        for cap in runner.information_states(u):
            for gauge in q.columns:
                ids = np.flatnonzero(meta.gauge.eq(gauge))
                values = q[gauge].to_numpy()
                prefix_last = np.maximum.accumulate(
                    np.where(np.isfinite(values), np.arange(len(values)), -1)
                )
                cap_positions = positions[ids] + cap
                expected_last = np.full(len(ids), -1)
                valid = (cap_positions >= 0) & (cap_positions < len(values))
                expected_last[valid] = prefix_last[cap_positions[valid]]
                np.testing.assert_array_equal(z[f"last_position_{u}_{cap}"][ids], expected_last)
                good = expected_last >= 24
                rows, s = ids[good], expected_last[good]
                observed = values[np.stack([s, s - 6, s - 24], axis=1)]
                expected = np.column_stack(
                    [
                        observed,
                        observed[:, 0] - observed[:, 1],
                        observed[:, 0] - observed[:, 2],
                        positions[rows] + u - s,
                    ]
                )
                np.testing.assert_allclose(z[f"q_{u}_{cap}"][rows], expected, equal_nan=True)
                if np.any(s > positions[rows] + cap):
                    raise ValueError("Hidden observation enters Q features")
    for source in sorted((OUT / "scores").iterdir()):
        spec = json.loads((source / "manifest.json").read_text())
        for path, digest in spec["inputs_and_source_sha256"].items():
            if sha256(ROOT / path) != digest:
                raise ValueError(f"Changed score input: {path}")
        for path, digest in spec["outputs_sha256"].items():
            if sha256(source / path) != digest:
                raise ValueError(f"Changed score output: {source.name}/{path}")
        frame = pd.read_parquet(source / "scores.parquet")
        if frame.duplicated(["case", "offset_h", "cap_h", "role", "target_k"]).any():
            raise ValueError("Duplicate scored state")
        if not np.isfinite(frame.crps).all() or (frame.crps < 0).any():
            raise ValueError("Invalid CRPS")
        ranked = frame[frame.target_k.gt(0)]
        if not (ranked.member_ids.map(len) == ranked.actual_k).all():
            raise ValueError("Incorrect donor count")
        if not ranked.member_ids.map(lambda ids: len(set(storms[ids])) == len(ids)).all():
            raise ValueError("Repeated donor storm")
        member_count = 0
        for u, group in ranked.groupby("offset_h"):
            qi = np.repeat(group.case.to_numpy(), group.actual_k.to_numpy())
            di = np.concatenate(group.member_ids.to_numpy()).astype(int)
            member_count += len(di)
            if np.any(cutoff[di] + 24 * hour > cutoff[qi]):
                raise ValueError("Donor verification not complete before query")
            if np.any(ends[di] + 12 * hour > cutoff[qi] + u * hour):
                raise ValueError("Donor episode not yet known closed")
            if np.any(storms[di] == storms[qi]):
                raise ValueError("Same-storm leakage")
            if spec["pool"] == "same_gauge":
                if np.any(gauges[di] != gauges[qi]):
                    raise ValueError("Incorrect same-gauge donors")
            elif np.any(rivers[di] == rivers[qi]):
                raise ValueError("Same physical river in cross-river pool")
        if spec["model"] != "baseline":
            _, available, _ = runner.eo_features(meta, spec["model"], spec["kind"])
            if not available[ranked.case.to_numpy()].all():
                raise ValueError("Unsupported EO query")
            di = np.concatenate(ranked.member_ids.to_numpy()).astype(int)
            if not available[di].all():
                raise ValueError("Unsupported EO donor")
        # Evenly spaced verification fixtures only; scientific scores use the census.
        samples = ranked.iloc[np.unique(np.linspace(0, len(ranked) - 1, 20).astype(int))]
        for row in samples.itertuples():
            ids = np.asarray(row.member_ids, int)
            y = z[f"outcome_{row.offset_h}"][row.case]
            members = z[f"outcome_{row.offset_h}"][ids] * areas[row.case] / areas[ids, None]
            crps = independent_crps(y, members)
            np.testing.assert_allclose(crps.mean(), row.crps, atol=1e-10, rtol=1e-10)
            np.testing.assert_allclose(
                row.crps * 3.6 / areas[row.case], row.crps_specific, atol=1e-12, rtol=1e-10
            )
            for h in [6, 12, 24]:
                np.testing.assert_allclose(
                    crps[h - 1], getattr(row, f"crps_h{h}"), atol=1e-10, rtol=1e-10
                )
        checks.append(
            dict(
                job=source.name,
                rows=len(frame),
                ranked_members=member_count,
                independent_score_fixtures=len(samples),
            )
        )
        print("audited", source.name, flush=True)
    report = dict(
        status="passed",
        jobs=checks,
        total_jobs=len(checks),
        source_sha256={str(Path(__file__).relative_to(ROOT)): sha256(Path(__file__))},
        git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        tracked_changes=subprocess.check_output(
            ["git", "diff", "--name-only"], cwd=ROOT, text=True
        ).splitlines(),
        note="All selected members and all prepared Q histories checked; independent direct CRPS fixtures. No scientific outcome sampling, new result or gate pass.",
    )
    (OUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
