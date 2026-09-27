"""Lexical TF-IDF hierarchical baseline for one temporal snapshot.

This is a reproducible surface-form baseline. It is not independent semantic
understanding and it does not optimize hyperedge fragmentation or temporal
stability. The single dendrogram is cut at several resolutions so memberships are
nested by construction.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time

from .data_pipeline import load_graph, write_json
from .quotient import coarsen, fragmentation


DEFAULT_BUDGETS = [12, 48, 120]
LEAF_LEVEL_NAME = "leaves"
LINKAGES = {"average", "ward"}


@dataclass(frozen=True)
class Tree:
    node_count: int
    children: dict[int, tuple[int, int]]
    distances: dict[int, float]
    leaf_members: dict[int, tuple[str, ...]]

    @property
    def root(self) -> int:
        return self.node_count if self.node_count == 1 else 2 * self.node_count - 2


def _require_sklearn():
    try:
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.feature_extraction.text import TfidfVectorizer
        import sklearn
        import numpy
        import scipy
    except ImportError as exc:  # pragma: no cover - exercised manually in env setup
        raise RuntimeError(
            "Install the lexical baseline dependencies: scikit-learn, numpy, scipy"
        ) from exc
    return AgglomerativeClustering, TfidfVectorizer, sklearn, numpy, scipy


def _empty_output_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise ValueError("Output directory is not empty. Choose a new directory to preserve prior results.")
    path.mkdir(parents=True, exist_ok=True)


def _features(nodes: list[dict]):
    _AgglomerativeClustering, TfidfVectorizer, sklearn, numpy, scipy = _require_sklearn()
    texts = [n["surface_form"] for n in nodes]
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        lowercase=True,
        strip_accents="unicode",
        norm="l2",
    )
    matrix = vectorizer.fit_transform(texts)
    zero_rows = numpy.flatnonzero(numpy.asarray(matrix.getnnz(axis=1) == 0)).astype(int).tolist()
    metadata = {
        "text_fields": ["surface_form"],
        "vectorizer": {
            "analyzer": "char_wb",
            "ngram_range": [3, 5],
            "lowercase": True,
            "strip_accents": "unicode",
            "norm": "l2",
            "vocabulary_size": len(vectorizer.vocabulary_),
        },
        "matrix_shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "zero_vector_count": len(zero_rows),
        "zero_vector_node_ids": [nodes[i]["id"] for i in zero_rows],
    }
    return matrix, metadata, _dependency_versions(sklearn, numpy, scipy)


def _fit_tree(nodes: list[dict], linkage: str = "average") -> tuple[Tree, dict, dict]:
    AgglomerativeClustering, _TfidfVectorizer, _sklearn, _numpy, _scipy = _require_sklearn()
    if linkage not in LINKAGES:
        raise ValueError(f"linkage must be one of {sorted(LINKAGES)}")
    node_ids = [n["id"] for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("Duplicate node IDs are not supported")
    leaf_members = {i: (node_id,) for i, node_id in enumerate(node_ids)}
    matrix, feature_metadata, dependency_versions = _features(nodes)
    if feature_metadata["zero_vector_count"]:
        raise ValueError("TF-IDF produced zero vectors; cosine/Ward comparison would be ill-defined")
    if len(nodes) == 1:
        return Tree(1, {}, {}, leaf_members), dependency_versions, feature_metadata

    dense = matrix.toarray()
    if linkage == "average":
        # Average linkage is compatible with cosine distances in scikit-learn.
        metric = "cosine"
    else:
        # Ward must use Euclidean geometry. It is not Ward-on-cosine.
        metric = "euclidean"
    model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.0,
        metric=metric,
        linkage=linkage,
        compute_distances=True,
    )
    model.fit(dense)
    children = {}
    distances = {}
    for row, pair in enumerate(model.children_):
        internal = len(nodes) + row
        children[internal] = (int(pair[0]), int(pair[1]))
        distances[internal] = float(model.distances_[row])
    return Tree(len(nodes), children, distances, leaf_members), dependency_versions, feature_metadata


def ward_delta_sse(group_a, group_b) -> float:
    """Exact Ward increase in within-cluster squared error for two groups.

    Uses arithmetic means: n_A*n_B/(n_A+n_B) * ||mean_A - mean_B||^2.
    This is an objective increase, not necessarily the linkage height reported by
    a clustering library.
    """
    _AgglomerativeClustering, _TfidfVectorizer, _sklearn, numpy, _scipy = _require_sklearn()
    a = numpy.asarray(group_a, dtype=float)
    b = numpy.asarray(group_b, dtype=float)
    if a.ndim != 2 or b.ndim != 2 or a.shape[1] != b.shape[1] or len(a) == 0 or len(b) == 0:
        raise ValueError("Groups must be nonempty 2D arrays with the same feature dimension")
    diff = a.mean(axis=0) - b.mean(axis=0)
    return float((len(a) * len(b) / (len(a) + len(b))) * numpy.dot(diff, diff))


def _dependency_versions(sklearn, numpy, scipy) -> dict:
    versions = {
        "python_requires": ">=3.10",
        "scikit-learn": sklearn.__version__,
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
    }
    try:
        import cloudpickle
        import joblib
        import threadpoolctl
        versions["cloudpickle"] = cloudpickle.__version__
        versions["joblib"] = joblib.__version__
        versions["threadpoolctl"] = threadpoolctl.__version__
    except ImportError:
        pass
    return versions


def _members_for_cluster(tree: Tree, cluster: int, cache: dict[int, tuple[int, ...]]) -> tuple[int, ...]:
    if cluster in cache:
        return cache[cluster]
    if cluster < tree.node_count:
        cache[cluster] = (cluster,)
    else:
        left, right = tree.children[cluster]
        cache[cluster] = _members_for_cluster(tree, left, cache) + _members_for_cluster(tree, right, cache)
    return cache[cluster]


def cut_tree(tree: Tree, target_groups: int) -> list[int]:
    """Return cluster ids for one nested horizontal cut of the dendrogram."""
    if target_groups < 1:
        raise ValueError("target_groups must be positive")
    wanted = min(target_groups, tree.node_count)
    clusters = [tree.root]
    while len(clusters) < wanted:
        split_candidates = [c for c in clusters if c in tree.children]
        if not split_candidates:
            break
        # Split the highest-distance remaining merge. This is the usual top-down
        # reading of a single agglomerative dendrogram and yields nested cuts.
        selected = max(split_candidates, key=lambda c: (tree.distances.get(c, 0.0), c))
        clusters.remove(selected)
        clusters.extend(tree.children[selected])
    cache: dict[int, tuple[int, ...]] = {}
    return sorted(clusters, key=lambda c: min(_members_for_cluster(tree, c, cache)))


def _partition_from_clusters(tree: Tree, clusters: list[int], node_ids: list[str]) -> dict[str, list[str]]:
    cache: dict[int, tuple[int, ...]] = {}
    return {
        f"c{cluster}": [node_ids[i] for i in _members_for_cluster(tree, cluster, cache)]
        for cluster in clusters
    }


def _parent_map(child_partition: dict[str, list[str]], parent_partition: dict[str, list[str]]) -> dict[str, str]:
    parent_by_node = {}
    for pid, members in parent_partition.items():
        for node_id in members:
            parent_by_node[node_id] = pid
    result = {}
    for cid, members in child_partition.items():
        parents = {parent_by_node[m] for m in members}
        if len(parents) != 1:
            raise ValueError("Cuts are not nested; child group spans multiple parents")
        result[cid] = next(iter(parents))
    return result


def _size_distribution(sizes: list[int]) -> dict:
    if not sizes:
        return {"min": 0, "max": 0, "histogram": {}}
    return {"min": min(sizes), "max": max(sizes), "histogram": dict(sorted(Counter(sizes).items()))}


def build_baseline(snapshot: dict, budgets: list[int] | None = None, linkage: str = "average") -> dict:
    """Build hierarchy and quotient data structures without writing files."""
    budgets = list(DEFAULT_BUDGETS if budgets is None else budgets)
    if linkage not in LINKAGES:
        raise ValueError(f"linkage must be one of {sorted(LINKAGES)}")
    nodes = snapshot["nodes"]
    node_ids = [n["id"] for n in nodes]
    node_by_id = {n["id"]: n for n in nodes}
    tree, dependency_versions, feature_metadata = _fit_tree(nodes, linkage=linkage)

    level_specs = [(f"k{min(k, len(nodes))}", min(k, len(nodes)), cut_tree(tree, k)) for k in budgets]
    level_specs.append((LEAF_LEVEL_NAME, len(nodes), list(range(len(nodes)))))

    hierarchy = []
    partitions = {}
    previous_partition = None
    for level_index, (level_name, actual_k, clusters) in enumerate(level_specs):
        partition = _partition_from_clusters(tree, clusters, node_ids)
        if len(partition) != actual_k:
            raise ValueError("Unexpected group count from tree cut")
        parents = {gid: None for gid in partition}
        if previous_partition is not None:
            parents = _parent_map(partition, previous_partition)
        for gid, members in partition.items():
            hierarchy.append({
                "id": f"L{level_index}_{gid}",
                "level": level_index,
                "level_name": level_name,
                "parent_id": f"L{level_index - 1}_{parents[gid]}" if parents[gid] is not None else None,
                "member_ids": members,
                "representative_members": [
                    {"id": m, "type": node_by_id[m]["type"], "surface_form": node_by_id[m]["surface_form"]}
                    for m in members[:5]
                ],
                "representative_names": [node_by_id[m]["surface_form"] for m in members[:5]],
                "representative_names_provisional": True,
                "gloss": None,
            })
        partitions[level_name] = partition
        previous_partition = partition

    quotient_by_level = {}
    level_summaries = []
    for level_index, (level_name, actual_k, _clusters) in enumerate(level_specs):
        # Prefix partition ids to keep quotient supernode ids identical to hierarchy ids.
        groups = {f"L{level_index}_{gid}": members for gid, members in partitions[level_name].items()}
        q = coarsen(snapshot, groups)
        frag = fragmentation(q)
        quotient_by_level[level_name] = q
        sizes = [len(v) for v in groups.values()]
        level_summaries.append({
            "level": level_index,
            "level_name": level_name,
            "requested_groups": budgets[level_index] if level_index < len(budgets) else len(nodes),
            "actual_groups": len(groups),
            "fragmentation": frag,
            "group_size_distribution": _size_distribution(sizes),
        })

    return {
        "hierarchy": hierarchy,
        "quotients": quotient_by_level,
        "summary": {
            "baseline": f"lexical_tfidf_agglomerative_{'cosine_average' if linkage == 'average' else 'euclidean_ward'}",
            "scientific_quality_warning": (
                "Execution success only. This surface-form baseline is not independent semantic "
                "understanding and does not optimize hyperedge fragmentation or temporal stability."
            ),
            "snapshot_meta": snapshot.get("meta", {}),
            "node_count": len(nodes),
            "edge_count": len(snapshot["hyperedges"]),
            "budgets": budgets,
            "levels": level_summaries,
            "dependencies": dependency_versions,
            "feature_metadata": feature_metadata,
            "node_ordering": "input snapshot order is preserved; ties are resolved deterministically by scikit-learn for fixed input order and by descending cluster id in cut_tree",
            "distance": ("cosine over character n-gram TF-IDF(surface_form)" if linkage == "average"
                         else "Euclidean over the same character n-gram TF-IDF(surface_form)"),
            "linkage": linkage,
        },
    }


def run(input_path: Path, output_dir: Path, budgets: list[int] | None = None, linkage: str = "average") -> dict:
    _empty_output_dir(output_dir)
    start = time.perf_counter()
    snapshot = load_graph(input_path)
    result = build_baseline(snapshot, budgets, linkage=linkage)
    elapsed = time.perf_counter() - start
    result["summary"]["runtime_seconds"] = elapsed
    result["summary"]["input_path"] = str(input_path)
    result["summary"]["input_sha256"] = hashlib.sha256(input_path.read_bytes()).hexdigest()

    write_json(output_dir / "hierarchy.json", {"supernodes": result["hierarchy"]})
    for level_name, quotient in result["quotients"].items():
        write_json(output_dir / f"quotient_{level_name}.json", quotient)
    write_json(output_dir / "summary.json", result["summary"])
    write_json(output_dir / "dependencies.json", result["summary"]["dependencies"])
    return result["summary"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Snapshot JSON, e.g. snapshot_2020.json")
    parser.add_argument("--output", type=Path, required=True, help="New or empty output directory")
    parser.add_argument("--budgets", type=int, nargs="*", default=DEFAULT_BUDGETS,
                        help="Nested group budgets before singleton leaves")
    parser.add_argument("--linkage", choices=sorted(LINKAGES), default="average",
                        help="average = cosine average linkage; ward = Euclidean Ward on the same TF-IDF features")
    args = parser.parse_args()
    try:
        summary = run(args.input, args.output, args.budgets, linkage=args.linkage)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps({
        "output": str(args.output),
        "node_count": summary["node_count"],
        "edge_count": summary["edge_count"],
        "runtime_seconds": round(summary["runtime_seconds"], 3),
        "levels": [{"level_name": l["level_name"], "actual_groups": l["actual_groups"],
                    "fragmentation": l["fragmentation"]} for l in summary["levels"]],
    }, indent=2))


if __name__ == "__main__":
    main()
