"""Headless fixture exercises the reusable modules without proprietary game assets."""
import json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
@unittest.skipUnless(os.environ.get('GODOT'),'set GODOT to run Godot module checks')
class ReusableGodotTests(unittest.TestCase):
    def test_route_cue_modules(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);(p/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Route cue modules"\n')
            dest=p/'addons/gamecore_world_life';dest.mkdir(parents=True)
            src=ROOT/'3d/godot/world_life'
            for f in src.glob('*.gd'):shutil.copy2(f,dest/f.name)
            shutil.copy2(src/'tests/route_cue_test.gd',p/'route_cue_test.gd')
            r=subprocess.run([os.environ['GODOT'],'--headless','--path',str(p),'--script','res://route_cue_test.gd'],capture_output=True,text=True,timeout=60)
            out=r.stdout+r.stderr
            self.assertEqual(r.returncode,0,out);self.assertNotIn('SCRIPT ERROR',out);self.assertIn('ROUTE_CUE_MODULES PASS',out)
    def test_painting_modules(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);(p/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Painting modules"\n')
            dest=p/'addons/gamecore_world_life';dest.mkdir(parents=True)
            src=ROOT/'3d/godot/world_life'
            for f in src.glob('*.gd'):shutil.copy2(f,dest/f.name)
            shutil.copy2(src/'tests/painting_test.gd',p/'painting_test.gd')
            r=subprocess.run([os.environ['GODOT'],'--headless','--path',str(p),'--script','res://painting_test.gd'],capture_output=True,text=True,timeout=60)
            out=r.stdout+r.stderr
            self.assertEqual(r.returncode,0,out);self.assertNotIn('SCRIPT ERROR',out);self.assertIn('PAINTING_MODULES PASS',out)
    def test_reusable_modules(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);(p/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Reusable modules"\n')
            dest=p/'addons/gamecore_world_life';dest.mkdir(parents=True)
            src=ROOT/'3d/godot/world_life'
            for f in src.glob('*.gd'):shutil.copy2(f,dest/f.name)
            shutil.copy2(src/'tests/reuse_test.gd',p/'reuse_test.gd')
            (p/'species.json').write_text(json.dumps({'schema':'gamecore.wing-species.v1','species':[
                {'name':'Amber example','from':'Example habitat','base':'f28a1a','edge':'1a1210','spot':'fffaf0','pattern':0},
                {'name':'Glass example','from':'Example habitat','base':[1,1,1,.18],'edge':'6b3a1e','spot':'ffffff','pattern':3}]}))
            r=subprocess.run([os.environ['GODOT'],'--headless','--path',str(p),'--script','res://reuse_test.gd'],capture_output=True,text=True,timeout=60)
            out=r.stdout+r.stderr
            self.assertEqual(r.returncode,0,out);self.assertNotIn('SCRIPT ERROR',out);self.assertIn('REUSABLE_WORLD_LIFE PASS',out)
if __name__=='__main__':unittest.main()
