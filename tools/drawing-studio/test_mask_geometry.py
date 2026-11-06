import unittest
import cv2
import numpy as np
from PIL import Image
from mask_geometry import foreground, primitive, chain_masks, fit_part, measure, remainder_candidates


class MaskGeometryTests(unittest.TestCase):
    def test_padding_and_background_are_excluded(self):
        im=np.full((698,1280,3),248,np.uint8); im[:,290:990]=[220,215,209]
        cv2.ellipse(im,(640,340),(130,160),0,0,360,(90,90,90),-1)
        mask,info=foreground(Image.fromarray(im))
        self.assertTrue(info['usable']); self.assertEqual(mask[340,640],1)
        self.assertEqual(mask[340,100],0); self.assertEqual(mask[340,320],0)

    def test_bent_chain_reduces_spill_and_rotates(self):
        mask=np.zeros((160,160),np.uint8)
        cv2.polylines(mask,[np.array([[30,20],[95,80],[45,140]])],False,1,18)
        for m in (mask,np.rot90(mask).copy()):
            parts=fit_part(m,'leg'); self.assertGreater(len(parts),1)
            old=primitive(m)['metrics']['spill_fraction']
            self.assertLess(np.mean([measure(p['points'],m)['spill_fraction'] for p in parts]),old)
            union=np.maximum.reduce(chain_masks(m)); np.testing.assert_array_equal(union,m)

    def test_empty_mask_and_residual_abstention(self):
        m=np.zeros((100,100),np.uint8)
        self.assertEqual(fit_part(m,'leg'),[])
        self.assertEqual(remainder_candidates(m,m,50),[])

    def test_allowed_primitives_and_torso_multiple_masses(self):
        m=np.zeros((150,250),np.uint8)
        cv2.fillPoly(m,[np.array([[20,30],[220,50],[220,85],[20,120]])],1)
        for label in ('muzzle','foot','head','neck','leg','tail'):
            self.assertTrue(all(p['primitive']=='ellipse' for p in fit_part(m,label)))
        self.assertEqual(fit_part(m,'ear')[0]['primitive'],'triangle')
        self.assertEqual(len(fit_part(m,'body')),2)


if __name__=='__main__':unittest.main()
