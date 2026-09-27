import tempfile
from pathlib import Path
import unittest

import numpy as np

from tkh_abstraction.semantic_baseline import (build_outputs, load_cache, save_cache,
                                               text_hash, validate_embeddings)


def snapshot():
    return {"meta": {"cutoff": 2020},
            "nodes": [
                {"id": "a", "type": "method", "surface_form": "alpha", "year": 2020, "first_seen_year": 2020, "last_seen_year": 2020},
                {"id": "b", "type": "method", "surface_form": "beta", "year": 2020, "first_seen_year": 2020, "last_seen_year": 2020},
                {"id": "c", "type": "dataset", "surface_form": "gamma", "year": 2020, "first_seen_year": 2020, "last_seen_year": 2020},
                {"id": "d", "type": "dataset", "surface_form": "delta", "year": 2020, "first_seen_year": 2020, "last_seen_year": 2020},
            ],
            "hyperedges": [
                {"id": "e", "relation_type": "uses", "members": ["a", "b", "c"], "year": 2020,
                 "provenance": {"article_year": 2020, "article_id": 1}}
            ]}


def embeddings():
    x = np.asarray([[1, 0], [0.9, 0.1], [0, 1], [0.1, 0.9]], dtype=float)
    return x / np.linalg.norm(x, axis=1, keepdims=True)


class SemanticBaselineTests(unittest.TestCase):
    def test_validate_rejects_nonfinite_or_unnormalized(self):
        ids = ["a"]
        hashes = [text_hash("alpha")]
        validate_embeddings(ids, hashes, [[1.0, 0.0]])
        with self.assertRaisesRegex(ValueError, "normalized"):
            validate_embeddings(ids, hashes, [[2.0, 0.0]])
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_embeddings(ids, hashes, [[float("nan"), 0.0]])

    def test_cache_alignment_rejects_text_mismatch(self):
        snap = snapshot()
        ids = [n["id"] for n in snap["nodes"]]
        hashes = [text_hash(n["surface_form"]) for n in snap["nodes"]]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "emb.npz"
            save_cache(path, node_ids=ids, text_hashes=hashes, embeddings=embeddings(), metadata={"ok": True})
            changed = snapshot()
            changed["nodes"][0]["surface_form"] = "changed"
            with self.assertRaisesRegex(ValueError, "does not match"):
                load_cache(path, changed["nodes"])

    def test_hierarchy_and_quotient_invariants(self):
        snap = snapshot()
        result = build_outputs(snap, embeddings(), budgets=[2], embedding_metadata={"dependencies": {}})
        rows = result["hierarchy"]
        self.assertEqual([r["actual_groups"] for r in result["summary"]["levels"]], [2, 4])
        for level in [0, 1]:
            seen = [m for r in rows if r["level"] == level for m in r["member_ids"]]
            self.assertEqual(set(seen), {"a", "b", "c", "d"})
            self.assertEqual(len(seen), 4)
        q = result["quotients"]["k2"]
        self.assertEqual(len(q["hyperedges"]), 1)
        self.assertEqual(q["hyperedges"][0]["original_members"], ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
