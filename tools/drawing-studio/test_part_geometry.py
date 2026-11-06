import unittest
from PIL import Image, ImageDraw
from part_geometry import torso_box, individual_detections, fit_geometry
from advanced import construction_parts


class PartGeometryTests(unittest.TestCase):
    def test_group_eye_box_removed_but_individual_eyes_retained(self):
        boxes=[('eye',[10,10,70,30]),('eye',[12,12,25,28]),('eye',[45,12,65,28])]
        self.assertEqual(individual_detections(boxes),boxes[1:])

    def test_torso_uses_anchors_and_mirrors(self):
        boxes=[('neck',[20,20,40,60]),('tail',[100,30,130,80]),('leg',[30,65,40,120]),('leg',[80,60,90,120])]
        box=torso_box(boxes)
        self.assertEqual(box[0],30)
        self.assertEqual(box[2],100)
        self.assertLess(box[3],70)
        mirrored=[(l,[150-b[2],b[1],150-b[0],b[3]]) for l,b in boxes]
        self.assertEqual(torso_box(mirrored),[150-box[2],box[1],150-box[0],box[3]])
        self.assertIsNone(torso_box(boxes[:1]))

    def test_triangle_is_closed_and_used_for_painting(self):
        im=Image.new('RGB',(100,100),'white')
        ImageDraw.Draw(im).polygon([(50,20),(30,80),(70,80)],outline='black',width=2)
        points,score=fit_geometry(im,[30,20,70,80],True)
        self.assertEqual(points[0],points[-1])
        self.assertGreater(score,.4)
        parts=construction_parts({'guides':[{'type':'contour','closed':True,'stage':1,'points':points,'proposed_role':'ear'}]})
        self.assertEqual(parts[1]['guide_indices'],[0])


if __name__=='__main__': unittest.main()
