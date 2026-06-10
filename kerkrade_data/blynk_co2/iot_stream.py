import csv
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent
PIN_MAPPING_PATH = BASE_DIR / "pin-mapping.json"
CSV_PATH = BASE_DIR / "streaming_data.csv"
PARQUET_PATH = BASE_DIR / "streaming_data.parquet"


def _get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _load_pin_mapping() -> dict[str, str]:
    with open(PIN_MAPPING_PATH, "r") as file:
        return json.load(file)


def _fetch_pin_value(base_token: str, pin: str):
    url = f"https://fra1.blynk.cloud/external/api/get?token={base_token}&{pin}"
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
            logging.warning("Failed to fetch %s (%s): %s", pin, attribute, exc)
            value = ""
        row[attribute] = "" if value is None else str(value)
    row["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return row


def _append_csv(path: Path, columns: list[str], row: dict[str, str]) -> None:
    file_exists = path.exists()
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _upsert_parquet(path: Path, columns: list[str], row: dict[str, str]) -> None:
    new_df = pd.DataFrame([row], columns=columns)
    if path.exists():
        old_df = pd.read_parquet(path)
        out_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        out_df = new_df
    out_df.to_parquet(path, index=False)


def main() -> None:
    base_token = _get_required_env("BLYNK_BASE_TOKEN")
    pin_mapping = _load_pin_mapping()
    columns = list(pin_mapping.values()) + ["updated"]
    row = _build_row(pin_mapping, base_token)

    _append_csv(CSV_PATH, columns, row)
    _upsert_parquet(PARQUET_PATH, columns, row)

    print(f"Appended 1 row at {row['updated']} UTC to {CSV_PATH.name} and {PARQUET_PATH.name}")


if __name__ == "__main__":
    main()
