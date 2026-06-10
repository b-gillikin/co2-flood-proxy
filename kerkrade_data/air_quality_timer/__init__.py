import csv
import json
import logging
import os
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import azure.functions as func
import requests
from azure.storage.blob import BlobServiceClient


SCRIPT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PIN_MAPPING_PATH = SCRIPT_DIR / 'blynk_co2' / 'pin-mapping.json'
DEFAULT_CONTAINER = 'air-quality-device-data-1'
DEFAULT_BLOB_PREFIX = 'air_quality'


def _get_required_env(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value:
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value


def _get_blob_service() -> BlobServiceClient:
    conn_str = _get_required_env('AZURE_STORAGE_CONNECTION_STRING')
    return BlobServiceClient.from_connection_string(conn_str)


def _load_pin_mapping() -> dict[str, str]:
    mapping_path = Path(os.getenv('BLYNK_PIN_MAPPING_PATH', str(DEFAULT_PIN_MAPPING_PATH)))
    with open(mapping_path, 'r') as f:
        return json.load(f)


def _fetch_pin_value(base_token: str, pin: str):
    url = f'https://fra1.blynk.cloud/external/api/get?token={base_token}&{pin}'
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return response.text.strip()


def _build_row(pin_mapping: dict[str, str], base_token: str) -> dict[str, str]:
    row: dict[str, str] = {}
    for pin, attribute in pin_mapping.items():
        try:
            value = _fetch_pin_value(base_token, pin)
        except requests.RequestException as exc:
            logging.warning('Failed to fetch %s (%s): %s', pin, attribute, exc)
            value = ''
        row[attribute] = '' if value is None else str(value)

    row['updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    return row


def _append_csv_line(container_name: str, blob_name: str, columns: list[str], row: dict[str, str]) -> None:
    svc = _get_blob_service()
    container = svc.get_container_client(container_name)
    if not container.exists():
        container.create_container()
    blob = container.get_blob_client(blob_name)

    existing_text = ''
    try:
        existing_text = blob.download_blob().readall().decode('utf-8', errors='replace')
    except Exception:
        existing_text = ''

    payload = StringIO()
    if existing_text:
        payload.write(existing_text)
        if not existing_text.endswith('\n'):
            payload.write('\n')
        writer = csv.DictWriter(payload, fieldnames=columns)
        writer.writerow(row)
    else:
        writer = csv.DictWriter(payload, fieldnames=columns)
        writer.writeheader()
        writer.writerow(row)

    blob.upload_blob(payload.getvalue().encode('utf-8'), overwrite=True)


def main(timer: func.TimerRequest) -> None:
    base_token = _get_required_env('BLYNK_BASE_TOKEN')
    container_name = os.getenv('AIR_QUALITY_CONTAINER', DEFAULT_CONTAINER).strip() or DEFAULT_CONTAINER
    blob_prefix = os.getenv('AIR_QUALITY_BLOB_PREFIX', DEFAULT_BLOB_PREFIX).strip() or DEFAULT_BLOB_PREFIX

    pin_mapping = _load_pin_mapping()
    columns = list(pin_mapping.values()) + ['updated']
    row = _build_row(pin_mapping, base_token)

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    blob_name = f'{blob_prefix}_{today}.csv'
    _append_csv_line(container_name, blob_name, columns, row)

    logging.info(
        "IoT row appended to %s/%s at %s",
        container_name,
        blob_name,
        row['updated'],
    )
