from copy import deepcopy
import unittest

from tkh_abstraction.data_pipeline import audit, snapshot, validate


def example():
    return {"meta": {}, "nodes": [
        {"id": "a", "type": "method", "surface_form": "Older method", "year": 1990,
         "first_seen_year": 2020, "last_seen_year": 2024},
        {"id": "b", "type": "dataset", "surface_form": "Later dataset", "year": 2022,
         "first_seen_year": 2022, "last_seen_year": 2022},
    ], "hyperedges": [{"id": "e", "relation_type": "evaluated_on", "members": ["a", "b"],
                        "year": 2020, "provenance": {"article_year": 2024}}]}


class DataTests(unittest.TestCase):
    def test_origin_date_does_not_admit_unseen_node(self):
        self.assertEqual(snapshot(example(), 2019)["nodes"], [])

    def test_future_endpoint_postpones_whole_edge(self):
        graph = example()
        graph["hyperedges"][0]["provenance"]["article_year"] = 2020
        early = snapshot(graph, 2020)
        self.assertEqual([n["id"] for n in early["nodes"]], ["a"])
        self.assertEqual(early["hyperedges"], [])
        self.assertEqual(snapshot(graph, 2022)["hyperedges"][0]["members"], ["a", "b"])

    def test_asserting_paper_gates_edge(self):
        self.assertEqual(snapshot(example(), 2022)["hyperedges"], [])
        self.assertEqual(len(snapshot(example(), 2024)["hyperedges"]), 1)

    def test_future_fact_gates_edge(self):
        graph = example()
        graph["hyperedges"][0]["year"] = 2026
        self.assertEqual(snapshot(graph, 2024)["hyperedges"], [])

    def test_dangling_endpoint_rejected(self):
        graph = example()
        graph["hyperedges"][0]["members"].append("missing")
        with self.assertRaisesRegex(ValueError, "Dangling"):
            validate(graph)

    def test_duplicate_node_rejected(self):
        graph = example()
        graph["nodes"].append(deepcopy(graph["nodes"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate node"):
            validate(graph)

    def test_repeat_endpoint_rejected(self):
        graph = example()
        graph["hyperedges"][0]["members"].append("a")
        with self.assertRaisesRegex(ValueError, "Repeated endpoint"):
            validate(graph)

    def test_snapshot_does_not_mutate_raw(self):
        graph = example()
        before = deepcopy(graph)
        snap = snapshot(graph, 2024)
        snap["hyperedges"][0]["members"].reverse()
        self.assertEqual(graph, before)

    def test_delays_and_isolates_audited(self):
        report = audit(example(), [2020, 2024])
        self.assertEqual(report["snapshots"][0]["isolated_nodes"], ["a"])
        delay = report["snapshots"][0]["delayed_edges"][0]
        self.assertTrue(delay["asserting_paper_after_cutoff"])
        self.assertEqual(delay["future_endpoint_ids"], ["b"])
        self.assertEqual(report["snapshots"][1]["added_edges_since_previous_cutoff"], 1)


if __name__ == "__main__":
    unittest.main()
