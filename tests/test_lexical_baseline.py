import tempfile
from pathlib import Path
import unittest

from tkh_abstraction.data_pipeline import write_json
from tkh_abstraction.lexical_baseline import build_baseline, run, ward_delta_sse


def snapshot():
    nodes = [
        ("n1", "alpha method"),
        ("n2", "alpha model"),
        ("n3", "beta dataset"),
        ("n4", "beta benchmark"),
        ("n5", "gamma isolated"),
        ("n6", "delta isolated"),
    ]
    return {
        "meta": {"cutoff": 2020, "contains_historical_metadata": True},
        "nodes": [
            {"id": node_id, "type": "method", "surface_form": text,
             "year": 2020, "first_seen_year": 2020, "last_seen_year": 2020}
            for node_id, text in nodes
        ],
        "hyperedges": [
            {"id": "e1", "relation_type": "extends", "members": ["n1", "n2", "n3"],
             "year": 2020, "provenance": {"article_id": 1, "article_year": 2020},
             "attributes": {"source_row": "kept"}},
            {"id": "e2", "relation_type": "claims", "members": ["n3", "n4"],
             "year": 2020, "provenance": {"article_id": 2, "article_year": 2020}},
        ],
    }


class LexicalBaselineTests(unittest.TestCase):
    def test_nested_coverage_and_budget_counts_with_isolates(self):
        result = build_baseline(snapshot(), budgets=[2, 4, 10])
        hierarchy = result["hierarchy"]
        by_level = {}
        for row in hierarchy:
            by_level.setdefault(row["level"], []).append(row)
        self.assertEqual([len(by_level[i]) for i in range(4)], [2, 4, 6, 6])
        expected = {f"n{i}" for i in range(1, 7)}
        for rows in by_level.values():
            seen = [member for row in rows for member in row["member_ids"]]
            self.assertEqual(set(seen), expected)
            self.assertEqual(len(seen), len(expected))
        self.assertTrue(all(row["representative_names_provisional"] for row in hierarchy))
        self.assertTrue(all(row["gloss"] is None for row in hierarchy))
        self.assertIn("feature_metadata", result["summary"])
        self.assertEqual(result["summary"]["feature_metadata"]["zero_vector_count"], 0)

    def test_parent_consistency(self):
        result = build_baseline(snapshot(), budgets=[2, 4, 6])
        by_id = {row["id"]: row for row in result["hierarchy"]}
        for row in result["hierarchy"]:
            if row["level"] == 0:
                self.assertIsNone(row["parent_id"])
            else:
                parent = by_id[row["parent_id"]]
                self.assertLess(parent["level"], row["level"])
                self.assertTrue(set(row["member_ids"]).issubset(parent["member_ids"]))

    def test_quotient_preserves_original_hyperedges_and_provenance(self):
        result = build_baseline(snapshot(), budgets=[2, 4])
        quotient = result["quotients"]["k2"]
        self.assertEqual(len(quotient["hyperedges"]), 2)
        e1 = next(e for e in quotient["hyperedges"] if e["id"] == "e1")
        self.assertEqual(e1["original_members"], ["n1", "n2", "n3"])
        self.assertEqual(e1["original_arity"], 3)
        self.assertEqual(e1["attributes"], {"source_row": "kept"})
        self.assertEqual(e1["provenance"], {"article_id": 1, "article_year": 2020})

    def test_ward_linkage_uses_same_schema_and_budgets(self):
        result = build_baseline(snapshot(), budgets=[2, 4], linkage="ward")
        self.assertEqual(result["summary"]["linkage"], "ward")
        self.assertIn("Euclidean", result["summary"]["distance"])
        self.assertEqual([row["actual_groups"] for row in result["summary"]["levels"]], [2, 4, 6])
        self.assertTrue(all("representative_members" in row for row in result["hierarchy"]))

    def test_ward_delta_matches_direct_sse_increase(self):
        a = [[0.0, 0.0], [2.0, 0.0]]
        b = [[4.0, 0.0], [6.0, 0.0], [8.0, 0.0]]
        def sse(rows):
            import numpy as np
            x = np.asarray(rows, dtype=float)
            mean = x.mean(axis=0)
            return float(((x - mean) ** 2).sum())
        direct = sse(a + b) - sse(a) - sse(b)
        self.assertAlmostEqual(ward_delta_sse(a, b), direct)

    def test_refuses_to_overwrite_nonempty_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "snapshot.json"
            output = root / "out"
            output.mkdir()
            (output / "keep.txt").write_text("user work", encoding="utf-8")
            write_json(input_path, snapshot())
            with self.assertRaisesRegex(ValueError, "not empty"):
                run(input_path, output, budgets=[2])


if __name__ == "__main__":
    unittest.main()
