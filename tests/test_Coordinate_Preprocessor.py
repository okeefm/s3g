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

  def test_process_file(self):
    the_input = "G54\nG55\nG1 X0 Y0 Z0\nG54"
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gcode') as f:
      input_path = f.name
      f.write(the_input)
    with tempfile.NamedTemporaryFile(delete=True, suffix='.gcode') as f:
      output_path = f.name
    expected_output = 'G1 X0 Y0 Z0\n'
    self.cp.process_file(input_path, output_path)
    with open(output_path) as f:
      self.assertEqual(f.read(), expected_output)

  def test_transform_line(self):
    cases = [
      ['G54', ''],
      ['G55', ''],
      ]
    for case in cases:
      self.assertEqual(case[1], self.cp._transform_line(case[0]))

if __name__ == "__main__":
  unittest.main()
