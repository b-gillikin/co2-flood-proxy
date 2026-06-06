"""Data loading and alignment entry points.

The June workflow expects one stable loader per source. Scripts should import
these functions and keep source-specific parsing details here.
"""

from __future__ import annotations


def load_iot(*args, **kwargs):
    """Load the Kerkrade IoT stream.

    TODO: parse timestamps, align to the analysis frequency, flag gaps, and
    return CO2/temp/humidity/pressure/PM columns.
    """
    raise NotImplementedError("Kerkrade IoT loader is not implemented yet.")


def load_weather(*args, **kwargs):
    """Load Visualcrossing or reference weather data."""
    raise NotImplementedError("Weather loader is not implemented yet.")


def load_discharge(*args, **kwargs):
    """Load Worm/Geul discharge data aligned to the analysis index."""
    raise NotImplementedError("Discharge loader is not implemented yet.")


def load_knmi(*args, **kwargs):
    """Load KNMI reference meteorological data."""
    raise NotImplementedError("KNMI loader is not implemented yet.")

