import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import glob
import unittest
import string

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
  def test_parse_out_axes_empty_set(self):
    codes = {}
    parsed_axes = s3g.ParseOutAxes(codes)
    self.assertEqual([], parsed_axes)

  def test_parse_out_axes_reject_non_axis(self):
    non_axes = set(string.uppercase) - set('XYZAB')

    for non_axis in non_axes:
      parsed_axes = s3g.ParseOutAxes([non_axis])
      self.assertEquals(parsed_axes, [])

  def test_parse_out_axes_single_axis(self):
    codes = {'X':True}
    parsed_axes = s3g.ParseOutAxes(codes)
    self.assertEqual(['X'], parsed_axes)

  def test_parse_out_axes(self):
    codes = {'X':True, 'Y':True, 'Z':True, 'A':True, 'B':True}
    parsedAxes = s3g.ParseOutAxes(codes)
    self.assertEqual(['A', 'B', 'X', 'Y', 'Z'], parsedAxes)

class ConvertDDASpeed(unittest.TestCase):
  def test_calculate_vector_magnitude_reject_non_5d_lists(self):
    self.assertRaises(s3g.PointLengthError, s3g.CalculateVectorMagnitude, range(0,4))

  def test_calculate_vector_magnitude_makes_good_results(self):
    cases = [
      [[0,0,0,0,0], 0],
      [[1234.1,0,0,0,0], 1234.1],
      [[1,-2,3,-4,5], pow(55,.5)],
    ]

    for case in cases:
      self.assertEquals(case[1], s3g.CalculateVectorMagnitude(case[0]))

  def test_calculate_motion_vector_reject_non_5d_list(self):
    points = [
        [range(4), range(5)],
        [range(5), range(4)],
        ]
    for point in points:
      self.assertRaises(s3g.PointLengthError, s3g.CalculateMotionVector, point[0], point[1])

  def test_calculate_motion_vector_good_results(self):
    point0 = [1, 2, 3, 4, 5]
    point1 = [6, 7, 8, 9, 10]
    expectedDif = [5, 5, 5, 5, 5]
    dif = s3g.CalculateMotionVector(point0, point1)
    self.assertEqual(expectedDif, dif)
 
  def test_calculate_unit_vector_reject_non_5d_list(self):
    self.assertRaises(s3g.PointLengthError, s3g.CalculateUnitVector, range(4))
 
  def test_calculate_unit_vector_good_result(self):
    p = [1, 2, 3, 4, 5]
    pMag = s3g.CalculateVectorMagnitude(p)
    expectedUnitP = []
    for val in p:
      expectedUnitP.append(val/pMag)
    unitP = s3g.CalculateUnitVector(p)
    self.assertEqual(expectedUnitP, unitP)
    
  def test_find_longest_axis(self):
    vector = [1, 2, 3, 4, 5]
    self.assertEqual(5, s3g.FindLongestAxis(vector))

  def test_point_mm_to_steps_unequal_lengths(self):
    point = range(4)
    self.assertRaises(s3g.PointLengthError, s3g.pointMMToSteps, point)

  def test_point_mm_to_step_good_length(self):
    expectedPoint = [94.140, 94.140, 400, 96.275, 96.275]
    point = [1, 1, 1, 1, 1]
    spmPoint = s3g.pointMMToSteps(point)
    self.assertEqual(expectedPoint, spmPoint)

  def test_calculate_dda_speed(self):
    curPoint = [100, 0, 0, 0, 0]
    target = [200, 0, 0, 0, 0]
    feedrate = 200
    targetFeedrate = 30000000
    self.assertEqual(targetFeedrate, s3g.CalculateDDASpeed(feedrate, curPoint, target))

  def test_get_Safe_feedrate_low_feedrate(self):
    point = [0, 0, 0, 0, 0]
    feedrate = 1
    self.assertEqual(feedrate, s3g.GetSafeFeedrate(point, feedrate))


#class ParseSampleGcodeFileTests(unittest.TestCase):
#  def test_parse_files(self):
#    # Terriable hack, to support running from the root or test directory.
#    files = [t]
#    path = '../doc/gcode_samples/'
#    files += glob.glob(os.path.join(path, '*.gcode'))
#    path = 'doc/gcode_samples/'
#    files += glob.glob(os.path.join(path, '*.gcode'))
#
#    assert len(files) > 0
#
#    for file in files:
#      with open(file) as lines:
#        for line in lines:
#          codes, flags, comment = s3g.ParseLine(line)


 
if __name__ == "__main__":
  unittest.main()
