import tempfile, unittest, json
from pathlib import Path
from tkh_abstraction.data_pipeline import write_json
from tkh_abstraction.identity import assign_base, assign_next, validate

class IdentityTests(unittest.TestCase):
 def test_propagation_and_uniqueness(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); base=root/'b'; cur=root/'c'; base.mkdir(); cur.mkdir()
   write_json(base/'hierarchy.json',{'supernodes':[{'id':'p','level_name':'k12','member_ids':['a'],'level':0,'parent_id':None},{'id':'la','level_name':'leaves','member_ids':['a'],'level':1,'parent_id':'p'}]})
   assign_base(base,'B')
   base_rows=json.loads((base/'hierarchy.json').read_text())['supernodes']
   self.assertEqual(next(r for r in base_rows if r['id']=='la')['persistent_id'],'node_a')
   write_json(cur/'hierarchy.json',{'supernodes':[{'id':'c','level_name':'k12','member_ids':['a','b'],'level':0,'parent_id':None},{'id':'la','level_name':'leaves','member_ids':['a'],'level':1,'parent_id':'c'},{'id':'lb','level_name':'leaves','member_ids':['b'],'level':1,'parent_id':'c'}]})
   write_json(cur/'temporal_identity_events.json',{'k12':{'matches':[{'previous_group_id':'p','current_group_id':'c','jaccard':.5}], 'events':[{'event_type':'growth_or_reassignment','previous_group_id':'p','current_group_id':'c','new_node_growth':['b'],'reassigned_existing_nodes':[]}], 'overlap_table':[]}})
   assign_next(base,cur,'C'); validate(cur)
   rows=json.loads((cur/'hierarchy.json').read_text())['supernodes']
   self.assertEqual(next(r for r in rows if r['id']=='la')['persistent_id'],'node_a')
   self.assertEqual([r for r in rows if r['id']=='c'][0]['persistent_id'],'B_k12_0000')
   ev=json.loads((cur/'temporal_identity_events.json').read_text())['k12']['events'][0]
   self.assertEqual(ev['new_node_growth'],['b'])
   self.assertEqual(ev['current_persistent_id'],'B_k12_0000')
if __name__=='__main__': unittest.main()
