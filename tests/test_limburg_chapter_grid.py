from datetime import datetime, timezone

import numpy as np
import pytest
from rasterio.transform import from_origin

from limburg_chapter_grid import patch_metadata, stitch_probabilities, windows


def test_native_1024_grid_has_complete_25_window_coverage():
    cells = windows(1024, 1024)
    assert len(cells) == 25
    prediction = np.broadcast_to(np.array([0.1, 0.2, 0.7], dtype=np.float32)[:, None, None], (3, 224, 224))
    pieces = [(top, left, prediction)
              for top, left in cells]
    result, valid = stitch_probabilities(pieces, 1024, 1024)
    assert valid.all()
    assert np.allclose(result[:, 0, 0], [0.1, 0.2, 0.7])
    assert np.allclose(result[:, 800:824, 800:824], np.array([0.1, 0.2, 0.7])[:, None, None])


def test_unknown_pixels_and_invalid_patch_are_not_dry():
    x = np.full((3, 2, 2), 1 / 3, dtype=np.float32)
    x[:, 0, 1] = np.nan
    out, valid = stitch_probabilities([(0, 0, x)], 2, 2)
    assert not valid[0, 1]
    assert np.isnan(out[:, 0, 1]).all()
    with pytest.raises(ValueError):
        stitch_probabilities([(1, 1, x)], 2, 2)


def test_patch_metadata_changes_with_location_and_pre_date():
    grid = from_origin(5.0, 51.0, 0.0001, 0.0001)
    pre = datetime(2026, 1, 1, tzinfo=timezone.utc)
    post = datetime(2026, 1, 10, tzinfo=timezone.utc)
    a = patch_metadata(grid, "EPSG:4326", 0, 0, 224, pre, post)
    b = patch_metadata(grid, "EPSG:4326", 200, 200, 224, pre, post)
    assert a[0, 0] != b[0, 0]
    assert a[0, 2] + 9 == a[1, 2]
    assert a[0, 3] == pytest.approx(0.0256)
