"""Audit source clocks, complete verification, masks and saved donor traces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.monitoring_analogues import ensemble_metrics
from src.scarcity import forward_hold, scenario_keep

OUT = ROOT / json.loads((ROOT / "config/limburg_scarcity_v1.json").read_text())["output"]


def preparation_audit():
    prep = OUT / "preparation"
    manifest = json.loads((prep / "manifest.json").read_text())
    for name, digest in manifest["sources_sha256"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f"Prepared source changed: {name}")
    for name, digest in manifest["outputs_sha256"].items():
        if sha256(prep / name) != digest:
            raise ValueError(f"Prepared artifact changed: {name}")
    meta = pd.read_parquet(prep / "cases.parquet")
    storms = pd.read_parquet(prep / "storms.parquet")
    bank = dict(np.load(prep / "bank.npz"))
    old = dict(np.load(ROOT / "results/limburg_monitoring_2026_10_28/preparation/inputs.npz"))
    config = json.loads((prep / "config.json").read_text())
    cutoff = np.array([t.value for t in storms.cutoff_utc])
    end = np.array([t.value for t in storms.end_utc])
    hour = pd.Timedelta(hours=1).value
    q = pd.read_parquet(ROOT / "results/storm_response/hourly_discharge.parquet")
    combined = q.copy()
    for site in config["maas_sources"]:
        f = pd.read_parquet(ROOT / f"results/meuse_context_2026_10_27/{site}_hourly.parquet")
        combined[site] = f.q_strict.reindex(q.index)
    for u in config["issue_offsets_h"]:
        np.testing.assert_array_equal(
            bank[f"outcome_{u}"].reshape(len(meta), 24), old[f"outcome_{u}"]
        )
        for qi, row in enumerate(storms.itertuples()):
            issue = row.cutoff_utc + pd.Timedelta(hours=u)
            direct = combined.loc[issue - pd.Timedelta(hours=config["q_history_h"] - 1) : issue]
            np.testing.assert_array_equal(direct.to_numpy().T, bank[f"q_{u}"][qi])
        for years in [0, *config["historical_caps_years"]]:
            allowed = (cutoff[None] + 24 * hour <= cutoff[:, None]) & (
                end[None] + 12 * hour <= cutoff[:, None] + u * hour
            )
            allowed &= storms.storm_id.to_numpy()[None] != storms.storm_id.to_numpy()[:, None]
            if years:
                earliest = np.array(
                    [(t - pd.DateOffset(years=years)).value for t in storms.cutoff_utc]
                )
                allowed &= cutoff[None] >= earliest[:, None]
            np.testing.assert_array_equal(allowed, bank[f"prior_{u}_{years}"])
    mask_records = []
    original = np.isfinite(q.to_numpy()).T
    for path in sorted(prep.glob("*pct.npy")):
        hidden = np.unpackbits(np.load(path), axis=-1, count=len(q)).astype(bool)
        if np.any(~np.isin(hidden, [False, True])):
            raise ValueError("Invalid binary mask")
        per_rep = hidden.mean(axis=(1, 2))
        observed_hidden = (
            np.einsum("rgt,gt->r", hidden.astype(float), original.astype(float), optimize=True)
            / original.sum()
        )
        mask_records.append(
            dict(
                name=path.stem,
                replicas=len(hidden),
                mean_fraction=float(per_rep.mean()),
                min_fraction=float(per_rep.min()),
                max_fraction=float(per_rep.max()),
                originally_observed_hidden_fraction=float(observed_hidden.mean()),
            )
        )
    report = dict(
        status="passed",
        kind="preparation_only_not_empirical_performance",
        cases=len(meta),
        storms=len(storms),
        mask_records=mask_records,
        source_manifest_sha256=sha256(prep / "manifest.json"),
    )
    (OUT / "preparation-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        "Prepared inputs, all issue histories, all chronology matrices and mask inventories audited",
        flush=True,
    )
    return meta, storms, bank, config


def audit_job(path, meta, storms, bank):
    prep = OUT / "preparation"
    spec = json.loads((path / "manifest.json").read_text())
    for name, digest in spec["sources_sha256"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f"Changed score source: {name}")
    for name, digest in spec["outputs_sha256"].items():
        if sha256(path / name) != digest:
            raise ValueError("Changed score output")
    frame = pd.read_parquet(path / "scores.parquet")
    u = spec["offset_h"]
    group = spec["group"]
    years = group.get("years", 0)
    truth = bank[f"outcome_valid_{u}"]
    prior = bank[f"prior_{u}_{years}"]
    expected = set(np.flatnonzero(truth.reshape(-1)))
    if set(frame["case"]) != expected:
        raise ValueError("A scored job lost or added a verified case")
    if frame.duplicated(["case", "method", "target_k"]).any():
        raise ValueError("Duplicate case/method/K")
    ranked = frame[frame.trace_kind.eq("analogue")]
    qi = np.repeat(ranked.storm.to_numpy(), ranked.trace_members.map(len).to_numpy())
    di = np.concatenate(ranked.trace_members.to_numpy()).astype(int)
    if not prior[qi, di].all():
        raise ValueError("Illegal prior or same-storm donor")
    gi = np.repeat((ranked["case"].to_numpy() % 8), ranked.trace_members.map(len).to_numpy())
    if not truth[di, gi].all():
        raise ValueError("Missing donor response")
    packed = (
        np.load(prep / (group.get("mask_name", group["name"]) + ".npy"), mmap_mode="r")
        if group["family"] in ["missing", "combined_missing"]
        else None
    )
    epochs = np.load(prep / "source_epoch_hours.npy")
    fixtures = frame.iloc[np.unique(np.linspace(0, len(frame) - 1, 96).astype(int))]
    for row in fixtures.itertuples():
        qi, gi = divmod(row.case, 8)
        y = bank[f"outcome_{u}"][qi, gi]
        if row.trace_kind == "none":
            if np.isfinite(row.trace_crps):
                raise ValueError("Missing forecast has finite trace score")
            continue
        if row.trace_kind == "persistence":
            pos = bank[f"positions_{u}"][qi]
            keep = scenario_keep(group, pos, epochs[pos], packed, gi)
            last = forward_hold(np.where(keep[0, gi], bank[f"q_{u}"][qi, gi], np.nan))[-1]
            members = np.full((1, 24), last)
        else:
            ids = (
                np.flatnonzero(prior[qi] & truth[:, gi])
                if row.trace_kind == "generic"
                else row.trace_members
            )
            members = bank[f"outcome_{u}"][ids, gi]
        expected_score = ensemble_metrics(y, members)["crps"]
        np.testing.assert_allclose(row.trace_crps, expected_score, rtol=1e-10, atol=1e-10)
    z = dict(np.load(path / "paired_replicates.npz"))
    np.testing.assert_allclose(
        z["paired"][..., 0],
        z["paired"][..., 1] + z["paired"][..., 2],
        atol=2e-7,
        rtol=1e-5,
        equal_nan=True,
    )
    return dict(
        job=path.name,
        rows=len(frame),
        verified_cases=len(expected),
        trace_members_checked=len(di),
        independent_score_fixtures=len(fixtures),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preparation-only", action="store_true")
    p.add_argument("--job")
    args = p.parse_args()
    meta, storms, bank, config = preparation_audit()
    if args.preparation_only:
        return
    paths = [OUT / "scores" / args.job] if args.job else sorted((OUT / "scores").iterdir())
    if not args.job:
        expected = json.loads((OUT / "preparation/manifest.json").read_text())["jobs"]
        if len(paths) != expected:
            raise ValueError("Full report requires the complete configured queue")
    reports = []
    for path in paths:
        reports.append(audit_job(path, meta, storms, bank))
        print("audited", path.name, flush=True)
    name = "benchmark-audit.json" if args.job else "audit.json"
    (OUT / name).write_text(
        json.dumps(
            dict(
                status="passed",
                complete_matrix=not bool(args.job),
                jobs=reports,
                source_sha256=sha256(Path(__file__)),
                note="Every selected first-replication donor identity checked; direct scalar CRPS fixtures. All masks retain the full eligible case census. No new chapter gate or positive EO finding asserted.",
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
