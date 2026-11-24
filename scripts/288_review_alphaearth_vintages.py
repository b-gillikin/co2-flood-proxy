"""Review matched 2017 and 2020 AlphaEarth results after fitting finishes."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dise_corrected import population, score
from src.dise_multiyear import assert_census, scopes_for
from src.dise_repeatability import (
    balanced_resamples,
    conditions,
    contrast_record,
    gauge_resamples,
    joint_multiplicities,
)
from src.geoglows_experiment import sha, write_json

OUT = ROOT / "results/limburg_representation_extension_v1/alphaearth_vintage_c0"
ORIGINAL = ROOT / "results/limburg_dise_multiyear_v1"
GEUL = OUT.parent / "satellite_c0_benchmark_2020/jobs/held_Geul_2021"
CONFIG = ROOT / "config/limburg_dise_repeatability_v1.json"


def read(path):
    return json.loads(path.read_text())


def verify_output(directory, manifest_name):
    manifest = read(directory / manifest_name)
    if manifest["status"] != "completed":
        raise ValueError(f"Incomplete output at {directory}")
    for name, digest in manifest["outputs"].items():
        if sha(directory / name) != digest:
            raise ValueError(f"Output hash mismatch: {directory / name}")
    return manifest


def record(archive, arms, labels, **metadata):
    expected = population(archive)
    scores = [score(archive, archive[arm], expected) for arm in arms]
    for metric in ("mae", "rmse"):
        baseline, earlier, later = [value[metric] for value in scores]
        for candidate, reference, c, r in (
            (labels[2], labels[1], later, earlier),
            (labels[2], labels[0], later, baseline),
            (labels[1], labels[0], earlier, baseline),
        ):
            yield dict(
                **metadata,
                rows=len(archive),
                dates=archive.day.nunique(),
                gauges=len(expected),
                metric=metric,
                candidate=candidate,
                reference=reference,
                candidate_value=c,
                reference_value=r,
                **contrast_record(c, r),
            )


def review(
    paired,
    settings,
    *,
    labels=("C0", "2017", "2020"),
    features=("H+A", "H+A+E_2017", "H+A+E_2020"),
):
    results, uncertainty = [], []
    datasets = {
        "local_temporal": paired.loc[paired.regime.eq("temporal") & paired.source_role.eq("local")],
        "local_spatial": paired.loc[paired.regime.eq("spatial") & paired.source_role.eq("local")],
        "external": paired.loc[paired.source_role.eq("reserved_external")],
    }
    for name, frame in datasets.items():
        calendar = pd.date_range(
            f"{frame.test_year.min()}-01-01", f"{frame.test_year.max()}-12-31", tz="UTC"
        )
        draws = {
            "whole_year" if days is None else f"moving_{days}d": joint_multiplicities(
                calendar, settings["draws"], settings["seed"], days
            )
            for days in (None, *settings["block_days"])
        }
        for policy in ("native_rmse", "article_faithful"):
            arms = [f"{policy}__{feature}" for feature in features]
            for stratum, include in conditions(frame).items():
                part = frame.loc[include]
                context = dict(dataset=name, policy=policy, stratum=stratum)
                results.extend(record(part, arms, labels, **context, scope="all"))
                for year, subset in part.groupby("test_year"):
                    results.extend(
                        record(subset, arms, labels, **context, scope="year", year=int(year))
                    )
                for scope, mask in scopes_for(frame).items():
                    if scope in {"local_all", "external_all"}:
                        continue
                    results.extend(
                        record(frame.loc[include & mask], arms, labels, **context, scope=scope)
                    )
                if part.empty:
                    continue
                expected = population(part)
                for scheme, multiplicities in draws.items():
                    gauges, counts, values = gauge_resamples(part, arms, calendar, multiplicities)
                    estimates, missing = balanced_resamples(gauges, counts, values, expected)
                    for j, metric in enumerate(("mae", "rmse")):
                        for c, r in ((2, 1), (2, 0), (1, 0)):
                            candidate, reference = labels[c], labels[r]
                            v, b = estimates[:, c, j], estimates[:, r, j]
                            valid = np.isfinite(v) & np.isfinite(b) & (b > 0)
                            limits = (
                                np.quantile(
                                    100 * (1 - v[valid] / b[valid]), [0.025, 0.975]
                                ).tolist()
                                if valid.any()
                                else [None, None]
                            )
                            uncertainty.append(
                                dict(
                                    **context,
                                    scheme=scheme,
                                    metric=metric,
                                    candidate=candidate,
                                    reference=reference,
                                    draws=len(valid),
                                    defined=int(valid.sum()),
                                    undefined=int((~valid).sum()),
                                    missing_population=missing,
                                    reduction_pct_95_range=limits,
                                )
                            )
    return results, uncertainty


def main():
    progress = read(OUT / "progress.json")
    if progress["status"] != "completed":
        raise SystemExit(
            "The comparison is still fitting. Run the review after all folds complete."
        )
    original = verify_output(ORIGINAL, "completion.json")
    paired = pd.read_parquet(OUT / "paired_predictions.parquet")
    old = pd.read_parquet(ORIGINAL / "predictions.parquet")
    assert_census(paired, original["test_rows"])
    pd.testing.assert_frame_equal(paired[old.columns], old, check_exact=True)
    jobs = read(OUT / "jobs.json")
    if len(jobs) != original["jobs"]:
        raise ValueError("Unexpected number of folds")
    caps = {}
    offset = 0
    for job in jobs:
        key = job["id"].removesuffix("_alphaearth_2020")
        directory = GEUL if key == "held_Geul_2021" else OUT / "jobs" / job["id"]
        verify_output(directory, "manifest.json")
        new = pd.read_parquet(directory / "predictions.parquet")
        chosen = paired.iloc[offset : offset + len(new)].reset_index(drop=True)
        for col in ("gauge", "day", "q_observed", "high_water", "clean_verification"):
            left, right = chosen[col], new[col]
            if col == "clean_verification":
                left, right = left.astype("boolean"), right.astype("boolean")
            pd.testing.assert_series_equal(left, right, check_exact=True)
        for policy in ("native_rmse", "article_faithful"):
            col = f"{policy}__H+A+E"
            np.testing.assert_array_equal(chosen[f"{col}_2017"], chosen[col])
            np.testing.assert_array_equal(chosen[f"{col}_2020"], new[col])
        caps[key] = {
            key: value
            for key, value in read(directory / "readout.json")["selected_fold_caps"].items()
            if key.endswith("__H+A+E")
        }
        offset += len(new)
    if offset != len(paired):
        raise ValueError("Per-fold pairing did not cover the full census")
    points, intervals = review(paired, read(CONFIG))
    output = OUT / "completion_review.json"
    write_json(
        output,
        dict(
            status="completed",
            paired_rows=len(paired),
            verified_folds=len(jobs),
            paired_predictions_sha256=sha(OUT / "paired_predictions.parquet"),
            settings_sha256=sha(CONFIG),
            selected_tuning_tree_caps=caps,
            point_estimates=points,
            paired_percentile_ranges=intervals,
        ),
    )
    print(output, flush=True)


if __name__ == "__main__":
    main()
