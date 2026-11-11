import numpy as np

from limburg_chapter_scores import paired_support, score_tile


def test_flood_errors_and_unknown_are_separate():
    label = np.array([[2, 2, 1, 0, 255]], dtype=np.uint8)
    prediction = np.array([[2, 1, 2, 2, 2]], dtype=np.uint8)
    result = score_tile(label, prediction, np.ones_like(label, dtype=bool))
    assert result["known_pixels"] == 4
    assert result["flood_iou"] == 1 / 4
    assert result["permanent_as_flood_pixels"] == 1
    assert result["flood_as_permanent_pixels"] == 1
    assert result["false_flood_km2"] == 0.0002
    assert result["missed_flood_km2"] == 0.0001


def test_no_flood_iou_is_undefined_unless_false_alarm():
    label = np.array([[0, 1]], dtype=np.uint8)
    assert score_tile(label, label, np.array([[True, True]]))["flood_iou"] is None
    assert score_tile(label, np.array([[2, 1]]), np.array([[True, True]]))["flood_iou"] == 0.0
    assert paired_support(label, np.array([[True, True]]), np.array([[False, True]])).tolist() == [[False, True]]
