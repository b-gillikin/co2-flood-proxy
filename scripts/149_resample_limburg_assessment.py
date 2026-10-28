"""Joint-outcome version of script 146 intervals; identical draws/estimands."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analogue_bootstrap import joint_intervals
from src.eo_comparison import load_script
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output

OUT = ROOT / "results/limburg_assessment_2026_10_27"
COMPONENTS = ["archive_difference", "representation_difference", "total_difference"]


def wide_intervals(run, frame, tags):
    out = []
    index = ["query_event_id", "query_storm_id", "query_onset_utc"]
    assert not frame.duplicated(index + ["metric"]).any()
    wide = frame.pivot(index=index, columns="metric", values=COMPONENTS)
    assert wide.notna().all().all()
    names = {f"c{i}": key for i, key in enumerate(wide.columns)}
    wide.columns = list(names)
    wide = wide.reset_index()
    earliest = run.meta.groupby("storm_id").onset_utc.min().dt.year
    wide["storm_year"] = wide.query_storm_id.map(earliest)
    for unit, label in [("query_storm_id", "storm_id"), ("storm_year", "storm_year")]:
        results = joint_intervals(
            wide,
            unit,
            list(names),
            draws=run.config["bootstrap_draws"],
            seed=run.config["bootstrap_seed"],
        )
        for col, values in results.items():
            component, metric = names[col]
            out.append(
                tags | dict(metric=metric, component=component, resampling_unit=label) | values
            )
    return out


def main():
    module = load_script("146_run_limburg_assessment.py", "joint_assessment_run")
    run = module.Run()
    dest = OUT / "intervals"
    outputs = []
    started = time.perf_counter()
    for path in sorted((OUT / "archive").glob("*/decomposition.parquet")):
        frame = pd.read_parquet(run.bind(path))
        keys = ["family", "kind", "model", "population", "setting", "baseline", "target_k"]
        for key, g in frame.groupby(keys, observed=True):
            tags = dict(zip(keys, key, strict=True)) | {"module": "archive"}
            for country in ["all", "NL", "DE"]:
                h = g if country == "all" else g[g.query_country.eq(country)]
                if not h.empty:
                    outputs += wide_intervals(run, h, tags | {"query_country": country})
        print(
            "joint intervals",
            path.parent.name,
            len(outputs),
            "rows",
            round(time.perf_counter() - started, 1),
            "seconds",
            flush=True,
        )
    parts = []
    for folder in sorted((OUT / "meuse").iterdir()):
        f = pd.read_parquet(run.bind(folder / "scores.parquet"))
        for setting in ["other_rivers", "quality", "main"]:
            if folder.name.endswith("_" + setting):
                context = folder.name[: -(len(setting) + 1)]
                break
        full = pd.read_parquet(run.bind(OUT / "baselines" / f"rain_{setting}" / "scores.parquet"))
        for baseline in run.config["baselines"]:
            a = f[f.method.eq(baseline + "_meuse")]
            r = f[f.method.eq(baseline)]
            b = full[full.method.eq(baseline)]
            x = a.merge(
                r,
                on=["query_event_id", "target_k"],
                suffixes=("_aug", "_restricted"),
                validate="one_to_one",
            )
            x = x.merge(b, on=["query_event_id", "target_k"], validate="one_to_one")
            for metric in module.SCORE_FIELDS:
                h = x[
                    [
                        "query_event_id",
                        "target_k",
                        "query_storm_id",
                        "query_onset_utc",
                        "query_country",
                    ]
                ].copy()
                h = h.assign(
                    context=context,
                    setting=setting,
                    baseline=baseline,
                    metric=metric,
                    full_loss=x[metric],
                    restricted_loss=x[metric + "_restricted"],
                    augmented_loss=x[metric + "_aug"],
                )
                h["archive_difference"] = h.restricted_loss - h.full_loss
                h["representation_difference"] = h.augmented_loss - h.restricted_loss
                h["total_difference"] = h.augmented_loss - h.full_loss
                parts.append(h)
    pairs = pd.concat(parts, ignore_index=True)
    keys = ["context", "setting", "baseline", "target_k"]
    for key, g in pairs.groupby(keys, observed=True):
        tags = dict(zip(keys, key, strict=True)) | {"module": "meuse"}
        for country in ["all", "NL", "DE"]:
            h = g if country == "all" else g[g.query_country.eq(country)]
            if not h.empty:
                outputs += wide_intervals(run, h, tags | {"query_country": country})
    with fresh_output(dest) as work:
        pd.DataFrame(outputs).to_parquet(work / "paired_intervals.parquet", index=False)
        pairs.to_parquet(work / "meuse_pairs.parquet", index=False)
        run.sources.update(
            {
                str(Path(__file__).relative_to(ROOT)): sha256(Path(__file__)),
                "src/analogue_bootstrap.py": sha256(ROOT / "src/analogue_bootstrap.py"),
            }
        )
        run.finish(work)
    print(
        "joint bootstrap complete",
        len(outputs),
        "rows",
        round(time.perf_counter() - started, 1),
        "seconds",
        flush=True,
    )


if __name__ == "__main__":
    main()
