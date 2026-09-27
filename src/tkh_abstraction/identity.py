"""Persistent identity assignment for exported hierarchies."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .data_pipeline import write_json

LEVELS=['k120','k48','k12']

def load_h(path): return json.loads((path/'hierarchy.json').read_text(encoding='utf-8'))['supernodes']
def save_h(path, rows): write_json(path/'hierarchy.json', {'supernodes': rows})

def assign_base(run:Path, prefix:str):
    rows=load_h(run)
    for lvl in LEVELS+['leaves']:
        group=[r for r in rows if r['level_name']==lvl]
        for i,r in enumerate(sorted(group,key=lambda x:x['id'])):
            r['persistent_id']=(f"node_{r['member_ids'][0]}" if lvl=='leaves' else f'{prefix}_{lvl}_{i:04d}')
            r['local_id']=r['id']
    save_h(run, rows)

def assign_next(prev:Path, cur:Path, prefix:str):
    prev_rows=load_h(prev); cur_rows=load_h(cur)
    prev_pid={(r['level_name'],r['id']):r.get('persistent_id',r['id']) for r in prev_rows}
    used={lvl:set() for lvl in LEVELS+['leaves']}
    events_path=cur/'temporal_identity_events.json'
    events=json.loads(events_path.read_text(encoding='utf-8')) if events_path.exists() else {}
    for lvl in LEVELS:
        matches=events.get(lvl,{}).get('matches',[])
        cur_to_prev={m['current_group_id']:m['previous_group_id'] for m in matches}
        counter=0
        for r in sorted([x for x in cur_rows if x['level_name']==lvl], key=lambda x:x['id']):
            r['local_id']=r['id']
            p=cur_to_prev.get(r['id'])
            if p and (lvl,p) in prev_pid:
                pid=prev_pid[(lvl,p)]
            else:
                while True:
                    pid=f'{prefix}_{lvl}_new_{counter:04d}'; counter+=1
                    if pid not in used[lvl]: break
            r['persistent_id']=pid; used[lvl].add(pid)
        for m in matches:
            m['previous_persistent_id']=prev_pid.get((lvl,m['previous_group_id']))
            m['current_persistent_id']=next((r['persistent_id'] for r in cur_rows if r['level_name']==lvl and r['id']==m['current_group_id']),None)
        for e in events.get(lvl,{}).get('events',[]):
            if 'previous_group_id' in e: e['previous_persistent_id']=prev_pid.get((lvl,e['previous_group_id']))
            if 'current_group_id' in e: e['current_persistent_id']=next((r['persistent_id'] for r in cur_rows if r['level_name']==lvl and r['id']==e['current_group_id']),None)
            if 'new_node_growth' not in e: e['new_node_growth']=[]
            if 'reassigned_existing_nodes' not in e: e['reassigned_existing_nodes']=[]
    # leaves are local singleton identities, deterministic by node id
    for r in [x for x in cur_rows if x['level_name']=='leaves']:
        r['local_id']=r['id']; r['persistent_id']=f"node_{r['member_ids'][0]}"
    save_h(cur,cur_rows); write_json(events_path,events)

def validate(run:Path):
    rows=load_h(run)
    for lvl in set(r['level_name'] for r in rows):
        p=[r.get('persistent_id') for r in rows if r['level_name']==lvl]
        if len(p)!=len(set(p)): raise ValueError(f'duplicate persistent_id at {run} {lvl}')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--base',type=Path); p.add_argument('--prefix'); p.add_argument('--prev',type=Path); p.add_argument('--cur',type=Path)
    a=p.parse_args()
    if a.base: assign_base(a.base,a.prefix or 'pid2020'); validate(a.base)
    else: assign_next(a.prev,a.cur,a.prefix or a.cur.name); validate(a.cur)
if __name__=='__main__': main()
