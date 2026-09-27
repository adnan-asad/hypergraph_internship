"""Auditable temporal direction inference for `extends` hyperedges.

This is a separate metadata layer. It does not alter member order, source data,
clustering scores, or evaluated partitions. Inferred direction is not verified
scientific fact.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import json

from .data_pipeline import load_graph, write_json

POLICY_VERSION = "extends_direction_temporal_heuristic_v1"


def method_evidence(edge: dict, node_by_id: dict[str, dict]) -> list[dict]:
    ev = []
    for pos, node_id in enumerate(edge["members"]):
        n = node_by_id[node_id]
        if n.get("type") == "method":
            ev.append({
                "id": node_id,
                "position": pos,
                "surface_form": n.get("surface_form"),
                "origin_year": n.get("origin_year"),
                "first_seen_year": n.get("first_seen_year"),
            })
    return ev


def infer_extends_direction(edge: dict, node_by_id: dict[str, dict]) -> dict:
    methods = method_evidence(edge, node_by_id)
    non_methods = [{"id": m, "type": node_by_id[m].get("type"), "surface_form": node_by_id[m].get("surface_form")}
                   for m in edge["members"] if node_by_id[m].get("type") != "method"]
    base = {
        "edge_id": edge["id"],
        "relation_type": edge["relation_type"],
        "original_members": list(edge["members"]),
        "edge_year": edge["year"],
        "inferred_source_method": None,
        "candidate_target_methods": [m["id"] for m in methods],
        "status": "unresolved",
        "rule_applied": None,
        "method_evidence": methods,
        "non_method_context": non_methods,
        "uncertainty_reason": None,
        "inference_policy_version": POLICY_VERSION,
        "note": "Direction is inferred from dates, not verified scientific fact; original hyperedge remains multi-target.",
    }
    if edge.get("relation_type") != "extends":
        base["uncertainty_reason"] = "not an extends edge"
        return base
    if len(methods) < 2:
        base["uncertainty_reason"] = "fewer than two method endpoints"
        return base
    known = [m for m in methods if isinstance(m.get("origin_year"), int)]
    missing = [m for m in methods if not isinstance(m.get("origin_year"), int)]
    future = [m for m in known if m["origin_year"] > edge["year"]]
    if future:
        base["uncertainty_reason"] = "future-origin contradiction relative to edge year"
        return base
    if missing:
        # Missing method dates can hide a newer/extending method, so abstain.
        base["uncertainty_reason"] = "missing origin_year ambiguity among method endpoints"
        return base

    equals_edge_year = [m for m in known if m["origin_year"] == edge["year"]]
    if len(equals_edge_year) == 1:
        anchor = equals_edge_year[0]
        if all(m["origin_year"] <= anchor["origin_year"] for m in known if m["id"] != anchor["id"]):
            return resolved(base, anchor["id"], methods, "unique_method_origin_equals_edge_year")
        base["uncertainty_reason"] = "known method dates contradict edge-year anchor being newest"
        return base
    if len(equals_edge_year) > 1:
        base["uncertainty_reason"] = "tie: multiple method origin_year values equal edge year"
        return base

    max_year = max(m["origin_year"] for m in known)
    newest = [m for m in known if m["origin_year"] == max_year]
    if len(newest) == 1 and max_year <= edge["year"]:
        return resolved(base, newest[0]["id"], methods, "unique_newest_known_method_temporally_compatible")
    if len(newest) > 1:
        base["uncertainty_reason"] = "tie: multiple newest method origin_year values"
    else:
        base["uncertainty_reason"] = "no temporally compatible unique newest method"
    return base


def resolved(base: dict, source: str, methods: list[dict], rule: str) -> dict:
    base = dict(base)
    base["inferred_source_method"] = source
    base["candidate_target_methods"] = [m["id"] for m in methods if m["id"] != source]
    base["status"] = "resolved"
    base["rule_applied"] = rule
    base["uncertainty_reason"] = "heuristic inference; not independently corroborated"
    return base


def infer_graph(graph: dict) -> dict:
    node_by_id = {n["id"]: n for n in graph["nodes"]}
    records = [infer_extends_direction(e, node_by_id) for e in graph["hyperedges"] if e.get("relation_type") == "extends"]
    agreements = disagreements = resolved_count = unresolved = 0
    examples = []
    for r in records:
        if r["status"] == "resolved":
            resolved_count += 1
            if r["original_members"] and r["inferred_source_method"] == r["original_members"][0]:
                agreements += 1
            else:
                disagreements += 1
                if len(examples) < 10:
                    examples.append(r)
        else:
            unresolved += 1
            if len(examples) < 10:
                examples.append(r)
    stats = {
        "extends_edges": len(records),
        "resolved": resolved_count,
        "unresolved": unresolved,
        "member0_diagnostic": {
            "denominator_resolved_edges": resolved_count,
            "agreements_with_member0": agreements,
            "disagreements_with_member0": disagreements,
            "note": "Diagnostic only; member[0] is not used as a direction contract.",
        },
        "status_by_reason": dict(Counter(r["uncertainty_reason"] for r in records)),
        "rule_counts": dict(Counter(r["rule_applied"] or "unresolved" for r in records)),
    }
    return {"policy_version": POLICY_VERSION,
            "limitation": "Earlier implementation preserved extends hyperedges without resolving direction. This layer adds a temporal heuristic with explicit abstention; unit tests/date consistency do not establish direction accuracy.",
            "statistics": stats, "representative_exceptions": examples, "edges": records}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = infer_graph(load_graph(args.snapshot))
    write_json(args.output, result)
    print(json.dumps(result["statistics"], indent=2))


if __name__ == "__main__":
    main()
