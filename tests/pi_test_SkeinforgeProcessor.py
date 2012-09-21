import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver

class Skeinforge50ProcessorTests(unittest.TestCase):
  
  def setUp(self):
    self.sp = makerbot_driver.GcodeProcessors.Skeinforge50Processor()
    
  def tearDown(self):
    self.sp = None

  def test_process_file_empty_file(self):
    gcodes = []
    expected_output = []
    got_output = self.sp.process_gcode(gcodes)
    self.assertEqual(expected_output, got_output)

  def test_process_file_progress_updates(self):
    gcodes = ["G90\n","G21\n","M104 S500\n","M105 S500\n","M101\n","M102\n","M108\n","G1 X0 Y0 Z0 A0 B0\n"]
    expected_output = ['G1 X0 Y0 Z0 A0 B0\n', 'M73 P100 (progress (100%))\n']
    got_output = self.sp.process_gcode(gcodes)
    self.assertEqual(expected_output, got_output)

  def test_process_file_stress_test(self):
    gcodes= [
        "G90\n",
        "G1 A0\n",
        "G1 B0\n",
        "M101\n",
        "G21\n",
        "G1 A0\n",
        "M104\n",
        "M108\n",
        "G1 B0\n",
        "M105\n",
        ]
    expected_output = [
        "G1 A0\n",
        "M73 P25 (progress (25%))\n",
        "G1 B0\n",
        "M73 P50 (progress (50%))\n",
        "G1 A0\n",
        "M73 P75 (progress (75%))\n",
        "G1 B0\n",
        "M73 P100 (progress (100%))\n",
        ]
    got_output = self.sp.process_gcode(gcodes)
    self.assertEqual(expected_output, got_output)
        

if __name__ == '__main__':
  unittest.main()
