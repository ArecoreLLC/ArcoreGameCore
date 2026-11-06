import unittest
from PIL import Image,ImageDraw
from advanced import sketch_schedules, schedule_count


class SketchScheduleTests(unittest.TestCase):
    def test_complete_each_parts_lines_and_shading_before_next(self):
        mask=Image.new('L',(640,349),1);ImageDraw.Draw(mask).rectangle((320,0,639,348),fill=2)
        parts=[{'id':'bg','name':'background'},{'id':'left','name':'Left'},{'id':'right','name':'Right'}]
        lines=[{'kind':'pencil','a':[900,10],'b':[910,10],'construction':False},{'kind':'pencil','a':[10,10],'b':[20,10],'construction':False}]
        shade=[{'x':900,'y':20},{'x':10,'y':20}]
        paint=[{'untouched':True}]
        data={'stages':[[],[],lines,shade,paint,paint],'instructions':[{} for _ in range(6)]}
        sketch_schedules(data,parts,mask)
        combined=data['stages'][2]+data['stages'][3]
        self.assertEqual([p['sketch_part_id'] for p in combined],['left','left','right','right'])
        self.assertEqual(combined[0]['kind'],'pencil');self.assertEqual(combined[1]['part_id'],'left')
        self.assertIs(data['stages'][4],paint)
        self.assertEqual(schedule_count(data['sketch_schedules'][0],1)[0],2)
