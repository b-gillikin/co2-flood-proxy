"""DISE-inspired preparation. Explicit phases; never launches the full study."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PROJ_DATA", str(Path(sys.base_prefix) / "share/proj"))
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.dise import daily_hour_end, specific_q
from src.dise_acquisition import HTTPRangeFile
from src.geoglows_experiment import disk_check, sha, write_json

CONFIG = ROOT / "config/limburg_dise_v1.json"
PLAN = json.loads(CONFIG.read_text())
RAW, OUT = ROOT / PLAN["raw"], ROOT / PLAN["output"]
WEATHER_BANDS = ["total_precipitation_sum", "temperature_2m", "dewpoint_temperature_2m",
                 "surface_pressure", "u_component_of_wind_10m", "v_component_of_wind_10m",
                 "surface_solar_radiation_downwards_sum", "surface_thermal_radiation_downwards_sum"]


def sites():
    p = json.loads((ROOT / PLAN["source_config"]).read_text())
    return [x for x in p["sites"] if x["channel"] in p["target_channels"]]


def geometries():
    import geopandas as gpd
    frame = gpd.read_file(ROOT / "data/interim/foundation_model_catchments.gpkg").to_crs(4326).set_index("gauge")
    return [(s, frame.loc[s["catchment_gauge"]].geometry) for s in sites()]


def verify_existing(path, identity):
    receipt = path.with_suffix(path.suffix + ".receipt.json")
    if path.exists():
        if not receipt.exists():
            raise ValueError(f"Existing output has no receipt: {path}")
        old = json.loads(receipt.read_text())
        if old["identity"] != identity or old["sha256"] != sha(path):
            raise ValueError(f"Existing source differs: {path}")
        return True
    return False


def camels_metadata():
    dest = RAW / "camels"
    dest.mkdir(parents=True, exist_ok=True)
    with HTTPRangeFile(PLAN["camels_archive"]) as remote:
        with zipfile.ZipFile(remote) as archive:
            members = [dict(name=i.filename, bytes=i.file_size, compressed_bytes=i.compress_size,
                            crc32=i.CRC) for i in archive.infolist()]
            write_json(dest / "archive_inventory.json", dict(url=remote.url, etag=remote.etag,
                       archive_bytes=remote.size, members=members))
            for item in archive.infolist():
                if not (item.filename.endswith("_attributes.csv") or item.filename.endswith(".gpkg")):
                    continue
                path = dest / Path(item.filename).name
                identity = dict(url=remote.url, etag=remote.etag, member=item.filename, crc32=item.CRC)
                if verify_existing(path, identity):
                    continue
                disk_check(ROOT, PLAN["reserve_gib"], item.file_size)
                tmp = path.with_suffix(path.suffix + ".partial")
                with archive.open(item) as source, tmp.open("wb") as target:
                    shutil.copyfileobj(source, target, 1024**2)
                tmp.replace(path)  # zipfile checks the member CRC before EOF.
                write_json(path.with_suffix(path.suffix + ".receipt.json"), dict(
                    identity=identity, sha256=sha(path), bytes=path.stat().st_size))
                print("Acquired metadata", path.name, flush=True)
        write_json(dest / "access_receipt.json", dict(archive_bytes=remote.size,
                   bytes_transferred_this_pass=remote.transferred, requests=remote.requests,
                   range_support_verified=True, full_archive_downloaded=False, etag=remote.etag))


def weather(years):
    import ee
    ee.Initialize(project=PLAN["earth_engine_project"])
    pairs = geometries()
    features = ee.FeatureCollection([ee.Feature(ee.Geometry(g.__geo_interface__), {"gauge": s["gauge"]}) for s, g in pairs])
    geom_hash = sha(ROOT / "data/interim/foundation_model_catchments.gpkg")

    def one(year):
        path = RAW / "weather" / f"local_daily_{year}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        identity = dict(collection=PLAN["weather_collection"], year=year,
                        bands=WEATHER_BANDS, geometry_sha256=geom_hash,
                        aggregation="native-grid pixel-area/fraction-weighted mean")
        if verify_existing(path, identity):
            print("Reused weather", year, flush=True)
            return
        collection = ee.ImageCollection(PLAN["weather_collection"]).filterDate(f"{year}-01-01", f"{year+1}-01-01")
        projection = collection.first().select(WEATHER_BANDS[0]).projection().getInfo()

        # Stack dates into bands: ONE spatial aggregation, not 365 concurrent
        # reduceRegions calls (which exceeds Earth Engine aggregation quotas).
        stacked = collection.select(WEATHER_BANDS).map(
            lambda im: im.set("system:index", im.date().format("YYYYMMdd"))).toBands()
        area = ee.Image.pixelArea().rename("sampled_area_m2")
        area = area.updateMask(stacked.mask().reduce(ee.Reducer.min()))
        weighted = stacked.multiply(area).addBands(area)
        values = weighted.reduceRegions(collection=features, reducer=ee.Reducer.sum(),
                     crs=projection["crs"], crsTransform=projection["transform"], tileScale=2).getInfo()
        records = []
        dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", tz="UTC")
        for value in values["features"]:
            props = value["properties"]
            for day in dates:
                row = dict(gauge=props["gauge"], day=day, sampled_area_m2=props["sampled_area_m2"])
                for band in WEATHER_BANDS:
                    row[band] = props.get(f"{day.strftime('%Y%m%d')}_{band}", np.nan) / props["sampled_area_m2"]
                records.append(row)
        frame = pd.DataFrame(records)
        frame["day"] = pd.to_datetime(frame.day, utc=True)
        if frame.duplicated(["gauge", "day"]).any():
            raise ValueError("Duplicate daily forcing rows")
        frame.to_parquet(path, index=False)
        write_json(path.with_suffix(path.suffix + ".receipt.json"), dict(
            identity=identity, sha256=sha(path), rows=len(frame),
            smallest_sampled_area_m2=float(frame.sampled_area_m2.min())))
        print("Acquired weather", year, len(frame), flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for _result in pool.map(one, years):
            pass


def attributes():
    import ee
    ee.Initialize(project=PLAN["earth_engine_project"])
    path = RAW / "local_attributes_v2.parquet"
    identity = dict(geometry=sha(ROOT / "data/interim/foundation_model_catchments.gpkg"),
                    sources=["CGIAR/SRTM90_V4", "COPERNICUS/Landcover/100m/Proba-V-C3/Global/2017",
                             "OpenLandMap/SOL/SOL_WATERCONTENT-33KPA_USDA-4B1C_M/v01"],
                    aggregation="EPSG:3035, 100 m pixel-area weighted; 2017 tree/crop/urban fractional cover")
    if verify_existing(path, identity):
        print("Reused attributes", flush=True)
        return
    features = ee.FeatureCollection([ee.Feature(ee.Geometry(g.__geo_interface__), {"gauge": s["gauge"]}) for s, g in geometries()])
    dem = ee.Image(identity["sources"][0]).select("elevation")
    lc = ee.Image(identity["sources"][1])
    image = ee.Image.cat([
        dem.rename("a_elevation_m"), ee.Terrain.slope(dem).rename("a_slope_deg"),
        lc.select("tree-coverfraction").divide(100).rename("a_tree_cover_fraction"),
        lc.select("crops-coverfraction").divide(100).rename("a_crop_cover_fraction"),
        lc.select("urban-coverfraction").divide(100).rename("a_urban_cover_fraction"),
        ee.Image(identity["sources"][2]).select("b0").rename("a_surface_field_capacity_pct"),
    ])
    area = ee.Image.pixelArea().rename("area_m2")
    # One common valid support for all bands; no per-band missing denominator.
    area = area.updateMask(image.mask().reduce(ee.Reducer.min()))
    values = image.multiply(area).addBands(area).reduceRegions(
        collection=features, reducer=ee.Reducer.sum(), scale=100, crs="EPSG:3035", tileScale=2).getInfo()
    frame = pd.DataFrame([v["properties"] for v in values["features"]])
    for column in [c for c in frame if c.startswith("a_")]:
        frame[column] /= frame.area_m2
    frame.to_parquet(path, index=False)
    write_json(path.with_suffix(path.suffix + ".receipt.json"), dict(identity=identity,
               sha256=sha(path), rows=len(frame), regulation="Unknown; not imputed as no regulation",
               soil="Surface field capacity proxy, not root-zone storage or permeability"))
    print("Acquired common-source local attributes", len(frame), flush=True)


def daily():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / "results/storm_response"
    observed = pd.read_parquet(source / "hourly_discharge.parquet")
    strict = pd.read_parquet(source / "hourly_strict.parquet")
    domain = pd.read_parquet(source / "hourly_domain.parquet")
    model = pd.read_parquet(ROOT / "data/raw/limburg_geoglows_stages12_v1/hourly_discharge.parquet")
    qo, count_o = daily_hour_end(observed)
    qm, count_m = daily_hour_end(model)
    clean, _ = daily_hour_end(observed.where(strict & domain))
    alpha_path = ROOT / "data/raw/foundation_assets/alphaearth/limburg_alphaearth_metric_grid_v2.csv"
    alpha = pd.read_csv(alpha_path)
    alpha = alpha.loc[alpha.embedding_year.eq(PLAN["alphaearth_primary_year"])].set_index("gauge")
    mapping = {x["gauge"]: x for x in json.loads((ROOT / "config/limburg_geoglows_reaches_v1.json").read_text())}
    rows = []
    for s in sites():
        gauge, channel, area = s["gauge"], str(s["channel"]), s["reference_area_km2"]
        if channel not in qm and int(channel) in qm:
            channel = int(channel)
        f = pd.DataFrame(dict(day=qo.index, q_observed_m3s=qo[gauge],
                             q_model_m3s=qm[channel].reindex(qo.index),
                             observed_hours=count_o[gauge], model_hours=count_m[channel].reindex(qo.index),
                             clean_verification=clean[gauge].notna())).reset_index(drop=True)
        f["gauge"], f["station"] = gauge, s["station"]
        f["river_group"] = "Wurm" if "Wurm" in s["river"] else s["river"]
        f["reference_area_km2"] = area
        f["q_observed"] = specific_q(f.q_observed_m3s, area)
        f["q_model"] = specific_q(f.q_model_m3s, area)
        f["h_mapping_area_ratio"] = mapping[gauge]["area_ratio"]
        f["h_mapping_overlap"] = mapping[gauge]["held_area_covered_fraction"]
        f["a_log_area_km2"] = np.log(area)
        for j in range(64):
            f[f"e_A{j:02d}"] = alpha.loc[s["catchment_gauge"], f"A{j:02d}"]
        rows.append(f)
    frame = pd.concat(rows, ignore_index=True)
    frame.to_parquet(OUT / "daily_reference.parquet", index=False)
    support = frame.assign(year=frame.day.dt.year, paired=np.isfinite(frame.q_observed) & np.isfinite(frame.q_model)).groupby(
        ["gauge", "station", "year"]).agg(days=("day", "size"), observed_days=("q_observed", "count"),
        model_days=("q_model", "count"), paired_days=("paired", "sum"), clean_days=("clean_verification", "sum"))
    support.to_csv(OUT / "daily_support.csv")
    print("Daily reference", len(frame), "rows; paired", int(frame.q_observed.notna().mul(frame.q_model.notna()).sum()), flush=True)
    weather_paths = [RAW / "weather" / f"local_daily_{y}.parquet" for y in PLAN["weather_years"]]
    if not all(p.exists() for p in weather_paths) or not (RAW / "local_attributes_v2.parquet").exists():
        print("Reference complete; feature assembly pending weather/attributes", flush=True)
        return
    w = pd.concat([pd.read_parquet(p) for p in weather_paths], ignore_index=True)
    aliases = dict(zip(WEATHER_BANDS, ["h_precip_m", "h_temp_k", "h_dewpoint_k", "h_pressure_pa", "h_u10", "h_v10", "h_shortwave_j", "h_longwave_j"], strict=True))
    w = w.rename(columns=aliases)
    for c in ["h_precip_m", "h_shortwave_j", "h_longwave_j"]:
        w[c] = w[c].where(w[c].ge(0))
    w = w.drop(columns="sampled_area_m2")
    frame = frame.merge(w, on=["gauge", "day"], how="left", validate="one_to_one")
    attrs = pd.read_parquet(RAW / "local_attributes_v2.parquet").drop(columns="area_m2")
    frame = frame.merge(attrs, on="gauge", how="left", validate="many_to_one")
    frame = frame.sort_values(["gauge", "day"]).reset_index(drop=True)
    frame["h_q_model"] = frame.q_model
    frame["h_season_sin"] = np.sin(2*np.pi*frame.day.dt.dayofyear/365.25)
    frame["h_season_cos"] = np.cos(2*np.pi*frame.day.dt.dayofyear/365.25)
    # Reindexed daily reference guarantees shift means a calendar-day lag, not a previous available row.
    lagged = {f"{c}_lag{lag}": frame.groupby("gauge")[c].shift(lag)
              for c in ["h_q_model", *aliases.values()] for lag in range(1, 8)}
    frame = pd.concat([frame, pd.DataFrame(lagged, index=frame.index)], axis=1)
    frame = frame.loc[frame.day.ge("2018-01-01")].copy()
    frame.to_parquet(OUT / "local_features.parquet", index=False)
    sources = [source / f"{x}.parquet" for x in ["hourly_discharge", "hourly_strict", "hourly_domain"]]
    sources += [alpha_path, CONFIG, *weather_paths, RAW / "local_attributes_v2.parquet",
                ROOT / "data/raw/limburg_geoglows_stages12_v1/hourly_discharge.parquet",
                ROOT / "config/limburg_geoglows_reaches_v1.json",
                ROOT / "data/interim/foundation_model_catchments.gpkg"]
    write_json(OUT / "preparation_receipt.json", dict(status="local_features_ready_regional_donors_pending",
               rows=len(frame), sources={str(p.relative_to(ROOT)): sha(p) for p in sources},
               outputs={p.name: sha(p) for p in OUT.glob("*.parquet")},
               target="daily reconstruction", full_comparison_started=False))
    print("Local features", frame.shape, flush=True)


def regional_inventory():
    """Candidate census only: no outcome-based selection or assumed reach mapping."""
    import geopandas as gpd
    from shapely.ops import unary_union

    dest = RAW / "camels"
    topo = pd.read_csv(dest / "CAMELS_DE_1h_topographic_attributes.csv")
    catch = gpd.read_file(dest / "CAMELS_DE_1h_catchments.gpkg").to_crs(3035)
    topo = topo.merge(catch[["gauge_id", "geometry"]], on="gauge_id", validate="one_to_one")
    topo = gpd.GeoDataFrame(topo, geometry="geometry", crs=3035)
    centers = topo.geometry.centroid.to_crs(4326)
    topo["centroid_lon"], topo["centroid_lat"] = centers.x, centers.y
    native = gpd.read_file(ROOT / "data/interim/foundation_model_catchments.gpkg").to_crs(3035)
    local = unary_union(native.loc[native.gauge.isin([s["catchment_gauge"] for s in sites()]), "geometry"])
    river = topo.water_body_name.fillna("").str.casefold()
    reserved = {}
    for name in PLAN["external_rivers"]:
        matches = topo.loc[river.eq(name.casefold()), "geometry"]
        if matches.empty:
            raise ValueError(f"No named outlet geometry found for reserved river {name}")
        reserved[name] = unary_union(matches)
    lo, south, hi, north = PLAN["regional_bounds"]
    low_area, high_area = PLAN["regional_area_km2"]
    topo["reference_area_km2"] = topo.area_metadata.where(topo.area_metadata.gt(0), topo["area"])
    topo["local_overlap_fraction"] = topo.geometry.intersection(local).area / topo.geometry.area
    for name, geom in reserved.items():
        topo[f"reserved_overlap_{name}"] = topo.geometry.intersection(geom).area / topo.geometry.area
    topo["role"] = "outside_declared_domain"
    eligible = topo.centroid_lon.between(lo, hi) & topo.centroid_lat.between(south, north) & topo.reference_area_km2.between(low_area, high_area)
    topo.loc[eligible, "role"] = "donor_candidate_mapping_pending"
    # A 1% overlap is deliberately conservative and recorded, not a claim of exact topology.
    topo.loc[eligible & topo.local_overlap_fraction.gt(0.01), "role"] = "local_network_overlap_excluded"
    topo["external_group"] = ""
    for name in PLAN["external_rivers"]:
        selected = eligible & topo[f"reserved_overlap_{name}"].gt(0.01)
        topo.loc[selected, ["role", "external_group"]] = ["external_candidate_mapping_pending", name]
    # Tiny positive overlaps remain review items, never silently admitted as independent.
    border = eligible & topo.role.eq("donor_candidate_mapping_pending") & (
        topo.local_overlap_fraction.gt(0) | topo[[f"reserved_overlap_{n}" for n in PLAN["external_rivers"]]].gt(0).any(axis=1))
    topo.loc[border, "role"] = "boundary_overlap_review"
    OUT.mkdir(parents=True, exist_ok=True)
    topo.drop(columns="geometry").to_csv(OUT / "regional_candidate_ledger.csv", index=False)
    topo.loc[eligible].to_parquet(OUT / "regional_candidate_geometries.parquet")
    # Verify local catchment overlaps independently of gauge-name grouping.
    pairs = geometries()
    native_selected = native.set_index("gauge")
    overlaps = []
    for i, (a, _) in enumerate(pairs):
        for b, _ in pairs[i+1:]:
            ga, gb = native_selected.loc[a["catchment_gauge"]].geometry, native_selected.loc[b["catchment_gauge"]].geometry
            overlaps.append(dict(a=a["gauge"], b=b["gauge"], fraction_of_smaller=ga.intersection(gb).area/min(ga.area, gb.area)))
    write_json(OUT / "regional_inventory_receipt.json", dict(
        status="candidate_census_not_frozen_training_cohort", counts=topo.role.value_counts().to_dict(),
        external_groups=topo.loc[topo.role.eq("external_candidate_mapping_pending"), "external_group"].value_counts().to_dict(),
        local_polygon_overlaps=overlaps, topology_mapping_still_required=True,
        archive_bytes=json.loads((dest / "archive_inventory.json").read_text())["archive_bytes"],
        excluded_data=["observed hydrologic signatures", "benchmark model predictions", "weather forecast archives"],
        source_hashes={str(p.relative_to(ROOT)): sha(p) for p in [CONFIG, dest / "CAMELS_DE_1h_topographic_attributes.csv", dest / "CAMELS_DE_1h_catchments.gpkg"]}))
    print("Regional candidates", topo.role.value_counts().to_dict(), flush=True)


def regional_sample():
    """Verify one preselected donor member and its schema, without a bulk pull."""
    ledger = pd.read_csv(OUT / "regional_candidate_ledger.csv")
    gauge = ledger.loc[ledger.role.eq("donor_candidate_mapping_pending"), "gauge_id"].sort_values().iloc[0]
    inventory = json.loads((RAW / "camels/archive_inventory.json").read_text())
    name = next(x["name"] for x in inventory["members"] if x["name"].endswith(f"timeseries_{gauge}.csv"))
    path = RAW / "camels" / Path(name).name
    identity = dict(url=PLAN["camels_archive"], etag=inventory["etag"], member=name,
                    selection="lexicographically first donor candidate, no flow/error selection")
    if not verify_existing(path, identity):
        with HTTPRangeFile(PLAN["camels_archive"]) as remote:
            if remote.etag != inventory["etag"]:
                raise ValueError("Archive changed since inventory")
            with zipfile.ZipFile(remote) as archive:
                member = archive.getinfo(name)
                disk_check(ROOT, PLAN["reserve_gib"], member.file_size)
                partial = path.with_suffix(".csv.partial")
                with archive.open(member) as source, partial.open("wb") as target:
                    shutil.copyfileobj(source, target, 1024**2)
                partial.replace(path)
        write_json(path.with_suffix(".csv.receipt.json"), dict(identity=identity, sha256=sha(path), bytes=path.stat().st_size))
    frame = pd.read_csv(path)
    write_json(OUT / "regional_sample_schema.json", dict(gauge=gauge, rows=len(frame),
               columns=frame.columns.tolist(), first_rows=frame.head(3).to_dict("records"),
               schema_only_not_verified_training_labels=True))
    print("Verified selected timeseries access", gauge, frame.shape, frame.columns.tolist(), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["metadata", "regional", "sample", "weather", "attributes", "daily"])
    parser.add_argument("--years", type=int, nargs="+")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    disk_check(ROOT, PLAN["reserve_gib"])
    if args.phase == "metadata":
        camels_metadata()
    elif args.phase == "regional":
        regional_inventory()
    elif args.phase == "sample":
        regional_sample()
    elif args.phase == "weather":
        weather(args.years or PLAN["weather_years"])
    elif args.phase == "attributes":
        attributes()
    else:
        daily()


if __name__ == "__main__":
    main()
