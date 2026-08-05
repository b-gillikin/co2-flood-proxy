"""Stable data-loading facade for chapter scripts.

Source-specific parsing lives in smaller modules (`io_iot`, `io_weather`,
`io_discharge`, `io_knmi`, and `io_groundwater`). Scripts import from here so
the implementation can stay organized by data family without churning callers.

RIVM air-quality loading was removed on 2026-08-05 with the cross-site transfer
analysis; see `archive/`.
"""

from __future__ import annotations

from src.io_discharge import DISCHARGE_SOURCES, load_discharge
from src.io_groundwater import load_groundwater, normalize_groundwater, select_primary_series
from src.io_iot import IOT_COLUMN_MAP, IOT_METADATA_COLUMNS, load_iot, load_iot_observations
from src.io_knmi import KNMI_STATION_SETS, knmi_station_set_frame, load_knmi
from src.io_weather import WEATHER_COLUMN_MAP, load_weather

__all__ = [
    "DISCHARGE_SOURCES",
    "IOT_COLUMN_MAP",
    "IOT_METADATA_COLUMNS",
    "KNMI_STATION_SETS",
    "WEATHER_COLUMN_MAP",
    "knmi_station_set_frame",
    "load_discharge",
    "load_groundwater",
    "load_iot",
    "load_iot_observations",
    "load_knmi",
    "load_weather",
    "normalize_groundwater",
    "select_primary_series",
]
