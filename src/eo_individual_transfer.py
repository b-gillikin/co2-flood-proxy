"""DOFA's held-watercourse, chronological residual experiment.

Every source residual excludes BOTH the outer target and that source's entire
watercourse. Inner watercourse folds repeat this exclusion. References/cache
keys bind all exclusions; target Q is never a model input or tuning label.
"""

from __future__ import annotations

import fcntl
import json
import os
import time
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd

from src.eo_event_inputs import completed_windows, context_id
from src.eo_individual_baselines import transfer_reference
from src.eo_individual_evaluation import (
    assessment_scores,
    common_context,
    feature_matrix,
    prediction_status,
)
from src.eo_individual_readout import ALPHAS, balanced_weights, choose, fit_grid, weighted_error
from src.eo_inputs import sha256


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def canonical_river(value):
    return "wurm" if str(value).lower() in {"wurm/worm", "wurm", "worm"} else str(value).lower()


def exclusion_graph(meta):
    sites = meta.drop_duplicates("site").sort_values("site")
    groups = sites.physical_river.map(canonical_river).to_numpy()
    assert len(groups) == 8
    return groups, np.r_[groups, ["maas", "maas"]]


class TransferReferences:
    def __init__(self, root, scenario, cases, bank, identity):
        self.root, self.scenario, self.cases, self.bank = root, scenario, cases, bank
        self.groups, self.channels = exclusion_graph(cases)
        self.areas = cases.drop_duplicates("site").sort_values("site").area_km2.to_numpy()
        self.identity = identity
        self.memory = OrderedDict()
        self.dest = (
            root / "results/limburg_individual_experiments_v1/transfer_references" / scenario
        )
        self.dest.mkdir(parents=True, exist_ok=True)
        storms = self.cases.drop_duplicates("query").sort_values("query")
        # Timestamp.value is explicitly nanoseconds. Series.astype(int64)
        # preserves a pandas array's us/ns resolution and cannot be compared
        # safely with a nanosecond boundary.
        hour = pd.Timedelta(hours=1).value
        ends_ns = np.array([pd.Timestamp(t).value for t in storms.end_utc])
        cutoffs_ns = np.array([pd.Timestamp(t).value for t in storms.cutoff_utc])
        self.closure = {
            u: np.maximum(ends_ns + 12 * hour, cutoffs_ns + (u + 24) * hour) for u in [0, 6, 12, 24]
        }

    def get(self, excluded):
        excluded = tuple(sorted(excluded))
        if excluded in self.memory:
            return self.memory[excluded]
        name = "+".join(excluded)
        output = self.dest / (name + ".npz")
        receipt = output.with_suffix(".json")
        with output.with_suffix(".lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if receipt.exists():
                saved = json.loads(receipt.read_text())
                assert saved["source_hashes"] == self.identity
                assert saved["sha256"] == sha256(output)
            else:
                arrays = {
                    k: np.full((len(self.cases), 24), np.nan)
                    for k in ["mean", "median", "fixed_mean", "fixed_median"]
                }
                donors = np.full((len(self.cases), 5, 2), -1, np.int32)
                ids = np.flatnonzero(np.isin(self.groups[self.cases.site.to_numpy()], excluded))
                for count, i in enumerate(ids):
                    row = self.cases.iloc[i]
                    qi, gi, u = int(row.query), int(row.site), int(row.offset_h)
                    a, b, members = transfer_reference(
                        self.bank, qi, gi, u, self.scenario, self.channels, self.areas, excluded
                    )
                    arrays["mean"][i], arrays["median"][i] = a, b
                    if members:
                        donors[i, : len(members)] = members
                    boundary = pd.Timestamp(f"{row.issue_utc.year}-01-01", tz="UTC")
                    # The bank's issue-specific prior still applies. The fixed
                    # archive additionally requires storm and response closure.
                    closed = self.bank[f"prior_{u}_0"][qi].copy()
                    closed &= self.closure[u] <= boundary.value
                    c, d, _ = transfer_reference(
                        self.bank,
                        qi,
                        gi,
                        u,
                        self.scenario,
                        self.channels,
                        self.areas,
                        excluded,
                        closed,
                    )
                    arrays["fixed_mean"][i], arrays["fixed_median"][i] = c, d
                    if count % 250 == 0:
                        print(
                            "transfer reference",
                            self.scenario,
                            name,
                            count,
                            "/",
                            len(ids),
                            flush=True,
                        )
                tmp = output.with_suffix(".partial")
                with tmp.open("wb") as stream:
                    np.savez_compressed(stream, **arrays, donors=donors)
                tmp.replace(output)
                atomic_json(
                    receipt,
                    dict(
                        status="completed",
                        exclusions=excluded,
                        source_hashes=self.identity,
                        rows=len(ids),
                        sha256=sha256(output),
                    ),
                )
        data = dict(np.load(output))
        # At most 41 small trajectory tables; no imagery or patch arrays.
        self.memory[excluded] = data
        if len(self.memory) > 6:
            self.memory.popitem(last=False)
        return data

    def rows(self, excluded):
        result = {
            k: np.full((len(self.cases), 24), np.nan)
            for k in ["mean", "median", "fixed_mean", "fixed_median"]
        }
        for river in np.unique(self.groups):
            ids = np.flatnonzero(self.groups[self.cases.site.to_numpy()] == river)
            reference = self.get(set(excluded) | {river})
            for key in result:
                result[key][ids] = reference[key][ids]
        return result


def transfer_training_mask(cases, groups, excluded, year, y, baseline, raw_available):
    boundary = pd.Timestamp(f"{year}-01-01", tz="UTC")
    year_mask = pd.to_datetime(cases.issue_utc, utc=True).dt.year.eq(year).to_numpy()
    held_storms = cases.loc[year_mask, "storm_id"].unique()
    closed = (
        (pd.to_datetime(cases.end_utc, utc=True) + pd.Timedelta(hours=12) <= boundary)
        & (pd.to_datetime(cases.response_end_utc, utc=True) <= boundary)
    ).to_numpy()
    return (
        closed
        & ~np.isin(cases.storm_id, held_storms)
        & ~np.isin(groups[cases.site.to_numpy()], list(excluded))
        & cases.outcome_valid.to_numpy(bool)
        & np.isfinite(y).all(1)
        & np.isfinite(baseline).all(1)
        & raw_available
    )


def run_transfer(root, scenario):
    root = Path(root)
    # All held-target watercourse channels are absent in both scenarios, so
    # rich_basin and local_q_absent are the SAME transfer information regime.
    if scenario == "rich_basin":
        dest = root / "results/limburg_individual_experiments_v1/scores/dofa__rich_basin"
        atomic_json(
            dest / "alias.json",
            dict(
                alias_of="dofa__local_q_absent",
                reason="Whole target-watercourse holdout removes local Q in either scenario; not an independent regime",
            ),
        )
        return
    began = time.time()
    out = root / "results/limburg_individual_experiments_v1"
    plan_path = root / "config/limburg_individual_encoder_experiments_v1.json"
    plan = json.loads(plan_path.read_text())
    prep = out / "preparation"
    fm_path = out / "features/dofa/manifest.json"
    fm = json.loads(fm_path.read_text())
    assert fm["status"] == "completed"
    feature_path = fm_path.parent / "context_features.parquet"
    assert fm["outputs"]["context_features.parquet"] == sha256(feature_path)
    source = root / plan["shared"]["source"] / "preparation"
    paths = [
        root / "scripts/162_review_scarcity.py",
        root / "results/storm_response/hourly_normalizer.parquet",
        root / "results/flood_case_review_2026_10_27/register.parquet",
        plan_path,
        prep / "manifest.json",
        fm_path,
        source / "manifest.json",
        Path(__file__),
        *[
            root / "src" / n
            for n in [
                "eo_individual_baselines.py",
                "eo_individual_evaluation.py",
                "eo_individual_readout.py",
                "scarcity.py",
            ]
        ],
    ]
    identity = {str(p.relative_to(root)): sha256(p) for p in paths}
    dest = out / "scores" / ("dofa__" + scenario)
    dest.mkdir(parents=True, exist_ok=True)
    final = dest / "manifest.json"
    if final.exists():
        saved = json.loads(final.read_text())
        assert saved["source_hashes"] == identity
        for p, h in saved["outputs"].items():
            assert sha256(dest / p) == h
        return
    cases = pd.read_parquet(prep / "cases.parquet")
    cases = cases[cases.scenario.eq(scenario)].reset_index(drop=True)
    bank = dict(np.load(source / "bank.npz"))
    window_end = cases.cutoff_utc.map(
        lambda t: pd.Timestamp(completed_windows(t, "monthly")[-1]["end"])
    )
    cases["eo_context_age_days"] = (cases.issue_utc - window_end).dt.total_seconds() / 86400
    assert (cases.eo_context_age_days >= 0).all()
    groups, channels = exclusion_graph(cases)
    row_groups = groups[cases.site.to_numpy()]
    features = pd.read_parquet(feature_path).set_index(["context_id", "catchment_gauge"])
    contexts = cases.cutoff_utc.map(
        lambda t: context_id("monthly", completed_windows(t, "monthly"))
    )
    aligned = features.reindex(
        pd.MultiIndex.from_arrays([contexts, cases.catchment_gauge])
    ).reset_index(drop=True)
    raw = feature_matrix(aligned, ["raw", "context", "terrain"], landscape=True)
    # Catchment area is a known physical transfer descriptor, not a response scale learned from target Q.
    raw = np.column_stack([raw, np.log(cases.area_km2.to_numpy())])
    eo = feature_matrix(aligned, ["primary"], landscape=True)
    rarea = [c for c in aligned if c.startswith("raw_area_")]
    raw_available = np.nan_to_num(aligned[rarea].to_numpy()).max(1) > 0
    eo_available = np.isfinite(eo).any(1) & (np.nansum(eo**2, axis=1) > 0)
    coverage_cols = sorted(c for c in aligned if "_area_" in c)
    coverage = aligned[coverage_cols].to_numpy() / (cases.area_km2.to_numpy()[:, None] * 1e6)
    y = np.stack(
        [
            bank[f"outcome_{r.offset_h}"][r.query, r.site] * 3.6 / r.area_km2
            for r in cases.itertuples()
        ]
    )
    references = TransferReferences(root, scenario, cases, bank, identity)
    years = pd.to_datetime(cases.issue_utc, utc=True).dt.year.to_numpy()
    prediction = {
        k: np.full_like(y, np.nan)
        for k in [
            "conventional_mean",
            "conventional_median",
            "fixed_year_mean",
            "fixed_year_median",
            "raw_correction",
            "encoder_correction",
        ]
    }
    tuning = []
    fit_cache = OrderedDict()

    def dataset(excluded):
        baseline = references.rows(excluded)
        conditions = np.empty((len(cases), 2))
        blocks = []
        for river in np.unique(groups):
            ids = np.flatnonzero(row_groups == river)
            exclude_channels = np.flatnonzero(np.isin(channels, list(set(excluded) | {river})))
            g, rain = common_context(
                bank,
                cases.iloc[ids],
                scenario,
                None,
                raw_available[ids],
                eo_available[ids],
                coverage[ids],
                exclude_channels,
            )
            g = np.column_stack([g, baseline["mean"][ids]])
            blocks.append((ids, g))
            conditions[ids] = np.column_stack([rain, baseline["mean"][ids].mean(1)])
        common = np.full((len(cases), blocks[0][1].shape[1]), np.nan)
        for ids, g in blocks:
            common[ids] = g
        return baseline, common, conditions

    def grid_for(excluded, year):
        key = (tuple(sorted(excluded)), int(year))
        if key in fit_cache:
            return fit_cache[key]
        cache_path = dest / "folds" / ("+".join(key[0]) + f"__{year}.npz")
        receipt = cache_path.with_suffix(".json")
        if receipt.exists():
            saved = json.loads(receipt.read_text())
            assert saved["source_hashes"] == identity and saved["sha256"] == sha256(cache_path)
            with np.load(cache_path) as data:
                ids, train = data["ids"], data["train"]
                grids = {
                    (float(k.split("_")[1]), float(k.split("_")[2])): data[k]
                    for k in data.files
                    if k.startswith("p_")
                }
            result = ids, grids, train, saved["solver"]
        else:
            baseline, common, conditions = dataset(excluded)
            mask = transfer_training_mask(
                cases, groups, excluded, year, y, baseline["mean"], raw_available
            )
            train = np.flatnonzero(mask)
            ids = np.flatnonzero((years == year) & np.isin(row_groups, list(excluded)))
            if not len(train) or not len(ids):
                return ids, {}, train, {"solver": "no_closed_source_training"}
            w = balanced_weights(
                cases.storm_id.to_numpy()[train], cases.site.to_numpy()[train], row_groups[train]
            )
            grid = fit_grid(
                common,
                raw,
                eo,
                conditions,
                y,
                baseline["mean"],
                train,
                ids,
                w,
                ALPHAS,
                (0.0, 0.1, 1.0),
            )
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with cache_path.with_suffix(".partial").open("wb") as stream:
                np.savez_compressed(
                    stream, ids=ids, train=train, **{f"p_{a}_{b}": v for (a, b), v in grid.items()}
                )
            cache_path.with_suffix(".partial").replace(cache_path)
            atomic_json(
                receipt,
                dict(
                    source_hashes=identity,
                    sha256=sha256(cache_path),
                    solver=fit_grid.last_solver,
                    exclusions=sorted(excluded),
                    year=int(year),
                ),
            )
            result = ids, grid, train, fit_grid.last_solver
        fit_cache[key] = result
        if len(fit_cache) > 4:
            fit_cache.popitem(last=False)
        atomic_json(
            dest / "progress.json",
            dict(
                status="running",
                phase="source_only_fold",
                excluded=key[0],
                year=int(year),
                folds_cached=len(fit_cache),
                elapsed_s=time.time() - began,
            ),
        )
        return result

    # Outer fixed-year fits; tuning holds out one of the remaining watercourses
    # AND a previous year. Pair-exclusion fits can serve both orientations.
    for river in np.unique(groups):
        refs, _, _ = dataset({river})
        own = row_groups == river
        for label, suffix in [
            ("conventional_mean", "mean"),
            ("conventional_median", "median"),
            ("fixed_year_mean", "fixed_mean"),
            ("fixed_year_median", "fixed_median"),
        ]:
            prediction[label][own] = refs[suffix][own]
        for year in sorted(np.unique(years)):
            ids, outer, train, solver = grid_for({river}, year)
            if not outer:
                tuning.append(
                    dict(
                        watercourse=river,
                        year=int(year),
                        training=0,
                        training_rows=[],
                        validation_years=[],
                        raw_parameters="baseline",
                        eo_parameters="raw_only",
                    )
                )
                prediction["raw_correction"][ids] = refs["mean"][ids]
                prediction["encoder_correction"][ids] = refs["mean"][ids]
                continue
            totals = {"baseline": [0.0, 0.0, -1.0, float("inf")]}
            totals.update({(w, a): [0.0, 0.0, w, a] for w in (0.0, 0.1, 1.0) for a in ALPHAS})
            used_years = []
            for previous in sorted(np.unique(years[train]), reverse=True):
                folds = []
                for held in np.unique(groups):
                    if held == river:
                        continue
                    vi, grid, _, _ = grid_for({river, held}, previous)
                    use = (
                        (row_groups[vi] == held)
                        & np.isfinite(y[vi]).all(1)
                        & cases.outcome_valid.to_numpy()[vi]
                        & raw_available[vi]
                        & eo_available[vi]
                    )
                    boundary = pd.Timestamp(f"{year}-01-01", tz="UTC")
                    use &= (
                        pd.to_datetime(cases.response_end_utc.iloc[vi], utc=True) <= boundary
                    ).to_numpy()
                    use &= (
                        pd.to_datetime(cases.end_utc.iloc[vi], utc=True) + pd.Timedelta(hours=12)
                        <= boundary
                    ).to_numpy()
                    use &= ~np.isin(
                        cases.storm_id.to_numpy()[vi], cases.loc[years == year, "storm_id"].unique()
                    )
                    if grid and use.any():
                        folds.append((held, vi, grid, use))
                if not folds:
                    continue
                # Equal watercourses, then sites/storms/issues inside each fold.
                for held, vi, grid, use in folds:
                    picked = vi[use]
                    validation_refs = references.get({river, held})["mean"][picked]
                    weights = balanced_weights(
                        cases.storm_id.to_numpy()[picked], cases.site.to_numpy()[picked]
                    ) / len(folds)
                    for parameter in totals:
                        pred = validation_refs if parameter == "baseline" else grid[parameter][use]
                        num, den = weighted_error(y[picked], pred, weights)
                        totals[parameter][0] += num
                        totals[parameter][1] += den
                used_years.append(int(previous))
                if len(used_years) == 2:
                    break
            raw_choice = choose({k: v for k, v in totals.items() if k == "baseline" or k[0] == 0})
            eo_choice = choose(totals)
            rp = refs["mean"][ids].copy()
            if raw_choice != "baseline":
                take = raw_available[ids]
                rp[take] = outer[raw_choice][take]
            ep = rp.copy()
            if eo_choice == "baseline":
                ep = refs["mean"][ids].copy()
            else:
                take = raw_available[ids] & (eo_available[ids] if eo_choice[0] else True)
                ep[take] = outer[eo_choice][take]
            prediction["raw_correction"][ids], prediction["encoder_correction"][ids] = rp, ep
            tuning.append(
                dict(
                    watercourse=river,
                    year=int(year),
                    training=len(train),
                    training_rows=train.tolist(),
                    validation_years=used_years,
                    raw_parameters=raw_choice,
                    eo_parameters=eo_choice,
                    solver=solver,
                    validation={str(k): v for k, v in totals.items()},
                )
            )
        print("DOFA finished held watercourse", river, flush=True)
    # Evaluation labels are attached only after every fit/selection is finished.
    import runpy

    label_function = runpy.run_path(str(root / "scripts/162_review_scarcity.py"))["labels"]
    meta = pd.read_parquet(source / "cases.parquet")
    normalizer = pd.read_parquet(root / "results/storm_response/hourly_normalizer.parquet")
    register = pd.read_parquet(root / "results/flood_case_review_2026_10_27/register.parquet")
    labels = {
        u: label_function(bank, meta, u, normalizer, register).set_index("case")
        for u in [0, 6, 12, 24]
    }
    for name in ["future_p99", "documented_flood_overlap", "verification_clean"]:
        cases[name] = [
            labels[r.offset_h].loc[r.query * 8 + r.site, name] for r in cases.itertuples()
        ]
    for river in np.unique(groups):
        ids = np.flatnonzero(row_groups == river)
        statuses = prediction_status(
            [r for r in tuning if r["watercourse"] == river],
            years[ids],
            raw_available[ids],
            eo_available[ids],
        )
        for key, values in statuses.items():
            if key not in cases:
                cases[key] = (
                    np.zeros(len(cases), int) if key == "training_count" else "conventional"
                )
            cases.loc[ids, key] = values
    cases["reference_available"] = np.isfinite(prediction["conventional_mean"]).all(1)
    cases["reference_kind"] = np.where(
        cases.reference_available, "source_watercourse_analogue", "unavailable"
    )
    cases["prediction_available"] = np.isfinite(prediction["encoder_correction"]).all(1)
    cases["held_watercourse"] = row_groups
    cases["model"] = "dofa"
    cases["raw_available"], cases["encoder_available"] = raw_available, eo_available
    cases["assessment_id"] = [f"{scenario}__u{r.offset_h}__{r.case_id}" for r in cases.itertuples()]
    scores = []
    for method, p in prediction.items():
        frame = cases.copy()
        for k, v in assessment_scores(y, p).items():
            frame[k] = v
        frame["method"] = method
        scores.append(frame)
    pd.concat(scores, ignore_index=True).to_parquet(dest / "scores.parquet", index=False)
    cases.to_parquet(dest / "cases.parquet", index=False)
    np.savez_compressed(dest / "predictions.npz", observed=y, **prediction)
    atomic_json(dest / "tuning.json", tuning)
    atomic_json(
        final,
        dict(
            status="completed",
            model="dofa",
            scenario=scenario,
            source_hashes=identity,
            rows=len(cases),
            elapsed_s=time.time() - began,
            target_watercourse_q_used_for_fit=False,
            outputs={
                p: sha256(dest / p)
                for p in ["scores.parquet", "cases.parquet", "predictions.npz", "tuning.json"]
            },
        ),
    )
    atomic_json(dest / "progress.json", dict(status="completed", model="dofa", scenario=scenario))
