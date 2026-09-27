from __future__ import annotations
import argparse,json,random,statistics
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .data_pipeline import load_graph, write_json

def group_score(X, idxs):
    if len(idxs)<2: return 1.0
    rows=X[idxs]
    centroid=rows.mean(axis=0)
    norm=np.linalg.norm(centroid)
    if norm==0: return 0.0
    sims=(rows@centroid)/(np.linalg.norm(rows,axis=1)*norm+1e-12)
    return float(np.mean(sims))

def eval_partition(graph,hierarchy,level,seeds):
    ids=[n['id'] for n in graph['nodes']]; index={n:i for i,n in enumerate(ids)}
    texts=[n['surface_form'] for n in graph['nodes']]
    X=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),lowercase=True,strip_accents='unicode',norm='l2').fit_transform(texts).toarray()
    rows=[r for r in json.loads(hierarchy.read_text(encoding='utf-8'))['supernodes'] if r['level_name']==level]
    sizes=[len(r['member_ids']) for r in rows]
    def summarize(groups):
        vals=[group_score(X,[index[m] for m in g]) for g in groups]
        return {'group_weighted_mean':float(np.mean(vals)),'node_weighted_mean':float(np.average(vals,weights=[len(g) for g in groups])),'group_scores':vals}
    actual=summarize([r['member_ids'] for r in rows])
    null=[]
    for seed in seeds:
        rng=random.Random(seed); shuffled=ids[:]; rng.shuffle(shuffled); groups=[]; pos=0
        for s in sizes: groups.append(shuffled[pos:pos+s]); pos+=s
        z=summarize(groups); null.append({'seed':seed,'group_weighted_mean':z['group_weighted_mean'],'node_weighted_mean':z['node_weighted_mean']})
    return {'metric':'automated lexical char-ngram TF-IDF centroid cosine proxy independent of MiniLM clustering embeddings; not expert validation','level':level,'actual':{k:actual[k] for k in ['group_weighted_mean','node_weighted_mean']},'null':null,'null_summary':{k:{'mean':statistics.mean([n[k] for n in null]),'stdev':statistics.stdev([n[k] for n in null])} for k in ['group_weighted_mean','node_weighted_mean']}}

def main():
 p=argparse.ArgumentParser(); p.add_argument('--snapshot',type=Path,required=True); p.add_argument('--hierarchy',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--seeds',type=int,nargs='+',default=[0,1,2,3,4,5,6,7,8,9])
 a=p.parse_args(); g=load_graph(a.snapshot); write_json(a.output,{lvl:eval_partition(g,a.hierarchy,lvl,a.seeds) for lvl in ['k12','k48','k120']})
if __name__=='__main__': main()
