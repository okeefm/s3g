import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import time

from s3g import Gcode, Profile

class s3gHelperFunctionTests(unittest.TestCase):
  def setUp(self):
    self.g = Gcode.GcodeStates()

  def tearDown(self):
    self.g = None

  def test_store_offsets(self):
    offset = 0
    offsets = [1, 2, 3]

  def test_store_offsets(self):
    offset = 0
    offsets = [1, 2, 3] 
    self.g.offsetPosition[0] = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        }
    self.g.StoreOffset(offset, offsets)
    expectedOffset = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        }
    self.assertEqual(expectedOffset, self.g.offsetPosition[0])

  def test_get_position_unspecified_axis_location(self):
    self.g.position['X'] = None
    self.assertRaises(Gcode.UnspecifiedAxisLocationError, self.g.GetPosition)

  def test_get_position_no_offsets(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    self.g.ofset_register = None
    expectedPosition = [0, 1, 2, 3, 4]
    self.assertEqual(expectedPosition, self.g.GetPosition())

  def test_get_position_with_offset(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    self.g.offsetPosition[0] = {
        'X' : 100,
        'Y' : 200,
        'Z' : 300,
        'A' : 400,
        'B' : 500,
        }
    self.g.offset_register = 0
    expectedPosition = [100, 201, 302, 403, 504]
    self.assertEqual(expectedPosition, self.g.GetPosition())
  
  def test_set_position_no_axes(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    axes = {}
    self.g.SetPosition(axes)
    self.assertEqual({'X':0,'Y':1,'Z':2,'A':3,'B':4}, self.g.position)

  def test_set_position_minimal_axes(self):
    self.g.position = {
        'X' : 0, 
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    axes = {'X' : -1}
    self.g.SetPosition(axes)
    self.assertEqual({'X' : -1, 'Y' : 1, 'Z' : 2, 'A' : 3, 'B' : 4}, self.g.position)

  def test_set_position(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    axes = {
        'X' : 5,
        'Y' : 6,
        'Z' : 7,  
        'A' : 8,
        'B' : 9, 
        }
    self.g.SetPosition(axes)
    self.assertEqual({'X' : 5, 'Y' : 6, 'Z' : 7, 'A' : 8, 'B' : 9}, self.g.position)

  def test_lose_position(self):
    self.g.position = {
          'X' : 1,
          'Y' : 2,
          'Z' : 3,
          'A' : 4,
          'B' : 5,
          }
    axes = ['X', 'Y', 'Z', 'A', 'B']
    self.g.LosePosition(axes)
    for key in self.g.position:
      self.assertTrue(self.g.position[key] == None)

  def test_lose_position_no_axes(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    axes = []
    expectedPosition = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2, 
        'A' : 3,
        'B' : 4, 
        }
    self.g.LosePosition(axes)
    self.assertEqual(expectedPosition, self.g.position)

  def test_lose_position_minimal_codes(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    expectedPosition = {
        'X' : None,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    axes = ['X']
    self.g.LosePosition(axes)
    self.assertEqual(expectedPosition, self.g.position)

  def test_set_build_name(self):
    build_name = 'test'
    self.g.SetBuildName(build_name)
    self.assertEqual(self.g.values['build_name'], build_name)

  def test_set_build_name_non_string(self):
    build_name = 9
    self.assertRaises(TypeError, self.g.SetBuildName, build_name)

class TestProfileInformationParsing(unittest.TestCase):

  def setUp(self):
    self.g = Gcode.GcodeStates()
    profile = Profile('ReplicatorDual')
    self.g.profile = profile
    self.axes = ['X', 'Y', 'Z', 'A', 'B']

  def tearDown(self):
    self.g = None

  def test_get_axes_values_key_error(self):
    key = 'this_is_going_to_fail_;('
    self.assertRaises(KeyError, self.g.GetAxesValues, self.axes, key)

  def test_get_axes_values(self):
    key = 'steps_per_mm'
    expected_values = [
        94.139,
        94.139,
        400,
        -96.275,
        -96.275,
        ]
    self.assertEqual(expected_values, self.g.GetAxesValues(self.axes, key))

class MachineProfileWith4Axes(unittest.TestCase):
  def setUp(self):
    self.g = Gcode.GcodeStates()
    profile = Profile('ReplicatorSingle')
    self.g.profile = profile

  def tearDown(self):
    self.g = None

  def get_axes_values_with_one_0(self):
    axes = ['X', 'Y', 'Z', 'A', 'B']
    key = 'steps_per_mm'
    expected_values = [
        94.139,
        94.139,
        400,
        -96.275,
        0,
        ]
    self.assertEqual(expected_values, self.g.GetAxesValues(axes, key))

if __name__ == "__main__":
  unittest.main()
