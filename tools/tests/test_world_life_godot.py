"""Runs the GameCore world-life components' headless Godot test when $GODOT is set.

It builds a temporary Godot project: the module in addons/gamecore_world_life/ (as a game vendors
it), the flat test world and the test script, then runs Godot headless. Skipped without $GODOT.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "3d" / "godot" / "world_life"


@unittest.skipUnless(os.environ.get("GODOT"), "set GODOT to a Godot 4 executable to run the component test")
class WorldLifeGodotTest(unittest.TestCase):
    def test_components_headless(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            (project / "project.godot").write_text('config_version=5\n\n[application]\n\nconfig/name="world-life-components"\n', encoding="utf-8")
            addon = project / "addons" / "gamecore_world_life"
            addon.mkdir(parents=True)
            for gd in MODULE.glob("*.gd"):
                shutil.copyfile(gd, addon / gd.name)
            for name in ("components_test.gd", "flat_world.gd"):
                shutil.copyfile(MODULE / "tests" / name, project / name)
            run = subprocess.run([os.environ["GODOT"], "--headless", "--path", str(project), "--script", "res://components_test.gd"],
                                 capture_output=True, text=True, timeout=300)
            out = run.stdout + run.stderr
            failures = [line for line in out.splitlines() if line.startswith("WORLD_LIFE_COMPONENT ") and line.endswith("=false")]
            self.assertNotIn("SCRIPT ERROR", out, out[-3000:])
            self.assertEqual(failures, [], out[-3000:])
            self.assertIn("WORLD_LIFE_COMPONENTS PASS", out, out[-3000:])


if __name__ == "__main__":
    unittest.main()
