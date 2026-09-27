import unittest

from tkh_abstraction.tuning import paired_family_bootstrap, select_weights, weight_grid


def trial(a=0, b=0, coherence=.7, stability=.5, overclaim=.05, seed=0):
    return dict(split="development", evaluation_ids=["dev_pair_1", "dev_pair_2"],
                protocol_id="test_protocol", seed=seed, coherence=coherence,
                stability=stability, overclaim_rate=overclaim, **{"lambda": a, "gamma": b})


def select(rows):
    return select_weights(rows, min_stability=.4, max_overclaim=.1)


class TuningTests(unittest.TestCase):
    def test_grid_contains_controls(self):
        self.assertEqual(len(weight_grid()), 9)
        self.assertIn((0., 0.), weight_grid())

    def test_selects_quality_not_smallest_penalty_weights(self):
        result = select([trial(), trial(a=1, b=.1, coherence=.8)])
        self.assertEqual(result["selected"]["lambda"], 1)

    def test_rejects_high_coherence_with_overclaims(self):
        result = select([trial(), trial(a=1, coherence=.9, overclaim=.3)])
        self.assertEqual(result["selected"]["lambda"], 0)

    def test_frozen_but_incoherent_candidate_rejected(self):
        result = select([trial(), trial(b=1, coherence=.6, stability=1)])
        self.assertFalse(result["trials"][1]["feasible"])

    def test_no_feasible_config_is_honest_failure(self):
        result = select([trial(stability=.1)])
        self.assertIsNone(result["selected"])

    def test_test_split_cannot_be_selected_on(self):
        t = trial()
        t["split"] = "held_out"
        with self.assertRaises(ValueError): select([t])

    def test_cohorts_must_match(self):
        t = trial(a=1)
        t["evaluation_ids"] = ["different"]
        with self.assertRaises(ValueError): select([trial(), t])

    def test_seeds_must_match(self):
        with self.assertRaises(ValueError): select([trial(), trial(a=1, seed=2)])

    def test_nan_rejected(self):
        with self.assertRaises(ValueError): select([trial(coherence=float("nan"))])

    def test_bootstrap_preserves_family_weighting(self):
        rows = [dict(evaluation_id="a", family_id="f1", split="held_out", baseline=.2, candidate=.6),
                dict(evaluation_id="b", family_id="f1", split="held_out", baseline=.2, candidate=.6),
                dict(evaluation_id="c", family_id="f2", split="held_out", baseline=.6, candidate=.2)]
        result = paired_family_bootstrap(rows, excluded_development_ids=[], repetitions=1000)
        self.assertAlmostEqual(result["mean_difference"], 0)
        self.assertLess(result["approximate_95_percent_interval"][0], 0)
        self.assertGreater(result["approximate_95_percent_interval"][1], 0)

    def test_bootstrap_rejects_dev_overlap(self):
        rows = [dict(evaluation_id="dev_pair_1", family_id="f1", split="held_out", baseline=.2, candidate=.6)]
        with self.assertRaises(ValueError):
            paired_family_bootstrap(rows, excluded_development_ids=["dev_pair_1"])


if __name__ == "__main__":
    unittest.main()
