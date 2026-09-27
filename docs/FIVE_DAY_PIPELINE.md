# Five-day implementation pipeline

## Decision

Build a stable hierarchy at each snapshot. Questions select branches through it;
questions and benchmark answers do not determine cluster membership.

The shipped graph is the primary input. Paper-reading agents form an optional
evidence layer around it; reconstructing all 52 papers into a new graph is not on
the critical path. A retrieval index finds passages; it is not itself a validated
hypergraph and does not resolve entity identities or relationship roles.

## Core route (required)

Raw export -> validation -> availability-gated snapshots -> text representations
and native hyperedge incidence -> laminar hierarchy with budgets -> temporal
coupling and lineage -> evidence-supported labels -> coarse-to-fine retrieval
versus flat retrieval -> independent evaluation -> reproducible report.

## Evidence route (optional, bounded)

Supplied/available papers -> version-and-date manifest -> page/section-aware text
chunks -> independent reader outputs with exact supporting passages -> reviewer
adjudication -> approved evidence store -> a small passage retrieval index.

Join evidence to existing node/edge IDs through recorded, reviewed mappings. Keep
unresolved mappings unresolved. Reader agents produce proposals; they never edit
the supplied graph. If a correction is accepted, write an explicit patch log and
evaluate the amended graph separately. Do not silently enrich only the hierarchy
and then compare it with a flat baseline lacking the same evidence.

Reader outputs are not authoritative truth. Verify quotes against source text,
retain page/section and source hash, and distinguish reported background from the
paper's own result. A second agent checking the first is useful error control,
not independent human validation. Using the same passages to generate and assess
labels checks source consistency but does not prove scientific truth; preserve a
blind audit and disclose overlap. Future-dated versions must not enter old cutoffs.

Do not index ground_truth.json or benchmark evidence snippets as retrieval content.
Keep questions out of clustering and paper-task selection. Select the initial
paper pilot by graph coverage/date/method diversity, before looking at test scores.

## Five-day schedule

| Day | Required output | Evidence/agent work |
|---|---|---|
| 1 | Loader, validation, four snapshot audits, frozen date policy and benchmark adapter plan | Maximum two-hour pilot with 3–5 available papers; stop if sources or extraction are difficult |
| 2 | Native quotient-edge contraction, semantic baseline, nested hierarchy and formal criterion | Reviewed evidence records; no new extraction pipeline |
| 3 | Temporal coupling, persistent IDs/events, labels and both retrieval paths | Optional citation lookup through a simple local index; same access for both retrieval baselines |
| 4 | Three method variants; 10% edge removal with five seeds; cross-snapshot stability; independent coherence/null and label audits; task metrics | Readers can assist with evidence lookup, but cannot see benchmark answers or score their own outputs as independent judges |
| 5 | Error analysis, confidence intervals with caveats, 3–5-page report, pinned environment, clean reproduction, AI log | No new features; source gaps become explicit limitations |

Three hierarchy variants: semantics only; semantics+native hypergraph; and
semantics+hypergraph+temporal coupling. Keep budgets and downstream scoring fixed.
Do not trade away null controls, label faithfulness, uncertainty reporting, or the
flat baseline to process more papers. There is no requirement to reread all 52
papers before building the hierarchy.

## Agent ownership

- One implementation agent owns src/ and tests/ at a time.
- At most two concurrent readers initially; each has one paper and one separate
  output file. More workers are justified only after the pilot's outputs validate.
- One reviewer examines reader proposals and source passages, without modifying
  raw graph or silently accepting suggested mappings.
- A coordinator accepts reviewed evidence and maintains the AI-use log.

If using separate Herdr panes, launch distinct Pi sessions and give each an
explicit assignment. This is manual orchestration, not automatic subagent support.
Pi's official repository provides a subagent extension example, but availability
in the user's installed version must be checked before relying on it. Do not
install an unpinned extension mid-deadline just to avoid two manual reader panes.

Reference: https://github.com/earendil-works/pi/tree/main/packages/coding-agent/examples/extensions/subagent

## Evidence record contract

Each proposed record needs: article_id; source_path; source_sha256; source version;
publication date and date precision; page/section; verbatim supporting passage;
bounded paraphrase; candidate existing node/edge IDs; relation roles marked
explicit/inferred/unknown; limitations; agent identity/model/prompt; review status.

Use review states pending, accepted, rejected, unresolved. Only accepted records
enter generation/retrieval. Empty or missing evidence remains unresolved rather
than being filled from model memory. Preserve historical evidence versions.

## Current starter status

Implemented: standard-library graph validation, audit, snapshot generation and
unit tests. Not implemented: embeddings, hierarchy, temporal clustering, RAG index,
paper extraction, labels, downstream evaluation, or automatic agent orchestration.

The snapshot files contain original historical metadata for audit. Do not pass
whole records to a labeller: filter last_seen_year and future provenance first.
The export has no text version history, so perfect historical text reconstruction
cannot be guaranteed. Annual dates also cannot establish February 2026 eligibility
for every 2026 item.
