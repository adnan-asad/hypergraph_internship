"""Deterministic blinded packets; identity key must not be shown to judges."""
import json, random, hashlib, argparse
from pathlib import Path
from collections import defaultdict, Counter
from tkh_abstraction.data_pipeline import load_graph, snapshot, write_json
from tkh_abstraction.submission_audit import RUNS

root=Path('evaluation_llm'); root.mkdir(exist_ok=True)
parser=argparse.ArgumentParser()
parser.add_argument('--graph',type=Path,default=Path('data/raw/tkh_collection10.json'))
parser.add_argument('--ground-truth',type=Path,default=Path('data/raw/ground_truth.json'))
args=parser.parse_args()
g=load_graph(args.graph)
gt=json.loads(args.ground_truth.read_text(encoding='utf-8'))
rng=random.Random(260926)
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def examples(ids,nodes,n=15):
    return [{'type':nodes[m]['type'],'text':nodes[m]['surface_form']} for m in rng.sample(sorted(ids),min(n,len(ids)))]

# Native group/null comparison: all 12 broad groups for both fixed 2024 controls.
s=snapshot(g,2024); nodes={n['id']:n for n in s['nodes']}; pools=defaultdict(list)
for node in s['nodes']: pools[node['type']].append(node['id'])
items=[]
for suffix in ('0','0p1'):
    rows=read(f'results/temporal_lambda_0p1_gamma_{suffix}_2024/hierarchy.json')['supernodes']
    groups=[r for r in rows if r['level_name']=='k12']
    shuffled={t:vals[:] for t,vals in pools.items()}
    for vals in shuffled.values(): rng.shuffle(vals)
    pos=Counter()
    for row in groups:
        null=[]
        for t,c in Counter(nodes[m]['type'] for m in row['member_ids']).items():
            null+=shuffled[t][pos[t]:pos[t]+c]; pos[t]+=c
        for condition,ids in [('actual',row['member_ids']),('null',null)]:
            items.append(({'group_size':len(ids),'members':examples(ids,nodes)}, {'gamma':suffix,'condition':condition,'group_id':row['id']}))
rng.shuffle(items); key={}; packets=[]
for i,(packet,identity) in enumerate(items):
    pid=f'C{i+1:03}'; key[pid]=identity; packets.append({'packet_id':pid,**packet})
write_json(root/'coherence_packets.json',{'sampling':'15 uniform random members without replacement per group; large groups are sampled, not exhaustively judged.','packets':packets})

# Four random groups at each required level in each snapshot, unchanged labels.
items=[]
for year,run in RUNS.items():
    s=snapshot(g,year); nodes={n['id']:n for n in s['nodes']}
    rows=read(f'results/{run}/hierarchy_labeled_extractive.json')['supernodes']
    for level in ('k12','k48'):
        for row in rng.sample([r for r in rows if r['level_name']==level],4):
            # Direct quotation witnesses plus random members. A keyword witness
            # prevents absent-from-sample being mistaken for absent-from-group.
            selected=list(row['supporting_node_ids'])
            selected+=rng.sample(row['member_ids'],min(12,len(row['member_ids'])))
            for term in row['label'].split(' / '):
                witness=next((m for m in row['member_ids'] if term.lower() in nodes[m]['surface_form'].lower()),None)
                if witness: selected.append(witness)
            selected=list(dict.fromkeys(selected))
            membertexts=[{'type':nodes[m]['type'],'text':nodes[m]['surface_form']} for m in selected]
            relations=[]
            selected_set=set(selected)
            for edge in s['hyperedges']:
                if len(selected_set.intersection(edge['members']))>=2:
                    relations.append({'relation':edge['relation_type'],'year':edge['year'],'members':[nodes[m]['surface_form'] for m in edge['members'][:8]],'endpoints_truncated':len(edge['members'])>8})
            items.append(({'cutoff':year,'group_size':len(row['member_ids']),'label':row['label'],'gloss':row['gloss'],'evidence_members':membertexts,'available_relation_context':relations[:4]}, {'year':year,'level':level,'group_id':row['id']}))
rng.shuffle(items); packets=[]
for i,(packet,identity) in enumerate(items):
    pid=f'F{i+1:03}'; key[pid]=identity; packets.append({'packet_id':pid,**packet})
write_json(root/'faithfulness_packets.json',{'scope':'Source-extraction faithfulness, not external-paper truth. Evidence contains quoted examples, random members, keyword witnesses and available relations. No embeddings or clustering scores.','packets':packets})

# Blind hierarchy-vs-flat returned evidence, scoring all questions without tuning.
nodes={n['id']:n for n in g['nodes']}; article_titles=defaultdict(list)
for n in g['nodes']:
    if n['type']=='article':
        for a in n.get('provenance',{}).get('articles',[]): article_titles[a].append(n['surface_form'])
items=[]
for q in read('results/retrieval_frozen_2026_gamma0p1.json')['queries']:
    truth=gt[q['question_id']]
    rubric={k:v for k,v in truth.items() if k in ['type','expected_methods','method_claims','fp_categories','required_citations','sources','required_claims']}
    for mode in ('hierarchy','flat'):
        returned=[]
        for r in q[mode]['results']:
            titles=sorted({t for a in nodes[r['node_id']].get('provenance',{}).get('articles',[]) for t in article_titles[a]})
            returned.append({'id':r['node_id'],'type':r['type'],'text':r['surface_form'],'source_article_titles':titles})
        items.append(({'question_id':q['question_id'],'question':q['question'],'rubric':rubric,'returned':returned},{'question_id':q['question_id'],'mode':mode}))
rng.shuffle(items); packets=[]
for i,(packet,identity) in enumerate(items):
    pid=f'R{i+1:03}'; key[pid]=identity; packets.append({'packet_id':pid,**packet})
write_json(root/'retrieval_packets.json',{'scope':'Frozen returned evidence only. Source titles attached from supplied provenance; no new retrieval or answer generation.','packets':packets})
write_json(root/'PRIVATE_identity_key.json',key)
write_json(root/'packet_manifest.json',{'seed':260926,'packets':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*_packets.json')}})
print({k:len(read(root/f'{k}_packets.json')['packets']) for k in ['coherence','faithfulness','retrieval']})
