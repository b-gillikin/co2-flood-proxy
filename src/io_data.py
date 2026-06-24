"""Stable data-loading facade for chapter scripts.

Source-specific parsing lives in smaller modules (`io_iot`, `io_weather`,
`io_discharge`, `io_knmi`, and `io_rivm`). Scripts can keep importing from this
module while the implementation stays organized by data family.
"""

from __future__ import annotations

from src.io_discharge import DISCHARGE_SOURCES, load_discharge
from src.io_iot import IOT_COLUMN_MAP, IOT_METADATA_COLUMNS, load_iot, load_iot_observations
from src.io_knmi import KNMI_STATION_SETS, knmi_station_set_frame, load_knmi
from src.io_rivm import load_rivm
from src.io_weather import WEATHER_COLUMN_MAP, load_weather


__all__ = [
    "DISCHARGE_SOURCES",
    "IOT_COLUMN_MAP",
    "IOT_METADATA_COLUMNS",
    "KNMI_STATION_SETS",
    "WEATHER_COLUMN_MAP",
    "knmi_station_set_frame",
    "load_discharge",
    "load_iot",
    "load_iot_observations",
    "load_knmi",
    "load_rivm",
    "load_weather",
]
