import logging
import os
import shutil
import hashlib
import json
import csv
import re
from pathlib import Path
from datetime import datetime, timezone, date

import azure.functions as func
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.communication.email import EmailClient
from azure.storage.blob import BlobServiceClient

import monthly_pull

SYNC_DIR = Path('/tmp/monthly_data_sync')
DEFAULT_LOCATION_CONTAINER_PAIRS = [
    ('Kerkrade', 'kerkrada-weather-data'),
    ('Liege', 'liege-weather-data'),
    ('Maastricht', 'maastricht-weather-data'),
    ('Aachen', 'aachen-weather-data'),
    ('Cologne', 'cologne-weather-data'),
]


def _get_blob_client():
    conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '').strip()
    if not conn_str:
        raise RuntimeError('AZURE_STORAGE_CONNECTION_STRING is required.')
    return BlobServiceClient.from_connection_string(conn_str)


def _sync_down(container_name: str) -> None:
    if SYNC_DIR.exists():
        shutil.rmtree(SYNC_DIR)
    SYNC_DIR.mkdir(parents=True, exist_ok=True)

    svc = _get_blob_client()
    container = svc.get_container_client(container_name)
    if not container.exists():
        try:
            container.create_container()
        except ResourceExistsError:
            pass

    for blob in container.list_blobs():
        destination = SYNC_DIR / blob.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, 'wb') as f:
            f.write(container.download_blob(blob.name).readall())


def _sync_up(container_name: str) -> list[str]:
    svc = _get_blob_client()
    container = svc.get_container_client(container_name)
    if not container.exists():
        try:
            container.create_container()
        except ResourceExistsError:
            pass

    uploaded = 0
    skipped = 0
    uploaded_blobs: list[str] = []

    for file_path in SYNC_DIR.rglob('*'):
        if not file_path.is_file():
            continue
        blob_name = str(file_path.relative_to(SYNC_DIR))
        blob = container.get_blob_client(blob_name)

        local_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                local_hash.update(chunk)
        local_digest = local_hash.digest()

        same_content = False
        try:
            remote_hash = hashlib.md5()
            for chunk in blob.download_blob().chunks():
                remote_hash.update(chunk)
            same_content = remote_hash.digest() == local_digest
        except ResourceNotFoundError:
            same_content = False

        if same_content:
            skipped += 1
            continue

        with open(file_path, 'rb') as data:
            container.upload_blob(name=blob_name, data=data, overwrite=True)
        uploaded += 1
        uploaded_blobs.append(blob_name)

    logging.info("Sync-up complete. uploaded=%s skipped=%s", uploaded, skipped)
    return uploaded_blobs


def _get_location_container_pairs() -> list[tuple[str, str]]:
    raw = os.getenv('LOCATION_CONTAINER_MAP', '').strip()
    if not raw:
        return DEFAULT_LOCATION_CONTAINER_PAIRS

    pairs: list[tuple[str, str]] = []
    for entry in raw.split(';'):
        item = entry.strip()
        if not item:
            continue
        if ':' not in item:
            raise RuntimeError(
                "Invalid LOCATION_CONTAINER_MAP format. Expected 'Location:container;Location2:container2'."
            )
        location, container = item.split(':', 1)
        location = location.strip()
        container = container.strip()
        if location and container:
            pairs.append((location, container))
    if not pairs:
        raise RuntimeError('LOCATION_CONTAINER_MAP resolved to an empty location/container list.')
    return pairs


def _months_remaining_in_sync_dir() -> int | None:
    state_path = SYNC_DIR / '.backfill_state.json'
    if not state_path.exists():
        return None
    try:
        with open(state_path, 'r') as f:
            state = json.load(f)
        value = state.get('months_remaining')
        return int(value) if value is not None else None
    except Exception as exc:
        logging.warning('Failed reading .backfill_state.json: %s', exc)
        return None


