# AI assistance log

## Project planning and setup

Tool: OpenAI assistant in Codex.

Tasks: assessment explanation, dataset inspection, endpoint-role audit,
project planning, and repository setup guidance.

Major requests: inspect the supplied assessment and dataset; explain the
objective; investigate endpoint-role ambiguity; guide project setup.

Verification: record commands actually run and checks independently reviewed.
Earlier assistant-reported findings must be reproduced by project code before
being presented as verified project results.

## Step 2 quotient/coarsening review

Tool: OpenAI assistant in Pi.

Tasks: reviewed `docs/STEP_2_COARSENING.md`, T4 in `docs/assessment.md`,
`src/tkh_abstraction/quotient.py`, and `tests/test_quotient.py`; ran the full
unit test suite and quotient demonstration; inspected real hyperedge `h_00001`
from `data/raw/tkh_collection10.json`; demonstrated an explicitly illustrative
coarsening and checked metadata preservation.

Major requests: explain partial and complete hyperedge collapse, original vs
coarse arity, preserved vs hidden information, and why fragmentation alone is a
bad grouping objective; propose the next semantic representation and merge-cost
module without implementing it.

Verification: ran `PYTHONPATH=src python -m unittest discover -s tests -v`
(18 tests, OK) and `PYTHONPATH=src python -m tkh_abstraction.quotient` (demo
fragmentation values 0.6667, 0.3333, 0.0). A separate standard-library Python
inspection loaded the real graph with UTF-8, coarsened edge `h_00001` using a
clearly labeled illustrative partition, and verified `attributes`, `provenance`,
and `original_members` were preserved exactly.

## 2020 lexical hierarchical-clustering baseline

Tool: OpenAI assistant in Pi.

Tasks: implemented `src/tkh_abstraction/lexical_baseline.py`, tests in
`tests/test_lexical_baseline.py`, `requirements-baseline.txt`, and README
reproduction notes. The module clusters only node `surface_form` strings using
character n-gram TF-IDF with cosine distance and average-linkage agglomerative
clustering, cuts one dendrogram at 12/48/120 groups plus leaves, and exports the
existing counted quotient at each saved level.

Major requests: build a reproducible lexical baseline for
`data/processed/baseline_input/snapshot_2020.json`; preserve temporal snapshot
limits; use the quotient implementation for coarse hyperedges; refuse nonempty
outputs; do not use `ground_truth.json` or the tuning module; report execution
separately from scientific quality.

Verification: inspected the active Python version (`Python 3.10.21`) and the
snapshot metadata warning that text is unversioned and historical metadata must
not be used for generation prompts. Installed the small baseline dependency set
into the existing venv with `ensurepip` and `pip install scikit-learn==1.4.2`;
exact installed versions are in `requirements-baseline.txt` and the run output's
`dependencies.json`. Ran `PYTHONPATH=src python -m unittest discover -s tests -v`
(33 tests, OK). Ran the real baseline with
`PYTHONPATH=src python -m tkh_abstraction.lexical_baseline --input data/processed/baseline_input/snapshot_2020.json --output results/lexical_baseline_2020`;
it completed on 1,505 nodes and 374 hyperedges in about 13.9 seconds. Checked the
k12 quotient has 374 hyperedges and preserves original edge IDs, provenance, and
`original_members` for sampled records. `ground_truth.json` was not read or used
for grouping.

## Linkage comparison: average vs Ward lexical baseline

Tool: OpenAI assistant in Pi.

Tasks: inspected the existing lexical baseline implementation and exported average
run; confirmed character n-gram TF-IDF settings, input node order, tree-cut logic,
zero-vector status, and the giant k12 group membership. Added a `--linkage` option
for a controlled Ward run using the same fitted TF-IDF representation and node
ordering, plus a tested `ward_delta_sse` objective-reference function. Generated
`results/lexical_ward_2020` and `results/lexical_linkage_comparison_2020.json`
without overwriting `results/lexical_baseline_2020`.

Major requests: preserve the completed average-linkage baseline; add Ward using
Euclidean geometry only; keep text representation, budgets, schema, and quotient
construction fixed; compare both outputs without using benchmark answers, weight
tuning, semantic embeddings, or structural/temporal penalties.

