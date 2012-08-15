import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver

class CoordinatePreprocessor(unittest.TestCase):
  
  def setUp(self):
    self.cp = makerbot_driver.Preprocessors.CoordinatePreprocessor()
    
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

if __name__ == "__main__":
  unittest.main()
