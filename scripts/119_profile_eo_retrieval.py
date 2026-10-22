"""Profile one real full-cohort retrieval and verify exact cache equivalence.

Engineering throughput only, no new scientific model score or event sample.
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_comparison import retrieve
from src.eo_retrieval_cache import RetrievalCache


def main():
    ready = ROOT / "results/basin_ai_event_interpretation_ready"
    sample = pd.read_csv(ready / "q_only_signatures.csv", parse_dates=["onset_utc"])
    meta = pd.read_csv(ready / "event_inventory.csv").set_index("event_id")
    for key in ["country", "physical_river_group"]:
        sample[key] = sample.event_id.map(meta[key])
    blocks = {
        "temporal": pd.read_parquet(ready / "q_only_ttm_ordered.parquet"),
        "state": pd.read_parquet(ready / "q_only_discharge_state.parquet"),
    }
    ids = set.intersection(*(set(frame.index) for frame in blocks.values()))
    sample = sample[sample.complete_scoring_sample & sample.event_id.isin(ids)].copy()
    cache = RetrievalCache(ROOT / "logs/eo-profile-cache", retrieve)
    started = time.perf_counter()
    first = cache(sample, blocks, exclude_same_river=False, quality=False, policy="pooled")
    first_seconds = time.perf_counter() - started
    started = time.perf_counter()
    second = cache(sample, blocks, exclude_same_river=False, quality=False, policy="pooled")
    hit_seconds = time.perf_counter() - started
    for a, b in zip(first, second, strict=True):
        pd.testing.assert_frame_equal(a, b)
    result = {
        "events": len(sample),
        "queries": len(first[0]),
        "donor_rows": len(first[1]),
        "first_call_seconds": first_seconds,
        "cache_hit_seconds": hit_seconds,
        "cache_hits": cache.hits,
        "cache_misses": cache.misses,
        "exact_equivalence": True,
        "scope": "One full eligible TTM/state cohort, pooled main all-river retrieval. Not an extrapolated total runtime or EO result.",
    }
    (ROOT / "logs/eo-retrieval-profile.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
