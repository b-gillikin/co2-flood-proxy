"""Checks for the rating-era build (decision D8)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "rating_eras", ROOT / "scripts" / "43_build_rating_eras.py"
)
ERAS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ERAS)


def version(formula, low, high):
    return pd.DataFrame(
        {"segment": ["1"], "stage_low_m": [low], "stage_high_m": [high], "formula": [formula]}
    )


def test_a_datum_shift_with_the_same_hydraulics_agrees_everywhere():
    old = version("2.0*(H-10.0)**2", 10.1, 12.0)
    new = version("2.0*(H-10.05)**2", 10.15, 12.05)

    assert ERAS.uniform_above(old, [(new, 0.05)]) == np.nanmin(ERAS.discharge(old, [10.1]))


def test_a_low_flow_revision_agrees_only_above_its_segment():
    old = version("2.0*(H-10.0)**2", 10.1, 12.0)
    new = pd.concat(
        [
            version("3.0*(H-10.0)**2", 10.1, 11.0).assign(segment="1"),
            version("2.0*(H-10.0)**2", 11.0, 12.0).assign(segment="2"),
        ]
    )

    level = ERAS.uniform_above(old, [(new, 0.0)])

    assert level > ERAS.discharge(old, [10.99])[0]
    assert level <= ERAS.discharge(old, [11.01])[0]


def test_versions_that_disagree_at_the_top_can_never_be_merged():
    old = version("2.0*(H-10.0)**2", 10.1, 12.0)
    new = version("2.2*(H-10.0)**2", 10.1, 12.0)

    assert ERAS.uniform_above(old, [(new, 0.0)]) == np.inf


def test_built_eras_match_the_decision_table():
    eras, literal = ERAS.build_tables()

    assert sorted(eras.gauge.unique()) == sorted(
        ["10.Q.29", "11.Q.32", "13.Q.34", "15.Q.41", "18.Q.45", "6.Q.18"]
    )
    gulp = eras[eras.gauge.eq("13.Q.34")]
    assert gulp.era_id.nunique() == 2
    assert "2011-03-01" not in set(gulp.rating_version)
    assert "2012-10-15" not in set(gulp.rating_version)
    assert eras.loc[eras.gauge.eq("18.Q.45"), "relation_uniform_above_m3s"].iloc[0] < 5.0
    assert literal.era_id.nunique() == 13
