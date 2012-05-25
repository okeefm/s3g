import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import glob
import unittest

import s3g

class ExtractCommentsTests(unittest.TestCase):
  def test_empty_string(self):
    line = ''
    [command, comment] = s3g.ExtractComments(line)
    assert '' == command
    assert '' == comment

  def test_semicolon_only(self):
    line = ';'
    [command, comment] = s3g.ExtractComments(line)
    assert '' == command
    assert '' == comment
    
  def test_semicolon_with_data(self):
    line = ';;asdf'
    [command, comment] = s3g.ExtractComments(line)
    assert '' == command
    assert ';asdf' == comment

  def test_parens_after_semicolon_ignored(self):
    line = ';)))'
    [command, comment] = s3g.ExtractComments(line)
    assert '' == command
    assert ')))' == comment

  def test_right_paren_only(self):
    line = '('
    [command, comment] = s3g.ExtractComments(line)
    assert '' == command
    assert '' == comment

  def test_right_paren_with_comment(self):
    line = '(comment'
    [command, comment] = s3g.ExtractComments(line)
    assert '' == command
    assert 'comment' == comment

  def test_command_left_paren(self):
    line = 'command)'
    self.assertRaises(s3g.CommentError, s3g.ExtractComments, line)

  def test_closed_parens(self):
    line = '()'
    [command, comment] = s3g.ExtractComments(line)
    assert '' == command
    assert '' == comment
 
  def test_closed_parens_with_nested_parens(self):
    line = '(())'
    [command, comment] = s3g.ExtractComments(line)
    assert '' == command
    assert '' == comment

  def test_command_closed_parens_with_comment(self):
    line = 'commanda(comment)commandb'

    [command, comment] = s3g.ExtractComments(line)
    assert 'commandacommandb' == command
    assert 'comment' == comment

  def test_comment_left_and_semicolon(self):
    line = 'asdf(qwer);testing'
    [command, comment] = s3g.ExtractComments(line)
    self.assertEqual('asdf', command)
    self.assertEqual('testingqwer', comment)

class ParseCommandTests(unittest.TestCase):
  def test_empty_string(self):
    command = ''

    codes = s3g.ParseCommand(command)
    assert {} == codes

  def test_garbage_code(self):
    cases = [
      '1',
      '~',
    ]

    for command in cases:
      self.assertRaises(s3g.InvalidCodeError, s3g.ParseCommand, command)

  def test_single_code_garbage_value(self):
    cases = [
      'Ga',
      'G1a',
      'G12345a',
      'G1..0',
      'G1,0',
    ]

    for command in cases:
      self.assertRaises(ValueError, s3g.ParseCommand, command)

  def test_single_code_accepts_lowercase(self):
    command = 'g'
    expected_codes = {'G' : True}

    codes = s3g.ParseCommand(command)
    assert expected_codes == codes

  def test_single_code_no_value(self):
    command = 'G'
    expected_codes = {'G' : True}

    codes = s3g.ParseCommand(command)
    assert expected_codes == codes

  def test_single_code_with_value(self):
    command = 'G0'
    expected_codes = {'G' : 0}

    codes = s3g.ParseCommand(command)
    assert expected_codes == codes

  def test_single_code_leading_whitespace(self):
    command = '\t\t\t G0'
    expected_codes = {'G' : 0}

    codes = s3g.ParseCommand(command)
    assert expected_codes == codes

  def test_repeated_code(self):
    command = 'G0 G0'
    self.assertRaises(s3g.RepeatCodeError, s3g.ParseCommand, command)

  def test_reject_both_g_and_m_code(self):
    command = 'G0 M0'
    self.assertRaises(s3g.MultipleCommandCodeError, s3g.ParseCommand, command)

  def test_reject_both_g_and_m_code(self):
    command = 'M0 G0'
    self.assertRaises(s3g.MultipleCommandCodeError, s3g.ParseCommand, command)

  def test_many_codes(self):
    command = 'M0 X1 Y2 Z3 F4'
    expected_codes = {
      'M' : 0,
      'X' : 1,
      'Y' : 2,
      'Z' : 3,
      'F' : 4,
    }

    codes = s3g.ParseCommand(command)
    assert expected_codes == codes

class CheckForExtraneousCodesTests(unittest.TestCase):
  def test_no_codes(self):
    codes = {}
    allowed_codes = ''
    s3g.CheckForExtraneousCodes(codes, allowed_codes)

  def test_extra_code_with_g_code(self):
    codes = {'G' : 0, 'X' : 0}
    allowed_codes = 'X'
    s3g.CheckForExtraneousCodes(codes, allowed_codes)

  def test_extra_code_With_m_code(self):
    codes = {'M' : 0, 'X' : 0}
    allowed_codes = 'X'
    s3g.CheckForExtraneousCodes(codes, allowed_codes)
  
  def test_extra_code_no_allowed_codes(self):
    codes = {'X' : 0}
    allowed_codes = ''
    self.assertRaises(s3g.InvalidCodeError, s3g.CheckForExtraneousCodes, codes, allowed_codes)

  def test_extra_code_some_allowed_codes(self):
    codes = {'X' : 0, 'A' : 2}
    allowed_codes = 'XYZ'
    self.assertRaises(s3g.InvalidCodeError, s3g.CheckForExtraneousCodes, codes, allowed_codes)

  def test_all_allowed_codes(self):
    codes = {'X' : 0, 'Y' : 2, 'Z' : 3}
    allowed_codes = 'XYZ'
    s3g.CheckForExtraneousCodes(codes, allowed_codes)

  def test_fewer_than_all_allowed_codes(self):
    codes = {'X' : 0, 'Y' : 2}
    allowed_codes = 'XYZ'
    s3g.CheckForExtraneousCodes(codes, allowed_codes)

  def test_check_extraneous_codes_gets_called(self):
    g = s3g.GcodeParser()
    command = "G161 X Y Z F Q"
    self.assertRaises(s3g.InvalidCodeError, g.ExecuteLine, command)

class ParseSampleGcodeFileTests(unittest.TestCase):

  def test_parse_files(self):
    # Terriable hack, to support running from the root or test directory.
    files = []
#    path = '../doc/gcode_samples/'
#    files += glob.glob(os.path.join(path, '*.gcode'))
#    path = 'doc/gcode_samples/'
#    files += glob.glob(os.path.join(path, '*.gcode'))

    assert len(files) > 0

    for file in files:
      with open(file) as lines:
        for line in lines:
          codes, comment = s3g.ParseLine(line)

 
if __name__ == "__main__":
  unittest.main()
