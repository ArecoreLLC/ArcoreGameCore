"""Geometric evidence tests, independent of spider-specific authored construction."""
import math
import unittest
import argparse
import json
from pathlib import Path
import tempfile

import cv2
import numpy as np

from shape_geometry import canonical_ellipse,detect_shapes,edge_evidence,ellipse_measure,ellipse_points,fit_trace
from measure_shapes import ROOT,run


class ShapeGeometryTests(unittest.TestCase):
    def test_rotated_ellipse_geometry_is_recovered(self):
        expected=(150,140,65,32,math.radians(29))
        points=ellipse_points(expected,240)
        fitted=canonical_ellipse(points)
        self.assertLess(abs(fitted[0]-expected[0]),.05)
        self.assertLess(abs(fitted[1]-expected[1]),.05)
        self.assertLess(abs(fitted[2]-expected[2]),.05)
        self.assertLess(abs(fitted[3]-expected[3]),.05)
        self.assertLess(abs(fitted[4]-expected[4]),.01)

    def test_exact_trace_needs_real_boundary_evidence(self):
        geometry=(150,150,65,35,math.radians(25));points=ellipse_points(geometry)
        good=np.full((300,300),245,np.uint8)
        cv2.fillPoly(good,[np.round(points).astype(np.int32)],35)
        measured=ellipse_measure(points,geometry,edge_evidence(good))
        blank=ellipse_measure(points,geometry,edge_evidence(np.full_like(good,245)))
        self.assertGreater(measured['geometric_support_score'],.90)
        self.assertLess(measured['rms_fit_error_px'],.01)
        self.assertEqual(blank['boundary_support_fraction'],0)
        self.assertEqual(blank['geometric_support_score'],0)

    def test_occlusion_lowers_support_despite_perfect_ellipse_trace(self):
        geometry=(150,150,60,60,0);points=ellipse_points(geometry)
        full=np.full((300,300),245,np.uint8)
        cv2.fillPoly(full,[np.round(points).astype(np.int32)],35)
        partial=full.copy();partial[:,:165]=245
        a=ellipse_measure(points,geometry,edge_evidence(full))
        b=ellipse_measure(points,geometry,edge_evidence(partial))
        self.assertLess(b['boundary_support_fraction'],a['boundary_support_fraction'])
        self.assertLess(b['geometric_support_score'],a['geometric_support_score']-.20)

    def test_closed_triangle_and_rectangle_are_measured(self):
        for vertices,kind in [([[45,220],[150,35],[250,220]],'triangle'),([[40,70],[245,70],[245,210],[40,210]],'rectangle')]:
            image=np.full((300,300),245,np.uint8)
            cv2.fillPoly(image,[np.array(vertices,np.int32)],35)
            contours,_=cv2.findContours(np.uint8(image<100)*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
            fits=fit_trace(contours[0],edge_evidence(image))
            best=max(fits,key=lambda f:f['measurements']['geometric_support_score'])
            self.assertEqual(best['kind'],kind)
            self.assertGreater(best['measurements']['geometric_support_score'],.9)

    def test_blank_image_has_no_accepted_shapes(self):
        result=detect_shapes(np.full((240,320,3),245,np.uint8))
        self.assertEqual(result['candidates'],[])

    def test_detector_recovers_known_circle_without_duplicate_rings(self):
        image=np.full((300,400,3),245,np.uint8)
        cv2.circle(image,(190,145),48,(35,55,40),-1,lineType=cv2.LINE_AA)
        result=detect_shapes(image,.80)
        candidates=[c for c in result['candidates'] if c['kind']=='circle']
        self.assertEqual(len(candidates),1)
        geometry=candidates[0]['geometry']
        self.assertLess(math.hypot(geometry[0]-190,geometry[1]-145),2)
        self.assertLess(abs(geometry[2]-48),2)
        self.assertIsNone(candidates[0]['semantic_label'])
        self.assertTrue(candidates[0]['review_required'])

    def test_cli_protects_reference_and_exports_reviewable_lesson(self):
        from PIL import Image,ImageDraw
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            root=Path(temp);source=root/'reference.png'
            im=Image.new('RGB',(400,300),(245,245,245));ImageDraw.Draw(im).ellipse((130,80,250,200),fill=(35,55,40));im.save(source)
            args=argparse.Namespace(input=source,output=root/'reference.json',min_score=.8,max_shapes=12,traces=None)
            with self.assertRaises(ValueError):run(args)
            args.output=root/'measured.shapes.json'
            report=run(args)
            self.assertGreater(report['candidate_count'],0)
            self.assertTrue((root/'measured.shapes.png').exists())
            self.assertTrue((root/'measured.shapes.svg').exists())
            lesson=json.loads((root/'measured.shapes-lesson.json').read_text())
            self.assertTrue(lesson['review_required'])
            self.assertEqual(lesson['study'],'custom')
            self.assertTrue(lesson['guides'])
            with Image.open(source) as preserved:
                self.assertEqual(preserved.size,(400,300))


if __name__=='__main__':unittest.main()
