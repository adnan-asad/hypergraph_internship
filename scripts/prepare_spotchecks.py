"""Create human checks without manufacturing any human decisions."""
import json,csv
from pathlib import Path
r=Path('evaluation_llm')
def read(name): return json.loads((r/name).read_text(encoding='utf-8'))
key=read('PRIVATE_identity_key.json')
c=read('coherence_ratings.json')['ratings']; f=read('faithfulness_ratings.json')['ratings']
selected=[min([x for x in c if key[x['packet_id']]['condition']==cond],key=lambda x:(x['rating'],x['packet_id'])) for cond in ['actual','null']]
categories=['accurate_informative','supported_but_vague','unsupported_or_wrong','insufficient_evidence']
selected+=sorted(f,key=lambda x:(categories.index(x['category']),x['packet_id']))[:2]+sorted(f,key=lambda x:(-categories.index(x['category']),x['packet_id']))[:2]
packets={p['packet_id']:p for kind in ['coherence','faithfulness'] for p in read(f'{kind}_packets.json')['packets']}
with (r/'human_spotchecks.csv').open('w',encoding='utf-8',newline='') as handle:
    w=csv.DictWriter(handle,fieldnames=['packet_id','task','llm_judgment','human_agrees','human_rating','human_notes']);w.writeheader()
    for x in selected:w.writerow({'packet_id':x['packet_id'],'task':'coherence' if x['packet_id'].startswith('C') else 'faithfulness','llm_judgment':x.get('category',x.get('rating'))})
parts=['# Six manual spot checks','These are pending human checks, not completed ratings. Read the supplied examples; enter your judgment in human_spotchecks.csv. Coherence: 1=incoherent, 2=mixed, 3=mostly coherent, 4=clear specific theme. Faithfulness: accurate_informative / supported_but_vague / unsupported_or_wrong / insufficient_evidence. A quoted example is not a claim about every member. You may disagree with the LLM; explain why.']
for x in selected:
    p=packets[x['packet_id']];parts += [f"## {x['packet_id']}",f"Group size: {p['group_size']}."]
    if 'label' in p: parts += [f"Label: {p['label']}",f"Gloss: {p['gloss']}"]
    parts += ['\n'.join(f"- ({v['type']}) {v['text']}" for v in p.get('members',p.get('evidence_members',[])))]
    if p.get('available_relation_context'): parts += ['Relation context:\n'+json.dumps(p['available_relation_context'],ensure_ascii=False,indent=2)]
    parts += [f"LLM judgment: **{x.get('category',x.get('rating'))}**. {x['rationale']}",'Your agreement/rating/notes: **pending**.']
(r/'human_spotchecks.md').write_text('\n\n'.join(parts)+'\n',encoding='utf-8')
print([x['packet_id'] for x in selected])
