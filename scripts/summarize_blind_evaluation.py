"""Decode independently saved judgments and produce auditable descriptive metrics."""
import json, statistics, random, math, csv
from pathlib import Path

root=Path('evaluation_llm')
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x): Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
key=read(root/'PRIVATE_identity_key.json')
def ratings(kind):
    packets=read(root/f'{kind}_packets.json')['packets']
    rows=read(root/f'{kind}_ratings.json')['ratings']
    assert len(rows)==len(packets) and {r['packet_id'] for r in rows}=={p['packet_id'] for p in packets}
    return [{**r,**key[r['packet_id']]} for r in rows]
def mean_ci(xs):
    rng=random.Random(6911); means=sorted(statistics.mean(rng.choices(xs,k=len(xs))) for _ in range(10000))
    return {'n':len(xs),'mean':statistics.mean(xs),'bootstrap95':[means[249],means[9749]],'interpretation':'Descriptive sampled-group interval conditional on one fixed judge; graph dependence and judge uncertainty not modeled.'}
def wilson(k,n):
    if not n: return None
    z=1.96; p=k/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den; half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0,mid-half),min(1,mid+half)]

coh=ratings('coherence'); coherence={}
for suffix in ('0','0p1'):
    values=[r for r in coh if r['gamma']==suffix]
    actual={r['group_id']:r['rating'] for r in values if r['condition']=='actual'}
    null={r['group_id']:r['rating'] for r in values if r['condition']=='null'}
    assert set(actual)==set(null) and len(actual)==12
    assert all(v in (1,2,3,4) for v in [*actual.values(),*null.values()])
    coherence[suffix]={'actual':mean_ci(list(actual.values())),'null':mean_ci(list(null.values())), 'paired_actual_minus_null':mean_ci([actual[g]-null[g] for g in actual]),'actual_rating_ge3':sum(x>=3 for x in actual.values()),'null_rating_ge3':sum(x>=3 for x in null.values())}

faith=ratings('faithfulness'); categories=['accurate_informative','supported_but_vague','unsupported_or_wrong','insufficient_evidence']
counts={c:sum(r['category']==c for r in faith) for c in categories}; assert sum(counts.values())==32
determinate=32-counts['insufficient_evidence']; wrong=counts['unsupported_or_wrong']
faithfulness={'sample_count':32,'counts':counts,'overclaim_numerator':wrong,'determinate_denominator':determinate,'overclaim_rate':wrong/determinate if determinate else None,'descriptive_wilson95':wilson(wrong,determinate),'all_sample_uncertainty_bounds':[wrong/32,(wrong+counts['insufficient_evidence'])/32],'scope':'Balanced sample of 4 groups per required level and snapshot; descriptive sample-level rate, not a population-weighted estimate or verified external-paper truth.','human_spotcheck_status':'pending'}

ret=ratings('retrieval'); packs={p['packet_id']:p for p in read(root/'retrieval_packets.json')['packets']}; scores=[]
weight={'full':1,'partial':.5,'absent':0,'contradicted':0}
for r in ret:
    p=packs[r['packet_id']]; valid_ids={v['id'] for v in p['returned']}
    cs=r['claim_results']; citations=r['citation_results']
    assert all(c['status'] in weight for c in cs)
    for c in cs+citations+r.get('method_results',[]):
        assert set(c.get('evidence_ids',[]))<=valid_ids
    assert all(c.get('evidence_ids') for c in cs if c['status'] in ('full','partial','contradicted'))
    assert all(c.get('evidence_ids') for c in citations if c['covered'])
    node_types={v['id']:v['type'] for v in p['returned']}
    for method in r.get('method_results',[]):
        if method['direct_node_hit']:
            assert any(node_types[n] in ('method','dataset') for n in method['evidence_ids']), 'Direct method recovery cannot use claim mentions alone'
    if r['type']=='A':
        expected=p['rubric']['expected_methods']
        assert {x['target'] for x in r['method_results']}==set(expected)
        assert {(x['target'],x['index']) for x in cs}=={(m,i) for m,claims in p['rubric']['method_claims'].items() for i in range(len(claims))}
    else:
        assert {x['id'] for x in cs}=={x['id'] for x in p['rubric']['required_claims']}
    assert {x['target'] for x in citations}==set(p['rubric']['required_citations'])
    score={'packet_id':r['packet_id'],'question_id':r['question_id'],'type':r['type'],'mode':r['mode'],'claim_count':len(cs),'claim_full':sum(c['status']=='full' for c in cs),'claim_partial':sum(c['status']=='partial' for c in cs),'claim_coverage':sum(weight[c['status']] for c in cs)/len(cs) if cs else None,'citation_count':len(citations),'citation_coverage':sum(c['covered'] for c in citations)/len(citations) if citations else None}
    if r['type']=='A':
        ms=r['method_results']; score.update({'method_count':len(ms),'direct_method_recall':sum(m['direct_node_hit'] for m in ms)/len(ms),'method_mention_recall':sum(m['mention_hit'] for m in ms)/len(ms)})
    scores.append(score)
