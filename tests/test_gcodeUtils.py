import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import glob
import unittest
import string
import mock
from s3g import Gcode, errors

class GcodeUtilities(unittest.TestCase):
  def setUp(self):
    reload(Gcode)

  def test_empty_string(self):
    line = ''
    [command, comment] = Gcode.ExtractComments(line)
    assert '' == command
    assert '' == comment

  def test_semicolon_only(self):
    line = ';'
    [command, comment] = Gcode.ExtractComments(line)
    assert '' == command
    assert '' == comment
    
  def test_semicolon_with_data(self):
    line = ';;asdf'
    [command, comment] = Gcode.ExtractComments(line)
    assert '' == command
    assert ';asdf' == comment

  def test_parens_after_semicolon_ignored(self):
    line = ';)))'
    [command, comment] = Gcode.ExtractComments(line)
    assert '' == command
    assert ')))' == comment

  def test_right_paren_only(self):
    line = '('
    [command, comment] = Gcode.ExtractComments(line)
    assert '' == command
    assert '' == comment

  def test_right_paren_with_comment(self):
    line = '(comment'
    [command, comment] = Gcode.ExtractComments(line)
    assert '' == command
    assert 'comment' == comment

  def test_command_left_paren(self):
    line = 'command)'
    self.assertRaises(Gcode.CommentError, Gcode.ExtractComments, line)

  def test_closed_parens(self):
    line = '()'
    [command, comment] = Gcode.ExtractComments(line)
    assert '' == command
    assert '' == comment
 
  def test_closed_parens_with_nested_parens(self):
    line = '(())'
    [command, comment] = Gcode.ExtractComments(line)
    assert '' == command
    assert '' == comment

  def test_command_closed_parens_with_comment(self):
    line = 'commanda(comment)commandb'

    [command, comment] = Gcode.ExtractComments(line)
    assert 'commandacommandb' == command
    assert 'comment' == comment

  def test_comment_left_and_semicolon(self):
    line = 'asdf(qwer);testing'
    [command, comment] = Gcode.ExtractComments(line)
    self.assertEqual('asdf', command)
    self.assertEqual('testingqwer', comment)

  def test_empty_string(self):
    command = ''

    codes, flags = Gcode.ParseCommand(command)
    assert {} == codes
    assert [] == flags 

  def test_garbage_code(self):
    cases = [
      '1',
      '~',
    ]

    for command in cases:
      self.assertRaises(Gcode.InvalidCodeError, Gcode.ParseCommand, command)

  def test_single_code_garbage_value(self):
    cases = [
      'Ga',
      'G1a',
      'G12345a',
      'G1..0',
      'G1,0',
    ]

    for command in cases:
      self.assertRaises(ValueError, Gcode.ParseCommand, command)

  def test_single_code_accepts_lowercase(self):
    command = 'g'
    expected_codes = {}
    expected_flags = ['G']

    codes, flags = Gcode.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)

  def test_single_code_no_value(self):
    command = 'G'
    expected_codes = {}
    expected_flags = ['G']

    codes, flags = Gcode.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)

  def test_single_code_with_value(self):
    command = 'G0'
    expected_codes = {'G' : 0}
    expected_flags = []

    codes, flags = Gcode.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)

  def test_single_code_leading_whitespace(self):
    command = '\t\t\t G0'
    expected_codes = {'G' : 0}
    expected_flags = []

    codes, flags = Gcode.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)

  def test_repeated_code(self):
    command = 'G0 G0'
    self.assertRaises(Gcode.RepeatCodeError, Gcode.ParseCommand, command)

  def test_reject_both_g_and_m_code(self):
    command = 'G0 M0'
    self.assertRaises(Gcode.MultipleCommandCodeError, Gcode.ParseCommand, command)

  def test_reject_both_g_and_m_code(self):
    command = 'M0 G0'
    self.assertRaises(Gcode.MultipleCommandCodeError, Gcode.ParseCommand, command)

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

    codes, flags = Gcode.ParseCommand(command)
    self.assertEquals(expected_codes, codes)
    self.assertEquals(expected_flags, flags)

  def test_no_codes(self):
    codes = {}
    allowed_codes = ''
    Gcode.CheckForExtraneousCodes(codes, allowed_codes)

  def test_extra_code_with_g_code(self):
    codes = {'G' : 0, 'X' : 0}
    allowed_codes = 'X'
    Gcode.CheckForExtraneousCodes(codes.keys(), allowed_codes)

  def test_extra_code_With_m_code(self):
    codes = {'M' : 0, 'X' : 0}
    allowed_codes = 'X'
    Gcode.CheckForExtraneousCodes(codes.keys(), allowed_codes)
  
  def test_extra_code_no_allowed_codes(self):
    codes = {'X' : 0}
    allowed_codes = ''
    self.assertRaises(Gcode.InvalidCodeError, Gcode.CheckForExtraneousCodes, codes.keys(), allowed_codes)

  def test_extra_code_some_allowed_codes(self):
    codes = {'X' : 0, 'A' : 2}
    allowed_codes = 'XYZ'
    self.assertRaises(Gcode.InvalidCodeError, Gcode.CheckForExtraneousCodes, codes.keys(), allowed_codes)

  def test_all_allowed_codes(self):
    codes = {'X' : 0, 'Y' : 2, 'Z' : 3}
    allowed_codes = 'XYZ'
    Gcode.CheckForExtraneousCodes(codes.keys(), allowed_codes)

  def test_fewer_than_all_allowed_codes(self):
    codes = {'X' : 0, 'Y' : 2}
    allowed_codes = 'XYZ'
    Gcode.CheckForExtraneousCodes(codes.keys(), allowed_codes)

  def test_parse_out_axes_empty_set(self):
    codes = {}
    parsed_axes = Gcode.ParseOutAxes(codes)
    self.assertEqual([], parsed_axes)

  def test_parse_out_axes_reject_non_axis(self):
    non_axes = set(string.uppercase) - set('XYZAB')

    for non_axis in non_axes:
      parsed_axes = Gcode.ParseOutAxes([non_axis])
      self.assertEquals(parsed_axes, [])

  def test_parse_out_axes_single_axis(self):
    codes = {'X':True}
    parsed_axes = Gcode.ParseOutAxes(codes)
    self.assertEqual(['X'], parsed_axes)

  def test_parse_out_axes(self):
    codes = {'X':True, 'Y':True, 'Z':True, 'A':True, 'B':True}
    parsedAxes = Gcode.ParseOutAxes(codes)
    self.assertEqual(['A', 'B', 'X', 'Y', 'Z'], parsedAxes)

