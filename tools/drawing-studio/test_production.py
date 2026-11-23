import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
import production as p

class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        buf=io.BytesIO();Image.new('RGB',(64,35),'white').save(buf,'PNG')
        self.lesson=dict(version=1,name='Geometric test',image='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode(),
            guides=[dict(type='ellipse',stage=0,points=[[400,200],[500,100],[600,200],[500,300],[400,200]]),
                    dict(type='line',stage=1,points=[[450,200],[550,200]])])
        self.path=self.root/'lesson.json';self.write()
    def tearDown(self):self.temp.cleanup()
    def write(self):self.path.write_text(json.dumps(self.lesson),encoding='utf-8')
    def test_discovery_explains_outputs(self):
        names={t['name'] for t in p.dispatch('tools/list',{})['tools']}
        self.assertEqual(names,{'drawing_guide','drawing_import_reference','drawing_validate','drawing_render','drawing_job',
                                'animal_guide','animal_validate','animal_status','animal_resume','animal_review'})
        self.assertIn('No automatic anatomical guide authoring',p.dispatch('drawing_guide',{})['boundaries'])
    def test_validation_requires_both_manual_stages(self):
        self.assertTrue(p.validate(self.path)['valid'])
        self.lesson['guides'].pop();self.write()
        with self.assertRaisesRegex(ValueError,'stage 0.*stage 1'):p.validate(self.path)
    def test_canvas_height(self):
        self.lesson['guides'][0]['points'][0][1]=700;self.write()
        with self.assertRaisesRegex(ValueError,'1280 x 698'):p.validate(self.path)
    def test_bad_schema_and_paths(self):
        with self.assertRaises(ValueError):p.dispatch('drawing_validate',{'lesson':'relative.json'})
        with self.assertRaises(ValueError):p.dispatch('drawing_render',{'lesson':str(self.path),'output_dir':str(self.root),'command':'oops'})
        with self.assertRaises(ValueError):p.dispatch('not_a_tool',{})
    def test_bounds_rejected_before_launch(self):
        for key,value in [('fps',0),('width',True),('duration',999),('force','yes')]:
            with self.assertRaises(ValueError):p.render(dict(lesson=str(self.path),output_dir=str(self.root),**{key:value}))
    def test_job_contract(self):
        path=self.root/'job.json';p.write_json(path,{'status':'passed'})
        with self.assertRaisesRegex(ValueError,'Not a Drawing'):p.read_job(path)
        p.write_json(path,{'schema':'gamecore.drawing-job.v1','status':'passed','outputs':{}})
        self.assertEqual(p.status(path)['status'],'passed')
    def test_personal_art_preserves_source_and_edited_lesson(self):
        source=self.root/'my-art.png';Image.new('RGB',(300,200),(190,92,45)).save(source)
        original=p.digest(source)
        result=p.import_reference(dict(source=str(source),output_dir=str(self.root/'imports')))
        self.assertEqual(p.digest(result['original']),original)
        self.assertEqual(p.digest(source),original)
        self.assertEqual(result['status'],'ready_to_trace')
        lesson=Path(result['lesson']);data=json.loads(lesson.read_text());self.assertEqual(data['guides'],[])
        data['name']='My reviewed draft';lesson.write_text(json.dumps(data))
        p.import_reference(dict(source=str(source),output_dir=str(self.root/'imports')))
        self.assertEqual(json.loads(lesson.read_text())['name'],'My reviewed draft')
        self.assertEqual(result['mapping']['canvas_size'],[1280,698])
        self.assertTrue(p.dispatch('drawing_validate',{'lesson':str(lesson),'mode':'trace'})['valid'])
        with self.assertRaisesRegex(ValueError,'stage 0'):p.validate(lesson)

if __name__=='__main__':unittest.main()