Verification: ran `PYTHONPATH=src python -m unittest discover -s tests -v` before
editing (33 tests, OK) and after editing (35 tests, OK). Independently checked the
2020 TF-IDF matrix: analyzer `char_wb`, n-gram range `(3, 5)`, L2 norm, vocabulary
size 22,894, shape 1,505 x 22,894, and zero-vector count 0. Verified the average
k12 giant group is present in `hierarchy.json` with 1,474 unique members out of
1,505, not a counting-only artifact. Resolved repeated `LAMMPS` representatives to
`meth_00267` (method) and `cite_00077` (cited_work). Ran Ward with
`PYTHONPATH=src python -m tkh_abstraction.lexical_baseline --input data/processed/baseline_input/snapshot_2020.json --output results/lexical_ward_2020 --linkage ward`; it completed on 1,505 nodes and 374 hyperedges in about 9.9 seconds.

## Frozen semantic representation comparison

Tool: OpenAI assistant in Pi.

Tasks: implemented `src/tkh_abstraction/semantic_baseline.py`, focused tests in
`tests/test_semantic_baseline.py`, `requirements-semantic.txt`, README reproduction
notes, and comparison artifacts. The run uses `surface_form` only, frozen
`sentence-transformers/all-MiniLM-L6-v2`, L2-normalized node embeddings, Euclidean
Ward linkage, existing hierarchy budgets, and existing quotient export. It keeps
`lambda=gamma=0` and does not add structural, temporal, type-token, neighborhood,
or benchmark-answer signals.

Major requests: preserve completed lexical average/Ward runs; resolve and record
an immutable model revision; cache embeddings with node IDs and text hashes;
validate cache alignment; report truncation; add tests that do not require model
downloads; compare lexical average, lexical Ward, and semantic Ward descriptively
without claiming independent scientific quality.

Verification: checked the environment before installing semantic dependencies
(`sentence_transformers`, `transformers`, `torch`, and `huggingface_hub` were not
installed). Installed a CPU semantic stack without changing the saved lexical run
outputs; exact versions are in `requirements-semantic.txt`. Ran
`PYTHONPATH=src python -m unittest discover -s tests -v` before semantic work (35
tests, OK) and after (38 tests, OK). Resolved model revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Ran
`PYTHONPATH=src python -m tkh_abstraction.semantic_baseline --input data/processed/baseline_input/snapshot_2020.json --output results/semantic_ward_2020`; it encoded 1,505 nodes on CPU, produced 384-dimensional normalized embeddings, reported zero truncated inputs, and completed clustering/export. Verified cache reload alignment and embedding norms (approximately 0.99999988 to 1.00000012). Created Ward inspection sheets and `results/representation_comparison_2020.json`. `ground_truth.json` was not read or used.

## Native hypergraph-aware agglomerative merging

Tool: OpenAI assistant in Pi.

Tasks: implemented `src/tkh_abstraction/hypergraph_agglomerative.py`, tests in
`tests/test_hypergraph_agglomerative.py`, README reproduction commands, and
exploratory result runs for lambda 0, 0.1, and 1. The engine reuses the cached
MiniLM embeddings from `results/semantic_ward_2020`, validates cache alignment,
uses arithmetic sufficient statistics for Ward-style semantic deltas, computes
native hyperedge fragmentation deltas from current edge incidences, and exports
the existing counted quotient at saved cuts.

Major requests: avoid re-encoding and preserve completed runs; implement
`delta_J = delta_S_raw/Z_t + lambda*delta_H`; keep gamma 0 and reject nonzero
gamma; avoid deep-copying quotients for every candidate; maintain one merge tree;
run predeclared exploratory lambdas; report scale, runtime, and inspection
examples without claiming scientific quality.

Verification: ran `PYTHONPATH=src python -m unittest discover -s tests -v` after
implementation (45 tests, OK). Tests compare Ward deltas with direct SSE,
structural deltas with quotient before/after including after an earlier merge,
combined deltas with direct objective differences, selected merges with exhaustive
search on small examples, lambda=0 merge criterion against Ward semantic deltas,
and hierarchy/quotient invariants. Ran exact lazy-heap engine on the 2020 snapshot
for lambda 0, 0.1, and 1 using `results/semantic_ward_2020/embeddings.npz`; runs
completed in about 25-28 seconds each. Wrote
`results/hypergraph_lambda_comparison_2020.json`. `ground_truth.json` was not read,
weight tuning was not run, and no commits/pushes were made.

## Hypergraph cut verification and temporal coupling plan

Tool: OpenAI assistant in Pi.

Tasks: verified that the saved hypergraph-aware hierarchy levels are the actual
active partitions reached at 120, 48, and 12 groups, not cuts obtained by sorting
possibly non-monotonic merge costs. Added a regression test for this behavior,
completed the lambda comparison report, and created anonymous blind development
review artifacts with blank human-rating fields.

