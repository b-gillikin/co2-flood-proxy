"""Recheck ALL physical predictions and render every held-event error sheet.

Sources/unknown masks are independently reconstructed from held raster bands.
Three displayed chips per event are diagnostic examples, not the evaluation
sample: every chip contributes to rederived confusion counts and the ledger.
"""

import argparse
import functools
import hashlib
import html
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import ListedColormap

from applied_water import PRITHVI_S2, class_scores, confusion, valid_labels

SEN = ROOT / "data/raw/limburg_applied_tasks/sen1floods11"
RADAR = ROOT / "data/raw/limburg_applied_tasks/flood_s1/extracted/flood_s1/data"


@functools.lru_cache(maxsize=4)
def sen_source(chip):
    arrays = []
    for kind in ["LabelHand", "S1Hand", "S2Hand"]:
        with rasterio.open(SEN / kind / f"{chip}_{kind}.tif") as src:
            arrays.append(src.read())
    return arrays


def source(chip, task, radar_inventory):
    if task != "copernicus":
        label, s1, s2 = sen_source(chip)
        label = valid_labels(
            label[0],
            s1=s1 if task != "prithvi" else None,
            s2=(s2[PRITHVI_S2] if task == "prithvi" else s2) if task != "galileo" else None,
        )
        image = (
            np.moveaxis(np.clip(s2[[3, 2, 1]] / 3000, 0, 1), 0, -1)
            if task != "galileo"
            else np.clip((s1[0] + 25) / 25, 0, 1)
        )
        return label, np.nan_to_num(image, nan=0)
    folder = RADAR / radar_inventory.loc[chip, "source_path"]
    arrays = []
    for prefix in ["SL1_IVV", "SL1_IVH", "MS1_IVV", "MS1_IVH", "MK0_MLU", "MK0_MNA"]:
        (path,) = folder.glob(prefix + "*.tif")
        with rasterio.open(path) as src:
            arrays.append(src.read(1))
    raw = np.stack(arrays[:4])
    valid = (np.isfinite(raw) & (raw != 0)).all(0) & (arrays[5] == 1) & (arrays[4] != 3)
    # Cast BEFORE inserting-1: NumPy2 scalar promotion can otherwise wrap an
    # unsigned source's ignore value to255. The production loader already casts.
    label = np.where(valid, arrays[4].astype(np.int64), -1)
    image = np.clip((10 * np.log10(np.maximum(arrays[2], 1e-10)) + 30) / 30, 0, 1)
    return label, np.nan_to_num(image, nan=0)


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "results/applied_study_v2/physical-audit")
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    planpath = ROOT / "results/applied_study_v2/execution-plan.json"
    plan = json.loads(planpath.read_text())
    radar = (
        pd.read_parquet(ROOT / "results/applied_study_v1/evaluation/radar-change-inventory.parquet")
        .rename(columns={"record": "chip"})
        .set_index("chip")
    )
    tiles = []
    events = []
    hashes = {}
    pages = []
    for job in plan["jobs"]:
        if job["learner"] != "physical":
            continue
        folder = ROOT / job["output"]
        manifest = json.loads((folder / "manifest.json").read_text())
        result = json.loads((folder / "selected-test.json").read_text())
        selection = json.loads((folder / "selection.json").read_text())
        classes = 3 if job["task"] == "copernicus" else 2
        target = classes - 1
        for name, digest in manifest["source_hashes"].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError("Changed source: " + name)
        matrices = {}
        jobtiles = []
        for chip in manifest["partitions"]["test"]:
            path = folder / "predictions" / f"{chip}.npz"
            prediction = np.load(path, allow_pickle=False)["prediction"]
            label, _ = source(chip, job["task"], radar)
            if prediction.shape != label.shape or not np.array_equal(prediction == 255, label < 0):
                raise ValueError("Changed target grid/unknown mask: " + str(path))
            m = confusion(label, prediction, classes=classes)
            event = str(job["fold"])
            matrices.setdefault(event, np.zeros((classes, classes), dtype=np.int64))
            matrices[event] += m
            scores = class_scores(m)
            tp = int(m[target, target])
            fn = int(m[target].sum() - tp)
            fp = int(m[:, target].sum() - tp)
            row = dict(
                task=job["task"],
                fold=event,
                chip=chip,
                tp=tp,
                fn=fn,
                fp=fp,
                tn=int(m.sum()) - tp - fn - fp,
                unknown_pixels=int((label < 0).sum()),
                iou=float(scores["iou"][target]) if np.isfinite(scores["iou"][target]) else None,
                evaluated_pixels=int(m.sum()),
                prediction=str(path.relative_to(ROOT)),
            )
            tiles.append(row)
            jobtiles.append(row)
            hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        if {e: m.tolist() for e, m in matrices.items()} != result["confusion"]:
            raise ValueError(
                "Saved confusion differs from independently reconstructed targets: " + job["id"]
            )
        scores = class_scores(sum(matrices.values()))
        c = selection["candidate"]
        endpoints = []
        for key in ["threshold", "threshold_db", "drop_db"]:
            values = [r[key] for r in manifest["threshold_grid"] if key in r]
            if key in c and c[key] in [min(values), max(values)]:
                endpoints.append(key)
        eventrow = dict(
            task=job["task"],
            fold=str(job["fold"]),
            chips=len(jobtiles),
            candidate=c,
            validation_iou=selection["validation_iou"],
            target_iou=float(scores["iou"][target]),
            target_precision=float(scores["precision"][target]),
            target_recall=float(scores["recall"][target]),
            target_f1=float(scores["f1"][target]),
            all_class_iou=[float(v) if np.isfinite(v) else None for v in scores["iou"]],
            boundary_parameters=endpoints,
            reference_pixels=int(sum(matrices.values()).sum()),
        )
        events.append(eventrow)
        # Error-selected illustrations are explicitly diagnostic; metrics above
        # always use every chip. Deduplicate examples, including tiny events.
        ordered = sorted(jobtiles, key=lambda r: (r["iou"] is None, r["iou"] or 0, r["chip"]))
        chosen = []
        for row in [
            max(jobtiles, key=lambda r: r["fp"]),
            max(jobtiles, key=lambda r: r["fn"]),
            ordered[len(ordered) // 2],
        ]:
            if row["chip"] not in {r["chip"] for r in chosen}:
                chosen.append(row)
        fig, axes = plt.subplots(len(chosen), 4, figsize=(12, 3 * len(chosen)), squeeze=False)
        for axesrow, row in zip(axes, chosen, strict=True):
            label, image = source(row["chip"], job["task"], radar)
            pred = np.load(ROOT / row["prediction"])["prediction"]
            errors = np.zeros(label.shape, dtype=np.uint8)
            known = label >= 0
            wet = label == target
            positive = pred == target
            errors[known & wet & positive] = 1
            errors[known & ~wet & positive] = 2
            errors[known & wet & ~positive] = 3
            errors[~known] = 4
            axesrow[0].imshow(image, cmap="gray", vmin=0, vmax=1)
            cmap = ListedColormap(["#eee9dd", "#2171b5", "#12aeb2", "#999999"])
            for ax, data in [(axesrow[1], label), (axesrow[2], np.where(pred == 255, -1, pred))]:
                view = np.where(data < 0, 3, data)
                ax.imshow(view, cmap=cmap, vmin=0, vmax=3, interpolation="nearest")
            axesrow[3].imshow(
                errors,
                cmap=ListedColormap(["#f4f4f4", "#228833", "#ee9933", "#bb3388", "#999999"]),
                vmin=0,
                vmax=4,
                interpolation="nearest",
            )
            axesrow[0].set_ylabel(row["chip"], fontsize=7)
            for ax in axesrow:
                ax.set_xticks([])
                ax.set_yticks([])
            axesrow[3].set_title(f"FP {row['fp']:,} / FN {row['fn']:,}", fontsize=8)
        for ax, title in zip(
            axes[0],
            [
                "Input (display stretch)",
                "Benchmark reference",
                "Selected physical prediction",
                "TP green / FP orange / FN magenta",
            ],
            strict=True,
        ):
            ax.set_title(title, fontsize=9)
        fig.suptitle(
            f"{job['task']} — {job['fold']} | held-event target IoU {eventrow['target_iou']:.3f}\nGray is unknown; benchmark agreement, not field truth. Diagnostic chips only.",
            fontsize=10,
        )
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        filename = job["id"] + ".png"
        fig.savefig(a.output / filename, dpi=110)
        plt.close(fig)
        pages.append(
            f'<h2>{html.escape(job["task"])} — {html.escape(str(job["fold"]))}</h2><p>{html.escape(json.dumps(c))}</p><img loading="lazy" src="{filename}" style="max-width:100%">'
        )
        print(
            json.dumps(dict(completed_events=len(events), checked_predictions=len(tiles))),
            flush=True,
        )
    pd.DataFrame(tiles).to_csv(a.output / "all-prediction-checks.csv", index=False)
    pd.DataFrame(events).to_json(a.output / "event-scores.json", orient="records", indent=2)
    report = dict(
        status="completed",
        held_event_outputs=len(events),
        predictions_checked=len(tiles),
        all_saved_confusions_reproduced=True,
        all_unknown_masks_reproduced=True,
        prediction_hashes=hashes,
        plan_sha256=hashlib.sha256(planpath.read_bytes()).hexdigest(),
        counts_by_task=pd.DataFrame(tiles).groupby("task").size().to_dict(),
        interpretation="Complete benchmark census. Illustrations are error-selected, not a new sample. Different tasks/sensors/targets are not a model ranking. Threshold endpoints are diagnostic, not a test-driven retuning instruction.",
    )
    (a.output / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    (a.output / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Physical baseline audit</title><body style="max-width:1400px;margin:auto;font-family:sans-serif"><h1>All53 held-event physical baselines</h1><p>All6,338 predictions checked. Optical RGB or radar VV context; gray unknown. Water and new-flood targets differ. Error-selected chips illustrate failures; all chips determine scores.</p>'
        + "".join(pages)
        + "</body>"
    )


if __name__ == "__main__":
    main()
