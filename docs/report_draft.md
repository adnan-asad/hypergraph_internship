# Draft report: temporal hypergraph abstraction evaluation

## Method summary

The frozen method uses `sentence-transformers/all-MiniLM-L6-v2` at revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, with node `surface_form` only. Groups
are built by exact greedy agglomeration over all active pairs. The merge objective
is

`delta_J = delta_S_raw / Z_t + lambda * delta_H + gamma * delta_T_r`.

For the evaluation trajectory, `lambda=0.1` and `gamma=0.1` are frozen exploratory
settings, not tuned winners. Temporal runs are stagewise greedy: the previous
partition reference changes at 120, 48, and 12 groups.

Hyperedges are coarsened with the counted quotient representation. Original edge
IDs, arities, attributes, and provenance are retained. The original implementation
preserved `extends` relations but did not resolve their direction because member
order is not a source/target contract. A separate artifact now adds an auditable
temporal direction heuristic for `extends` with explicit abstention; it does not
change clustering scores, memberships, or previous evaluation results. Direction
accuracy is not established by unit tests or date consistency.

## Main measured results

### Perturbation robustness

A 10% original-hyperedge-removal experiment was run over five fixed seeds for 2022
and 2024, holding nodes, embeddings, and historical references fixed. ARI is
computed against the corresponding unperturbed hierarchy on the same nodes.

Gamma 0.1 perturbation mean ARI:

- 2022: k12 0.573, k48 0.583, k120 0.750
- 2024: k12 0.447, k48 0.472, k120 0.631

Approximate t intervals and paired gamma differences are in
`results/perturbation_uncertainty.json`. These intervals use only five seeds and
are descriptive.

### Coherence proxy and nulls

The automated coherence metric is a lexical character n-gram TF-IDF centroid
cosine. It is independent of MiniLM clustering embeddings but was previously used
in lexical baseline exploration, so it is a proxy rather than expert validation.

For 2024 gamma 0.1, actual scores exceed both group-size-preserving and
node-type-composition-preserving randomization nulls at k12/k48/k120. Full null
means and variability are in `results/coherence_null_2024_gamma0p1.json` and
`results/coherence_type_preserving_null_2024_gamma0p1.json`.

### Temporal stability

Cross-snapshot ARI bootstrap intervals are in `results/stability_bootstrap_*.json`.
Node bootstrap resamples shared nodes and does not model graph dependence or
uncertainty across independent corpora.

### Retrieval benchmark

A 2026 supplied-corpus run was created for evaluation, with annual-date limitation:
we cannot prove exact February 2026 availability. Retrieval settings were frozen
before scoring. Type A mean recall was lower for hierarchy than flat retrieval:

- hierarchy: 0.274
- flat: 0.298

Claim evidence retrieval was weak under text matching: returned claim nodes rarely
matched required claim strings. Type B remains inadequately scored without richer
claim/evidence judgment. See `results/retrieval_score_2026_gamma0p1.json` and
`results/retrieval_claim_scoring_2026_gamma0p1.json`.

## Extends direction inference

The separate direction layer is in `results/extends_direction/`. It inspects
method endpoints and origin years, never choosing an anchor solely because it is
`member[0]`. In the 2026 snapshot, 4 of 50 `extends` hyperedges are resolved and
46 remain unresolved, mostly because of missing method origin years. Edge `h_00003`
remains unresolved despite one method dated to the edge year because other method
origin years are missing. Resolved cases agree with member[0] in this data version
(4/4), but that is only a diagnostic and not a schema guarantee.

## Pending human-review metrics

- Scientific coherence blind review: `results/blind_scientific_coherence_review.json`.
- Label faithfulness/overclaim review: `results/label_faithfulness_review_sample.json`.

No human ratings are filled yet.

## Limitations

- Lexical coherence proxy is not expert semantic coherence.
- Extractive labels are not proof of zero overclaim.
- Benchmark target mapping is mostly exact surface matching; aliases remain
  unresolved.
- The hierarchy retrieval baseline underperformed the flat baseline on Type A
  recall.
- Exact all-pairs clustering is memory-heavy; the 2026 run used about 6.6 GiB peak
  ru_maxrss.

## Assessment checklist

Implemented: temporal snapshots, native hyperedge quotient, semantic/structural
objective, temporal regularization, persistent identity exports, perturbation
robustness, cross-snapshot ARI, retrieval outputs/scoring.

Remaining: literature synthesis in final prose, human coherence ratings,
faithfulness overclaim ratings, stronger Type B evidence scoring, and final
report formatting.
