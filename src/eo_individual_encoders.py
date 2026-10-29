"""Model-specific frozen outputs for the ten-part study, isolated per process.

Spatial maps are temporary. The caller immediately combines their weighted
moments and persists only catchment/context features and resumable tile totals.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from src.eo_encoder_corrections import ANYSAT_MEAN, ANYSAT_STD, croma_input, pixel_months
from src.eo_inputs import standardize
from src.eo_token_masks import token_observations

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "data/raw/limburg_dynamic_model_weights"
spec = importlib.util.spec_from_file_location(
    "individual_publisher_load", ROOT / "environments/eo-screen/check_load.py"
)
loaders = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loaders)


class IndividualEncoder:
    def __init__(self, name, device="cpu"):
        self.name = name
        self.device = torch.device(device)
        if device == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("MPS unavailable")
        torch.manual_seed(1729)
        self.model = loaders.build_model(name).to(self.device)
        if name == "prithvi":
            interpolate = self.model.encoder.interpolate_pos_encoding
            self.model.encoder.interpolate_pos_encoding = lambda shape: interpolate(shape).to(
                self.device
            )
        torch.set_num_threads(4 if name == "presto" and device == "cpu" else 2)
        self.norm = json.loads((ROOT / "config/limburg_eo_model_assets.json").read_text())

    def t(self, x):
        return torch.as_tensor(np.ascontiguousarray(x), device=self.device, dtype=torch.float32)

    def __call__(self, frames, physical=None):
        with torch.inference_mode(), torch.device(self.device):
            result = self.forward(frames, physical)
        for key, value in result.items():
            if key.endswith("_support"):
                continue
            if not np.isfinite(value).all():
                raise ValueError(f"Nonfinite encoder output: {self.name}/{key}")
        return result

    def forward(self, frames, physical=None):
        name, m = self.name, self.model
        valid = np.stack([p["valid"] for p in frames])
        v = np.stack([p["values"] for p in frames], axis=1)
        dates = [
            datetime.fromisoformat(
                p["metadata"]["representative_date"] or p["metadata"]["window"]["start"]
            )
            for p in frames
        ]
        nt = len(frames)
        meta = frames[0]["metadata"]

        def cpu(x):
            return x.detach().cpu().numpy().astype(np.float32)

        if name == "presto":
            from presto import construct_batch_presto_input
            from rasterio.warp import transform

            union = valid.any(0)
            h, w = union.shape
            pixels = self.t(v.transpose(2, 3, 1, 0)[union])
            months = pixel_months(frames, union)
            rows, cols = np.nonzero(union)
            x0, _, _, y1 = meta["bounds"]
            res = meta["resolution_m"]
            lon, lat = transform(
                meta["crs"],
                "EPSG:4326",
                (x0 + (cols + 0.5) * res).tolist(),
                (y1 - (rows + 0.5) * res).tolist(),
            )
            location = np.array([lat, lon], np.float32).T
            outputs = []
            for start in range(0, len(pixels), 128):
                x, missing, dw = construct_batch_presto_input(
                    s2=pixels[start : start + 128].cpu(), s2_bands=meta["bands"], normalize=True
                )
                missing[torch.from_numpy(~valid[:, union].T[start : start + 128])] = 1
                outputs.append(
                    cpu(
                        m.encoder(
                            x=x.to(self.device),
                            mask=missing.to(self.device),
                            dynamic_world=dw.long().to(self.device),
                            latlons=self.t(location[start : start + 128]),
                            month=torch.as_tensor(months[start : start + 128], device=self.device),
                        )
                    )
                )
            out = np.zeros((1, h, w, 128), np.float32)
            if outputs:
                out[0, union] = np.concatenate(outputs)
            return {"primary": out, "primary_support": union[None].astype(float)}
        if name == "anysat":
            keep = valid.any(axis=(1, 2))
            if not keep.any():
                raise ValueError("AnySat requires an observed frame")
            x = standardize(v[:, keep], valid[keep], ANYSAT_MEAN, ANYSAT_STD)
            kept_dates = [d for d, k in zip(dates, keep, strict=True) if k]
            tokens = m(
                {
                    "s2": self.t(x).permute(1, 0, 2, 3)[None],
                    "s2_dates": torch.tensor(
                        [[d.timetuple().tm_yday for d in kept_dates]], device=self.device
                    ),
                },
                patch_size=20,
                output="all",
            )
            n = tokens.shape[1] - 1
            grid = int(round(n**0.5))
            if grid * grid != n:
                raise ValueError("AnySat patch grid is not square")
            out = cpu(tokens[:, 1:].reshape(1, grid, grid, -1))
            return {
                "primary": out,
                "primary_support": valid.mean(0, keepdims=True),
                "ablation": cpu(tokens[:, 0]).reshape(1, 1, 1, -1),
                "ablation_support": valid.mean(0, keepdims=True),
            }
        if name == "prithvi":
            kept = np.flatnonzero(valid.any(axis=(1, 2)))
            if not len(kept):
                raise ValueError("Prithvi requires an observed frame")
            selected_dates = [dates[i] for i in kept]
            x = standardize(
                v[:, kept] * 10000,
                valid[kept],
                [1087, 1342, 1433, 2734, 1958, 1363],
                [2248, 2179, 2178, 1850, 1242, 1049],
            )
            temporal = self.t([[[d.year, d.timetuple().tm_yday] for d in selected_dates]])
            location = self.t([[meta["latitude"], meta["longitude"]]])
            original = m.encoder.num_frames
            m.encoder.num_frames = len(kept)
            try:
                tokens = m.forward_features(self.t(x)[None], temporal, location)[-1][:, 1:]
            finally:
                m.encoder.num_frames = original
            if tokens.shape[1] != len(kept) * 14 * 14:
                raise ValueError("Prithvi Tiny TL token layout changed")
            encoded = cpu(tokens.reshape(len(kept), 14, 14, -1))
            out = np.zeros((nt, 14, 14, encoded.shape[-1]), np.float32)
            out[kept] = encoded
            return {
                "primary": out,
                "primary_support": valid.astype(float),
                "ablation": out.mean((1, 2), keepdims=True),
                "ablation_support": valid.astype(float),
            }
        if name == "olmoearth":
            from olmoearth_pretrain.datatypes import MaskedOlmoEarthSample

            valid = token_observations(valid, 4)
            mean = np.array([-11.648990747328444, -17.745436133270044])
            sd = np.array([10.840350299936597, 10.216274681392647])
            x = standardize(v, valid, mean - 2 * sd, 4 * sd)
            sample = MaskedOlmoEarthSample(
                timestamps=torch.tensor(
                    [[[d.day, d.month - 1, d.year] for d in dates]], device=self.device
                ),
                sentinel1=self.t(x).permute(2, 3, 1, 0)[None],
                sentinel1_mask=torch.where(
                    torch.as_tensor(valid, device=self.device), 0, 3
                ).permute(1, 2, 0)[None, :, :, :, None],
            )
            out = m.encoder(sample, patch_size=4)["tokens_and_masks"]
            features = out.sentinel1[0]
            if features.ndim != 5:
                raise ValueError("OlmoEarth native BHWTSD shape changed")
            features = features.mean(dim=3).permute(2, 0, 1, 3)
            return {"primary": cpu(features), "primary_support": valid.astype(float)}
        if name == "galileo":
            if physical is None:
                raise ValueError("Galileo physical inputs required")
            norm = json.loads((ASSETS / "code/galileo/config/normalization.json").read_text())
            valid = token_observations(valid, 8)
            h, w = valid.shape[-2:]
            optical = standardize(
                v,
                valid,
                np.array(norm["13"]["mean"][2:12]) - 2 * np.array(norm["13"]["std"][2:12]),
                4 * np.array(norm["13"]["std"][2:12]),
            )
            st = torch.zeros(1, h, w, nt, 13, device=self.device)
            st[0, :, :, :, 2:12] = self.t(optical).permute(2, 3, 1, 0)
            stm = torch.ones(1, h, w, nt, 7, device=self.device)
            stm[0, :, :, :, 1:6] = self.t(~valid).permute(1, 2, 0)[:, :, :, None]
            terrain = physical["terrain"]
            terrain_valid = np.isfinite(terrain).all(0)
            sp = torch.zeros(1, h, w, 16, device=self.device)
            spm = torch.ones(1, h, w, 3, device=self.device)
            sp[0, :, :, :2] = self.t(
                standardize(
                    terrain,
                    terrain_valid,
                    np.array(norm["16"]["mean"][:2]) - 2 * np.array(norm["16"]["std"][:2]),
                    4 * np.array(norm["16"]["std"][:2]),
                )
            ).permute(1, 2, 0)
            spm[0, :, :, 0] = self.t(~terrain_valid)
            climate = physical["climate"]
            climate_valid = np.isfinite(climate).all(1)
            tx = torch.zeros(1, nt, 6, device=self.device)
            tm = torch.ones(1, nt, 3, device=self.device)
            a = np.array(norm["6"]["mean"][:2])
            b = np.array(norm["6"]["std"][:2])
            tx[0, :, :2] = self.t(
                np.where(climate_valid[:, None], (climate - (a - 2 * b)) / (4 * b), 0)
            )
            tm[0, :, 0] = self.t(~climate_valid)
            static = torch.zeros(1, 18, device=self.device)
            static_mask = torch.ones(1, 4, device=self.device)
            months = torch.tensor([[d.month - 1 for d in dates]], device=self.device)
            out = m(
                st,
                sp,
                tx,
                static,
                stm,
                spm,
                tm,
                static_mask,
                months,
                patch_size=8,
                input_resolution_m=10,
            )
            primary = cpu(m.average_tokens(*out[:8])).reshape(1, 1, 1, -1)
            support = (valid.any(0) | terrain_valid)[None].astype(float)
            result = {"primary": primary, "primary_support": support}
            if valid.any():
                alt = m(
                    st,
                    torch.zeros_like(sp),
                    torch.zeros_like(tx),
                    static,
                    stm,
                    torch.ones_like(spm),
                    torch.ones_like(tm),
                    static_mask,
                    months,
                    patch_size=8,
                    input_resolution_m=10,
                )
                result.update(
                    ablation=cpu(m.average_tokens(*alt[:8])).reshape(1, 1, 1, -1),
                    ablation_support=valid.mean(0, keepdims=True),
                    paired_primary=primary.copy(),
                    paired_primary_support=valid.mean(0, keepdims=True),
                )
            return result
        outputs = []
        alternatives = []
        used_valid = valid.copy()
        for patch in frames:
            values, mask = patch["values"], patch["valid"]
            md = patch["metadata"]
            if not mask.any() or (
                name == "croma" and (mask.sum() < 2 or np.any(values[:, mask].std(1) <= 0))
            ):
                dim = {"croma": 768, "terramind": 192, "copernicus_fm": 768}[name]
                outputs.append(np.zeros(dim, np.float32))
                used_valid[len(outputs) - 1] = False
                if name == "copernicus_fm":
                    alternatives.append(np.zeros(dim, np.float32))
                continue
            if name == "croma":
                out = m(SAR_images=self.t(croma_input(values, mask))[None])["SAR_GAP"]
            elif name == "terramind":
                x = standardize(
                    values,
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
                features = m({"S2L2A": self.t(x)[None]})[-1]
                out = features.mean(tuple(range(1, features.ndim - 1)))
            elif name == "copernicus_fm":
                norm = next(a for a in self.norm["models"] if a["id"] == name)["input_contract"][
                    "s2_normalization"
                ]
                norm = [a for a in norm if a["band"] not in ("B01", "B09", "B10")]
                x = standardize(
                    values, mask, [a["mean_DN"] for a in norm], [a["std_DN"] for a in norm]
                )
                day = (
                    datetime.fromisoformat(md["representative_date"])
                    - datetime(
                        1970, 1, 1, tzinfo=datetime.fromisoformat(md["representative_date"]).tzinfo
                    )
                ).total_seconds() / 86400
                metadata = self.t(
                    [
                        [
                            md["longitude"],
                            md["latitude"],
                            day,
                            (16 * md["resolution_m"] / 1000) ** 2,
                        ],
                        [np.nan] * 4,
                    ]
                )
                out = m(
                    self.t(x)[None].repeat(2, 1, 1, 1),
                    metadata,
                    [a["wavelength_nm"] for a in norm],
                    [a["bandwidth_nm"] for a in norm],
                    None,
                    "spectral",
                    16,
                )[1]
                alternatives.append(cpu(out[1]))
                out = out[:1]
            else:
                raise ValueError(f"Unsupported fresh extraction: {name}")
            outputs.append(cpu(out).reshape(-1))
        result = {
            "primary": np.stack(outputs)[:, None, None, :],
            "primary_support": used_valid.astype(float),
        }
        if alternatives:
            result.update(
                ablation=np.stack(alternatives)[:, None, None, :],
                ablation_support=used_valid.astype(float),
            )
        return result
