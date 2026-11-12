import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('check_unreal_automation', Path(__file__).resolve().parents[1] / 'check_unreal_automation.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

class UnrealEvidenceTests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(checker.validate({'tests': [{'fullTestPath': 'Example.Play', 'state': 'Success', 'errors': 0}]}, 'Example.')['count'], 1)

    def test_empty_missing_or_wrong_suite(self):
        for report in ({}, {'tests': []}, {'tests': [{'fullTestPath': 'Other', 'state': 'Success'}]}):
            with self.assertRaises(ValueError):
                checker.validate(report, 'Example.')

    def test_failure_pending_and_errors(self):
        for state, errors in [('Fail', 0), ('NotRun', 0), ('InProcess', 0), ('Success', 1)]:
            with self.assertRaises(ValueError):
                checker.validate({'tests': [{'fullTestPath': 'Example.Play', 'state': state, 'errors': errors}]}, 'Example.')
