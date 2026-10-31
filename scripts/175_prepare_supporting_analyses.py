"""Freeze held supporting inputs and work contracts; never submit computation."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_supporting_controls import saved_combined_profiles


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prep = ROOT / "results/limburg_scarcity_v2_2026_10_28/preparation"
    land = ROOT / "data/raw/limburg_monitoring_land_state"
    acquired = json.loads((land / "manifest.json").read_text())
    assert acquired["status"] == "completed" and acquired["completed_months"] == 204
    hashes = {}
    paths = [prep / name for name in ["groups.json", "block_12h_50pct.npy", "source_epoch_hours.npy", "manifest.json"]]
    paths += [land / "manifest.json", ROOT / "src/eo_supporting_controls.py", Path(__file__)]
    receipts = sorted(land.glob("*.receipt.json"))
    assert len(receipts) == 204
    for receipt in receipts:
        record = json.loads(receipt.read_text())
        path = receipt.with_name(receipt.name.replace(".receipt.json", ".nc"))
        assert digest(path) == record["sha256"], path
        paths.extend([receipt, path])
    for path in paths:
        hashes[str(path.relative_to(ROOT))] = digest(path)
    profiles = saved_combined_profiles(json.loads((prep / "groups.json").read_text()))
    plan = dict(
        status="prepared_not_submitted_not_a_fit_runner",
        protected_primary_queue="unchanged; finish and audit primary jobs before supporting refits",
        source_hashes=hashes, saved_combined_profiles=profiles,
        jobs=[
            dict(name="soil_snow", fields=["swvl1", "swvl2", "sd"],
                 readiness="204 receipts and source checksums verified; causal join helper tested",
                 remaining="Area-weight native ERA5-Land cells to each existing catchment; preserve source coverage; join strictly prior hourly states; expose identical controls to raw and encoder heads; refit chronologically in versioned outputs",
                 interpretation="Retrospective physical-state control, not as-issued input; no substitution for Galileo TerraClimate channels"),
            dict(name="combined_profiles", readiness="Exact saved subsets, phases, mask and clock hashes retained",
                 remaining="Adapt both common context and conventional references to each saved realization; fit each head on the same scenario; reuse shared year and mask resampling; DOFA retains held-watercourse exclusions",
                 interpretation="420 exact network/schedule combinations and 100 saved network/block realizations; not frozen-head replay or a new severity search"),
            dict(name="encoder_without_raw_attribution", readiness="Supporting arm specified",
                 remaining="Use same allowed common context and frozen C reference, omit model-specific raw block only; retain zero encoder choice, chronological tuning and matched support",
                 interpretation="C+E attribution, not the primary equal-input C+R+E versus C+R test"),
            dict(name="satmae_product", readiness="Product-and-support sensitivity specified; paired acquisition inventory pending",
                 remaining="Match SR and TOA acquisitions, bands, pixel/patch acceptance and temporal support; derive raw controls from each exact input; use declared checkpoint normalization; version all outputs",
                 interpretation="Report common-support comparison separately; unmatched differences confound product and support"),
        ],
        safeguards=["No new acquisition authorized by this preparation", "No extraction or fitting launched", "Do not alter active source hashes", "Do not select severity or configuration by observed improvements", "Use full eligible census and report missing support"],
    )
    dest = ROOT / "config/limburg_individual_supporting_prepared_2026_10_31.json"
    text = json.dumps(plan, indent=2) + "\n"
    if dest.exists() and dest.read_text() != text:
        raise RuntimeError("Preserve existing preparation; choose a versioned destination")
    dest.write_text(text)
    print(f"Prepared {len(plan['jobs'])} supporting work contracts; verified {len(receipts)} monthly files; launched nothing")


if __name__ == "__main__":
    main()
