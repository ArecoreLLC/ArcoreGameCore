import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("interaction_modules", Path(__file__).resolve().parents[1] / "interaction_modules.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InteractionModulesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "shared"
        self.project = Path(self.temp.name) / "consumer"
        (self.root / "shared").mkdir(parents=True)
        self.project.mkdir()
        (self.root / "helper.gd").write_text("extends RefCounted\n")
        self.manifest = dict(modules=[dict(id="synthetic", version="0.1.0", runtime="godot", files=[dict(source="helper.gd", destination="addons/example/helper.gd", sha256=module.digest(self.root / "helper.gd"))])])
        self.save_manifest()

    def save_manifest(self):
        (self.root / "shared/interaction-modules.json").write_text(json.dumps(self.manifest))

    def install(self, **kwargs):
        return module.vendor(self.project, godot_dir="game", root=self.root, **kwargs)

    def test_offline_check_and_edited_copy_rejected(self):
        self.install()
        (self.root / "helper.gd").unlink()
        module.check(self.project)
        (self.project / "game/addons/example/helper.gd").write_text("local change")
        with self.assertRaisesRegex(ValueError, "Installed module changed"):
            module.check(self.project)

    def test_unmanaged_file_preserved(self):
        target = self.project / "game/addons/example/helper.gd"
        target.parent.mkdir(parents=True)
        target.write_text("authored")
        with self.assertRaisesRegex(ValueError, "unmanaged"):
            self.install()
        self.assertEqual(target.read_text(), "authored")
        self.assertFalse((self.project / module.LOCK).exists())

    def test_upgrade_requires_explicit_update_and_rejects_local_edits(self):
        self.install()
        (self.root / "helper.gd").write_text("extends RefCounted\n# next\n")
        self.manifest["modules"][0]["version"] = "0.2.0"
        self.manifest["modules"][0]["files"][0]["sha256"] = module.digest(self.root / "helper.gd")
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "--update"):
            self.install()
        self.install(update=True)
        module.check(self.project)
        (self.project / "game/addons/example/helper.gd").write_text("local edit")
        with self.assertRaisesRegex(ValueError, "Installed module changed"):
            self.install(update=True)

    def test_paths_and_changed_sources_fail_before_install(self):
        for path in ["../escape", "/absolute"]:
            self.manifest["modules"][0]["files"][0]["destination"] = path
            self.save_manifest()
            with self.assertRaises(ValueError):
                self.install()
        self.manifest["modules"][0]["files"][0]["destination"] = "addons/example/helper.gd"
        self.save_manifest()
        (self.root / "helper.gd").write_text("changed canonical source")
        with self.assertRaisesRegex(ValueError, "Canonical source"):
            self.install()
        self.assertFalse((self.project / module.LOCK).exists())


if __name__ == "__main__":
    unittest.main()
