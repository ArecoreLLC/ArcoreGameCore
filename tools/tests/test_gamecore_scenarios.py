"""A donor scenario must not change the donor's default game mode."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gamecore

class ScenarioTests(unittest.TestCase):
    def test_native_override_and_rejected_url_injection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'Config').mkdir()
            (root/'Donor.uproject').write_text('{}')
            manifest=dict(schema_version=1, project_id='scenario', editor_target='DonorEditor',
                          platform='Win64', project_file='Donor.uproject',
                          automation=dict(prefix='Scenario.',required_tests=['Scenario.One']),
                          smoke=dict(map='/Game/Maps/Slice',flag='SliceSmoke',pass_marker='PASS',fail_marker='FAIL'))
            path=root/'Config/GameCore.project.json'
            for mode in [None,'/Script/Donor.SliceMode']:
                if mode: manifest['smoke']['game_mode']=mode
                path.write_text(json.dumps(manifest))
                loaded=gamecore.project_config(root)
                cmd=gamecore.commands(root,loaded,dict(editor=Path('Editor.exe')),root,'smoke')
                self.assertEqual(cmd[2],'/Game/Maps/Slice'+('?game='+mode if mode else ''))
            for mode in ['','/Script/Donor.SliceMode?listen','/Script/Donor.SliceMode -ExecCmds=Quit','/Game/Unreviewed']:
                manifest['smoke']['game_mode']=mode
                path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError,'game_mode'): gamecore.project_config(root)

    def test_module_only_consumer_needs_no_runner_declaration(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'Config').mkdir()
            (root/'Game.uproject').write_text('{}')
            manifest=dict(schema_version=1, project_id='modules-only', editor_target='GameEditor',
                          platform='Win64', project_file='Game.uproject', modules=[])
            (root/'Config/GameCore.project.json').write_text(json.dumps(manifest))
            self.assertEqual(gamecore.project_config(root, runner=False)['project_id'], 'modules-only')
            with self.assertRaises(KeyError): gamecore.project_config(root)
            manifest['smoke']=dict(map='/Engine/Maps/Entry',flag='X',pass_marker='P',fail_marker='F')
            (root/'Config/GameCore.project.json').write_text(json.dumps(manifest))
            # A declared runner block is still validated even for module-only actions.
            with self.assertRaises((KeyError, ValueError)): gamecore.project_config(root, runner=False)
