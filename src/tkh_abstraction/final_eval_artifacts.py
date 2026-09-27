from __future__ import annotations
import argparse,json,random,math,csv,re,statistics
from pathlib import Path
from collections import defaultdict,Counter
from .data_pipeline import load_graph, write_json
from .coherence_eval import group_score
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def mean_ci(xs):
    m=statistics.mean(xs); sd=statistics.stdev(xs) if len(xs)>1 else 0
    # t_0.975,df4 = 2.776 for n=5
    half=2.776*sd/(len(xs)**0.5) if len(xs)>1 else 0
    return {'mean':m,'stdev':sd,'n':len(xs),'approx_95_ci':[m-half,m+half],'assumption':'t interval over five seed-level ARIs; small n, descriptive only'}

def perturbation_uncertainty(out:Path):
    specs=[('2022','g0','results/perturb_lambda_0p1_gamma_0_2022'),('2022','g01','results/perturb_lambda_0p1_gamma_0p1_2022'),('2024','g0','results/perturb_lambda_0p1_gamma_0_2024'),('2024','g01','results/perturb_lambda_0p1_gamma_0p1_2024')]
    data={}
    for snap,g,path in specs:
        rec=json.load(open(Path(path)/'robustness_summary.json'))['records']
        data[(snap,g)]={r['seed']:r['ari_vs_unperturbed'] for r in rec}
    res={}
    for snap in ['2022','2024']:
        if set(data[(snap,'g0')]) != set(data[(snap,'g01')]) or len(data[(snap,'g0')]) != 5:
            raise ValueError('Paired five-seed intervals require identical five-seed cohorts')
        res[snap]={}
        for lvl in ['k12','k48','k120']:
            g0=[data[(snap,'g0')][s][lvl] for s in sorted(data[(snap,'g0')])]
            g1=[data[(snap,'g01')][s][lvl] for s in sorted(data[(snap,'g01')])]
            diff=[b-a for a,b in zip(g0,g1)]
            res[snap][lvl]={'gamma0':mean_ci(g0),'gamma0p1':mean_ci(g1),'paired_gamma0p1_minus_gamma0':mean_ci(diff),'warning':'Do not infer significance from separate CI overlap; paired differences are descriptive with n=5.'}
    write_json(out,res)

def type_preserving_coherence(snapshot:Path,hierarchy:Path,out:Path,seeds=list(range(10))):
    g=load_graph(snapshot); ids=[n['id'] for n in g['nodes']]; node={n['id']:n for n in g['nodes']}; idx={n['id']:i for i,n in enumerate(g['nodes'])}
    X=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),lowercase=True,strip_accents='unicode',norm='l2').fit_transform([n['surface_form'] for n in g['nodes']]).toarray()
    by_type=defaultdict(list)
    for n in g['nodes']: by_type[n['type']].append(n['id'])
    rows=json.load(open(hierarchy))['supernodes']; result={}
    for lvl in ['k12','k48','k120']:
        groups=[r['member_ids'] for r in rows if r['level_name']==lvl]
        actual=[group_score(X,[idx[m] for m in gr]) for gr in groups]
        null=[]
        specs=[Counter(node[m]['type'] for m in gr) for gr in groups]
        for seed in seeds:
            rng=random.Random(seed); pools={t:vals[:] for t,vals in by_type.items()}
            for vals in pools.values(): rng.shuffle(vals)
            pos={t:0 for t in pools}; ng=[]
            for spec in specs:
                gr=[]
                for t,c in spec.items(): gr += pools[t][pos[t]:pos[t]+c]; pos[t]+=c
                ng.append(gr)
            vals=[group_score(X,[idx[m] for m in gr]) for gr in ng]
            null.append({'seed':seed,'group_weighted_mean':float(np.mean(vals)),'node_weighted_mean':float(np.average(vals,weights=[len(x) for x in ng]))})
        result[lvl]={'metric':'lexical char-ngram TF-IDF centroid cosine; proxy only; type-composition-preserving null','actual':{'group_weighted_mean':float(np.mean(actual)),'node_weighted_mean':float(np.average(actual,weights=[len(x) for x in groups]))},'null':null,'null_summary':{k:{'mean':statistics.mean([z[k] for z in null]),'stdev':statistics.stdev([z[k] for z in null])} for k in ['group_weighted_mean','node_weighted_mean']}}
    write_json(out,result)

