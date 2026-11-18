#!/usr/bin/env python3
"""Step 3: fixed multiyear predictions, paired uncertainty and largest flows."""

from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.dise_corrected import population, score
from src.dise_multiyear import scopes_for
from src.dise_repeatability import (
    CONTRASTS,
    balanced_resamples,
    conditions,
    contrast_record,
    gauge_resamples,
    joint_multiplicities,
    regional_episodes,
)
from src.geoglows_experiment import sha, write_json

CONFIG = ROOT / "config/limburg_dise_repeatability_v1.json"
METRICS = ["mae", "rmse", "bias"]


def stamp():
    return datetime.now(timezone.utc).isoformat()


def point_metrics(f, arms, expected=None):
    expected = population(f) if expected is None else expected
    return {arm: score(f, f[arm], expected) for arm in arms}


def paired_rows(f, arms, context, expected=None):
    expected = population(f) if expected is None else expected
    values = point_metrics(f, arms, expected)
    result = []
    for name, (candidate, reference) in CONTRASTS.items():
        if candidate not in arms or reference not in arms:
            continue
        for metric in METRICS[:2]:
            c, r = values[candidate][metric], values[reference][metric]
            result.append(
                dict(
                    **context,
                    contrast=name,
                    metric=metric,
                    candidate=candidate,
                    reference=reference,
                    candidate_value=c,
                    reference_value=r,
                    **contrast_record(c, r),
                    rows=len(f),
                    gauges=f.gauge.nunique(),
                    expected_gauges=len(expected),
                    missing_population=sorted(set(expected) - set(f.gauge)),
                    rivers=f.river_group.nunique(),
                    dates=f.day.nunique(),
                    status="defined" if c is not None and r is not None else "undefined",
                )
            )
    return result


def windows(p, episodes, padding, arms):
    rows = []
    for ep in episodes:
        start = ep["start"] - pd.Timedelta(days=padding)
        end = ep["end"] + pd.Timedelta(days=padding)
        river = p[p.river_group.eq(ep["river_group"])]
        for gauge, all_days in river.groupby("gauge"):
            f = all_days[all_days.day.between(start, end)].sort_values("day")
            if f.empty:
                rows.append(dict(**ep, gauge=gauge, rows=0, status="no_verification"))
                continue
            actual = f.loc[f.q_observed.idxmax()]
            expected_days = int((end - start).days) + 1
            complete = len(f) == expected_days
            for arm in arms:
                finite = np.isfinite(f[arm]).all()
                model_peak = f.loc[f[arm].idxmax()] if finite else None
                obs_sum = f.q_observed.sum()
                rows.append(
                    dict(
                        **ep,
                        gauge=gauge,
                        station=f.station.iloc[0],
                        arm=arm,
                        rows=len(f),
                        expected_days=expected_days,
                        complete_window=complete,
                        status="defined" if finite else "nonfinite_prediction",
                        high_water_days=int(f.high_water.fillna(False).sum()),
                        clean_days=int(f.clean_verification.fillna(False).sum()),
                        unknown_quality_days=int(f.clean_verification.isna().sum()),
                        observed_peak_day=actual.day,
                        observed_peak=float(actual.q_observed),
                        observed_peak_m3s=float(
                            actual.q_observed * actual.reference_area_km2 / 86.4
                        ),
                        peak_clean=actual.clean_verification,
                        overlap_stratum=actual.overlap_stratum,
                        location_stratum=actual.location_stratum,
                        on_peak_estimate=float(actual[arm]),
                        on_peak_error=float(actual[arm] - actual.q_observed),
                        window_peak=float(model_peak[arm]) if finite and complete else None,
                        peak_day_error=int((model_peak.day - actual.day).days)
                        if finite and complete
                        else None,
                        volume_bias_pct=float(100 * (f[arm].sum() / obs_sum - 1))
                        if complete and finite and obs_sum > 0
                        else None,
                        available_day_mae=float(np.abs(f[arm] - f.q_observed).mean())
                        if finite
                        else None,
                        peak_ties=int(f.q_observed.eq(actual.q_observed).sum()),
                    )
                )
    return rows


