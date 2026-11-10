"""Verified primary/gap-recovery archive view without copying any imagery."""

from __future__ import annotations

import json
from pathlib import Path

from src import eo_coherent_inputs, eo_expansion_inputs, eo_inputs
from src.eo_token_masks import token_observations

_READ_PRODUCT = eo_inputs.read_product
_SHA256 = eo_inputs.sha256


class Archive:
    def __init__(self, root, model):
        self.root = Path(root)
        self.model = model
        self.index = {}
        self.verified = {}
        self.inputs = {}
        self.current_inputs = {}
        if model == "satmae":
            roots = [
                (self.root / "data/processed/eo_expansion_input_views/satmae_toa_qa60", "jobs.json")
            ]
        else:
            roots = [(self.root / "data/raw/limburg_compact_eo", "jobs.json")]
            if model != "dofa":
                roots.append(
                    (
                        self.root / "data/raw/limburg_monitoring_eo",
                        str(
                            self.root
                            / "results/monitoring_acquisition_2026_10_28/eo-new-window-jobs.json"
                        ),
                    )
                )
        self.catalogues = []
        for archive, catalogue in roots:
            p = archive / catalogue
            self.catalogues.append(p)
            needed = (
                {"hls"}
                if model == "prithvi"
                else {"s1_ascending"}
                if model in {"croma", "olmoearth"}
                else {"s2_10m", "s2_20m", "s2_toa_qa60"}
            )
            for original in json.loads(p.read_text()):
                if original["product"] not in needed:
                    continue
                job = original.copy()
                path = archive / job["relative_path"]
                receipt = path.with_suffix(".receipt.json")
                present = path.exists() and receipt.exists()
                if present:
                    r = json.loads(receipt.read_text())
                    for k in ("asset_ids", "acquisition_ms", "source_metadata"):
                        if k not in job:
                            job[k] = r.get(k, [])
                job["_archive"] = str(archive)
                job["_present"] = present
                key = (job["window"]["id"], tuple(job["bounds"]), job["product"])
                if key not in self.index or (not self.index[key]["_present"] and present):
                    self.index[key] = job
        self.original_read = _READ_PRODUCT
        # Isolated worker only: alias all maintained loaders to this root-aware
        # verifier. A stat-bound cache avoids rehashing immutable tiles 12 times.
        self.original_sha = _SHA256
        eo_inputs.read_product = self.read_product
        eo_coherent_inputs.read_product = self.read_product
        eo_expansion_inputs.read_product = self.read_product
        eo_inputs.sha256 = self.cached_sha

    def cached_sha(self, path):
        path = Path(path)
        stat = path.stat()
        key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
        if key not in self.verified:
            self.verified[key] = self.original_sha(path)
        return self.verified[key]

    def read_product(self, root, job):
        archive = Path(job.get("_archive", root))
        if job["product"] == "s1_ascending":
            orbits = {
                m["relativeOrbitNumber_start"]
                for m in job.get("source_metadata", [])
                if "relativeOrbitNumber_start" in m
            }
            if (orbits and orbits != {88}) or job.get("orbit", 88) != 88:
                raise ValueError("Primary SAR orbit mismatch")
        result = self.original_read(archive, job)
        key = str((archive / job["relative_path"]).relative_to(self.root))
        self.inputs[key] = result[-1]["sha256"]
        self.current_inputs[key] = result[-1]["sha256"]
        return result

    def tile(self, window, bounds, product):
        key = (window["id"], tuple(bounds), product)
        job = self.index.get(key)
        if not job or not job["_present"]:
            return None
        if product == "s2_10m":
            required = ["s2_20m"] + (["s2_toa_qa60"] if self.model == "satmae" else [])
            if any(
                not self.index.get((window["id"], tuple(bounds), p), {}).get("_present")
                for p in required
            ):
                return None
        loader = (
            eo_expansion_inputs.read_coherent_tile
            if self.model == "satmae"
            else eo_coherent_inputs.read_coherent_tile
        )
        tile = loader(Path(job["_archive"]), job, self.index)
        if self.model in {"galileo", "olmoearth"}:
            original_count = int(tile.valid.sum())
            tile.valid = token_observations(tile.valid, 8 if self.model == "galileo" else 4)
            for source in tile.sources:
                source["native_mask_pixels_removed"] = original_count - int(tile.valid.sum())
                source["native_mask_policy"] = "all_pixels_observed_in_native_token"
        return tile
