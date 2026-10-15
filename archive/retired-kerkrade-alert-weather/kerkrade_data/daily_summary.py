"""Pure message construction for the daily Kerkrade status email."""

from __future__ import annotations

from datetime import datetime


def build_message(
    now: datetime,
    sender: str,
    recipients: list[str],
    hourly_weather_summary: str,
    iot_summary: str,
) -> dict:
    """Return the Azure Communication Services email payload."""
    body = "\n\n".join(
        [
            f"Kerkrade daily data summary generated {now:%Y-%m-%d %H:%M:%S} UTC",
            hourly_weather_summary,
            iot_summary,
        ]
    )
    return {
        "senderAddress": sender,
        "content": {
            "subject": f"Kerkrade daily data summary — {now:%Y-%m-%d} UTC",
            "plainText": body,
        },
        "recipients": {"to": [{"address": address} for address in recipients]},
    }
