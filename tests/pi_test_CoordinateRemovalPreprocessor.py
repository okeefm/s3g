import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest

import makerbot_driver

class TestCoordinateRemovalPreprocessor(unittest.TestCase):
  
  def setUp(self):
    self.cp = makerbot_driver.Preprocessors.CoordinateRemovalPreprocessor()
    
  def tearDown(self):
    self.cp = None

  def test_transform_g54(self):
    cases = [
        ['G54\n'  , '',],
        ['G55\n'  , 'G55\n',],
        ]
    for case in cases:
      self.assertEqual(case[1], self.cp._transform_g54(case[0]))

  def test_transform_g55(self):
    cases = [
        ['G55\n', '',],
        ['G54\n', 'G54\n'],
        ]
    for case in cases:
      self.assertEqual(case[1], self.cp._transform_g55(case[0]))

  def test_transform_g10(self):
    cases = [
        ["G11\n", "G11\n"],
        ["G10\n", ""],
        ]
    for case in cases:
      self.assertEqual(case[1], self.cp._transform_g10(case[0]))

  def test_transform_g90(self):
    cases = [
        ["G11\n", "G11\n"],
        ["G90\n", ""],
        ]
    for case in cases:
      self.assertEqual(case[1], self.cp._transform_g90(case[0]))

  def test_transform_g21(self):
    cases = [
        ["G11\n", "G11\n"],
        ["G21\n", ""],
        ]
    for case in cases:
      self.assertEqual(case[1], self.cp._transform_g21(case[0]))

if __name__ == "__main__":
  unittest.main()
