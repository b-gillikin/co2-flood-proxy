import numpy as np
import pandas as pd
import pytest

from src.meuse_context import hourly_context, source_rows, state_at_cutoff


def observations(code="00"):
    return pd.DataFrame(
        dict(
            timestamp=pd.date_range("2021-07-01T00:00Z", periods=7, freq="10min"),
            q=np.arange(7.0),
            code=code,
            status="Gecontroleerd",
        )
    )


def test_centred_support_cannot_enter_its_timestamp_cutoff():
    f = hourly_context(observations(), "2021-07-01", "2021-07-01T02:00Z")
    assert pd.isna(f.loc["2021-07-01T00:00Z", "q_strict"])
    assert f.loc["2021-07-01T01:00Z", "q_strict"] == 2.5
    assert f.loc["2021-07-01T01:00Z", "n_strict"] == 6


def test_interpolation_is_visible_but_never_promoted_to_strict():
    f = hourly_context(observations("25"), "2021-07-01", "2021-07-01T02:00Z")
    assert f.q_strict.isna().all()
    assert f.loc["2021-07-01T01:00Z", "q_display"] == 2.5
    assert f.loc["2021-07-01T01:00Z", "n_interpolated"] == 6


def test_missing_and_uncontrolled_do_not_become_zero_or_stale_context():
    rows = observations().iloc[:3].copy()
    f = hourly_context(rows, "2021-07-01", "2021-07-01T04:00Z")
    assert f.q_strict.isna().all()
    rows["status"] = "Ongecontroleerd"
    assert hourly_context(rows, "2021-07-01", "2021-07-01T04:00Z").n_display.sum() == 0


def test_conflicting_annual_overlap_raises_and_identical_overlap_deduplicates():
    rows = observations()
    f = hourly_context(pd.concat([rows, rows]), "2021-07-01", "2021-07-01T02:00Z")
    assert f.n_strict.sum() == 7
    altered = rows.iloc[:1].copy()
    altered["q"] = 999.0
    with pytest.raises(ValueError, match="Conflicting"):
        hourly_context(pd.concat([rows, altered]), "2021-07-01", "2021-07-01T02:00Z")


def test_rank_uses_previous_calendar_years_only():
    i = pd.date_range("2020-12-31T20:00Z", periods=10, freq="h")
    f = pd.DataFrame(
        dict(
            q_strict=[1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 3.0, 4.0, 1000.0, 1000.0],
            q_display=1.0,
            n_interpolated=0.0,
        ),
        index=i,
    )
    a = state_at_cutoff(f, pd.Timestamp("2021-01-01T02:00Z"))
    assert a["prior_year_rank"] == 0.75
    assert a["history_hours"] == 4
    f.loc[f.index > pd.Timestamp("2021-01-01T02:00Z"), "q_strict"] = -100.0
    pd.testing.assert_series_equal(
        pd.Series(state_at_cutoff(f, pd.Timestamp("2021-01-01T02:00Z"))), pd.Series(a)
    )


def test_daily_other_methods_and_wrong_units_are_not_mixed():
    def block(method, processing, unit):
        return dict(
            AquoMetadata=dict(
                WaardeBepalingsMethode={"Code": method},
                WaardeBewerkingsMethode={"Code": processing},
                Grootheid={"Code": "Q"},
                Eenheid={"Code": unit},
            ),
            MetingenLijst=[
                dict(
                    Tijdstip=time,
                    Meetwaarde={"Waarde_Numeriek": 10.0},
                    WaarnemingMetadata=dict(
                        Kwaliteitswaardecode="00", Statuswaarde="Gecontroleerd"
                    ),
                )
                for time in ["2021-01-01T00:00Z", "2021-01-01T00:10Z"]
            ],
        )

    rows, audit = source_rows(
        dict(
            WaarnemingenLijst=[
                block("other:F103", "NVT", "m3/s"),
                block("other:F103", "GEM24H", "m3/s"),
                block("other:F006", "NVT", "m3/s"),
                block("other:F103", "NVT", "cm"),
            ]
        )
    )
    assert len(rows) == 2
    assert len(audit) == 4


def test_daily_cadence_is_excluded_even_with_unprocessed_metadata():
    from copy import deepcopy

    block = dict(
        AquoMetadata=dict(
            WaardeBepalingsMethode={"Code": "other:F103"},
            WaardeBewerkingsMethode={"Code": "NVT"},
            Grootheid={"Code": "Q"},
            Eenheid={"Code": "m3/s"},
        ),
        MetingenLijst=[],
    )
    for t in ["2021-01-01T00:00Z", "2021-01-02T00:00Z"]:
        block["MetingenLijst"].append(
            dict(
                Tijdstip=t,
                Meetwaarde={"Waarde_Numeriek": 10.0},
                WaarnemingMetadata=dict(Kwaliteitswaardecode="00", Statuswaarde="Gecontroleerd"),
            )
        )
    daily = deepcopy(block)
    block["MetingenLijst"][1]["Tijdstip"] = "2021-01-01T00:10Z"
    rows, audit = source_rows({"WaarnemingenLijst": [block, daily]})
    assert len(rows) == 2
    assert not audit[1]["selected_method"]
    assert audit[1]["median_step_minutes"] == 1440
