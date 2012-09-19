import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import makerbot_driver

class TestPreprocessor(unittest.TestCase):

  def setUp(self):
    self.p = makerbot_driver.Preprocessors.Preprocessor()

  def tearDown(self):
    self.p = None

  def test_remove_variables(self):
    cases = [
        ['G92 X#X Y#Y Z#Z A#A B#B\n', 'G92 X0 Y0 Z0 A0 B0\n'],
        ['M104 T#TOOL_0 S#TOOL_TEMP\n', 'M104 T0 S0\n'],
        ]
    for case in cases:
      self.assertEqual(case[1], self.p._remove_variables(case[0]))

if __name__ == "__main__":
  unittest.main()
