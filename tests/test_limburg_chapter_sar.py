from datetime import datetime

import numpy as np
import pytest

from limburg_chapter_sar import SARScene, raw_sar_db, updated_reference


def scene(name, day, *, orbit=20, process="sigma0-grd-v1", platform="S1A", coverage=True):
    return SARScene(name, datetime(2026, 1, day), platform, orbit, "ASC", process, coverage)


def test_updated_reference_uses_metadata_and_preserves_delivered_fallback():
    delivered = scene("p0", 1)
    candidates = [
        scene("old", 2), scene("new", 5), scene("wrong-orbit", 6, orbit=21),
        scene("wrong-processing", 7, process="sigma0-rtc-v1"),
        scene("partial", 8, coverage=False), scene("after", 10),
    ]
    assert updated_reference(delivered, candidates, datetime(2026, 1, 9)).scene_id == "new"
    assert updated_reference(delivered, [], datetime(2026, 1, 9)) == delivered
    with pytest.raises(ValueError):
        updated_reference(scene("late", 10), [], datetime(2026, 1, 9))


def test_physical_input_keeps_raw_dynamic_range_and_invalid_pixels_unknown():
    x = np.full((4, 2, 2), 0.2, dtype=np.float32)
    x[:, 0, 1] = 0
    x[0, 1, 0] = np.nan
    db, valid = raw_sar_db(x)
    assert db[0, 0, 0] == pytest.approx(10 * np.log10(0.2))
    assert valid.tolist() == [[True, False], [False, True]]
    assert np.isnan(db[:, 0, 1]).all()
