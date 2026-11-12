import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_unreal_smoke import validate

class SmokeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.log = Path(self.temp.name) / 'run.log'
        self.log.write_text('[2026.11.11-12.00.00:000][ 42]LogTemp: Display: EXAMPLE_SMOKE PASS details\n')
    def test_valid_marker(self):
        self.assertEqual(validate(self.log, 'EXAMPLE_SMOKE PASS', 0, 0)['status'], 'passed')
    def test_marker_does_not_hide_runtime_error(self):
        for error in ('LogTemp: Error: bad actor', 'Fatal error: crash', 'Ensure condition failed: state', 'EXAMPLE_SMOKE FAIL'):
            with self.subTest(error=error):
                self.log.write_text('LogTemp: Display: EXAMPLE_SMOKE PASS\n' + error)
                with self.assertRaises(ValueError): validate(self.log, 'EXAMPLE_SMOKE PASS', 0, 0)
    def test_missing_stale_and_failed_exit(self):
        with self.assertRaises(ValueError): validate(self.log, 'EXAMPLE_SMOKE PASS', 1, 0)
        os.utime(self.log, (100,100))
        with self.assertRaises(ValueError): validate(self.log, 'EXAMPLE_SMOKE PASS', 0, 101)
        with self.assertRaises(ValueError): validate(self.log.with_name('missing'), 'EXAMPLE_SMOKE PASS', 0, 0)
    def test_echoed_arguments_and_partial_marker_rejected(self):
        for content in ('LogInit: CommandLine: --marker="EXAMPLE_SMOKE PASS"', 'LogTemp: Display: EXAMPLE_SMOKE PASSING', ''):
            self.log.write_text(content)
            with self.assertRaises(ValueError): validate(self.log, 'EXAMPLE_SMOKE PASS', 0, 0)
    def test_invalid_start_time_rejected(self):
        for value in (float("nan"), float("inf"), -1):
            with self.assertRaises(ValueError): validate(self.log, "EXAMPLE_SMOKE PASS", 0, value)

    def test_empty_marker_rejected(self):
        with self.assertRaises(ValueError): validate(self.log, '', 0, 0)

if __name__ == '__main__': unittest.main()
