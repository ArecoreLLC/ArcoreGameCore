import copy
import unittest
import numpy as np
from PIL import Image
from construction_polish import polish_guides, align_muzzle
from mask_geometry import primitive


class PolishTests(unittest.TestCase):
    def test_torso_arcs_fade_without_changing_geometry(self):
        guides=[{'canonical_part':'part.torso','points':[[0,0],[10,0],[10,10],[0,0]]}, {'canonical_part':'part.leg','points':[[4,-2],[12,-2],[12,3],[4,3],[4,-2]]}]
        before=copy.deepcopy(guides); polish_guides(guides)
        self.assertEqual(guides[0]['segment_opacity'][0],.22)
        self.assertEqual(guides[0]['points'],before[0]['points'])
        self.assertTrue(all(a==1 for a in guides[1]['segment_opacity']))

    def test_no_muzzle_edge_abstains(self):
        mask=np.zeros((60,80),np.uint8); mask[20:40,15:65]=1
        shape=primitive(mask); result,evidence=align_muzzle(Image.new('RGB',(80,60),'white'),mask,shape)
        self.assertFalse(evidence['applied']); self.assertEqual(shape,result)
