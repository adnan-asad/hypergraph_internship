"""Stagewise temporal hypergraph-aware agglomeration.

Development control: delta_J = delta_S_raw/Z_t + lambda*delta_H + gamma*delta_T_r.
The temporal reference changes by stage (120, then 48, then 12), so this is
stagewise greedy optimization, not one fixed global objective.
"""
from __future__ import annotations

import argparse, json, time, hashlib
from .runtime_metrics import peak_memory_kb
from collections import Counter, defaultdict
from pathlib import Path
from math import comb
from sklearn.metrics import adjusted_rand_score

from .data_pipeline import load_graph, write_json
from .hypergraph_agglomerative import AgglomerativeState, direct_objective, _delta_summary
from .lexical_baseline import DEFAULT_BUDGETS, LEAF_LEVEL_NAME, _empty_output_dir, _parent_map, _size_distribution
from .quotient import coarsen, fragmentation
from .semantic_baseline import encode_nodes, inspection_for_run, load_cache, node_signature, resolve_revision, save_cache, MODEL_ID


def hierarchy_partition(path: Path, level_name: str) -> dict[str, list[str]]:
    rows = json.loads(path.read_text(encoding="utf-8"))["supernodes"]
    return {r["id"]: r["member_ids"] for r in rows if r["level_name"] == level_name}


def previous_labels(prev_partition: dict[str, list[str]], shared_ids: set[str]) -> dict[str, str]:
    labels = {}
    for gid, members in prev_partition.items():
        for m in members:
            if m in shared_ids:
                labels[m] = gid
    return labels


def temporal_disagreement(partition: dict[str, list[str]], prev_partition: dict[str, list[str]]) -> float:
    shared = {m for vs in partition.values() for m in vs} & {m for vs in prev_partition.values() for m in vs}
    if len(shared) < 2:
        return 0.0
    cur = {}
    prev = {}
    for gid, vs in partition.items():
        for m in vs:
            if m in shared: cur[m] = gid
    for gid, vs in prev_partition.items():
        for m in vs:
            if m in shared: prev[m] = gid
    ids = sorted(shared); diff = 0
    for i, a in enumerate(ids):
        for b in ids[i+1:]:
            diff += (cur[a] == cur[b]) != (prev[a] == prev[b])
    return diff / comb(len(ids), 2)


def temporal_ari(partition: dict[str, list[str]], prev_partition: dict[str, list[str]]) -> float:
    shared = sorted({m for vs in partition.values() for m in vs} & {m for vs in prev_partition.values() for m in vs})
    if len(shared) < 2:
        return 0.0
    cur_label = {m: gid for gid, vs in partition.items() for m in vs if m in shared}
    prev_label = {m: gid for gid, vs in prev_partition.items() for m in vs if m in shared}
    return float(adjusted_rand_score([prev_label[m] for m in shared], [cur_label[m] for m in shared]))


