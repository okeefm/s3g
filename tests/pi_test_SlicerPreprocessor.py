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

  def test_transform_line(self):
    cases = [
        ['G1 X0 Y0\n' , 'G1 X0 Y0\n'],
        ['G90\n'      , ''],
        ['G21\n'      , ''],
        ['M106 S500\n', ''],
        ['M107 S500\n', ''],
        ]
    for case in cases:
      self.assertEqual(case[1], self.sp._transform_line(case[0]))

  def test_tranform_g90(self):
    cases = [
        ['G90\n', ''],
        ['G92\n', 'G92\n'],
        ]
    for case in cases:
      self.assertEqual(case[1], self.sp._transform_g90(case[0]))

  def test_transform_g21(self):
    cases = [
        ['G21\n', ''],
        ['G92\n', 'G92\n'],
        ]
    for case in cases:
      self.assertEqual(case[1], self.sp._transform_g21(case[0]))

  def test_transform_m106(self):
    cases = [
        ['M106 S500\n', ''],
        ['M100\n', 'M100\n'],
        ]
    for case in cases:
      self.assertEqual(case[1], self.sp._transform_m106(case[0]))

  def test_transform_m107(self):
    cases = [
        ['M107 S500\n', ''],
        ['M100\n', 'M100\n'],
        ]
    for case in cases:
      self.assertEqual(case[1], self.sp._transform_m107(case[0]))

  def test_process_file(self):
    the_input = "G90\nG21\nM107 S500\nM106 S500\nM101\nM102\nM108\nG1 X0 Y0 Z0 A0 B0\n"
    expected_output = 'M73 P50 (progress (50%): 1/2)\nG1 X0 Y0 Z0 A0 B0'
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as f:
      f.write(the_input)
      input_file = f.name
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
      output_file = f.name
    self.sp.process_file(input_file, output_file)
    with open(output_file) as f:
      got_output = f.read()
      got_output = got_output.lstrip('\n').rstrip('\n')
      self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
  unittest.main()
