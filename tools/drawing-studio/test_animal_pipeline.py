import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import animal_pipeline as ap
import production

class AnimalPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'source.txt').write_text('original')
        (self.root/'build.py').write_text("from pathlib import Path\nPath('output.json').write_text('{\"status\":\"passed\"}')\n")
        self.path=self.root/'animal.json'
        self.m={'schema':'gamecore.animal.v1','animal_id':'sample','workspace':str(self.root),'toolchain':{'python':sys.version},'stages':[
            {'id':'art-review','kind':'review','gate':'reference-guides','inputs':['source.txt']},
            {'id':'build','kind':'command','inputs':['source.txt','build.py'],'argv':['{python}','build.py'],'outputs':[{'path':'output.json','kind':'json','expect':{'status':'passed'}}]},
            {'id':'model-review','kind':'review','gate':'companion','inputs':['output.json']},
            {'id':'final-review','kind':'review','gate':'payoff','inputs':['output.json']}]}
        self.save()
    def save(self):self.path.write_text(json.dumps(self.m))
    def approve(self,stage):return ap.review(self.path,stage,'approve','test reviewer','Inspected fixture; test only.')
    def built(self):self.approve('art-review');return ap.resume(self.path)
    def test_stops_at_manual_gate(self):
        self.assertEqual(ap.resume(self.path)['next']['id'],'art-review');self.assertFalse((self.root/'output.json').exists())
    def test_pass_skip_and_finish(self):
        self.built();mtime=(self.root/'output.json').stat().st_mtime_ns
        self.approve('model-review');self.approve('final-review')
        self.assertEqual(ap.resume(self.path)['status'],'complete')
        self.assertEqual(mtime,(self.root/'output.json').stat().st_mtime_ns)
    def test_reference_change_invalidates_reviews(self):
        self.built();self.approve('model-review');self.approve('final-review')
        (self.root/'source.txt').write_text('changed')
        self.assertEqual(ap.inspect(self.path)['next']['id'],'art-review')
        self.assertEqual(ap.inspect(self.path)['stages'][-1]['status'],'blocked_dependency')
    def test_corrupt_output_reruns(self):
        self.built();(self.root/'output.json').write_text('')
        self.assertEqual(ap.inspect(self.path)['next']['status'],'pending')
        self.assertEqual(ap.resume(self.path)['next']['id'],'model-review')
    def test_changed_adapter_reruns(self):
        self.built();(self.root/'build.py').write_text((self.root/'build.py').read_text()+'\n# updated\n')
        self.assertEqual(ap.inspect(self.path)['next']['id'],'build')
    def test_launch_receipt_is_not_completion(self):
        self.approve('art-review');(self.root/'build.py').write_text("from pathlib import Path\nPath('output.json').write_text('{\"status\":\"queued\"}')\n")
        self.assertEqual(ap.resume(self.path)['status'],'failed')
    def test_failed_process_not_cached(self):
        self.approve('art-review');(self.root/'build.py').write_text('raise SystemExit(3)')
        self.assertEqual(ap.resume(self.path)['status'],'failed')
        self.assertEqual(ap.resume(self.path)['status'],'failed')
        self.assertEqual(len(list((self.root/'.gamecore/animals/sample/runs').glob('*'))),2)
    def test_rejection_blocks(self):
        ap.review(self.path,'art-review','reject','artist','Eye placement needs correction')
        self.assertEqual(ap.resume(self.path)['next']['status'],'needs_review')
    def test_cannot_approve_later_gate(self):
        with self.assertRaises(ValueError):self.approve('final-review')
    def test_missing_input(self):
        (self.root/'source.txt').unlink();self.assertEqual(ap.resume(self.path)['status'],'invalid_artifacts')
    def test_live_lock_prevents_second_writer(self):
        state=ap.load(self.path)[3]
        with ap.locked(state):
            with self.assertRaises(ValueError):ap.resume(self.path)
    def test_dead_lock_recovers(self):
        state=ap.load(self.path)[3];ap.write(state/'lock.json',{'pid':99999999})
        with patch.object(ap,'alive',return_value=False):self.assertEqual(ap.resume(self.path)['next']['id'],'art-review')
    def test_missing_gate_rejected(self):
        self.m['stages'].pop();self.save()
        with self.assertRaises(ValueError):ap.load(self.path)
    def test_output_escape_rejected(self):
        self.m['stages'][1]['outputs'][0]['path']='../escape.json';self.save()
        with self.assertRaises(ValueError):ap.load(self.path)
    def test_through_limits_work(self):
        self.built();self.approve('model-review')
        self.assertEqual(ap.resume(self.path,'build')['next']['id'],'final-review')
    def test_mcp_discovery_and_status(self):
        names=[t['name'] for t in production.dispatch('tools/list',{})['tools']]
        self.assertIn('animal_resume',names)
        self.assertTrue(production.dispatch('animal_validate',{'manifest':str(self.path)})['valid'])
        self.assertEqual(production.dispatch('animal_status',{'manifest':str(self.path)})['next']['id'],'art-review')
    def test_later_output_cannot_be_review_input(self):
        self.m['stages'][0]['inputs']=['output.json'];self.save()
        with self.assertRaises(ValueError):ap.load(self.path)
    def test_timeout_does_not_pass(self):
        self.m['stages'][1]['timeout']=1;self.save();self.approve('art-review')
        (self.root/'build.py').write_text('import time;time.sleep(10)')
        self.assertEqual(ap.resume(self.path)['status'],'failed')
    def test_async_resume_reaches_gate(self):
        self.approve('art-review');job=production.dispatch('animal_resume',{'manifest':str(self.path)})
        self.assertEqual(job['status'],'queued')
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            data=json.loads(Path(job['job_file']).read_text())
            if data['status'] in ['finished','failed']:break
            time.sleep(.1)
        self.assertEqual(data['status'],'finished')
        self.assertEqual(data['result']['next']['id'],'model-review')

if __name__=='__main__':unittest.main()
