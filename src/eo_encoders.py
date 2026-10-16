"""Frozen EO engineering adapters. No fitting, response labels or event ranking."""

import importlib.util
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from .eo_inputs import standardize, validate_frames

NATIVE_TEMPORAL = {"olmoearth", "galileo", "anysat", "prithvi", "presto"}

HERE = Path(__file__).resolve().parents[1]
ASSETS = HERE / "data/raw/limburg_dynamic_model_weights"
spec = importlib.util.spec_from_file_location(
    "eo_load", HERE / "environments/eo-screen/check_load.py"
)
loaders = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loaders)
# Keep this module importable even where upstream code uses its own `src` package.


def tensor(x):
    return torch.from_numpy(np.ascontiguousarray(x)).float()


class Encoder:
    def __init__(self, name):
        self.name = name
        torch.manual_seed(1729)
        self.model = loaders.build_model(name)

    def __call__(self, patch):
        if not patch["valid"].any():
            raise ValueError("No observed pixels: do not generate an embedding")
        with torch.inference_mode():
            out = self.forward(patch)
        result = out.detach().cpu().numpy().astype(np.float32).reshape(-1)
        if not len(result) or not np.isfinite(result).all():
            raise ValueError("Nonfinite or empty embedding")
        return result

    def sequence(self, patches):
        validate_frames(patches)
        if self.name in NATIVE_TEMPORAL:
            return self({**patches[0], "frames": patches})
        # Snapshot encoders have no temporal attention. Equal frame mean is an
        # explicit order-invariant summary, never called a native sequence model.
        return np.stack([self(p) for p in patches]).mean(0)

    def forward(self, patch):
        v, mask, meta = patch["values"], patch["valid"], patch["metadata"]
        name, m = self.name, self.model
        frames = patch.get("frames", [patch])
        dates = [datetime.fromisoformat(p["metadata"]["representative_date"]) for p in frames]
        if name in NATIVE_TEMPORAL:
            v = np.stack([p["values"] for p in frames], axis=1)
            mask = np.stack([p["valid"] for p in frames])
        nt = len(frames)
        if name == "croma":
            # Official CROMA SAR example: mean +/- 2 SD -> clipped eight-bit.
            observed = v[:, mask]
            mean, std = observed.mean(1), observed.std(1)
            if np.any(std == 0):
                raise ValueError("CROMA contrast stretch undefined for constant observed channel")
            x = (
                np.clip((v - (mean - 2 * std)[:, None, None]) / (4 * std)[:, None, None], 0, 1)
                * 255
            )
            x[:, ~mask] = 127
            return m(SAR_images=tensor(x.astype(np.uint8).astype(np.float32))[None])["SAR_GAP"]
        if name == "olmoearth":
            from olmoearth_pretrain.datatypes import MaskedOlmoEarthSample
            from olmoearth_pretrain.nn.pooling import PoolingType, pool_instance_wise

            mean = np.array([-11.648990747328444, -17.745436133270044])
            std = np.array([10.840350299936597, 10.216274681392647])
            x = standardize(v, mask, mean - 2 * std, 4 * std)
            sample = MaskedOlmoEarthSample(
                timestamps=torch.tensor([[[d.day, d.month - 1, d.year] for d in dates]]),
                sentinel1=tensor(x).permute(2, 3, 1, 0)[None],
                sentinel1_mask=torch.where(torch.from_numpy(mask), 0, 3).permute(1, 2, 0)[
                    None, :, :, :, None
                ],
            )
            return pool_instance_wise(
                m.encoder(sample, patch_size=4)["tokens_and_masks"], PoolingType.MEAN
            )
        if name == "prithvi":
            x = standardize(
                v * 10000,
                mask,
                [1087, 1342, 1433, 2734, 1958, 1363],
                [2248, 2179, 2178, 1850, 1242, 1049],
            )
            temporal = torch.tensor(
                [[[d.year, d.timetuple().tm_yday] for d in dates]], dtype=torch.float32
            )
            location = torch.tensor([[meta["latitude"], meta["longitude"]]], dtype=torch.float32)
            original = m.encoder.num_frames
            try:
                m.encoder.num_frames = nt
                return m.forward_features(tensor(x)[None], temporal, location)[-1][:, 1:].mean(1)
            finally:
                m.encoder.num_frames = original
        if name == "dofa":
            # Non-TCI Satlas bands have a documented exact DN // 32 conversion.
            # Do not approximate missing TCI RGB from physical reflectance.
            x = np.clip(np.floor(v[[3, 4, 5, 6, 8, 9]] / 32), 0, 255)
            x = standardize(
                x,
                mask,
                [84.33539309, 97.84789168, 103.94461911, 101.435633, 72.32804172, 56.66528851],
                [64.57022983, 61.72545487, 61.34187099, 60.29744676, 47.88519516, 42.55886798],
            )
            return m.forward_features(tensor(x)[None], [0.705, 0.740, 0.783, 0.842, 1.61, 2.19])
        if name == "copernicus_fm":
            models = json.loads((HERE / "config/limburg_eo_model_assets.json").read_text())[
                "models"
            ]
            norm = next(a for a in models if a["id"] == name)["input_contract"]["s2_normalization"]
            norm = [a for a in norm if a["band"] not in ("B01", "B09", "B10")]
            x = standardize(v, mask, [a["mean_DN"] for a in norm], [a["std_DN"] for a in norm])
            # Publisher's unknown-metadata encoding; retain real coordinates/dates in receipt.
            return m(
                tensor(x)[None],
                torch.full((1, 4), float("nan")),
                [a["wavelength_nm"] for a in norm],
                [a["bandwidth_nm"] for a in norm],
                None,
                "spectral",
                16,
            )[1]
        if name == "anysat":
            x = standardize(
                v,
                mask,
                [
                    4304.32958984375,
                    4159.2666015625,
                    4057.776611328125,
                    4328.951171875,
                    4571.22119140625,
                    4644.87109375,
                    4837.2470703125,
                    4700.2578125,
                    2823.264404296875,
                    2319.97021484375,
                ],
                [
                    3537.99755859375,
                    3324.23486328125,
                    3270.070068359375,
                    3250.530029296875,
                    2897.391357421875,
                    2754.4970703125,
                    2821.521484375,
                    2625.952392578125,
                    1731.56298828125,
                    1549.3028564453125,
                ],
            )
            return m(
                {
                    "s2": tensor(x).permute(1, 0, 2, 3)[None],
                    "s2_dates": torch.tensor([[d.timetuple().tm_yday - 1 for d in dates]]),
                },
                patch_size=20,
                output="tile",
            )
        if name == "terramind":
            x = standardize(
                v,
                mask,
                [
                    1503.317,
                    1718.197,
                    1853.91,
                    2199.1,
                    2779.975,
                    2987.011,
                    3083.234,
                    3132.22,
                    2424.884,
                    1857.648,
                ],
                [
                    2141.107,
                    2038.973,
                    2134.138,
                    2085.321,
                    1889.926,
                    1820.257,
                    1871.918,
                    1753.829,
                    1434.261,
                    1334.311,
                ],
            )
            out = m({"S2L2A": tensor(x)[None]})[-1]
            return out.mean(tuple(range(1, out.ndim - 1)))
        if name == "satmae":
            x = standardize(
                v,
                mask,
                [
                    1184.3824625,
                    1120.77120066,
                    1136.26026392,
                    1263.73947144,
                    1645.40315151,
                    1846.87040806,
                    1762.59530783,
                    1972.62420416,
                    1732.16362238,
                    1247.91870117,
                ],
                [
                    650.2842772,
                    712.12507725,
                    965.23119807,
                    948.9819932,
                    1108.06650639,
                    1258.36394548,
                    1233.1492281,
                    1364.38688993,
                    1310.36996126,
                    1087.6020813,
                ],
            )
            return m.forward_features(tensor(x)[None])
        if name == "galileo":
            norm = json.loads((ASSETS / "code/galileo/config/normalization.json").read_text())["13"]
            # Official std=True maps mean +/- 2 SD to [0, 1], without clipping.
            x = standardize(
                v,
                mask,
                np.array(norm["mean"][2:12]) - 2 * np.array(norm["std"][2:12]),
                np.array(norm["std"][2:12]) * 4,
            )
            h, w = mask.shape[-2:]
            st = torch.zeros(1, h, w, nt, 13)
            st[0, :, :, :, 2:12] = tensor(x).permute(2, 3, 1, 0)
            stm = torch.ones(1, h, w, nt, 7)
            stm[0, :, :, :, 1:6] = torch.from_numpy(~mask).permute(1, 2, 0)[:, :, :, None].float()
            out = m(
                st,
                torch.zeros(1, h, w, 16),
                torch.zeros(1, nt, 6),
                torch.zeros(1, 18),
                stm,
                torch.ones(1, h, w, 3),
                torch.ones(1, nt, 3),
                torch.ones(1, 4),
                torch.tensor([[d.month - 1 for d in dates]]),
                patch_size=8,  # Published max patch size; 32px -> 4x4 tokens, matching 12-frame training shape.
                input_resolution_m=10,
            )
            return m.average_tokens(*out[:8])
        if name == "presto":
            from presto import construct_batch_presto_input
            from rasterio.warp import transform

            union = mask.any(0)
            pixels = tensor(v.transpose(2, 3, 1, 0)[union])
            pixel_missing = ~mask[:, union].T
            rows, cols = np.nonzero(union)
            xmin, _, _, ymax = meta["bounds"]
            res = meta["resolution_m"]
            lons, lats = transform(
                meta["crs"],
                "EPSG:4326",
                (xmin + (cols + 0.5) * res).tolist(),
                (ymax - (rows + 0.5) * res).tolist(),
            )
            locations_all = np.asarray([lats, lons], dtype=np.float32).T
            results = []
            for offset, batch in enumerate(pixels.split(128)):
                x, missing, dw = construct_batch_presto_input(
                    s2=batch, s2_bands=meta["bands"], normalize=True
                )
                absent = torch.from_numpy(pixel_missing[offset * 128 : offset * 128 + len(batch)])
                missing[absent] = 1
                locations = tensor(locations_all[offset * 128 : offset * 128 + len(batch)])
                months = torch.tensor([[d.month - 1 for d in dates]]).repeat(len(batch), 1)
                results.append(
                    m.encoder(
                        x=x, mask=missing, dynamic_world=dw.long(), latlons=locations, month=months
                    )
                )
            return torch.cat(results).mean(0, keepdim=True)
        raise ValueError(name)
