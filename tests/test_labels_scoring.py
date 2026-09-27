import tempfile, unittest, json
from pathlib import Path
from tkh_abstraction.data_pipeline import write_json
from tkh_abstraction.labels import label_run
from tkh_abstraction.score_retrieval import score

class LabelScoringTests(unittest.TestCase):
 def test_extractive_labels_keep_support_and_blank_overclaim(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); snap=root/'s.json'; run=root/'r'; run.mkdir()
   write_json(snap,{'meta':{},'nodes':[{'id':'a','type':'method','surface_form':'Alpha Method','year':2020,'first_seen_year':2020,'last_seen_year':2020},{'id':'b','type':'claim','surface_form':'Alpha improves accuracy','year':2020,'first_seen_year':2020,'last_seen_year':2020}], 'hyperedges':[{'id':'e','relation_type':'r','members':['a','b'],'year':2020,'provenance':{'article_year':2020}}]})
   write_json(run/'hierarchy.json',{'supernodes':[{'id':'g','level_name':'k12','member_ids':['a','b']} ]})
   out=label_run(snap,run)
   row=json.load(open(out))['supernodes'][0]
   self.assertEqual(row['overclaim_score'], None)
   self.assertEqual(row['supporting_node_ids'], ['a','b'])
 def test_score_isolated_after_retrieval(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); ret=root/'ret.json'; gt=root/'gt.json'; out=root/'score.json'
   write_json(ret,{'config':{},'queries':[{'question_id':'Q1','question':'q','hierarchy':{'results':[{'surface_form':'MACE','type':'method','node_id':'m','score':1}], 'retrieval_work':{}},'flat':{'results':[{'surface_form':'Other','type':'method','node_id':'o','score':1}], 'retrieval_work':{}}}]})
   write_json(gt,{'Q1':{'type':'A','expected_methods':['MACE'],'method_claims':{}}})
   score(ret,gt,out)
   s=json.load(open(out))['summary']
   self.assertEqual(s['A_hierarchy_mean_recall'],1)
   self.assertEqual(s['A_flat_mean_recall'],0)
if __name__=='__main__': unittest.main()
