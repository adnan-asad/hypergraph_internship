"""Native hypergraph-aware agglomerative merging over cached embeddings.

This is an exploratory 2020 engine. It uses original hyperedges for structural
merge deltas and exports the counted quotient only at saved cuts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import heapq
import hashlib
import json
from pathlib import Path
import random
import time

from .data_pipeline import load_graph, write_json
from .lexical_baseline import DEFAULT_BUDGETS, LEAF_LEVEL_NAME, Tree, _empty_output_dir, _members_for_cluster, _parent_map, _partition_from_clusters, _size_distribution, cut_tree
from .quotient import coarsen, fragmentation
from .semantic_baseline import inspection_for_run, load_cache


def _require_numpy():
    import numpy as np
    return np


class AgglomerativeState:
    def __init__(self, graph: dict, embeddings, lam: float):
        if lam < 0:
            raise ValueError("lambda must be nonnegative")
        self.np = _require_numpy()
        self.graph = graph
        self.x = self.np.asarray(embeddings, dtype=float)
        self.lam = float(lam)
        self.node_ids = [n["id"] for n in graph["nodes"]]
        self.node_index = {node_id: i for i, node_id in enumerate(self.node_ids)}
        self.edge_count = len(graph["hyperedges"])
        self.next_id = len(self.node_ids)
        self.active = set(range(len(self.node_ids)))
        self.version = {i: 0 for i in self.active}
        self.size = {i: 1 for i in self.active}
        self.sum = {i: self.x[i].copy() for i in self.active}
        self.sse = {i: 0.0 for i in self.active}
        self.members = {i: [self.node_ids[i]] for i in self.active}
        self.children: dict[int, tuple[int, int]] = {}
        self.distances: dict[int, float] = {}
        self.merge_log = []
        self.edge_weight, self.incident_edges = self._edge_structures()
        overall = self.x.mean(axis=0) if len(self.x) else self.np.zeros(0)
        self.total_scatter = float(((self.x - overall) ** 2).sum()) if len(self.x) else 0.0
        self.zero_scatter = self.total_scatter == 0.0
        self.current_sse = 0.0
        self.current_fragmentation = 1.0 if self.edge_count else 0.0
        self.heap = []
        self.semantic_deltas = []
        self.structural_deltas = []
        self._init_heap()

    def _edge_structures(self):
        edge_weight = {}
        incident = defaultdict(set)
        if not self.graph["hyperedges"]:
            return edge_weight, incident
        for idx, edge in enumerate(self.graph["hyperedges"]):
            arity = len(edge["members"])
            edge_weight[idx] = 1.0 / (self.edge_count * (arity - 1))
            for node_id in edge["members"]:
                incident[self.node_index[node_id]].add(idx)
        return edge_weight, incident

    def semantic_delta_raw(self, a: int, b: int) -> float:
        na, nb = self.size[a], self.size[b]
        mean_a = self.sum[a] / na
        mean_b = self.sum[b] / nb
        diff = mean_a - mean_b
        return float((na * nb / (na + nb)) * self.np.dot(diff, diff))

    def semantic_delta_norm(self, a: int, b: int) -> float:
        if self.zero_scatter:
            return 0.0
        return self.semantic_delta_raw(a, b) / self.total_scatter

    def structural_delta(self, a: int, b: int) -> float:
        if not self.edge_count:
            return 0.0
        ea = self.incident_edges.get(a, set())
        eb = self.incident_edges.get(b, set())
        if len(ea) > len(eb):
            ea, eb = eb, ea
        return -sum(self.edge_weight[e] for e in ea if e in eb)

    def combined_delta(self, a: int, b: int) -> tuple[float, float, float]:
        ds = self.semantic_delta_norm(a, b)
        dh = self.structural_delta(a, b)
        return ds + self.lam * dh, ds, dh

    def _push(self, a: int, b: int) -> None:
        if a == b or a not in self.active or b not in self.active:
            return
        if b < a:
            a, b = b, a
        dj, ds, dh = self.combined_delta(a, b)
        heapq.heappush(self.heap, (dj, ds, dh, a, b, self.version[a], self.version[b]))

    def _init_heap(self) -> None:
        ids = sorted(self.active)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                self._push(a, b)

    def best_pair_exhaustive(self):
        best = None
        ids = sorted(self.active)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                cand = (*self.combined_delta(a, b), a, b)
                key = (cand[0], cand[1], cand[2], cand[3], cand[4])
                if best is None or key < best[0]:
                    best = (key, cand)
        return best[1]

    def pop_best(self):
        while self.heap:
            dj, ds, dh, a, b, va, vb = heapq.heappop(self.heap)
            if a in self.active and b in self.active and self.version[a] == va and self.version[b] == vb:
                # Recompute to avoid stale numeric values from earlier incidences.
                rdj, rds, rdh = self.combined_delta(a, b)
                return rdj, rds, rdh, a, b
        raise RuntimeError("No merge candidates remain")

    def merge_once(self):
        dj, ds, dh, a, b = self.pop_best()
        new = self.next_id
        self.next_id += 1
        self.children[new] = (a, b)
        self.distances[new] = dj
        self.size[new] = self.size[a] + self.size[b]
        self.sum[new] = self.sum[a] + self.sum[b]
        raw = ds * self.total_scatter if not self.zero_scatter else self.semantic_delta_raw(a, b)
        self.sse[new] = self.sse[a] + self.sse[b] + raw
        self.members[new] = self.members[a] + self.members[b]
        self.incident_edges[new] = self.incident_edges.get(a, set()) | self.incident_edges.get(b, set())
        self.active.remove(a); self.active.remove(b); self.active.add(new)
        self.version[new] = 0
        self.current_sse += raw
        self.current_fragmentation += dh
        self.semantic_deltas.append(ds)
        self.structural_deltas.append(dh)
        self.merge_log.append({"new": new, "left": a, "right": b, "delta_J": dj,
                               "delta_S_normalized": ds, "delta_H": dh,
                               "group_count_after": len(self.active)})
        for old in (a, b):
            self.version[old] = self.version.get(old, 0) + 1
        for other in sorted(self.active):
            if other != new:
                self._push(new, other)
        return self.merge_log[-1]

    def partition(self) -> dict[str, list[str]]:
        return {f"c{cid}": list(self.members[cid]) for cid in sorted(self.active, key=lambda c: min(self.node_index[m] for m in self.members[c]))}


def direct_objective(graph: dict, embeddings, partition: dict[str, list[str]], lam: float, total_scatter: float | None = None) -> tuple[float, float, float]:
    np = _require_numpy()
    node_ids = [n["id"] for n in graph["nodes"]]
    idx = {n: i for i, n in enumerate(node_ids)}
    x = np.asarray(embeddings, dtype=float)
    if total_scatter is None:
        overall = x.mean(axis=0) if len(x) else np.zeros(0)
        total_scatter = float(((x - overall) ** 2).sum()) if len(x) else 0.0
    sse = 0.0
    for members in partition.values():
        rows = x[[idx[m] for m in members]]
        mean = rows.mean(axis=0)
        sse += float(((rows - mean) ** 2).sum())
    norm_sse = 0.0 if total_scatter == 0 else sse / total_scatter
    frag = fragmentation(coarsen(graph, partition))
    return norm_sse + lam * frag, norm_sse, frag


def run_engine(graph: dict, embeddings, *, lam: float, budgets: list[int] | None = None) -> dict:
    if lam < 0:
        raise ValueError("lambda must be nonnegative")
    budgets = list(DEFAULT_BUDGETS if budgets is None else budgets)
    targets = sorted({min(k, len(graph["nodes"])) for k in budgets} | {len(graph["nodes"])}, reverse=True)
    state = AgglomerativeState(graph, embeddings, lam)
    saved = {len(graph["nodes"]): state.partition()}
    start = time.perf_counter()
    wanted = set(targets)
    while len(state.active) > min(wanted):
        state.merge_once()
        if len(state.active) in wanted:
            saved[len(state.active)] = state.partition()
    runtime = time.perf_counter() - start
    # Continue to root to maintain one complete merge tree for diagnostics/cuts.
    while len(state.active) > 1:
        state.merge_once()
    tree = Tree(len(graph["nodes"]), state.children, state.distances,
                {i: (node_id,) for i, node_id in enumerate(state.node_ids)})
    node_by_id = {n["id"]: n for n in graph["nodes"]}
    hierarchy, quotients, level_summaries = [], {}, []
    ordered_specs = [(f"k{min(k, len(graph['nodes']))}", min(k, len(graph["nodes"]))) for k in budgets]
    ordered_specs.append((LEAF_LEVEL_NAME, len(graph["nodes"])))
    previous = None
    for level_index, (level_name, k) in enumerate(ordered_specs):
        partition = saved.get(k)
        if partition is None:
            clusters = cut_tree(tree, k)
            partition = _partition_from_clusters(tree, clusters, state.node_ids)
        parents = {gid: None for gid in partition} if previous is None else _parent_map(partition, previous)
        for gid, members in partition.items():
            hierarchy.append({"id": f"L{level_index}_{gid}", "level": level_index,
                              "level_name": level_name,
                              "parent_id": f"L{level_index - 1}_{parents[gid]}" if parents[gid] else None,
                              "member_ids": members,
                              "representative_members": [{"id": m, "type": node_by_id[m]["type"],
                                                          "surface_form": node_by_id[m]["surface_form"]}
                                                         for m in members[:5]],
                              "representative_names_provisional": True, "gloss": None})
        groups = {f"L{level_index}_{gid}": members for gid, members in partition.items()}
        q = coarsen(graph, groups)
        quotients[level_name] = q
        sizes = [len(v) for v in groups.values()]
        J, norm_sse, frag = direct_objective(graph, embeddings, groups, lam, state.total_scatter)
        level_summaries.append({"level": level_index, "level_name": level_name,
                                "requested_groups": k, "actual_groups": len(groups),
                                "cut_source": "saved_active_partition_at_group_count",
                                "normalized_sse": norm_sse, "fragmentation": frag,
                                "combined_objective": J,
                                "group_size_distribution": _size_distribution(sizes)})
        previous = partition
    deltas = {"semantic_delta_normalized": _delta_summary(state.semantic_deltas),
              "structural_delta": _delta_summary(state.structural_deltas),
              "combined_delta": _delta_summary([r["delta_J"] for r in state.merge_log])}
    return {"hierarchy": hierarchy, "quotients": quotients,
            "summary": {"baseline": f"hypergraph_agglomerative_minilm_lambda_{lam:g}_gamma_0",
                        "lambda": lam, "gamma": 0, "node_count": len(graph["nodes"]),
                        "edge_count": len(graph["hyperedges"]), "budgets": budgets,
                        "levels": level_summaries, "merge_runtime_seconds": runtime,
                        "total_runtime_seconds": runtime,
                        "total_scatter_Z_t": state.total_scatter,
                        "zero_scatter_semantic_contribution": state.zero_scatter,
                        "merge_delta_summaries": deltas,
                        "candidate_policy": "exact lazy heap over all active cluster pairs; stale entries recomputed; deterministic tie order by delta_J, delta_S, delta_H, cluster ids",
                        "objective": "delta_J = delta_S_raw/Z_t + lambda*delta_H; gamma rejected/unused"},
            "merge_log": state.merge_log}


def _delta_summary(values: list[float]) -> dict:
    if not values:
        return {"count": 0}
    vals = sorted(values)
    return {"count": len(vals), "min": vals[0], "median": vals[len(vals)//2],
            "mean": sum(vals)/len(vals), "max": vals[-1]}


def run(input_path: Path, embedding_cache: Path, semantic_summary: Path, output_dir: Path, *, lam: float, gamma: float = 0.0, budgets: list[int] | None = None) -> dict:
    if gamma != 0:
        raise ValueError("gamma must be 0 until temporal coupling exists")
    _empty_output_dir(output_dir)
    graph = load_graph(input_path)
    embeddings, emb_meta = load_cache(embedding_cache, graph["nodes"])
    semantic = json.loads(semantic_summary.read_text(encoding="utf-8"))
    if emb_meta.get("revision") != semantic.get("embedding_metadata", {}).get("revision"):
        raise ValueError("Embedding cache revision does not match semantic run summary")
    start = time.perf_counter()
    result = run_engine(graph, embeddings, lam=lam, budgets=budgets)
    result["summary"]["total_runtime_seconds"] = time.perf_counter() - start
    result["summary"]["input_path"] = str(input_path)
    result["summary"]["input_sha256"] = hashlib.sha256(input_path.read_bytes()).hexdigest()
    result["summary"]["embedding_cache"] = str(embedding_cache)
    result["summary"]["model_id"] = emb_meta.get("model_id")
    result["summary"]["model_revision"] = emb_meta.get("revision")
    result["summary"]["embedding_metadata"] = emb_meta
    write_json(output_dir / "hierarchy.json", {"supernodes": result["hierarchy"]})
    for level_name, quotient in result["quotients"].items():
        write_json(output_dir / f"quotient_{level_name}.json", quotient)
    write_json(output_dir / "summary.json", result["summary"])
    write_json(output_dir / "merge_log.json", {"merges": result["merge_log"]})
    write_json(output_dir / "inspection_k12.json", inspection_for_run(output_dir / "hierarchy.json", graph["nodes"], embeddings))
    return result["summary"]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=Path("data/processed/baseline_input/snapshot_2020.json"))
    p.add_argument("--embeddings", type=Path, default=Path("results/semantic_ward_2020/embeddings.npz"))
    p.add_argument("--semantic-summary", type=Path, default=Path("results/semantic_ward_2020/summary.json"))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--lambda", dest="lam", type=float, required=True)
    p.add_argument("--gamma", type=float, default=0.0)
    p.add_argument("--budgets", type=int, nargs="*", default=DEFAULT_BUDGETS)
    a = p.parse_args()
    try:
        summary = run(a.input, a.embeddings, a.semantic_summary, a.output, lam=a.lam, gamma=a.gamma, budgets=a.budgets)
    except ValueError as exc:
        p.error(str(exc))
    print(json.dumps({"output": str(a.output), "lambda": summary["lambda"],
                      "runtime_seconds": round(summary["total_runtime_seconds"], 3),
                      "levels": [{"level_name": l["level_name"], "actual_groups": l["actual_groups"],
                                  "normalized_sse": l["normalized_sse"], "fragmentation": l["fragmentation"],
                                  "combined_objective": l["combined_objective"]} for l in summary["levels"]]}, indent=2))


if __name__ == "__main__":
    main()
