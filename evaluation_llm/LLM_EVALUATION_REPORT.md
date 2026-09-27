# Blind LLM evaluation report

The assessor confirmed that documented blind LLM evaluation is acceptable. Three fresh-context judges independently evaluated anonymized packets with fixed rubrics: 48 coherence packets, 32 label/gloss packets, and 36 retrieval packets covering all 18 questions and both result lists. Judges received no clustering embeddings, merge scores, configuration identities or earlier project discussion. This is post-hoc evaluation of frozen outputs; nothing was retrained or reranked.

## Coherence against a matched null

Every 2024 k12 group from gamma 0 and gamma 0.1 was evaluated from 15 uniformly sampled member texts. Matched null groups preserve group sizes and type composition. Ratings: 1 incoherent, 2 mixed, 3 mostly coherent, 4 specific coherent concept. These are sampled-group judgments, not exhaustive scientific validation.

| Gamma | Actual mean | Null mean | Paired difference [descriptive 95% interval] | Actual rating ≥3 | Null rating ≥3 |
|---|---:|---:|---|---:|---:|

| 0 | 2.750 | 1.750 | 1.000 [0.500, 1.500] | 7/12 | 0/12 |

| 0.1 | 2.333 | 1.667 | 0.667 [0.000, 1.333] | 5/12 | 0/12 |

Both actual partitions exceed their null means. Gamma 0 is rated more coherent in this sample; gamma 0.1 has a descriptive actual-minus-null interval touching zero. This does not establish a universally superior configuration. Intervals resample twelve matched groups, conditional on a single judge and one null realization. Dependence within the same graph and judge stochasticity are not captured.

## Label faithfulness and informativeness

Four randomly selected groups at each required level (0 and 1), in each of four snapshots, yield 32 judgments. Evidence includes member examples, random members, keyword witnesses and available hyperedge context. The scope is faithfulness to the supplied extraction, not external full-paper truth.

| Judgment | Count |
|---|---:|

| accurate_informative | 16 |

| supported_but_vague | 16 |

| unsupported_or_wrong | 0 |

| insufficient_evidence | 0 |

Observed unsupported/wrong rate: **0/32 = 0.0%**; descriptive Wilson interval **0.0%–10.7%**. Half the sample is supported but vague. A zero observed rate does not prove universal safety, scientific truth, or usefulness. The interval is a sample summary, not a population-weighted estimate for differently sized level strata.

Human qualitative spot-checks recorded: **6/6**; explicit ratings/agreement decisions: **1**. C004 received 1, with uncertainty driven by group size. The developer saw only some author connections in C006, an energy/DFT theme in F002, uncertain scientific meaning despite shared keywords in F003, and vague searching-method themes in F001/F005. These comments do not establish six categorical agreements or an independent human overclaim rate; LLM judgments remain unchanged.

## All-question downstream evidence evaluation

The judge saw anonymous frozen result lists. It evaluated 448 claim criteria and 180 citation targets across both modes. Full=1, partial=0.5, absent/contradicted=0 for descriptive evidence coverage. Macro averages give each question equal weight. Method-node recovery and a name appearing in a claim are separate. Citation coverage uses supplied provenance titles plus available rubric identity mappings; ambiguous author/year mappings remain uncovered.

| Task | Mode | Direct method recall | Method mention recall | Claim coverage | Citation coverage |
|---|---|---:|---:|---:|---:|

| A | hierarchy | 0.064 | 0.294 | 0.125 | 0.060 |

| A | flat | 0.064 | 0.318 | 0.129 | 0.060 |

| B | hierarchy | N/A | N/A | 0.172 | 0.600 |

| B | flat | N/A | N/A | 0.172 | 0.600 |

There is no demonstrated hierarchy accuracy advantage: Type A direct recovery ties, claim coverage is slightly lower, and Type B coverage ties. The LLM alias-aware diagnostic differs from strict exact-name matching (which returns zero); both are retained with their scoring definitions. Scores assess available evidence, not the quality of a generated answer. Provenance source coverage alone does not entail a claim. The candidate set excludes datasets and the routing remains one coarse-filter step.

### Per-question coverage

| Question | Type | Mode | Claim coverage | Citation coverage |
|---|---|---|---:|---:|

| Q1 | A | flat | 0.000 | 0.000 |

| Q1 | A | hierarchy | 0.000 | 0.000 |

| Q2 | A | flat | 0.150 | 0.000 |

| Q2 | A | hierarchy | 0.100 | 0.000 |

| Q3 | A | flat | 0.167 | 0.000 |

| Q3 | A | hierarchy | 0.167 | 0.000 |

| Q4 | A | flat | 0.222 | 0.000 |

| Q4 | A | hierarchy | 0.222 | 0.000 |

| Q5 | A | flat | 0.083 | 0.500 |

| Q5 | A | hierarchy | 0.083 | 0.500 |

| Q6 | A | flat | 0.167 | 0.333 |

| Q6 | A | hierarchy | 0.167 | 0.333 |

| Q7 | A | flat | 0.000 | 0.000 |

| Q7 | A | hierarchy | 0.000 | 0.000 |

| Q8 | A | flat | 0.500 | 0.000 |

| Q8 | A | hierarchy | 0.500 | 0.000 |

