"""Shared helpers for building stable, lowercase column/name tokens.

Several loaders turn free-form source names (weather locations, RIVM station
codes, discharge gauge columns) into safe column prefixes. Keeping that logic in
one place stops the three near-identical copies from drifting apart.
"""

from __future__ import annotations


def safe_token(value):
    """Lowercase a value and collapse non-alphanumerics into single-run tokens.

    Every non-alphanumeric character becomes ``_``; leading/trailing separators
    are stripped. ``"Maastricht Airport"`` -> ``"maastricht_airport"``.
    """
    return "".join(char.lower() if char.isalnum() else "_" for char in str(value)).strip("_")


def source_token(value, strip_prefix="", strip_suffix=""):
    """Turn a source column name into a compact output-column prefix.

    Optionally drops a known prefix/suffix (e.g. ``discharge_``/``_m3s``) before
    normalizing with :func:`safe_token`.
    """
    token = str(value)
    if strip_prefix:
        token = token.removeprefix(strip_prefix)
    if strip_suffix:
        token = token.removesuffix(strip_suffix)
    return safe_token(token)
