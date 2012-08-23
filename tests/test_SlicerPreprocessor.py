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
    start_gcode = '***begin start gcode\n
                  G162 X Y F2000\n
                  G161 Z F2000\n
                  G92 X0 Y0 Z0 A0 B0\n
                  (**** end of start.gcode ****)\n' 
    end_gcode = '(******* End.gcode*******)
                G162 X Y F2000\n
                G161 Z F2000\n
                (*********end End.gcode*******)'
    with tempfile.NamedTemporaryFile(suffix='.gcode') as f:
      input_file = f.name
    with tempfile.NamedTemporaryFile(suffix='.gcode') as f:
      output_file = f.name
    the_input = start_gcode+"G90\nG21\nM107 S500\nM106 S500\nM101\nM102\nM108\nG1 X0 Y0 Z0 A0 B0"+end_gcode
    expected_output = '\nG1 X0 Y0 Z0 A0 B0'
    with open(input_file, 'w') as f:
      f.write(the_input)
    self.sp.process_file(input_file, output_file)
    with open(output_file) as f:
      self.assertEqual(expected_output, f.read())

if __name__ == '__main__':
  unittest.main()