Major requests: preserve completed runs; do not assume monotonic dendrogram
heights because combined costs can be negative/non-monotonic; complete missing
lambda=1 comparison values; prepare blind development review sheets; propose a
concrete temporal extension for 2020/2022/2024 before implementing temporal
coupling.

Verification: ran `PYTHONPATH=src python -m unittest discover -s tests -v` (46
tests, OK). Replayed merge logs for lambda 0, 0.1, and 1 and verified that saved
`k120`, `k48`, `k12`, and leaf hierarchy memberships exactly match the active
partitions at those group counts. Wrote updated
`results/hypergraph_lambda_comparison_2020.json`,
`results/blind_development_review_hypergraph_2020.json`, CSV review sheet, and an
anonymous-key file for audit. Estimated all-pairs heap sizes for 2020, 2022, and
2024 snapshots from node counts. `ground_truth.json` was not read, tuning was not
run, and no commits/pushes were made.

## Stagewise temporal hypergraph extension

Tool: OpenAI assistant in Pi.

Tasks: implemented `src/tkh_abstraction/temporal_hypergraph.py` and
`tests/test_temporal_hypergraph.py`. The module uses gamma consistently in
`delta_J = delta_S_raw/Z_t + lambda*delta_H + gamma*delta_T_r`, computes exact
temporal merge deltas from previous-group membership counts, rebuilds candidate
priorities at stage transitions, exports exact active-partition cuts, and writes
deterministic Jaccard-based identity/event records plus full overlap tables.

Major requests: compare gamma 0 and 0.1 with lambda fixed at exploratory 0.1;
start both from the completed 2020 lambda 0.1 hierarchy; run 2022 then 2024 with
each configuration using its own previous hierarchy; preserve embeddings/model
revision/text construction; report descriptive development metrics only.

Verification: checked available memory before 2024 (`free -h`, about 6.7 GiB
available) and estimated all-pairs candidates for 2024 at 8,667,366 pairs
(~1.6-2.4 GiB heap-entry payload before stale entries/dicts). Ran
`PYTHONPATH=src python -m unittest discover -s tests -v` (49 tests, OK). Tests
cover temporal delta against direct pairwise disagreement including new nodes,
stage-transition heap rebuild against exhaustive search, and gamma=0 reducing to
the non-temporal merge criterion. Ran temporal experiments for 2022 and 2024 at
gamma 0 and 0.1. Peak ru_maxrss was about 1.4 GiB for 2022 and 3.9 GiB for 2024.
Wrote `results/temporal_comparison_2022_2024.json`. No benchmark answers were
accessed, no automatic tuning was run, and no commit/push was made.

## Evaluation protocol and scaffolding

Tool: OpenAI assistant in Pi.

Tasks: verified temporal export semantics and hierarchy validity, mapped assessment
evaluation requirements to existing artifacts versus remaining work, wrote
`docs/EVALUATION_PROTOCOL.md`, implemented `src/tkh_abstraction/evaluation_scaffold.py`,
and added tests in `tests/test_evaluation_scaffold.py`. Generated
`results/evaluation_scaffold/requirement_inventory.json`, `runtime_estimate.json`,
and fixed perturbation manifests.

Major requests: freeze current exploratory settings and move toward evaluation;
distinguish development judgments from final evaluation; define independent
semantic coherence, null models, perturbation stability, cross-snapshot ARI with
uncertainty, label overclaim evaluation, and hierarchy retrieval versus a flat
baseline; do not use benchmark answers for construction, tuning, labels, or query
routing.

Verification: checked parent references and subset nesting for the current 2020,
2022, and 2024 outputs; all inspected hierarchy parent references were valid.
Inspected temporal identity exports and documented matching/event denominators and
thresholds. Ran `PYTHONPATH=src python -m tkh_abstraction.evaluation_scaffold --output results/evaluation_scaffold` and `PYTHONPATH=src python -m unittest discover -s tests -v` (51 tests, OK). No benchmark answers were accessed, no repeated full perturbation runs were launched, and no commit/push was made.

## Evaluation execution scaffolding and frozen baselines

Tool: OpenAI assistant in Pi.

Tasks: added persistent IDs to current 2020/2022/2024 hierarchies, propagated
accepted predecessor identities per configuration/resolution, implemented
`src/tkh_abstraction/identity.py`, `labels.py`, `retrieval.py`,
`perturbation_eval.py`, and `stability_metrics.py`, plus identity tests. Generated
extractive provisional label/gloss files, frozen 2024 retrieval outputs, and
cross-snapshot ARI bootstrap files.

