"""Checks for the RWS quality filter and forward-year information boundary."""

import importlib.util
import json
from pathlib import Path

import pandas as pd


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/62_test_maas_tributary_increment.py"
SPEC = importlib.util.spec_from_file_location("maas_tributary_increment", SCRIPT)
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def test_rws_cleaner_drops_interpolated_and_daily_values(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "RAW", tmp_path)
    monkeypatch.setattr(pilot, "YEARS", range(2021, 2022))

    def block(values, code="00", processing="NVT"):
        return {
            "AquoMetadata": {"WaardeBepalingsMethode": {"Code": "other:F103"},
                             "WaardeBewerkingsMethode": {"Code": processing}},
            "MetingenLijst": [{"Tijdstip": f"2021-01-01T{hour:02d}:{minute:02d}:00+00:00",
                               "Meetwaarde": {"Waarde_Numeriek": value},
                               "WaarnemingMetadata": {"Kwaliteitswaardecode": code,
                                                       "Statuswaarde": "Gecontroleerd"}}
                              for hour, minute, value in values],
        }

    good = [(0, minute, float(i)) for i, minute in enumerate((10, 20, 30, 40, 50), 1)]
    good.append((1, 0, 6.0))
    interpolated = [(1, minute, 1000.0) for minute in (10, 20, 30, 40, 50)]
    interpolated.append((2, 0, 1000.0))
    source = {"WaarnemingenLijst": [block(good), block(interpolated, "25"),
                                     block([(12, 0, 999.0)], processing="GEM24H")]}
    (tmp_path / "example_2021.json").write_text(json.dumps(source))
    hourly, qa, _ = pilot.clean_rws_hourly("example", min_high_frequency_block_readings=1)
    assert hourly.loc[pd.Timestamp("2021-01-01T01:00Z")] == 3.5
    assert pd.isna(hourly.loc[pd.Timestamp("2021-01-01T02:00Z")])
    assert qa.accepted_readings.iloc[0] == 6
    assert "25" in qa.all_code_counts.iloc[0]


def test_forward_test_year_outcomes_do_not_enter_predictions(monkeypatch):
    monkeypatch.setattr(pilot, "YEARS", range(2017, 2021))
    rows = []
    for year in range(2017, 2021):
        for i in range(4):
            row = {name: float(i + (year - 2017) / 10) for name in pilot.ADDED}
            row.update({"year": year, "target_end_utc": pd.Timestamp(f"{year}-01-03T00:00Z"),
                        "high_venlo_next_72h": i % 2})
            rows.append(row)
    frame = pd.DataFrame(rows)
    first = pilot.forward_predictions(frame)
    altered = frame.copy()
    altered.loc[altered.year.eq(2020), "high_venlo_next_72h"] = 1
    second = pilot.forward_predictions(altered)
    pd.testing.assert_series_equal(first.p_base, second.p_base)
    pd.testing.assert_series_equal(first.p_plus_tributaries, second.p_plus_tributaries)