def _send_upload_email(container_name: str, uploaded_blobs: list[str]) -> None:
    conn = os.getenv('AZURE_COMMUNICATION_CONNECTION_STRING', '').strip()
    sender = os.getenv('ALERT_SENDER', '').strip()
    recipients_raw = os.getenv('ALERT_RECIPIENTS', '').strip()
    if not conn or not sender or not recipients_raw:
        logging.info('Email settings missing; skipping upload notification.')
        return

    recipients = [r.strip() for r in recipients_raw.split(',') if r.strip()]
    if not recipients:
        return

    preview = uploaded_blobs[:20]
    numbered = [f"{idx}. {name}" for idx, name in enumerate(preview, start=1)]
    suffix = '' if len(uploaded_blobs) <= 20 else f"\n...and {len(uploaded_blobs) - 20} more"
    iot_summary = _build_iot_summary()
    hourly_weather_summary = _build_hourly_weather_summary()

    body = (
        "### WEATHER DATA - HISTORICAL ###\n"
        f"Upload sync completed for container: {container_name}\n"
        f"Uploaded/updated blobs: {len(uploaded_blobs)}\n\n"
        + "\n".join(numbered)
        + suffix
    )
    if hourly_weather_summary:
        body += f"\n\n{hourly_weather_summary}"
    if iot_summary:
        body += f"\n\n{iot_summary}"

    message = {
        'senderAddress': sender,
        'content': {
            'subject': f'{container_name} update ({len(uploaded_blobs)} files)',
            'plainText': body,
        },
        'recipients': {'to': [{'address': r} for r in recipients]},
    }

    client = EmailClient.from_connection_string(conn)
    poller = client.begin_send(message)
    result = poller.result()
    logging.info('Timer upload email sent. Message ID: %s', result.get('id'))


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _blob_date_from_name(name: str, prefix: str) -> date | None:
    pattern = rf"^{re.escape(prefix)}_(\d{{4}}-\d{{2}}-\d{{2}})\.csv$"
    m = re.match(pattern, name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), '%Y-%m-%d').date()
    except ValueError:
        return None


def _download_csv_rows(container, blob_name: str) -> list[dict[str, str]]:
    data = container.download_blob(blob_name).readall().decode('utf-8', errors='replace')
    return list(csv.DictReader(data.splitlines()))


def _build_iot_summary() -> str:
    container_name = os.getenv('AIR_QUALITY_CONTAINER', 'air-quality-device-data-1').strip() or 'air-quality-device-data-1'
    prefix = os.getenv('AIR_QUALITY_BLOB_PREFIX', 'air_quality').strip() or 'air_quality'

    try:
        svc = _get_blob_client()
        container = svc.get_container_client(container_name)
        dated_blobs: list[tuple[date, str]] = []
        for b in container.list_blobs(name_starts_with=f'{prefix}_'):
            name = b.name
            if not name.endswith('.csv'):
                continue
            d = _blob_date_from_name(name, prefix)
            if d is not None:
                dated_blobs.append((d, name))

        if not dated_blobs:
            now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            return (
                "### AIR QUALITY DEVICE DATA ###\n"
                f"Container: {container_name}\n"
                "Most recent full day blob: (none)\n"
                "Most recent full day Number of rows: 0\n"
                "Most recent full day Avg Temperature: n/a\n"
                "Most recent full day Avg CO2: n/a\n\n"
                "Latest Temperature: n/a\n"
                "Latest CO2: n/a\n\n"
                f"Summary generated (UTC): {now_utc}"
            )

        dated_blobs.sort(key=lambda x: x[0])
        today_utc = datetime.now(timezone.utc).date()

        latest_blob_date, latest_blob_name = dated_blobs[-1]
        latest_rows = _download_csv_rows(container, latest_blob_name)
        latest_row = latest_rows[-1] if latest_rows else {}

        full_day_candidates = [(d, n) for (d, n) in dated_blobs if d < today_utc]
        if full_day_candidates:
            full_day_date, full_day_blob = full_day_candidates[-1]
        else:
            full_day_date, full_day_blob = latest_blob_date, latest_blob_name

        full_day_rows = _download_csv_rows(container, full_day_blob)
        if not full_day_rows:
            now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            return (
                "### AIR QUALITY DEVICE DATA ###\n"
                f"Container: {container_name}\n"
                f"Most recent full day blob: {full_day_blob}\n"
                "Most recent full day Number of rows: 0\n"
                "Most recent full day Avg Temperature: n/a\n"
                "Most recent full day Avg CO2: n/a\n\n"
                f"Latest Temperature: {latest_row.get('Temperature', 'n/a') if latest_row else 'n/a'}\n"
                f"Latest CO2: {latest_row.get('CO2', 'n/a') if latest_row else 'n/a'}\n\n"
                f"Summary generated (UTC): {now_utc}"
            )

        temp_vals = [_safe_float(r.get('Temperature')) for r in full_day_rows]
        temp_vals = [v for v in temp_vals if v is not None]
        co2_vals = [_safe_float(r.get('CO2')) for r in full_day_rows]
        co2_vals = [v for v in co2_vals if v is not None]

        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        avg_temp = round(sum(temp_vals) / len(temp_vals), 2) if temp_vals else 'n/a'
        avg_co2 = round(sum(co2_vals) / len(co2_vals), 2) if co2_vals else 'n/a'
        latest_temp = latest_row.get('Temperature', 'n/a') if latest_row else 'n/a'
        latest_co2 = latest_row.get('CO2', 'n/a') if latest_row else 'n/a'

        return (
            "### AIR QUALITY DEVICE DATA ###\n"
            f"Container: {container_name}\n"
            f"Most recent full day blob: {full_day_blob}\n"
            f"Most recent full day Number of rows: {len(full_day_rows)}\n"
            f"Most recent full day Avg Temperature: {avg_temp}\n"
            f"Most recent full day Avg CO2: {avg_co2}\n\n"
            f"Latest Temperature: {latest_temp}\n"
            f"Latest CO2: {latest_co2}\n\n"
            f"Summary generated (UTC): {now_utc}"
        )
    except Exception as exc:
        logging.warning('Failed to build IoT summary: %s', exc)
        return "IoT summary unavailable (read/parse failed)."


