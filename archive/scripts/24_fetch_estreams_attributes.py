"""Fetch EStreams catchment attributes for the Limburg gauges.

EStreams (Nascimento et al., Scientific Data, 2024) publishes streamflow indices,
hydro-climatic signatures and landscape descriptors for 17,130 European
catchments, with delineated boundaries. It is exactly the static-descriptor set
this chapter needs -- terrain, soil, geology, vegetation, land cover -- already
computed per catchment, so no delineation or geospatial stack is required for the
tabular attributes.

    https://zenodo.org/records/10733142

The obstacle is packaging: the archive is a single 10 GB zip, dominated by 15,047
per-catchment daily meteorology files the chapter does not need. The attribute
tables inside are a few megabytes.

Zenodo serves HTTP range requests, so this script reads the zip's central
directory from the tail of the file and then fetches only the members it wants.
That turns a 10 GB download into a few MB. The approach is standard remote-zip
access; it depends on Zenodo continuing to honour ranges, and falls back to a
clear error rather than silently downloading everything.

Matching to Waterschap Limburg gauges is by nearest EStreams gauging station
within a tolerance, reported with the distance so a bad match is visible rather
than assumed.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.fetching import great_circle_km

ZIP_URL = "https://zenodo.org/records/10733142/files/EStreams.zip"
INVENTORY_PATH = Path("data/interim/waterschap_locations.csv")
RAW_DIR = Path("data/raw/estreams")
OUTPUT_PATH = Path("data/interim/estreams_gauge_attributes.csv")

# Tabular members worth pulling. Shapefiles are skipped; they need a geospatial
# stack and the attributes are what the similarity axes consume.
WANTED = (
    "streamflow_gauges/estreams_gauging_stations.csv",
    "attributes/static_attributes/estreams_terrain_attributes.csv",
    "attributes/static_attributes/estreams_soil_attributes.csv",
    "attributes/static_attributes/estreams_geology_attributes.csv",
    "attributes/static_attributes/estreams_hydrology_attributes.csv",
    "attributes/static_attributes/estreams_vegetation_attributes.csv",
    "attributes/temporal_attributes/estreams_landcover_attributes.csv",
)
# 1 km, not 5. Beyond about 2 km the "matches" are spurious nearest-neighbours
# to unrelated catchments; 18 gauges sit at essentially 0.00 km because EStreams
# contains those same stations. See docs/scope-decisions.md section 3.
MATCH_TOLERANCE_KM = 1.0


class RemoteFile(io.RawIOBase):
    """Minimal seekable file over HTTP range requests."""

    def __init__(self, url):
        self.url = url
        self._position = 0
        with urlopen(Request(url, method="HEAD"), timeout=60) as response:
            self.size = int(response.headers["content-length"])

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self._position = offset
        elif whence == io.SEEK_CUR:
            self._position += offset
        else:
            self._position = self.size + offset
        return self._position

    def tell(self):
        return self._position

    def seekable(self):
        return True

    def readable(self):
        return True

    def read(self, size=-1):
        if size < 0:
            size = self.size - self._position
        if size == 0:
            return b""
        end = min(self._position + size, self.size) - 1
        request = Request(self.url, headers={"Range": f"bytes={self._position}-{end}"})
        with urlopen(request, timeout=180) as response:
            if response.status != 206:
                raise RuntimeError(
                    "Zenodo did not honour a range request; refusing to download "
                    "the full 10 GB archive. Download EStreams.zip manually and "
                    "point --local-zip at it."
                )
            payload = response.read()
        self._position += len(payload)
        return payload


def extract(archive, refresh=False):
    """Pull the wanted members, caching each to disk."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    names = set(archive.namelist())
    tables = {}
    for member in WANTED:
        candidates = [n for n in names if n.endswith(member)]
        if not candidates:
            print(f"  {member}: not present in archive")
            continue
        target = RAW_DIR / Path(member).name
        if not target.exists() or refresh:
            with archive.open(candidates[0]) as handle:
                target.write_bytes(handle.read())
        tables[Path(member).stem] = pd.read_csv(target, low_memory=False)
        print(f"  {Path(member).name}: {len(tables[Path(member).stem]):,} rows")
    return tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--local-zip", default="", help="Use a downloaded EStreams.zip")
    args = parser.parse_args()

    source = args.local_zip or RemoteFile(ZIP_URL)
    print(f"reading EStreams archive ({'local' if args.local_zip else 'remote, ranged'})")
    with zipfile.ZipFile(source) as archive:
        tables = extract(archive, refresh=args.refresh)

    stations = tables.get("estreams_gauging_stations")
    if stations is None:
        print("no gauging-station table; cannot match")
        return

    lat_col = next(c for c in stations.columns if c.lower() in {"lat", "latitude", "gauge_lat"})
    lon_col = next(c for c in stations.columns if c.lower() in {"lon", "longitude", "gauge_lon"})
    id_col = next(c for c in stations.columns if "id" in c.lower())

    inventory = pd.read_csv(INVENTORY_PATH)
    gauges = inventory.loc[inventory["LocationType"].eq("Drainage") & inventory["Latitude"].notna()]

    rows = []
    for gauge in gauges.itertuples(index=False):
        point = (float(gauge.Latitude), float(gauge.Longitude))
        best, best_km = None, 9e9
        for station in stations.itertuples(index=False):
            candidate = (getattr(station, lat_col), getattr(station, lon_col))
            if pd.isna(candidate[0]) or pd.isna(candidate[1]):
                continue
            km = great_circle_km(point, candidate)
            if km < best_km:
                best, best_km = station, km
        rows.append(
            {
                "waterschap_id": gauge.Id,
                "waterschap_name": gauge.Name,
                "water_name": gauge.WaterName,
                "estreams_id": getattr(best, id_col) if best is not None else None,
                "match_distance_km": round(best_km, 2) if best is not None else None,
                "matched": best is not None and best_km <= MATCH_TOLERANCE_KM,
            }
        )
    matches = pd.DataFrame(rows).sort_values("match_distance_km")

    # Join every static attribute table onto the matched EStreams id.
    combined = matches
    for name, table in tables.items():
        if name == "estreams_gauging_stations":
            continue
        key = next((c for c in table.columns if "id" in c.lower()), None)
        if key is None:
            continue
        combined = combined.merge(
            table.add_prefix(f"{name.replace('estreams_', '').replace('_attributes', '')}_"),
            left_on="estreams_id",
            right_on=f"{name.replace('estreams_', '').replace('_attributes', '')}_{key}",
            how="left",
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT_PATH, index=False)
    good = int(matches["matched"].sum())
    print(
        f"\nmatched {good} of {len(matches)} Waterschap discharge gauges "
        f"within {MATCH_TOLERANCE_KM} km"
    )
    print(f"wrote {OUTPUT_PATH} ({combined.shape[1]} columns)")


if __name__ == "__main__":
    main()