summary={}
for typ in ('A','B'):
    summary[typ]={}
    for mode in ('hierarchy','flat'):
        rs=[r for r in scores if r['type']==typ and r['mode']==mode]
        assert len(rs)==(14 if typ=='A' else 4)
        keys=['claim_coverage','citation_coverage']+(['direct_method_recall','method_mention_recall'] if typ=='A' else [])
        summary[typ][mode]={'questions':len(rs),**{k:statistics.mean(r[k] for r in rs if r[k] is not None) for k in keys}}

human=[]
if (root/'human_spotchecks.csv').exists():
    with (root/'human_spotchecks.csv').open(encoding='utf-8-sig',newline='') as handle:
        human=list(csv.DictReader(handle))
completed=[r for r in human if r.get('human_agrees','').strip() or r.get('human_rating','').strip()]
annotated=[r for r in human if any(r.get(k,'').strip() for k in ('human_agrees','human_rating','human_notes'))]
faithfulness['human_spotcheck_status']='qualitative_checks_recorded' if len([r for r in annotated if r['packet_id'].startswith('F')])==4 else ('partial' if any(r['packet_id'].startswith('F') for r in annotated) else 'pending')
metrics={'protocol':'evaluation_llm/PROTOCOL.md','coherence':coherence,'faithfulness':faithfulness,'retrieval_macro':summary,'retrieval_per_question':scores,'human_spotchecks':{'qualitatively_reviewed':len(annotated),'explicit_ratings_or_agreement':len(completed),'requested':6,'records':human},'limitations':['One fresh-context LLM per task; no repeated stochastic judging.','Blindness hides configuration identities, not the observable content of groups.','Matched null is one type/size-preserving randomization per configuration.','Human completion is reported separately; prior developer review is not substituted for new checks.','Post-hoc evidence scoring of frozen coarse-filter retrieval; no generated answers or multilevel routing measured.']}
write(root/'metrics.json',metrics)
write(root/'decoded_ratings.json',{'coherence':coh,'faithfulness':faith,'retrieval':ret})
current=read('metrics.json'); current['blind_llm_evaluation']=metrics; current['label_faithfulness']=faithfulness; write('metrics.json',current)

# Six deterministic human checks, including actual/null and adverse/positive label judgments.
cp={p['packet_id']:p for p in read(root/'coherence_packets.json')['packets']}; fp={p['packet_id']:p for p in read(root/'faithfulness_packets.json')['packets']}
selected=[min([r for r in coh if r['condition']==cond],key=lambda r:(r['rating'],r['packet_id'])) for cond in ['actual','null']]
selected+=sorted(faith,key=lambda r:(categories.index(r['category']),r['packet_id']))[:2]+sorted(faith,key=lambda r:(-categories.index(r['category']),r['packet_id']))[:2]
if not (root/'human_spotchecks.csv').exists():
    with (root/'human_spotchecks.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['packet_id','task','llm_judgment','human_agrees','human_rating','human_notes']); w.writeheader()
        for r in selected: w.writerow({'packet_id':r['packet_id'],'task':'coherence' if r['packet_id'].startswith('C') else 'faithfulness','llm_judgment':r.get('category',r.get('rating'))})
write(root/'human_spotcheck_evidence.json',[{'packet':(cp|fp)[r['packet_id']],'llm_judgment':r} for r in selected])
print(json.dumps(metrics,ensure_ascii=True,indent=2)[:5500])
