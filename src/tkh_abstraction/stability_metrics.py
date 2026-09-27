from __future__ import annotations
import argparse,json,random,statistics
from pathlib import Path
from sklearn.metrics import adjusted_rand_score
from .data_pipeline import write_json

def partition(path,level):
 rows=json.loads(path.read_text(encoding='utf-8'))['supernodes']; lab={}
 for r in rows:
  if r['level_name']==level:
   for m in r['member_ids']: lab[m]=r.get('persistent_id',r['id'])
 return lab

def bootstrap(prev,cur,level,reps=1000,seed=0):
 a=partition(prev,level); b=partition(cur,level); shared=sorted(set(a)&set(b))
 if len(shared)<2: return {'ari':0,'ci95':[0,0],'shared_nodes':len(shared)}
 ari=float(adjusted_rand_score([a[i] for i in shared],[b[i] for i in shared])); rng=random.Random(seed); vals=[]
 for _ in range(reps):
  sample=[rng.choice(shared) for _ in shared]
  vals.append(float(adjusted_rand_score([a[i] for i in sample],[b[i] for i in sample])))
 vals.sort(); return {'ari':ari,'ci95':[vals[int(.025*(reps-1))], vals[int(.975*(reps-1))]],'shared_nodes':len(shared),'resampling_unit':'shared node','warning':'Node bootstrap does not model graph dependence or uncertainty across independent corpora.'}

def main():
 p=argparse.ArgumentParser(); p.add_argument('--prev',type=Path,required=True); p.add_argument('--cur',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--reps',type=int,default=1000)
 a=p.parse_args(); write_json(a.output,{lvl:bootstrap(a.prev,a.cur,lvl,a.reps) for lvl in ['k12','k48','k120']})
if __name__=='__main__': main()
