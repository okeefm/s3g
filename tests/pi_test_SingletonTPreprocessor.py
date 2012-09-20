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

  def test_transform_singleton(self):
    cases = [
      ['T0\n', 'M135 T0\n'],
      ['T53\n', 'M135 T53\n'],
      ['(comments)T0\n', 'M135 T0\n'],
      ['(comments)T0 \n', 'M135 T0\n'],
      ['(comments)T0(MOAR COMMENTS)\n', 'M135 T0\n'],
      ['M126 T0\n', 'M126 T0\n'],
      ]
    for case in cases:
      self.assertEqual(case[1], self.p._transform_singleton(case[0]))

  def test_process_file(self):
    the_input = ["T0","\n","G1 X8 Y9","\n","T1","\n","G92 X0 Y0","\n","T7","\n"]
    expected_output = ["M135 T0\n","\n","G1 X8 Y9","\n","M135 T1\n","\n","G92 X0 Y0","\n","M135 T7\n","\n"]
    got_output = self.p.process_file(the_input)
    self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
  unittest.main()
