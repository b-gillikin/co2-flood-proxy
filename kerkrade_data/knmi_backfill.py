"""Resumable KNMI station-slim backfill for Azure Functions.

The KNMI open-data endpoint issues one temporary download URL per 10-minute
NetCDF file. A full 2020-to-present pull is therefore a long-running queue, not
one big download. This module keeps a small cursor blob in Azure Storage so a
timer-triggered function can safely pull a bounded batch each run.

By default raw all-station NetCDF files are temporary only. The persistent
landing zone keeps broad KNMI variables, but only for the selected Meuse/Maas
stations, written as compact monthly gzip CSV files.
"""

from __future__ import annotations

import gzip
import io
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

KDP_BASE_URL = "https://api.dataplatform.knmi.nl/open-data/v1"
DEFAULT_DATASET = "10-minute-in-situ-meteorological-observations"
DEFAULT_VERSION = "1.0"
FILENAME_PREFIX = "KMDS__OPER_P___10M_OBS_L2"
DEFAULT_CONTAINER = "knmi-data"
DEFAULT_RAW_PREFIX = "raw/10-minute-in-situ"
DEFAULT_SLIM_PREFIX = "slim/10-minute-in-situ"
DEFAULT_STATE_BLOB = "state/knmi_backfill_state.json"
DEFAULT_FORWARD_STATE_BLOB = "state/knmi_forward_state.json"
DEFAULT_STATIONS = "06380,06377,06392,06370,06375,06350,06356"
DEFAULT_DIRECTION = "forward"
DEFAULT_AVAILABILITY_LAG_MINUTES = 180


