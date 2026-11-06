import unittest
import cv2
import numpy as np
from fit_detected_parts import body_fit,classify_appendage


class BodyFitTests(unittest.TestCase):
    def test_palp_separation(self):
        head=[200,150,100,70,0]
        geometry=[175,220,15,25,0]
        role,_=classify_appendage(geometry,head,[[0,0,400,300]])
        self.assertEqual(role,'unresolved mouth appendage')
        role,_=classify_appendage(geometry,head,[[160,195,190,245]])
        self.assertEqual(role,'palp candidate')
        role,_=classify_appendage([50,250,15,25,0],head,[])
        self.assertEqual(role,'walking-leg segment candidate')

    def test_supported_body(self):
        image=np.full((300,400,3),230,np.uint8)
        cv2.ellipse(image,(200,150),(95,65),0,0,360,(80,80,80),-1)
        result=body_fit(image,[100,80,300,220])
        self.assertLess(np.linalg.norm(np.array(result['geometry'][:2])-[200,150]),10)
        self.assertGreater(result['measurements']['geometric_support_score'],.7)

    def test_blank_has_no_support(self):
        result=body_fit(np.full((300,400,3),230,np.uint8),[100,80,300,220])
        self.assertEqual(result['measurements']['geometric_support_score'],0)


if __name__=='__main__':unittest.main()
