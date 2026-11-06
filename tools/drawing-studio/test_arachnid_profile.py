import unittest
from arachnid_profile import eligible,adapt
from fit_detected_parts import classify_appendage

class ArachnidProfileTests(unittest.TestCase):
    def test_gate_requires_spider_caption_and_profile(self):
        self.assertTrue(eligible('profile.arachnid','A jumping spider.'))
        self.assertFalse(eligible('profile.arachnid','A scorpion.'))
        self.assertFalse(eligible('profile.quadruped','A spider.'))

    def test_mouth_appendages_not_counted_as_legs(self):
        head=[100,100,50,40,0]
        role,_=classify_appendage([100,140,10,20,0],head,[])
        self.assertEqual(role,'unresolved mouth appendage')
        role,_=classify_appendage([100,140,10,20,0],head,[[90,130,110,155]])
        self.assertEqual(role,'palp candidate')

    def test_adapter_preserves_uncertain_segment_identity(self):
        candidate={'proposed_role':'walking-leg segment candidate','points':[[1,1],[2,1],[2,2]],'measurements':{},'eligible_for_walking_leg_grouping':True}
        result=adapt({'body_parts':[],'appendage_candidates':[candidate]})[0]
        self.assertEqual(result['canonical'],'part.unknown')
        self.assertTrue(result['walking_segment_candidate'])
        self.assertEqual(result['shape']['points'][0],result['shape']['points'][-1])
