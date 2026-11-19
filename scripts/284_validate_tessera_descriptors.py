"""Export and validate the full TESSERA descriptor receipt as a quoted CSV."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results/limburg_representation_extension_v1/tessera_census_v1"
RECEIPT = OUTPUT / "receipt_2018_direct.json"
COVERAGE = ROOT / "results/limburg_representation_extension_v1/tessera_coverage_v1/receipt_2018_direct.json"
CSV_PATH = OUTPUT / "descriptors_2018.csv"
MANIFEST_PATH = OUTPUT / "validation_2018.json"
BANDS = 128


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    receipt = json.loads(RECEIPT.read_text())
    coverage = json.loads(COVERAGE.read_text())
    basins = receipt["basins"]
    if receipt["status"] != "complete" or receipt["coverage_only"]:
        raise ValueError("The descriptor extraction receipt is not complete")
    if receipt["snapshot_id"] != coverage["snapshot_id"] or receipt["year"] != 2018:
        raise ValueError("Coverage and descriptor receipts do not share the frozen source/year")
    if len(basins) != 394 or len(coverage["basins"]) != 394:
        raise ValueError("Expected the complete 394-catchment census")

    columns = [f"tessera_{index:03d}" for index in range(BANDS)]
    temporary = CSV_PATH.with_suffix(".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gauge", "station", "role", "coverage_fraction", "valid_pixel_count", *columns])
        for gauge, basin in sorted(basins.items()):
            vector = np.asarray(basin["mean"], dtype=np.float64)
            if vector.shape != (BANDS,) or not np.isfinite(vector).all():
                raise ValueError(f"Invalid 128-value descriptor for {gauge}")
            if abs(basin["coverage_fraction"] - coverage["basins"][gauge]["coverage_fraction"]) > 1e-12:
                raise ValueError(f"Coverage does not match the scale-only census for {gauge}")
            writer.writerow(
                [
                    gauge,
                    basin["station"],
                    basin["role"],
                    format(basin["coverage_fraction"], ".17g"),
                    basin["valid_pixel_count"],
                    *(format(float(value), ".17g") for value in vector),
                ]
            )
    temporary.replace(CSV_PATH)

    max_abs_delta = 0.0
    with CSV_PATH.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 394 or len({row["gauge"] for row in rows}) != 394:
        raise ValueError("CSV row count or gauge uniqueness failed")
    for row in rows:
        basin = basins[row["gauge"]]
        saved = np.asarray([float(row[column]) for column in columns])
        max_abs_delta = max(max_abs_delta, float(np.max(np.abs(saved - basin["mean"]))))
    if max_abs_delta > 1e-12:
        raise ValueError(f"CSV values differ from receipt by {max_abs_delta}")

    manifest = {
        "status": "validated",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "rows": len(rows),
        "feature_dimensions": BANDS,
        "max_abs_delta_csv_vs_receipt": max_abs_delta,
        "receipt_sha256": sha256(RECEIPT),
        "coverage_receipt_sha256": sha256(COVERAGE),
        "csv_sha256": sha256(CSV_PATH),
        "exporter_sha256": sha256(Path(__file__)),
        "station_names_csv_quoted": True,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
