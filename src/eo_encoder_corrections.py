"""Versioned publisher-input corrections; historical encoder source stays frozen.

Only the new extraction entry point installs these corrections. No learned
parameter, exposure selection, donor rule or output pooling is changed.
"""

from datetime import datetime

import numpy as np
import torch

from src.eo_inputs import standardize

VERSION = "publisher_inputs_2026_10_22_v1"
SATMAE_MEAN = np.array(
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
    ]
)
SATMAE_STD = np.array(
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
    ]
)
ANYSAT_MEAN = [
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
]
ANYSAT_STD = [
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
]


def satmae_input(values, valid):
    """Pinned SentinelNormalize -> uint8 -> ToTensor, without training crops."""
    low = (SATMAE_MEAN - 2 * SATMAE_STD)[:, None, None]
    width = (4 * SATMAE_STD)[:, None, None]
    filled = np.where(valid[None], values, SATMAE_MEAN[:, None, None])
    return np.clip((filled - low) / width * 255, 0, 255).astype(np.uint8).astype(np.float32) / 255


def croma_input(values, valid):
    """Publisher eight-bit SAR stretch and final /255 over observed support."""
    observed = torch.from_numpy(np.ascontiguousarray(values[:, valid])).float()
    if observed.shape[1] < 2:
        raise ValueError("CROMA sample SD requires at least two observed pixels")
    # Use the publisher's float32 torch sample-SD convention (default correction=1).
    mean = observed.mean(1).numpy()
    std = observed.std(1).numpy()
    if np.any(std <= 0) or not np.isfinite(std).all():
        raise ValueError("CROMA contrast stretch undefined for constant observed channel")
    low, high = mean - 2 * std, mean + 2 * std
    x = np.clip((values - low[:, None, None]) / (high - low)[:, None, None] * 255, 0, 255)
    x[:, ~valid] = 127
    return x.astype(np.uint8).astype(np.float32) / 255


def pixel_months(frames, union):
    """Zero-based actual pixel acquisition months; ignored slots use masked zero."""
    result = []
    for frame in frames:
        valid = frame["valid"][union]
        days = frame["days"][union]
        if not np.isfinite(days[valid]).all():
            raise ValueError("Observed Presto pixel lacks its acquisition day")
        months = np.zeros(len(days), dtype=np.int64)
        calendar_days = days[valid].astype("datetime64[D]")
        if np.isnat(calendar_days).any():
            raise ValueError("Observed Presto pixel lacks its acquisition day")
        calendar = calendar_days.astype("datetime64[M]").astype(np.int64)
        months[valid] = calendar % 12
        result.append(months)
    return np.stack(result, axis=1)


def install(module):
    """Install into the CPU or existing MPS module before constructing an encoder."""
    if getattr(module.Encoder, "input_corrections", None) == VERSION:
        return
    original = module.Encoder.forward

    def forward(self, patch):
        name, model = self.name, self.model
        values, valid = patch["values"], patch["valid"]
        if name == "croma":
            return model(SAR_images=module.tensor(croma_input(values, valid))[None])["SAR_GAP"]
        if name == "satmae":
            return model.forward_features(module.tensor(satmae_input(values, valid))[None])
        if name == "anysat":
            frames = patch.get("frames", [patch])
            x = standardize(
                np.stack([p["values"] for p in frames], axis=1),
                np.stack([p["valid"] for p in frames]),
                ANYSAT_MEAN,
                ANYSAT_STD,
            )
            dates = [datetime.fromisoformat(p["metadata"]["representative_date"]) for p in frames]
            return model(
                {
                    "s2": module.tensor(x).permute(1, 0, 2, 3)[None],
                    # Match the pinned demo/dated training loaders, including day 366.
                    "s2_dates": torch.tensor([[d.timetuple().tm_yday for d in dates]]),
                },
                patch_size=20,
                output="tile",
            )
        if name == "presto":
            from presto import construct_batch_presto_input
            from rasterio.warp import transform

            frames = patch.get("frames", [patch])
            values = np.stack([p["values"] for p in frames], axis=1)
            valid = np.stack([p["valid"] for p in frames])
            union = valid.any(0)
            pixels = module.tensor(values.transpose(2, 3, 1, 0)[union])
            missing_pixels = ~valid[:, union].T
            months = pixel_months(frames, union)
            meta = patch["metadata"]
            rows, cols = np.nonzero(union)
            xmin, _, _, ymax = meta["bounds"]
            resolution = meta["resolution_m"]
            lons, lats = transform(
                meta["crs"],
                "EPSG:4326",
                (xmin + (cols + 0.5) * resolution).tolist(),
                (ymax - (rows + 0.5) * resolution).tolist(),
            )
            locations = np.asarray([lats, lons], dtype=np.float32).T
            outputs = []
            for offset, batch in enumerate(pixels.split(128)):
                start, stop = offset * 128, offset * 128 + len(batch)
                x, missing, dw = construct_batch_presto_input(
                    s2=batch, s2_bands=meta["bands"], normalize=True
                )
                missing[torch.from_numpy(missing_pixels[start:stop])] = 1
                outputs.append(
                    model.encoder(
                        x=x,
                        mask=missing,
                        dynamic_world=dw.long(),
                        latlons=module.tensor(locations[start:stop]),
                        month=torch.from_numpy(months[start:stop]),
                    )
                )
            return torch.cat(outputs).mean(0, keepdim=True)
        return original(self, patch)

    module.Encoder.forward = forward
    module.Encoder.input_corrections = VERSION
