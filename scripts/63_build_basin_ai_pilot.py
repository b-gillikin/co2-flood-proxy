#!/usr/bin/env python3
"""Build source-grounded prompt packets for the Limburg basin-AI pilot.

This script does not call a language model and does not score generated
answers. It validates the corpus, benchmark, graph and deterministic tools;
then it builds identical question packets for the four evidence-access arms.
The first pilot therefore tests whether the evidence can be retrieved and
computed before model behavior is introduced.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "docs/ai-eval"
OUT = ROOT / "results/basin_ai_pilot"


def load_json(name: str):
    return json.loads((DESIGN / name).read_text(encoding="utf-8"))


def validate_contract(sources, benchmark, graph, arms, rubric) -> None:
    source_ids = {item["source_id"] for item in sources}
    if len(source_ids) != len(sources):
        raise ValueError("Duplicate source_id")
    case_ids = {item["case_id"] for item in benchmark}
    if len(case_ids) != len(benchmark):
        raise ValueError("Duplicate case_id")
    missing = {
        source
        for case in benchmark
        for source in case["gold_source_ids"]
        if source not in source_ids
    }
    if missing:
        raise ValueError(f"Benchmark cites unknown sources: {sorted(missing)}")
    node_ids = {node["id"] for node in graph["nodes"]}
    dangling = [
        edge
        for edge in graph["edges"]
        if edge["subject"] not in node_ids or edge["object"] not in node_ids
    ]
    if dangling:
        raise ValueError(f"Dangling graph edges: {dangling}")
    if [item["arm_id"] for item in arms] != [
        "A0_GENERAL_LLM",
        "A1_DOCUMENT_RAG",
        "A2_RAG_TOOLS",
        "A3_BASIN_GROUNDED",
    ]:
        raise ValueError("The four comparison arms changed")
    dimensions = {item["dimension"] for item in rubric}
    unknown = {
        dimension
        for case in benchmark
        for dimension in case["applicable_dimensions"]
        if dimension not in dimensions
    }
    if unknown:
        raise ValueError(f"Unknown scoring dimensions: {sorted(unknown)}")


def retrieve(question: str, sources: list[dict], top_k: int = 3) -> list[dict]:
    """Small hybrid lexical retriever for the feasibility pilot."""
    texts = [item["retrieval_text"] for item in sources]
    word = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)
    char = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 5), lowercase=True, sublinear_tf=True
    )
    word_matrix = word.fit_transform(texts + [question])
    char_matrix = char.fit_transform(texts + [question])
    score = 0.7 * cosine_similarity(word_matrix[-1], word_matrix[:-1]).ravel()
    score += 0.3 * cosine_similarity(char_matrix[-1], char_matrix[:-1]).ravel()
    order = np.argsort(-score)[:top_k]
    return [
        {
            "source_id": sources[index]["source_id"],
            "score": float(score[index]),
            "title": sources[index]["title"],
            "text": sources[index]["retrieval_text"],
        }
        for index in order
    ]


def _bool(value) -> bool:
    return bool(value) and str(value).lower() not in {"false", "0", "nan"}


class CheckedTools:
    """Narrow read-only tools over already audited local tables."""

    def __init__(self, graph: dict):
        self.graph = graph

    def gauge_metadata(self, query: str) -> dict:
        gauges = pd.read_csv(ROOT / "data/interim/event_study_gauges.csv")
        key = query.casefold()
        hit = gauges[
            gauges.apply(
                lambda row: (
                    key in str(row["gauge"]).casefold() or key in str(row["watercourse"]).casefold()
                ),
                axis=1,
            )
        ]
        if len(hit) != 1:
            return {"status": "ambiguous_or_not_found", "matches": int(len(hit))}
        row = hit.iloc[0]
        return {
            "status": "ok",
            "gauge": row.gauge,
            "watercourse": row.watercourse,
            "july_2021_status": row.july_2021_status,
            "timezone_verified": _bool(row.timezone_verified),
            "zero_semantics_verified": _bool(row.zero_semantics_verified),
        }

    def rating_era(self, gauge: str, timestamp: str) -> dict:
        eras = pd.read_csv(ROOT / "data/interim/event_study_rating_eras.csv")
        when = pd.Timestamp(timestamp)
        if when.tzinfo is None:
            when = when.tz_localize("UTC")
        start = pd.to_datetime(eras.valid_from_utc, utc=True)
        end = pd.to_datetime(eras.valid_to_utc, utc=True, errors="coerce")
        hit = eras[(eras.gauge == gauge) & start.le(when) & (end.isna() | end.gt(when))]
        if len(hit) != 1:
            return {"status": "ambiguous_or_not_found", "matches": int(len(hit))}
        row = hit.iloc[0]
        return {
            "status": "ok",
            "gauge": gauge,
            "era_id": row.era_id,
            "valid_from_utc": row.valid_from_utc,
            "valid_to_utc": None if pd.isna(row.valid_to_utc) else row.valid_to_utc,
            "domain_min_m3s": float(row.domain_min_m3s),
            "domain_max_m3s": float(row.domain_max_m3s),
            "source_document": row.source_document,
        }

    def current_thresholds(self, gauge: str) -> dict:
        path = (
            ROOT
            / "data/raw/external_deliveries/waterschap_limburg/2026-09-29/warning tresholds(Blad1).csv"
        )
        raw = pd.read_csv(path, header=None)
        hit = raw[raw.iloc[:, 1].astype(str).eq(gauge)]
        if len(hit) != 1:
            return {"status": "not_found"}
        row = hit.iloc[0]
        return {
            "status": "ok",
            "gauge": gauge,
            "H1_m3s": float(row.iloc[3]),
            "H2_m3s": float(row.iloc[4]),
            "H3_m3s": float(row.iloc[5]),
            "temporal_scope": "current snapshot only; historical thresholds unavailable",
        }

    def event_review(self, gauge: str, timestamp: str) -> dict:
        events = pd.read_csv(ROOT / "results/event_study/real_data_v1/event_analysis_status.csv")
        target = pd.Timestamp(timestamp)
        observed = pd.to_datetime(events.onset_utc, utc=True)
        if target.tzinfo is None:
            target = target.tz_localize("UTC")
        hit = events[(events.gauge == gauge) & observed.eq(target)]
        if len(hit) != 1:
            return {"status": "not_found", "matches": int(len(hit))}
        row = hit.iloc[0]
        return {
            "status": "ok",
            "event_id": row.event_id,
            "onset_pair_admissible": _bool(row.onset_pair_admissible),
            "onset_within_domain": _bool(row.onset_within_domain),
            "measurement_concern": _bool(row.measurement_concern_y),
            "provider_status": row.provider_status,
            "decision_basis": row.decision_basis,
        }

    def maas_quality(self, site: str, start: str, end: str) -> dict:
        # The event-specific result is already audited against raw RWS JSON.
        # Keep this tool on that frozen finding rather than reparsing a second way.
        if site.casefold() != "venlo" or start != "2021-07-12" or end != "2021-07-20":
            return {"status": "unsupported_window"}
        return {
            "status": "ok",
            "site": "Venlo",
            "window": [start, end],
            "quality_result": "ten-minute discharge values are almost entirely code 25",
            "code_25_meaning": "interpolated in space and time",
            "consequence": "strict direct-measurement analysis excludes the July 2021 rise",
            "source": "docs/limburg-maas-tributary-pilot-2026-10-04.md",
        }

    def graph_facts(self, query: str) -> dict:
        stopwords = {
            "the",
            "and",
            "for",
            "from",
            "that",
            "this",
            "with",
            "does",
            "can",
            "entire",
            "used",
            "use",
            "what",
            "which",
            "during",
            "series",
            "station",
            "gauge",
            "held",
            "provide",
            "directly",
            "records",
            "record",
            "discharge",
            "water",
            "flow",
        }
        terms = {
            part.strip(".,?()[]").casefold()
            for part in query.replace("/", " ").split()
            if len(part.strip(".,?()[]")) > 2 and part.strip(".,?()[]").casefold() not in stopwords
        }
        nodes = []
        selected_ids = set()
        for node in self.graph["nodes"]:
            haystack = " ".join([node["name"], *node.get("aliases", [])]).casefold()
            if any(term in haystack for term in terms):
                nodes.append(node)
                selected_ids.add(node["id"])
        edges = [
            edge
            for edge in self.graph["edges"]
            if edge["subject"] in selected_ids or edge["object"] in selected_ids
        ]
        connected_ids = selected_ids | {e["subject"] for e in edges} | {e["object"] for e in edges}
        context_nodes = [node for node in self.graph["nodes"] if node["id"] in connected_ids]
        return {"status": "ok", "nodes": context_nodes, "edges": edges}

    def call(self, name: str, args: dict) -> dict:
        method = getattr(self, name, None)
        if method is None or name.startswith("_"):
            return {"status": "unknown_tool", "name": name}
        return method(**args)


def graph_context(question: str, graph: dict) -> dict:
    return CheckedTools(graph).graph_facts(question)


def build(top_k: int = 3) -> dict:
    sources = load_json("source-inventory.json")
    benchmark = load_json("benchmark-draft.json")
    graph = load_json("basin-graph.json")
    arms = load_json("system-arms.json")
    rubric = load_json("scoring-rubric.json")
    validate_contract(sources, benchmark, graph, arms, rubric)

    pilot = [case for case in benchmark if case["split"] == "pilot"]
    tools = CheckedTools(graph)
    packets = []
    retrieval_rows = []
    for case in pilot:
        retrieved = retrieve(case["question"], sources, top_k=top_k)
        retrieved_ids = [item["source_id"] for item in retrieved]
        gold = set(case["gold_source_ids"])
        retrieval_rows.append(
            {
                "case_id": case["case_id"],
                "top_k": top_k,
                "retrieved_source_ids": ";".join(retrieved_ids),
                "gold_source_ids": ";".join(case["gold_source_ids"]),
                "gold_hit": bool(gold.intersection(retrieved_ids)),
                "all_gold_retrieved": gold.issubset(retrieved_ids),
            }
        )
        tool_results = [
            {
                "tool": call["name"],
                "args": call["args"],
                "result": tools.call(call["name"], call["args"]),
            }
            for call in case["tool_calls"]
        ]
        basin = graph_context(case["question"], graph)
        for arm in arms:
            packets.append(
                {
                    "case_id": case["case_id"],
                    "arm_id": arm["arm_id"],
                    "question": case["question"],
                    "documents": retrieved if arm["document_access"] else [],
                    "tool_results": tool_results if arm["checked_tools"] else [],
                    "basin_graph": basin if arm["basin_graph"] else {},
                    "output_contract": {
                        "assessment": "string",
                        "claims": [{"text": "string", "source_ids": ["string"]}],
                        "measurement_limits": ["string"],
                        "unresolved_conflicts": ["string"],
                        "insufficient_evidence": ["string"],
                    },
                    "instruction": "Answer only from accessible evidence. Cite source IDs for material claims. Do not issue a warning. State unsupported conclusions explicitly.",
                }
            )

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "prompt_packets.jsonl").open("w", encoding="utf-8") as stream:
        for packet in packets:
            stream.write(json.dumps(packet, ensure_ascii=False) + "\n")
    retrieval = pd.DataFrame(retrieval_rows)
    retrieval.to_csv(OUT / "retrieval_pilot.csv", index=False)
    summary = {
        "status": "evidence-path pilot complete; no LLM answers generated or scored",
        "source_count": len(sources),
        "benchmark_case_count": len(benchmark),
        "pilot_case_count": len(pilot),
        "arm_count": len(arms),
        "prompt_packet_count": len(packets),
        "top_k": top_k,
        "any_gold_retrieval_rate": float(retrieval.gold_hit.mean()),
        "all_gold_retrieval_rate": float(retrieval.all_gold_retrieved.mean()),
        "next_human_step": "Review reference answers and applicable scoring dimensions before any model run.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    build(top_k=args.top_k)


if __name__ == "__main__":
    main()
