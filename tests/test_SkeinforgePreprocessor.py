import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver

class Skeinforge50PreprocessorTests(unittest.TestCase):
  
  def setUp(self):
    self.sp = makerbot_driver.Preprocessors.Skeinforge50Preprocessor()
    
  def tearDown(self):
    self.sp = None

  def test_transform_m104_non_m104_command(self):
    input_string = 'G1;M104\n'
    expected_string = 'G1;M104\n'
    got_string = self.sp._transform_m104(input_string)
    self.assertEqual(expected_string, got_string)

  def test_transoform_m104_command_has_t_code(self):
    input_string = 'M104 T2 S0\n'
    expected_string = 'M104 T2 S0\n'
    got_string = self.sp._transform_m104(input_string)
    self.assertEqual(expected_string, got_string)

  def test_transform_m104_command_no_t_code(self):
    input_string = 'M104 S0\n'
    expected_string = '\n'
    got_string = self.sp._transform_m104(input_string)

  def test_transform_m105_non_m105_command(self):
    input_string = 'G1;M105\n'
    expected_string = 'G1;M105\n'
    got_string = self.sp._transform_m105(input_string)
    self.assertEqual(expected_string, got_string)

  def test_transform_m105(self):
    input_string = 'M105\n'
    expected_string = ''
    got_string = self.sp._transform_m105(input_string)
    self.assertEqual(expected_string, got_string)

  def test_transform_line(self):
    inputs = [
        ['M105\n'     , ''],
        ['M104\n'     , ''],
        ]
    for i in inputs:
      self.assertEqual(i[1], self.sp._transform_line(i[0]))

  def test_process_file_input_doesnt_exist(self):
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      pass
    input_path = input_file.name
    os.unlink(input_path)
    output_file = 'test.gcode'
    self.assertRaises(IOError, self.sp.process_file, input_path, output_file)

  def test_process_file_input_file_isnt_gcode(self):
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as input_file:
      pass
    input_path = input_file.name
    os.unlink(input_path)
    output_path = 'test.gcode'
    self.assertRaises(makerbot_driver.Preprocessors.NotGCodeFileError, self.sp.process_file, input_path, output_path)

  def test_process_file_output_file_isnt_gcode(self):
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      pass
    input_path = input_file.name
    bad_output = 'something'
    self.assertRaises(makerbot_driver.Preprocessors.NotGCodeFileError, self.sp.process_file, input_path, bad_output)
    os.unlink(input_path)

  def test_process_file_good_inputs(self):
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      pass
    input_path = input_file.name
    output_path = 'test.gcode'
    self.sp.process_file(input_path, output_path)
    os.unlink(input_path)
    os.unlink(output_path)

  def test_process_file_can_proces_parsable_file(self):
    #Make input temp file
    test_gcode_file = "M103\nM101\nM108 R2.51 T0\nM105"
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      pass
    input_path = input_file.name
    f = open(input_path, 'w')
    f.write(test_gcode_file)
    f.close()
    #Make output temp file
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as output_file:
      pass
    output_path = output_file.name
    os.unlink(output_path)
    self.sp.process_file(input_path, output_path)
    expected_output = "M135 T0\n"
    with open(output_path, 'r') as f:
      got_output = f.read()
    self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
  unittest.main()
