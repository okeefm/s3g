import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver

class SlicerPreprocessor(unittest.TestCase):
  
  def setUp(self):
    self.sp = makerbot_driver.Preprocessors.SlicerPreprocessor()
    
  def tearDown(self):
    self.sp = None

  def test_process_file(self):
    the_input = ["G90\n","G21\n","M107 S500\n","M106 S500\n","M101\n","M102\n","M108\n","G1 X0 Y0 Z0 A0 B0\n"]
    expected_output = ['G1 X0 Y0 Z0 A0 B0\n', 'M73 P100 (progress (100%))\n']
    got_output = self.sp.process_file(the_input)
    self.assertEqual(expected_output, got_output)

  def test_process_file_no_progress_updates(self):
    the_input = ["G90\n","G21\n","M106 S500\n","M107 S500\n","M101\n","M102\n","M108\n","G1 X0 Y0 Z0 A0 B0\n"]
    expected_output = ['G1 X0 Y0 Z0 A0 B0\n']
    got_output = self.sp.process_file(the_input, add_progress=False)
    self.assertEqual(expected_output, got_output)

  def test_process_file_remove_start_end_with_progress(self):
    the_input = ["(**** start.gcode\n", "G1 X0 Y0 Z0\n", "(end of start.gcode\n", "G1 X9 Y9 Z9\n", "(**** End.gcode\n", "G1 X0 Y0 Z0\n", "(end End.gcode\n"]
    expected_output = ["G1 X9 Y9 Z9\n", "M73 P100 (progress (100%))\n"]
    got_output = self.sp.process_file(the_input, remove_start_end=True)
    self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
  unittest.main()