Major requests: preserve frozen method settings and existing outputs; separate
new-node growth from reassignment; keep benchmark-answer access separate from
retrieval output generation; avoid tuning after seeing benchmark answers; prepare
perturbation evaluation with checkpoint/resume.

Verification: ran persistent-ID assignment for 2020 and both gamma trajectories
through 2024; ran `PYTHONPATH=src python -m unittest discover -s tests -v` (52
tests, OK). Generated retrieval output before any benchmark scoring and did not
read `ground_truth.json`. Implemented resumable perturbation runner and manifests,
but did not launch the full 20-run perturbation suite in this turn because prior
measured runtimes imply roughly an hour+ of sequential 2024 jobs with high memory.

## Evaluation execution: perturbation, coherence proxy, 2026 retrieval scoring

Tool: OpenAI assistant in Pi.

Tasks: executed the predefined 20 perturbation runs sequentially with checkpoint
resume, added a primary group-size-preserving null coherence proxy
(`src/tkh_abstraction/coherence_eval.py`), ran the supplied-corpus 2026 temporal
extension from the frozen 2024 gamma=0.1 predecessor, froze 2026 retrieval outputs,
and scored them in an isolated step (`src/tkh_abstraction/score_retrieval.py`).
Added focused tests for labels and scoring.

Major requests: preserve frozen method settings; do not add clustering variants;
run perturbations despite expected runtime; keep benchmark-answer access confined
to scoring after retrieval output freeze; report date limitations and unresolved
mappings; update inventory and AI usage.

Verification: full perturbation outputs are in `results/perturb_lambda_*`; 2024
perturbation runs used about 3.45-3.48 GiB peak memory and ~6.3-6.5 minutes per
seed. The 2026 supplied-corpus run completed in 968.8 seconds with peak ru_maxrss
about 6.6 GiB. Retrieval output `results/retrieval_frozen_2026_gamma0p1.json` was
written before reading/scoring `ground_truth.json`; isolated scoring is in
`results/retrieval_score_2026_gamma0p1.json`. Ran
`PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v` (54 tests, OK).
No commits/pushes were made.

## Final evaluation artifacts and report draft

Tool: OpenAI assistant in Pi.

Tasks: added `src/tkh_abstraction/final_eval_artifacts.py`, generated perturbation
uncertainty intervals, node-type-composition-preserving coherence nulls, blind
scientific-coherence review packets, label-faithfulness review sample, benchmark
target mapping audit, retrieval claim scoring, and `docs/report_draft.md`.

Major requests: preserve method and frozen retrieval outputs; do not tune in
response to benchmark results; report strict text-match separately from audited
mapping artifacts; keep unresolved/absent targets visible; leave human review
ratings blank; include current retrieval underperformance and limitations.

Verification: generated `results/perturbation_uncertainty.json`,
`results/coherence_type_preserving_null_2024_gamma0p1.json`,
`results/blind_scientific_coherence_review.json`,
`results/label_faithfulness_review_sample.json`,
`results/benchmark_target_mapping_audit.json`, and
`results/retrieval_claim_scoring_2026_gamma0p1.json`. Updated
`results/evaluation_scaffold/requirement_inventory.json`. Ran
`PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v` (54 tests, OK).
No clustering/routing changes were made after benchmark scoring and no commit/push
was made.

## Navigation cuts and selective expansion

Tool: OpenAI assistant in Pi.

Tasks: implemented `src/tkh_abstraction/navigation.py`, tests in
`tests/test_navigation.py`, exported k80/k24 navigation cuts for 2020, 2022, 2024,
and 2026 main runs, and demonstrated selective expansion/collapse on the 2024
gamma=0.1 hierarchy.

Major requests: preserve evaluated outputs and 12/48/120 checkpoints; replay saved
merge histories chronologically; do not sort by merge cost; export additional
views and mixed-depth frontier quotients from original hyperedges; provide a small
CLI; do not claim persistent identities for new navigation levels.

Verification: exported `results/navigation_2024_gamma0p1` and analogous 2020/2022/2026
navigation directories. Demo started from 12 groups, expanded merge-tree group
`7990` into children `7731` and `7989` to obtain 13 groups, exported the mixed
frontier quotient, collapsed back, and verified the original 12-group frontier was
recovered exactly. Ran `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`
(57 tests, OK). No clustering/routing changes, commits, or pushes were made.

## Extends direction inference layer

Tool: OpenAI assistant in Pi.

