"""Frozen sentence-transformer Ward baseline for the 2020 snapshot.

Semantic-only control: surface_form inputs, frozen all-MiniLM-L6-v2 embeddings,
Euclidean Ward linkage, no hypergraph/temporal tuning terms.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import time

from .data_pipeline import load_graph, write_json
from .lexical_baseline import (DEFAULT_BUDGETS, LEAF_LEVEL_NAME, Tree, _empty_output_dir,
                               _members_for_cluster, _parent_map, _partition_from_clusters,
                               _size_distribution, cut_tree)
from .quotient import coarsen, fragmentation

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def node_signature(nodes: list[dict]) -> dict:
    return {"node_ids": [n["id"] for n in nodes],
            "text_hashes": [text_hash(n["surface_form"]) for n in nodes]}


def validate_embeddings(node_ids: list[str], text_hashes: list[str], embeddings) -> None:
    import numpy as np
    x = np.asarray(embeddings, dtype=float)
    if x.ndim != 2 or x.shape[0] != len(node_ids) or len(node_ids) != len(text_hashes):
        raise ValueError("Embedding shape does not match node/text metadata")
    if not np.isfinite(x).all():
        raise ValueError("Embeddings contain non-finite values")
    norms = np.linalg.norm(x, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-5):
        raise ValueError("Embeddings must be L2-normalized per node")


def save_cache(path: Path, *, node_ids: list[str], text_hashes: list[str], embeddings, metadata: dict) -> None:
    import numpy as np
    validate_embeddings(node_ids, text_hashes, embeddings)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, embeddings=np.asarray(embeddings, dtype="float32"),
                        node_ids=np.asarray(node_ids), text_hashes=np.asarray(text_hashes),
                        metadata=json.dumps(metadata, ensure_ascii=False))


def load_cache(path: Path, nodes: list[dict]):
    import numpy as np
    expected = node_signature(nodes)
    data = np.load(path, allow_pickle=False)
    node_ids = [str(x) for x in data["node_ids"].tolist()]
    text_hashes = [str(x) for x in data["text_hashes"].tolist()]
    if node_ids != expected["node_ids"] or text_hashes != expected["text_hashes"]:
        raise ValueError("Embedding cache does not match current node order/text hashes")
    embeddings = data["embeddings"]
    validate_embeddings(node_ids, text_hashes, embeddings)
    metadata = json.loads(str(data["metadata"].tolist()))
    return embeddings, metadata


def dependency_versions() -> dict:
    import sentence_transformers, transformers, torch, huggingface_hub, tokenizers, numpy, sklearn, scipy
    versions = {"python_requires": ">=3.10", "sentence-transformers": sentence_transformers.__version__,
                "transformers": transformers.__version__, "torch": torch.__version__,
                "huggingface-hub": huggingface_hub.__version__, "tokenizers": tokenizers.__version__,
                "numpy": numpy.__version__, "scikit-learn": sklearn.__version__, "scipy": scipy.__version__}
    for name in ["certifi", "charset_normalizer", "filelock", "fsspec", "idna", "jinja2",
                 "networkx", "packaging", "PIL", "requests", "safetensors", "sympy", "tqdm", "urllib3"]:
        try:
            module = __import__(name)
            key = "Pillow" if name == "PIL" else name.replace("_", "-")
            versions[key] = getattr(module, "__version__", "unknown")
        except ImportError:
            pass
    return versions


def resolve_revision(model_id: str = MODEL_ID) -> str:
    from huggingface_hub import HfApi
    return HfApi().model_info(model_id).sha


def encode_nodes(nodes: list[dict], *, revision: str, device: str | None = None):
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    start = time.perf_counter()
    selected_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = SentenceTransformer(MODEL_ID, revision=revision, device=selected_device)
    texts = [n["surface_form"] for n in nodes]
    max_len = int(model.max_seq_length)
    tokenizer = model.tokenizer
    tokenized = tokenizer(texts, padding=False, truncation=False, add_special_tokens=True)
    lengths = [len(ids) for ids in tokenized["input_ids"]]
    truncated = [i for i, length in enumerate(lengths) if length > max_len]
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True,
                              convert_to_numpy=True, normalize_embeddings=True)
    embeddings = np.asarray(embeddings, dtype="float32")
    validate_embeddings([n["id"] for n in nodes], [text_hash(t) for t in texts], embeddings)
    elapsed = time.perf_counter() - start
    metadata = {"model_id": MODEL_ID, "revision": revision, "device": selected_device,
                "max_seq_length": max_len, "tokenizer_class": tokenizer.__class__.__name__,
                "tokenizer_settings": {"padding": False, "truncation": False,
                                       "add_special_tokens_for_count": True},
                "truncation_count": len(truncated),
                "truncated_node_ids": [nodes[i]["id"] for i in truncated],
                "max_observed_token_length": max(lengths) if lengths else 0,
                "encoding_runtime_seconds": elapsed,
                "dependencies": dependency_versions()}
    return embeddings, metadata


def fit_ward_tree(embeddings, node_ids: list[str]) -> Tree:
    from sklearn.cluster import AgglomerativeClustering
    if len(node_ids) == 1:
        return Tree(1, {}, {}, {0: (node_ids[0],)})
    model = AgglomerativeClustering(n_clusters=None, distance_threshold=0.0,
                                    metric="euclidean", linkage="ward", compute_distances=True)
    model.fit(embeddings)
    children, distances = {}, {}
    for row, pair in enumerate(model.children_):
        internal = len(node_ids) + row
        children[internal] = (int(pair[0]), int(pair[1]))
        distances[internal] = float(model.distances_[row])
    return Tree(len(node_ids), children, distances, {i: (node_id,) for i, node_id in enumerate(node_ids)})


def build_outputs(snapshot: dict, embeddings, *, budgets: list[int] | None, embedding_metadata: dict,
                  clustering_runtime_seconds: float = 0.0) -> dict:
    budgets = list(DEFAULT_BUDGETS if budgets is None else budgets)
    nodes = snapshot["nodes"]
    node_ids = [n["id"] for n in nodes]
    node_by_id = {n["id"]: n for n in nodes}
    tree = fit_ward_tree(embeddings, node_ids)
    level_specs = [(f"k{min(k, len(nodes))}", min(k, len(nodes)), cut_tree(tree, k)) for k in budgets]
    level_specs.append((LEAF_LEVEL_NAME, len(nodes), list(range(len(nodes)))))
    hierarchy, partitions, previous = [], {}, None
    for level_index, (level_name, _actual_k, clusters) in enumerate(level_specs):
        partition = _partition_from_clusters(tree, clusters, node_ids)
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
        partitions[level_name] = partition
        previous = partition
    quotients, level_summaries = {}, []
    for level_index, (level_name, _actual_k, _clusters) in enumerate(level_specs):
        groups = {f"L{level_index}_{gid}": members for gid, members in partitions[level_name].items()}
        q = coarsen(snapshot, groups)
        quotients[level_name] = q
        sizes = [len(v) for v in groups.values()]
        level_summaries.append({"level": level_index, "level_name": level_name,
                                "requested_groups": budgets[level_index] if level_index < len(budgets) else len(nodes),
                                "actual_groups": len(groups), "fragmentation": fragmentation(q),
                                "group_size_distribution": _size_distribution(sizes)})
    summary = {"baseline": "semantic_all-MiniLM-L6-v2_euclidean_ward_lambda0_gamma0",
               "scientific_quality_warning": "Semantic-only control; no hypergraph or temporal terms and no validated scientific glosses.",
               "snapshot_meta": snapshot.get("meta", {}), "node_count": len(nodes),
               "edge_count": len(snapshot["hyperedges"]), "budgets": budgets,
               "levels": level_summaries, "embedding_metadata": embedding_metadata,
               "clustering_runtime_seconds": clustering_runtime_seconds,
               "distance": "Euclidean over L2-normalized sentence-transformer embeddings",
               "linkage": "ward", "lambda": 0, "gamma": 0,
               "centroid_policy": "arithmetic means of normalized node vectors; group centroids are not renormalized"}
    return {"hierarchy": hierarchy, "quotients": quotients, "summary": summary}


def inspection_for_run(hierarchy_path: Path, nodes: list[dict], vectors, *, seed: int = 0) -> list[dict]:
    import numpy as np
    node_by_id = {n["id"]: n for n in nodes}
    index = {n["id"]: i for i, n in enumerate(nodes)}
    rows = [r for r in json.loads(hierarchy_path.read_text(encoding="utf-8"))["supernodes"] if r["level"] == 0]
    rng = random.Random(seed)
    result = []
    for row in rows:
        member_ids = row["member_ids"]
        idx = [index[m] for m in member_ids]
        centroid = vectors[idx].mean(axis=0)
        dist = [(float(np.linalg.norm(vectors[i] - centroid)), nodes[i]["id"]) for i in idx]
        nearest = [m for _d, m in sorted(dist)[:5]]
        farthest = [m for _d, m in sorted(dist, reverse=True)[:5]]
        sample = rng.sample(member_ids, min(5, len(member_ids)))
        def pack(ids):
            seen, packed = set(), []
            for m in ids:
                if m in seen: continue
                seen.add(m); n = node_by_id[m]
                packed.append({"id": m, "type": n["type"], "surface_form": n["surface_form"]})
            return packed
        result.append({"id": row["id"], "size": len(member_ids),
                       "type_counts": dict(Counter(node_by_id[m]["type"] for m in member_ids).most_common()),
                       "nearest_to_centroid": pack(nearest), "random_sample_seed": seed,
                       "random_sample": pack(sample), "farthest_from_centroid": pack(farthest)})
    return result


def run(input_path: Path, output_dir: Path, cache_path: Path | None = None,
        revision: str | None = None, budgets: list[int] | None = None) -> dict:
    _empty_output_dir(output_dir)
    total_start = time.perf_counter()
    snapshot = load_graph(input_path)
    nodes = snapshot["nodes"]
    resolved_revision = revision or resolve_revision(MODEL_ID)
    cache = cache_path or output_dir / "embeddings.npz"
    input_sha = hashlib.sha256(input_path.read_bytes()).hexdigest()
    if cache.exists():
        embeddings, emb_meta = load_cache(cache, nodes)
    else:
        embeddings, emb_meta = encode_nodes(nodes, revision=resolved_revision)
        emb_meta["input_sha256"] = input_sha
        sig = node_signature(nodes)
        save_cache(cache, node_ids=sig["node_ids"], text_hashes=sig["text_hashes"],
                   embeddings=embeddings, metadata=emb_meta)
    cluster_start = time.perf_counter()
    result = build_outputs(snapshot, embeddings, budgets=budgets, embedding_metadata=emb_meta,
                           clustering_runtime_seconds=0.0)
    result["summary"]["clustering_runtime_seconds"] = time.perf_counter() - cluster_start
    result["summary"]["runtime_seconds"] = time.perf_counter() - total_start
    result["summary"]["input_path"] = str(input_path)
    result["summary"]["input_sha256"] = input_sha
    result["summary"]["embedding_cache"] = str(cache)
    write_json(output_dir / "hierarchy.json", {"supernodes": result["hierarchy"]})
    for level_name, quotient in result["quotients"].items():
        write_json(output_dir / f"quotient_{level_name}.json", quotient)
    write_json(output_dir / "summary.json", result["summary"])
    write_json(output_dir / "dependencies.json", emb_meta["dependencies"])
    write_json(output_dir / "inspection_k12.json", inspection_for_run(output_dir / "hierarchy.json", nodes, embeddings))
    return result["summary"]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--cache", type=Path)
    p.add_argument("--revision", help="Immutable model commit SHA; resolved from Hub if omitted")
    p.add_argument("--budgets", type=int, nargs="*", default=DEFAULT_BUDGETS)
    a = p.parse_args()
    try:
        summary = run(a.input, a.output, cache_path=a.cache, revision=a.revision, budgets=a.budgets)
    except ValueError as exc:
        p.error(str(exc))
    print(json.dumps({"output": str(a.output), "node_count": summary["node_count"],
                      "edge_count": summary["edge_count"],
                      "encoding_runtime_seconds": round(summary["embedding_metadata"].get("encoding_runtime_seconds", 0), 3),
                      "clustering_runtime_seconds": round(summary["clustering_runtime_seconds"], 3),
                      "runtime_seconds": round(summary["runtime_seconds"], 3),
                      "truncation_count": summary["embedding_metadata"].get("truncation_count"),
                      "levels": [{"level_name": l["level_name"], "actual_groups": l["actual_groups"],
                                  "fragmentation": l["fragmentation"]} for l in summary["levels"]]}, indent=2))


if __name__ == "__main__":
    main()
