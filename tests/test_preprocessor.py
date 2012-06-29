import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import s3g

class PreprocessorTests(unittest.TestCase):

  def test_can_create_preprocessor(self):
    p = s3g.Preprocessors.Preprocessor()

  def test_can_preprocess_file(self):
    input_path = 'input'
    output_path = 'output'
    p = s3g.Preprocessors.Preprocessor()
    p.process_file(input_path, output_path)
    
class Skeinforge50PreprocessorTests(unittest.TestCase):
  
  def setUp(self):
    self.sp = s3g.Preprocessors.Skeinforge50Preprocessor()
    
  def tearDown(self):
    self.sp = None

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

  def test_transform_m101_non_m101_command(self):
    input_string = 'G1;M101\n'
    expected_string = 'G1;M101\n'
    got_string = self.sp._transform_m101(input_string)
    self.assertEqual(expected_string, got_string)

  def test_transform_m101(self):
    input_string = 'M101\n'
    expected_string = ''
    got_string = self.sp._transform_m101(input_string)
    self.assertEqual(expected_string, got_string)

  def test_transform_m103_non_m103_command(self):
    input_string = 'G1;M103\n'
    expected_string = 'G1;M103\n'
    got_string = self.sp._transform_m103(input_string)
    self.assertEqual(expected_string, got_string)

  def test_transform_m103(self):
    input_string = 'M103\n'
    expected_string = ''
    got_string = self.sp._transform_m103(input_string)
    self.assertEqual(expected_string, got_string)

  def test_transform_m108(self):
    input_output_dict = {
        'M108\n'    :   '\n',
        'M108 R25.1\n'    :   '\n',
        'M108;comment\n'  :   '\n',
        'M108 T0\n'       :   'M135 T0\n',
        'M108 T0 R25.1\n' :   'M135 T0\n',
        'M108 T0 R25.1;superCOMMENT\n'  : 'M135 T0; superCOMMENT\n',
        'M108 (heres a comment) T0\n'   : 'M135 T0; heres a comment\n',
        'M108 (heres a comment) T0;heres another comment\n'   :   'M135 T0; heres another commentheres a comment\n',
        }
    for key in input_output_dict:
      self.assertEqual(input_output_dict[key], self.sp._transform_m108(key))

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
    self.assertRaises(s3g.Preprocessors.NotGCodeFileError, self.sp.process_file, input_path, output_path)

  def test_process_file_output_file_isnt_gcode(self):
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      pass
    input_path = input_file.name
    bad_output = 'something'
    self.assertRaises(s3g.Preprocessors.NotGCodeFileError, self.sp.process_file, input_path, bad_output)
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
