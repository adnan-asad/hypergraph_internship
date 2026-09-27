import tempfile
from pathlib import Path
import unittest

from tkh_abstraction.data_pipeline import write_json
from tkh_abstraction.navigation import (collapse, expand, export_cuts, export_frontier,
                                        init_frontier, list_frontier, replay_partitions)


def graph(n=5):
    return {"meta": {}, "nodes": [
        {"id": str(i), "type": "method", "surface_form": f"node {i}", "year": 2020,
         "first_seen_year": 2020, "last_seen_year": 2020} for i in range(n)],
        "hyperedges": [{"id": "e", "relation_type": "r", "members": ["0", "1", "2"],
                        "year": 2020, "provenance": {"article_year": 2020},
                        "attributes": {"kept": True}}]}


def merges():
    return {"merges": [
        {"left": 0, "right": 1, "new": 5},
        {"left": 2, "right": 3, "new": 6},
        {"left": 5, "right": 6, "new": 7},
    ]}


class NavigationTests(unittest.TestCase):
    def test_chronological_cut_reconstruction_and_missing(self):
        parts = replay_partitions(graph(), merges()["merges"], {4, 3, 2})
        self.assertEqual(len(parts[4]), 4)
        self.assertEqual(len(parts[3]), 3)
        self.assertEqual(len(parts[2]), 2)
        with self.assertRaisesRegex(ValueError, "does not reach"):
            replay_partitions(graph(), merges()["merges"], {1})

    def test_expand_collapse_roundtrip_and_invalids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); run = root / "run"; run.mkdir(); snap = root / "snap.json"; state = root / "state.json"
            write_json(snap, graph()); write_json(run / "merge_log.json", merges())
            write_json(state, {"snapshot": str(snap), "run": str(run), "frontier": [4, 7]})
            before = list_frontier(state)
            expand(state, 7)
            self.assertEqual(list_frontier(state)["frontier_size"], 3)
            with self.assertRaisesRegex(ValueError, "leaf"):
                expand(state, 4)
            with self.assertRaisesRegex(ValueError, "not siblings"):
                collapse(state, 4, 5)
            collapse(state, 5, 6)
            self.assertEqual(list_frontier(state), before)

    def test_export_frontier_preserves_hyperedges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); run = root / "run"; run.mkdir(); snap = root / "snap.json"; state = root / "state.json"; out = root / "out"
            write_json(snap, graph()); write_json(run / "merge_log.json", merges())
            write_json(state, {"snapshot": str(snap), "run": str(run), "frontier": [4, 7]})
            export_frontier(state, out)
            import json
            q = json.loads((out / "quotient_frontier.json").read_text())
            self.assertEqual(q["hyperedges"][0]["original_members"], ["0", "1", "2"])
            self.assertEqual(q["hyperedges"][0]["attributes"], {"kept": True})


if __name__ == "__main__":
    unittest.main()
