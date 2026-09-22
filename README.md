# Temporal Hypergraph Abstraction

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
