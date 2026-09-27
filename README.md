# Temporal Hypergraph Abstraction

## Submission entry points

Start with **[report.md](report.md)** (final concise report), **[metrics.json](metrics.json)** (measured evidence), and **[docs/SUBMISSION_STATUS.md](docs/SUBMISSION_STATUS.md)** (requirement coverage and limits). Earlier milestone docs below are retained as development history.

- `submission/2020/hierarchy.json`, `submission/2022/hierarchy.json`, `submission/2024/hierarchy.json`, `submission/2026/hierarchy.json`: canonical labelled nested exports with corrected stable singleton identities.
- Each snapshot directory also contains `temporal_events.json`. Original quotients, merge logs, controls, perturbations and summaries remain under `results/`.
- `docs/developer_review/`: actual developer annotations, reproducible descriptive counts, and limitations. Not an independent expert review.
- `verification/`: this packaging pass's test log and recomputed saved-result checks.
- `COMMIT_CHECKLIST.md`: what to copy and commit to the existing repository.

The assessor-approved **blind LLM evaluation** is in `evaluation_llm/LLM_EVALUATION_REPORT.md`: coherence versus matched nulls, 32 level-0/1 faithfulness judgments and all 18 benchmark questions. Fresh human spot-checks are in `evaluation_llm/human_spotchecks.md` and its CSV. Frozen hierarchy retrieval did not establish an accuracy advantage.

After adding genuine human spot-check entries, refresh the supplemental metrics/report with:

```bash
python scripts/summarize_blind_evaluation.py
python scripts/write_llm_report.py
```

This preserves the human CSV and independent LLM ratings. Update the report's human-completion sentence when all checks are actually complete. To reproduce packet sampling, run `PYTHONPATH=src python scripts/prepare_blind_evaluation.py` with the supplied files in `data/raw/`; send anonymized packets to fresh judges using the recorded protocol. Judge outputs are retained because LLM evaluation is not deterministically reproducible. Do not show judges the identity key.

## Quick verification without model download

Use Python 3.10–3.12. The packaging tests ran on Windows/Python 3.12.14 with the numerical packages pinned here; original experiments ran on Linux/Python 3.10.21. In WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/verify_saved_results.py
```

Put the assessor's original files in `data/raw/` (not committed). Then rebuild the final export audit and consolidated metrics without training or clustering:

```bash
PYTHONPATH=src python -m tkh_abstraction.submission_audit \
  --graph data/raw/tkh_collection10.json \
  --ground-truth data/raw/ground_truth.json
```

This reads ground truth only to score already frozen retrieval outputs. It does not select weights or change rankings. Use ordinary Python, not `python -O`, because the audit uses assertions. Original saved results are preserved; canonical submission exports and root metrics are regenerated.

## Full reproduction

The original semantic dependency list is retained separately from the earlier lexical environment (which used a different NumPy version). For the main pipeline install `requirements.txt`, not both historical lists together. CPU PyTorch uses its official extra index:

```bash
python -m pip install -r requirements.txt
bash scripts/reproduce.sh /absolute/path/to/supplied/data /absolute/path/to/empty/reproduction full
```

The script creates snapshots, semantic caches, structural controls, both temporal trajectories, labels and identities, frozen retrieval, coherence and stability, and the 20 perturbation runs. Omit `full` to skip the expensive perturbation suite and its derived artifacts. Expect an hour or more for the full run and memory above the observed 6.6 GiB peak. It requires network access for the pinned model. An empty output directory is mandatory. Historical lexical controls use the explicit commands below; navigation is optional.

The full download/rebuild script was assembled from the tested module interfaces but **was not executed end-to-end in this packaging pass**. Recorded evidence and local numerical tests are supplied; exact fresh-install portability of all historical transitive pins remains a limitation. Embedding caches and source data are intentionally omitted from Git. The provided zip is a repository handoff, not a container image.

---

Internship assessment: build and evaluate a multi-resolution semantic
hierarchy over an evolving scientific knowledge hypergraph.

## Objectives

- Inspect and validate the supplied graph.
- Construct chronological snapshots.
- Build nested, hyperedge-aware semantic groups.
- Track group identities across snapshots.
- Generate evidence-supported labels.
- Evaluate coherence, stability, faithfulness, and retrieval usefulness.

## Project layout

- src/tkh_abstraction/: implementation
- tests/: automated checks
- data/raw/: original supplied data, kept locally
- data/processed/: derived snapshots and caches
- docs/: research notes and report
- results/: generated outputs

## First milestone

Load the supplied graph and produce a reproducible data-quality audit.

## Lexical baseline for the 2020 snapshot

This baseline clusters nodes using only `surface_form` text. It uses character
n-gram TF-IDF with cosine distance and average-linkage agglomerative clustering,
then cuts one dendrogram at 12, 48, and 120 groups plus singleton leaves. It is a
lexical baseline, not independent semantic understanding, and it does not optimize
hyperedge fragmentation or temporal stability.

Original average-linkage reproduction command:

```bash
PYTHONPATH=src python -m tkh_abstraction.lexical_baseline \
  --input data/processed/baseline_input/snapshot_2020.json \
  --output results/lexical_baseline_2020
```

Controlled Ward comparison, using the same surface-form-only TF-IDF features and
node ordering:

```bash
PYTHONPATH=src python -m tkh_abstraction.lexical_baseline \
  --input data/processed/baseline_input/snapshot_2020.json \
  --output results/lexical_ward_2020 \
  --linkage ward
