#!/usr/bin/env python3
"""Restore two verified archives at a time, score maps, retain compact classes."""

from __future__ import annotations

import argparse
import fcntl
import json
import shutil
import subprocess
import sys
import tarfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import OUT, atomic_json, score_prediction, sha256

EXTERNAL = ROOT / "results/limburg_chapter_sized_v1/external"
PRINT_LOCK = threading.Lock()


def score_archive(ledger_path):
    ledger = json.loads(ledger_path.read_text())
    digest = ledger["sha256"]
    target = OUT / "archive_scores" / f"{digest}.parquet"
    finish = target.with_suffix(".complete.json")
    support_hash = sha256(OUT / "support/manifest.json")
    if finish.exists():
        record = json.loads(finish.read_text())
        if record["support_manifest_sha256"] != support_hash or record["score_sha256"] != sha256(
            target
        ):
            raise ValueError("Completed scores differ from support specification/output hash")
        return {"status": "reused", "archive": digest, "predictions": record["predictions"]}
    cache = OUT / "restore_work"
    cache.mkdir(parents=True, exist_ok=True)
    bundle = cache / f"{digest}.tar"
    partial = bundle.with_suffix(".partial.tar")
    if not bundle.exists():
        if shutil.disk_usage(ROOT).free < 50 * 1024**3 + ledger["archive_bytes"] + 1024**3:
            raise RuntimeError("Restoration would breach 50 GiB disk reserve")
        command = [
            "az",
            "storage",
            "blob",
            "download",
            "--account-name",
            ledger["account"],
            "--container-name",
            ledger["container"],
            "--auth-mode",
            "login",
            "--name",
            ledger["blob"],
            "--file",
            str(partial),
            "--overwrite",
            "true",
            "--only-show-errors",
            "--output",
            "none",
            "--max-connections",
            "4",
        ]
        for attempt in range(1, 4):
            started = time.time()
            result = subprocess.run(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=3600
            )
            if (
                result.returncode == 0
                and partial.stat().st_size == ledger["archive_bytes"]
                and sha256(partial) == digest
            ):
                partial.replace(bundle)
                break
            partial.unlink(missing_ok=True)
            with PRINT_LOCK:
                print(
                    json.dumps(
                        {
                            "status": "retry_restore",
                            "archive": digest,
                            "attempt": attempt,
                            "exit_code": result.returncode,
                            "elapsed_s": round(time.time() - started),
                        }
                    ),
                    flush=True,
                )
            if attempt == 3:
                raise RuntimeError(f"Unable to restore verified archive {digest}")
            time.sleep(10)
    if bundle.stat().st_size != ledger["archive_bytes"] or sha256(bundle) != digest:
        raise ValueError(f"Restored archive hash differs: {digest}")
    rows = []
    compact = {}
    with tarfile.open(bundle, "r:") as tar:
        entries = {entry.name: entry for entry in tar if entry.isfile()}
        expected_names = set(ledger["members"]) | set(ledger["receipt_sha256"])
        if set(entries) != expected_names:
            raise ValueError("Archive members differ from verified ledger")
        for name in sorted(ledger["members"]):
            parts = Path(name).parts
            _, kind, dataset, event, filename = parts
            stem = Path(filename).stem
            key, reference, seed_text = stem.rsplit("-", 2)
            if key.split("-")[0] != event:
                raise ValueError("Archive event/path mismatch")
            with (
                tar.extractfile(entries[name]) as stream,
                np.load(stream, allow_pickle=False) as data,
            ):
                prediction, valid = data["prediction"], data["radar_valid"]
            rows.extend(
                score_prediction(key, dataset, reference, kind, int(seed_text), prediction, valid)
            )
            compact_target = OUT / "compact" / name
            compact_target.parent.mkdir(parents=True, exist_ok=True)
            compact_partial = compact_target.with_suffix(".partial.npz")
            np.savez_compressed(compact_partial, prediction=prediction, radar_valid=valid)
            compact_partial.replace(compact_target)
            compact[name] = sha256(compact_target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".partial.parquet")
    pd.DataFrame(rows).to_parquet(temporary, index=False)
    temporary.replace(target)
    atomic_json(
        finish,
        {
            "status": "archive_scored",
            "archive_sha256": digest,
            "support_manifest_sha256": support_hash,
            "score_sha256": sha256(target),
            "runner_sha256": sha256(Path(__file__)),
            "evaluation_code_sha256": sha256(ROOT / "src/limburg_chapter_evaluation.py"),
            "predictions": len(compact),
            "rows": len(rows),
            "compact_sha256": compact,
            "completed_unix": time.time(),
        },
    )
    bundle.unlink()
    return {"status": "scored", "archive": digest, "predictions": len(compact), "rows": len(rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, choices=[1, 2], default=2)
    parser.add_argument(
        "--limit", type=int, help="Engineering batch only; final census requires no limit"
    )
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / ".archive-scoring.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    support = json.loads((OUT / "support/complete.json").read_text())
    if support["status"] != "support_census_complete" or support["tiles"] != 1301:
        raise ValueError("Incomplete support census")
    ledgers = sorted(
        (EXTERNAL / "archives").glob("*.json"),
        key=lambda path: (json.loads(path.read_text())["archive_bytes"], path.name),
    )
    if len(ledgers) != 46:
        raise ValueError("Archive census differs")
    if args.limit is not None:
        ledgers = ledgers[: args.limit]
    predictions = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(score_archive, path): path for path in ledgers}
        for completed, future in enumerate(as_completed(futures), 1):
            result = future.result()
            predictions += result["predictions"]
            state = {
                **result,
                "archives_complete": completed,
                "archives_total": len(ledgers),
                "predictions_complete": predictions,
                "free_gib": round(shutil.disk_usage(ROOT).free / 1024**3, 2),
            }
            atomic_json(OUT / "archive_scoring_status.json", state)
            print(json.dumps(state), flush=True)
    if args.limit is None:
        if predictions != 18762:
            raise ValueError("Scored prediction census differs")
        atomic_json(
            OUT / "archives-complete.json",
            {
                "status": "full_learned_scoring_complete",
                "archives": len(ledgers),
                "predictions": predictions,
                "completed_unix": time.time(),
            },
        )


if __name__ == "__main__":
    main()
