import unittest
import numpy as np
from tkh_abstraction.temporal_hypergraph import TemporalState, temporal_disagreement, run_temporal


def graph(new=False):
    ids=['a','b','c','d'] + (['e'] if new else [])
    return {'meta':{},'nodes':[{'id':x,'type':'method','surface_form':x,'year':2020,'first_seen_year':2020,'last_seen_year':2020} for x in ids], 'hyperedges':[{'id':'h','relation_type':'r','members':['a','b','c'],'year':2020,'provenance':{'article_year':2020}}]}

def emb(n=4):
    x=np.arange(n*2,dtype=float).reshape(n,2); return x/(np.linalg.norm(x,axis=1,keepdims=True)+1e-9)

class TemporalTests(unittest.TestCase):
    def test_temporal_delta_matches_pairwise_with_new_nodes(self):
        g=graph(new=True); st=TemporalState(g, emb(5), .1); st.gamma=.1
        prev={'p1':['a','b'], 'p2':['c','d']}
        st.set_temporal_reference(prev)
        # merge singleton a and c: cross=1, same=0, shared total=4 denom=6 => +1/6
        self.assertAlmostEqual(st.temporal_delta(0,2), 1/6)
        before=temporal_disagreement(st.partition(), prev)
        part=st.partition(); part['m']=part.pop('c0')+part.pop('c2')
        after=temporal_disagreement(part, prev)
        self.assertAlmostEqual(st.temporal_delta(0,2), after-before)
        # new node e contributes no temporal pairs
        self.assertEqual(st.temporal_delta(0,4), 0)

    def test_stage_transition_rebuild_matches_exhaustive(self):
        g=graph(); x=emb(4); prev_path=None
        st=TemporalState(g,x,.1); st.gamma=.1
        st.set_temporal_reference({'p1':['a','b'], 'p2':['c','d']})
        st.merge_once()
        st.set_temporal_reference({'q1':['a','c'], 'q2':['b','d']})
        heap_best=st.pop_best(); exhaustive=st.best_pair_exhaustive()
        self.assertEqual(heap_best[4:], exhaustive[4:])
        self.assertAlmostEqual(heap_best[0], exhaustive[0])

    def test_gamma_zero_matches_non_temporal_components(self):
        g=graph(); st=TemporalState(g, emb(4), .1); st.gamma=0
        st.set_temporal_reference({'p1':['a','b'], 'p2':['c','d']})
        dj, ds, dh, dt = st.combined_delta(0,1)
        self.assertAlmostEqual(dj, ds + .1*dh)

if __name__=='__main__': unittest.main()
