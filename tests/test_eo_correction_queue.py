"""Resource ownership and corrected-run provenance must remain explicit."""

import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
QUEUE = runpy.run_path(str(ROOT / "scripts/122_run_coherent_eo_correction.py"))
ENTRY = runpy.run_path(str(ROOT / "scripts/118_extract_versioned_eo_sequences.py"))


@pytest.mark.parametrize("smoke", [False, True])
@pytest.mark.parametrize(
    "model,device,runtime", [job for lane in QUEUE["LANES"].values() for job in lane]
)
def test_actual_queue_modes_are_forwarded_without_runtime_profile_abbreviation(
    model, device, runtime, smoke
):
    command = QUEUE["extraction_command"](model, device, runtime, smoke=smoke)
    parsed, delegated = ENTRY["argument_parser"]().parse_known_args(command[3:])
    assert parsed.model == model and parsed.device == device
    assert parsed.runtime_profile == ("presto-torch291-cpu4" if model == "presto" else "native")
    assert ("--smoke" if smoke else "--run") in delegated


def test_eight_affected_models_have_single_owners_and_exact_resource_split():
    lanes = QUEUE["LANES"]
    assert len(lanes) == 3
    assert sum(name.startswith("cpu") for name in lanes) == 2
    assert sum(name.startswith("mps") for name in lanes) == 1
    models = [m for lane in lanes.values() for m, _, _ in lane]
    assert len(models) == len(set(models)) == 8
    assert set(models) == {m for m, route in QUEUE["ROUTES"].items() if route[0] == "s2_10m"} | {
        "croma"
    }
    assert not set(models) & {"prithvi", "olmoearth"}
    for name, lane in lanes.items():
        assert {device for _, device, _ in lane} == {"cpu" if name.startswith("cpu") else "mps"}


def test_presto_keeps_validated_runtime_and_engineering_cannot_mingle_with_census():
    make = QUEUE["extraction_command"]
    census = make("presto", "cpu", "presto-torch291")
    smoke = make("presto", "cpu", "presto-torch291", smoke=True)
    assert "presto-torch291/bin/python" in census[0]
    assert "presto-torch291-cpu4" in census and "--run" in census
    assert "--smoke" in smoke and "--run" not in smoke
    assert census[census.index("--output") + 1] != smoke[smoke.index("--output") + 1]


def test_unknown_or_old_input_policy_cannot_be_reused_as_corrected(tmp_path, monkeypatch):
    run = tmp_path / "sequences/galileo/run"
    run.mkdir(parents=True)
    (run / "manifest.json").write_text("{}")
    verify = QUEUE["verified_model_run"]
    monkeypatch.setitem(verify.__globals__, "SEQUENCES", tmp_path / "sequences")
    monkeypatch.setitem(
        verify.__globals__, "validate_run", lambda *a, **k: ({"input_policy": "old"}, {})
    )
    with pytest.raises(ValueError, match="coherent"):
        verify("galileo", ["context"])
    monkeypatch.setitem(
        verify.__globals__,
        "validate_run",
        lambda *a, **k: (
            {"input_policy": QUEUE["POLICY"], "input_corrections": QUEUE["INPUT_CORRECTIONS"]},
            {},
        ),
    )
    assert verify("galileo", ["context"])[0] == run
