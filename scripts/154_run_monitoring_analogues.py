"""Run complete held-data monitoring-loss comparisons; two independent CPU lanes.

Each job is one representation/readout/archive policy. No source acquisition,
encoder extraction, training, retrospective p99 transfer or forecast-head use.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analogue_distributions import group_weights
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output
from src.monitoring_analogues import (
    OFFSETS,
    information_states,
    native_members,
    prior_distances,
    score_rows,
    select_distinct,
)

OUT = ROOT / "results/limburg_monitoring_2026_10_28"
PREP = OUT / "preparation"
MODELS = [
    "dofa",
    "croma",
    "satmae",
    "copernicus_fm",
    "terramind",
    "presto",
    "anysat",
    "galileo",
    "prithvi",
    "olmoearth",
]
EO = ROOT / "results/eo_catchment_representations/coherent_v1/selected/census"


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def features(meta, arrays, u, cap, season=True):
    q = arrays[f"q_{u}_{cap}"].copy()
    q[:, :5] *= (3.6 / meta.area_km2.to_numpy())[:, None]
    fields = [arrays[f"rain_{u}"], q]
    if season:
        day = (meta.cutoff_utc + pd.Timedelta(hours=u)).dt.dayofyear.to_numpy()
        fields.append(
            np.column_stack([np.sin(2 * np.pi * day / 365.25), np.cos(2 * np.pi * day / 365.25)])
        )
    return np.column_stack(fields)


def chronology(meta, u, pool):
    # Parquet/pandas may preserve microseconds: integer datetime units are not
    # intrinsically nanoseconds. Normalize explicitly before hour arithmetic.
    times = meta.cutoff_utc.dt.as_unit("ns").astype("int64").to_numpy()
    ends = meta.end_utc.dt.as_unit("ns").astype("int64").to_numpy()
    hour = 3600 * 10**9
    good = times[:, None] >= times[None, :] + 24 * hour
    good &= ends[None, :] + 12 * hour <= times[:, None] + u * hour
    good &= meta.storm_id.to_numpy()[:, None] != meta.storm_id.to_numpy()[None, :]
    if pool == "same_gauge":
        good &= meta.gauge.to_numpy()[:, None] == meta.gauge.to_numpy()[None, :]
    elif pool == "other_rivers":
        good &= meta.physical_river.to_numpy()[:, None] != meta.physical_river.to_numpy()[None, :]
    else:
        raise ValueError("Unknown donor geography")
    return good


def eo_features(meta, model, kind):
    path = EO / (model + ".parquet")
    d = pd.read_parquet(path)
    d = d[d.kind.eq(kind)]
    if d.duplicated(["context_id", "catchment_gauge"]).any():
        raise ValueError("Duplicate selected EO context/catchment")
    cols = [c for c in d if c.startswith("e") and c[1:].isdigit()]
    keys = pd.MultiIndex.from_arrays([meta[kind + "_context_id"], meta.catchment_gauge])
    d = d.set_index(["context_id", "catchment_gauge"]).reindex(keys)
    x = d[cols].to_numpy(dtype=float, copy=True)
    norms = np.linalg.norm(x, axis=1)
    valid = np.isfinite(x).all(axis=1) & (norms > 0)
    x[valid] /= norms[valid, None]
    x[~valid] = np.nan
    return x, valid, path


def run_job(job):
    model, kind, pool = job
    name = f"{model}__{kind}__{pool}"
    target = OUT / "scores" / name
    sources = {
        str(p.relative_to(ROOT)): sha256(p)
        for p in [
            Path(__file__),
            ROOT / "src/monitoring_analogues.py",
            ROOT / "src/analogue_distributions.py",
            PREP / "manifest.json",
            PREP / "inputs.npz",
            PREP / "cases.parquet",
        ]
    }
    if model != "baseline":
        sources[str((EO / (model + ".parquet")).relative_to(ROOT))] = sha256(
            EO / (model + ".parquet")
        )
    if (target / "manifest.json").exists():
        saved = json.loads((target / "manifest.json").read_text())
        if saved["inputs_and_source_sha256"] != sources:
            raise ValueError("Completed monitoring score job inputs changed; version a new run")
        for p, digest in saved["outputs_sha256"].items():
            if sha256(target / p) != digest:
                raise ValueError("Completed score output changed")
        return name, "reused"
    meta = pd.read_parquet(PREP / "cases.parquet")
    with np.load(PREP / "inputs.npz") as z:
        arrays = {k: z[k] for k in z.files}
    n = len(meta)
    areas = meta.area_km2.to_numpy(float)
    storms = meta.storm_id.to_numpy()
    eo = eo_valid = None
    if model != "baseline":
        eo, eo_valid, _ = eo_features(meta, model, kind)
    progress = OUT / "progress" / (name + ".json")
    progress.parent.mkdir(parents=True, exist_ok=True)
    rows, coverage = [], []
    began = time.monotonic()

    def scored(qi, u, cap, role, ids, k, x, weights=None):
        if not len(ids):
            return
        y = arrays[f"outcome_{u}"][qi]
        a = (
            native_members(arrays[f"outcome_{u}"], np.asarray(ids), areas, areas[qi])
            if x is None
            else x
        )
        good = bool(
            arrays[f"quality_{u}"][qi]
            and arrays[f"input_clean_{u}_{cap}"][qi]
            and meta.boundary_known.iloc[qi]
        )
        clean = bool(
            arrays[f"quality_{u}"][np.asarray(ids)].all()
            and arrays[f"input_clean_{u}_{cap}"][np.asarray(ids)].all()
        )
        rows.append(
            dict(
                case=qi,
                offset_h=u,
                cap_h=cap,
                role=role,
                target_k=k,
                actual_k=len(ids),
                query_clean=good,
                donors_clean=clean,
                member_ids=list(ids) if role != "generic" else [],
                **score_rows(y, a, areascale=3.6 / areas[qi], weights=weights),
            )
        )

    for u in OFFSETS:
        allowed = chronology(meta, u, pool)
        outcomes_ok = arrays[f"outcome_valid_{u}"]
        fixed = arrays[f"fixed_valid_{u}"]
        states = information_states(u)
        all_x = {cap: features(meta, arrays, u, cap) for cap in states}
        for qi in range(n):
            if not outcomes_ok[qi]:
                continue
            prior = allowed[qi]
            fixed_ids = np.flatnonzero(prior & fixed)
            restricted = np.flatnonzero(prior & fixed & eo_valid) if eo_valid is not None else []
            if model != "baseline":
                cov = dict(
                    case=qi,
                    offset_h=u,
                    query_eo=bool(eo_valid[qi]),
                    fixed_donors=len(fixed_ids),
                    eo_donors=len(restricted),
                )
                coverage.append(cov)
                if not eo_valid[qi] or not len(restricted):
                    continue
                ed, es = prior_distances(eo[restricted], eo[qi])
            generic_ids = np.flatnonzero(prior & outcomes_ok) if model == "baseline" else []
            generic_weights = group_weights(storms[generic_ids]) if len(generic_ids) else None
            generic_score = None
            for cap in states:
                x = all_x[cap]
                if model == "baseline":
                    last = arrays[f"q_{u}_{cap}"][qi, 0]
                    if np.isfinite(last):
                        scored(qi, u, cap, "persistence", [qi], 0, np.full((1, 24), last))
                    if len(generic_ids):
                        if generic_score is None:
                            a = native_members(
                                arrays[f"outcome_{u}"], generic_ids, areas, areas[qi]
                            )
                            generic_score = score_rows(
                                arrays[f"outcome_{u}"][qi],
                                a,
                                areascale=3.6 / areas[qi],
                                weights=generic_weights,
                            )
                        rows.append(
                            dict(
                                case=qi,
                                offset_h=u,
                                cap_h=cap,
                                role="generic",
                                target_k=0,
                                actual_k=len(generic_ids),
                                query_clean=bool(arrays[f"quality_{u}"][qi]),
                                donors_clean=bool(arrays[f"quality_{u}"][generic_ids].all()),
                                member_ids=[],
                                **generic_score,
                            )
                        )
                if not np.isfinite(x[qi]).all():
                    continue
                if model == "baseline":
                    natural_ids = np.flatnonzero(prior & outcomes_ok & np.isfinite(x).all(axis=1))
                    groups = [
                        ("natural_conventional", natural_ids, True),
                        ("fixed_conventional", fixed_ids, True),
                        ("natural_no_season", natural_ids, False),
                    ]
                    for role, ids, season in groups:
                        if not len(ids):
                            continue
                        xx = x if season else x[:, :-2]
                        d, _ = prior_distances(xx[ids], xx[qi])
                        chosen = select_distinct(ids, d, storms)
                        for k in [5, 10]:
                            scored(qi, u, cap, role, chosen[:k], k, None)
                else:
                    cd, cs = prior_distances(x[restricted], x[qi])
                    mixed = np.sqrt(0.5 * (cd / cs) ** 2 + 0.5 * (ed / es) ** 2)
                    for role, d in [("matched_conventional", cd), ("eo_augmented", mixed)]:
                        chosen = select_distinct(restricted, d, storms)
                        for k in [5, 10]:
                            scored(qi, u, cap, role, chosen[:k], k, None)
            if qi % 40 == 0:
                progress.write_text(
                    json.dumps(
                        dict(
                            status="running",
                            offset_h=u,
                            cases_visited=OFFSETS.index(u) * n + qi,
                            total_case_issues=4 * n,
                            rows=len(rows),
                            elapsed_s=time.monotonic() - began,
                        )
                    )
                )
    with fresh_output(target) as stage:
        pd.DataFrame(rows).to_parquet(stage / "scores.parquet", index=False)
        pd.DataFrame(coverage).to_parquet(stage / "eo_coverage.parquet", index=False)
        report = dict(
            status="completed",
            model=model,
            kind=kind,
            pool=pool,
            rows=len(rows),
            elapsed_s=time.monotonic() - began,
            inputs_and_source_sha256=sources,
            outputs_sha256={p.name: sha256(p) for p in stage.iterdir()},
        )
        (stage / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    progress.write_text(
        json.dumps(dict(status="completed", rows=len(rows), elapsed_s=time.monotonic() - began))
    )
    return name, "completed"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers", type=int, choices=[1, 2], default=2)
    p.add_argument("--pool", choices=["same_gauge", "other_rivers", "both"], default="both")
    p.add_argument("--model", choices=["all", "baseline", *MODELS], default="all")
    args = p.parse_args()
    pools = ["same_gauge", "other_rivers"] if args.pool == "both" else [args.pool]
    jobs = []
    for pool in pools:
        if args.model in ["all", "baseline"]:
            jobs.append(("baseline", "none", pool))
        for model in (
            MODELS if args.model == "all" else ([] if args.model == "baseline" else [args.model])
        ):
            jobs.extend((model, kind, pool) for kind in ["recent", "monthly_snapshot"])
    finished = []
    out = OUT / "execution.json"
    out.write_text(
        json.dumps(
            dict(
                status="running",
                pid=os.getpid(),
                updated_utc=timestamp(),
                planned_jobs=len(jobs),
                completed_jobs=0,
                percent_complete=0,
                jobs=[],
            ),
            indent=2,
        )
        + "\n"
    )
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        pending = {executor.submit(run_job, j): j for j in jobs}
        for f in as_completed(pending):
            try:
                result = f.result()
            except Exception as exc:
                for other in pending:
                    other.cancel()
                out.write_text(
                    json.dumps(
                        dict(
                            status="failed",
                            job=pending[f],
                            error=str(exc),
                            completed_jobs=len(finished),
                            jobs=finished,
                        ),
                        indent=2,
                    )
                    + "\n"
                )
                raise
            finished.append(result)
            out.write_text(
                json.dumps(
                    dict(
                        status="running",
                        pid=os.getpid(),
                        updated_utc=timestamp(),
                        planned_jobs=len(jobs),
                        completed_jobs=len(finished),
                        percent_complete=100 * len(finished) / len(jobs),
                        jobs=finished,
                    ),
                    indent=2,
                )
                + "\n"
            )
            print(result, flush=True)
    out.write_text(
        json.dumps(
            dict(
                status="completed",
                planned_jobs=len(jobs),
                completed_jobs=len(finished),
                jobs=finished,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
