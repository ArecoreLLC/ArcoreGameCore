import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("capture_validation", Path(__file__).parents[1] / "capture_validation.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CaptureValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "source.cpp").write_text("baseline")
        (self.root / "build.log").write_text("Build succeeded")

    def test_source_and_evidence_changes_change_hashes(self):
        check = {"id": "build", "status": "passed", "command": "build", "artifacts": ["build.log"]}
        first = module.capture(self.root, ["source.cpp"], [check])
        (self.root / "source.cpp").write_text("changed")
        (self.root / "build.log").write_text("New build succeeded")
        second = module.capture(self.root, ["source.cpp"], [check])
        self.assertNotEqual(first["source_sha256"], second["source_sha256"])
        self.assertNotEqual(first["checks"][0]["artifacts"], second["checks"][0]["artifacts"])

    def test_pass_requires_evidence_and_command(self):
        for check in [{"id": "x", "status": "passed"}, {"id": "x", "status": "passed", "artifacts": ["build.log"]}]:
            with self.assertRaises(ValueError):
                module.capture(self.root, ["source.cpp"], [check])

    def test_escape_and_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            module.capture(self.root, ["../outside"], [])
        with self.assertRaises(ValueError):
            module.capture(self.root, ["source.cpp"], [{"id": "x", "status": "not_run"}]*2)

    def test_not_run_is_not_promoted(self):
        result = module.capture(self.root, ["source.cpp"], [{"id": "playtest", "status": "not_run"}])
        self.assertEqual(result["checks"][0]["status"], "not_run")

    def test_missing_or_empty_evidence_rejected(self):
        (self.root / "empty.log").touch()
        with self.assertRaises(ValueError):
            module.capture(self.root, ["source.cpp"], [{"id": "x", "status": "passed", "command": "test", "artifacts": ["empty.log"]}])
        with self.assertRaises(FileNotFoundError):
            module.capture(self.root, ["source.cpp"], [{"id": "x", "status": "passed", "command": "test", "artifacts": ["missing.log"]}])
