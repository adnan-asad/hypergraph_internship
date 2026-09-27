# Assessment evidence and remaining limits

This is a completed packaging/audit pass over the supplied implementation, not a claim that every research desideratum has succeeded. Use `report.md` and root `metrics.json` as the current account. Earlier milestone documents and requirement inventories are historical.

| Requirement / weight | Evidence | Status |
|---|---|---|
| Formal problem and method, 25% | report.md; exact merge-delta tests; stagewise objective | Implemented; greedy, no optimality guarantee |
| Valid evaluation, 30% | root metrics.json; lexical and blind-LLM nulls; 20 perturbation runs; cross-snapshot bootstrap; blind evidence evaluation of all questions; developer annotations | Blind LLM coherence/faithfulness accepted by assessor and now executed; six qualitative developer spot-checks recorded; no demonstrated retrieval gain |
| Temporal treatment, 15% | Four snapshot exports, overlap matching, event logs | Implemented; timestamps annual and node text unversioned |
| Native collapse, 10% | Counted quotients preserving every original edge and provenance | Implemented and exhaustively audited for four main snapshots and four levels |
| Reproducibility, 10% | Pinned requirements, tests, reproduction script, saved evidence, manifest | Local numerical tests pass; full fresh model download/clustering rerun not performed in packaging audit |
| Clarity, 10% | report, evidence ledger, AI disclosure | Explicit verified/assumed separation |

## Changes in this packaging pass

- Fixed base singleton persistent IDs to match later `node_<id>` identities. Canonical `submission/<year>/hierarchy.json` contains corrected exports; original result files are unchanged.
- Made peak-RSS collection portable: Linux values unchanged; unavailable Windows measurements return null, not fabricated zero.
- Added strict exact-name retrieval diagnostics and tests. Existing substring-proxy scores are preserved and relabelled accurately in the report.
- Added exhaustive hierarchy, quotient, and extractive-integrity checks and a consolidated metrics file.
- Integrated the actual developer CSV and its quantitative report. Mixed-scope annotations remain mixed-scope; blanks remain missing.

## Important interpretation

Neither unit-test success nor zero extractive copy errors measures scientific label overclaim. A new, separately blinded level-0/1 sample was actually judged: 16 informative, 16 supported-but-vague, zero unsupported/wrong. Observed overclaim is 0/32 with descriptive Wilson interval 0–10.7%; this is source-extraction faithfulness, not proof of external scientific truth. Old development review packets remain historical/unrated; the new `evaluation_llm/` artifacts are authoritative. Human spot-check completion remains separate.

The strict retrieval audit was added after answers had been inspected. It is a diagnostic of the frozen outputs, not a new preregistered headline benchmark. No weights, groupings, candidate pools, or rankings were changed based on those answers.

## What to do before submitting

Read the final report and AI disclosure, confirm you can explain the formulas, and run the short audit/test commands in README. Six qualitative developer spot checks are recorded; only one is numerically rated. Preserve the expressed uncertainty and do not infer categorical agreement. Domain expertise is not mandatory according to the assessor, but do not claim manual checks before entering actual judgments. The remaining major method limitation is coarse-filter retrieval rather than full multilevel routing; its negative result is disclosed.
