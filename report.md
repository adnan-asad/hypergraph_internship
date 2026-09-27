# Semantic abstraction over an evolving knowledge hypergraph

**Submission report — Adnan.** Option A; supplied scientific knowledge graph. The implementation produces nested, provenance-preserving views and temporal identity records. Evaluation includes blind LLM coherence and faithfulness judgments, matched nulls, temporal controls and all benchmark questions. It does **not** establish superior retrieval. Numerical evidence is in `metrics.json`; complete blind results in `evaluation_llm/LLM_EVALUATION_REPORT.md`; developer annotations remain separate.

## 1. Problem statement and data

Given a snapshot hypergraph \(G_t=(V_t,E_t)\), construct nested, disjoint partitions \(P_t^{12},P_t^{48},P_t^{120}\) and singleton leaves. Each partition covers every node, including isolates. A coarse node denotes a set of original nodes; its children partition that set. Top-level views target twelve groups, within the requested approximate dozen. The other budgets are display choices, not discovered natural scales. Additional cuts at 24 and 80 and selective expansion replay the same merge history without reclustering.

The supplied corpus contains 5,798 nodes and 1,429 hyperedges. Conservative annual filtering produces:

| Cutoff | Nodes | Hyperedges |
|---|---:|---:|
| 2020 | 1,505 | 374 |
| 2022 | 2,164 | 526 |
| 2024 | 4,164 | 983 |
| 2026 | 5,798 | 1,429 |

Nodes enter by `first_seen_year`, rather than a possibly earlier invention/origin date. Edges require their own date, asserting article date and all endpoints to be available. An unavailable endpoint postpones the whole edge; filtering does not clip a scientific relationship into a different one. Text is not historically versioned, so these are availability-filtered views of the supplied extraction, not guaranteed reconstructions of contemporary knowledge. Annual timestamps cannot establish exact February 2026 availability.

Success requires more than small partitions: recognizable concepts, retained multiway evidence, navigable nesting, and limited unnecessary reassignment as the corpus grows. Hard partitions are a simplifying assumption: a scientist, technique or paper may legitimately belong to several topics. The graph's mixed node types also make surname similarity and author-only clusters possible failure modes.

## 2. Method and literature positioning

Each node's `surface_form` is encoded with frozen `all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. No benchmark answers or paper full texts enter clustering. Node vectors are normalized; group means are arithmetic averages without renormalization. At each stage, choose the active pair with minimum

\[
\Delta J=\frac{\Delta S_{raw}}{Z_t}+\lambda\Delta H+\gamma\Delta T_r,
\qquad
\Delta S_{raw}=\frac{n_A n_B}{n_A+n_B}\|\mu_A-\mu_B\|^2.
\]

Here \(S_{raw}\) is within-group squared error and \(Z_t\) is fixed total snapshot scatter. Zero-scatter inputs contribute zero semantic cost. This is the exact Ward increment, not cosine distance between centroids. For edge \(e\), original arity \(a_e\) stays fixed and \(r_e(P)\) counts groups touched:

\[
H(P)=|E_t|^{-1}\sum_e\frac{r_e(P)-1}{a_e-1},\qquad
\Delta H=-|E_t|^{-1}\sum_{e:\ e\cap A\ne\varnothing,\ e\cap B\ne\varnothing}\frac1{a_e-1}.
\]

Empty edge sets have zero structural cost. This term is hypergraph-native: a shared multiway relationship contributes once, without clique projection. Fragmentation always decreases or stays fixed under merging; low fragmentation alone is not good science. Budgets and semantic loss counter its incentive to collapse everything.

The temporal term counts pairwise co-membership disagreements on nodes shared with the previous snapshot. If a proposed merge contains `cross` cross-group shared-node pairs and `same` of these belonged together previously, its change is \((cross-2same)/\binom{|V_t\cap V_{t-1}|}{2}\), with zero when fewer than two nodes are shared. New nodes incur no direct historical penalty. Historical references change at the 120-, 48- and 12-group stages, rebuilding priorities. This is **stagewise greedy optimization**, not optimization of one fixed global objective throughout the tree. All active pairs are considered using a lazy heap. Partition cuts follow merge chronology, not sorted merge costs, which need not be monotone.

Exploratory controls used \(\lambda\in\{0,0.1,1\}\), then \(\gamma\in\{0,0.1\}\) with \(\lambda=0.1\). The main exported trajectory uses 0.1 for both weights. These are fixed exploratory settings, not trained parameters or proven optima. A tuning scaffold exists but did not select a validated winner.

