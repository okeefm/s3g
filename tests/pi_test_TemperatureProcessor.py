import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest

import makerbot_driver

class TestTemperatureProcessor(unittest.TestCase):

  def setUp(self):
    self.p = makerbot_driver.GcodeProcessors.TemperatureProcessor()

  def tearDown(self):
    self.p = None

  def test_transform_m104(self):
    cases = [
        ["M104\n", ""],
        ["M105\n", "M105\n"],
        ["(comments)M104", ""],
        ["M104(comments)\n", ""],
        ["(comments)M104(comments)\n", ""],
        ["", ""],
        ]
    for case in cases:
      self.assertEqual(case[1], self.p._transform_m104(case[0]))

  def test_transform_m105(self):
    cases = [
        ["M105\n", ""],
        ["M104\n", "M104\n"],
        ["(comments)M105", ""],
        ["M105(comments)\n", ""],
        ["(comments)M105(comments)\n", ""],
        ["", ""],
        ]
    for case in cases:
      self.assertEqual(case[1], self.p._transform_m105(case[0]))

if __name__ == "__main__":
  unittest.main()