```

The command refuses to write into a nonempty output directory. The exact installed
baseline dependencies are recorded in `requirements-baseline.txt` and in each
run's `dependencies.json`.

## Frozen semantic Ward control for the 2020 snapshot

This comparison changes only the representation: node text remains
`surface_form` only, the snapshot/node order/budgets/quotient export stay fixed,
and clustering is Euclidean Ward with `lambda=gamma=0`. It uses the frozen
`sentence-transformers/all-MiniLM-L6-v2` encoder without fine-tuning.

Reproduction command using the frozen revision resolved for this project:

```bash
PYTHONPATH=src python -m tkh_abstraction.semantic_baseline \
  --input data/processed/baseline_input/snapshot_2020.json \
  --output results/semantic_ward_2020 \
  --revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41
```

The run writes `embeddings.npz`, validates cache node/text alignment before reuse,
and refuses nonempty output directories. Semantic-control dependencies are in
`requirements-semantic.txt` and `results/semantic_ward_2020/dependencies.json`.
The combined descriptive comparison is `results/representation_comparison_2020.json`.

## Native hypergraph-aware agglomerative runs

These exploratory runs reuse the cached 2020 MiniLM embeddings and optimize
`delta_J = delta_S_raw / Z_t + lambda * delta_H` with `gamma=0`. They preserve
original hyperedge records and export counted quotients at 120, 48, 12, and leaf
levels. The lambda values below are predeclared controls, not tuned winners.

```bash
PYTHONPATH=src python -m tkh_abstraction.hypergraph_agglomerative \
  --lambda 0 \
  --output results/hypergraph_agglomerative_lambda_0_2020

PYTHONPATH=src python -m tkh_abstraction.hypergraph_agglomerative \
  --lambda 0.1 \
  --output results/hypergraph_agglomerative_lambda_0p1_2020

PYTHONPATH=src python -m tkh_abstraction.hypergraph_agglomerative \
  --lambda 1 \
  --output results/hypergraph_agglomerative_lambda_1_2020
```

The implementation validates the semantic embedding cache against node IDs and
surface-form text hashes, rejects nonzero `gamma`, and refuses nonempty outputs.
A descriptive comparison is written to `results/hypergraph_lambda_comparison_2020.json`.
Saved cuts are active partitions captured when the run reaches each target group
count; they are not derived by sorting merge costs. Blind development-review
artifacts are in `results/blind_development_review_hypergraph_2020.json` and
`results/blind_development_review_hypergraph_2020.csv`.

## Stagewise temporal hypergraph controls

Temporal runs use `gamma` for temporal strength:

```text
delta_J = delta_S_raw / Z_t + lambda * delta_H + gamma * delta_T_r
```

`delta_T_r` is the exact merge delta of shared-node pairwise disagreement against
the previous snapshot partition at the active stage resolution. The objective is
stagewise greedy: candidate priorities are rebuilt when the historical reference
changes at 120, 48, and 12 groups.

First controlled temporal comparison, lambda fixed to exploratory `0.1`:

```bash
PYTHONPATH=src python -m tkh_abstraction.temporal_hypergraph \
  --snapshot data/processed/baseline_input/snapshot_2022.json \
  --prev-hierarchy results/hypergraph_agglomerative_lambda_0p1_2020/hierarchy.json \
  --cache results/semantic_ward_2022/embeddings.npz \
  --output results/temporal_lambda_0p1_gamma_0_2022 \
  --lambda 0.1 --gamma 0

PYTHONPATH=src python -m tkh_abstraction.temporal_hypergraph \
  --snapshot data/processed/baseline_input/snapshot_2022.json \
  --prev-hierarchy results/hypergraph_agglomerative_lambda_0p1_2020/hierarchy.json \
  --cache results/semantic_ward_2022/embeddings.npz \
  --output results/temporal_lambda_0p1_gamma_0p1_2022 \
  --lambda 0.1 --gamma 0.1
```

Repeat for 2024 using each configuration's 2022 hierarchy as its previous
hierarchy. The descriptive comparison is `results/temporal_comparison_2022_2024.json`.

## Evaluation protocol scaffold

The frozen evaluation plan and requirement inventory are documented in
`docs/EVALUATION_PROTOCOL.md`. Machine-readable scaffold artifacts are generated
with:

```bash
PYTHONPATH=src python -m tkh_abstraction.evaluation_scaffold \
  --output results/evaluation_scaffold
```

This writes requirement inventory, runtime estimates, and fixed 10% hyperedge
removal manifests for later perturbation evaluation. It does not read benchmark
answers or tune method settings.

## Navigation cuts and selective expansion

Additional navigation views replay existing merge histories; they do not recluster
or change weights. Example for the 2024 gamma=0.1 run:

```bash
PYTHONPATH=src python -m tkh_abstraction.navigation export-cuts \
  --snapshot data/processed/baseline_input/snapshot_2024.json \
  --run results/temporal_lambda_0p1_gamma_0p1_2024 \
  --output results/navigation_2024_gamma0p1 \
  --cuts 80 24

PYTHONPATH=src python -m tkh_abstraction.navigation init \
  --snapshot data/processed/baseline_input/snapshot_2024.json \
  --run results/temporal_lambda_0p1_gamma_0p1_2024 \
  --state results/navigation_demo_2024/frontier_k12.json

PYTHONPATH=src python -m tkh_abstraction.navigation expand \
  --state results/navigation_demo_2024/frontier_k12.json \
  --cluster 7990 \
  --output results/navigation_demo_2024/frontier_expanded.json

PYTHONPATH=src python -m tkh_abstraction.navigation collapse \
  --state results/navigation_demo_2024/frontier_expanded.json \
  --left 7731 --right 7989 \
  --output results/navigation_demo_2024/frontier_collapsed.json
```

Exported frontiers rebuild quotients from original hyperedges, so relationships
between expanded and unexpanded groups are represented directly.
