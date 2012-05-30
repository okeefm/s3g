import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import time
import mock
import copy

import s3g

class gcodeTestsMockedS3G(unittest.TestCase):
  def setUp(self):
    self.mock = mock.Mock(s3g.s3g)

    self.g = s3g.GcodeParser()
    self.g.s3g = self.mock

  def test_check_gcode_errors_are_recorded_correctly(self):
    command = "G161 Q1" #NOTE: this assumes that G161 does not accept a Q code
    expectedError = "#0: G161 Q1"
    try:
      self.g.ExecuteLine(command)
      #If we get to this point we want to fail, to show that this test was never able
      #to successfully complete
      self.assertTrue(False)
    except s3g.GcodeError as e:
      self.assertEqual(expectedError, str(e))

  def test_check_gcode_extraneous_codes_gets_called(self):
    command = "G161 Q1" # Note: this assumes that G161 does not accept a Q code
    self.assertRaises(s3g.InvalidCodeError, self.g.ExecuteLine, command)

  def test_check_gcode_extraneous_flags_gets_called(self):
    command = "G161 Q" # Note: this assumes that G161 does not accept a Q flag
    self.assertRaises(s3g.InvalidCodeError, self.g.ExecuteLine, command)

  def test_check_mcode_extraneous_codes_gets_called(self):
    command = "M6 X4" # Note: This assumes that M6 does not accept an X code
    self.assertRaises(s3g.InvalidCodeError, self.g.ExecuteLine, command)

  def test_check_mcode_extraneous_flags_gets_called(self):
    command = "M6 X" # Note: This assumes that M6 does not accept an X flag
    self.assertRaises(s3g.InvalidCodeError, self.g.ExecuteLine, command)

  def test_wait_for_toolhead_can_update_toolhead(self):
    tool_index = 2
    timeout = 3

    codes = {'T':tool_index, 'P':timeout}
    self.g.WaitForToolhead(codes, [], '')
    
    self.assertEquals(self.g.state.values['tool_index'], tool_index)

  def test_wait_for_toolhead_missing_timeout(self):
    tool_index = 2

    codes = {'T':tool_index}

    self.assertRaises(s3g.MissingCodeError, self.g.WaitForToolhead, codes, [], '')

  def test_wait_for_toolhead(self):
    tool_index = 2
    timeout = 3
    delay = 100 # As specified in the gcode protocol

    codes = {'T':tool_index, 'P':timeout}
    self.g.WaitForToolhead(codes, [], '')

    self.mock.WaitForToolReady.assert_called_once_with(tool_index, delay, timeout)

  def test_disable_axes(self):
    flags = ['A','B','X','Y','Z']

    self.g.DisableAxes({}, flags, '')
    self.mock.ToggleAxes.assert_called_once_with(flags, False)


  # TODO: test for missing timeout
  def test_display_message(self):
    row = 0 # As specified in the gcode protocol
    col = 0 # As specified in the gcode protocol
    message = 'ABCDEFG123'
    timeout = 123
    clear_existing = True # As specified in the gcode protocol
    last_in_group = True # As specified in the gcode protocol
    wait_for_button = False # As specified in the gcode protocol

    codes = {'P' : timeout}
    comment = message

    self.g.DisplayMessage(codes, [], comment)
    self.mock.DisplayMessage.assert_called_once_with(
      row,
      col,
      message,
      timeout,
      clear_existing,
      last_in_group,
      wait_for_button)


  def test_play_song_missing_song_id(self):
    codes = {}

    self.assertRaises(s3g.MissingCodeError, self.g.PlaySong, codes, [], '')

  def test_play_song(self):
    song_id = 2
    codes = {'P' : song_id}

    self.g.PlaySong(codes, [], '')
    self.mock.QueueSong.assert_called_once_with(song_id)


  def test_set_build_percentage_missing_percent(self):
    codes = {}

    self.assertRaises(s3g.MissingCodeError, self.g.SetBuildPercentage, codes, [], '')

  def test_set_build_percentage(self):
    build_percentage = 2
    codes = {'P' : build_percentage}

    self.g.SetBuildPercentage(codes, [], '')
    self.mock.SetBuildPercent.assert_called_once_with(build_percentage)


  def test_rapid_position_all_codes_accounted_for(self):
    codes = 'XYZ'
    flags = ''
    self.assertEqual(self.g.GCODE_INSTRUCTIONS[0][1], codes)
    self.assertEqual(self.g.GCODE_INSTRUCTIONS[0][2], flags)

  def test_rapid_position(self):
    self.g.state.position = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'A' : 0,
        'B' : 0,
        } 
    codes = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        }
    self.g.RapidPositioning(codes,[], '')
    expectedPoint = [1, 2, 3, 0, 0]
    spmList = [
        self.g.state.xSPM, 
        self.g.state.ySPM, 
        self.g.state.zSPM, 
        self.g.state.aSPM, 
        self.g.state.bSPM
        ]
    for i in range(len(spmList)):
      expectedPoint[i] *= spmList[i]
    self.mock.QueueExtendedPoint.assert_called_once_with(expectedPoint, self.g.state.rapidFeedrate)

 
  def test_store_offsets_all_codes_accounted_for(self):
    codes = 'XYZP'
    flags = ''
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[10][1])
    self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[10][2])

  def test_store_offsets_not_enough_codes(self):
    codes = {
        'X' : 0,
        'Y' : 0,
        'P' : 0,
        }
    self.assertRaises(s3g.MissingCodeError, self.g.StoreOffsets, codes, [], '')

  def test_store_offsets_no_p(self):
    codes = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        }
    self.assertRaises(s3g.MissingCodeError, self.g.StoreOffsets, codes, [],  '')

  def test_store_offsets(self):
    self.g.state.offsetPosition[0] = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'A' : 0,
        'B' : 0,
        }
    codes = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        'P' : 0,
        }
    self.g.StoreOffsets(codes, [], '')
    expectedOffsets = {
        0: {
            'X' : 1,
            'Y' : 2,
            'Z' : 3,
            'A' : 0,
            'B' : 0,
            },
        1:  {
            'X' : 0,
            'Y' : 0,
            'Z' : 0,
            'A' : 0,
            'B' : 0,
            }
        }
    self.assertEqual(expectedOffsets, self.g.state.offsetPosition)

  def test_use_p1_offsets_all_codes_accounted_for(self):
    codes = ''
    flags = ''
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[55][1])
    self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[55][2])

  def test_use_p1_offsets(self):
    codes = {}
    self.g.UseP1Offsets(codes, [], '')
    self.assertEqual(1, self.g.state.offset_register)
    self.assertEqual(1, self.g.state.values['tool_index'])

  def test_use_p0_offsets_all_codes_accounted_for(self):
    codes = ''
    flags = ''
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[54][1])
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[55][2])

  def test_use_p0_offsets(self):
    codes = {}
    self.g.UseP0Offsets(codes, [], '')
    self.assertEqual(0, self.g.state.offset_register) 
    self.assertEqual(0, self.g.state.values['tool_index'])

  def test_absolute_programming_all_codes_accounted_for(self):
    codes = ''
    flags = ''
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[90][1])

  def test_absolute_programming(self):
    oldState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,
        self.g.state.values,
        ]
    self.g.AbsoluteProgramming({}, [], "")
    newState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,     
        self.g.state.values,
        ]
    self.assertEqual(oldState, newState)

  def test_milimeter_programming_all_codes_accounted_for(self):
    codes = ''
    flags = ''
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[21][1])
    self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[21][2])

  def test_milimeter_programming(self):
    oldState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,
        self.g.state.values,
        ]
    self.g.MilimeterProgramming({}, [], "")
    newState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,     
        self.g.state.values,
        ]
    self.assertEqual(oldState, newState)   

  def test_set_position_all_codes_accounted_for(self):
    codes = 'XYZAB'
    flags = ''
    self.assertEqual(sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[92][1]))
    self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[92][2])

  def test_set_position(self):
    codes = { 
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    self.g.SetPosition(codes, [], '')
    self.assertEqual({'X':0,'Y':1,'Z':2,'A':3,'B':4}, self.g.state.position)
    expectedPosition = [0, 1, 2, 3, 4]
    spmList = [
        self.g.state.xSPM, 
        self.g.state.ySPM, 
        self.g.state.zSPM, 
        self.g.state.aSPM,
        self.g.state.bSPM,
        ]
    for i in range(len(spmList)):
      expectedPosition[i] *= spmList[i]
    self.mock.SetExtendedPosition.assert_called_once_with(expectedPosition)
  
  def test_find_axes_minimum_missing_feedrate(self):
    codes = {'G' : 161}
    self.assertRaises(s3g.MissingCodeError, self.g.FindAxesMinimums, codes, [], '') 
  def test_find_axes_minimums_all_codes_accounted_for(self):
    """
    Tests to make sure that throwing all registers in a command doesnt raise an
    extra register error.
    """
    codes = 'F'
    flags = 'XYZ'
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[161][1])
    self.assertEqual(sorted(flags), sorted(self.g.GCODE_INSTRUCTIONS[161][2]))

  def test_find_Axes_maximum_missing_feedrate(self):
    codes = {"G" : 162}
    self.assertRaises(s3g.MissingCodeError, self.g.FindAxesMaximums, codes, [], '')

  def test_find_axes_maximums_all_codes_accounted_for(self):
    codes = 'F'
    flags = 'XYZ'
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[162][1])
    self.assertEqual(sorted(flags), sorted(self.g.GCODE_INSTRUCTIONS[162][2]))

  def test_set_potentiometer_values_all_codes_accounted_for(self):
    codes = 'XYZAB'
    flags = ''
    self.assertEqual(sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[130][1]))
    self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[130][2])

  def test_set_potentiometer_values_no_codes(self):
    codes = {'G' : 130}
    self.g.SetPotentiometerValues(codes, [], '')
    self.assertEqual(self.mock.mock_calls, [])

  def test_set_potentiometer_values_one_axis(self):
    codes = {'G' : 130, 'X' : 0}
    cmd = s3g.host_action_command_dict['SET_POT_VALUE']
    axes = ['X']
    val = 0
    self.g.SetPotentiometerValues(codes, [], '')
    self.mock.SetPotentiometerValue.assert_called_once_with(axes, val)
  
  def test_set_potentiometer_values_all_axes(self):
    codes = {'X' : 0, 'Y' : 1, 'Z' : 2, 'A': 3, 'B' : 4} 
    expected = [
        [['X'], 0],
        [['Y'], 1],
        [['Z'], 2],
        [['A'], 3],
        [['B'], 4],
        ]
    cmd = s3g.host_action_command_dict['SET_POT_VALUE']
    self.g.SetPotentiometerValues(codes, [], '')
    for i in range(len(expected)):
      self.assertEqual(self.mock.mock_calls[i], mock.call.SetPotentiometerValue(expected[i][0], expected[i][1]))

  def test_set_potentiometer_values_all_codes_same(self):
    codes = {'X' : 0, 'Y' : 0, 'Z' : 0, 'A' : 0, 'B' : 0}
    self.g.SetPotentiometerValues(codes, [], '')
    axes = ['X', 'Y', 'Z', 'A', 'B']
    val = 0
    self.mock.SetPotentiometerValue.called_once_with(axes, val)

  def test_find_axes_minimums(self):
    codes = 'F'
    flags = 'XYZ'
    self.assertEqual(sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[161][1]))
    self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[161][2])

  def test_find_axes_minimum(self):
    self.g.state.position = {
          'X' : 0,
          'Y' : 0,
          'Z' : 0,
          'A' : 0,
          'B' : 0,
          }
    codes = {'F':0}
    flags = ['X', 'Y', 'Z']
    cmd = s3g.host_action_command_dict['FIND_AXES_MINIMUMS']
    axes = flags
    feedrate = 0
    timeout = self.g.state.findingTimeout
    self.g.FindAxesMinimums(codes, flags, '')
    self.mock.FindAxesMinimums.assert_called_once_with(axes, feedrate, timeout)
    expectedPosition = {
        'X'   :   None,
        'Y'   :   None,
        'Z'   :   None,
        'A'   :   0,
        'B'   :   0,
        }
    self.assertEqual(expectedPosition, self.g.state.position)

  def test_find_axes_minimum_no_axes(self):
    codes = {'F':0}
    cmd = s3g.host_action_command_dict['FIND_AXES_MINIMUMS']
    axes = []
    feedrate = 0
    timeout = self.g.state.findingTimeout
    self.g.FindAxesMinimums(codes, [], '')
    self.mock.FindAxesMinimums.assert_called_once_with(axes, feedrate, timeout)

  def test_find_axes_maximums_all_codes_accounted_for(self):
    codes = 'F'
    flags = 'XYZ'
    self.assertEqual(sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[162][1]))
    self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[162][2])

  def test_find_axes_maximum(self):
    self.g.state.position = {
        'X'   :   1,
        'Y'   :   2,
        'Z'   :   3,
        'A'   :   4,
        'B'   :   5
        }
    codes = {'F':0}
    flags = ['X', 'Y', 'Z']
    cmd = s3g.host_action_command_dict['FIND_AXES_MAXIMUMS']
    axes = flags
    feedrate = 0
    timeout = self.g.state.findingTimeout
    self.g.FindAxesMaximums(codes, flags, '')
    self.mock.FindAxesMaximums.assert_called_once_with(axes, feedrate, timeout)
    expectedPosition = {
        'X'   :   None,
        'Y'   :   None,
        'Z'   :   None,
        'A'   :   4,
        'B'   :   5,
        }
    self.assertEqual(expectedPosition, self.g.state.position)

  def test_find_axes_maximum_no_axes(self):
    codes = {'F':0}
    cmd = s3g.host_action_command_dict['FIND_AXES_MAXIMUMS']
    axes = []
    feedrate = 0
    timeout = self.g.state.findingTimeout
    self.g.FindAxesMaximums(codes, [], '')
    self.mock.FindAxesMaximums.assert_called_once_with(axes, feedrate, timeout)

  def test_linear_interpolation_all_codes_accounted_for(self):
    codes = 'XYZABEF'
    flags = ''
    self.assertEqual(sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[1][1]))
    self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[1][2])

  def test_linear_interpolation_no_feedrate_no_last_feedrate_set(self):
    codes = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
    }
    self.assertRaises(s3g.MissingCodeError, self.g.LinearInterpolation, codes, [], '')

  def test_linear_interpolation_no_feedrate_last_feedrate_set(self):
    feedrate = 50
    tool_index = 0
    extrusion_length = 5

    initialPosition = [0, 1, 2, 3, 4]
    expectedPoint = [0, 1, 2, 8, 4]

    self.g.state.position = {
        'X' : initialPosition[0],
        'Y' : initialPosition[1],
        'Z' : initialPosition[2],
        'A' : initialPosition[3],
        'B' : initialPosition[4],
        }

    self.g.state.values['feedrate'] = feedrate
    self.g.state.values['tool_index'] = tool_index

    codes = {
        'E' : extrusion_length
        }

    self.g.LinearInterpolation(codes, [], '')

    spmList = [
        self.g.state.xSPM,
        self.g.state.ySPM,
        self.g.state.zSPM,
        self.g.state.aSPM,
        self.g.state.bSPM,
        ]

    # s3g works in steps, so we need to convert the expected position to steps
    for i in range(len(expectedPoint)):
      expectedPoint[i] *= spmList[i]

    self.mock.QueueExtendedPoint.assert_called_once_with(expectedPoint, feedrate)
 
  def test_linaer_interpolation_e_and_a_codes_present(self):
    codes = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'E' : 0,
        'A' : 0,
        'F' : 0,
        }
    self.assertRaises(s3g.LinearInterpolationError, self.g.LinearInterpolation, codes, [], '')

  def test_linear_interpolation_e_and_b_codes_present(self):
    codes = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'E' : 0,
        'B' : 0,
        'F' : 0,
        }
    self.assertRaises(s3g.LinearInterpolationError, self.g.LinearInterpolation, codes, [], '')

  def test_linear_interpolation_e_and_a_and_b_present(self):
    codes = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'E' : 0,
        'A' : 0,
        'B' : 0,
        'F' : 0,
        }
    self.assertRaises(s3g.LinearInterpolationError, self.g.LinearInterpolation, codes, [], '')

  def test_linear_interpolation_no_e_code(self):
    self.g.state.position = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'A' : 0,
        'B' : 0,
        }
    codes = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        'A' : 4,
        'B' : 5,
        'F' : 0,
        }
    expectedPoint = [1, 2, 3, 4, 5]
    spmList = [
        self.g.state.xSPM,
        self.g.state.ySPM,
        self.g.state.zSPM,
        self.g.state.aSPM,
        self.g.state.bSPM,
        ]
    for i in range(len(expectedPoint)):
      expectedPoint[i] *= spmList[i]
    feedrate = 0
    self.g.LinearInterpolation(codes, [], '')
    self.mock.QueueExtendedPoint.assert_called_once_with(expectedPoint, feedrate)
    expectedPosition = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        'A' : 4,
        'B' : 5,
        }
    self.assertEqual(expectedPosition, self.g.state.position)

  def test_linear_interpolation_e_code_no_toolhead(self):
    codes = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'E' : 0,
        'F' : 0,
        }
    self.assertRaises(s3g.NoToolIndexError, self.g.LinearInterpolation, codes, [], '')

  def test_linear_interpolation_e_code(self):
    self.g.state.position = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'A' : 0,
        'B' : 0,
        }
    self.g.state.values['tool_index'] = 0
    codes = {
        'X' : 1, 
        'Y' : 2,
        'Z' : 3,
        'E' : 4,
        'F' : 1,
        }
    self.g.LinearInterpolation(codes, [], '')
    expectedPoint = [1, 2, 3, 4, 0]
    spmList = [
        self.g.state.xSPM,
        self.g.state.ySPM,
        self.g.state.zSPM,
        self.g.state.aSPM,
        self.g.state.bSPM,
        ]
    for i in range(len(expectedPoint)):
      expectedPoint[i] *= spmList[i]
    feedrate = 1
    self.mock.QueueExtendedPoint.assert_called_once_with(expectedPoint, feedrate)

  def test_linear_interpolation_a_and_b(self):
    self.g.state.position = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'A' : 0,
        'B' : 0,
        }
    codes = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        'A' : 4,
        'B' : 5,
        'F' : 1,
        }
    self.g.LinearInterpolation(codes, [], '')
    expectedPoint = [1, 2, 3, 4, 5]
    spmList = [
        self.g.state.xSPM,
        self.g.state.ySPM,
        self.g.state.zSPM,
        self.g.state.aSPM,
        self.g.state.bSPM,
        ]
    for i in range(len(expectedPoint)):
      expectedPoint[i] *= spmList[i]
    feedrate = 1
    self.mock.QueueExtendedPoint.assert_called_once_with(expectedPoint, feedrate)

  def test_dwell_all_codes_accounted_for(self):
    codes = 'P'
    flags = ''
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[4][1])
    self.assertEqual(flags, self.g.GCODE_INSTRUCTIONS[4][2])

  def test_dwell_no_p(self):
    codes = {}
    self.assertRaises(s3g.MissingCodeError, self.g.Dwell, codes, [], '')

  def test_dwell(self):
    codes = {'P'  : 10}
    miliConstant = 1000
    microConstant = 1000000
    d = 10 * microConstant / miliConstant
    self.g.Dwell(codes, [], '')
    self.mock.Delay.assert_called_once_with(d)

  def test_set_toolhead_temperature_all_codes_accounted_for(self):
    codes = 'ST'
    flags = ''
    self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[104][1])
    self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[104][2])

  def test_set_toolhead_temperature_no_s(self):
    codes = {'T'  : 2}
    self.assertRaises(s3g.MissingCodeError, self.g.SetToolheadTemperature, codes, [], '')

  def test_set_toolhead_temperature_no_t_no_set_tool_index(self):
    codes = {'S'  : 100}
    self.assertRaises(s3g.MissingCodeError, self.g.SetToolheadTemperature, codes, [], '')

  def test_set_toolhead_temperature_no_t_set_tool_index(self):
    tool_index = 0
    temperature = 100

    codes = {'S'  : temperature}
    self.g.state.values['tool_index'] = tool_index
    self.g.SetToolheadTemperature(codes, [], '')
    self.mock.SetToolheadTemperature.assert_called_once_with(tool_index, temperature)

  def test_set_toolhead_temperature_t_code_defined(self):
    tool_index = 2
    temperature = 100

    codes = {'S'  : temperature, 'T' :  tool_index}
    self.g.SetToolheadTemperature(codes, [], '')
    self.mock.SetToolheadTemperature.assert_called_once_with(tool_index, temperature)
    self.assertEqual(tool_index, self.g.state.values['tool_index'])

  def test_set_platform_temperature_all_codes_accounted_for(self):
    codes = 'ST'
    flags = ''

    self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[109][1])
    self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[109][2])

  def test_set_platform_temperature_no_s(self):
    codes = {'T'  : 2}
    self.assertRaises(s3g.MissingCodeError, self.g.SetPlatformTemperature, codes, [], '')

  def test_set_platform_temperature_no_t_no_set_toolhead(self):
    codes = {'S'  : 100}
    self.assertRaises(s3g.MissingCodeError, self.g.SetPlatformTemperature, codes, [], '')

  def test_set_platform_temperature_no_t_set_toolhead(self):
    codes = {'S'  : 100}

    self.g.state.values['tool_index'] = 2
    self.g.SetPlatformTemperature(codes, [], '')
    self.mock.SetPlatformTemperature.assert_called_once_with(self.g.state.values['tool_index'], 100)

  def test_set_platform_temperature_t_code_Defined(self):
    tool_index = 2
    codes = {'S'  : 100,  'T' : tool_index}
    self.g.SetPlatformTemperature(codes, [], '')
    self.mock.SetPlatformTemperature.assert_called_once_with(tool_index, 100)
    self.assertEqual(tool_index, self.g.state.values['tool_index'])

  def test_load_position_all_codes_accounted_for(self):
    codes = ''
    flags = ''
    self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[132][1])
    self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[132][2])

  def test_load_position(self):
    self.g.state.position = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'A' : 0,
        'B' : 0,
        }
    self.g.LoadPosition({}, [], '')
    expectedPosition = {
        'X' : None,
        'Y' : None,
        'Z' : None,
        'A' : 0,
        'B' : 0,
        }
    self.assertEqual(expectedPosition, self.g.state.position)
    self.mock.RecallHomePositions.assert_called_once_with(['X', 'Y', 'Z'])    

  def test_extruder_on_forward_all_codes_accounted_for(self):
    codes = ''
    flags = ''
    self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[101][1])
    self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[101][2])

  def test_extruder_on_forward(self):
    oldState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,
        self.g.state.values,
        ]
    self.g.ExtruderOnForward({}, [], "")
    newState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,     
        self.g.state.values,
        ]
    self.assertEqual(oldState, newState)

  def test_extruder_on_reverse_all_codes_accounted_for(self):
    codes = ''
    flags = ''
    self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[102][1])
    self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[102][2])

  def test_extruder_on_reverse(self):
    oldState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,
        self.g.state.values,
        ]
    self.g.ExtruderOnReverse({}, [], "")
    newState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,     
        self.g.state.values,
        ]
    self.assertEqual(oldState, newState)

  def test_extruder_off_all_codes_accounted_for(self):
    codes = 'T'
    flags = ''
    self.assertEqual(codes, self.g.MCODE_INSTRUCTIONS[103][1])
    self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[103][2])

  def test_extruder_off(self):
    oldState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,
        self.g.state.values,
        ]
    self.g.ExtruderOff({}, [], "")
    newState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,     
        self.g.state.values,
        ]
    self.assertEqual(oldState, newState)

  def test_set_extruder_speed_all_codes_accounted_for(self):
    codes = 'TR'
    flags = ''
    self.assertEqual(sorted(codes), sorted(self.g.MCODE_INSTRUCTIONS[108][1]))
    self.assertEqual(flags, self.g.MCODE_INSTRUCTIONS[108][2])

  def test_set_extruder_speed_no_t(self):
    oldState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,
        self.g.state.values,
        ]
    self.g.SetExtruderSpeed({}, [], "")
    newState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.offset_register,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,     
        self.g.state.values,
        ]
    self.assertEqual(oldState, newState)

  def test_set_extruder_speed_t_code(self):
    tool_index = 0
    codes = {'T'  : tool_index}
    self.g.SetExtruderSpeed(codes, [], "")
    self.assertEqual(tool_index, self.g.state.tool_index)

if __name__ == "__main__":
  unittest.main()