class TemporalState(AgglomerativeState):
    def __init__(self, graph: dict, embeddings, lam: float, gamma: float = 0.0):
        self.gamma = float(gamma)
        self.temporal_counts = {}
        self.temporal_shared_counts = {}
        self.temporal_denom = 0
        self.temporal_deltas = []
        super().__init__(graph, embeddings, lam)

    def set_temporal_reference(self, prev_partition: dict[str, list[str]]):
        shared_ids = set(self.node_ids) & {m for vs in prev_partition.values() for m in vs}
        self.temporal_shared_total = len(shared_ids)
        self.temporal_denom = comb(len(shared_ids), 2) if len(shared_ids) >= 2 else 0
        labels = previous_labels(prev_partition, shared_ids)
        self.temporal_counts = {}
        self.temporal_shared_counts = {}
        for cid in self.active:
            c = Counter(labels[m] for m in self.members[cid] if m in labels)
            self.temporal_counts[cid] = c
            self.temporal_shared_counts[cid] = sum(c.values())
        self.heap = []
        self._init_heap()

    def temporal_delta(self, a: int, b: int) -> float:
        if getattr(self, "temporal_denom", 0) == 0:
            return 0.0
        ca, cb = self.temporal_counts.get(a, Counter()), self.temporal_counts.get(b, Counter())
        same = sum(v * cb.get(g, 0) for g, v in ca.items())
        cross = self.temporal_shared_counts.get(a, 0) * self.temporal_shared_counts.get(b, 0)
        return (cross - 2 * same) / self.temporal_denom

    def combined_delta(self, a: int, b: int):
        ds = self.semantic_delta_norm(a, b); dh = self.structural_delta(a, b); dt = self.temporal_delta(a, b)
        return ds + self.lam * dh + self.gamma * dt, ds, dh, dt

    def _push(self, a: int, b: int) -> None:
        if a == b or a not in self.active or b not in self.active: return
        if b < a: a, b = b, a
        vals = self.combined_delta(a, b)
        heap = (vals[0], vals[1], vals[2], vals[3], a, b, self.version[a], self.version[b])
        import heapq; heapq.heappush(self.heap, heap)

    def pop_best(self):
        import heapq
        while self.heap:
            dj, ds, dh, dt, a, b, va, vb = heapq.heappop(self.heap)
            if a in self.active and b in self.active and self.version[a] == va and self.version[b] == vb:
                rdj, rds, rdh, rdt = self.combined_delta(a, b)
                return rdj, rds, rdh, rdt, a, b
        raise RuntimeError("No merge candidates remain")

    def merge_once(self):
        dj, ds, dh, dt, a, b = self.pop_best()
        new = self.next_id; self.next_id += 1
        self.children[new] = (a, b); self.distances[new] = dj
        self.size[new] = self.size[a] + self.size[b]; self.sum[new] = self.sum[a] + self.sum[b]
        raw = ds * self.total_scatter if not self.zero_scatter else self.semantic_delta_raw(a, b)
        self.sse[new] = self.sse[a] + self.sse[b] + raw
        self.members[new] = self.members[a] + self.members[b]
        self.incident_edges[new] = self.incident_edges.get(a,set()) | self.incident_edges.get(b,set())
        self.temporal_counts[new] = self.temporal_counts.get(a,Counter()) + self.temporal_counts.get(b,Counter())
        self.temporal_shared_counts[new] = self.temporal_shared_counts.get(a,0) + self.temporal_shared_counts.get(b,0)
        self.active.remove(a); self.active.remove(b); self.active.add(new); self.version[new] = 0
        self.current_sse += raw; self.current_fragmentation += dh
        self.semantic_deltas.append(ds); self.structural_deltas.append(dh)
        if not hasattr(self, 'temporal_deltas'): self.temporal_deltas=[]
        self.temporal_deltas.append(dt)
        row={"new":new,"left":a,"right":b,"delta_J":dj,"delta_S_normalized":ds,"delta_H":dh,"delta_T":dt,"group_count_after":len(self.active)}
        self.merge_log.append(row)
        for old in (a,b): self.version[old]=self.version.get(old,0)+1
        for other in sorted(self.active):
            if other != new: self._push(new, other)
        return row

    def best_pair_exhaustive(self):
        best=None
        ids=sorted(self.active)
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                vals=self.combined_delta(a,b); key=(*vals,a,b)
                if best is None or key < best[0]: best=(key, (*vals,a,b))
        return best[1]


def level_rows(graph, embeddings, state, partition, prev_partition, level_index, level_name, k, lam, gamma):
    groups = {f"L{level_index}_{gid}": members for gid, members in partition.items()}
    q = coarsen(graph, groups)
    J0, nsse, frag = direct_objective(graph, embeddings, groups, lam, state.total_scatter)
    td = temporal_disagreement(groups, prev_partition)
    ari = temporal_ari(groups, prev_partition)
    sizes=[len(v) for v in groups.values()]
    return groups, q, {"level":level_index,"level_name":level_name,"requested_groups":k,"actual_groups":len(groups),"cut_source":"saved_active_partition_at_group_count","normalized_sse":nsse,"fragmentation":frag,"shared_node_temporal_disagreement":td,"shared_node_ari":ari,"combined_objective_with_stage_temporal":nsse + lam*frag + gamma*td,"largest_group_fraction":max(sizes)/len(graph['nodes']),"singleton_count":sum(s==1 for s in sizes),"group_size_distribution":_size_distribution(sizes)}


