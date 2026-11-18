"""Acceptance requires the tested build and every stage, not only a success string."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import gamecore
from check_unreal_smoke import validate_stages

class AcceptanceTests(unittest.TestCase):
    def test_bundled_runner_is_input_but_python_cache_is_not(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); source=p/'Tools/GameCore/tools'; source.mkdir(parents=True)
            (source/'runner.py').write_text('source'); cache=source/'__pycache__'; cache.mkdir(); (cache/'runner.pyc').write_bytes(b'cache')
            files=gamecore.snapshot(p)
            self.assertEqual(list(files),['Tools/GameCore/tools/runner.py'])
    def test_named_scenarios_are_bounded_and_do_not_mutate_default(self):
        original={'smoke':{'flag':'Default','pass_marker':'PASS','fail_marker':'FAIL'},'smoke_scenarios':{'navigation':{'flag':'Nav','pass_marker':'NAV PASS','required_markers':['NAV STEP']}}}
        selected=gamecore.select_scenario(original,'navigation')
        self.assertEqual(selected['smoke']['flag'],'Nav'); self.assertEqual(original['smoke']['flag'],'Default')
        with self.assertRaises(ValueError):gamecore.select_scenario(original,'missing')
        original['smoke_scenarios']['bad']={'flag':'Nav -ExecCmds=Quit'}
        with self.assertRaises(ValueError):gamecore.select_scenario(original,'bad')
        original['smoke_scenarios']['bad']={'map':'/Game/Other'}
        with self.assertRaises(ValueError):gamecore.select_scenario(original,'bad')
    def test_stages_are_ordered_real_messages(self):
        good='LogTemp: Display: ONE detail\nLogTemp: Display: TWO\nLogTemp: Display: PASS'
        self.assertEqual(validate_stages(good,['ONE','TWO'],'PASS'),['ONE','TWO'])
        for bad in ['LogInit: CommandLine: ONE TWO\nPASS','TWO\nONE\nPASS','ONE\nPASS','ONE_MORE\nTWO\nPASS','PASS\nONE\nTWO']:
            with self.subTest(log=bad),self.assertRaises(ValueError): validate_stages(bad,['ONE','TWO'],'PASS')
        for stages in [['ONE','ONE'],['PASS'],['bad\nline'],[''],[None],'ONE']:
            with self.subTest(stages=stages),self.assertRaises(ValueError): validate_stages(good,stages,'PASS')

    def test_source_and_binary_provenance_required(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); run=p/'Saved/GameCore/001-build'; run.mkdir(parents=True)
            sources={'Source/Game.cpp':'source'}; binaries={'Binaries/Win64/Game.dll':'binary'}; engine={'PatchVersion':4}
            receipt=dict(status='passed',source_hashes=sources,binary_hashes=binaries,engine=engine)
            (run/'receipt.json').write_text(json.dumps(receipt))
            self.assertIn('sha256',gamecore.matching_build(p,sources,binaries,engine))
            for source,binary,version in [({},binaries,engine),(sources,{},engine),(sources,binaries,{})]:
                with self.assertRaisesRegex(ValueError,'rebuild'):gamecore.matching_build(p,source,binary,version)
            receipt['status']='failed'; (run/'receipt.json').write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):gamecore.matching_build(p,sources,binaries,engine)

    def test_runtime_error_overrides_success(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); (p/'engine.log').write_text('LogTemp: Display: PASS\nLogTemp: Error: broken')
            with self.assertRaisesRegex(ValueError,'Runtime errors'):
                gamecore.verify_result({'smoke':{'pass_marker':'PASS','fail_marker':'FAIL'}},p,'smoke')
