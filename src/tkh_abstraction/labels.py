"""Extractive provisional labels/glosses from snapshot-available node text."""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path
from .data_pipeline import load_graph, write_json
STOP=set('the and for with from into using used use based model models method methods data learning graph neural material materials prediction property properties'.split())

def label_run(snapshot:Path, run:Path, output:Path|None=None):
    graph=load_graph(snapshot); node={n['id']:n for n in graph['nodes']}; rows=json.loads((run/'hierarchy.json').read_text(encoding='utf-8'))['supernodes']
    for r in rows:
        texts=[node[m]['surface_form'] for m in r['member_ids'] if m in node]
        toks=[]
        for t in texts:
            toks += [x.lower() for x in re.findall(r"[A-Za-z][A-Za-z0-9+\-]{2,}", t) if x.lower() not in STOP]
        common=[w for w,_ in Counter(toks).most_common(4)]
        examples=[{'id':m,'surface_form':node[m]['surface_form']} for m in r['member_ids'][:5] if m in node]
        r['label']=' / '.join(common) if common else (texts[0][:60] if texts else 'unlabeled group')
        r['label_status']='extractive_provisional_not_validated'
        r['gloss']=f"Extractive summary only: {len(r['member_ids'])} nodes; examples include " + '; '.join(e['surface_form'] for e in examples[:3])
        r['gloss_status']='extractive_fallback_overclaim_not_assessed'
        r['supporting_node_ids']=[e['id'] for e in examples]
        r['supporting_text']=[e['surface_form'] for e in examples]
        r['overclaim_score']=None
    out=output or run/'hierarchy_labeled_extractive.json'; write_json(out,{'supernodes':rows}); return out

def main():
    p=argparse.ArgumentParser(); p.add_argument('--snapshot',type=Path,required=True); p.add_argument('--run',type=Path,required=True); p.add_argument('--output',type=Path)
    a=p.parse_args(); print(label_run(a.snapshot,a.run,a.output))
if __name__=='__main__': main()