def review_samples():
    # blind scientific coherence packets from existing inspection files
    mapping={'A':'results/temporal_lambda_0p1_gamma_0_2024/inspection_k12.json','B':'results/temporal_lambda_0p1_gamma_0p1_2024/inspection_k12.json','C':'results/temporal_lambda_0p1_gamma_0p1_2026_eval/inspection_k12.json'}
    packets={'rubric':{'4':'coherent scientific theme','3':'mostly coherent','2':'mixed/weak','1':'incoherent','blank':'not yet rated'},'method_identities_hidden':True,'packets':[]}
    for aid,path in mapping.items():
        for g in json.load(open(path))[:12]:
            seen=set(); examples=[]
            for key in ['nearest_to_centroid','random_sample','farthest_from_centroid']:
                for m in g[key]:
                    if m['id'] not in seen: seen.add(m['id']); examples.append({'sample_kind':key,'node_id':m['id'],'type':m['type'],'text':m['surface_form']})
            packets['packets'].append({'anonymous_method':aid,'group_id':g['id'],'group_size':g['size'],'examples':examples,'scientific_coherence_rating_blank':'','notes_blank':''})
    write_json(Path('results/blind_scientific_coherence_review.json'),packets)

def label_review():
    specs=[('2020','results/hypergraph_agglomerative_lambda_0p1_2020/hierarchy_labeled_extractive.json'),('2024','results/temporal_lambda_0p1_gamma_0p1_2024/hierarchy_labeled_extractive.json'),('2026','results/temporal_lambda_0p1_gamma_0p1_2026_eval/hierarchy_labeled_extractive.json')]
    out={'rubric':['accurate_informative','supported_but_vague','unsupported_or_wrong','insufficient_evidence'],'aggregation':'overclaim_rate=(unsupported_or_wrong)/(reviewed labels); vague reported separately','items':[]}
    for snap,path in specs:
        rows=json.load(open(path))['supernodes']
        for r in [x for x in rows if x['level_name'] in ('k12','k48')][:20]:
            out['items'].append({'snapshot':snap,'group_id':r['id'],'persistent_id':r.get('persistent_id'),'level_name':r['level_name'],'label':r.get('label'),'gloss':r.get('gloss'),'supporting_node_ids':r.get('supporting_node_ids',[]),'supporting_text':r.get('supporting_text',[]),'rating_blank':'','notes_blank':''})
    write_json(Path('results/label_faithfulness_review_sample.json'),out)

def mapping_and_claim_score():
    ret=json.load(open('results/retrieval_frozen_2026_gamma0p1.json')); gt=json.load(open('data/raw/ground_truth.json'))
    # build graph exact surface map
    graph=load_graph(Path('data/processed/baseline_input/snapshot_2026.json')); surface=defaultdict(list)
    for n in graph['nodes']: surface[n['surface_form'].lower()].append({'id':n['id'],'type':n['type'],'surface_form':n['surface_form']})
    mappings=[]
    for qid,rec in gt.items():
        for t in rec.get('expected_methods',[]):
            hits=surface.get(t.lower(),[]); status='exact' if hits else 'absent_or_alias_needed'
            mappings.append({'question_id':qid,'target':t,'status':status,'graph_nodes':hits,'mapping_decision':'exact surface match only' if hits else 'unresolved; kept in denominator'})
    write_json(Path('results/benchmark_target_mapping_audit.json'),{'note':'Mapping independent of retrieved rank/system identity. Aliases not inferred automatically.', 'mappings':mappings})
    # claim retrieval: claim nodes actually returned
    scores=[]
    for q in ret['queries']:
        rec=gt.get(q['question_id'],{}); typ=rec.get('type')
        for mode in ['hierarchy','flat']:
            returned_claims=[x for x in q[mode]['results'] if x['type']=='claim']
            required=[]
            if typ=='A':
                for claims in rec.get('method_claims',{}).values(): required += claims
            else:
                required=[c.get('text','') for c in rec.get('required_claims',[])]
            found=sum(any(req.lower() in rc['surface_form'].lower() or rc['surface_form'].lower() in req.lower() for rc in returned_claims) for req in required)
            scores.append({'question_id':q['question_id'],'type':typ,'mode':mode,'returned_claim_count':len(returned_claims),'required_claim_count':len(required),'claim_text_hits':found,'claim_recall_text_proxy':found/len(required) if required else None,'limitation':'Counts claims actually returned by frozen retriever; text proxy only.'})
    write_json(Path('results/retrieval_claim_scoring_2026_gamma0p1.json'),{'scores':scores})

def main():
    p=argparse.ArgumentParser(); p.add_argument('--all',action='store_true')
    a=p.parse_args();
    perturbation_uncertainty(Path('results/perturbation_uncertainty.json'))
    type_preserving_coherence(Path('data/processed/baseline_input/snapshot_2024.json'),Path('results/temporal_lambda_0p1_gamma_0p1_2024/hierarchy.json'),Path('results/coherence_type_preserving_null_2024_gamma0p1.json'))
    review_samples(); label_review(); mapping_and_claim_score()
if __name__=='__main__': main()
