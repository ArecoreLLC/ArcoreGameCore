"""Regression coverage for dependency admission and trustworthy runner outcomes."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gamecore as runner
import gamecore_modules as modules


class ModuleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'framework'
        self.project = Path(self.temp.name) / 'game'
        (self.root / 'shared').mkdir(parents=True)
        (self.root / 'rule.h').write_text('// original\n')
        (self.root / 'guide.md').write_text('Guide')
        self.entry = dict(id='rule', version='0.1.0', source='rule.h',
                          sha256=modules.digest(self.root / 'rule.h'), documentation='guide.md',
                          dependencies=[], tests=[])
        self.save_registry()
        self.manifest = dict(project_id='sample', modules=[dict(id='rule', version='0.1.0', destination='Source/Rule.h')])

    def save_registry(self):
        modules.write_json(self.root / 'shared/modules.json', dict(schema_version=1, modules=[self.entry]))

    def install(self, update=False):
        return modules.sync(self.project, self.manifest, update, self.root)

    def test_install_and_offline_check(self):
        self.install()
        (self.root / 'rule.h').unlink()
        modules.check_lock(self.project, self.manifest)

    def test_modified_local_header_not_overwritten_even_with_update(self):
        self.install()
        target = self.project / 'Source/Rule.h'
        target.write_text('// local work')
        with self.assertRaisesRegex(ValueError, 'Modified installed'):
            self.install(True)
        self.assertEqual(target.read_text(), '// local work')

    def test_registry_drift_rejected_before_writes(self):
        (self.root / 'rule.h').write_text('// changed')
        with self.assertRaisesRegex(ValueError, 'Registry source drift'):
            self.install()
        self.assertFalse((self.project / 'Source/Rule.h').exists())

    def test_unselected_source_drift_does_not_block_admission(self):
        other = dict(self.entry, id='other', source='unrelated.h')
        modules.write_json(self.root / 'shared/modules.json', dict(schema_version=1, modules=[self.entry, other]))
        self.install()
        modules.check_lock(self.project, self.manifest)
        # Full registry auditing still detects the unrelated missing source.
        with self.assertRaises(OSError):
            modules.registry(self.root)

    def test_version_change_requires_explicit_update(self):
        self.install()
        self.entry['version'] = '0.2.0'
        (self.root / 'rule.h').write_text('// reviewed v2')
        self.entry['sha256'] = modules.digest(self.root / 'rule.h')
        self.save_registry()
        self.manifest['modules'][0]['version'] = '0.2.0'
        with self.assertRaisesRegex(ValueError, 'explicit'):
            self.install()
        self.install(True)
        modules.check_lock(self.project, self.manifest)

    def test_unmanaged_file_preserved(self):
        target = self.project / 'Source/Rule.h'
        target.parent.mkdir(parents=True)
        target.write_text('private work')
        with self.assertRaisesRegex(ValueError, 'Unmanaged'):
            self.install()

    def test_same_version_cannot_change_bytes(self):
        self.install()
        (self.root / 'rule.h').write_text('// changed without release')
        self.entry['sha256'] = modules.digest(self.root / 'rule.h')
        self.save_registry()
        with self.assertRaisesRegex(ValueError, 'version bump'):
            self.install(True)

    def test_path_escape(self):
        for value in ('../outside.h', 'Source/../../outside.h', 'C:/outside.h'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                modules.contained(self.project, value)

    def test_duplicate_destination(self):
        self.manifest['modules'].append(dict(id='other', version='0.1.0', destination='Source/Rule.h'))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.install()

    def test_cycle_rejected(self):
        self.entry['dependencies'] = ['rule']
        self.save_registry()
        with self.assertRaisesRegex(ValueError, 'cycle'):
            self.install()

    def test_manifest_lock_mismatch(self):
        self.install()
        self.manifest['modules'][0]['version'] = '0.2.0'
        with self.assertRaisesRegex(ValueError, 'selection changed'):
            modules.check_lock(self.project, self.manifest)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        (self.output / 'report').mkdir()
        self.manifest = dict(automation=dict(prefix='Pilot.', required_tests=['Pilot.One', 'Pilot.Two']),
                             smoke=dict(pass_marker='PILOT PASS', fail_marker='PILOT FAIL'))

    def report(self, names, state='Success'):
        modules.write_json(self.output / 'report/index.json', dict(tests=[dict(fullTestPath=n, state=state, errors=0) for n in names]))

    def test_missing_required_test_rejected(self):
        self.report(['Pilot.One'])
        with self.assertRaisesRegex(ValueError, 'Required automation'):
            runner.verify_result(self.manifest, self.output, 'automation')

    def test_failed_and_empty_automation_rejected(self):
        for names, state in [([], 'Success'), (['Pilot.One', 'Pilot.Two'], 'Fail')]:
            self.report(names, state)
            with self.assertRaises(ValueError):
                runner.verify_result(self.manifest, self.output, 'automation')

    def test_named_tests_pass(self):
        self.report(['Pilot.One', 'Pilot.Two'])
        self.assertEqual(runner.verify_result(self.manifest, self.output, 'automation')['count'], 2)

    def test_smoke_requires_pass_without_fail(self):
        for text in ('startup only', 'PILOT PASS\nPILOT FAIL'):
            (self.output / 'engine.log').write_text(text)
            with self.assertRaises(ValueError):
                runner.verify_result(self.manifest, self.output, 'smoke')
        (self.output / 'engine.log').write_text('PILOT PASS')
        runner.verify_result(self.manifest, self.output, 'smoke')

    def test_failure_retains_receipt_and_fresh_run_directory(self):
        project = self.output / 'game'
        project.mkdir()
        manifest = dict(project_id='pilot', engine_version='5.8.4')
        with patch.object(runner, 'check_lock'), patch.object(runner, 'engine_tools', return_value=({}, {})), \
             patch.object(runner, 'commands', return_value=['fake']), patch.object(runner, 'execute', return_value=7):
            for _ in range(2):
                with self.assertRaisesRegex(ValueError, 'exit code 7'):
                    runner.run(project, manifest, self.output, 'build', 5)
        receipts = list(project.glob('Saved/GameCore/*/receipt.json'))
        self.assertEqual(len(receipts), 2)
        self.assertTrue(all(modules.read_json(p)['status'] == 'failed' for p in receipts))


if __name__ == '__main__':
    unittest.main()
