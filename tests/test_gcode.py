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

class ParseCommandTests(unittest.TestCase):
  def test_empty_string(self):
    command = ''

    registers = s3g.ParseCommand(command)
    assert {} == registers

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
    expected_registers = {'G' : True}

    registers = s3g.ParseCommand(command)
    assert expected_registers == registers

  def test_single_code_no_value(self):
    command = 'G'
    expected_registers = {'G' : True}

    registers = s3g.ParseCommand(command)
    assert expected_registers == registers

  def test_single_code_with_value(self):
    command = 'G0'
    expected_registers = {'G' : 0}

    registers = s3g.ParseCommand(command)
    assert expected_registers == registers

  def test_single_code_leading_whitespace(self):
    command = '\t\t\t G0'
    expected_registers = {'G' : 0}

    registers = s3g.ParseCommand(command)
    assert expected_registers == registers

  def test_repeated_code(self):
    command = 'G0 G0'
    self.assertRaises(s3g.RepeatCodeError, s3g.ParseCommand, command)

  def test_many_codes(self):
    command = 'M0 X1 Y2 Z3 F4'
    expected_registers = {
      'M' : 0,
      'X' : 1,
      'Y' : 2,
      'Z' : 3,
      'F' : 4,
    }

    registers = s3g.ParseCommand(command)
    assert expected_registers == registers


class ParseSampleGcodeFileTests(unittest.TestCase):
  """
  Run the parser across all of the sample gcode files, to verify that no assertions
  are thrown
  """
  def test_parse_files(self):
    path = '../doc/gcode_samples/'
    files = glob.glob(os.path.join(path, '*.gcode'))

    assert len(files) > 0

    for file in files:
      with open(file) as lines:
        for line in lines:
          registers, comment = s3g.ParseLine(line)

if __name__ == "__main__":
  unittest.main()
