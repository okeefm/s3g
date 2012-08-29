import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile
import makerbot_driver 

class TestProgressPreprocessor(unittest.TestCase):

  def setUp(self):
    self.p = makerbot_driver.Preprocessors.ProgressPreprocessor()

  def tearDown(self):
    self.p = None

  def test_process_file(self):
    the_input = "G1 X50 Y50\nG1 X0 Y0 A50\nG1 X0 Y0 B50\nG1 X0 Y0 B50\nG1 X0 Y0 B50\nG1 X0 Y0 A50\nG1 X0 Y0 B50\n"
    expected_output = "M73 P12 (progress (12%): 1/8)\nG1 X50 Y50\nM73 P25 (progress (25%): 2/8)\nG1 X0 Y0 A50\nM73 P37 (progress (37%): 3/8)\nG1 X0 Y0 B50\nM73 P50 (progress (50%): 4/8)\nG1 X0 Y0 B50\nM73 P62 (progress (62%): 5/8)\nG1 X0 Y0 B50\nM73 P75 (progress (75%): 6/8)\nG1 X0 Y0 A50\nM73 P87 (progress (87%): 7/8)\nG1 X0 Y0 B50\n"
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      input_file.write(the_input)
    with tempfile.NamedTemporaryFile(suffix='.gcode',delete=True) as output:
      output_path = output.name
    self.p.process_file(input_file.name, output_path)
    with open(output_path) as exp:
      self.assertEqual(expected_output, exp.read())

if __name__ == '__main__':
  unittest.main()
