# Quantitative developer review of the 2020 hierarchy

Prepared 26 September 2026. Reviewer: Adnan, project developer. Anonymous configurations A/B/C were retained; the identity key was not opened for this analysis.

## What this report measures

This is a quantitative descriptive analysis of recorded developer judgments, supplemented by qualitative notes. The reviewer reports inspecting most groups. Some entries concern individual members; others summarize groups. Consequently, the primary unit is a **recorded rating entry**, not a uniformly assessed group or an independent node. No missing rating is interpreted as positive, negative, or uninspected. The counts are exact for the provided file, but they do not establish a population-level coherence rate or a ranking of clustering configurations.

## Main findings

The sheet contains 540 displayed rows: 36 groups, 12 per run, with 15 central/random/peripheral sample rows per group. There are 120 filled ratings (22.2% of displayed rows), spanning 22/36 groups (61.1%). The other 14 groups have no recorded rating. This is documentation coverage, not a claim about how much the reviewer read. Each row is a sampled example, not necessarily a unique node; these samples do not cover every node in the original graph.

| Run | Displayed rows | Rated entries | Groups with entries / 12 | 0 | 1 | 2 | Unsure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dev_run_A | 180 | 104 | 10 | 5 | 42 | 33 | 24 |
| dev_run_B | 180 | 7 | 6 | 1 | 4 | 2 | 0 |
| dev_run_C | 180 | 9 | 6 | 1 | 4 | 3 | 1 |
| Total | 540 | 120 | 22 / 36 | 7 | 50 | 38 | 25 |

## Rating distribution

The intended rubric was 0 = no clear coherence, 1 = broad/mixed coherence, 2 = clear coherence, and unsure = insufficient confidence. The mixed rating scope means these labels apply to recorded judgments, not automatically to whole groups.

| Recorded rating | Count | Share of all 120 entries | Share of 95 numeric entries |
| --- | --- | --- | --- |
| 0 | 7 | 5.8% | 7.4% |
| 1 | 50 | 41.7% | 52.6% |
| 2 | 38 | 31.7% | 40.0% |
| unsure | 25 | 20.8% | Excluded |

Of the 95 numeric entries, 88 (92.6%) are 1 or 2. This indicates broad/mixed or clear coherence in those recorded judgments; **it must not be described as 92.6% of groups being coherent**. Clear-coherence ratings account for 38/95 (40.0%) of numeric entries. Uncertainty remains substantial: 25/120 (20.8%) entries are unsure. No ordinal-score average is needed to describe this distribution.

## Central, random and peripheral entries

These are sampling categories, not separate independent experiments. Central/peripheral selection uses the clustering representation. Counts show how annotation is distributed; they do not establish causal effects of member position.

| Run | Sample kind | Rated | 0 | 1 | 2 | Unsure |
| --- | --- | --- | --- | --- | --- | --- |
| dev_run_A | central | 38 | 4 | 12 | 20 | 2 |
| dev_run_A | random | 34 | 0 | 20 | 5 | 9 |
| dev_run_A | peripheral | 32 | 1 | 10 | 8 | 13 |
| dev_run_B | central | 6 | 1 | 4 | 1 | 0 |
| dev_run_B | random | 1 | 0 | 0 | 1 | 0 |
| dev_run_B | peripheral | 0 | 0 | 0 | 0 | 0 |
| dev_run_C | central | 7 | 1 | 2 | 3 | 1 |
| dev_run_C | random | 1 | 0 | 1 | 0 | 0 |
| dev_run_C | peripheral | 1 | 0 | 1 | 0 | 0 |

## Repeated members and mixed judgments

After grouping recorded entries by (run, group, node ID), 116 distinct keys have ratings. This grouping is a duplicate audit, not a conversion into node-level truth: a rating on that row may summarize its whole group.

| Deduplicated-key status | Count |
| --- | --- |
| 0 | 7 |
| 1 | 47 |
| 2 | 36 |
| unresolved_multiple_values | 3 |
| unsure | 23 |

Repeated samples with identical ratings are counted once in the sensitivity audit. Different ratings for the same key are retained as unresolved; none are averaged or arbitrarily selected. The primary 120-entry table intentionally retains every annotation, including repeated sample positions.

| Run | Group | Node | Recorded values | CSV lines |
| --- | --- | --- | --- | --- |
| dev_run_A | L0_c2986 | clai_00475 | 1, 2 | 34, 41 |
| dev_run_A | L0_c2978 | metr_00022 | 1, unsure | 83, 87 |
| dev_run_A | L0_c2978 | cite_00578 | unsure, unsure | 85, 88 |
| dev_run_A | L0_c2972 | auth_00142 | 1, 2 | 93, 99 |

Nine groups have more than one distinct recorded value (seven in A and two in C). Different values within a group can legitimately express variation between members. They should not automatically be called reviewer conflicts. The 13 groups with a single distinct value likewise cannot automatically be treated as 13 explicit whole-group judgments.

## Qualitative interpretation

The notes identify plausible themes involving molecular/crystal machine learning, amorphous carbon, materials properties, fracture, and software ecosystems. They also identify uncertainty about author collections, generic chemical names, shared keywords, and relations between platform-specific evidence. Some positive numeric ratings accompany tentative language; values were preserved rather than silently recoded. Notes reflect the reviewer’s understanding and were not treated as independently verified scientific facts.

The review is evidence that the developer inspected outputs and identified both plausible connections and possible failures. It does not measure label overclaim: that requires assessing specific generated assertions against source evidence. Coherence annotations must not be substituted for label-faithfulness scores.

## Limitations and appropriate claims

