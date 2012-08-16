import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver

class PreprocessorTests(unittest.TestCase):
  def setUp(self):
    self.p = makerbot_driver.Preprocessors.Preprocessor()

  def test_can_preprocess_file(self):
    input_path = 'input'
    output_path = 'output'
    self.p.process_file(input_path, output_path)

  def test_inputs_are_gcode(self):
    cases = [
        ['foo.gcode', 'bar.gcode', True],
        ['foo.gcode', 'bar', False],
        ['foo', 'bar.gcode', False],
        ['foo', 'bar', False],
        ]
    for case in cases:
      if case[2]:
        self.p.inputs_are_gcode(case[0], case[1])
      else:
        self.assertRaises(makerbot_driver.Preprocessors.NotGCodeFileError, self.p.inputs_are_gcode, case[0], case[1])
    
if __name__ == '__main__':
  unittest.main()
