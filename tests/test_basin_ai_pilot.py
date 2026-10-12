import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "basin_ai", ROOT / "scripts/63_build_basin_ai_pilot.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def load(name):
    return json.loads((ROOT / "docs/ai-eval" / name).read_text())


def test_contract_has_four_fixed_arms_and_no_dangling_evidence():
    MODULE.validate_contract(
        load("source-inventory.json"),
        load("benchmark-draft.json"),
        load("basin-graph.json"),
        load("system-arms.json"),
        load("scoring-rubric.json"),
    )


def test_pilot_questions_retrieve_a_gold_source_in_top_three():
    sources = load("source-inventory.json")
    cases = [case for case in load("benchmark-draft.json") if case["split"] == "pilot"]
    for case in cases:
        retrieved = {
            item["source_id"] for item in MODULE.retrieve(case["question"], sources, top_k=3)
        }
        assert retrieved.intersection(case["gold_source_ids"]), case["case_id"]


def test_graph_keeps_honsdorf_off_wurm():
    result = MODULE.CheckedTools(load("basin-graph.json")).graph_facts("Honsdorf")
    located_on = {
        (edge["subject"], edge["object"])
        for edge in result["edges"]
        if edge["predicate"] == "located_on"
    }
    assert ("gauge_honsdorf", "river_beeckflies") in located_on
    assert ("gauge_honsdorf", "river_worm") not in located_on


def test_document_tools_arm_never_receives_graph_tool_calls():
    cases = load("benchmark-draft.json")
    assert all(call["name"] != "graph_facts" for case in cases for call in case["tool_calls"])


def test_current_threshold_tool_preserves_historical_limit():
    result = MODULE.CheckedTools(load("basin-graph.json")).current_thresholds("10.Q.29")
    assert result["H3_m3s"] == 27.5
    assert "historical thresholds unavailable" in result["temporal_scope"]
