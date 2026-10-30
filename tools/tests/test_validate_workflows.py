import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'validate_workflows.py'
spec = importlib.util.spec_from_file_location('validator', SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ScaffoldValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = SCRIPT.parents[1]
        for name in ('2d', '3d', 'shared', 'workflows', 'tools', 'docs', 'porting', 'framework'):
            shutil.copytree(source / name, self.root / name, ignore=shutil.ignore_patterns('__pycache__'))
        for name in ('README.md', 'AGENTS.md'):
            shutil.copy2(source / name, self.root / name)

    def mutate_index(self, change):
        path = self.root / 'workflows/index.json'
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def test_valid_scaffold(self):
        self.assertEqual(validator.validate(self.root), [])

    def test_missing_example(self):
        (self.root / 'workflows/phaser-to-godot/example.md').unlink()
        self.assertTrue(any('missing file' in e for e in validator.validate(self.root)))

    def test_duplicate_id(self):
        self.mutate_index(lambda d: d['workflows'].append(d['workflows'][0]))
        self.assertTrue(any('duplicate' in e for e in validator.validate(self.root)))

    def test_path_escape(self):
        self.mutate_index(lambda d: d['workflows'][0].update(guide='../outside.md'))
        self.assertTrue(any('inside repository' in e for e in validator.validate(self.root)))

    def test_invalid_status(self):
        self.mutate_index(lambda d: d['workflows'][0].update(status='verified'))
        self.assertTrue(any('invalid scaffold status' in e for e in validator.validate(self.root)))

    def test_bad_dimensions(self):
        self.mutate_index(lambda d: d['workflows'][0].update(dimensions=['4d']))
        self.assertTrue(any('dimensions' in e for e in validator.validate(self.root)))

    def test_broken_link(self):
        with (self.root / '2d/README.md').open('a') as f:
            f.write('\n[broken](missing.md)\n')
        self.assertTrue(any('broken local link' in e for e in validator.validate(self.root)))

    def test_missing_workflow(self):
        self.mutate_index(lambda d: d['workflows'].pop())
        self.assertTrue(any('missing required' in e for e in validator.validate(self.root)))

    def test_cli_failure_returns_json_and_nonzero(self):
        (self.root / 'workflows/index.json').write_text('{')
        result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['status'], 'failed')

    def test_malformed_json(self):
        (self.root / 'workflows/index.json').write_text('{')
        self.assertTrue(validator.validate(self.root))


if __name__ == '__main__':
    unittest.main()