def run_temporal(graph, embeddings, prev_hierarchy: Path, *, lam: float, gamma: float, budgets=None):
    budgets = list(DEFAULT_BUDGETS if budgets is None else budgets)
    state = TemporalState(graph, embeddings, lam, gamma=gamma)
    saved = {len(graph['nodes']): state.partition()}; prev_parts={f"k{k}": hierarchy_partition(prev_hierarchy, f"k{k}") for k in budgets}
    start=time.perf_counter()
    for target in sorted([min(k,len(graph['nodes'])) for k in budgets], reverse=True):
        lname=f"k{target}"; state.set_temporal_reference(prev_parts[lname])
        while len(state.active) > target: state.merge_once()
        saved[target]=state.partition()
    runtime=time.perf_counter()-start
    specs=[(f"k{min(k,len(graph['nodes']))}", min(k,len(graph['nodes']))) for k in budgets] + [(LEAF_LEVEL_NAME,len(graph['nodes']))]
    hierarchy=[]; quotients={}; summaries=[]; previous=None; node_by_id={n['id']:n for n in graph['nodes']}
    for li,(lname,k) in enumerate(specs):
        part=saved[k]
        parents={gid:None for gid in part} if previous is None else _parent_map(part, previous)
        prev_ref = prev_parts.get(lname, {m:[m] for m in []}) if lname != LEAF_LEVEL_NAME else {m:[m] for m in state.node_ids if m in set().union(*[set(v) for v in prev_parts[f"k{budgets[-1]}"].values()])}
        groups,q,summary=level_rows(graph, embeddings, state, part, prev_ref, li, lname, k, lam, gamma)
        for gid,members in part.items():
            hierarchy.append({"id":f"L{li}_{gid}","level":li,"level_name":lname,"parent_id":f"L{li-1}_{parents[gid]}" if parents[gid] else None,"member_ids":members,"representative_members":[{"id":m,"type":node_by_id[m]['type'],"surface_form":node_by_id[m]['surface_form']} for m in members[:5]],"representative_names_provisional":True,"gloss":None})
        quotients[lname]=q; summaries.append(summary); previous=part
    return {"hierarchy":hierarchy,"quotients":quotients,"merge_log":state.merge_log,"summary":{"baseline":f"temporal_hypergraph_lambda_{lam:g}_gamma_{gamma:g}","lambda":lam,"gamma":gamma,"node_count":len(graph['nodes']),"edge_count":len(graph['hyperedges']),"levels":summaries,"merge_runtime_seconds":runtime,"total_scatter_Z_t":state.total_scatter,"merge_delta_summaries":{"semantic_delta_normalized":_delta_summary(state.semantic_deltas),"structural_delta":_delta_summary(state.structural_deltas),"temporal_delta":_delta_summary(getattr(state,'temporal_deltas',[])),"combined_delta":_delta_summary([m['delta_J'] for m in state.merge_log])},"method":"stagewise greedy: temporal reference is refreshed/rebuilt at 120, 48, and 12 stages"}}


