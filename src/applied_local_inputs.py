"""Deterministic local input pairing and source/QA support, independent of labels."""

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

from applied_copernicus import normalize_radar
from applied_water import PRITHVI_S2, galileo_radar_norm


def pair_rows(frame, task):
    frame = frame.copy()
    frame["time"] = pd.to_datetime(frame.acquisition_utc, utc=True)
    frame["grid"] = frame.path.map(lambda x: Path(x).stem)
    sensor = "s2_event" if task in {"terramind", "prithvi"} else "s1_event"
    outputs = []
    for row in frame[frame.sensor == sensor].sort_values("path").to_dict("records"):
        candidates = frame[
            (frame.aoi == row["aoi"]) & (frame.grid == row["grid"]) & (frame.time <= row["time"])
        ]
        pair = None
        if task == "terramind":
            candidates = candidates[candidates.sensor == "s1_event"]
        elif task == "copernicus":
            candidates = candidates[
                (candidates.sensor == "s1_pre")
                & (candidates.relative_orbit == row["relative_orbit"])
                & (candidates.orbit_pass == row["orbit_pass"])
            ]
        else:
            candidates = candidates.iloc[:0]
        if len(candidates):
            pair = candidates.sort_values(["time", "path"]).iloc[-1].to_dict()
        outputs.append(
            dict(
                primary=row,
                paired=pair,
                available=task not in {"terramind", "copernicus"} or pair is not None,
                pair_rule="Latest held preceding same-grid event radar for optical fusion; latest held same-orbit/pass pre radar for change. No reference-map information enters pairing.",
            )
        )
    return outputs


def spectral_support(array, n):
    return (array[-1] == 1) & np.isfinite(array[:n]).all(0) & (array[:n] != -9999).all(0)


def optical_clear(array):
    q = array[13]
    known = np.isfinite(q) & (q != -9999)
    flags = np.where(known, q, 0).astype(np.int64)
    return known & ((flags & ((1 << 10) | (1 << 11))) == 0)


def read_inputs(pair, task, root):
    raw = []
    profile = None
    for r in [pair["primary"], pair["paired"]]:
        if r is None:
            continue
        with rasterio.open(root / r["path"]) as ds:
            if profile and (ds.shape, ds.transform, ds.crs) != (
                raw[0].shape[-2:],
                profile["transform"],
                profile["crs"],
            ):
                raise ValueError("Local paired inputs are not aligned")
            raw.append(ds.read())
            profile = ds.profile.copy()
    first = raw[0]
    if task in {"prithvi", "terramind"}:
        valid = spectral_support(first, 13) & optical_clear(first)
        optical = np.where(first[:13] != -9999, first[:13], np.nan)
        if task == "prithvi":
            x = (
                optical[PRITHVI_S2] - np.array([1087, 1342, 1433, 2734, 1958, 1363])[:, None, None]
            ) / np.array([2248, 2179, 2178, 1850, 1242, 1049])[:, None, None]
    elif task == "galileo":
        valid = spectral_support(first, 3)
        x = galileo_radar_norm(np.where(first[:2] != -9999, first[:2], np.nan))
        x = np.nan_to_num(x, nan=0.5, posinf=0.5, neginf=0.5)
    else:
        pre = raw[1]
        valid = spectral_support(first, 3) & spectral_support(pre, 3)
        raw_intensity = np.concatenate(
            [np.power(10.0, pre[:2] / 10), np.power(10.0, first[:2] / 10)]
        )
        raw_intensity[:, ~valid] = 0
        x, _ = normalize_radar(raw_intensity)
    if task == "terramind":
        # Same held training normalization, not statistics fitted on local maps.
        from importlib.util import module_from_spec, spec_from_file_location

        path = Path(__file__).resolve().parents[1] / "scripts/185_run_applied_water.py"
        spec = spec_from_file_location("water_normalization", path)
        w = module_from_spec(spec)
        spec.loader.exec_module(w)
        radar = raw[1]
        valid &= spectral_support(radar, 3)
        s1 = np.where(radar[:2] != -9999, radar[:2], np.nan)
        x = np.concatenate(
            [
                w.standardize(optical, w.TM_S2_MEAN, w.TM_S2_STD),
                w.standardize(s1, [-12.599, -20.293], [5.195, 5.890]),
            ]
        )
    return np.nan_to_num(x, nan=0, posinf=0, neginf=0).astype(np.float32), valid, profile