def main():
    started = time.monotonic()
    cfg = json.loads(CONFIG.read_text())
    source, out = ROOT / cfg["source"], ROOT / cfg["output"]
    out.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(ROOT).free / 1024**3 < cfg["reserve_gib"]:
        raise RuntimeError("Disk reserve reached before small Step 3 output")
    completion = json.loads((source / "completion.json").read_text())
    if completion["status"] != "completed":
        raise ValueError("Step 2 incomplete")
    for name, digest in completion["outputs"].items():
        if sha(source / name) != digest:
            raise ValueError(f"Step 2 frozen output changed: {name}")
    inputs = {
        str(CONFIG.relative_to(ROOT)): sha(CONFIG),
        str((source / "completion.json").relative_to(ROOT)): sha(source / "completion.json"),
        str((source / "predictions.parquet").relative_to(ROOT)): sha(
            source / "predictions.parquet"
        ),
        "scripts/277_assess_dise_repeatability.py": sha(Path(__file__)),
        "src/dise_repeatability.py": sha(ROOT / "src/dise_repeatability.py"),
        "config/limburg_flood_review_evidence.json": sha(
            ROOT / "config/limburg_flood_review_evidence.json"
        ),
    }
    progress = dict(status="running", completed_contexts=0, total_contexts=36, started_utc=stamp())
    write_json(out / "progress.json", progress)
    p = pd.read_parquet(source / "predictions.parquet")
    if p.duplicated(["regime", "gauge", "day"]).any() or len(p) != completion["test_rows"]:
        raise ValueError("Frozen census differs")
    arms = ["q_model", "donor_fdc"] + [
        f"{policy}__{arm}"
        for policy in ["native_rmse", "article_faithful"]
        for arm in ["H", "H+A", "H+E", "H+A+E"]
    ]
    datasets = {
        "local_temporal": p[p.regime.eq("temporal") & p.source_role.eq("local")],
        "local_spatial": p[p.regime.eq("spatial") & p.source_role.eq("local")],
        "external_transfer": p[p.regime.eq("temporal") & p.source_role.eq("reserved_external")],
    }
    point, annual, gauges, influence, intervals, support = [], [], [], [], [], []
    extremes, events, docs, volume, memberships = [], [], [], [], []
    verified = 0
    saved = pd.read_csv(source / "pooled_metrics.csv")
    evidence = json.loads((ROOT / "config/limburg_flood_review_evidence.json").read_text())
    for dataset, f in datasets.items():
        f = f.copy()
        use_arms = arms + (["local_fdc"] if dataset.startswith("local") else [])
        scope_masks = {k: v for k, v in scopes_for(f).items() if v.any()}
        calendar = pd.date_range(
            f"{f.test_year.min()}-01-01", f"{f.test_year.max()}-12-31", tz="UTC"
        )
        schemes = {"whole_year": None, **{f"moving_{n}d": n for n in cfg["block_days"]}}
        matrices = {
            name: joint_multiplicities(calendar, cfg["draws"], cfg["seed"], block)
            for name, block in schemes.items()
        }
        np.savez_compressed(
            out / f"{dataset}_draw_dates.npz",
            dates_ns=calendar.as_unit("ns").asi8,
            **matrices,
        )
        for stratum, condition in conditions(f).items():
            part = f.loc[condition]
            for scope, mask in scope_masks.items():
                selected = f.loc[condition & mask]
                context = dict(dataset=dataset, scope=scope, stratum=stratum)
                point.extend(paired_rows(selected, use_arms, context))
                expected = population(selected)
                eligible_gauges = sorted(f.loc[mask, "gauge"].unique())
                support.append(
                    dict(
                        **context,
                        rows=len(selected),
                        dates=selected.day.nunique(),
                        gauges=len(expected),
                        eligible_gauges=len(eligible_gauges),
                        no_stratum_gauges=sorted(set(eligible_gauges) - set(expected)),
                        unknown_high_water=int(f.loc[mask, "high_water"].isna().sum()),
                        unknown_quality=int(selected.clean_verification.isna().sum()),
                    )
                )
                # Independently computed bootstrap sufficient sums must reproduce
                # every saved Step 2 metric at multiplicity one.
                if len(selected):
                    gs, cs, vs = gauge_resamples(
                        selected, use_arms, calendar, np.ones((1, len(calendar)))
                    )
                    independent, _ = balanced_resamples(gs, cs, vs, expected)
                    for k, arm in enumerate(use_arms):
                        old = saved[
                            saved.regime.eq(f.regime.iloc[0])
                            & saved.scope.eq(scope)
                            & saved.stratum.eq(stratum)
                            & saved.arm.eq(arm)
                        ].iloc[0]
                        for j, metric in enumerate(METRICS):
                            if not np.isclose(
                                independent[0, k, j],
                                old[metric],
                                rtol=1e-10,
                                atol=1e-10,
                                equal_nan=True,
                            ):
                                raise ValueError(f"Metric mismatch: {context}/{arm}/{metric}")
                        verified += 1
                for year in sorted(f.test_year.unique()):
                    one = selected[selected.test_year.eq(year)]
                    annual.extend(paired_rows(one, use_arms, dict(**context, year=int(year))))
                for omit in sorted(selected.test_year.unique()):
                    influence.extend(
                        paired_rows(
                            selected[selected.test_year.ne(omit)],
                            use_arms,
                            dict(**context, omission_type="year", omitted=str(omit)),
                            expected=expected,
                        )
                    )
                if scope in ("local_all", "external_all"):
                    for omit in sorted(selected.river_group.unique()):
                        influence.extend(
                            paired_rows(
                                selected[selected.river_group.ne(omit)],
                                use_arms,
                                dict(**context, omission_type="river", omitted=omit),
                                expected={
                                    g: river for g, river in expected.items() if river != omit
                                },
                            )
                        )
                    for gauge, one in selected.groupby("gauge"):
                        gauges.extend(
                            paired_rows(
                                one,
                                use_arms,
                                dict(
                                    **context,
                                    gauge=gauge,
                                    river_group=one.river_group.iloc[0],
                                    station=one.station.iloc[0],
                                ),
                            )
                        )
                for arm, scores in point_metrics(selected, use_arms).items():
                    ratio = []
                    for _, one in selected.groupby(["river_group", "gauge"]):
                        total = one.q_observed.sum()
                        value = (
                            100 * (one[arm].sum() / total - 1)
                            if total > 0 and np.isfinite(one[arm]).all()
                            else np.nan
                        )
                        ratio.append(dict(river_group=one.river_group.iloc[0], ratio=value))
                    ratios = pd.DataFrame(ratio)
                    vb = (
                        float(ratios.groupby("river_group").ratio.mean().mean())
                        if len(ratios) and np.isfinite(ratios.ratio).all()
                        else None
                    )
                    volume.append(
                        dict(
                            **context,
                            arm=arm,
                            rows=len(selected),
                            bias=scores["bias"],
                            volume_bias_pct=vb,
                        )
                    )
            for scheme, matrix in matrices.items():
                started_context = time.monotonic()
                gs, counts, values = gauge_resamples(part, use_arms, calendar, matrix)
                distributions = []
                for scope, mask in scope_masks.items():
                    selected = f.loc[condition & mask]
                    context = dict(dataset=dataset, scope=scope, stratum=stratum, scheme=scheme)
                    draws, missing_population = balanced_resamples(
                        gs, counts, values, population(selected)
                    )
                    distributions.append(draws)
                    for contrast, (candidate, reference) in CONTRASTS.items():
                        if candidate not in use_arms:
                            continue
                        c, r = use_arms.index(candidate), use_arms.index(reference)
                        for j, metric in enumerate(METRICS[:2]):
                            delta = draws[:, c, j] - draws[:, r, j]
                            valid = np.isfinite(delta)
                            percent = np.full(len(delta), np.nan)
                            np.divide(
                                100 * (draws[:, r, j] - draws[:, c, j]),
                                draws[:, r, j],
                                out=percent,
                                where=valid & (draws[:, r, j] > 0),
                            )
                            pct_valid = np.isfinite(percent)
                            bounds = (
                                np.quantile(delta[valid], [0.025, 0.975])
                                if valid.any()
                                else [None, None]
                            )
                            pb = (
                                np.quantile(percent[pct_valid], [0.025, 0.975])
                                if pct_valid.any()
                                else [None, None]
                            )
                            intervals.append(
                                dict(
                                    **context,
                                    contrast=contrast,
                                    metric=metric,
                                    draws=cfg["draws"],
                                    defined_draws=int(valid.sum()),
                                    undefined_draws=int((~valid).sum()),
                                    missing_population_draws=missing_population,
                                    percent_undefined_draws=int((~pct_valid).sum()),
                                    delta_low=bounds[0],
                                    delta_high=bounds[1],
                                    reduction_pct_low=pb[0],
                                    reduction_pct_high=pb[1],
                                    status="conditional_on_defined_draws"
                                    if valid.any() and not valid.all()
                                    else "defined"
                                    if valid.all()
                                    else "undefined",
                                    test_years=int(f.test_year.nunique()),
                                )
                            )
                np.savez_compressed(
                    out / f"{dataset}_{stratum}_{scheme}.npz",
                    scores=np.stack(distributions, axis=1),
                    scopes=np.array(list(scope_masks)),
                    arms=np.array(use_arms),
                    metrics=np.array(METRICS),
                )
                progress["completed_contexts"] += 1
                progress.update(
                    updated_utc=stamp(),
                    dataset=dataset,
                    stratum=stratum,
                    scheme=scheme,
                    context_seconds=time.monotonic() - started_context,
                )
                write_json(out / "progress.json", progress)
                print(json.dumps(progress), flush=True)
        episodes = regional_episodes(f, cfg["event_gap_days"])
        for ep in episodes:
            for gauge in f.loc[f.river_group.eq(ep["river_group"]), "gauge"].unique():
                memberships.append(dict(dataset=dataset, gauge=gauge, **ep))
        events.extend(
            dict(dataset=dataset, **r)
            for r in windows(f, episodes, cfg["event_padding_days"], use_arms)
        )
        for (gauge, year), one in f.groupby(["gauge", "test_year"]):
            peak = one.loc[one.q_observed.idxmax()]
            for arm in use_arms:
                extremes.append(
                    dict(
                        dataset=dataset,
                        gauge=gauge,
                        year=int(year),
                        river_group=peak.river_group,
                        station=peak.station,
                        day=peak.day,
                        observed=peak.q_observed,
                        observed_m3s=peak.q_observed * peak.reference_area_km2 / 86.4,
                        arm=arm,
                        estimate=peak[arm],
                        signed_error=peak[arm] - peak.q_observed,
                        clean_verification=peak.clean_verification,
                        overlap_stratum=peak.overlap_stratum,
                        location_stratum=peak.location_stratum,
                        eligible_days=len(one),
                        high_water=peak.high_water,
                    )
                )
        for case in evidence["documentary_cases"]:
            selected = f[
                f.gauge.eq(case["gauge"]) & f.day.ge(case["start"]) & f.day.lt(case["end"])
            ]
            for arm in use_arms:
                docs.append(
                    dict(
                        dataset=dataset,
                        case_id=case["case_id"],
                        gauge=case["gauge"],
                        arm=arm,
                        rows=len(selected),
                        date_precision=case["date_precision"],
                        impact_confirmation=case["impact_confirmation"],
                        source_ids=case["source_ids"],
                        status="available_days_only"
                        if len(selected)
                        else "outside_test_or_no_verification",
                        mae=float(np.abs(selected[arm] - selected.q_observed).mean())
                        if len(selected)
                        else None,
                        note=case["note"],
                    )
                )
    tables = {
        "paired_effects": point,
        "annual_effects": annual,
        "per_gauge_effects": gauges,
        "influence": influence,
        "paired_intervals": intervals,
        "stratum_support": support,
        "volume_bias": volume,
        "gauge_year_maxima": extremes,
        "episodes": events,
        "episode_membership": memberships,
        "documentary_cases": docs,
    }
    for name, records in tables.items():
        pd.DataFrame(records).to_csv(out / f"{name}.csv", index=False)
    e = pd.DataFrame(events)
    a = e[e.arm.eq("native_rmse__H+A")].set_index(["dataset", "episode", "gauge"])
    b = e[e.arm.eq("native_rmse__H+A+E")].set_index(["dataset", "episode", "gauge"])
    paired = a[["available_day_mae", "complete_window", "observed_peak_day", "peak_clean"]].join(
        b[["available_day_mae"]], lsuffix="_conventional", rsuffix="_alpha"
    )
    paired["mae_delta"] = paired.available_day_mae_alpha - paired.available_day_mae_conventional
    paired.reset_index().to_csv(out / "episode_contrasts.csv", index=False)
    selected_cases = []
    for _dataset, one in paired.reset_index().groupby("dataset"):
        # All episodes remain in the census; this is only a symmetric review index.
        for label, order in [("helped", True), ("harmed", False)]:
            chosen = one.sort_values(
                ["mae_delta", "episode", "gauge"], ascending=[order, True, True]
            ).head(5)
            selected_cases.append(chosen.assign(selection=label))
    pd.concat(selected_cases).to_csv(out / "symmetric_case_review_index.csv", index=False)
    # Source identities must also match after analysis.
    for path, digest in inputs.items():
        if sha(ROOT / path) != digest:
            raise ValueError(f"Input/code mutated during Step 3: {path}")
    write_json(
        out / "manifest.json",
        dict(
            status="completed",
            completed_utc=stamp(),
            seconds=time.monotonic() - started,
            inputs=inputs,
            step2_rows=len(p),
            verified_step2_metric_records=verified,
            draws=cfg["draws"],
            seed=cfg["seed"],
            output_hashes={
                str(x.relative_to(out)): sha(x)
                for x in sorted(out.iterdir())
                if x.is_file() and x.suffix in [".csv", ".npz"]
            },
            limitations=[
                "Few test years and river systems; marginal exploratory intervals.",
                "Rolling fits share training history; uncertainty is conditional on fixed predictions.",
                "Synchronized time blocks preserve shared dates/nested gauges; they are not identified meteorological storms.",
                "Missing-population draws retained; interval quantiles conditional on defined draws.",
                "Unknown external row QA prevents clean-only inference.",
                "Daily maxima and p99 do not establish flood stages or warning skill.",
            ],
            free_gib=shutil.disk_usage(ROOT).free / 1024**3,
        ),
    )
    progress.update(status="completed", updated_utc=stamp(), seconds=time.monotonic() - started)
    write_json(out / "progress.json", progress)
    print(json.dumps(progress), flush=True)


if __name__ == "__main__":
    main()
