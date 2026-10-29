"""Audit completed individual experiments and write paired evidence tables.

Run incrementally; a partial queue is labelled partial and is never substituted
for a complete ten-experiment conclusion. These are research aids, not prose.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_individual_review import paired_summary, verify_losses
from src.eo_individual_transfer import atomic_json
from src.eo_inputs import sha256

OUT = ROOT / "results/limburg_individual_experiments_v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", help="One score directory name; default all completed jobs")
    args = parser.parse_args()
    cases = pd.read_parquet(OUT / "preparation/cases.parquet")
    years = sorted(cases.cutoff_utc.dt.year.unique())
    rng = np.random.default_rng(1729)
    draws = np.array(
        [
            np.bincount(rng.integers(0, len(years), len(years)), minlength=len(years))
            for _ in range(999)
        ]
    )
    shared = OUT / "review/year-bootstrap.npz"
    shared.parent.mkdir(parents=True, exist_ok=True)
    with shared.with_suffix(".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if shared.exists():
            held = np.load(shared)
            np.testing.assert_array_equal(held["multiplicities"], draws)
            np.testing.assert_array_equal(held["years"], years)
        else:
            tmp = shared.with_name(shared.name + f".{os.getpid()}.tmp")
            with tmp.open("wb") as stream:
                np.savez_compressed(stream, years=np.array(years), multiplicities=draws)
            tmp.replace(shared)
    paths = (
        [OUT / "scores" / args.job / "manifest.json"]
        if args.job
        else sorted((OUT / "scores").glob("*/manifest.json"))
    )
    inventory = []
    for path in paths:
        manifest = json.loads(path.read_text())
        assert manifest["status"] == "completed"
        for name, h in manifest["outputs"].items():
            assert sha256(path.parent / name) == h, f"Output changed: {path.parent / name}"
        for name, h in manifest["source_hashes"].items():
            assert sha256(ROOT / name) == h, f"Source changed since fitting: {name}"
        meta = pd.read_parquet(path.parent / "cases.parquet")
        scores = pd.read_parquet(path.parent / "scores.parquet")
        predictions = dict(np.load(path.parent / "predictions.npz"))
        checked = verify_losses(meta, predictions, scores)
        tuning = json.loads((path.parent / "tuning.json").read_text())
        for record in tuning:
            assert all(v < record["year"] for v in record.get("validation_years", []))
        methods = scores.pivot(index="assessment_id", columns="method", values="mae").reindex(
            meta.assessment_id
        )
        contrasts = [
            ("encoder_correction", x)
            for x in [
                "raw_correction",
                "conventional_mean",
                "conventional_median",
                "fixed_year_mean",
                "fixed_year_median",
            ]
        ]
        if "ablation_correction" in methods:
            contrasts = [("encoder_correction", "ablation_correction")]
        tables = []
        subsets = {
            "all": np.ones(len(meta), bool),
            "high_water": meta.future_p99.to_numpy(bool),
            "documented_flood": meta.documented_flood_overlap.to_numpy(bool),
        }
        groups = {"whole_network": np.ones(len(meta), bool)}
        for country in ["NL", "DE"]:
            groups["country_" + country] = meta.country.eq(country).to_numpy()
        for gauge in meta.gauge.unique():
            groups["gauge_" + str(gauge)] = meta.gauge.eq(gauge).to_numpy()
        for river in meta.physical_river.unique():
            groups["watercourse_" + str(river)] = meta.physical_river.eq(river).to_numpy()
        for a, b in contrasts:
            difference = methods[a].to_numpy() - methods[b].to_numpy()
            for stratum, select in subsets.items():
                for support in ["pipeline_with_fallback", "paired_source_supported"]:
                    keep = select.copy()
                    if support == "paired_source_supported":
                        keep &= meta.raw_available.to_numpy(bool) & meta.encoder_available.to_numpy(
                            bool
                        )
                    if "ablation_correction" in methods:
                        keep &= meta.ablation_paired_support.to_numpy(bool)
                    for group, group_mask in groups.items():
                        ids = keep & group_mask
                        summary = paired_summary(
                            meta.loc[ids],
                            difference[ids],
                            years,
                            draws,
                            manifest["model"] == "dofa",
                        )
                        tables.append(
                            dict(
                                model=manifest["model"],
                                scenario=manifest["scenario"],
                                method=a,
                                reference=b,
                                support=support,
                                stratum=stratum,
                                group=group,
                                units="mm/h",
                                **summary,
                            )
                        )
        review = path.parent / "review"
        review.mkdir(exist_ok=True)
        table = pd.DataFrame(tables)
        table.to_csv(review / "paired-effects.csv", index=False)
        # The same within-storm averaging used by the declared point estimand.
        storm_native = (
            scores.groupby(["gauge", "country", "method", "storm_id"], observed=True)
            .agg(mae_mmh=("mae", "mean"), area_km2=("area_km2", "first"))
            .reset_index()
        )
        native = (
            storm_native.groupby(["gauge", "country", "method"], observed=True)
            .agg(
                storms=("mae_mmh", "count"),
                mae_mmh=("mae_mmh", "mean"),
                area_km2=("area_km2", "first"),
            )
            .reset_index()
        )
        native["mae_m3s"] = native.mae_mmh * native.area_km2 / 3.6
        native.to_csv(review / "site-native-scores.csv", index=False)
        # Preserve every case, plus the largest positive/negative paired contrasts
        # as an explicitly outcome-selected interpretation aid, not a new test.
        detail = meta.copy()
        for a, b in contrasts:
            detail[a + "_minus_" + b] = methods[a].to_numpy() - methods[b].to_numpy()
        detail.to_parquet(review / "case-effects.parquet", index=False)
        delta = detail[contrasts[0][0] + "_minus_" + contrasts[0][1]]
        selected = pd.concat(
            [detail.loc[delta.nsmallest(10).index], detail.loc[delta.nlargest(10).index]]
        ).drop_duplicates("assessment_id")
        selected.to_csv(review / "illustrative-cases.csv", index=False)
        statuses = (
            pd.Series([str(r.get("eo_parameters", "raw_only")) for r in tuning])
            .value_counts()
            .to_dict()
        )
        atomic_json(
            review / "audit.json",
            dict(
                status="passed",
                recomputed_point_losses=checked,
                census_rows=len(meta),
                bootstrap_sha256=sha256(shared),
                bootstrap_draws=999,
                selection_counts=statuses,
                source_manifest_sha256=sha256(path),
                independent_watercourse_groups=6 if manifest["model"] == "dofa" else None,
                inference="Exploratory, conditional on fitted procedures and held network; differences below zero favour the encoder arm",
            ),
        )
        lines = [
            f"{manifest['model']} / {manifest['scenario']}",
            "",
            f"Census assessments: {len(meta)}; EO-supported: {int(meta.encoder_available.sum())}; raw-supported: {int(meta.raw_available.sum())}.",
            "Negative paired error differences favour the encoder arm.",
            "Whole-year intervals condition on fitted models and this held network; they are not family-wise claims or proof of operational warning skill.",
            "",
            "Whole-network paired MAE differences (mm/h):",
        ]
        for r in table[table.group.eq("whole_network")].itertuples():
            lines.append(
                f"{r.stratum}; {r.support}; versus {r.reference}: {r.estimate:.6g} [{r.lower:.6g}, {r.upper:.6g}], n={r.assessments}, years={r.years}, nonfinite draws={r.bootstrap_nonfinite}"
            )
        (review / "results-note.txt").write_text("\n".join(lines) + "\n")
        inventory.append(dict(job=path.parent.name, status="audited", rows=len(meta)))
        print(path.parent.name, "audited", flush=True)
    audited = []
    for p in sorted((OUT / "scores").glob("*/review/audit.json")):
        receipt = json.loads(p.read_text())
        audited.append(
            dict(job=p.parent.parent.name, status=receipt["status"], rows=receipt["census_rows"])
        )
    expected = {
        m + "__" + scenario
        for m in [
            "presto",
            "anysat",
            "galileo",
            "olmoearth",
            "croma",
            "prithvi",
            "copernicus_fm",
            "dofa",
            "terramind",
            "satmae",
        ]
        for scenario in ["rich_basin", "local_q_absent", "all_q_absent"]
        if not (m == "dofa" and scenario == "rich_basin")
    }
    available = {r["job"] for r in audited}
    atomic_json(
        OUT / "review/inventory.json",
        dict(
            status="primary_matrix_available" if expected <= available else "partial",
            jobs=audited,
            missing_primary=sorted(expected - available),
            no_family_winner_claim=True,
        ),
    )


if __name__ == "__main__":
    main()
