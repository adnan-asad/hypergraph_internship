"""Run/resume predefined 10% hyperedge-removal robustness experiments."""
from __future__ import annotations
import argparse,json,time,statistics
from pathlib import Path
from sklearn.metrics import adjusted_rand_score
from .data_pipeline import load_graph, write_json
from .temporal_hypergraph import ensure_embeddings, write_run

def filtered_snapshot(src:Path, removed:set[str], out:Path):
    g=load_graph(src); g['hyperedges']=[e for e in g['hyperedges'] if e['id'] not in removed]; write_json(out,g)

def labels(hpath, level):
    rows=json.loads(hpath.read_text(encoding='utf-8'))['supernodes']; lab={}
    for r in rows:
        if r['level_name']==level:
            for m in r['member_ids']: lab[m]=r['id']
    ids=sorted(lab); return ids,[lab[i] for i in ids]

def ari(base_h, pert_h, level):
    ids,a=labels(base_h,level); lab2={}
    rows=json.loads(pert_h.read_text(encoding='utf-8'))['supernodes']
    for r in rows:
        if r['level_name']==level:
            for m in r['member_ids']: lab2[m]=r['id']
    return float(adjusted_rand_score(a,[lab2[i] for i in ids]))

def run_manifest(manifest_path:Path, snapshot:Path, cache:Path, prev_hierarchy:Path, base_hierarchy:Path, output:Path, gamma:float, lam=.1, revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41'):
    output.mkdir(parents=True, exist_ok=True); man=json.load(open(manifest_path,encoding='utf-8'))[snapshot.stem]
    records=[]
    for row in man['seeds']:
        sd=output/f"seed_{row['seed']}"; summ=sd/'summary.json'
        if not summ.exists():
            if sd.exists() and any(sd.iterdir()):
                # Incomplete pre-checkpoint from an interrupted run; remove only our temp snapshot if present.
                tmp_old = sd / 'snapshot_perturbed.json'
                if tmp_old.exists():
                    tmp_old.unlink()
            tmp=output/f"snapshot_perturbed_seed_{row['seed']}.json"
            filtered_snapshot(snapshot,set(row['removed_edge_ids']),tmp)
            g=load_graph(tmp); emb=ensure_embeddings(snapshot,cache,revision); write_run(g,emb,prev_hierarchy,sd,lam,gamma)
        rec=json.load(open(summ,encoding='utf-8')); vals={lvl:ari(base_hierarchy,sd/'hierarchy.json',lvl) for lvl in ['k12','k48','k120']}; records.append({'seed':row['seed'],'ari_vs_unperturbed':vals,'runtime_seconds':rec['total_runtime_seconds'],'peak_memory_kb':rec['peak_memory_kb']})
    summary={}
    for lvl in ['k12','k48','k120']:
        xs=[r['ari_vs_unperturbed'][lvl] for r in records]; summary[lvl]={'mean':statistics.mean(xs),'stdev':statistics.stdev(xs) if len(xs)>1 else 0,'min':min(xs),'max':max(xs)}
    write_json(output/'robustness_summary.json',{'records':records,'summary':summary,'note':'Perturbation robustness, not cross-snapshot temporal stability.'})

def main():
    p=argparse.ArgumentParser(); p.add_argument('--manifest',type=Path,default=Path('results/evaluation_scaffold/perturbation_manifests.json')); p.add_argument('--snapshot',type=Path,required=True); p.add_argument('--cache',type=Path,required=True); p.add_argument('--prev-hierarchy',type=Path,required=True); p.add_argument('--base-hierarchy',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--gamma',type=float,required=True)
    a=p.parse_args(); run_manifest(a.manifest,a.snapshot,a.cache,a.prev_hierarchy,a.base_hierarchy,a.output,a.gamma)
if __name__=='__main__': main()
