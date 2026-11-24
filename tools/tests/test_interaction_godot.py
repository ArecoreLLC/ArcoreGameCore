"""Exercise extracted modules in an empty project, without game assets/autoloads."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.environ.get("GODOT"), "set GODOT to run isolated interaction fixtures")
class InteractionGodotTests(unittest.TestCase):
    def test_alternate_consumers(self):
        source = ROOT / "shared/godot"
        fixtures = sorted(p for p in source.glob("*/tests/*.gd") if p.name.startswith("test_") or p.name == "run_tests.gd")
        self.assertGreaterEqual(len(fixtures), 5, "All five GDScript modules need standalone fixtures")
        with tempfile.TemporaryDirectory(prefix="gamecore-interactions-") as temp:
            project = Path(temp)
            user_dir = (project / "userdata").as_posix()
            (project / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Interaction fixtures"\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir="' + user_dir + '"\n')
            shutil.copytree(source, project / "addons/gamecore")
            command = [os.environ["GODOT"], "--headless", "--path", str(project)]
            result = subprocess.run(command + ["--import"], capture_output=True, text=True, timeout=90)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertNotIn("SCRIPT ERROR", output)
            self.assertNotIn("\nERROR:", output)
            for fixture in fixtures:
                with self.subTest(fixture=fixture.relative_to(source).as_posix()):
                    script = "res://addons/gamecore/" + fixture.relative_to(source).as_posix()
                    result = subprocess.run(command + ["--script", script], capture_output=True, text=True, timeout=90)
                    output = result.stdout + result.stderr
                    self.assertEqual(result.returncode, 0, output)
                    self.assertNotIn("SCRIPT ERROR", output)
                    self.assertNotIn("\nERROR:", output)
                    self.assertIn("PASS", output)


if __name__ == "__main__":
    unittest.main()