1. Reviewer is the developer, not an independent domain expert; the review was supported by discussion with an assistant. Configuration identities were concealed using anonymous labels, but this does not remove developer familiarity or confirmation bias.
2. Member-level and group-level rating scope was not recorded consistently. No scope was inferred solely from one or several ratings in a group.
3. Annotation density differs markedly by run and by sampling category. There is no defensible best-run ranking from these counts.
4. Missing entries were left missing, and unsure was not converted to zero.
5. Examples were selected by central/random/peripheral sampling and may repeat nodes; they are not a simple random sample of all corpus nodes.
6. No human-rated null partition or second reviewer is present. This review complements, rather than replaces, the separate automated null-model evaluation.
7. No confidence interval or significance test is reported: treating mixed-scope, dependent entries as independent trials would imply unsupported precision.

## CSV integrity and reproducibility

The original Downloads CSV was not modified. One row (CSV line 2) contains an unquoted comma in the final note, producing a tenth column. The analysis rejoined the final fragments with a comma to preserve the note. One rating spelled usnure was normalized to unsure. All original fields, source line numbers, normalized ratings, and complete notes are retained in annotations_audit.json. All per-group counts and duplicate diagnostics are in metrics.json.

Source SHA-256: `240c9c9824dd6cf7be74c212f1daacf84ba8a1e5b1ff1e54ea4edf98e7109c63`

## Text suitable for the assessment report

> A developer review was conducted using anonymously labelled outputs from three 2020 clustering configurations. The sheet contained 540 sampled-member rows across 36 top-level groups. The developer recorded 120 ratings spanning 22 groups: 38 ratings of 2, 50 of 1, 7 of 0, and 25 unsure. Among the 95 numeric annotations, 40.0% received the highest rating and 92.6% received either 1 or 2. These are descriptive annotation proportions, not group-level coherence rates: the reviewer mixed member-level and group-level judgments, and annotation density differed across configurations. Qualitative notes identified recognizable themes alongside uncertainty about author collections, keyword-driven similarity, and peripheral members. The review is reported as developer error analysis with quantitative annotation summaries; it does not establish a winning configuration or an independently validated semantic-coherence rate.

## Per-group audit

Rows are ordered by anonymous run and group ID. Multiple distinct values are preserved, not treated as an error by default.

| Run | Group | Original group size | Filled rows / 15 | 0 | 1 | 2 | Unsure | Distinct values |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev_run_A | L0_c2747 | 12 | 1 | 1 | 0 | 0 | 0 | 0 |
| dev_run_A | L0_c2849 | 16 | 1 | 0 | 0 | 0 | 1 | unsure |
| dev_run_A | L0_c2969 | 22 | 1 | 1 | 0 | 0 | 0 | 0 |
| dev_run_A | L0_c2972 | 112 | 11 | 0 | 7 | 4 | 0 | 1, 2 |
| dev_run_A | L0_c2978 | 55 | 15 | 0 | 4 | 5 | 6 | 1, 2, unsure |
| dev_run_A | L0_c2986 | 80 | 15 | 2 | 9 | 1 | 3 | 0, 1, 2, unsure |
| dev_run_A | L0_c2988 | 100 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_A | L0_c2989 | 54 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_A | L0_c2991 | 361 | 15 | 1 | 7 | 2 | 5 | 0, 1, 2, unsure |
| dev_run_A | L0_c2994 | 430 | 15 | 0 | 4 | 9 | 2 | 1, 2, unsure |
| dev_run_A | L0_c2996 | 120 | 15 | 0 | 3 | 8 | 4 | 1, 2, unsure |
| dev_run_A | L0_c2997 | 143 | 15 | 0 | 8 | 4 | 3 | 1, 2, unsure |
| dev_run_B | L0_c2784 | 23 | 1 | 0 | 1 | 0 | 0 | 1 |
| dev_run_B | L0_c2858 | 20 | 1 | 1 | 0 | 0 | 0 | 0 |
| dev_run_B | L0_c2958 | 41 | 1 | 0 | 1 | 0 | 0 | 1 |
| dev_run_B | L0_c2963 | 44 | 1 | 0 | 1 | 0 | 0 | 1 |
| dev_run_B | L0_c2971 | 143 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_B | L0_c2973 | 39 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_B | L0_c2975 | 28 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_B | L0_c2977 | 95 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_B | L0_c2985 | 102 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_B | L0_c2986 | 108 | 1 | 0 | 1 | 0 | 0 | 1 |
| dev_run_B | L0_c2996 | 340 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_B | L0_c2997 | 522 | 2 | 0 | 0 | 2 | 0 | 2 |
| dev_run_C | L0_c2833 | 23 | 2 | 0 | 1 | 1 | 0 | 1, 2 |
| dev_run_C | L0_c2856 | 20 | 1 | 1 | 0 | 0 | 0 | 0 |
| dev_run_C | L0_c2902 | 28 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_C | L0_c2929 | 33 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_C | L0_c2935 | 79 | 3 | 0 | 1 | 2 | 0 | 1, 2 |
| dev_run_C | L0_c2960 | 73 | 1 | 0 | 0 | 0 | 1 | unsure |
| dev_run_C | L0_c2975 | 52 | 1 | 0 | 1 | 0 | 0 | 1 |
| dev_run_C | L0_c2982 | 140 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_C | L0_c2994 | 264 | 1 | 0 | 1 | 0 | 0 | 1 |
| dev_run_C | L0_c2995 | 230 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_C | L0_c2996 | 203 | 0 | 0 | 0 | 0 | 0 | Missing |
| dev_run_C | L0_c2997 | 360 | 0 | 0 | 0 | 0 | 0 | Missing |
