import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'validate_wizards.py'
spec = importlib.util.spec_from_file_location('wizards', SCRIPT)
wizards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wizards)

REPO = SCRIPT.parents[1]
SCHEMA = json.loads((REPO / wizards.SCHEMA_PATH).read_text(encoding='utf-8'))
LOGO = json.loads((REPO / 'workflows/logo-sting-video/wizard.json').read_text(encoding='utf-8'))
IDS = {'logo-sting-video'}


class WizardTemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.template = copy.deepcopy(LOGO)

    def errors(self):
        path = Path(self.temp.name) / 'wizard.json'
        path.write_text(json.dumps(self.template), encoding='utf-8')
        return wizards.validate_template(path, SCHEMA, IDS)

    def assertError(self, fragment):
        errors = self.errors()
        self.assertTrue(any(fragment in e for e in errors), errors)

    def stage(self, sid):
        return next(s for s in self.template['stages'] if s['id'] == sid)

    def test_logo_sting_template_is_valid(self):
        self.assertEqual(self.errors(), [])

    def test_unknown_property_rejected_by_schema(self):
        self.template['stages'][0]['shell'] = 'blender -b'
        self.assertError('unknown property shell')

    def test_flow_category_limited(self):
        self.stage('finish')['flow_category'] = 'sources'
        self.assertError('flow_category')

    def test_unknown_step_field(self):
        self.template['wizard']['steps'][0]['fields'].append('missing_field')
        self.assertError('unknown field missing_field')

    def test_artifact_used_before_produced(self):
        self.template['stages'][0]['inputs']['artifacts'] = ['final_video']
        self.assertError('not produced by an earlier stage')

    def test_artifact_produced_twice(self):
        self.stage('finish')['outputs'].append('scene_frames')
        self.assertError('already produced')

    def test_enum_default_must_be_allowed(self):
        self.template['fields']['speed']['default'] = 2
        self.assertError('speed=2 not in')

    def test_numeric_default_within_bounds(self):
        self.template['fields']['video_crf']['default'] = 99
        self.assertError('video_crf=99 outside')

    def test_preset_unknown_field(self):
        self.template['presets']['arecore-v3-pro-1-5x']['values']['bitrate'] = 5
        self.assertError('unknown field bitrate')

    def test_field_must_appear_in_a_step(self):
        for step in self.template['wizard']['steps']:
            if 'video_crf' in step['fields']:
                step['fields'].remove('video_crf')
        self.assertError('video_crf is not shown in any wizard step')

    def test_stage_must_be_reachable(self):
        for step in self.template['wizard']['steps']:
            step['stages'] = [s for s in step['stages'] if s != 'deliver']
        self.assertError('stage deliver is not reachable')

    def test_ai_required_stage_contradicts_no_ai_claim(self):
        self.stage('soundtrack')['assistance'] = 'required'
        self.assertError('requires AI')

    def test_passed_acceptance_needs_evidence(self):
        self.template['acceptance']['no_ai_run'] = 'passed'
        self.assertError('passed without evidence')

    def test_implemented_needs_verified_stages(self):
        self.template['implementation_status'] = 'implemented'
        self.assertError('requires every stage verified')

    def test_unknown_workflow(self):
        self.template['workflow'] = 'not-a-workflow'
        self.assertError('unknown workflow')


class WizardRepositoryTests(unittest.TestCase):
    def test_repository_wizards_pass(self):
        errors, count = wizards.validate(REPO)
        self.assertEqual(errors, [])
        self.assertGreaterEqual(count, 1)

    def test_index_mismatch_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('shared', 'workflows'):
                shutil.copytree(REPO / name, root / name)
            path = root / 'workflows/logo-sting-video/wizard.json'
            data = json.loads(path.read_text(encoding='utf-8'))
            data['workflow'] = 'phaser-to-godot'
            path.write_text(json.dumps(data), encoding='utf-8')
            errors, _ = wizards.validate(root)
            self.assertTrue(any('does not match index id' in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