| Q9 | A | flat | 0.000 | 0.000 |

| Q9 | A | hierarchy | 0.056 | 0.000 |

| Q10 | A | flat | 0.167 | 0.000 |

| Q10 | A | hierarchy | 0.083 | 0.000 |

| Q11 | A | flat | 0.250 | 0.000 |

| Q11 | A | hierarchy | 0.250 | 0.000 |

| Q12 | A | flat | 0.026 | 0.000 |

| Q12 | A | hierarchy | 0.026 | 0.000 |

| Q13 | A | flat | 0.021 | 0.000 |

| Q13 | A | hierarchy | 0.021 | 0.000 |

| Q14 | A | flat | 0.061 | 0.000 |

| Q14 | A | hierarchy | 0.076 | 0.000 |

| Q15 | B | flat | 0.250 | 0.400 |

| Q15 | B | hierarchy | 0.250 | 0.400 |

| Q16 | B | flat | 0.167 | 1.000 |

| Q16 | B | hierarchy | 0.167 | 1.000 |

| Q17 | B | flat | 0.071 | 0.600 |

| Q17 | B | hierarchy | 0.071 | 0.600 |

| Q18 | B | flat | 0.200 | 0.400 |

| Q18 | B | hierarchy | 0.200 | 0.400 |

### Type B qualitative evidence findings

#### Q15 — flat

What are the most important open scientific challenges (by Feb 2026) in AI-based multiscale modeling of solid-state materials?

Frozen-evidence assessment: 1 full, 3 partial, 6 absent, 0 contradicted claims. 2/5 citations covered. All rubric targets retained. Quantitative qualifiers and asserted-only caveats are not supplied by rubric text as evidence.

#### Q15 — hierarchy

What are the most important open scientific challenges (by Feb 2026) in AI-based multiscale modeling of solid-state materials?

Frozen-evidence assessment: 1 full, 3 partial, 6 absent, 0 contradicted claims. 2/5 citations covered. All rubric targets retained. Quantitative qualifiers and asserted-only caveats are not supplied by rubric text as evidence.

#### Q16 — flat

How does E(3)-equivariance improve GNN-based interatomic potentials in accuracy and data efficiency in comparison with vanilla GNN?

Frozen-evidence assessment: 0 full, 3 partial, 6 absent, 0 contradicted claims. 4/4 citations covered. All rubric targets retained. Quantitative qualifiers and asserted-only caveats are not supplied by rubric text as evidence.

#### Q16 — hierarchy

How does E(3)-equivariance improve GNN-based interatomic potentials in accuracy and data efficiency in comparison with vanilla GNN?

Frozen-evidence assessment: 0 full, 3 partial, 6 absent, 0 contradicted claims. 4/4 citations covered. All rubric targets retained. Quantitative qualifiers and asserted-only caveats are not supplied by rubric text as evidence.

#### Q17 — flat

Give evidences that ML-based coarse-grained molecular dynamics is effective for studying ionic transport and phase transitions in solid-state systems (by Feb 2026).

Frozen-evidence assessment: 0 full, 1 partial, 6 absent, 0 contradicted claims. 3/5 citations covered. All rubric targets retained. Quantitative qualifiers and asserted-only caveats are not supplied by rubric text as evidence.

#### Q17 — hierarchy

Give evidences that ML-based coarse-grained molecular dynamics is effective for studying ionic transport and phase transitions in solid-state systems (by Feb 2026).

Frozen-evidence assessment: 0 full, 1 partial, 6 absent, 0 contradicted claims. 3/5 citations covered. All rubric targets retained. Quantitative qualifiers and asserted-only caveats are not supplied by rubric text as evidence.

#### Q18 — flat

What mechanisms embed physical constraints, i.e., symmetry, locality, and size extensivity, into machine-learned interatomic potential architectures, and what evidence bears on whether these constraints improve transfer to system sizes and conditions beyond the training set (by Feb 2026)?

Frozen-evidence assessment: 1 full, 2 partial, 7 absent, 0 contradicted claims. 2/5 citations covered. All rubric targets retained. Quantitative qualifiers and asserted-only caveats are not supplied by rubric text as evidence.

#### Q18 — hierarchy

What mechanisms embed physical constraints, i.e., symmetry, locality, and size extensivity, into machine-learned interatomic potential architectures, and what evidence bears on whether these constraints improve transfer to system sizes and conditions beyond the training set (by Feb 2026)?

Frozen-evidence assessment: 1 full, 2 partial, 7 absent, 0 contradicted claims. 2/5 citations covered. All rubric targets retained. Quantitative qualifiers and asserted-only caveats are not supplied by rubric text as evidence.

## Audit trail and limits

Read PROTOCOL.md and JUDGE_INSTRUCTIONS.md for blinding, rubrics and prompt content; *_packets.json for inputs; *_ratings.json for unchanged judgments; decoded_ratings.json for identities after scoring; metrics.json for aggregation. Packet hashes fix the inputs. Each supported claim references actual returned node IDs, and completeness checks retain every rubric criterion. One judge per task, unknown exact backend version, no repeat judging, sparse group samples and unversioned source text limit generalization. A domain expert is not required by the assessor, but human spot-check completion must still be documented honestly.
