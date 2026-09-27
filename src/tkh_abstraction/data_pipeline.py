"""Day-one loader, audit, and conservative snapshots. Python 3.10+, stdlib only."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path


def validate(graph: dict) -> None:
    """Reject structural defects; preserve date discrepancies for the audit."""
    if not all(k in graph for k in ("meta", "nodes", "hyperedges")):
        raise ValueError("Expected meta, nodes, and hyperedges")
    nodes = graph["nodes"]
    edges = graph["hyperedges"]
    ids = [n["id"] for n in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate node ID")
    edge_ids = [e["id"] for e in edges]
    if len(edge_ids) != len(set(edge_ids)):
        raise ValueError("Duplicate edge ID")
    known = set(ids)
    for n in nodes:
        if not isinstance(n.get("surface_form"), str) or not n["surface_form"].strip():
            raise ValueError(f"Empty/non-text surface_form: {n['id']}")
        if not isinstance(n.get("type"), str) or not n["type"]:
            raise ValueError(f"Missing type: {n['id']}")
        for field in ("year", "first_seen_year", "last_seen_year"):
            if type(n.get(field)) is not int:
                raise ValueError(f"Missing/non-integer {field}: {n['id']}")
        if n["first_seen_year"] > n["last_seen_year"]:
            raise ValueError(f"first_seen_year exceeds last_seen_year: {n['id']}")
    for e in edges:
        members = e["members"]
        if not isinstance(members, list) or len(members) < 2:
            raise ValueError(f"Invalid raw edge arity: {e['id']}")
        if len(members) != len(set(members)):
            raise ValueError(f"Repeated endpoint: {e['id']}")
        if set(members) - known:
            raise ValueError(f"Dangling endpoint: {e['id']}")
        if not e.get("relation_type"):
            raise ValueError(f"Missing relation_type: {e['id']}")
        if type(e.get("year")) is not int:
            raise ValueError(f"Missing/non-integer edge year: {e['id']}")
        if type(e.get("provenance", {}).get("article_year")) is not int:
            raise ValueError(f"Missing/non-integer asserting article year: {e['id']}")


def load_graph(path: Path) -> dict:
    graph = json.loads(path.read_text(encoding="utf-8"))
    validate(graph)
    return graph


def available_year(edge: dict, nodes: dict) -> int:
    return max(edge["year"], edge["provenance"]["article_year"],
               *(nodes[v]["first_seen_year"] for v in edge["members"]))


def snapshot(graph: dict, cutoff: int) -> dict:
    """Select full records; never clip future endpoints out of an edge.

    Nodes retain historical metadata for auditing. These files are NOT sanitized
    label prompts: last_seen_year and full node provenance can reveal later data.
    A later evidence-payload builder must filter those fields before any LLM use.
    """
    index = {n["id"]: n for n in graph["nodes"]}
    nodes = [deepcopy(n) for n in graph["nodes"] if n["first_seen_year"] <= cutoff]
    edges = [deepcopy(e) for e in graph["hyperedges"]
             if available_year(e, index) <= cutoff]
    return {
        "meta": {
            "cutoff": cutoff,
            "policy": "node:first_seen; edge:max(year,article_year,endpoint_first_seen)",
            "node_text_versioned": False,
            "contains_historical_metadata": True,
            "warning": "Filter future provenance/last_seen from generation inputs; text is unversioned.",
        },
        "nodes": nodes,
        "hyperedges": edges,
    }


def describe(graph: dict) -> dict:
    nodes, edges = graph["nodes"], graph["hyperedges"]
    touched = {v for e in edges for v in e["members"]}
    return {
        "node_count": len(nodes), "edge_count": len(edges),
        "node_types": dict(sorted(Counter(n["type"] for n in nodes).items())),
        "relation_types": dict(sorted(Counter(e["relation_type"] for e in edges).items())),
        "arity_distribution": dict(sorted(Counter(len(e["members"]) for e in edges).items())),
        "isolated_nodes": sorted(n["id"] for n in nodes if n["id"] not in touched),
        "edge_year_range": [min(e["year"] for e in edges), max(e["year"] for e in edges)] if edges else None,
        "node_first_seen_range": [min(n["first_seen_year"] for n in nodes), max(n["first_seen_year"] for n in nodes)] if nodes else None,
    }


def audit(graph: dict, cutoffs: list[int]) -> dict:
    index = {n["id"]: n for n in graph["nodes"]}
    anomalies = {
        "node_year_before_first_seen": [n["id"] for n in graph["nodes"] if n["year"] < n["first_seen_year"]],
        "edge_year_before_article": [e["id"] for e in graph["hyperedges"] if e["year"] < e["provenance"]["article_year"]],
        "edge_year_after_article": [e["id"] for e in graph["hyperedges"] if e["year"] > e["provenance"]["article_year"]],
        "edge_before_endpoint_first_seen": [e["id"] for e in graph["hyperedges"] if any(index[v]["first_seen_year"] > e["year"] for v in e["members"])],
    }
    records = []
    previous_nodes, previous_edges = set(), set()
    for cutoff in sorted(set(cutoffs)):
        snap = snapshot(graph, cutoff)
        node_ids = {n["id"] for n in snap["nodes"]}
        edge_ids = {e["id"] for e in snap["hyperedges"]}
        delayed = []
        for e in graph["hyperedges"]:
            if e["year"] <= cutoff and e["id"] not in edge_ids:
                delayed.append({
                    "edge_id": e["id"], "available_year": available_year(e, index),
                    "asserting_paper_after_cutoff": e["provenance"]["article_year"] > cutoff,
                    "future_endpoint_ids": [v for v in e["members"] if index[v]["first_seen_year"] > cutoff],
                })
        records.append({"cutoff": cutoff, **describe(snap),
                        "naive_year_edge_count": sum(e["year"] <= cutoff for e in graph["hyperedges"]),
                        "added_nodes_since_previous_cutoff": len(node_ids - previous_nodes) if records else None,
                        "added_edges_since_previous_cutoff": len(edge_ids - previous_edges) if records else None,
                        "delayed_edges": delayed})
        previous_nodes, previous_edges = node_ids, edge_ids
    return {"full_graph": describe(graph), "date_anomalies": anomalies,
            "note": "Different origin/mention dates need not be errors; anomalies require interpretation.",
            "snapshots": records}


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, default=Path("data/raw/tkh_collection10.json"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/day1"))
    parser.add_argument("--cutoffs", type=int, nargs="+", default=[2020, 2022, 2024, 2026])
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Output directory is not empty. Choose a new run directory to preserve prior results.")
    graph = load_graph(args.graph)
    report = audit(graph, args.cutoffs)
    report["input_sha256"] = hashlib.sha256(args.graph.read_bytes()).hexdigest()
    write_json(args.output / "audit.json", report)
    for record in report["snapshots"]:
        cutoff = record["cutoff"]
        write_json(args.output / f"snapshot_{cutoff}.json", snapshot(graph, cutoff))
        print(f"{cutoff}: {record['node_count']} nodes, {record['edge_count']} edges, "
              f"{len(record['isolated_nodes'])} isolated nodes")
    print(f"Audit saved to {args.output / 'audit.json'}")


if __name__ == "__main__":
    main()
