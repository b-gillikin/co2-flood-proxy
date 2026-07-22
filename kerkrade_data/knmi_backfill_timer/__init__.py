"""Azure Timer trigger for KNMI historical or forward collection."""

from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone

import azure.functions as func


def main(timer: func.TimerRequest, diagnostic: func.Out[str]) -> None:
    """Run one bounded KNMI collection batch and write a diagnostic marker."""
    payload = {
        "status": "started",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "past_due": bool(timer.past_due),
    }

    try:
        if timer.past_due:
            logging.warning("KNMI backfill timer is past due.")

        import knmi_backfill

        summary = knmi_backfill.run_backfill_once()
        payload["status"] = "complete"
        payload["summary"] = summary
        logging.info(
            "KNMI backfill batch complete: %s",
            json.dumps(summary, sort_keys=True),
        )
    except Exception as exc:
        payload["status"] = "failed"
        payload["error_type"] = type(exc).__name__
        payload["error_message"] = str(exc)
        payload["traceback"] = traceback.format_exc()
        logging.exception("KNMI backfill batch failed.")
    finally:
        payload["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        diagnostic.set(json.dumps(payload, indent=2, sort_keys=True))
