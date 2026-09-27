import unittest

import numpy as np

from tkh_abstraction.hypergraph_agglomerative import AgglomerativeState, direct_objective, run_engine
from tkh_abstraction.quotient import coarsen, fragmentation


def graph():
    return {"meta": {},
            "nodes": [{"id": x, "type": "method", "surface_form": x, "year": 2020,
                       "first_seen_year": 2020, "last_seen_year": 2020}
                      for x in ["a", "b", "c", "d", "iso"]],
            "hyperedges": [
                {"id": "e1", "relation_type": "r", "members": ["a", "b", "c"], "year": 2020,
                 "provenance": {"article_year": 2020}},
                {"id": "e2", "relation_type": "r", "members": ["b", "c", "d"], "year": 2020,
                 "provenance": {"article_year": 2020}},
                {"id": "e3", "relation_type": "r", "members": ["a", "d"], "year": 2020,
                 "provenance": {"article_year": 2020}},
            ]}


def embeddings():
    return np.asarray([[0., 0.], [0.1, 0.], [5., 0.], [5.1, 0.], [10., 0.]], dtype=float)


class HypergraphAgglomerativeTests(unittest.TestCase):
    def test_ward_delta_matches_direct_sse(self):
        st = AgglomerativeState(graph(), embeddings(), 0.0)
        before = st.sse[0] + st.sse[1]
        raw = st.semantic_delta_raw(0, 1)
        rows = embeddings()[[0, 1]]
        mean = rows.mean(axis=0)
        after = float(((rows - mean) ** 2).sum())
        self.assertAlmostEqual(raw, after - before)

    def test_structural_delta_matches_quotient_before_after_after_prior_merge(self):
        g = graph(); x = embeddings(); st = AgglomerativeState(g, x, 0.0)
        # Force one earlier merge, then compare a remaining candidate.
        st.merge_once()
        active = sorted(st.active)
        a, b = active[0], active[1]
        part_before = st.partition()
        before = fragmentation(coarsen(g, {k: v for k, v in part_before.items()}))
        # Manual partition after merging a,b.
        after_part = {}
        for cid in active:
            key = f"c{cid}"
            if cid == a:
                after_part[f"cmerge"] = st.members[a] + st.members[b]
            elif cid == b:
                continue
            else:
                after_part[key] = st.members[cid]
        after = fragmentation(coarsen(g, after_part))
        self.assertAlmostEqual(st.structural_delta(a, b), after - before)

    def test_combined_delta_matches_direct_objective_difference(self):
        g = graph(); x = embeddings(); lam = 0.7; st = AgglomerativeState(g, x, lam)
        a, b = 0, 1
        before = direct_objective(g, x, st.partition(), lam, st.total_scatter)[0]
        after_part = st.partition()
        after_part["merged"] = after_part.pop(f"c{a}") + after_part.pop(f"c{b}")
        after = direct_objective(g, x, after_part, lam, st.total_scatter)[0]
        self.assertAlmostEqual(st.combined_delta(a, b)[0], after - before)

    def test_selected_merge_matches_exhaustive_small(self):
        st = AgglomerativeState(graph(), embeddings(), 1.0)
        heap_best = st.pop_best()
        exhaustive = st.best_pair_exhaustive()
        self.assertEqual(heap_best[3:], exhaustive[3:])
        self.assertAlmostEqual(heap_best[0], exhaustive[0])

    def test_lambda_zero_follows_ward_criterion(self):
        st = AgglomerativeState(graph(), embeddings(), 0.0)
        best = st.pop_best()
        all_semantic = []
        for i, a in enumerate(sorted(st.active)):
            for b in sorted(st.active)[i + 1:]:
                all_semantic.append((st.semantic_delta_norm(a, b), a, b))
        self.assertEqual(best[3:], min(all_semantic)[1:])

    def test_outputs_cover_nested_budgets_and_preserve_edges(self):
        result = run_engine(graph(), embeddings(), lam=0.1, budgets=[2, 4])
        self.assertEqual([l["actual_groups"] for l in result["summary"]["levels"]], [2, 4, 5])
        self.assertTrue(all(l["cut_source"] == "saved_active_partition_at_group_count"
                            for l in result["summary"]["levels"]))
        rows = result["hierarchy"]
        for level in [0, 1, 2]:
            seen = [m for r in rows if r["level"] == level for m in r["member_ids"]]
            self.assertEqual(set(seen), {"a", "b", "c", "d", "iso"})
            self.assertEqual(len(seen), 5)
        by_id = {r["id"]: r for r in rows}
        for r in rows:
            if r["parent_id"]:
                self.assertTrue(set(r["member_ids"]).issubset(by_id[r["parent_id"]]["member_ids"]))
        q = result["quotients"]["k2"]
        self.assertEqual(len(q["hyperedges"]), 3)
        self.assertEqual(q["hyperedges"][0]["original_members"], ["a", "b", "c"])
        self.assertEqual(q["hyperedges"][0]["provenance"], {"article_year": 2020})

    def test_saved_cuts_do_not_assume_monotonic_merge_costs(self):
        result = run_engine(graph(), embeddings(), lam=1.0, budgets=[2])
        costs = [m["delta_J"] for m in result["merge_log"]]
        self.assertTrue(any(b < a for a, b in zip(costs, costs[1:])))
        g = graph()
        merges_until_two = [m for m in result["merge_log"] if m["group_count_after"] >= 2]
        clusters = {i: {n["id"]} for i, n in enumerate(g["nodes"])}
        for row in merges_until_two:
            clusters[row["new"]] = clusters.pop(row["left"]) | clusters.pop(row["right"])
        expected = sorted(sorted(v) for v in clusters.values())
        observed = sorted(sorted(r["member_ids"]) for r in result["hierarchy"] if r["level_name"] == "k2")
        self.assertEqual(observed, expected)

    def test_gamma_rejected_by_cli_layer_contract(self):
        # run() validates gamma with file IO; engine exposes only lambda.
        with self.assertRaises(ValueError):
            AgglomerativeState(graph(), embeddings(), -1)


if __name__ == "__main__":
    unittest.main()
