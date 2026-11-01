"""Download the complete public hand-labeled task set with source MD5 checks.

One canonical dataset for all supported tasks. No labels are invented, no raster
values transformed, and no model is run. Resume verifies existing source bytes.
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/reviews/applied-task-config-2026-10-31"
BASE = ROOT / "data/raw/limburg_applied_tasks/sen1floods11"
OUT = ROOT / "results/applied_study_v1/acquisition"


def hashes(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            md5.update(block)
            sha.update(block)
    return base64.b64encode(md5.digest()).decode(), sha.hexdigest()


def get(item):
    name = Path(item["name"])
    folder, filename = name.parts[-2:]
    if folder not in {"LabelHand", "S1Hand", "S2Hand", "JRCWaterHand"} or name.suffix != ".tif":
        raise ValueError("Unexpected source object")
    target = BASE / folder / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        while shutil.disk_usage(ROOT).free < 52 * 1024**3:
            time.sleep(10)
        tmp = target.with_suffix(".partial")
        for attempt in range(4):
            try:
                request = urllib.request.Request(
                    "https://storage.googleapis.com/sen1floods11/" + item["name"]
                )
                with (
                    urllib.request.urlopen(request, timeout=120) as source,
                    tmp.open("wb") as stream,
                ):
                    shutil.copyfileobj(source, stream, length=1024**2)
                md5, digest = hashes(tmp)
                if tmp.stat().st_size != int(item["size"]) or md5 != item["md5Hash"]:
                    raise ValueError("Source size/MD5 mismatch")
                tmp.replace(target)
                break
            except Exception:
                tmp.unlink(missing_ok=True)
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
    md5, digest = hashes(target)
    if target.stat().st_size != int(item["size"]) or md5 != item["md5Hash"]:
        raise ValueError("Existing source conflicts: " + str(target))
    return dict(
        path=str(target.relative_to(ROOT)),
        source_object=item["name"],
        bytes=int(item["size"]),
        md5=md5,
        sha256=digest,
    )


def main():
    import fcntl

    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / ".sen1.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    items = []
    for folder in ["LabelHand", "S1Hand", "S2Hand", "JRCWaterHand"]:
        items += json.loads((EVIDENCE / f"sen1floods11-{folder}-objects.json").read_text())["items"]
    state = dict(status="running", planned_files=len(items), verified_files=0, bytes=0, failures=[])

    def save():
        state.update(updated_unix=time.time(), free_gib=shutil.disk_usage(ROOT).free / 1024**3)
        tmp = OUT / "sen1-progress.partial"
        tmp.write_text(json.dumps(state, indent=2) + "\n")
        tmp.replace(OUT / "sen1-progress.json")

    save()
    with (OUT / "sen1-files.jsonl").open("w") as ledger, ThreadPoolExecutor(max_workers=4) as pool:
        future_map = {pool.submit(get, item): item for item in items}
        for future in as_completed(future_map):
            try:
                row = future.result()
                ledger.write(json.dumps(row) + "\n")
                ledger.flush()
                state["verified_files"] += 1
                state["bytes"] += row["bytes"]
            except Exception as exc:
                state["failures"].append(
                    dict(object=future_map[future]["name"], error=f"{type(exc).__name__}: {exc}")
                )
            if (state["verified_files"] + len(state["failures"])) % 20 == 0:
                save()
                print(json.dumps(state), flush=True)
    state["status"] = "completed" if not state["failures"] else "incomplete"
    save()
    if state["failures"]:
        raise SystemExit("Failed objects retained in progress; rerun to retry")


if __name__ == "__main__":
    main()
