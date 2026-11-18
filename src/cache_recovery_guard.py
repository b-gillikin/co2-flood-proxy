"""Do not interpret intentionally offloaded historical inputs as missing data."""

from pathlib import Path


def require_local_cache(path):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        marker = parent / "OFFLOADED-DERIVED.json"
        if marker.is_file():
            raise RuntimeError(
                f"Historical cache is offloaded, not missing observations: {marker}. "
                "Use scripts/278_offload_historical_derived.py --restore-path "
                "PROJECT_RELATIVE_FILE, or restore its recorded bundle."
            )