Four research connections motivate the choices. [Clauset, Newman and Moore (2004)](https://arxiv.org/abs/cond-mat/0408187) construct hierarchical communities by greedy modularity optimization. This supports a merge-history representation, but pairwise modularity is not our scientific-coherence objective. [Zhou, Huang and Schölkopf (2006)](https://proceedings.neurips.cc/paper_files/paper/2006/file/dff8e9c2ac33381546d96deea9922999-Paper.pdf) formulate learning with hypergraphs, motivating explicit multiway incidence; this implementation uses counted contractions rather than their spectral relaxation. [Loukas (2019)](https://www.jmlr.org/papers/v20/18-680.html) studies graph reduction with spectral and cut guarantees. It highlights the difference between preserving source records and preserving an operator: we establish the former, not spectral approximation guarantees. [Chakrabarti, Kumar and Tomkins (2006)](https://doi.org/10.1145/1150402.1150467) balance snapshot quality and historical consistency in evolutionary clustering. Our pairwise penalty follows that motivation while making the resolution-specific reference explicit.

## 3. Hyperedge collapse and temporal identity

A four-node edge \(\{a,b,c,d\}\) becomes an edge with counts \(\{X:2,c:1,d:1\}\) when \(a,b\) merge. If every endpoint eventually lies inside one group, the internal edge remains with count four. Distinct source edges remain distinct even when their coarse endpoints coincide. Exports retain original IDs, endpoint order, arity, relation type, attributes, dates and provenance. Original `n_targets` describes the source edge; it is not a statement about the number of coarse endpoints. No unsupported endpoint-role semantics are inferred.

This counted quotient is used both in exports and in checking the fragmentation objective. It preserves the evidence needed for drill-down, but does not assert that every member of one supernode has the original relation to every member of another. Tests compare incremental merging with direct coarsening and exact objective differences.

Across snapshots, overlap-based matching propagates group identities and records birth, merge, split, death and growth/reassignment events. Death means retirement of a group identity, not disappearance of scientific evidence. Matching thresholds are operational conventions. Canonical exports correct a base-snapshot singleton-ID inconsistency: leaves now retain `node_<original-id>` across time. Original experiment artifacts remain unchanged.

## 4. Evaluation and results

**Representation and structure.** At 2020 k12, surface-form cosine/average linkage placed 1,474 of 1,505 nodes in one group. Semantic representation improved the size distribution, but that is not independent evidence of coherence. For the semantic hypergraph comparison, increasing \(\lambda\) trades semantic dispersion against fragmentation:

| Lambda | Normalized SSE | Fragmentation | Largest-group fraction |
|---|---:|---:|---:|
| 0 | 0.8768 | 0.5026 | 0.239 |
| 0.1 | 0.8790 | 0.2255 | 0.347 |
| 1 | 0.9023 | 0.0360 | 0.286 |

Combined objective values at different weights are not comparable evidence of superiority.

**Coherence and circularity.** MiniLM similarity is not reused as an evaluation score. A different representation, character 3–5-gram TF-IDF, measures mean cosine to each group's centroid. For 2024 gamma 0.1, group-weighted scores are 0.251, 0.374 and 0.456 at k12/k48/k120, versus size-preserving null means 0.149, 0.183 and 0.233. A second shuffle preserves each group's type composition as well as size; its results are in `metrics.json`. These nulls randomize node assignment, not hyperedge topology. They control simple size/type explanations but do not establish domain-expert agreement. Ten shuffles give minimum plus-one permutation p=1/11, so no 5% significance claim follows. The evaluator also uses the same underlying text and lexical features were explored in baselines: representation independence reduces the direct same-embedding circularity, but scientific validation remains limited.

**Temporal stability.** ARI measures agreement of partitions on shared nodes without relying on group-ID names. At k12, 2020→2022 ARI increases from 0.323 to 0.590 with gamma 0.1; respective node-bootstrap 95% intervals are [0.297, 0.356] and [0.554, 0.628]. For 2022→2024 the values are 0.367 and 0.386, intervals [0.341, 0.397] and [0.360, 0.417]. Node bootstrap ignores graph dependence; these are conditional descriptive intervals, not uncertainty across independent scientific corpora. Temporal regularization is not uniformly beneficial.

**Perturbation stability.** Twenty saved rebuilds cover two years, two gamma values and five fixed seeds removing 10% of original edges, with nodes, embeddings and history held fixed. For gamma 0.1, mean ARIs at k12/k48/k120 are 0.573/0.583/0.750 in 2022 and 0.447/0.472/0.631 in 2024. At k12, approximate five-seed t intervals are [0.450, 0.697] and [0.401, 0.493]. Paired gamma differences and intervals are reported rather than inferred from overlap of separate intervals. Five perturbations provide limited precision.

**Developer review and labels.** The developer recorded 120 annotations across 22 of 36 anonymized groups: 38 ratings of 2, 50 of 1, seven of 0 and 25 unsure. Among 95 numeric annotations, 40.0% received 2. Rating scope mixed individual members and whole groups; coverage differs across runs. These counts quantify actual review effort and observations, not a group-coherence rate or a winning method. Notes identify plausible material-science themes and concerns about author/name grouping.

Following the assessor's clarification that blind LLM evaluation is acceptable, fresh-context judges received anonymized packets without embeddings, scores or configuration identities. For coherence, all twelve 2024 groups per gamma control were sampled with fifteen random members and compared with matched type/size-preserving nulls. On a 1–4 scale, gamma 0 scored **2.750 versus 1.750** for its null; gamma 0.1 scored **2.333 versus 1.667**. Descriptive paired-difference bootstrap intervals were [0.500, 1.500] and [0.000, 1.333]. This reveals a coherence/stability trade-off rather than a uniformly best setting. One judge and one null realization per configuration limit inference.

Labels are keyword lists and glosses explicitly quote examples. An exhaustive audit of 14,351 rows found zero mechanical extraction errors; this is not an overclaim score. A separate blind judge evaluated **32 level-0/1 label/gloss pairs**, four per level per snapshot, using examples, random members, keyword witnesses and available relation context. It rated 16 accurate/informative, 16 supported but vague, and zero unsupported/wrong: observed overclaim **0/32**, descriptive Wilson interval **0–10.7%**. This assesses support in the supplied extraction, not full-paper truth or unseen groups. The developer supplied six qualitative spot-checks in `evaluation_llm/human_spotchecks.csv`: C004 received 1 with a size/coverage caveat; F002 appeared thematically related; F003 raised semantic-coherence uncertainty; F001/F005 appeared vague; C006 showed only some author connections. Only one explicit numeric rating was supplied, so no human agreement or overclaim rate is inferred. LLM ratings are unchanged.

**Extrinsic utility.** For all 18 questions the frozen retriever scores twelve broad centroids, selects four, then ranks method/claim nodes inside their union and returns twenty. The flat control ranks all method/claim candidates with the same encoder and budget. This is a single coarse-filter step. Historical Type-A substring-proxy recall is 0.274 versus 0.298; strict exact-name node recovery is zero for both, with only 32/63 target occurrences exactly mapped in the graph. A fresh blind LLM judge therefore assessed aliases, claim support and citations separately, without changing the retrieved lists:

| Blind metric (macro average) | Hierarchy | Flat |
|---|---:|---:|
| Type A, Q1–Q14: direct method-node recall | 0.064 | 0.064 |
| Type A: method mentions, including claims | 0.294 | 0.318 |
| Type A: claim coverage | 0.125 | 0.129 |
| Type A: citation coverage | 0.060 | 0.060 |
| Type B, Q15–Q18: claim coverage | 0.172 | 0.172 |
| Type B: source coverage | 0.600 | 0.600 |

Every rubric criterion was retained: 448 claim criteria and 180 citation targets across both modes. Claim coverage assigns full/partial/absent-or-contradicted weights 1/0.5/0. Source coverage requires provenance-title or explicit citation support; unresolved author/year mappings remain uncovered. This is post-hoc evidence evaluation, not generated-answer accuracy. Candidate filtering excludes datasets, a limitation for Q14. The hierarchy uses about 67.5% of flat score counts including twelve group scores, excluding encoding, centroid formation and sorting; this is not latency. No downstream accuracy improvement is demonstrated.

## 5. Verification, decision and four more weeks

The packaging audit verifies all four canonical hierarchies for exact partition coverage, nesting and budgets, and all four quotient levels for original edge identity, endpoint counts and metadata. All 60 numerical tests passed; 60 seed/level ARIs were recomputed from the 20 saved perturbation hierarchies and matched their recorded values. Tests exercise objective deltas and temporal transitions. Full clustering was not rerun during packaging; original runtime records include roughly 969 seconds and 6.6 GiB peak RSS for 2026. Reproduction requires model download and substantial memory; the numerical audit can run without those.

I would ship the provenance-preserving hierarchy as an **exploratory browsing artifact**, retain flat retrieval as the accuracy reference, and expose provisional labels. The new blind review favors gamma 0 for sampled coherence, while gamma 0.1 improves some temporal measures; both should remain visible controls rather than declaring one universal winner. With four more weeks I would complete human checks and repeat judging on a held-out set, test context-enriched representations and type-aware ablations, then implement multilevel retrieval with equal compute budgets, a frozen alias policy and method-to-claim evidence paths. Finally I would investigate temporal matching and computational pruning while checking exact small-case equivalence. Evaluation design, rather than extra architecture, remains the priority.
