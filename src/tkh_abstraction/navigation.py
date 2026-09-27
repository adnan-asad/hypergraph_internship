"""Navigation cuts and selective expansion from saved merge histories.

This replays existing merge logs. It does not recluster, retune, or sort merges by
cost. Additional cuts are navigation views of an existing run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data_pipeline import load_graph, write_json
from .quotient import coarsen, fragmentation


def load_merges(run: Path) -> list[dict]:
    path = run / "merge_log.json"
    if not path.exists():
        raise ValueError(f"Missing merge history: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    merges = data.get("merges")
    if not isinstance(merges, list):
        raise ValueError(f"Invalid merge history schema: {path}")
    return merges


def replay_partitions(graph: dict, merges: list[dict], targets: set[int]) -> dict[int, dict[int, list[str]]]:
    node_ids = [n["id"] for n in graph["nodes"]]
    active = {i: [node_id] for i, node_id in enumerate(node_ids)}
    saved = {}
    if len(active) in targets:
        saved[len(active)] = {k: list(v) for k, v in active.items()}
    for row in merges:
        left, right, new = row.get("left"), row.get("right"), row.get("new")
        if left not in active or right not in active:
            raise ValueError(f"Merge log is not replayable at merge {row}")
        active[new] = active.pop(left) + active.pop(right)
        if len(active) in targets:
            saved[len(active)] = {k: list(v) for k, v in active.items()}
    missing = targets - set(saved)
    if missing:
        raise ValueError(f"Merge history does not reach requested active counts: {sorted(missing)}")
    return saved


def partition_groups(partition: dict[int, list[str]], prefix: str) -> dict[str, list[str]]:
    return {f"{prefix}_m{cid}": members for cid, members in sorted(partition.items())}


def verify_nested(finer: dict[int, list[str]], coarser: dict[int, list[str]]) -> None:
    parent_by_node = {}
    for cid, members in coarser.items():
        for m in members:
            parent_by_node[m] = cid
    for cid, members in finer.items():
        parents = {parent_by_node[m] for m in members}
        if len(parents) != 1:
            raise ValueError(f"Partition is not nested at cluster {cid}")


def export_cuts(snapshot: Path, run: Path, output: Path, cuts: list[int]) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory is not empty")
    output.mkdir(parents=True, exist_ok=True)
    graph = load_graph(snapshot)
    merges = load_merges(run)
    all_cuts = sorted(set(cuts + [12, 24, 48, 80, 120]), reverse=True)
    parts = replay_partitions(graph, merges, set(all_cuts))
    # Verify requested navigation chain where available: 120 -> 80 -> 48 -> 24 -> 12.
    chain = [120, 80, 48, 24, 12]
    for a, b in zip(chain, chain[1:]):
        verify_nested(parts[a], parts[b])
    summary = {"source_run": str(run), "snapshot": str(snapshot),
               "note": "Additional cuts replay existing merge history; not independently optimized temporal resolutions.",
               "cuts": {}}
    for k in cuts:
        groups = partition_groups(parts[k], f"k{k}")
        quotient = coarsen(graph, groups)
        rows = [{"id": gid, "merge_tree_id": int(gid.split("_m")[-1]), "level_name": f"k{k}",
                 "member_ids": members, "representative_text": representative_text(graph, members)}
                for gid, members in groups.items()]
        write_json(output / f"hierarchy_k{k}.json", {"supernodes": rows})
        write_json(output / f"quotient_k{k}.json", quotient)
        summary["cuts"][f"k{k}"] = {"groups": len(groups), "fragmentation": fragmentation(quotient)}
    write_json(output / "navigation_summary.json", summary)
    return summary


def representative_text(graph: dict, members: list[str], limit: int = 5) -> list[str]:
    node = {n["id"]: n for n in graph["nodes"]}
    return [node[m]["surface_form"] for m in members[:limit] if m in node]


def children_map(merges: list[dict]) -> dict[int, tuple[int, int]]:
    return {row["new"]: (row["left"], row["right"]) for row in merges}


def parent_map(merges: list[dict]) -> dict[tuple[int, int], int]:
    result = {}
    for row in merges:
        a, b = row["left"], row["right"]
        if b < a:
            a, b = b, a
        result[(a, b)] = row["new"]
    return result


def init_frontier(snapshot: Path, run: Path, output: Path) -> dict:
    graph = load_graph(snapshot)
    part = replay_partitions(graph, load_merges(run), {12})[12]
    state = {"snapshot": str(snapshot), "run": str(run), "frontier": sorted(part),
             "note": "Frontier merge_tree_ids are local to this run, not temporal persistent IDs."}
    write_json(output, state)
    return state


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frontier_partition(state: dict) -> dict[int, list[str]]:
    graph = load_graph(Path(state["snapshot"]))
    merges = load_merges(Path(state["run"]))
    # Replay until every requested frontier node has been created; then materialize members from all merge definitions.
    node_ids = [n["id"] for n in graph["nodes"]]
    members = {i: [node_id] for i, node_id in enumerate(node_ids)}
    for row in merges:
        if row["left"] in members and row["right"] in members:
            members[row["new"]] = members[row["left"]] + members[row["right"]]
    frontier = state["frontier"]
    part = {cid: members[cid] for cid in frontier}
    assert_exact_cover(graph, part)
    return part


def assert_exact_cover(graph: dict, part: dict[int, list[str]]) -> None:
    expected = {n["id"] for n in graph["nodes"]}
    seen = [m for members in part.values() for m in members]
    if set(seen) != expected or len(seen) != len(expected):
        raise ValueError("Frontier does not cover every node exactly once")


def expand(state_path: Path, cluster: int, output: Path | None = None) -> dict:
    state = load_state(state_path)
    cmap = children_map(load_merges(Path(state["run"])))
    if cluster not in state["frontier"]:
        raise ValueError(f"Cluster {cluster} is not visible")
    if cluster not in cmap:
        raise ValueError(f"Cluster {cluster} is a leaf and cannot be expanded")
    frontier = [c for c in state["frontier"] if c != cluster] + list(cmap[cluster])
    state["frontier"] = sorted(frontier)
    frontier_partition(state)  # validate exact cover
    write_json(output or state_path, state)
    return state


def collapse(state_path: Path, left: int, right: int, output: Path | None = None) -> dict:
    state = load_state(state_path)
    if left not in state["frontier"] or right not in state["frontier"]:
        raise ValueError("Both clusters must be visible")
    a, b = sorted((left, right))
    pmap = parent_map(load_merges(Path(state["run"])))
    parent = pmap.get((a, b))
    if parent is None:
        raise ValueError("Visible clusters are not siblings")
    frontier = [c for c in state["frontier"] if c not in (left, right)] + [parent]
    state["frontier"] = sorted(frontier)
    frontier_partition(state)
    write_json(output or state_path, state)
    return state


def list_frontier(state_path: Path) -> dict:
    state = load_state(state_path)
    graph = load_graph(Path(state["snapshot"]))
    part = frontier_partition(state)
    rows = [{"merge_tree_id": cid, "size": len(members),
             "representative_text_unvalidated": representative_text(graph, members)}
            for cid, members in sorted(part.items())]
    return {"frontier_size": len(rows), "groups": rows}


def export_frontier(state_path: Path, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory is not empty")
    output.mkdir(parents=True, exist_ok=True)
    state = load_state(state_path)
    graph = load_graph(Path(state["snapshot"]))
    part = frontier_partition(state)
    groups = partition_groups(part, "frontier")
    quotient = coarsen(graph, groups)
    rows = [{"id": gid, "merge_tree_id": int(gid.split("_m")[-1]), "member_ids": members,
             "representative_text_unvalidated": representative_text(graph, members)}
            for gid, members in groups.items()]
    write_json(output / "frontier_state.json", state)
    write_json(output / "hierarchy_frontier.json", {"supernodes": rows})
    write_json(output / "quotient_frontier.json", quotient)
    summary = {"frontier_size": len(rows), "fragmentation": fragmentation(quotient),
               "note": "Quotient rebuilt from original hyperedges for mixed-depth frontier."}
    write_json(output / "frontier_summary.json", summary)
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export-cuts"); e.add_argument("--snapshot", type=Path, required=True); e.add_argument("--run", type=Path, required=True); e.add_argument("--output", type=Path, required=True); e.add_argument("--cuts", type=int, nargs="+", default=[80, 24])
    i = sub.add_parser("init"); i.add_argument("--snapshot", type=Path, required=True); i.add_argument("--run", type=Path, required=True); i.add_argument("--state", type=Path, required=True)
    l = sub.add_parser("list"); l.add_argument("--state", type=Path, required=True)
    x = sub.add_parser("expand"); x.add_argument("--state", type=Path, required=True); x.add_argument("--cluster", type=int, required=True); x.add_argument("--output", type=Path)
    c = sub.add_parser("collapse"); c.add_argument("--state", type=Path, required=True); c.add_argument("--left", type=int, required=True); c.add_argument("--right", type=int, required=True); c.add_argument("--output", type=Path)
    f = sub.add_parser("export-frontier"); f.add_argument("--state", type=Path, required=True); f.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.cmd == "export-cuts": result = export_cuts(a.snapshot, a.run, a.output, a.cuts)
    elif a.cmd == "init": result = init_frontier(a.snapshot, a.run, a.state)
    elif a.cmd == "list": result = list_frontier(a.state)
    elif a.cmd == "expand": result = expand(a.state, a.cluster, a.output)
    elif a.cmd == "collapse": result = collapse(a.state, a.left, a.right, a.output)
    else: result = export_frontier(a.state, a.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
