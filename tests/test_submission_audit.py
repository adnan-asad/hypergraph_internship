import unittest
from tkh_abstraction.submission_audit import exact_target_hit

class ExactScoringTests(unittest.TestCase):
    def test_claim_mentions_are_not_method_recovery(self):
        self.assertFalse(exact_target_hit('MACE',[{'type':'claim','surface_form':'MACE'}],{'method'}))

    def test_substring_is_not_exact(self):
        self.assertFalse(exact_target_hit('ACE',[{'type':'method','surface_form':'MACE'}],{'method'}))
        self.assertFalse(exact_target_hit('',[{'type':'method','surface_form':''}],{'method'}))

    def test_normalized_name_and_dataset(self):
        self.assertTrue(exact_target_hit('DeepH-E3',[{'type':'method','surface_form':'DeepH E3'}],{'method'}))
        self.assertTrue(exact_target_hit('Matbench',[{'type':'dataset','surface_form':'Matbench'}],{'method','dataset'}))
