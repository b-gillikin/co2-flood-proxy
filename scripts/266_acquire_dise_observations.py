"""Two resumable workers acquire selected CAMELS members and audit daily labels.

Geometry flags stay attached. Acquisition does not approve a model mapping.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.dise import daily_hour_end, specific_q
from src.dise_acquisition import HTTPRangeFile
from src.geoglows_experiment import disk_check, sha, write_json

PLAN = json.loads((ROOT / "config/limburg_dise_v2.json").read_text())
OUT = ROOT / PLAN["output"]
RAW = ROOT / "data/raw/limburg_dise_v2/camels_timeseries"
DAILY = OUT / "regional_observations"


def one(archive, row, etag):
    gauge = row.gauge_id
    member = next(n for n in archive.namelist() if n.endswith(f"timeseries_{gauge}.csv"))
    info = archive.getinfo(member)
    source = RAW / f"{gauge}.csv.gz"
    receipt = source.with_suffix(".gz.receipt.json")
    identity = dict(url=PLAN["camels_archive"], etag=etag, member=member, crc32=info.CRC)
    if source.exists():
        old = json.loads(receipt.read_text())
        if old["identity"] != identity or old["sha256"] != sha(source):
            raise ValueError("Changed retained source member")
    else:
        disk_check(ROOT, PLAN["reserve_gib"], info.file_size)
        digest = hashlib.sha256()
        partial = source.with_suffix(".gz.partial")
        with archive.open(member) as inp, gzip.open(partial, "wb", compresslevel=1) as dest:
            while chunk := inp.read(1024**2):
                disk_check(ROOT, PLAN["reserve_gib"], len(chunk))
                digest.update(chunk)
                dest.write(chunk)
        partial.replace(source)
        write_json(
            receipt,
            dict(
                identity=identity,
                sha256=sha(source),
                uncompressed_sha256=digest.hexdigest(),
                uncompressed_bytes=info.file_size,
                compressed_bytes=source.stat().st_size,
            ),
        )
    frame = pd.read_csv(source, usecols=["date", "discharge_vol_obs"])
    frame["date"] = pd.to_datetime(frame.date, utc=True)  # source already UTC; no second CET shift
    q = frame.set_index("date").discharge_vol_obs
    negatives = int(q.lt(0).sum())
    daily, count = daily_hour_end(q.to_frame())
    maximum = q.where(q.ge(0)).copy()
    maximum.index -= pd.Timedelta(hours=1)
    maximum = maximum.resample("D").max()
    d = pd.DataFrame(
        dict(
            day=daily.index,
            q_observed_m3s=daily.iloc[:, 0].to_numpy(),
            observed_hours=count.iloc[:, 0].to_numpy(),
            hourly_max_m3s=maximum.reindex(daily.index).to_numpy(),
        )
    )
    d["q_observed"] = specific_q(d.q_observed_m3s, row.reference_area_km2)
    d["gauge"] = gauge
    d["river_group"] = (
        row.external_group if row.resolved_role == "reserved_external" else row.topology_group
    )
    d["source_role"] = row.resolved_role
    d["geometry_review_flag"] = row.geometry_review_flag
    d["clean_verification"] = pd.Series(pd.NA, index=d.index, dtype="boolean")
    d["source_quality"] = "provider-dependent; no row-level flags in this export"
    path = DAILY / f"{gauge}.parquet"
    d.to_parquet(path, index=False)
    report = dict(
        gauge=gauge,
        source_sha256=sha(source),
        daily_sha256=sha(path),
        rows=len(frame),
        first=str(frame.date.min()),
        last=str(frame.date.max()),
        negative_source_values=negatives,
        complete_days=int(d.q_observed.notna().sum()),
        days=len(d),
        complete_days_2018_2024=int(
            d.loc[d.day.dt.year.between(2018, 2024), "q_observed"].notna().sum()
        ),
        role=row.resolved_role,
        geometry_review_flag=bool(row.geometry_review_flag),
        quality="unknown/mixed provider QA, not inferred from finite values",
        boundary="UTC hour end; incomplete terminal day stays missing",
    )
    write_json(path.with_suffix(".parquet.receipt.json"), report)
    return report


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    DAILY.mkdir(parents=True, exist_ok=True)
    ledger = OUT / "regional_mapping_ledger.csv"
    data = pd.read_csv(ledger)
    chosen = data.loc[data.resolved_role.isin(["regional_donor", "reserved_external"])].sort_values(
        "gauge_id"
    )
    rows = list(chosen.itertuples(index=False))
    inventory = json.loads((ROOT / PLAN["raw"] / "camels/archive_inventory.json").read_text())
    compressed = sum(
        x["compressed_bytes"]
        for x in inventory["members"]
        if any(x["name"].endswith(f"timeseries_{r.gauge_id}.csv") for r in rows)
    )
    disk_check(ROOT, PLAN["reserve_gib"], int(compressed * 2))
    pinned = sha(ledger)
    completed, failed = [], []
    lock = threading.Lock()
    start = time.monotonic()

    def worker(batch):
        with HTTPRangeFile(PLAN["camels_archive"]) as remote:
            if remote.etag != inventory["etag"]:
                raise ValueError("Source ZIP changed since inventory")
            with zipfile.ZipFile(remote) as archive:
                for row in batch:
                    error = None
                    for attempt in range(3):
                        try:
                            record = one(archive, row, remote.etag)
                            error = None
                            break
                        except Exception as exc:
                            error = repr(exc)
                            if attempt < 2:
                                time.sleep(2**attempt)
                    with lock:
                        if error:
                            failed.append(dict(gauge=row.gauge_id, error=error))
                        else:
                            completed.append(record)
                        count = len(completed) + len(failed)
                        write_json(
                            OUT / "regional_acquisition_progress.json",
                            dict(
                                status="running",
                                completed=len(completed),
                                failed=failed,
                                total=len(rows),
                                percent=100 * count / len(rows),
                                seconds=time.monotonic() - start,
                                free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
                                workers=2,
                            ),
                        )
                        print(
                            f"{len(completed)}/{len(rows)} acquired; {len(failed)} failed",
                            flush=True,
                        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        for _ in pool.map(worker, [rows[::2], rows[1::2]]):
            pass
    if sha(ledger) != pinned:
        raise ValueError("Mapping ledger changed during acquisition")
    write_json(
        OUT / "regional_acquisition_receipt.json",
        dict(
            status="completed" if not failed else "completed_with_unresolved_transfers",
            source_etag=inventory["etag"],
            mapping_sha256=pinned,
            completed=completed,
            failed=failed,
            source_clock_verified="docs/reviews/limburg-dise-source-qa-2026-11-16.json",
            geometry_flags_do_not_approve_model_pairs=True,
        ),
    )
    write_json(
        OUT / "regional_acquisition_progress.json",
        dict(
            status="completed" if not failed else "completed_with_unresolved_transfers",
            completed=len(completed),
            failed=failed,
            total=len(rows),
            percent=100,
            seconds=time.monotonic() - start,
        ),
    )


if __name__ == "__main__":
    main()
