import unittest
import cv2
import numpy as np
from complete_arcs import complete


class CompletionTests(unittest.TestCase):
    def test_partial_circle(self):
        image=np.full((698,1280,3),230,np.uint8)
        cv2.circle(image,(640,350),160,(90,90,90),-1)
        cv2.rectangle(image,(700,350),(850,530),(230,230,230),-1)
        candidates=complete(image)
        self.assertTrue(any(c['kind']=='circle' and np.linalg.norm(np.array(c['geometry'][:2])-[640,350])<15 and abs(c['geometry'][2]-160)<15 for c in candidates))

    def test_blank(self):
        self.assertEqual(complete(np.full((698,1280,3),230,np.uint8)),[])


if __name__=='__main__':unittest.main()
