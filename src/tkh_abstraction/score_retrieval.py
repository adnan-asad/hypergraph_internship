from __future__ import annotations
import argparse,json,re
from pathlib import Path
from .data_pipeline import write_json

def norm(s): return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()
def hit(target, item):
 t=norm(target); x=norm(item)
 return t==x or (len(t)>2 and (t in x or x in t))

def score(retrieval:Path, ground_truth:Path, output:Path):
 ret=json.load(open(retrieval,encoding='utf-8')); gt=json.load(open(ground_truth,encoding='utf-8'))
 rows=[]
 agg={'A':[],'B':[]}
 unresolved=[]
 for q in ret['queries']:
  qid=q['question_id']; rec=gt.get(qid,{}); typ=rec.get('type',q.get('type'))
  for mode in ['hierarchy','flat']:
   items=q[mode]['results']; texts=[i['surface_form'] for i in items]
   if typ=='A':
    targets=rec.get('expected_methods',[]); found=[]; miss=[]
    for t in targets:
     if any(hit(t,x) for x in texts): found.append(t)
     else: miss.append(t); unresolved.append({'question_id':qid,'target':t,'mode':mode})
    recall=len(found)/len(targets) if targets else None
    precision=sum(any(hit(t,x) for t in targets) for x in texts)/len(texts) if texts else 0
    row={'question_id':qid,'type':typ,'mode':mode,'target_count':len(targets),'found_count':len(found),'recall':recall,'precision_proxy':precision,'missing_targets':miss,'retrieval_work':q[mode]['retrieval_work']}
   else:
    targets=[c.get('text','') for c in rec.get('required_claims',[])]
    # surface-form matching is only a weak diagnostic for Type B claims
    found=[t for t in targets if any(hit(t,x) for x in texts)]
    row={'question_id':qid,'type':typ,'mode':mode,'required_claim_count':len(targets),'surface_text_found_count':len(found),'surface_text_recall_proxy':len(found)/len(targets) if targets else None,'warning':'Type B requires claim/evidence judgment; surface matching is not sufficient.','retrieval_work':q[mode]['retrieval_work']}
   rows.append(row)
   if row.get('recall') is not None: agg[typ].append((mode,row['recall']))
 summary={}
 for typ,vals in agg.items():
  for mode in ['hierarchy','flat']:
   xs=[v for m,v in vals if m==mode]
   if xs: summary[f'{typ}_{mode}_mean_recall']=sum(xs)/len(xs)
 write_json(output,{'config':ret['config'],'summary':summary,'question_results':rows,'unresolved_entity_mappings':unresolved,'warning':'Scoring is isolated after retrieval output freeze; Type B surface matching is incomplete.'})

def main():
 p=argparse.ArgumentParser(); p.add_argument('--retrieval',type=Path,required=True); p.add_argument('--ground-truth',type=Path,default=Path('data/raw/ground_truth.json')); p.add_argument('--output',type=Path,required=True)
 a=p.parse_args(); score(a.retrieval,a.ground_truth,a.output)
if __name__=='__main__': main()