class DDASpeedTests(unittest.TestCase):

  def setUp(self):
    profile = Gcode.Profile("ReplicatorDual")
    self.g = Gcode.GcodeStates()
    self.g.profile = profile

  def tearDown(self):
    self.profile = None

  def test_reject_non_5d_lists(self):
    self.assertRaises(errors.PointLengthError, Gcode.CalculateVectorMagnitude, range(0,4))

  def test_makes_good_results(self):
    cases = [
      [[0,0,0,0,0], 0],
      [[1234.1,0,0,0,0], 1234.1],
      [[1,-2,3,-4,5], pow(55,.5)],
    ]

    for case in cases:
      self.assertEquals(case[1], Gcode.CalculateVectorMagnitude(case[0]))

  def test_reject_non_5d_list(self):
    self.assertRaises(Gcode.PointLengthError, Gcode.CalculateVectorDifference, range(4), range(5))

  def test_reject_non_5d_list(self):
    self.assertRaises(Gcode.PointLengthError, Gcode.CalculateVectorDifference, range(5), range(4))

  def test_good_result(self):
    cases = [
      [[0, 0, 0, 0, 0],  [0, 0, 0, 0, 0],      [0, 0, 0, 0, 0]],
      [[1, 2, 3, 4, 5],  [-1, -2, -3, -4, -5], [2, 4, 6, 8, 10]],
      [[6, 7, 8, 9, 10], [1, 2, 3, 4, 5],      [5, 5, 5, 5, 5]],
    ]

    for case in cases:
      diff = Gcode.CalculateVectorDifference(case[0], case[1])
      self.assertEqual(case[2], diff)

  def test_reject_non_5d_list(self):
    self.assertRaises(Gcode.PointLengthError, Gcode.CalculateUnitVector, range(4))
 
  def test_null_vector(self):
    vector = [0,0,0,0,0]
    expected_unit_vector = [0,0,0,0,0]

    unit_vector = Gcode.CalculateUnitVector(vector)
    self.assertEquals(expected_unit_vector, unit_vector)
 
  def test_good_result(self):
    cases = [
      [[1, 0, 0, 0, 0], [1,0,0,0,0]],
      [[-1, 0, 0, 0, 0], [-1,0,0,0,0]],
      [[1, -2, 3, -4, 5], [1/pow(55,.5),-2/pow(55,.5),3/pow(55,.5),-4/pow(55,.5),5/pow(55,.5)]],
    ]

    for case in cases:
      unit_vector = Gcode.CalculateUnitVector(case[0])
      self.assertEqual(case[1], unit_vector)

  def test_reject_non_5d_list(self):
    self.assertRaises(Gcode.PointLengthError, Gcode.GetSafeFeedrate, range(4), range(5), 0)

  def test_zero_displacement(self):
    point = [0, 0, 0, 0, 0]
    max_feedrates = [1, 1, 1, 1, 1]
    feedrate = 1
    Gcode.CalculateVectorMagnitude = mock.Mock(side_effect=Gcode.VectorLengthZeroError)
    self.assertRaises(Gcode.VectorLengthZeroError, Gcode.GetSafeFeedrate, point, max_feedrates, feedrate)

  def test_negative_feedrate(self):
    point = [1, 1, 1, 1, 1]
    max_feedrates = [1, 1, 1, 1, 1]
    feedrate = -1
    self.assertRaises(Gcode.InvalidFeedrateError, Gcode.GetSafeFeedrate, point, max_feedrates, feedrate)

  def test_zero_feedrate(self):
    point = [1, 1, 1, 1, 1]
    max_feedrates = [1, 1, 1, 1, 1]
    feedrate = 0
    self.assertRaises(Gcode.InvalidFeedrateError, Gcode.GetSafeFeedrate, point, max_feedrates, feedrate)

  def test_good_result(self):
    # Note: All of these cases use integers, and would fail if the float() casts
    #       were to be remvoed from GetSafeFeedrate. Try it.
    cases = [
      [[1,  0, 0, 0, 0],    # Single axis: Move under the max feedrate
       [10, 0, 0, 0, 0],
       1, 1],
      [[11, 0, 0, 0, 0],    # Single axis: Move at the max feedrate
       [2,  0, 0, 0, 0],
       2, 2],
      [[-12,0, 0, 0, 0],    # Single axis: Move in negative direction at the max feedrate
       [1,  0 ,0, 0, 0],
       1, 1],
      [[13, 0, 0, 0, 0],    # Single axis: Move faster than the max feedrate
       [1,  0, 0, 0, 0],
       10, 1],
      [[1, -1, 1,-1, 1],    # Multi axis: Move in negative direction at the max feedrate
       [1,  1, 1, 1, 1],
       pow(5,.5), pow(5,.5)],
      [[1, -2, 3,-4, 5],    # Multi axis: Move faster than the max feedrate
       [1,  1, 1, 1, 1],
       10, pow(55,.5)/5],
    ]
    for case in cases:
      self.assertEquals(case[3], Gcode.GetSafeFeedrate(case[0], case[1], case[2]))

  def test_reject_non_5d_list(self):
    self.assertRaises(Gcode.PointLengthError, Gcode.ConvertMmToSteps, range(4), range(5))
 
  def test_reject_non_5d_list(self):
    self.assertRaises(Gcode.PointLengthError, Gcode.ConvertMmToSteps, range(5), range(4))

  def test_good_result(self):
    cases = [
      [[0,0,0,0,0], [0,0,0,0,0], [0,0,0,0,0]],
      [[1,-2,3,-4,5], [1,2,3,4,5], [1,-4,9,-16,25]]
    ]

    for case in cases:
      self.assertEqual(case[2], Gcode.ConvertMmToSteps(case[0], case[1]))

  def test_reject_non_5d_list(self):
    self.assertRaises(errors.PointLengthError, Gcode.FindLongestAxis, range(4))

  def test_good_result(self):
    cases = [
      [[0,0,0,0,0],    0],
      [[1,0,0,0,0],    0],
      [[-1,0,0,0,0],   0],
      [[1,-2,3,-4,5],  4],
      [[-1,2,-3,4,-5], 4],
    ]

    for case in cases:
      self.assertEqual(case[1], Gcode.FindLongestAxis(case[0]))

  def test_zero_move(self):
    initial_position = [0,0,0,0,0]
    target_position =  [0,0,0,0,0]
    target_feedrate = 0
    Gcode.CalculateVectorMagnitude = mock.Mock(return_value=0)

    self.assertRaises(Gcode.VectorLengthZeroError, Gcode.CalculateDDASpeed, initial_position, target_position, target_feedrate, self.g.GetAxesValues('max_feedrate'), self.g.GetAxesValues('steps_per_mm'))

  def test_calculate_dda_speed_good_result(self):
    # TODO: These cases assume a replicator with specific steps_per_mm
    cases = [
      [[100,0,0,0,0], [200,0,0,0,0], 200, 30000000/9413.0],    # Single axis, forward motion
      [[0,100,0,0,0], [0,200,0,0,0], 300, 20000000/9413.0],
      [[0,0,100,0,0], [0,0,200,0,0], 300, 20000000/40000.0],
      [[200,0,0,0,0], [100,0,0,0,0], 200, 30000000/9413.0],    # Single axis, reverse motion
      [[0,0,0,0,0],   [1,1,1,0,0],   100, 1039230/400],        # Multiple axis, forward motion
    ]

    tolerance = .1
    for case in cases:
      dda_speed = Gcode.CalculateDDASpeed(
          case[0], 
          case[1], 
          case[2], 
          self.g.GetAxesValues('max_feedrate'), 
          self.g.GetAxesValues('steps_per_mm'))
      self.assertAlmostEqual(case[3], dda_speed, 7)

"""
[[9413,0,0,0,0) in 180000000 us (relative: 18)
[[18828,0,0,0,0) in 30000000 us (relative: 18)
[[28242,0,0,0,0) in 20000000 us (relative: 18)
[[37656,0,0,0,0) in 15000000 us (relative: 18)
[[47070,0,0,0,0) in 12000000 us (relative: 18)
[[56484,0,0,0,0) in 10000000 us (relative: 18)
[[65898,0,0,0,0) in 8571428 us (relative: 18)
[[75311,0,0,0,0) in 7500000 us (relative: 18)
[[84726,0,0,0,0) in 6666666 us (relative: 18)
[[94140,0,0,0,0) in 6000000 us (relative: 18)
[[103554,0,0,0,0) in 3000000 us (relative: 18)
[[112967,0,0,0,0) in 2000000 us (relative: 18)
[[122382,0,0,0,0) in 1500000 us (relative: 18)
"""

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
#          codes, flags, comment = Gcode.ParseLine(line)


 
if __name__ == "__main__":
  unittest.main()
