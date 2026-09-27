"""Frozen hierarchy and flat retrieval baselines.

This writes retrieval outputs only. Scoring against benchmark answers must be a
separate step after outputs/configuration are frozen.
"""
from __future__ import annotations
import argparse,json,hashlib,csv
from pathlib import Path
import numpy as np
from .data_pipeline import load_graph, write_json
from .semantic_baseline import load_cache

CANDIDATE_TYPES={'method','claim'}

def cosine(a,b):
    na=np.linalg.norm(a); nb=np.linalg.norm(b)
    return float(np.dot(a,b)/(na*nb)) if na and nb else 0.0

def load_questions(path):
    with path.open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f,delimiter=';'))

def embed_queries(texts, revision):
    from sentence_transformers import SentenceTransformer
    m=SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', revision=revision, device='cpu')
    return m.encode(texts, normalize_embeddings=True, convert_to_numpy=True)

def group_vec(rows,node_index,emb):
    idx=[node_index[m] for m in rows]
    return emb[idx].mean(axis=0)

def run(snapshot, hierarchy, cache, questions, output, revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41', top_groups=4, result_count=20):
    graph=load_graph(snapshot); emb,_=load_cache(cache, graph['nodes']); node={n['id']:n for n in graph['nodes']}; idx={n['id']:i for i,n in enumerate(graph['nodes'])}; qs=load_questions(questions); qv=embed_queries([q['question'] for q in qs], revision)
    rows=json.loads(hierarchy.read_text(encoding='utf-8'))['supernodes']
    lvl0=[r for r in rows if r['level_name']=='k12']; candidates=[n for n in graph['nodes'] if n['type'] in CANDIDATE_TYPES]
    outputs=[]
    for q,vec in zip(qs,qv):
        gr=sorted([(cosine(vec,group_vec(r['member_ids'],idx,emb)),r) for r in lvl0], reverse=True, key=lambda x:x[0])[:top_groups]
        allowed={m for _,r in gr for m in r['member_ids']}
        hc=[n for n in candidates if n['id'] in allowed]
        hres=sorted([(cosine(vec,emb[idx[n['id']]]),n) for n in hc], reverse=True, key=lambda x:x[0])[:result_count]
        fres=sorted([(cosine(vec,emb[idx[n['id']]]),n) for n in candidates], reverse=True, key=lambda x:x[0])[:result_count]
        pack=lambda arr:[{'node_id':n['id'],'type':n['type'],'surface_form':n['surface_form'],'score':s} for s,n in arr]
        outputs.append({'question_id':q['question_id'],'question':q['question'],'hierarchy':{'top_groups':[{'group_id':r['id'],'score':s,'persistent_id':r.get('persistent_id')} for s,r in gr],'results':pack(hres),'retrieval_work':{'groups_scored':len(lvl0),'nodes_scored':len(hc)}},'flat':{'results':pack(fres),'retrieval_work':{'nodes_scored':len(candidates)}},'result_count':result_count})
    write_json(output,{'config':{'candidate_types':sorted(CANDIDATE_TYPES),'query_encoder':'all-MiniLM-L6-v2','revision':revision,'top_groups':top_groups,'result_count':result_count,'snapshot':str(snapshot),'note':'Outputs frozen before benchmark scoring; do not tune after scoring.'},'queries':outputs})

def main():
    p=argparse.ArgumentParser(); p.add_argument('--snapshot',type=Path,required=True); p.add_argument('--hierarchy',type=Path,required=True); p.add_argument('--cache',type=Path,required=True); p.add_argument('--questions',type=Path,default=Path('data/raw/questions.csv')); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); run(a.snapshot,a.hierarchy,a.cache,a.questions,a.output)
if __name__=='__main__': main()
