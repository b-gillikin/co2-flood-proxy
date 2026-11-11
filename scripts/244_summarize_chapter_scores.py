#!/usr/bin/env python3
"""Consolidate the complete map census into paired event and episode contrasts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import OUT, atomic_json, sha256

COUNT_COLUMNS = [f"c{i}{j}" for i in range(3) for j in range(3)]


def iou_from_counts(frame):
    union = frame.c20 + frame.c21 + frame.c22 + frame.c02 + frame.c12
    return frame.c22 / union.replace(0, np.nan)


def block_estimate(values, lookup):
    values = values.dropna()
    grouped = values.groupby(values.index.map(lookup)).mean()
    if len(grouped) < 2:
        return {
            "estimate": float(grouped.mean()) if len(grouped) else None,
            "interval_low": None,
            "interval_high": None,
            "blocks": len(grouped),
            "activations": len(values),
        }, []
    numbers = grouped.to_numpy()
    rng = np.random.default_rng(20261111)
    draws = numbers[rng.integers(0, len(numbers), size=(9999, len(numbers)))].mean(axis=1)
    low, high = np.quantile(draws, [0.025, 0.975])
    leave_out = [
        {"omitted_block": key, "estimate": float(grouped.drop(key).mean())} for key in grouped.index
    ]
    return {
        "estimate": float(grouped.mean()),
        "interval_low": float(low),
        "interval_high": float(high),
        "blocks": len(numbers),
        "activations": len(values),
        "activation_balanced_mean": float(values.mean()),
        "event_min": float(values.min()),
        "event_max": float(values.max()),
    }, leave_out


def contrasts():
    comparisons = {}
    pairs = [("native", "unet"), ("native", "physical"), ("unet", "physical")]
    for first, second in pairs:
        for dataset, reference, support in [
            ("delivered", "p0", "full"),
            ("ee", "p0", "paired"),
            ("ee", "p1", "paired"),
        ]:
            comparisons[f"{first}_minus_{second}__{dataset}_{reference}"] = {
                (first, dataset, reference, support): 1,
                (second, dataset, reference, support): -1,
            }
    for model in ("native", "unet", "physical"):
        comparisons[f"reference_P1_minus_P0__{model}"] = {
            (model, "ee", "p1", "paired"): 1,
            (model, "ee", "p0", "paired"): -1,
        }
    for first, second in pairs:
        comparisons[f"interaction__{first}_minus_{second}"] = {
            (first, "ee", "p1", "paired"): 1,
            (first, "ee", "p0", "paired"): -1,
            (second, "ee", "p1", "paired"): -1,
            (second, "ee", "p0", "paired"): 1,
        }
    return comparisons


def performance_table(events, config):
    lookup = {
        event: block for block, members in config["episode_blocks"].items() for event in members
    }
    records = []
    group = ["stratum", "variant", "model", "dataset", "reference", "support"]
    for combination, rows in events.groupby(group):
        event_means = rows.groupby("event").flood_iou.mean()
        estimate, _ = block_estimate(event_means, lookup)
        per_seed = []
        pooled = []
        false_area, missed_area = [], []
        for _seed, repeated in rows.groupby("seed"):
            per_seed.append(
                block_estimate(repeated.set_index("event").flood_iou, lookup)[0]["estimate"]
            )
            counts = repeated[COUNT_COLUMNS].sum().to_frame().T
            pooled.append(iou_from_counts(counts).iloc[0])
            false_area.append(float((counts.c02.iloc[0] + counts.c12.iloc[0]) * 100 / 1e6))
            missed_area.append(float((counts.c20.iloc[0] + counts.c21.iloc[0]) * 100 / 1e6))
        finite_seeds = [value for value in per_seed if value is not None]
        records.append(
            {
                **dict(zip(group, combination, strict=True)),
                **estimate,
                "seed_min": min(finite_seeds) if finite_seeds else None,
                "seed_max": max(finite_seeds) if finite_seeds else None,
                "pooled_pixel_iou": float(np.nanmean(pooled))
                if np.isfinite(pooled).any()
                else None,
                "false_flood_km2_record_sum": float(np.mean(false_area)),
                "missed_flood_km2_record_sum": float(np.mean(missed_area)),
            }
        )
    return pd.DataFrame(records)


def summarize_table(scores, coverage, config):
    lookup = {
        event: block for block, events in config["episode_blocks"].items() for event in events
    }
    data = scores.merge(
        coverage[["key", "post_label_offset_days", "source_bbox_intersection"]],
        on="key",
        validate="many_to_one",
    )
    event_tables, estimates, event_contrasts, leave_out_rows = [], [], [], []
    strata = {
        "all": np.ones(len(data), dtype=bool),
        "listed_timing_within_24h": data.post_label_offset_days.abs() <= 1,
        "new_source_footprint": ~data.source_bbox_intersection,
        "overlapping_source_footprint": data.source_bbox_intersection,
    }
    for stratum, selected in strata.items():
        subset = data.loc[selected]
        if subset.empty:
            continue
        group = ["variant", "event", "model", "seed", "dataset", "reference", "support"]
        counts = subset.groupby(group, as_index=False)[COUNT_COLUMNS + ["known_pixels"]].sum()
        counts["flood_iou"] = iou_from_counts(counts)
        counts["stratum"] = stratum
        event_tables.append(counts)
        for variant, current in counts.groupby("variant"):
            by_model = (
                current.groupby(["event", "model", "dataset", "reference", "support"])
                .flood_iou.mean()
                .reset_index()
            )
            wide = by_model.pivot(
                index="event",
                columns=["model", "dataset", "reference", "support"],
                values="flood_iou",
            )
            for name, terms in contrasts().items():
                if not all(term in wide.columns for term in terms):
                    continue
                values = sum(wide[term] * coefficient for term, coefficient in terms.items())
                result, omissions = block_estimate(values, lookup)
                record = {"stratum": stratum, "variant": variant, "contrast": name, **result}
                estimates.append(record)
                for event, value in values.dropna().items():
                    event_contrasts.append(
                        {
                            "stratum": stratum,
                            "variant": variant,
                            "contrast": name,
                            "event": event,
                            "block": lookup[event],
                            "difference": float(value),
                        }
                    )
                leave_out_rows.extend(
                    {"stratum": stratum, "variant": variant, "contrast": name, **row}
                    for row in omissions
                )
    return (
        pd.concat(event_tables, ignore_index=True),
        pd.DataFrame(estimates),
        pd.DataFrame(event_contrasts),
        pd.DataFrame(leave_out_rows),
    )


def main():
    if (
        not (OUT / "archives-complete.json").exists()
        or not (OUT / "physical-complete.json").exists()
    ):
        raise ValueError(
            "Final summary requires the complete learned and physical scoring censuses"
        )
    physical = pd.read_parquet(OUT / "physical_scores.parquet")
    files = sorted((OUT / "archive_scores").glob("*.parquet"))
    if len(files) != 46:
        raise ValueError("Archive score census differs")
    scores = pd.concat([physical] + [pd.read_parquet(p) for p in files], ignore_index=True)
    key = ["key", "dataset", "reference", "model", "seed", "support", "variant"]
    if scores.duplicated(key).any():
        raise ValueError("Duplicate scored map/support")
    check = scores.groupby(
        ["key", "dataset", "reference", "support", "variant"]
    ).known_pixels.nunique()
    if (check > 1).any():
        raise ValueError("Methods/seeds differ in scored pixel support")
    if len(scores[key[:5]].drop_duplicates()) != 21889:
        raise ValueError("Final scored-map census differs")
    coverage = pd.read_parquet(OUT / "support/tile_coverage.parquet")
    config_path = ROOT / "config/limburg_chapter_evaluation_v1.json"
    config = json.loads(config_path.read_text())
    event, estimates, contrasts_table, leave_out = summarize_table(scores, coverage, config)
    performance = performance_table(event, config)
    summary = OUT / "summary"
    summary.mkdir(parents=True, exist_ok=True)
    for name, table in [
        ("tile_scores", scores),
        ("event_scores", event),
        ("contrasts", estimates),
        ("event_contrasts", contrasts_table),
        ("leave_one_block_out", leave_out),
        ("performance", performance),
    ]:
        table.to_parquet(summary / f"{name}.parquet", index=False)
    primary = estimates.loc[(estimates.stratum == "all") & (estimates.variant == "composed")]
    lines = [
        "# Internal flood-map results guide",
        "",
        "Brian writes dissertation/article text.",
        "",
        "All results below use the completed released cohort and fixed source-trained models.",
        "Values are differences in flood IoU; positive favors the first method or P1.",
        "Intervals resample eight conservative episode blocks. With so few blocks they are exploratory uncertainty summaries.",
        "Listed SAR/label timing discrepancies and shared source products limit interpretation as independent simultaneous flood truth.",
        "",
        "| Method | Image chain | Reference | Support | Episode-balanced IoU | Pixel-pooled IoU |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in performance.loc[
        (performance.stratum == "all") & (performance.variant == "composed")
    ].itertuples():
        lines.append(
            f"| {row.model} | {row.dataset} | {row.reference} | {row.support} | {row.estimate:.3f} | {row.pooled_pixel_iou:.3f} |"
        )
    lines += [
        "",
        "| Contrast | Difference | 95% block-bootstrap interval | Blocks |",
        "| --- | ---: | --- | ---: |",
    ]
    for row in primary.itertuples():
        interval = (
            f"[{row.interval_low:.3f}, {row.interval_high:.3f}]"
            if pd.notna(row.interval_low)
            else "undefined"
        )
        lines.append(f"| {row.contrast} | {row.estimate:.3f} | {interval} | {row.blocks} |")
    lines += [
        "",
        "Read the per-activation and seed tables alongside these averages. A few events cannot establish general model superiority or equivalence.",
        "The delivered P0 cohort is distinct from the same-processing paired P0/P1 subset; their scores are not a reference-age contrast.",
        "False/missed area and permanent-water confusion counts are retained in the tile/event tables. Local July 2021 receiving cases remain a separate interpretation layer.",
        "Sensitivity tables retain source-mask composition, validity and a one-pixel boundary convention, timing strata and source-footprint flags.",
    ]
    (summary / "results-guide.md").write_text("\n".join(lines) + "\n")
    atomic_json(
        summary / "complete.json",
        {
            "status": "complete_external_comparisons",
            "scored_maps": 21889,
            "tile_score_rows": len(scores),
            "activations": 9,
            "episode_blocks": len(config["episode_blocks"]),
            "contract_sha256": sha256(config_path),
            "inputs": {
                str(p.relative_to(ROOT)): sha256(p)
                for p in files + [OUT / "physical_scores.parquet"]
            },
            "outputs": {p.name: sha256(p) for p in summary.glob("*.parquet")},
        },
    )
    print(primary.to_string(index=False))


if __name__ == "__main__":
    main()
