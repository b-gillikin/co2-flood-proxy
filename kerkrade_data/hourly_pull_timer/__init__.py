import hashlib
import logging
import os
from datetime import date, timedelta
from pathlib import Path

import azure.functions as func

import hourly_pull


SYNC_DIR = Path("/tmp/hourly_data_sync")
DEFAULT_CONTAINER = "kerkrada-weather-data"
DEFAULT_LOCATION = "Kerkrade"


def _get_blob_client():
    from azure.storage.blob import BlobServiceClient

    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "").strip()
    if not conn_str:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING is required.")
    return BlobServiceClient.from_connection_string(conn_str)


def _month_blob_name(location: str, year: int, month: int) -> str:
    loc = hourly_pull.safe_location_name(location)
    return f"weather_{loc}_{year:04d}-{month:02d}.csv"


def _target_month_blobs(location: str, lookback_days: int) -> list[str]:
    today = date.today()
    months = set()
    for offset in range(lookback_days + 1):
        d = today - timedelta(days=offset)
        months.add((d.year, d.month))
    return sorted(_month_blob_name(location, y, m) for (y, m) in months)


def _sync_down_target_files(container_name: str, blob_names: list[str]) -> None:
    if SYNC_DIR.exists():
        for p in SYNC_DIR.rglob("*"):
            if p.is_file():
                p.unlink()
    SYNC_DIR.mkdir(parents=True, exist_ok=True)

    svc = _get_blob_client()
    container = svc.get_container_client(container_name)
    if not container.exists():
        try:
            container.create_container()
        except Exception:
            pass

    for name in blob_names:
        destination = SYNC_DIR / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(destination, "wb") as f:
                f.write(container.download_blob(name).readall())
        except Exception:
            continue


def _sync_up(container_name: str) -> list[str]:
    svc = _get_blob_client()
    container = svc.get_container_client(container_name)
    if not container.exists():
        try:
            container.create_container()
        except Exception:
            pass

    uploaded_blobs: list[str] = []

    for file_path in SYNC_DIR.rglob("*"):
        if not file_path.is_file():
            continue
        blob_name = str(file_path.relative_to(SYNC_DIR))
        blob = container.get_blob_client(blob_name)

        local_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                local_hash.update(chunk)
        local_digest = local_hash.digest()

        same_content = False
        try:
            remote_hash = hashlib.md5()
            for chunk in blob.download_blob().chunks():
                remote_hash.update(chunk)
            same_content = remote_hash.digest() == local_digest
        except Exception:
            same_content = False

        if same_content:
            continue

        with open(file_path, "rb") as data:
            container.upload_blob(name=blob_name, data=data, overwrite=True)
        uploaded_blobs.append(blob_name)

    return uploaded_blobs


def main(timer: func.TimerRequest) -> None:
    container = os.getenv("HOURLY_DATA_CONTAINER", DEFAULT_CONTAINER).strip() or DEFAULT_CONTAINER
    location = os.getenv("HOURLY_LOCATION", DEFAULT_LOCATION).strip() or DEFAULT_LOCATION
    lookback_days = int(os.getenv("HOURLY_LOOKBACK_DAYS", "1"))

    target_blobs = _target_month_blobs(location, lookback_days)
    logging.info(
        "Hourly weather pull fired. container=%s location=%s target_blobs=%s",
        container,
        location,
        ", ".join(target_blobs),
    )

    _sync_down_target_files(container, target_blobs)

    os.environ["SAVE_FOLDER"] = str(SYNC_DIR)
    os.environ["LOCATION"] = location
    os.environ["HOURLY_LOOKBACK_DAYS"] = str(lookback_days)
    try:
        hourly_pull.main()
    except RuntimeError as exc:
        message = str(exc)
        # Keep timer healthy if API has no currently observed row for this window,
        # or if the key is temporarily out of daily budget.
        if "No observed hourly rows returned by API" in message:
            logging.info("No observed hourly row available for this run; skipping upload.")
            return
        if "HTTP 429" in message or "Maximum daily cost exceeded" in message:
            logging.warning("Hourly API budget hit (429). Skipping this run.")
            return
        raise

    uploaded = _sync_up(container)
    logging.info(
        "Hourly weather pull complete. uploaded=%s container=%s location=%s",
        len(uploaded),
        container,
        location,
    )
