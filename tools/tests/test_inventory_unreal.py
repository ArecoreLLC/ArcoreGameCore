"""Regression checks for complete, non-executing external source inventories."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('inventory_unreal', Path(__file__).resolve().parents[1] / 'inventory_unreal.py')
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class UnrealInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'GameCore'
        self.repo.mkdir()
        self.source = self.root / 'EngineFramework'
        (self.source / 'Tools').mkdir(parents=True)
        (self.source / 'Tools/probe.py').write_text('raise RuntimeError("must never execute")\n', encoding='utf-8')
        self.config = {'schema_version': 1, 'reviewed_on': '2026-11-02', 'engine': {'version': '5.8.4'},
                       'framework_version': '0.1.0', 'revision_note': 'snapshot',
                       'extensions': ['.py', '.md'], 'excluded_directories': ['__pycache__'],
                       'sources': [{'id': 'test', 'root': '../EngineFramework', 'ownership': 'test',
                                    'trees': ['Tools'], 'root_files': [], 'documentation_trees': []}]}

    def build(self):
        return inventory.build_inventory(self.repo, self.config)

    def test_inventory_never_executes_project_code(self):
        self.assertEqual(len(self.build()['entries']), 1)

    def test_detects_added_removed_and_modified_scripts(self):
        before = self.build()
        probe = self.source / 'Tools/probe.py'
        probe.write_text('print("modified")', encoding='utf-8')
        (self.source / 'Tools/new.py').write_text('', encoding='utf-8')
        errors = inventory.check_catalog(before, self.build())
        self.assertTrue(any(e.startswith('changed:') for e in errors))
        self.assertTrue(any(e.startswith('uncataloged:') for e in errors))
        probe.unlink()
        self.assertTrue(any(e.startswith('missing:') for e in inventory.check_catalog(before, self.build())))

    def test_missing_declared_tree_cannot_look_like_success(self):
        self.config['sources'][0]['trees'].append('missing')
        with self.assertRaises(ValueError):
            self.build()

    def test_generated_and_binary_files_are_excluded(self):
        cache = self.source / 'Tools/__pycache__'
        cache.mkdir()
        (cache / 'generated.py').write_text('invalid syntax!', encoding='utf-8')
        (self.source / 'Tools/asset.uasset').write_bytes(b'binary')
        self.assertEqual(len(self.build()['entries']), 1)

    def test_path_escape_is_rejected(self):
        self.config['sources'][0]['trees'] = ['../GameCore']
        with self.assertRaises(ValueError):
            self.build()

    def test_declared_root_file_cannot_escape_checkout(self):
        (self.repo / 'outside.py').write_text('', encoding='utf-8')
        self.config['sources'][0]['root_files'] = ['../GameCore/outside.py']
        with self.assertRaises(ValueError):
            self.build()

    def test_declarations_are_captured_without_importing_dependencies(self):
        raw = b'''import nonexistent_engine\nparser.add_argument('--audit')\n@registry.tool_call\ndef native_audit():\n    """Bounded native audit."""\n    pass\nclass Checks:\n    def test_empty_export(self): pass\n'''
        record = inventory.describe('open-world', 'Tools/check.py', raw)
        self.assertIn('nonexistent_engine', record['imports'])
        self.assertEqual(record['declared_arguments'], ['--audit'])
        self.assertEqual(record['declared_tests'], ['test_empty_export'])
        self.assertEqual(record['native_mcp_tools'][0]['name'], 'native_audit')

    def test_hash_baseline_is_deterministic(self):
        self.assertEqual(self.build(), self.build())

    def test_metadata_drift_is_not_ignored(self):
        before = self.build()
        changed = copy.deepcopy(before)
        changed['framework_version'] = '2.0.0'
        self.assertTrue(inventory.check_catalog(before, changed))


if __name__ == '__main__':
    unittest.main()
