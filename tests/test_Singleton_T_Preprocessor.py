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
    input_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        'test_singleton_t_preprocessor_input',
        )
    expected_output_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        'test_singleton_t_preprocessor_output',
        )
    with tempfile.NamedTemporaryFile(delete=False) as output_file:
      pass
    got_output_path = output_file.name
    os.unlink(got_output_path)
    self.p.process_file(input_path, got_output_path)
    with open(expected_output_path) as exp:
      with open(got_output_path) as got:
        self.assertEqual(exp.read(), got.read())    

if __name__ == '__main__':
  unittest.main()
