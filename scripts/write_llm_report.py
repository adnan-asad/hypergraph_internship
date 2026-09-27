import json
from pathlib import Path
r=Path('evaluation_llm')
m=json.loads((r/'metrics.json').read_text(encoding='utf-8'))
decoded=json.loads((r/'decoded_ratings.json').read_text(encoding='utf-8'))
packets={p['packet_id']:p for p in json.loads((r/'retrieval_packets.json').read_text(encoding='utf-8'))['packets']}
parts=['# Blind LLM evaluation report',
'The assessor confirmed that documented blind LLM evaluation is acceptable. Three fresh-context judges independently evaluated anonymized packets with fixed rubrics: 48 coherence packets, 32 label/gloss packets, and 36 retrieval packets covering all 18 questions and both result lists. Judges received no clustering embeddings, merge scores, configuration identities or earlier project discussion. This is post-hoc evaluation of frozen outputs; nothing was retrained or reranked.',
'## Coherence against a matched null',
'Every 2024 k12 group from gamma 0 and gamma 0.1 was evaluated from 15 uniformly sampled member texts. Matched null groups preserve group sizes and type composition. Ratings: 1 incoherent, 2 mixed, 3 mostly coherent, 4 specific coherent concept. These are sampled-group judgments, not exhaustive scientific validation.',
'| Gamma | Actual mean | Null mean | Paired difference [descriptive 95% interval] | Actual rating ≥3 | Null rating ≥3 |\n|---|---:|---:|---|---:|---:|']
for g,z in m['coherence'].items():
    d=z['paired_actual_minus_null'];ci=d['bootstrap95']
    parts.append(f"| {g.replace('p','.')} | {z['actual']['mean']:.3f} | {z['null']['mean']:.3f} | {d['mean']:.3f} [{ci[0]:.3f}, {ci[1]:.3f}] | {z['actual_rating_ge3']}/12 | {z['null_rating_ge3']}/12 |")
parts += ['Both actual partitions exceed their null means. Gamma 0 is rated more coherent in this sample; gamma 0.1 has a descriptive actual-minus-null interval touching zero. This does not establish a universally superior configuration. Intervals resample twelve matched groups, conditional on a single judge and one null realization. Dependence within the same graph and judge stochasticity are not captured.',
'## Label faithfulness and informativeness',
'Four randomly selected groups at each required level (0 and 1), in each of four snapshots, yield 32 judgments. Evidence includes member examples, random members, keyword witnesses and available hyperedge context. The scope is faithfulness to the supplied extraction, not external full-paper truth.',
'| Judgment | Count |\n|---|---:|']
for k,v in m['faithfulness']['counts'].items(): parts.append(f'| {k} | {v} |')
f=m['faithfulness'];ci=f['descriptive_wilson95']
parts += [f"Observed unsupported/wrong rate: **{f['overclaim_numerator']}/{f['determinate_denominator']} = {f['overclaim_rate']:.1%}**; descriptive Wilson interval **{ci[0]:.1%}–{ci[1]:.1%}**. Half the sample is supported but vague. A zero observed rate does not prove universal safety, scientific truth, or usefulness. The interval is a sample summary, not a population-weighted estimate for differently sized level strata.",
f"Human qualitative spot-checks recorded: **{m['human_spotchecks']['qualitatively_reviewed']}/6**; explicit ratings/agreement decisions: **{m['human_spotchecks']['explicit_ratings_or_agreement']}**. C004 received 1, with uncertainty driven by group size. The developer saw only some author connections in C006, an energy/DFT theme in F002, uncertain scientific meaning despite shared keywords in F003, and vague searching-method themes in F001/F005. These comments do not establish six categorical agreements or an independent human overclaim rate; LLM judgments remain unchanged.",
'## All-question downstream evidence evaluation',
'The judge saw anonymous frozen result lists. It evaluated 448 claim criteria and 180 citation targets across both modes. Full=1, partial=0.5, absent/contradicted=0 for descriptive evidence coverage. Macro averages give each question equal weight. Method-node recovery and a name appearing in a claim are separate. Citation coverage uses supplied provenance titles plus available rubric identity mappings; ambiguous author/year mappings remain uncovered.',
'| Task | Mode | Direct method recall | Method mention recall | Claim coverage | Citation coverage |\n|---|---|---:|---:|---:|---:|']
for typ, modes in m['retrieval_macro'].items():
    for mode,z in modes.items():
        direct=f"{z['direct_method_recall']:.3f}" if typ=='A' else 'N/A'
        mention=f"{z['method_mention_recall']:.3f}" if typ=='A' else 'N/A'
        parts.append(f"| {typ} | {mode} | {direct} | {mention} | {z['claim_coverage']:.3f} | {z['citation_coverage']:.3f} |")
parts += ['There is no demonstrated hierarchy accuracy advantage: Type A direct recovery ties, claim coverage is slightly lower, and Type B coverage ties. The LLM alias-aware diagnostic differs from strict exact-name matching (which returns zero); both are retained with their scoring definitions. Scores assess available evidence, not the quality of a generated answer. Provenance source coverage alone does not entail a claim. The candidate set excludes datasets and the routing remains one coarse-filter step.',
'### Per-question coverage',
'| Question | Type | Mode | Claim coverage | Citation coverage |\n|---|---|---|---:|---:|']
for row in sorted(m['retrieval_per_question'],key=lambda x:(int(x['question_id'][1:]),x['mode'])):
    parts.append(f"| {row['question_id']} | {row['type']} | {row['mode']} | {row['claim_coverage']:.3f} | {row['citation_coverage']:.3f} |")
parts += ['### Type B qualitative evidence findings']
for row in sorted([x for x in decoded['retrieval'] if x['type']=='B'],key=lambda x:(int(x['question_id'][1:]),x['mode'])):
    parts += [f"#### {row['question_id']} — {row['mode']}",packets[row['packet_id']]['question'],str(row['summary'])]
parts += ['## Audit trail and limits',
'Read PROTOCOL.md and JUDGE_INSTRUCTIONS.md for blinding, rubrics and prompt content; *_packets.json for inputs; *_ratings.json for unchanged judgments; decoded_ratings.json for identities after scoring; metrics.json for aggregation. Packet hashes fix the inputs. Each supported claim references actual returned node IDs, and completeness checks retain every rubric criterion. One judge per task, unknown exact backend version, no repeat judging, sparse group samples and unversioned source text limit generalization. A domain expert is not required by the assessor, but human spot-check completion must still be documented honestly.']
(r/'LLM_EVALUATION_REPORT.md').write_text('\n\n'.join(parts)+'\n',encoding='utf-8')
