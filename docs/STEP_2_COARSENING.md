# Step 2: preserve hyperedges when groups merge

This step implements the mechanics required by T4. It does not choose semantic
groups or implement the full hierarchy. It depends on the step-one data_pipeline
module. Python 3.10+; no additional dependencies.

## Representation

An edge connecting a, b, c, d becomes a counted edge on X, c, d when a and b merge:
`{"X": 2, "c": 1, "d": 1}`. It remains one multiway relationship, not a clique.
When all four endpoints merge, the edge remains as an internal record with count
4. Different source edges remain separate, even when they have identical members.

For every edge retain its ID, original endpoint order, original arity, relation,
dates, attributes and provenance. `members` now lists coarse group IDs;
`incidence_counts` gives original endpoint multiplicities; `internal` tells whether
only one group is touched. Original `n_targets` and evaluation attributes describe
the original relationship, not a new assertion about all members of a super-node.

Endpoint roles are not inferred. Any future role inference belongs in separately
marked metadata. This implementation preserves source records without claiming
that an entire group extends another group or was evaluated on another group.

## Structural score

For each original edge, compute `(coarse_arity - 1)/(original_arity - 1)` and take
the mean over original edges. Empty edge sets have score zero. The denominator
never changes during contraction. This matches the proposed uniform-weight
fragmentation term exactly. It is not a faithfulness or semantic-coherence metric.

The score always decreases or stays constant under merges. Optimizing it alone
would favor putting everything together, so semantic loss, display budgets and
temporal costs must be added before it can choose useful groups. Hyperedge fidelity
comes from retaining records and multiplicities, not from minimizing this score.

## Run

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m tkh_abstraction.quotient
```

The demonstration is synthetic, not a scientific clustering result. It shows
partial collapse across three groups, across two groups, then complete collapse.
The three fragmentation values should be approximately 0.667, 0.333, and 0.

## What is verified

Tests cover the required collapse cases, complete partition coverage including
isolates, overlap rejection, preservation of parallel edges/provenance, input
immutability, invalid merges, and objective equivalence against the original
hyperedges across different merge sequences.

The correctness-first implementation traverses original incidences after every
merge and copies the quotient. This is suitable for validation and a reference
implementation; a clustering search that scores thousands of candidates should
use cached semantic and incidence deltas rather than repeatedly deep-copying it.

## Next Pi review task

Read this document, quotient.py and its tests alongside T4 in docs/assessment.md.
Run the tests and demo. Explain how original_arity differs from coarse_arity and
why an internal edge must remain available. Inspect one real hyperedge, propose
a clearly labeled illustrative partition, and confirm its source metadata survives
coarsening. Do not describe that partition as a learned scientific grouping.
Update AI_USAGE.md with this review and any modifications. Then propose the
semantic representation and merge-cost implementation; do not install new
dependencies or launch a large experiment yet. Do not commit or push automatically.