def parse_utc(value: str | None, default: datetime | None = None) -> datetime:
    """Parse an ISO-ish timestamp into a timezone-aware UTC datetime."""
    if not value:
        if default is None:
            raise ValueError("timestamp is required")
        return default
    cleaned = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def floor_10_minutes(ts: datetime) -> datetime:
    """Round a UTC timestamp down to the nearest KNMI 10-minute file boundary."""
    ts = ts.astimezone(timezone.utc).replace(second=0, microsecond=0)
    return ts.replace(minute=(ts.minute // 10) * 10)


def filename_for(ts: datetime) -> str:
    """Return the KNMI filename for one UTC 10-minute timestamp."""
    return f"{FILENAME_PREFIX}_{ts.strftime('%Y%m%d%H%M')}.nc"


def blob_name_for(filename: str, raw_prefix: str) -> str:
    """Build the raw-cache blob name for a KNMI file."""
    return f"{raw_prefix.strip('/')}/{filename}"


def slim_blob_name_for(ts: datetime, slim_prefix: str) -> str:
    """Build the monthly slim-table blob name for a UTC timestamp."""
    ts = ts.astimezone(timezone.utc)
    return (
        f"{slim_prefix.strip('/')}/"
        f"year={ts.year:04d}/month={ts.month:02d}/"
        f"knmi_meuse_10min_{ts.year:04d}_{ts.month:02d}.csv.gz"
    )


def parse_station_list(value: str | None) -> list[str]:
    """Parse comma-separated KNMI station IDs into zero-padded strings."""
    raw = value or DEFAULT_STATIONS
    stations = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        digits = "".join(char for char in token if char.isdigit())
        if len(digits) == 3:
            stations.append(f"06{digits}")
        elif len(digits) == 4:
            stations.append(digits.zfill(5))
        else:
            stations.append(digits or token)
    return stations


def normalize_direction(value: str | None) -> str:
    """Return a supported backfill direction."""
    direction = (value or DEFAULT_DIRECTION).strip().lower()
    if direction in {"backward", "reverse", "descending", "desc"}:
        return "backward"
    if direction in {"forward", "ascending", "asc"}:
        return "forward"
    raise ValueError("KNMI_BACKFILL_DIRECTION must be 'forward' or 'backward'")


def initial_cursor(start: datetime, end: datetime, direction: str) -> datetime:
    """Return the first timestamp cursor for the requested direction."""
    return floor_10_minutes(end if direction == "backward" else start)


def cursor_in_bounds(cursor: datetime, start: datetime, end: datetime, direction: str) -> bool:
    """Return whether the cursor remains inside the configured date window."""
    return cursor >= start if direction == "backward" else cursor <= end


def advance_cursor(cursor: datetime, direction: str) -> datetime:
    """Move the cursor by one KNMI 10-minute file interval."""
    step = -10 if direction == "backward" else 10
    return cursor + timedelta(minutes=step)


def default_state_blob(direction: str) -> str:
    """Keep historical-backfill and forward-maintenance cursors independent."""
    if normalize_direction(direction) == "forward":
        return DEFAULT_FORWARD_STATE_BLOB
    return DEFAULT_STATE_BLOB


def availability_end(now: datetime, direction: str, lag_minutes: float) -> datetime:
    """Return a safe collection end, allowing time for new KNMI files to publish."""
    if lag_minutes < 0:
        raise ValueError("KNMI_AVAILABILITY_LAG_MINUTES must be non-negative")
    if normalize_direction(direction) == "forward":
        return now - timedelta(minutes=lag_minutes)
    return now


def new_state(start: datetime, end: datetime, direction: str) -> dict:
    """Initialize a fresh resumable backfill state."""
    return {
        "direction": direction,
        "next_timestamp_utc": initial_cursor(start, end, direction).isoformat(),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "runs": 0,
        "attempted_files": 0,
        "downloaded_files": 0,
        "cached_files": 0,
        "not_found_files": 0,
        "failed_files": 0,
    }


def load_state(container, state_blob: str, start: datetime, end: datetime, direction: str) -> dict:
    """Read the cursor state blob, or initialize a new backfill state."""
    from azure.core.exceptions import ResourceNotFoundError

    try:
        payload = container.download_blob(state_blob).readall()
    except ResourceNotFoundError:
        return new_state(start, end, direction)

    state = json.loads(payload.decode("utf-8"))
    if state.get("direction") != direction:
        state = new_state(start, end, direction)
        state["reset_reason"] = f"direction changed to {direction}"
    return state


def save_state(container, state_blob: str, state: dict) -> None:
    """Write the cursor state blob."""
    from azure.storage.blob import ContentSettings

    state["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    container.upload_blob(
        state_blob,
        json.dumps(state, indent=2, sort_keys=True).encode("utf-8"),
        overwrite=True,
        content_settings=ContentSettings(content_type="application/json"),
    )


def temporary_download_url(api_key: str, dataset: str, version: str, filename: str) -> str | None:
    """Request a temporary KNMI download URL for one filename."""
    response = requests.get(
        f"{KDP_BASE_URL}/datasets/{dataset}/versions/{version}/files/{filename}/url",
        headers={"Authorization": api_key},
        timeout=60,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()["temporaryDownloadUrl"]


def download_bytes(url: str) -> bytes:
    """Download one KNMI file into memory for direct blob upload."""
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    return response.content


def extract_station_rows(content: bytes, filename: str, stations: list[str]):
    """Extract broad station-filtered rows from one KNMI NetCDF payload."""
    import pandas as pd
    import xarray as xr

    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as handle:
        handle.write(content)
        temp_path = Path(handle.name)

    try:
        with xr.open_dataset(temp_path) as dataset:
            available = {str(value) for value in dataset["station"].values}
            selected = [station for station in stations if station in available]
            if not selected:
                return pd.DataFrame()

            slim = dataset.sel(station=selected)
            frame = slim.to_dataframe().reset_index()
    finally:
        temp_path.unlink(missing_ok=True)

    frame = frame.rename(columns={"time": "timestamp_utc", "station": "knmi_station"})
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame["knmi_station"] = frame["knmi_station"].astype(str)
    frame["knmi_source_file"] = filename

    first_columns = ["timestamp_utc", "knmi_station", "knmi_source_file"]
    other_columns = [column for column in frame.columns if column not in first_columns]
    return frame[first_columns + other_columns]


def frame_to_gzip_csv(frame) -> bytes:
    """Serialize a dataframe as gzip-compressed CSV bytes."""
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=6) as gz:
        frame.to_csv(gz, index=False)
    return buffer.getvalue()


def read_existing_slim_blob(container, blob_name: str):
    """Read an existing monthly slim blob, returning an empty frame if absent."""
    import pandas as pd
    from azure.core.exceptions import ResourceNotFoundError

    try:
        payload = container.download_blob(blob_name).readall()
    except ResourceNotFoundError:
        return pd.DataFrame()
    compression = "gzip" if payload[:2] == b"\x1f\x8b" else None
    return pd.read_csv(io.BytesIO(payload), compression=compression)


def upload_monthly_slim_frames(container, frames: list, slim_prefix: str) -> tuple[int, int]:
    """Append/dedupe slim station rows into monthly gzip CSV blobs."""
    import pandas as pd
    from azure.storage.blob import ContentSettings

    if not frames:
        return 0, 0

    batch = pd.concat(frames, ignore_index=True)
    batch["timestamp_utc"] = pd.to_datetime(batch["timestamp_utc"], utc=True)
    written_blobs = 0
    written_rows = 0

    for _period, group in batch.groupby(batch["timestamp_utc"].dt.to_period("M")):
        ts = group["timestamp_utc"].iloc[0].to_pydatetime()
        blob_name = slim_blob_name_for(ts, slim_prefix)
        existing = read_existing_slim_blob(container, blob_name)
        combined = pd.concat([existing, group], ignore_index=True)
        combined["timestamp_utc"] = pd.to_datetime(combined["timestamp_utc"], utc=True)
        combined = combined.drop_duplicates(
            ["timestamp_utc", "knmi_station"], keep="last"
        ).sort_values(["timestamp_utc", "knmi_station"])
        payload = frame_to_gzip_csv(combined)
        container.upload_blob(
            blob_name,
            payload,
            overwrite=True,
            content_settings=ContentSettings(
                content_type="text/csv",
                content_encoding="gzip",
            ),
        )
        written_blobs += 1
        written_rows += len(combined)

    return written_blobs, written_rows


def should_keep_raw() -> bool:
    """Return whether the Azure collector should persist raw NetCDF files."""
    return os.getenv("KNMI_KEEP_RAW", "false").strip().lower() in {"1", "true", "yes"}


def run_backfill_once() -> dict:
    """Download one bounded KNMI batch and return a concise run summary."""
    from azure.storage.blob import BlobServiceClient, ContentSettings

    api_key = os.getenv("KNMI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("KNMI_API_KEY app setting is required.")

    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "").strip()
    if not connection_string:
        connection_string = os.getenv("AzureWebJobsStorage", "").strip()
    if not connection_string:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING or AzureWebJobsStorage is required.")

    container_name = os.getenv("KNMI_CONTAINER", DEFAULT_CONTAINER).strip() or DEFAULT_CONTAINER
    dataset = os.getenv("KNMI_DATASET", DEFAULT_DATASET).strip() or DEFAULT_DATASET
    version = os.getenv("KNMI_VERSION", DEFAULT_VERSION).strip() or DEFAULT_VERSION
    raw_prefix = os.getenv("KNMI_RAW_PREFIX", DEFAULT_RAW_PREFIX).strip() or DEFAULT_RAW_PREFIX
    slim_prefix = os.getenv("KNMI_SLIM_PREFIX", DEFAULT_SLIM_PREFIX).strip() or DEFAULT_SLIM_PREFIX
    stations = parse_station_list(os.getenv("KNMI_STATIONS", DEFAULT_STATIONS))
    start = parse_utc(os.getenv("KNMI_START", "2020-01-01T00:00:00Z"))
    direction = normalize_direction(os.getenv("KNMI_BACKFILL_DIRECTION", DEFAULT_DIRECTION))
    state_blob = os.getenv("KNMI_STATE_BLOB", "").strip() or default_state_blob(direction)
    availability_lag_minutes = float(
        os.getenv("KNMI_AVAILABILITY_LAG_MINUTES", str(DEFAULT_AVAILABILITY_LAG_MINUTES))
    )
    requested_end = parse_utc(os.getenv("KNMI_END"), default=datetime.now(timezone.utc))
    end = floor_10_minutes(availability_end(requested_end, direction, availability_lag_minutes))
    max_downloads = int(os.getenv("KNMI_MAX_DOWNLOADS_PER_RUN", "10"))
    sleep_seconds = float(os.getenv("KNMI_DOWNLOAD_SLEEP_SECONDS", "0.0"))

    service = BlobServiceClient.from_connection_string(connection_string)
    container = service.get_container_client(container_name)
    if not container.exists():
        container.create_container()

    state = load_state(container, state_blob, start, end, direction)
    cursor = floor_10_minutes(parse_utc(state.get("next_timestamp_utc"), default=start))

    summary = {
        "planned": 0,
        "downloaded": 0,
        "raw_uploaded": 0,
        "not_found": 0,
        "failed": 0,
        "slim_rows_extracted": 0,
        "slim_blobs_written": 0,
        "slim_rows_in_written_blobs": 0,
        "direction": direction,
        "availability_lag_minutes": availability_lag_minutes,
        "stations": ",".join(stations),
        "start_cursor_utc": cursor.isoformat(),
        "start_limit_utc": start.isoformat(),
        "end_limit_utc": end.isoformat(),
    }

    if not cursor_in_bounds(cursor, start, end, direction):
        state["complete_through_utc"] = (
            end.isoformat() if direction == "forward" else start.isoformat()
        )
        save_state(container, state_blob, state)
        summary["complete"] = True
        return summary

    state["last_run_status"] = "running"
    state["last_run_started_at_utc"] = datetime.now(timezone.utc).isoformat()
    state["last_run_summary"] = summary
    save_state(container, state_blob, state)

    attempted = 0
    slim_frames = []
    keep_raw = should_keep_raw()
    while attempted < max_downloads and cursor_in_bounds(cursor, start, end, direction):
        filename = filename_for(cursor)
        summary["planned"] += 1
        attempted += 1

        try:
            url = temporary_download_url(api_key, dataset, version, filename)
            if url is None:
                summary["not_found"] += 1
            else:
                content = download_bytes(url)
                summary["downloaded"] += 1

                if keep_raw:
                    blob_name = blob_name_for(filename, raw_prefix)
                    blob = container.get_blob_client(blob_name)
                    if not blob.exists():
                        blob.upload_blob(
                            content,
                            overwrite=False,
                            content_settings=ContentSettings(content_type="application/x-netcdf"),
                        )
                        summary["raw_uploaded"] += 1

                station_rows = extract_station_rows(content, filename, stations)
                if not station_rows.empty:
                    summary["slim_rows_extracted"] += len(station_rows)
                    slim_frames.append(station_rows)
        except Exception:
            summary["failed"] += 1
            logging.exception("KNMI file failed: %s", filename)

        cursor = advance_cursor(cursor, direction)
        state["in_run_next_candidate_utc"] = cursor.isoformat()
        state["last_run_summary"] = summary
        save_state(container, state_blob, state)
        if sleep_seconds and attempted < max_downloads:
            time.sleep(sleep_seconds)

    slim_blob_count, slim_row_count = upload_monthly_slim_frames(
        container,
        slim_frames,
        slim_prefix,
    )
    summary["slim_blobs_written"] = slim_blob_count
    summary["slim_rows_in_written_blobs"] = slim_row_count

    state["next_timestamp_utc"] = cursor.isoformat()
    state["runs"] = int(state.get("runs", 0)) + 1
    state["attempted_files"] = int(state.get("attempted_files", 0)) + summary["planned"]
    state["downloaded_files"] = int(state.get("downloaded_files", 0)) + summary["downloaded"]
    state["raw_uploaded_files"] = int(state.get("raw_uploaded_files", 0)) + summary["raw_uploaded"]
    state["slim_rows_extracted"] = (
        int(state.get("slim_rows_extracted", 0)) + summary["slim_rows_extracted"]
    )
    state["not_found_files"] = int(state.get("not_found_files", 0)) + summary["not_found"]
    state["failed_files"] = int(state.get("failed_files", 0)) + summary["failed"]
    state["last_run_summary"] = summary
    state["last_run_status"] = "complete"
    state["last_run_completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_state(container, state_blob, state)

    summary["next_timestamp_utc"] = cursor.isoformat()
    summary["state_blob"] = state_blob
    summary["container"] = container_name
    return summary
