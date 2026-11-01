"""Use held dates and legitimate gauge context; audit pre/post gap alternatives.

Venlo is linked only to Venlo. No automatic Wurm link for Rur/Inde AOIs.
SL2 metadata is inventoried, not substituted into model inputs after results.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from applied_timing import acquisition_context


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "results/applied_study_v2/timing")
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    source = ROOT / "results/applied_study_v1/local_references/local-scene-pixel-inventory.parquet"
    gaugesource = ROOT / "results/meuse_context_2026_10_27/venlo_hourly.parquet"
    f = pd.read_parquet(source).drop_duplicates(["aoi", "sensor", "scene"])
    gauge = pd.read_parquet(gaugesource)
    rows = []
    for r in f.itertuples():
        entry = dict(
            aoi=r.aoi,
            sensor=r.sensor,
            scene=r.scene,
            acquisition_utc=r.acquisition_utc,
            reference_offset_hours=r.reference_offset_hours,
            delivery_time_utc=None,
            delivery_status="not established by acquisition metadata",
        )
        if r.aoi == "EMSR520_AOI01" and pd.Timestamp("2021-07-01T00:00Z") <= pd.Timestamp(
            r.acquisition_utc
        ) <= pd.Timestamp("2021-08-01T00:00Z"):
            entry.update(
                gauge="venlo",
                link_basis="Same named Meuse mainstem AOI/station; context, not pixel truth",
                context=acquisition_context(
                    gauge, r.acquisition_utc, "2021-07-01T00:00Z", "2021-08-01T00:00Z"
                ),
            )
        elif r.aoi == "EMSR520_AOI01":
            entry.update(
                gauge="venlo",
                context=None,
                reason="Pre-event acquisition outside declared July review window; retain without a July flood-phase label",
            )
        else:
            entry.update(
                gauge=None,
                context=None,
                reason="No held, verified local gauge link for this Rur/Inde AOI; do not substitute Wurm",
            )
        rows.append(entry)
    base = ROOT / "data/raw/limburg_applied_tasks/flood_s1/extracted/flood_s1"
    pairs = []
    paths = [source, gaugesource]
    for split in ["train", "val", "test"]:
        path = base / f"grid_dict_{split}.json"
        paths.append(path)
        for record, r in json.loads(path.read_text()).items():
            info = r["info"]
            sources = info["sources"]
            post = pd.Timestamp(sources["MS1"]["source_date"])
            for kind in ["SL1", "SL2"]:
                pre = sources.get(kind, {}).get("source_date")
                pairs.append(
                    dict(
                        record=record,
                        event=str(info["actid"]),
                        pair=kind,
                        pre_date=pre,
                        post_date=post.isoformat(),
                        gap_days=(post - pd.Timestamp(pre)).total_seconds() / 86400
                        if pre
                        else None,
                    )
                )
    pairs = pd.DataFrame(pairs)
    pairs.to_parquet(a.output / "radar-reference-gaps.parquet", index=False)
    summary = []
    for (event, kind), group in pairs.groupby(["event", "pair"]):
        d = group.gap_days.dropna()
        summary.append(
            dict(
                event=event,
                pair=kind,
                records=len(group),
                missing_dates=int(group.gap_days.isna().sum()),
                min_days=float(d.min()) if len(d) else None,
                median_days=float(d.median()) if len(d) else None,
                max_days=float(d.max()) if len(d) else None,
                over90_days=int((d > 90).sum()),
                over365_days=int((d > 365).sum()),
            )
        )
    output = dict(
        local_cases=rows,
        radar_gap_summary=summary,
        input_hashes={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
        interpretation="Acquisition context only. Missing measured peaks and gauge links remain unknown. No SL2 substitution, delivery estimate, warning lead time or model result.",
    )
    (a.output / "audit.json").write_text(json.dumps(output, indent=2) + "\n")
    print(
        json.dumps(
            dict(acquisitions=len(rows), radar_records=len(pairs) // 2, gap_groups=len(summary))
        )
    )


if __name__ == "__main__":
    main()
