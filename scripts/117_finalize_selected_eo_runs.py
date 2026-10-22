"""Check or merge explicitly selected EO runs; no newest-run substitution or scoring."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES
from src.eo_integrity import merge_selected, selected_aggregates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--selection", type=Path, default=ROOT / "config/limburg_eo_selected_runs.json"
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "results/eo_catchment_representations/selected/census"
    )
    parser.add_argument("--merge", action="store_true")
    parser.add_argument(
        "--available-only",
        action="store_true",
        help="Explicit separate partial merge of verified completed models; never claim all ten",
    )
    args = parser.parse_args()
    selection = json.loads(args.selection.read_text())
    if set(selection["models"]) != set(ROUTES):
        raise ValueError("Selection must account for all ten configured models")
    if args.available_only:
        if args.out == ROOT / "results/eo_catchment_representations/selected/census":
            args.out = ROOT / "results/eo_catchment_representations/available/census"
    if args.merge:
        merge_selected(ROOT, selection, args.out, available_only=args.available_only)
        print(json.dumps({"status": "merged_selected_runs", "output": str(args.out)}))
    else:
        _, readiness = selected_aggregates(ROOT, selection)
        out = ROOT / "logs/eo-selected-readiness.json"
        out.write_text(json.dumps(readiness, indent=2) + "\n")
        print(json.dumps(readiness, indent=2))
        return int(any(r["status"] == "invalid" for r in readiness.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
