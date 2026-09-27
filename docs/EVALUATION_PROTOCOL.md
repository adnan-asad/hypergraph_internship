# Evaluation protocol and requirement inventory

This document freezes the current exploratory method settings and moves the work
toward evaluation. Development observations are not final evidence. Benchmark
answers must not be used to choose clustering weights, construct groups, generate
labels, or design query routing.

## Frozen method settings

Primary temporal method for evaluation:

- encoder: `sentence-transformers/all-MiniLM-L6-v2`
- revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- text: node `surface_form` only
- semantic vectors: L2-normalized node embeddings
- group means: arithmetic means, not re-normalized
- lambda: `0.1` exploratory setting
- gamma controls: `0` and `0.1`, for development comparison only
- saved levels: 120, 48, 12, leaves

## Temporal export semantics

### Node change categories

For adjacent snapshots, let `shared` be nodes present in both snapshots.

- `new_node_growth`: current group members not in `shared`; these are newly
  arriving nodes relative to the previous snapshot.
- `reassigned_existing_nodes`: current members in `shared` that are not in the
  matched predecessor group. These existed before but moved between groups.

### Overlap table denominators

For every previous group `P` and current group `C`, restricted to shared nodes:

- `intersection_size = |P ∩ C|`
- `previous_overlap_fraction = |P ∩ C| / |P|`
- `current_overlap_fraction = |P ∩ C| / |C|`
- `jaccard = |P ∩ C| / |P ∪ C|`

Rows with zero intersection are omitted from the exported overlap table.

### Persistent identity matching

At each saved resolution independently, matching is deterministic one-to-one:

1. sort all nonzero overlaps by descending Jaccard, then previous group id, then
   current group id;
2. accept a pair if neither side is already matched and `jaccard >= 0.30`;
3. unmatched current groups are births; unmatched previous groups are deaths.

The threshold `0.30` is a configurable development choice, not a validated value.
Death means retirement of a group identity, not deletion of member nodes.

### Merge and split event rules

Development thresholds:

- merge threshold: `current_overlap_fraction >= 0.20`
- split threshold: `previous_overlap_fraction >= 0.20`

A current group is marked as a merge if two or more previous groups pass the merge
threshold for that current group. A previous group is marked as a split if two or
more current groups pass the split threshold for that previous group.

### Parent references and trajectories

Parent references in exported hierarchies are required to point to existing
supernodes one level coarser, and child member sets must be subsets of parent
member sets. This has been verified for the current 2020, 2022, and 2024 outputs.

The 2024 gamma comparison is **not** a same-reference intervention. It compares two
evolving trajectories:

- gamma 0 in 2024 uses the gamma 0 2022 hierarchy as history;
- gamma 0.1 in 2024 uses the gamma 0.1 2022 hierarchy as history.

## Assessment requirement inventory

Machine-readable inventory: `results/evaluation_scaffold/requirement_inventory.json`.

Summary:

- T1 data audit: implemented; summarize audit artifacts in report.
- T2 formal method: partly documented; final report still needed.
- T3 temporal coupling: first method implemented; quality still needs evaluation.
- T4 hyperedge collapse: implemented and tested; report preservation/losses.
- T5 labels: not implemented; no faithfulness score yet.
- T6 evaluation: not complete; protocol below defines remaining work.

Implementation tests do not by themselves satisfy evaluation requirements.

## Final evaluation protocol

### 1. Independent semantic coherence

Use a signal independent of MiniLM embeddings used for clustering. Acceptable first
choice: blind human ratings on sampled groups, using the existing anonymous review
sheet format. Alternative: a different frozen embedding family, reported clearly
as a weaker automated proxy.

Unit of rating: one group at one level/snapshot. Inputs: central, random, and
peripheral members with IDs/types/text. Human score fields remain blank until
rated. Report mean score by run/level with bootstrap intervals over groups.

### 2. Null model

Primary null: within each snapshot and level, randomly permute node labels among
groups while preserving the exact group-size distribution. This isolates whether
observed coherence exceeds chance group membership at the same display budget.

For hyperedge-specific checks, add an arity-preserving hyperedge endpoint shuffle
as a secondary null, preserving relation type and edge arity while sampling valid
node IDs without duplicate endpoints in an edge.

### 3. 10% hyperedge-removal stability

Perturbation manifest: `results/evaluation_scaffold/perturbation_manifests.json`.

Policy:

- hold nodes fixed;
- hold embeddings fixed;
- remove 10% of original hyperedge records;
- do not clip members from retained hyperedges;
- use seeds `[0,1,2,3,4]`;
- use the same removed-edge samples across compared configurations.

For temporal perturbations, hold historical references fixed. This measures
sensitivity to current-snapshot hyperedge evidence, not compounding changes in the
previous snapshot.

Report ARI between original and perturbed partitions at each saved level, with
confidence intervals over the five seeds. This is a small-sample development
estimate, not a definitive robustness proof.

### 4. Cross-snapshot temporal stability

Metric: shared-node ARI between adjacent snapshots at each saved level. Existing
point estimates are in temporal summaries. For uncertainty, bootstrap over shared
nodes with replacement within each adjacent snapshot pair and recompute ARI for
1,000 resamples. Resampling unit: shared node. Report intervals separately for
2020→2022 and 2022→2024.

Also report shared-node temporal disagreement as already defined, but do not treat
it as semantic quality.

### 5. Label/gloss faithfulness and overclaim rate

Not yet implemented. Required steps:

1. build temporally filtered evidence payloads: no future-only metadata, no claims
   beyond snapshot cutoff;
2. generate short label and one-sentence gloss per level 0/1 group;
3. evaluate overclaim rate using either blind human labels or an NLI model;
4. classify each sampled gloss as supported / vague but safe / overclaim / wrong.

Scores remain blank until this is actually performed.

### 6. Hierarchy-based question retrieval vs flat baseline

Freeze routing before using benchmark answers. Proposed protocol:

- represent each question using the same frozen encoder or a separately declared
  retrieval encoder;
- hierarchy route: rank level-0 groups, expand top `b`, rank child groups, continue
  to leaves, collect candidate method/claim nodes;
- flat baseline: same query representation and scoring over all nodes directly,
  with the same candidate budget;
- only after routing is frozen, compare against `ground_truth.json` for hit rate,
  precision/recall, and steps-to-target.

Do not use benchmark answers to set lambda, gamma, branching factor, prompts, or
labels.

## Runtime estimate before repeated runs

Machine-readable estimate: `results/evaluation_scaffold/runtime_estimate.json`.
The exact all-pairs heap is feasible for the current snapshots but expensive,
especially for 2024. Five perturbation seeds over two gamma settings and two future
snapshots would require roughly 20 full temporal rebuilds; based on measured 2024
runtime (~6 minutes each), this is on the order of hours, not minutes.