def _build_hourly_weather_summary() -> str:
    container_name = os.getenv('HOURLY_DATA_CONTAINER', 'kerkrada-weather-data').strip() or 'kerkrada-weather-data'
    location = os.getenv('HOURLY_LOCATION', 'Kerkrade').strip() or 'Kerkrade'
    today_utc = datetime.now(timezone.utc).date()
    month_blob = f"weather_{monthly_pull.safe_location_name(location)}_{today_utc:%Y-%m}.csv"

    try:
        svc = _get_blob_client()
        container = svc.get_container_client(container_name)
        rows = _download_csv_rows(container, month_blob)
        count_today = 0
        day_prefix = today_utc.isoformat()
        for r in rows:
            dt = (r.get('datetime') or '').strip()
            if dt.startswith(day_prefix):
                count_today += 1
        return (
            "### WEATHER DATA - HOURLY ###\n"
            f"Container: {container_name}\n"
            f"Number of Rows Uploaded: {count_today}"
        )
    except Exception as exc:
        logging.warning('Failed to build hourly weather summary: %s', exc)
        return (
            "### WEATHER DATA - HOURLY ###\n"
            f"Container: {container_name}\n"
            "Number of Rows Uploaded: n/a"
        )


def main(timer: func.TimerRequest) -> None:
    pairs = _get_location_container_pairs()
    logging.info("Timer fired. Evaluating %s location/container pairs.", len(pairs))

    for location, container in pairs:
        logging.info(
            "Checking location '%s' in blob container '%s' for remaining backfill work.",
            location,
            container,
        )
        _sync_down(container)
        months_remaining = _months_remaining_in_sync_dir()
        if months_remaining == 0:
            logging.info(
                "Backfill complete for location '%s' in container '%s'. Moving to next location.",
                location,
                container,
            )
            continue

        os.environ['SAVE_FOLDER'] = str(SYNC_DIR)
        os.environ['LOCATION'] = location
        monthly_pull.main()

        uploaded_blobs = _sync_up(container)
        if uploaded_blobs:
            _send_upload_email(container, uploaded_blobs)
        logging.info(
            "Run complete for location '%s'. Data synced to blob container '%s'.",
            location,
            container,
        )
        return

    logging.info("All configured locations are complete (months_remaining == 0). Nothing to do.")
