from copy import deepcopy
import random
import unittest

from tkh_abstraction.quotient import coarsen, fragmentation, merge_groups


def graph():
    return {"meta": {}, "nodes": [
        {"id": x, "type": "method", "surface_form": x, "year": 2020,
         "first_seen_year": 2020, "last_seen_year": 2020}
        for x in ["a", "b", "c", "d", "isolated"]
    ], "hyperedges": [
        {"id": "e1", "relation_type": "extends", "members": ["a", "b", "c", "d"],
         "year": 2020, "provenance": {"article_id": 1, "article_year": 2020},
         "attributes": {"n_targets": 3}},
        {"id": "e2", "relation_type": "extends", "members": ["a", "b", "c", "d"],
         "year": 2020, "provenance": {"article_id": 2, "article_year": 2020}},
        {"id": "e3", "relation_type": "extends", "members": ["a", "c"],
         "year": 2020, "provenance": {"article_id": 1, "article_year": 2020}},
    ]}


class QuotientTests(unittest.TestCase):
    def test_partial_collapse_retains_three_way_edge_and_counts(self):
        q = coarsen(graph(), {"X": ["a", "b"], "Y": ["c"], "Z": ["d"], "I": ["isolated"]})
        e = q["hyperedges"][0]
        self.assertEqual(e["incidence_counts"], {"X": 2, "Y": 1, "Z": 1})
        self.assertEqual(e["coarse_arity"], 3)
        self.assertEqual(e["original_arity"], 4)
        self.assertFalse(e["internal"])

    def test_fully_internal_edge_is_retained(self):
        q = coarsen(graph(), {"X": ["a", "b", "c", "d"], "I": ["isolated"]})
        self.assertEqual(len(q["hyperedges"]), 3)
        self.assertEqual(q["hyperedges"][0]["incidence_counts"], {"X": 4})
        self.assertTrue(all(e["internal"] for e in q["hyperedges"]))
        self.assertEqual(fragmentation(q), 0)

    def test_parallel_edges_and_original_evidence_remain_distinct(self):
        raw = graph()
        q = coarsen(raw, {n["id"]: [n["id"]] for n in raw["nodes"]})
        self.assertEqual(len(q["hyperedges"]), 3)
        for old, new in zip(raw["hyperedges"], q["hyperedges"]):
            for key in set(old) - {"members"}:
                self.assertEqual(old[key], new[key])
            self.assertEqual(new["original_members"], old["members"])

    def test_partition_cannot_overlap(self):
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            coarsen(graph(), {"X": ["a", "b"], "Y": ["b", "c", "d", "isolated"]})

    def test_partition_cannot_omit_isolates_or_add_nodes(self):
        for members in [["a", "b", "c", "d"], ["a", "b", "c", "d", "isolated", "unknown"]]:
            with self.assertRaisesRegex(ValueError, "cover exactly"):
                coarsen(graph(), {"X": members})

    def test_merge_does_not_mutate_input(self):
        raw = graph()
        q = coarsen(raw, {n["id"]: [n["id"]] for n in raw["nodes"]})
        before = deepcopy(q)
        merge_groups(q, "a", "b", "X")
        self.assertEqual(q, before)

    def test_invalid_merge_rejected(self):
        raw = graph()
        q = coarsen(raw, {n["id"]: [n["id"]] for n in raw["nodes"]})
        for a, b, new in [("a", "a", "X"), ("a", "missing", "X"), ("a", "b", "c")]:
            with self.assertRaises(ValueError):
                merge_groups(q, a, b, new)

    def test_contraction_equals_direct_construction_and_original_objective(self):
        # Independent objective oracle reads RAW edges and the current partition.
        # Several contraction orders check conservation beyond one hand example.
        for seed in range(5):
            raw = graph()
            rng = random.Random(seed)
            q = coarsen(raw, {n["id"]: [n["id"]] for n in raw["nodes"]})
            previous_cost = fragmentation(q)
            step = 0
            while len(q["supernodes"]) > 1:
                left, right = rng.sample([n["id"] for n in q["supernodes"]], 2)
                q = merge_groups(q, left, right, f"merge_{step}")
                groups = {n["id"]: n["member_ids"] for n in q["supernodes"]}
                assignment = {v: k for k, vs in groups.items() for v in vs}
                expected = sum((len({assignment[v] for v in e["members"]}) - 1) /
                               (len(e["members"]) - 1) for e in raw["hyperedges"]) / len(raw["hyperedges"])
                self.assertAlmostEqual(fragmentation(q), expected)
                self.assertEqual(q, coarsen(raw, groups))
                self.assertLessEqual(fragmentation(q), previous_cost)
                for e in q["hyperedges"]:
                    self.assertEqual(sum(e["incidence_counts"].values()), e["original_arity"])
                previous_cost = fragmentation(q)
                step += 1

    def test_empty_edge_set(self):
        raw = graph()
        raw["hyperedges"] = []
        self.assertEqual(fragmentation(coarsen(raw, {"all": [n["id"] for n in raw["nodes"]]})), 0)


if __name__ == "__main__":
    unittest.main()
