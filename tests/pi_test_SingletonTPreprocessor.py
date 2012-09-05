import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import makerbot_driver
import tempfile

class TestSingletonTPreprocessor(unittest.TestCase):
  def setUp(self):
    self.p = makerbot_driver.Preprocessors.SingletonTPreprocessor()

  def tearDown(self):
    self.p = None

  def test_singleton_t(self):
    cases = [
        [True, 'T0\n'],
        [False, 'T\n'],
        [False, ';lkj\n'],
        [False, '(some stuff)\n'],
        [False, 'G1 X4 Y5\n'],
        [False, 'M135 T0\n'],
        [True, 'T1;lkj\n'],
        ]
    for case in cases:
      self.assertEqual(case[0], self.p.is_singleton_t(case[1]))

  def test_turn_into_toolchange(self):
    cases = [
      ['T0\n', 'M135 T0\n'],
      ['T53\n', 'M135 T53\n'],
      ]
    for case in cases:
      self.assertEqual(case[1], self.p.turn_into_toolchange(case[0]))

  def test_process_file(self):
    the_input = "T0\nG1 X8 Y9\nT1\nG92 X0 Y0\nT7\n"
    expected_output = "M135 T0\nG1 X8 Y9\nM135 T1\nG92 X0 Y0\nM135 T7\n"
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gcode') as input_file:
      input_file.write(the_input)
    with tempfile.NamedTemporaryFile(delete=True, suffix='.gcode') as output_file:
      output_path = output_file.name
    self.p.process_file(input_file.name, output_path)
    with open(output_path) as exp:
      self.assertEqual(expected_output, exp.read())

if __name__ == '__main__':
  unittest.main()
