"""Content-addressed cache of unchanged analogue retrievals, never of new scores."""

import hashlib
import json
from pathlib import Path

import pandas as pd

from src.eo_inputs import sha256
from src.eo_integrity import fresh_output

ROOT = Path(__file__).resolve().parents[1]


def frame_digest(frame):
    h = hashlib.sha256()
    schema = [(str(c), str(t)) for c, t in zip(frame.columns, frame.dtypes, strict=True)]
    h.update(
        json.dumps({"columns": schema, "index_names": frame.index.names}, default=str).encode()
    )
    h.update(pd.util.hash_pandas_object(frame, index=True).to_numpy().tobytes())
    return h.hexdigest()


class RetrievalCache:
    def __init__(self, folder, retrieve):
        self.folder = Path(folder)
        self.retrieve = retrieve
        self.hits = self.misses = 0
        self.code = {
            name: sha256(ROOT / name)
            for name in [
                "scripts/65_hydrological_analogue_baseline.py",
                "scripts/64_build_basin_ai_event_library.py",
                "src/eo_comparison.py",
                "src/eo_retrieval_cache.py",
            ]
        }

    def __call__(self, sample, blocks=None, **options):
        spec = {
            "sample": frame_digest(sample),
            "blocks": None
            if blocks is None
            else {name: frame_digest(frame) for name, frame in sorted(blocks.items())},
            "options": options,
            "code": self.code,
        }
        key = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
        target = self.folder / key
        receipt = target / "manifest.json"
        if receipt.exists():
            saved = json.loads(receipt.read_text())
            if saved["identity"] != spec or any(
                sha256(target / name) != digest for name, digest in saved["outputs_sha256"].items()
            ):
                raise ValueError("Retrieval cache content differs from receipt")
            self.hits += 1
            return pd.read_parquet(target / "predictions.parquet"), pd.read_parquet(
                target / "donors.parquet"
            )
        predictions, donors = self.retrieve(sample, blocks, **options)
        with fresh_output(target) as stage:
            predictions.to_parquet(stage / "predictions.parquet", index=False)
            donors.to_parquet(stage / "donors.parquet", index=False)
            saved = {
                "identity": spec,
                "outputs_sha256": {p.name: sha256(p) for p in stage.glob("*.parquet")},
            }
            (stage / "manifest.json").write_text(json.dumps(saved, indent=2) + "\n")
        self.misses += 1
        return predictions, donors
