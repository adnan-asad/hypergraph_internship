import unittest
from tkh_abstraction.extends_direction import infer_extends_direction


def nodes(years):
    d = {}
    for node_id, year in years.items():
        d[node_id] = {"id": node_id, "type": "method", "surface_form": node_id,
                      "origin_year": year, "first_seen_year": 2020, "year": year or 2020,
                      "last_seen_year": 2020}
    d["task"] = {"id": "task", "type": "task", "surface_form": "context", "origin_year": None,
                 "first_seen_year": 2020, "year": 2020, "last_seen_year": 2020}
    return d


def edge(members, year=2020):
    return {"id": "e", "relation_type": "extends", "members": members, "year": year,
            "provenance": {"article_year": year}}


class ExtendsDirectionTests(unittest.TestCase):
    def test_unique_date_match(self):
        r = infer_extends_direction(edge(["a", "b"], 2020), nodes({"a": 2020, "b": 2019}))
        self.assertEqual(r["status"], "resolved")
        self.assertEqual(r["inferred_source_method"], "a")
        self.assertEqual(r["rule_applied"], "unique_method_origin_equals_edge_year")

    def test_unique_newest_candidate(self):
        r = infer_extends_direction(edge(["a", "b"], 2020), nodes({"a": 2018, "b": 2019}))
        self.assertEqual(r["status"], "resolved")
        self.assertEqual(r["inferred_source_method"], "b")
        self.assertEqual(r["rule_applied"], "unique_newest_known_method_temporally_compatible")

    def test_tied_dates_unresolved(self):
        r = infer_extends_direction(edge(["a", "b"], 2020), nodes({"a": 2020, "b": 2020}))
        self.assertEqual(r["status"], "unresolved")
        self.assertIn("tie", r["uncertainty_reason"])

    def test_missing_dates_unresolved(self):
        r = infer_extends_direction(edge(["a", "b"], 2020), nodes({"a": 2020, "b": None}))
        self.assertEqual(r["status"], "unresolved")
        self.assertIn("missing", r["uncertainty_reason"])

    def test_future_dates_unresolved(self):
        r = infer_extends_direction(edge(["a", "b"], 2020), nodes({"a": 2020, "b": 2021}))
        self.assertEqual(r["status"], "unresolved")
        self.assertIn("future", r["uncertainty_reason"])

    def test_permutation_invariance(self):
        n = nodes({"a": 2018, "b": 2019, "c": 2017})
        r1 = infer_extends_direction(edge(["a", "b", "c"], 2020), n)
        r2 = infer_extends_direction(edge(["c", "a", "b"], 2020), n)
        self.assertEqual(r1["inferred_source_method"], r2["inferred_source_method"])
        self.assertEqual(r1["inferred_source_method"], "b")

    def test_preserves_original_members_and_context(self):
        r = infer_extends_direction(edge(["task", "a", "b"], 2020), nodes({"a": 2020, "b": 2019}))
        self.assertEqual(r["original_members"], ["task", "a", "b"])
        self.assertEqual(r["non_method_context"][0]["id"], "task")
        self.assertEqual(r["candidate_target_methods"], ["b"])


if __name__ == "__main__":
    unittest.main()
