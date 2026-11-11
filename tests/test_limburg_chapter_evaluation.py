import numpy as np
from rasterio.transform import from_origin

from limburg_chapter_evaluation import remove_prior_coverage


def test_overlap_ownership_keeps_prior_holes_and_support_bits():
    grid = from_origin(500000, 5700000, 10, 10)
    current = np.full((2, 3), 15, dtype=np.uint8)
    prior = np.array([[15, 1, 0], [8, 0, 2]], dtype=np.uint8)
    result = remove_prior_coverage(current, grid, "EPSG:32631", [(prior, grid, "EPSG:32631")])
    assert result.tolist() == [[0, 14, 15], [7, 15, 13]]


def test_overlap_ownership_uses_map_coordinates():
    grid = from_origin(500000, 5700000, 10, 10)
    old_grid = from_origin(500020, 5700000, 10, 10)
    result = remove_prior_coverage(
        np.ones((2, 3), dtype=np.uint8),
        grid,
        "EPSG:32631",
        [(np.ones((2, 3), dtype=np.uint8), old_grid, "EPSG:32631")],
    )
    assert result.tolist() == [[1, 1, 0], [1, 1, 0]]
