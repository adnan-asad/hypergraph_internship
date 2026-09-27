"""Evaluation scaffolding and immutable protocol manifests.

This module does not score benchmark answers and does not tune clustering weights.
It writes requirement inventories and perturbation manifests for later evaluation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random

from .data_pipeline import load_graph, write_json


FINAL_RUNS = {
    "2020": "results/hypergraph_agglomerative_lambda_0p1_2020",
    "2022_gamma0": "results/temporal_lambda_0p1_gamma_0_2022",
    "2022_gamma0p1": "results/temporal_lambda_0p1_gamma_0p1_2022",
    "2024_gamma0": "results/temporal_lambda_0p1_gamma_0_2024",
    "2024_gamma0p1": "results/temporal_lambda_0p1_gamma_0p1_2024",
}


def requirement_inventory() -> dict:
    return {
        "P1_laminar_refinement": {
            "status": "implemented_and_unit_checked",
            "artifacts": ["hierarchy.json", "tests/test_hypergraph_agglomerative.py", "tests/test_temporal_hypergraph.py"],
            "remaining_evaluation": "Report coverage/nesting validation for final exported runs.",
        },
        "P2_size_budget": {
            "status": "implemented",
            "artifacts": ["summary.json levels actual_groups"],
            "remaining_evaluation": "Confirm budgets in metrics.json for selected snapshots.",
        },
        "P3_semantic_coherence": {
            "status": "not_yet_evaluated_independently",
            "artifacts": ["blind_development_review_hypergraph_2020.*"],
            "remaining_evaluation": "Use independent signal: blind human/LLM ratings or an embedding family not used for clustering; compare to null.",
        },
        "P4_hyperedge_fidelity": {
            "status": "implemented_reference_tests_exist",
            "artifacts": ["quotient_*.json", "tests/test_quotient.py"],
            "remaining_evaluation": "Report fragmentation and verify provenance preservation for final runs.",
        },
        "P5_temporal_stability": {
            "status": "implemented_development_metrics_only",
            "artifacts": ["temporal_identity_events.json", "results/temporal_comparison_2022_2024.json"],
            "remaining_evaluation": "Cross-snapshot ARI with confidence intervals and perturbation stability over five seeds.",
        },
        "P6_faithful_labels": {
            "status": "not_implemented",
            "artifacts": [],
            "remaining_evaluation": "Generate provisional labels/glosses from temporally filtered evidence, then measure overclaim rate via NLI or blind review.",
        },
        "T1_data_audit": {
            "status": "implemented",
            "artifacts": ["data/processed/baseline_input/audit.json"],
            "remaining_evaluation": "Summarize in report.",
        },
        "T2_method_formal_statement": {
            "status": "partly_documented",
            "artifacts": ["README.md", "docs/EVALUATION_PROTOCOL.md"],
            "remaining_evaluation": "Write final report section: objective, tradeoffs, complexity, guarantees vs empirical.",
        },
        "T3_temporal_coupling": {
            "status": "implemented_first_method",
            "artifacts": ["src/tkh_abstraction/temporal_hypergraph.py"],
            "remaining_evaluation": "Evaluate stability; do not treat implementation tests as evidence of quality.",
        },
        "T4_hyperedge_collapse": {
            "status": "implemented",
            "artifacts": ["src/tkh_abstraction/quotient.py", "docs/STEP_2_COARSENING.md"],
            "remaining_evaluation": "Explain what coarsening preserves/hides in report.",
        },
        "T5_labeling_faithfulness": {
            "status": "not_implemented",
            "artifacts": [],
            "remaining_evaluation": "Implement labeler and overclaim protocol; scores currently blank.",
        },
        "T6_extrinsic_utility": {
            "status": "not_started",
            "artifacts": ["questions.csv available; ground_truth.json intentionally not used for construction/tuning"],
            "remaining_evaluation": "Freeze retrieval procedure, then score hierarchy vs matched flat baseline against ground truth once, after method freeze.",
        },
    }


def perturbation_manifest(snapshot_path: Path, seeds: list[int], removal_fraction: float = 0.10) -> dict:
    graph = load_graph(snapshot_path)
    edge_ids = [e["id"] for e in graph["hyperedges"]]
    remove_n = round(len(edge_ids) * removal_fraction)
    records = []
    for seed in seeds:
        rng = random.Random(seed)
        removed = sorted(rng.sample(edge_ids, remove_n)) if remove_n else []
        records.append({"seed": seed, "removed_edge_count": len(removed), "removed_edge_ids": removed})
    return {
        "snapshot": str(snapshot_path),
        "node_policy": "hold all nodes and cached embeddings fixed",
        "edge_policy": "remove original hyperedge records only; do not clip members from retained edges",
        "historical_reference_policy": "for temporal perturbation stability, hold previous snapshot hierarchies fixed so the experiment measures sensitivity to current-snapshot edge evidence; use identical removed-edge samples across compared gamma configurations",
        "removal_fraction": removal_fraction,
        "original_edge_count": len(edge_ids),
        "seeds": records,
    }


def runtime_estimate(snapshot_paths: list[Path]) -> dict:
    rows = []
    for p in snapshot_paths:
        g = load_graph(p)
        n = len(g["nodes"])
        pairs = n * (n - 1) // 2
        rows.append({
            "snapshot": str(p), "nodes": n, "hyperedges": len(g["hyperedges"]),
            "initial_candidate_pairs": pairs,
            "heap_payload_estimate_gib_200B": pairs * 200 / 1024**3,
            "heap_payload_estimate_gib_300B": pairs * 300 / 1024**3,
        })
    return {"note": "Payload estimates exclude dictionaries, Python allocator overhead, stale lazy-heap entries, embeddings, and quotient export objects.", "snapshots": rows}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("results/evaluation_scaffold"))
    p.add_argument("--snapshots", type=Path, nargs="+", default=[Path("data/processed/baseline_input/snapshot_2022.json"), Path("data/processed/baseline_input/snapshot_2024.json")])
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    args = p.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        p.error("Output directory is not empty")
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "requirement_inventory.json", requirement_inventory())
    write_json(args.output / "runtime_estimate.json", runtime_estimate(args.snapshots))
    perturbations = {p.stem: perturbation_manifest(p, args.seeds) for p in args.snapshots}
    write_json(args.output / "perturbation_manifests.json", perturbations)
    print(f"Wrote evaluation scaffold to {args.output}")


if __name__ == "__main__":
    main()
