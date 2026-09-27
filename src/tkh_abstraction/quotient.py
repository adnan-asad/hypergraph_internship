"""Counted hyperedge coarsening. No embeddings or clustering decisions yet.

Every original edge remains a separate record. Membership is undirected for
scoring; original endpoint order is retained without asserting its semantic role.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json

from .data_pipeline import validate


def _membership(groups: dict[str, list[str]], expected: set[str]) -> dict[str, str]:
    assignment = {}
    for group, members in groups.items():
        if not isinstance(group, str) or not group:
            raise ValueError("Group IDs must be nonempty strings")
        if not isinstance(members, list) or not members:
            raise ValueError(f"Group must contain a nonempty member list: {group}")
        for member in members:
            if member in assignment:
                raise ValueError(f"Overlapping or repeated member: {member}")
            assignment[member] = group
    if set(assignment) != expected:
        raise ValueError("Partition must cover exactly the original node IDs")
    return assignment


def _refresh(edge: dict, assignment: dict[str, str]) -> None:
    # First-occurrence order is retained for traceability, not role inference.
    counts = Counter(assignment[v] for v in edge["original_members"])
    edge["members"] = list(counts)
    edge["incidence_counts"] = dict(counts)
    edge["coarse_arity"] = len(counts)
    edge["internal"] = len(counts) == 1


def coarsen(graph: dict, groups: dict[str, list[str]]) -> dict:
    """Create a quotient from a raw graph/snapshot and an exact hard partition.

    Original attributes (including n_targets), dates and provenance are copied
    unchanged. They describe the ORIGINAL edge, not a new group-level assertion.
    Original arity may differ from coarse arity. Internal edges are retained.
    """
    validate(graph)
    reserved = {"original_members", "original_arity", "coarse_arity", "incidence_counts", "internal"}
    if any(reserved.intersection(e) for e in graph["hyperedges"]):
        raise ValueError("coarsen expects raw edges; use merge_groups on an existing quotient")
    assignment = _membership(groups, {n["id"] for n in graph["nodes"]})
    edges = []
    for original in graph["hyperedges"]:
        edge = deepcopy(original)
        edge["original_members"] = list(original["members"])
        edge["original_arity"] = len(original["members"])
        _refresh(edge, assignment)
        edges.append(edge)
    return {
        "meta": {"representation": "counted_quotient_v1",
                 "roles": "not inferred; original order preserved",
                 "source_meta": deepcopy(graph["meta"])},
        "supernodes": [{"id": k, "member_ids": list(v)} for k, v in groups.items()],
        "hyperedges": edges,
    }


def merge_groups(quotient: dict, left: str, right: str, new_id: str) -> dict:
    """Merge two WHOLE groups, returning a new quotient without mutating input.

    Correctness-first implementation rebuilds incidence counts in O(N + I),
    where I is the original incidence total. It is not an optimized search loop.
    """
    groups = {n["id"]: list(n["member_ids"]) for n in quotient["supernodes"]}
    if left == right or left not in groups or right not in groups:
        raise ValueError("Select two distinct existing groups")
    if not isinstance(new_id, str) or not new_id or new_id in groups:
        raise ValueError("Merged group requires a new, nonempty unique ID")
    merged = groups.pop(left) + groups.pop(right)
    groups[new_id] = merged
    expected = {v for n in quotient["supernodes"] for v in n["member_ids"]}
    assignment = _membership(groups, expected)
    result = deepcopy(quotient)
    result["supernodes"] = [{"id": k, "member_ids": v} for k, v in groups.items()]
    for edge in result["hyperedges"]:
        _refresh(edge, assignment)
    return result


def fragmentation(quotient: dict) -> float:
    """Uniform-edge mean of (coarse_arity - 1)/(original_arity - 1).

    This is a structural optimization term, NOT semantic quality or fidelity.
    The denominator retains original arity even after partial/full collapse.
    Empty edge sets have cost zero. Parallel source edges contribute separately.
    """
    edges = quotient["hyperedges"]
    if not edges:
        return 0.0
    return sum((len(e["incidence_counts"]) - 1) / (e["original_arity"] - 1)
               for e in edges) / len(edges)


def _demo() -> None:
    graph = {"meta": {}, "nodes": [
        {"id": v, "type": "method", "surface_form": v, "year": 2020,
         "first_seen_year": 2020, "last_seen_year": 2020}
        for v in ["a", "b", "c", "d"]
    ], "hyperedges": [{"id": "example_edge", "relation_type": "illustrative",
                        "members": ["a", "b", "c", "d"], "year": 2020,
                        "provenance": {"article_year": 2020}}]}
    q = coarsen(graph, {v: [v] for v in ["a", "b", "c", "d"]})
    for name, left, right in [("X", "a", "b"), ("Y", "X", "c"), ("Z", "Y", "d")]:
        q = merge_groups(q, left, right, name)
        print(json.dumps({"counts": q["hyperedges"][0]["incidence_counts"],
                          "internal": q["hyperedges"][0]["internal"],
                          "fragmentation": fragmentation(q)}, sort_keys=True))


if __name__ == "__main__":
    _demo()
