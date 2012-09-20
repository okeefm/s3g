import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver

class Skeinforge50PreprocessorTests(unittest.TestCase):
  
  def setUp(self):
    self.sp = makerbot_driver.Preprocessors.Skeinforge50Preprocessor()
    
  def tearDown(self):
    self.sp = None

  def test_process_file_can_proces_parsable_file(self):
    #Make input temp file
    test_gcode_file = ["M103\n","M101\n","M108 R2.51 T0\n","M105\n"]
    got_output = self.sp.process_file(inlines)
    expected_output = ["M73 P50 (progress (50%): 1/2)\n","M135 T0"]
    self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
  unittest.main()
