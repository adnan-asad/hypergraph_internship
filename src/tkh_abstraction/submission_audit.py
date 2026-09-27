"""Rebuild submission exports and audit frozen results; no clustering or tuning.

Run from repository root. Original result files remain unchanged.
"""
from __future__ import annotations
import argparse, hashlib, json, re, statistics
from collections import Counter
from pathlib import Path
from .data_pipeline import load_graph, snapshot, write_json

RUNS = {
    2020: 'hypergraph_agglomerative_lambda_0p1_2020',
    2022: 'temporal_lambda_0p1_gamma_0p1_2022',
    2024: 'temporal_lambda_0p1_gamma_0p1_2024',
    2026: 'temporal_lambda_0p1_gamma_0p1_2026_eval',
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def norm(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def exact_target_hit(target, results, eligible_types):
    key = norm(target)
    return bool(key) and any(r['type'] in eligible_types and norm(r['surface_form']) == key for r in results)


def retrieval_audit(graph, ground_truth, frozen):
    scores=[]; mapping=[]
    for q in frozen['queries']:
        truth=ground_truth[q['question_id']]
        if truth['type'] != 'A':
            continue
        # The benchmark uses expected_methods for a dataset question as well.
        types={'method','dataset'}
        targets=truth['expected_methods']
        for target in targets:
            ids=[n['id'] for n in graph['nodes'] if n['type'] in types and norm(n['surface_form'])==norm(target)]
            mapping.append({'question_id':q['question_id'],'target':target,'exact_node_ids':ids,'status':'mapped' if ids else 'unresolved_alias_or_absent'})
        for mode in ['hierarchy','flat']:
            found=[t for t in targets if exact_target_hit(t,q[mode]['results'],types)]
            scores.append({'question_id':q['question_id'],'mode':mode,'targets':len(targets),'hits':found,'recall':len(found)/len(targets) if targets else None})
    work=[]
    for q in frozen['queries']:
        hw=q['hierarchy']['retrieval_work']; fw=q['flat']['retrieval_work']
        work.append({'question_id':q['question_id'],'hierarchy_node_scores':hw['nodes_scored'],'group_scores':hw['groups_scored'],'flat_node_scores':fw['nodes_scored'],'score_count_ratio':(hw['nodes_scored']+hw['groups_scored'])/fw['nodes_scored']})
    return {'policy':'Post-hoc strict normalized exact-name diagnostic, method/dataset nodes only. No substring matches, aliases or claim mentions counted as recovered methods. Frozen retrieval unchanged.',
            'limitations':['Unresolved aliases count as misses: this is a conservative diagnostic, not a complete semantic benchmark score.','Type B and claim entailment remain unscored.','Candidate pool excluded datasets, making dataset recovery impossible.','Work excludes encoding, centroid formation, sorting, and offline clustering; it is not measured latency.'],
            'type_A_macro_recall':{m:statistics.mean(s['recall'] for s in scores if s['mode']==m) for m in ['hierarchy','flat']},
            'mapping_coverage':{'target_occurrences':len(mapping),'exactly_mapped':sum(bool(m['exact_node_ids']) for m in mapping)},
            'per_question':scores,'target_mapping':mapping,'work':work,
            'mean_score_count_ratio':statistics.mean(w['score_count_ratio'] for w in work)}


def audit_exports(graph, out):
    records=[]; previous_leaves=None
    for year, run in RUNS.items():
        src=Path('results')/run; snap=snapshot(graph,year)
        nodes={n['id']:n for n in snap['nodes']}; expected=set(nodes)
        rows=read(src/'hierarchy_labeled_extractive.json')['supernodes']
        byid={r['id']:r for r in rows}
        assert len(byid)==len(rows), 'duplicate hierarchy ID'
        per_level={}
        for level in ['k12','k48','k120','leaves']:
            subset=[r for r in rows if r['level_name']==level]
            flat=[m for r in subset for m in r['member_ids']]
            assert len(flat)==len(expected) and set(flat)==expected, 'partition overlap or missing node'
            assert len(subset)==(len(expected) if level=='leaves' else int(level[1:])), 'wrong budget'
            for r in subset:
                assert all(k in r for k in ['id','level','parent_id','member_ids','label','gloss'])
                if r['parent_id'] is not None:
                    assert set(r['member_ids']) <= set(byid[r['parent_id']]['member_ids']), 'non-nested hierarchy'
                if level=='leaves':
                    r['persistent_id']='node_'+r['member_ids'][0]
            assert len({r['persistent_id'] for r in subset})==len(subset)
            # Verify lossless source-edge provenance and counted incidence at each cut.
            quotient=read(src/f'quotient_{level}.json')
            original={e['id']:e for e in snap['hyperedges']}
            assert len(quotient['hyperedges'])==len(original)
            assert {e['id'] for e in quotient['hyperedges']}==set(original)
            assignment={m:r['id'] for r in subset for m in r['member_ids']}
            for e in quotient['hyperedges']:
                orig=original[e['id']]
                assert e['original_members']==orig['members']
                assert e['original_arity']==len(orig['members'])
                assert e['incidence_counts']==dict(Counter(assignment[m] for m in orig['members']))
                for key,value in orig.items():
                    if key!='members': assert e[key]==value
            per_level[level]=len(subset)
        leaves={r['member_ids'][0]:r['persistent_id'] for r in rows if r['level_name']=='leaves'}
        if previous_leaves is not None:
            assert all(leaves[m]==pid for m,pid in previous_leaves.items())
        previous_leaves=leaves
        # Exhaustive mechanical extraction audit. This is not an entailment score.
        checks=[]
        for r in rows:
            texts=[nodes[m]['surface_form'] for m in r['member_ids']]
            supports=r['supporting_node_ids']; support_text=r['supporting_text']
            exact=all(m in r['member_ids'] and nodes[m]['surface_form']==t for m,t in zip(supports,support_text)) and len(supports)==len(support_text)
            expected_gloss=f"Extractive summary only: {len(r['member_ids'])} nodes; examples include " + '; '.join(texts[:3])
            checks.append(exact and r['gloss']==expected_gloss)
        dest=out/str(year); write_json(dest/'hierarchy.json',{'supernodes':rows})
        events=read(src/'temporal_identity_events.json') if (src/'temporal_identity_events.json').exists() else {'initial_snapshot':True,'events':[{'event_type':'birth','current_group_id':r['id'],'current_persistent_id':r['persistent_id']} for r in rows if r['level_name']!='leaves']}
        write_json(dest/'temporal_events.json',events)
        records.append({'year':year,'nodes':len(nodes),'hyperedges':len(snap['hyperedges']),'groups':per_level,'partition_nested_and_quotient_checks':'passed','extractive_glosses_checked':len(checks),'extractive_integrity_failures':len(checks)-sum(checks),'source':str(src)})
    return records


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--graph',type=Path,required=True); parser.add_argument('--ground-truth',type=Path,required=True)
    a=parser.parse_args(); graph=load_graph(a.graph)
    exports=audit_exports(graph,Path('submission'))
    frozen=read('results/retrieval_frozen_2026_gamma0p1.json')
    strict=retrieval_audit(graph,read(a.ground_truth),frozen)
    write_json(Path('results/submission_retrieval_audit.json'),strict)
    metrics={'status':'Audited saved experiment evidence; not a rerun of full clustering.',
        'graph_sha256':hashlib.sha256(a.graph.read_bytes()).hexdigest(),'export_validation':exports,
        'coherence_lexical_proxy':read('results/coherence_null_2024_gamma0p1.json'),
        'coherence_type_preserving_null':read('results/coherence_type_preserving_null_2024_gamma0p1.json'),
        'perturbation':read('results/perturbation_uncertainty.json'),
        'cross_snapshot':{p.stem:read(p) for p in Path('results').glob('stability_bootstrap_*.json')},
        'label_faithfulness':{'semantic_overclaim_rate':None,'status':'Not independently assessed. Mechanical extractive integrity is reported separately and cannot establish scientific faithfulness.'},
        'retrieval_historical_substring_proxy':read('results/retrieval_score_2026_gamma0p1.json'),
        'retrieval_strict_diagnostic':strict,
        'developer_review':read('docs/developer_review/metrics.json'),
        'limitations':['Developer ratings mix row/group units and uneven coverage; not a blinded held-out expert comparison.','Ten lexical null permutations give minimum plus-one p=1/11, insufficient for a 5% significance claim.','Full multilevel retrieval is not implemented. The separate blind LLM section, when present, supplies claim-evidence judgments of frozen outputs.']}
    llm_path=Path('evaluation_llm/metrics.json')
    if llm_path.exists():
        llm=read(llm_path)
        metrics['blind_llm_evaluation']=llm
        metrics['label_faithfulness']=llm['faithfulness']
    write_json(Path('metrics.json'),metrics)
    print(json.dumps({'exports':exports,'strict_recall':strict['type_A_macro_recall'],'score_count_ratio':strict['mean_score_count_ratio']},indent=2))

if __name__=='__main__': main()