Tasks: inspected `docs/assessment.md` and `docs/ASSESSOR_CLARIFICATIONS.md`, then
implemented a separate temporal heuristic layer for `extends` direction in
`src/tkh_abstraction/extends_direction.py` with tests in
`tests/test_extends_direction.py`. Generated per-snapshot artifacts in
`results/extends_direction/`.

Major requests: preserve original member order/source data and existing clustering
results; never infer direction from `member[0]`; export original edge IDs/members,
method year evidence, inferred source or null, candidate targets, non-method
context, uncertainty reasons, and policy version; report member[0] agreement only
as a diagnostic.

Verification: ran targeted tests for unique date match, unique newest candidate,
tied dates, missing dates, future-origin contradictions, permutation invariance,
and original hyperedge/context preservation. Generated stats for 2020/2022/2024/2026.
For 2026, 4/50 `extends` edges resolved and 46 remained unresolved; h_00003 is
unresolved due to missing method origin years. Direction accuracy is not claimed,
and no clustering/evaluation outputs were changed. No commit/push was made.

## Submission audit and writing — 26 September 2026

Tool: OpenAI Codex desktop assistant. The developer supplied the actual repository archive and edited developer-review CSV. Major request: finish the project, prepare the assessment deliverables, audit measured evidence and identify what to commit. The assistant was instructed to prioritize rubric coverage; no invented experiments, ratings or performance improvements were accepted.

Work: inspected source and saved outputs; consolidated real developer annotations; drafted the report, literature positioning, evidence ledger and reproduction/commit instructions; added exact-name retrieval diagnostics and exhaustive hierarchy/quotient/extractive-integrity audits; fixed base singleton persistent IDs and portable peak-memory reporting; added checks for paired seed cohorts. Original experiment outputs and rankings were retained. Canonical exports correct singleton IDs without reclustering.

Verification performed by the assistant on the copied repository: 60 tests passed using Windows Python 3.12.14 with pinned numerical dependencies; 60 ARIs recomputed from 20 saved perturbation hierarchies matched stored values; four snapshots passed partition, nesting, budget and quotient-preservation checks; 14,351 gloss rows passed mechanical extraction checks. Source data were used to verify membership/provenance. Ground truth was accessed only for a disclosed post-hoc diagnostic of already frozen retrieval; the method and rankings were not retuned.

Limits at that stage: the developer's review is not an independent expert review. AI-assisted writing and code checks alone do not establish scientific coherence or label overclaim. No expert ratings were synthesized. Full model download/clustering and the complete reproduction shell script were not rerun during this packaging pass. The developer must read the final documents, confirm their interpretation and own the submission. No Git commit or push was made by the assistant.

## Assessor-approved blind LLM evaluation — subsequent extension

The developer supplied the assessor's clarification that documented blind LLM judging plus manual checks is acceptable, and explicitly requested its execution. Three fresh-context Codex evaluator agents received separate anonymized files with no inherited conversation. Their precise backend model version/temperature were not exposed. Rubrics and instructions are retained in `evaluation_llm/PROTOCOL.md` and `JUDGE_INSTRUCTIONS.md`; packet hashes and unchanged ratings are retained. These are actual LLM evaluations, not fabricated human or expert ratings.

Tasks: one judge rated 48 coherence packets (2024 gamma controls and matched type/size nulls), one judged 32 required-level label/gloss pairs, and one scored all36 frozen question/result packets including Q15–Q18 evidence rubrics. Each provided individual rationales. Configuration identities, clustering embeddings and scores were withheld. The controller decoded identities after outputs were saved, checked all expected packets/criteria and evidence IDs, calculated descriptive intervals and compiled the reports. No clusters, weights, generated labels or retrieval rankings were changed to improve the evaluation.

Verification: all48/32/36 packets present; 448 claim criteria and180 citation targets retained; cited support IDs belong to their returned packet. Source-extraction overclaim was 0/32, while16 labels were supported-but-vague. This does not imply no possible overclaim. Human spot-checks were requested separately and remain pending unless the developer has filled their CSV. Previous developer annotations remain a distinct analysis. The LLM coherence trade-off and negative retrieval findings were retained, not edited away.


## Developer spot-check feedback recorded

The developer supplied comments on all six requested cases in chat. The assistant preserved the original message, transcribed notes to the CSV, and recorded only the explicit C004 rating of 1. Other categories/agreement fields were not inferred. Reports distinguish six qualitative checks from one explicit numeric rating; no LLM judgment or measured overclaim numerator was changed.
