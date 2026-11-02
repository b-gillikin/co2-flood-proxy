"""Completion and recovery invariants for durable spatial comparison jobs."""

import hashlib
import json
from pathlib import Path

import numpy as np

from applied_selection import select_trial


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for b in iter(lambda: stream.read(8 * 1024**2), b""):
            h.update(b)
    return h.hexdigest()


def atomic(path, value):
    path = Path(path)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def verify_completed(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    trials = json.loads((directory / "trials.json").read_text())
    selected = json.loads((directory / "selection.json").read_text())
    result = json.loads((directory / "selected-test.json").read_text())
    if len(trials) != len(manifest["rates"]) or {r["trial"] for r in trials} != set(
        range(len(trials))
    ):
        raise ValueError("Incomplete candidate ledger")
    if any(r["status"] not in {"completed", "failed"} for r in trials):
        raise ValueError("Unfinished candidate")
    winner = select_trial(trials)
    if (
        selected["trial"] != winner["trial"]
        or selected["validation_iou"] != winner["validation_iou"]
    ):
        raise ValueError("Selection is not validation winner")
    checkpoints = {}
    for r in trials:
        p = directory / f"trial-{r['trial']}.pt"
        if p.exists():
            if sha(p) != r["checkpoint_sha256"]:
                raise ValueError("Checkpoint changed")
            checkpoints[p.name] = dict(bytes=p.stat().st_size, sha256=r["checkpoint_sha256"])
    if f"trial-{winner['trial']}.pt" not in checkpoints:
        raise ValueError("Missing selected checkpoint")
    expected = set(manifest["partitions"]["test"])
    files = list((directory / "predictions").glob("*.npz"))
    if len(expected) != len(manifest["partitions"]["test"]) or {p.stem for p in files} != expected:
        raise ValueError("Incomplete prediction census")
    task = manifest["arguments"]["task"]
    classes = 3 if task == "copernicus" else 2
    shape = (224, 224) if task == "copernicus" else (512, 512)
    valid = 0
    prediction_hashes = {}
    for p in files:
        with np.load(p, allow_pickle=False) as z:
            y = z["prediction"]
            if y.shape != shape or not set(np.unique(y)) <= set(range(classes)) | {255}:
                raise ValueError("Invalid prediction grid/classes")
            valid += int((y != 255).sum())
        prediction_hashes[p.name] = sha(p)
    if valid != sum(int(np.asarray(m).sum()) for m in result["confusion"].values()):
        raise ValueError("Confusion and prediction coverage differ")
    return dict(
        status="verified_complete",
        candidate_failures=sum(r["status"] == "failed" for r in trials),
        test_predictions=len(files),
        test_valid_pixels=valid,
        checkpoints=checkpoints,
        prediction_hashes=prediction_hashes,
        selected_trial=winner["trial"],
        manifest_sha256=sha(directory / "manifest.json"),
    )


def retire_verified_checkpoints(directory, receipt):
    """Only inactive checkpoint files, only after exact remote member readback."""
    directory = Path(directory).resolve()
    receipt = json.loads(Path(receipt).read_text())
    if receipt["status"] != "remote_readback_and_every_member_verified":
        raise ValueError("Remote recovery unverified")
    # Caller supplies a single completed directory; no recursive directory deletion.
    complete = json.loads((directory / "complete.json").read_text())
    removed = []
    for name, r in complete["checkpoints"].items():
        p = directory / name
        if p.parent != directory or p.suffix != ".pt":
            raise ValueError("Unsafe checkpoint path")
        if not p.exists():
            continue
        matches = [v for k, v in receipt["inventory"].items() if str(p).endswith("/" + k)]
        if len(matches) != 1 or matches[0]["sha256"] != r["sha256"] or sha(p) != r["sha256"]:
            raise ValueError("Recovery checkpoint differs")
        p.unlink()
        removed.append(name)
    return removed
