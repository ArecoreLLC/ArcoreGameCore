import copy
import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('course_contract', Path(__file__).resolve().parents[1] / 'course_contract.py')
course = importlib.util.module_from_spec(spec)
spec.loader.exec_module(course)

class CourseContractTests(unittest.TestCase):
    def setUp(self):
        self.data = {'schema_version': 1, 'units': 'centimeters', 'bounds': [0, -500, 2000, 500],
                     'grid': 100, 'max_pieces': 2, 'protected_zones': [[900, -500, 1100, 500]],
                     'pieces': [{'id': 'platform', 'half_extent': [50, 50], 'travel': [150, 0]}]}

    def test_motion_envelope_and_protected_zone(self):
        course.validate(self.data)
        self.assertTrue(course.placement(self.data, 0, 200, 0))
        self.assertFalse(course.placement(self.data, 0, 100, 0))
        self.assertTrue(course.placement(self.data, 0, 700, 0))
        self.assertFalse(course.placement(self.data, 0, 800, 0))

    def test_grid_overlap_and_capacity(self):
        self.assertFalse(course.placement(self.data, 0, 250, 0))
        self.assertFalse(course.placement(self.data, 0, 200, 0, [[0,-50,400,50]]))
        self.assertTrue(course.placement(self.data, 0, 600, 0, [[0,-50,400,50]]))
        self.assertFalse(course.placement(self.data, 0, 600, 0, [[0,-50,100,50], [1500,-50,1600,50]]))

    def test_nonfinite_and_types(self):
        for bad in (float('nan'), float('inf'), True, '100', None, 1e100, 1e-12, 10**1000):
            data = copy.deepcopy(self.data)
            data['grid'] = bad
            with self.assertRaises(ValueError): course.validate(data)
        for bad in (float('nan'), float('inf'), True):
            self.assertFalse(course.placement(self.data, 0, bad, 0))
        self.assertFalse(course.placement(self.data, -1, 200, 0))

    def test_invalid_rectangles_and_piece_identity(self):
        for key, value in [('bounds', [0,0,0,100]), ('protected_zones', [[0,0,100,float('inf')]]), ('max_pieces', 0)]:
            data = copy.deepcopy(self.data); data[key] = value
            with self.assertRaises(ValueError): course.validate(data)
        self.data['pieces'] *= 2
        with self.assertRaises(ValueError): course.validate(self.data)

    def test_oversize_envelope_rejected(self):
        self.data['pieces'][0]['travel'] = [2000, 0]
        with self.assertRaises(ValueError): course.validate(self.data)

    def test_header_is_deterministic_and_handles_no_zones(self):
        self.data['protected_zones'] = []
        course.validate(self.data)
        result = course.header(self.data, 'a'*64)
        self.assertIn('ZoneCount = 0', result)
        self.assertIn('200.000000000f', result)
        self.assertEqual(result, course.header(self.data, 'a'*64))

if __name__ == '__main__':
    unittest.main()
