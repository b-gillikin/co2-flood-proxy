"""Stable data-loading facade for chapter scripts.

Source-specific parsing lives in smaller modules (`io_iot`, `io_weather`,
`io_knmi`). Scripts import from here so the implementation can stay organized by
data family without churning callers.

Three families have been removed rather than kept "in case". RIVM air-quality
loading went on 2026-08-05 with the cross-site transfer analysis. Discharge
loading went on 2026-08-06: it read the same Waterschap endpoint as
`scripts/22_ingest_waterschap_gauges.py` but with different missing-value
handling. Groundwater went on 2026-08-07 with the rest of the donor-instrument
lane — it characterised three wells and never touched the transfer question.
All in `archive/`.
"""

from __future__ import annotations

from src.io_iot import IOT_COLUMN_MAP, IOT_METADATA_COLUMNS, load_iot, load_iot_observations
from src.io_knmi import KNMI_STATION_SETS, knmi_station_set_frame, load_knmi
from src.io_weather import WEATHER_COLUMN_MAP, load_weather

__all__ = [
    "IOT_COLUMN_MAP",
    "IOT_METADATA_COLUMNS",
    "KNMI_STATION_SETS",
    "WEATHER_COLUMN_MAP",
    "knmi_station_set_frame",
    "load_iot",
    "load_iot_observations",
    "load_knmi",
    "load_weather",
]
