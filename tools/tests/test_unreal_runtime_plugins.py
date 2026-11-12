import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unreal_runtime_plugins import inspect_runtime_plugins

class RuntimePluginsTest(unittest.TestCase):
    def test_enabled_external_plugin_and_missing_wiring(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plugin = root / 'Shared' / 'Example'
            plugin.mkdir(parents=True)
            (plugin / 'Example.uplugin').write_text(json.dumps({'Modules': [{'Type': 'Runtime'}]}))
            game = root / 'Game.uproject'
            game.write_text(json.dumps({'AdditionalPluginDirectories': ['Shared'], 'Plugins': [{'Name': 'Example', 'Enabled': True}]}))
            self.assertEqual(inspect_runtime_plugins(game, ['Example'])['errors'], [])
            game.write_text('{}')
            self.assertEqual(len(inspect_runtime_plugins(game, ['Example'])['errors']), 2)
    def test_editor_only_and_invalid_name(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plugin = root / 'Plugins' / 'Example'
            plugin.mkdir(parents=True)
            descriptor = plugin / 'Example.uplugin'
            descriptor.write_text(json.dumps({'Modules': [{'Type': 'Editor'}]}))
            game = root / 'Game.uproject'
            game.write_text(json.dumps({'Plugins': [{'Name': 'Example', 'Enabled': True}]}))
            self.assertIn('no Runtime module', inspect_runtime_plugins(game, ['Example'])['errors'][0])
            self.assertIn('Invalid runtime plugin name', inspect_runtime_plugins(game, ['../Example'])['errors'][0])
            descriptor.write_text('{broken')
            self.assertIn('Invalid plugin descriptor', inspect_runtime_plugins(game, ['Example'])['errors'][0])
if __name__ == '__main__':
    unittest.main()