def overlap_and_events(prev_part, cur_part, threshold=0.30, merge_threshold=0.20, split_threshold=0.20):
    prev_sets={k:set(v) for k,v in prev_part.items()}; cur_sets={k:set(v) for k,v in cur_part.items()}; shared=set().union(*prev_sets.values()) & set().union(*cur_sets.values())
    table=[]
    for p,ps in prev_sets.items():
        ps=ps & shared
        for c,cs0 in cur_sets.items():
            cs=cs0 & shared; inter=len(ps & cs)
            if inter:
                table.append({"previous_group_id":p,"current_group_id":c,"intersection_size":inter,"previous_overlap_fraction":inter/len(ps) if ps else 0,"current_overlap_fraction":inter/len(cs) if cs else 0,"jaccard":inter/len(ps|cs) if ps|cs else 0})
    # deterministic one-to-one greedy matching by Jaccard, then ids
    matches=[]; usedp=set(); usedc=set()
    for row in sorted(table, key=lambda r:(-r['jaccard'], r['previous_group_id'], r['current_group_id'])):
        if row['jaccard']>=threshold and row['previous_group_id'] not in usedp and row['current_group_id'] not in usedc:
            matches.append(row); usedp.add(row['previous_group_id']); usedc.add(row['current_group_id'])
    events=[]
    for c,cs in cur_sets.items():
        preds=[r for r in table if r['current_group_id']==c and r['current_overlap_fraction']>=merge_threshold]
        matched=next((m for m in matches if m['current_group_id']==c), None)
        new_nodes=sorted(cs - shared); reassigned=sorted((cs & shared) - (prev_sets.get(matched['previous_group_id'],set()) if matched else set()))
        if not matched: events.append({"event_type":"birth","current_group_id":c,"new_node_growth":new_nodes,"reassigned_existing_nodes":sorted(cs & shared)})
        elif new_nodes or reassigned: events.append({"event_type":"growth_or_reassignment","previous_group_id":matched['previous_group_id'],"current_group_id":c,"new_node_growth":new_nodes,"reassigned_existing_nodes":reassigned})
        if len(preds)>1: events.append({"event_type":"merge","current_group_id":c,"previous_group_ids":[r['previous_group_id'] for r in preds]})
    for p,ps in prev_sets.items():
        succ=[r for r in table if r['previous_group_id']==p and r['previous_overlap_fraction']>=split_threshold]
        if not any(m['previous_group_id']==p for m in matches): events.append({"event_type":"death","previous_group_id":p,"meaning":"retirement of previous group identity"})
        if len(succ)>1: events.append({"event_type":"split","previous_group_id":p,"current_group_ids":[r['current_group_id'] for r in succ]})
    return {"matching_threshold":threshold,"merge_threshold":merge_threshold,"split_threshold":split_threshold,"matches":matches,"overlap_table":table,"events":events}


def ensure_embeddings(snapshot_path: Path, cache_path: Path, revision: str):
    graph=load_graph(snapshot_path)
    if cache_path.exists(): return load_cache(cache_path, graph['nodes'])[0]
    emb, meta=encode_nodes(graph['nodes'], revision=revision); meta['input_sha256']=hashlib.sha256(snapshot_path.read_bytes()).hexdigest(); sig=node_signature(graph['nodes']); save_cache(cache_path,node_ids=sig['node_ids'],text_hashes=sig['text_hashes'],embeddings=emb,metadata=meta); return emb


def write_run(graph, embeddings, prev_hierarchy, output, lam, gamma, previous_output=None):
    _empty_output_dir(output)
    start_mem=peak_memory_kb(); start=time.perf_counter()
    result=run_temporal(graph, embeddings, prev_hierarchy, lam=lam, gamma=gamma)
    result['summary']['total_runtime_seconds']=time.perf_counter()-start
    peak=peak_memory_kb()
    result['summary']['peak_memory_kb']=peak
    result['summary']['peak_memory_delta_kb']=peak-start_mem if peak is not None and start_mem is not None else None
    write_json(output/'hierarchy.json', {"supernodes":result['hierarchy']})
    for lname,q in result['quotients'].items(): write_json(output/f'quotient_{lname}.json', q)
    write_json(output/'summary.json', result['summary']); write_json(output/'merge_log.json', {"merges":result['merge_log']}); write_json(output/'inspection_k12.json', inspection_for_run(output/'hierarchy.json', graph['nodes'], embeddings))
    # identity/events
    identities={}
    for lvl in ['k120','k48','k12']:
        identities[lvl]=overlap_and_events(hierarchy_partition(prev_hierarchy,lvl), hierarchy_partition(output/'hierarchy.json',lvl))
    write_json(output/'temporal_identity_events.json', identities)
    return result['summary']


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--snapshot',type=Path,required=True); p.add_argument('--prev-hierarchy',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--cache',type=Path,required=True); p.add_argument('--lambda',dest='lam',type=float,default=0.1); p.add_argument('--gamma',type=float,required=True); p.add_argument('--revision',default='1110a243fdf4706b3f48f1d95db1a4f5529b4d41')
    a=p.parse_args(); graph=load_graph(a.snapshot); emb=ensure_embeddings(a.snapshot,a.cache,a.revision); summary=write_run(graph,emb,a.prev_hierarchy,a.output,a.lam,a.gamma); print(json.dumps({'output':str(a.output),'runtime_seconds':round(summary['total_runtime_seconds'],3),'peak_memory_kb':summary['peak_memory_kb'],'levels':summary['levels']},indent=2))
if __name__=='__main__': main()
