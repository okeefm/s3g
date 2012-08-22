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
    input_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        'test_toolchange_preprocessor_input.gcode'
        )
    output_file = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        'test_toolchange_preprocessor_output.gcode'
        )  
    with tempfile.NamedTemporaryFile(suffix='.gcode',delete=False) as output:
      pass
    output_path = output.name
    os.unlink(output_path)
    self.p.process_file(input_path, output_path)
    got_output = open(output_path)
    expected_output = open(output_file)
    self.assertEqual(expected_output.read(), got_output.read())

if __name__ == '__main__':
  unittest.main()
