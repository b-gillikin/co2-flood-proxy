"""Timer-triggered, restart-safe ERA5-Land backfill to Azure Blob Storage."""

from __future__ import annotations

import io
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import azure.functions as func
import cdsapi
import pandas as pd
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContentSettings
from era5_common import (
    DATASET,
    MANIFEST_COLUMNS,
    blob_name,
    expected_periods,
    manifest_row,
    period_from_name,
    request_for_month,
    validate_netcdf,
)

STATE_BLOB = "_state.json"
MANIFEST_BLOB = "manifest.csv"
MAX_PERIOD_ATTEMPTS = 3


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def load_state(container):
    try:
        payload = container.download_blob(STATE_BLOB).readall()
    except ResourceNotFoundError:
        return {"active": None, "attempts": {}, "created_utc": now_utc()}
    return json.loads(payload)


def save_state(container, state):
    state["updated_utc"] = now_utc()
    container.upload_blob(
        STATE_BLOB,
        json.dumps(state, indent=2, sort_keys=True),
        overwrite=True,
        content_settings=ContentSettings(content_type="application/json"),
    )


def completed_periods(container):
    completed = set()
    for blob in container.list_blobs(name_starts_with="source/"):
        period = period_from_name(blob.name)
        if period is not None:
            completed.add(period)
    return completed


def next_missing_period(container):
    completed = completed_periods(container)
    return next((period for period in expected_periods() if period not in completed), None)


def cds_client():
    """Use short HTTP retries; later timer invocations provide durable retry."""
    return cdsapi.Client(
        url=os.environ["CDSAPI_URL"],
        key=os.environ["CDSAPI_KEY"],
        wait_until_complete=False,
        delete=False,
        quiet=True,
        progress=False,
        retry_max=2,
        sleep_max=5,
        timeout=30,
    )


def append_manifest(container, row):
    try:
        existing = pd.read_csv(io.BytesIO(container.download_blob(MANIFEST_BLOB).readall()))
    except ResourceNotFoundError:
        existing = pd.DataFrame(columns=MANIFEST_COLUMNS)

    updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
    updated = (
        updated.drop_duplicates(["year", "month"], keep="last")
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )
    container.upload_blob(
        MANIFEST_BLOB,
        updated.to_csv(index=False),
        overwrite=True,
        content_settings=ContentSettings(content_type="text/csv"),
    )


def submit_next(container, state):
    period = next_missing_period(container)
    if period is None:
        state["completed_utc"] = now_utc()
        save_state(container, state)
        logging.info("ERA5-Land backfill complete: all %d months present", len(expected_periods()))
        return

    year, month = period
    remote = cds_client().retrieve(DATASET, request_for_month(year, month))
    state["active"] = {
        "year": year,
        "month": month,
        "request_id": remote.request_id,
        "submitted_utc": now_utc(),
    }
    save_state(container, state)
    logging.info("Submitted ERA5-Land %04d-%02d as %s", year, month, remote.request_id)


def record_failure(container, state, status, message):
    active = state["active"]
    key = f"{active['year']:04d}-{active['month']:02d}"
    attempts = state.setdefault("attempts", {})
    attempts[key] = int(attempts.get(key, 0)) + 1
    state["last_error"] = {"period": key, "status": status, "message": message}
    state["active"] = None
    if attempts[key] >= MAX_PERIOD_ATTEMPTS:
        state["blocked"] = state["last_error"]
    save_state(container, state)
    logging.error("ERA5-Land %s failed (%s), attempt %d", key, status, attempts[key])


def finish_active(container, state, remote):
    active = state["active"]
    year, month = active["year"], active["month"]
    target_blob = blob_name(year, month)

    with tempfile.TemporaryDirectory(prefix="era5_") as temp_dir:
        path = Path(temp_dir) / Path(target_blob).name
        remote.download(str(path))
        validate_netcdf(path, year, month)
        row = manifest_row(path, year, month, target_blob)
        with path.open("rb") as source:
            container.upload_blob(
                target_blob,
                source,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/x-netcdf"),
            )
        append_manifest(container, row)

    state["active"] = None
    state.setdefault("attempts", {}).pop(f"{year:04d}-{month:02d}", None)
    state["last_completed"] = {"year": year, "month": month, "completed_utc": now_utc()}
    save_state(container, state)
    logging.info("Validated and uploaded ERA5-Land %04d-%02d", year, month)


def record_finish_error(container, state, message):
    active = state["active"]
    attempts = int(active.get("finish_attempts", 0)) + 1
    active["finish_attempts"] = attempts
    state["last_error"] = {
        "period": f"{active['year']:04d}-{active['month']:02d}",
        "status": "download_or_validation_failed",
        "message": message,
    }
    if attempts >= MAX_PERIOD_ATTEMPTS:
        state["blocked"] = state["last_error"]
    save_state(container, state)


def main(timer: func.TimerRequest) -> None:
    if os.getenv("ERA5_ENABLED", "false").lower() != "true":
        logging.info("ERA5-Land backfill is paused")
        return

    service = BlobServiceClient.from_connection_string(
        os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    )
    container = service.get_container_client(os.environ.get("ERA5_CONTAINER", "era5-land"))
    try:
        container.create_container()
    except ResourceExistsError:
        pass

    state = load_state(container)
    if state.get("blocked"):
        logging.error("ERA5-Land backfill is blocked: %s", state["blocked"])
        return

    active = state.get("active")
    if not active:
        submit_next(container, state)
        return

    try:
        client = cds_client()
        remote = client.client.get_remote(active["request_id"])
        status = remote.status
    except Exception:
        logging.exception("Could not poll ERA5-Land request %s", active["request_id"])
        return

    state["active"]["last_status"] = status
    state["active"]["last_polled_utc"] = now_utc()
    save_state(container, state)

    if status in {"accepted", "queued", "running"}:
        logging.info("ERA5-Land %04d-%02d remains %s", active["year"], active["month"], status)
        return
    if status in {"failed", "rejected", "dismissed", "deleted"}:
        record_failure(container, state, status, f"CDS request {active['request_id']}")
        return
    if status != "successful":
        record_failure(container, state, status, "unknown CDS status")
        return

    try:
        finish_active(container, state, remote)
    except Exception as error:
        logging.exception(
            "Could not download/validate ERA5-Land %04d-%02d", active["year"], active["month"]
        )
        record_finish_error(container, state, str(error))
