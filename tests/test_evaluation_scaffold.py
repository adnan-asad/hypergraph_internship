import unittest

from tkh_abstraction.evaluation_scaffold import perturbation_manifest, requirement_inventory
from tkh_abstraction.data_pipeline import write_json
from pathlib import Path
import tempfile


class EvaluationScaffoldTests(unittest.TestCase):
    def test_inventory_marks_unsatisfied_evaluation_requirements(self):
        inv = requirement_inventory()
        self.assertEqual(inv["P3_semantic_coherence"]["status"], "not_yet_evaluated_independently")
        self.assertEqual(inv["P6_faithful_labels"]["status"], "not_implemented")
        self.assertEqual(inv["T6_extrinsic_utility"]["status"], "not_started")

    def test_perturbation_manifest_removes_edges_not_nodes(self):
        graph = {"meta": {}, "nodes": [
            {"id": "a", "type": "x", "surface_form": "a", "year": 2020, "first_seen_year": 2020, "last_seen_year": 2020},
            {"id": "b", "type": "x", "surface_form": "b", "year": 2020, "first_seen_year": 2020, "last_seen_year": 2020}],
            "hyperedges": [
                {"id": f"e{i}", "relation_type": "r", "members": ["a", "b"], "year": 2020, "provenance": {"article_year": 2020}}
                for i in range(10)]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snap.json"
            write_json(path, graph)
            manifest = perturbation_manifest(path, [0, 1], removal_fraction=.1)
        self.assertEqual(manifest["node_policy"], "hold all nodes and cached embeddings fixed")
        self.assertEqual([r["removed_edge_count"] for r in manifest["seeds"]], [1, 1])
        self.assertNotEqual(manifest["seeds"][0]["removed_edge_ids"], manifest["seeds"][1]["removed_edge_ids"])


if __name__ == "__main__":
    unittest.main()
