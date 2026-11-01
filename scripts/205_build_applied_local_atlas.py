"""All54 local acquisitions: imagery, qualified CEMS references and observability.

Display mosaics are40m nearest-neighbour previews, NOT analysis inputs or new
labels. Coverage counts are computed separately on original10m source grids.
No flood classifier is fitted or applied to local references by this script.
"""

import argparse
import hashlib
import html
import json
import os
import re
from contextlib import ExitStack
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import ListedColormap
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.transform import array_bounds


def dependence(aoi, sensor, scene, reference_time):
    if aoi != "EMSR520_AOI01":
        return "Different reference sensor (Pleiades); time-offset remains important"
    if sensor.startswith("s2"):
        return "Optical input versus radar-derived CEMS reference; not field truth"
    dates = re.findall(r"\d{8}T\d{6}", scene)
    overlaps = False
    if len(dates) >= 2:
        start, end = (pd.Timestamp(t, tz="UTC") for t in dates[:2])
        overlaps = start <= pd.Timestamp(reference_time) <= end
    return (
        "Same radar sensor/reference lineage; acquisition-time overlap candidate (source table lacks full product ID)"
        if overlaps
        else "Same radar sensor/reference lineage; different acquisition time"
    )


def source_support(raw, spectral_bands):
    """QA availability is separate from spectral observation availability."""
    bands = raw[:spectral_bands]
    return (raw[-1] == 1) & np.isfinite(bands).all(0) & (bands != -9999).all(0)


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "results/applied_study_v2/local-atlas")
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    pairs_path = (
        ROOT / "results/applied_study_v1/local_references/scoring/scene-reference-pairs.parquet"
    )
    pairs = pd.read_parquet(pairs_path)
    inventory = json.loads(
        (ROOT / "results/applied_study_v1/local_references/local-scene-inventory.json").read_text()
    )
    aois = {r["aoi"]: r for r in inventory["aois"]}
    context = json.loads((ROOT / "results/applied_study_v2/timing-checked/audit.json").read_text())
    contexts = {(r["aoi"], r["sensor"], r["scene"]): r for r in context["local_cases"]}
    cards = []
    records = []
    hashes = {}
    for path in [
        pairs_path,
        ROOT / "results/applied_study_v1/local_references/local-scene-inventory.json",
        ROOT / "results/applied_study_v2/timing-checked/audit.json",
        Path(__file__),
    ]:
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    sources = ROOT / "data/raw/limburg_applied_tasks/local_scenes"
    for i, ((aoi, sensor, scene), rows) in enumerate(
        pairs.groupby(["aoi", "sensor", "scene"], sort=True)
    ):
        optical = sensor.startswith("s2")
        indices = [4, 3, 2, 14, 15] if optical else [1, 4]
        counts = dict(
            source_valid=0,
            eligible_reference=0,
            source_and_reference=0,
            reference_flood_in_source=0,
            qa_cloud_on_reference=0,
            qa_unknown_on_reference=0,
        )
        with ExitStack() as stack:
            inputs = []
            references = []
            for r in rows.itertuples():
                ipath = sources / r.path
                rpath = ROOT / r.reference_path
                image = stack.enter_context(rasterio.open(ipath))
                ref = stack.enter_context(rasterio.open(rpath))
                if (image.shape, image.transform, image.crs) != (ref.shape, ref.transform, ref.crs):
                    raise ValueError("Unaligned native reference/source")
                raw = image.read()
                label = ref.read(1)
                valid = source_support(raw, 13 if optical else 3)
                eligible = label != 255
                support = valid & eligible
                counts["source_valid"] += int(valid.sum())
                counts["eligible_reference"] += int(eligible.sum())
                counts["source_and_reference"] += int(support.sum())
                counts["reference_flood_in_source"] += int((support & (label == 1)).sum())
                if optical:
                    qa = raw[13]
                    known = np.isfinite(qa) & (qa != -9999)
                    flags = np.where(known, qa, 0).astype(np.int64)
                    cloud = ((flags & (1 << 10)) != 0) | ((flags & (1 << 11)) != 0)
                    counts["qa_cloud_on_reference"] += int((support & known & cloud).sum())
                    counts["qa_unknown_on_reference"] += int((support & ~known).sum())
                for path in [ipath, rpath]:
                    hashes[str(path.relative_to(ROOT))] = hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest()
                inputs.append(image)
                references.append(ref)
            x, transform = merge(
                inputs, indexes=indices, res=40, nodata=-9999, resampling=Resampling.nearest
            )
            bounds = array_bounds(x.shape[1], x.shape[2], transform)
            label, _ = merge(
                references,
                indexes=[1],
                bounds=bounds,
                res=40,
                nodata=255,
                resampling=Resampling.nearest,
            )
        label = label[0]
        valid = source_support(x, 3 if optical else 1)
        if optical:
            image = np.moveaxis(np.clip(x[:3] / 3000, 0, 1), 0, -1)
            image[~valid] = 0.65
        else:
            image = np.where(valid, np.clip((x[0] + 25) / 25, 0, 1), 0.65)
        support = np.zeros(label.shape, dtype=np.uint8)
        support[valid] = 1
        support[valid & (label != 255)] = 2
        if optical:
            qa = x[3]
            known = np.isfinite(qa) & (qa != -9999)
            flags = np.where(known, qa, 0).astype(np.int64)
            cloud = ((flags & (1 << 10)) != 0) | ((flags & (1 << 11)) != 0)
            support[valid & (label != 255) & known & cloud] = 3
            support[valid & (label != 255) & ~known] = 4
        extent = [bounds[0] / 1000, bounds[2] / 1000, bounds[1] / 1000, bounds[3] / 1000]
        fig, axes = plt.subplots(1, 3, figsize=(14, 5))
        axes[0].imshow(image, cmap="gray", vmin=0, vmax=1, extent=extent)
        axes[1].imshow(
            np.where(label == 255, 2, label),
            cmap=ListedColormap(["#eee9dd", "#12aeb2", "#999999"]),
            vmin=0,
            vmax=2,
            extent=extent,
            interpolation="nearest",
        )
        axes[2].imshow(
            support,
            cmap=ListedColormap(["#999999", "#9988bb", "#66aa88", "#ee9933", "#ddcc77"]),
            vmin=0,
            vmax=4,
            extent=extent,
            interpolation="nearest",
        )
        titles = [
            "Optical RGB / radar VV (display stretch)",
            "CEMS: mapped flood cyan; gray excluded/unknown",
            "Support: green eligible; orange cloud flags",
        ]
        for ax, title in zip(axes, titles, strict=True):
            ax.set_title(title, fontsize=9)
            ax.set_xlabel("UTM31 east (km)")
        axes[0].set_ylabel("UTM31 north (km)")
        row = rows.iloc[0]
        stamp = pd.Timestamp(row.acquisition_utc)
        offset = float(row.reference_offset_hours)
        note = dependence(aoi, sensor, scene, aois[aoi]["reference_time"])
        fig.suptitle(
            f"{aois[aoi]['name']} — {sensor} — {stamp.isoformat()}\nReference offset {offset:+.2f}h | {note}",
            fontsize=9,
        )
        fig.text(
            0.02,
            0.01,
            "40m preview only; counts use native grids. Purple: source observed but reference excluded. Yellow: QA unknown. Gray: no source. QA60 does not guarantee clear water visibility.",
            fontsize=8,
        )
        fig.tight_layout(rect=(0, 0.04, 1, 0.9))
        filename = f"acquisition-{i:03d}.png"
        fig.savefig(a.output / filename, dpi=110)
        plt.close(fig)
        record = dict(
            aoi=aoi,
            name=aois[aoi]["name"],
            sensor=sensor,
            scene=scene,
            acquisition_utc=stamp.isoformat(),
            reference_time=aois[aoi]["reference_time"],
            reference_offset_hours=offset,
            dependence=note,
            role=row.comparison_role,
            counts=counts,
            context=contexts[(aoi, sensor, scene)],
            figure=filename,
        )
        records.append(record)
        cards.append(
            f'<section id="acq-{i}"><h2>{html.escape(aois[aoi]["name"])} — {html.escape(sensor)} — {stamp.strftime("%d %b %H:%M UTC")}</h2><p>{html.escape(row.comparison_role)}; {html.escape(note)}.</p><p>Native coverage: {counts["source_and_reference"]:,} eligible observed pixels; {counts["qa_cloud_on_reference"]:,} QA cloud-flagged. Not accuracy scores.</p><img loading="lazy" src="{filename}" style="max-width:100%"></section>'
        )
        print(
            json.dumps(
                dict(
                    acquisitions=len(records),
                    tiles_accounted=sum(
                        len(g)
                        for _, g in list(pairs.groupby(["aoi", "sensor", "scene"], sort=True))[
                            : i + 1
                        ]
                    ),
                )
            ),
            flush=True,
        )
    # Full acquisition timeline and explicit gauge quality, not invented phase.
    fig, axes = plt.subplots(4, 1, figsize=(13, 9), sharex=True)
    for ax, (aoi, info) in zip(axes[:3], aois.items(), strict=True):
        selected = [r for r in records if r["aoi"] == aoi]
        for sensor, color, y in [
            ("s1_pre", "#888888", 0),
            ("s1_event", "#3366aa", 1),
            ("s2_event", "#dd9933", 2),
        ]:
            times = [pd.Timestamp(r["acquisition_utc"]) for r in selected if r["sensor"] == sensor]
            ax.scatter(times, [y] * len(times), label=sensor, color=color, s=18)
        ax.axvline(
            pd.Timestamp(info["reference_time"]),
            color="black",
            linestyle="--",
            label="CEMS reference time",
        )
        ax.set_title(info["name"] + " — dashed line: CEMS reference acquisition")
        ax.set_yticks([0, 1, 2], ["pre radar", "event radar", "optical"])
        ax.grid(alpha=0.2)
    qpath = ROOT / "results/meuse_context_2026_10_27/venlo_hourly.parquet"
    q = pd.read_parquet(qpath).loc["2021-06-27":"2021-07-23"]
    axes[-1].plot(
        q.index,
        q.q_display,
        color="#999999",
        linestyle="--",
        label="Display (may include interpolation)",
    )
    axes[-1].plot(q.index, q.q_strict, color="#226644", label="Strict measured series")
    axes[-1].set_ylabel("Venlo Q (m³/s)")
    axes[-1].legend(fontsize=8)
    axes[-1].set_title(
        "Venlo context only; missing records remain gaps; measured window peak unverified"
    )
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    fig.tight_layout()
    fig.savefig(a.output / "timeline.png", dpi=120)
    plt.close(fig)
    hashes[str(qpath.relative_to(ROOT))] = hashlib.sha256(qpath.read_bytes()).hexdigest()
    (a.output / "atlas.json").write_text(
        json.dumps(
            dict(
                acquisitions=records,
                input_hashes=hashes,
                total_acquisitions=len(records),
                total_source_tiles=len(pairs),
                display_resolution_m=40,
                interpretation="Qualified local evidence atlas, not local model validation. Different dates are not independent events; mapped non-flood is not verified dry ground. No live delivery/forecast/peak-inundation claim.",
            ),
            indent=2,
        )
        + "\n"
    )
    (a.output / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Local flood evidence atlas</title><body style="font-family:sans-serif;max-width:1500px;margin:auto"><h1>Local event evidence — all54 acquisitions</h1><p>Venlo, Eschweiler, Wassenberg. Input imagery, CEMS mapping and observability; no local model predictions yet. Source masks and time offsets remain explicit.</p><img src="timeline.png" style="max-width:100%">'
        + "".join(cards)
        + "</body>"
    )


if __name__ == "__main__":
    main()
