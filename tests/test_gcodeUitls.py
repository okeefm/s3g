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

    codes, flags = s3g.ParseCommand(command)
    assert {} == codes
    assert [] == flags 

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
    expected_codes = {}
    expected_flags = ['G']

    codes, flags = s3g.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)

  def test_single_code_no_value(self):
    command = 'G'
    expected_codes = {}
    expected_flags = ['G']

    codes, flags = s3g.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)

  def test_single_code_with_value(self):
    command = 'G0'
    expected_codes = {'G' : 0}
    expected_flags = []

    codes, flags = s3g.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)

  def test_single_code_leading_whitespace(self):
    command = '\t\t\t G0'
    expected_codes = {'G' : 0}
    expected_flags = []

    codes, flags = s3g.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)

  def test_repeated_code(self):
    command = 'G0 G0'
    self.assertRaises(s3g.RepeatCodeError, s3g.ParseCommand, command)

  def test_reject_both_g_and_m_code(self):
    command = 'G0 M0'
    self.assertRaises(s3g.MultipleCommandCodeError, s3g.ParseCommand, command)

  def test_reject_both_g_and_m_code(self):
    command = 'M0 G0'
    self.assertRaises(s3g.MultipleCommandCodeError, s3g.ParseCommand, command)

  def test_many_codes_and_flags(self):
    command = 'M0 X1 Y2 Z3 F4 A B'
    expected_codes = {
      'M' : 0,
      'X' : 1,
      'Y' : 2,
      'Z' : 3,
      'F' : 4,
    }
    expected_flags = ['A','B']

    codes, flags = s3g.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)


class CheckForExtraneousCodesTests(unittest.TestCase):
  def test_no_codes(self):
    codes = {}
    allowed_codes = ''
    s3g.CheckForExtraneousCodes(codes, allowed_codes)

  def test_extra_code_with_g_code(self):
    codes = {'G' : 0, 'X' : 0}
    allowed_codes = 'X'
    s3g.CheckForExtraneousCodes(codes.keys(), allowed_codes)

  def test_extra_code_With_m_code(self):
    codes = {'M' : 0, 'X' : 0}
    allowed_codes = 'X'
    s3g.CheckForExtraneousCodes(codes.keys(), allowed_codes)
  
  def test_extra_code_no_allowed_codes(self):
    codes = {'X' : 0}
    allowed_codes = ''
    self.assertRaises(s3g.InvalidCodeError, s3g.CheckForExtraneousCodes, codes.keys(), allowed_codes)

  def test_extra_code_some_allowed_codes(self):
    codes = {'X' : 0, 'A' : 2}
    allowed_codes = 'XYZ'
    self.assertRaises(s3g.InvalidCodeError, s3g.CheckForExtraneousCodes, codes.keys(), allowed_codes)

  def test_all_allowed_codes(self):
    codes = {'X' : 0, 'Y' : 2, 'Z' : 3}
    allowed_codes = 'XYZ'
    s3g.CheckForExtraneousCodes(codes.keys(), allowed_codes)

  def test_fewer_than_all_allowed_codes(self):
    codes = {'X' : 0, 'Y' : 2}
    allowed_codes = 'XYZ'
    s3g.CheckForExtraneousCodes(codes.keys(), allowed_codes)


class ParseOutAxesTests(unittest.TestCase):

  def test_all_axes_not_flags_empty_codes(self):
    codes = {}
    self.assertTrue(s3g.AllAxesNotFlags(codes))

  def test_all_axes_not_flags_one_flagged_code(self):
    codes = {
        'X' : True,
        'Y' : 0,
        }
    self.assertRaises(s3g.CodeValueError, s3g.AllAxesNotFlags, codes)

  def test_all_Axes_not_flags_no_flags(self):
    codes = {
        'X' : 0,
        'Y' : 1,
        }
    self.assertTrue(s3g.AllAxesNotFlags(codes))

  def test_parse_out_axes(self):
    codes = {'X':True, 'Y':True, 'Z':True, 'A':True, 'B':True}
    parsedAxes = s3g.ParseOutAxes(codes)
    self.assertEqual(sorted(['X', 'Y', 'Z', 'A', 'B']), sorted(parsedAxes))

  def test_parse_out_axes_extra_axes(self):
    codes = {'X':True, 'Y':True, 'Z':True, 'A':True, 'B':True, 'Q':True}
    parsedAxes = s3g.ParseOutAxes(codes)
    self.assertEqual(sorted(['X', 'Y', 'Z', 'A', 'B']), sorted(parsedAxes))

  def test_parse_out_axes_no_axes(self):
    codes = {}
    parsedAxes = s3g.ParseOutAxes(codes)
    self.assertEqual([], parsedAxes)

  def test_parse_out_axes_minimal_axes(self):
    codes = {'X':True}
    parsedAxes = s3g.ParseOutAxes(codes)
    self.assertEqual(['X'], parsedAxes)

class UtilityFunctionTests(unittest.TestCase):

  def test_code_present_missing_register(self):
    registers = {}
    self.assertFalse(s3g.IsCodePresent(registers, 'G'))

  def test_code_present(self):
    registers = {'G' : True}
    self.assertTrue(s3g.IsCodePresent(registers, 'G'))

  def test_is_code_a_flag_missing_register(self):
    registers = {}
    self.assertRaises(s3g.MissingCodeError, s3g.IsCodeAFlag, registers, 'G')

  def test_is_code_a_flag_not_a_flag(self):
    registers = {'G' : 0}
    self.assertFalse(s3g.IsCodeAFlag(registers, 'G'))

  def test_is_code_a_flag(self):
    registers = {'G' : True}
    self.assertTrue(s3g.IsCodeAFlag(registers, 'G'))

  def test_code_present_and_non_flag_missing_code(self):
    registers = {}
    self.assertRaises(s3g.MissingCodeError, s3g.CodePresentAndNonFlag,registers, 'G')

  def test_code_present_and_non_flag_code_is_flag(self):
    registers = {'G' : True}
    self.assertRaises(s3g.CodeValueError,s3g.CodePresentAndNonFlag,registers, 'G')

  def test_code_presetn_and_non_flag(self):
    registers = {'G' : 0}
    self.assertTrue(s3g.CodePresentAndNonFlag(registers, 'G'))

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
