#!/usr/bin/env python3
"""Emit a small Limburg run-state event to Azure Application Insights.

The ingestion connection string lives in the local environment or a private
file. This tool is deliberately independent of the research data/model code.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib import request


DEFAULT_PRIVATE_FILE = Path(__file__).resolve().parents[1] / "config/local_monitor.env"
ALLOWED_STATES = ("running", "planned_pause", "failed", "completed")


def connection_string(path: Path) -> str:
    value = os.environ.get("LIMBURG_APPINSIGHTS_CONNECTION_STRING", "").strip()
    if value:
        return value
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    raise RuntimeError("No monitoring connection string in environment or private file")


def endpoint_and_key(value: str) -> tuple[str, str]:
    parts = dict(part.split("=", 1) for part in value.split(";") if "=" in part)
    endpoint = parts.get("IngestionEndpoint", "").rstrip("/")
    key = parts.get("InstrumentationKey", "")
    if not endpoint.startswith("https://") or not key:
        raise ValueError("Monitoring connection string lacks HTTPS ingestion endpoint or key")
    return endpoint + "/v2/track", key


def emit(state: str, run_id: str, detail: str, private_file: Path) -> None:
    url, key = endpoint_and_key(connection_string(private_file))
    now = datetime.now(timezone.utc).isoformat()
    envelope = {
        "name": "Microsoft.ApplicationInsights.Event",
        "time": now,
        "iKey": key,
        "data": {
            "baseType": "EventData",
            "baseData": {
                "ver": 2,
                "name": f"limburg-run-{state}",
                "properties": {"run_id": run_id, "detail": detail[:500]},
            },
        },
    }
    body = json.dumps(envelope).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=15) as response:
        if response.status not in (200, 206):
            raise RuntimeError(f"Telemetry ingestion returned HTTP {response.status}")
        result = json.load(response)
    if result.get("itemsAccepted") != 1 or result.get("errors"):
        raise RuntimeError(f"Telemetry ingestion did not accept event: {result}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", choices=ALLOWED_STATES)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--detail", default="")
    parser.add_argument("--private-file", type=Path, default=DEFAULT_PRIVATE_FILE)
    args = parser.parse_args()
    try:
        emit(args.state, args.run_id, args.detail, args.private_file)
    except Exception as exc:
        print(f"monitor event failed: {exc}", file=sys.stderr)
        return 1
    print(f"accepted: {args.state} run={args.run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
