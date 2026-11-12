import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/252_summarize_event_review.py"
    spec = importlib.util.spec_from_file_location("event_explanation", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_flood_to_permanent_loses_flood_accuracy_but_keeps_water_detection():
    row = {f"c{i}{j}": 0 for i in range(3) for j in range(3)}
    row.update(c00=1, c11=1, c21=1)
    result = module().add_water_metrics(pd.DataFrame([row])).iloc[0]
    assert result.water_iou == 1
    assert result.flood_recall == 0
    assert result.flood_as_permanent_fraction == 1


def test_gain_and_two_loss_routes_reconstruct_net_detection_change():
    row = {f"y{y}_p0{i}_p1{j}": 0 for y in range(3) for i in range(3) for j in range(3)}
    row.update(y2_p02_p12=5, y2_p02_p11=3, y2_p02_p10=1, y2_p00_p12=2)
    result = module().transition_metrics(pd.DataFrame([row])).iloc[0]
    assert result.old_flood_tp == 9
    assert result.new_flood_tp == 7
    assert result.net_flood_tp_change == -2
    assert result.lost_flood_to_permanent_fraction == 0.75


def test_no_flood_target_does_not_create_a_recall_value():
    row = {f"c{i}{j}": 0 for i in range(3) for j in range(3)}
    row.update(c00=10)
    result = module().add_water_metrics(pd.DataFrame([row])).iloc[0]
    assert np.isnan(result.flood_recall)
    assert np.isnan(result.water_iou)
