import runpy
from pathlib import Path

import pytest

M = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/114_expand_limburg_eo_acquisition.py")
)


def test_sar_passes_remain_separate_and_existing_route_is_not_duplicated():
    def record(direction, orbit):
        return {
            "source": "s1",
            "properties": {"orbitProperties_pass": direction, "relativeOrbitNumber_start": orbit},
        }

    assert M["route"](record("ASCENDING", 88)) == []
    assert M["route"](record("DESCENDING", 37))[0][0] == "s1_descending_37"
    assert M["route"](record("ASCENDING", 15))[0][0] == "s1_ascending_15"
    with pytest.raises(ValueError):
        M["route"](record(None, None))


def test_optical_calibration_and_quality_products_cannot_silently_replace_sr():
    routes = M["route"]({"source": "s2_toa"})
    assert {r[0] for r in routes} == {"s2_toa_10m", "s2_toa_20m", "s2_toa_qa60"}
    assert next(r for r in routes if r[0].endswith("qa60"))[2] == 60
    assert all("s2_sr" not in r[0] for r in routes)
    old = M["route"]({"source": "landsat7"})[0]
    assert old[0] == "landsat7_sr" and old[2] == 30 and old[3] == "float32"
    assert {"QA_PIXEL", "QA_RADSAT", "sensor_id", "acquired_day"} <= set(old[1])
    assert M["LANDSAT_BANDS"]["old"] != M["LANDSAT_BANDS"]["new"]
