"""Send one consolidated Kerkrade data-status email per UTC day."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import azure.functions as func
from azure.communication.email import EmailClient
from daily_summary import build_message
from monthly_pull_timer import _build_hourly_weather_summary, _build_iot_summary


def _required_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _message(now: datetime | None = None) -> dict:
    """Build the single daily email from the current weather and IoT blobs."""
    now = now or datetime.now(timezone.utc)
    sender = _required_setting("ALERT_SENDER")
    recipients = [
        address.strip()
        for address in _required_setting("ALERT_RECIPIENTS").split(",")
        if address.strip()
    ]
    if not recipients:
        raise RuntimeError("ALERT_RECIPIENTS does not contain a usable address")

    return build_message(
        now=now,
        sender=sender,
        recipients=recipients,
        hourly_weather_summary=_build_hourly_weather_summary(),
        iot_summary=_build_iot_summary(),
    )


def main(timer: func.TimerRequest) -> None:
    """Azure Functions timer entry point."""
    if timer.past_due:
        logging.warning("Daily summary timer is past due.")

    client = EmailClient.from_connection_string(
        _required_setting("AZURE_COMMUNICATION_CONNECTION_STRING")
    )
    result = client.begin_send(_message()).result()
    logging.info("Daily summary email sent. Message ID: %s", result.get("id"))
