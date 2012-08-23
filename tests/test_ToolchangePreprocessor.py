import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile
import makerbot_driver 

class TestToolchangePreprocessor(unittest.TestCase):

  def setUp(self):
    self.p = makerbot_driver.Preprocessors.ToolchangePreprocessor()

  def tearDown(self):
    self.p = None

  def test_get_used_extruder(self):
    cases = [
      [None, 'G1 X0'],
      [None, 'G0'],
      [None, 'G1 X0 E0'],
      ['A', 'G1 A0'],
      ['A', 'G1 a0'],
      ['B', 'G1 B0'],
      ['B', 'G1 b0'],
      ]
    for case in cases:
      self.assertEqual(case[0], self.p.get_used_extruder(case[1]))

  def test_process_file(self):
    the_input = "G1 X50 Y50\nG1 X0 Y0 A50\nG1 X0 Y0 B50\nG1 X0 Y0 B50\nG1 X0 Y0 B50\nG1 X0 Y0 A50\nG1 X0 Y0 B50\n"
    expected_output = "G1 X50 Y50\nG1 X0 Y0 A50\nM135 T1\nG1 X0 Y0 B50\nG1 X0 Y0 B50\nG1 X0 Y0 B50\nM135 T0\nG1 X0 Y0 A50\nM135 T1\nG1 X0 Y0 B50\n"
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      input_file.write(the_input)
    with tempfile.NamedTemporaryFile(suffix='.gcode',delete=True) as output:
      output_path = output.name
    self.p.process_file(input_file.name, output_path)
    with open(output_path) as exp:
      self.assertEqual(expected_output, exp.read())

if __name__ == '__main__':
  unittest.main()
