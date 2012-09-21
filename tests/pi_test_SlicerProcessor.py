import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver

class SlicerProcessor(unittest.TestCase):
  
  def setUp(self):
    self.sp = makerbot_driver.GcodeProcessors.SlicerProcessor()
    
  def tearDown(self):
    self.sp = None

  def test_process_file(self):
    gcodes = ["G90\n","G21\n","M107 S500\n","M106 S500\n","M101\n","M102\n","M108\n","G1 X0 Y0 Z0 A0 B0\n"]
    expected_output = ['G1 X0 Y0 Z0 A0 B0\n', 'M73 P100 (progress (100%))\n']
    got_output = self.sp.process_gcode(gcodes)
    self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
  unittest.main()
