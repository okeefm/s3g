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
    self.mock = mock.Mock()

    self.g = s3g.GcodeParser()
    self.g.s3g = self.mock

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

  def test_wait_for_toolhead_can_update_temperature(self):
    tool_index = 2
    timeout = 3
    delay = 100

    codes = {'T':tool_index, 'P':timeout}
    self.g.WaitForToolhead(codes, [], '')
    
    self.assertEquals(self.g.state.values['tool_index'], tool_index)

  def test_wait_for_toolhead_missing_timeout(self):
    tool_index = 2
    timeout = 3
    delay = 100

    codes = {'T':tool_index}
    self.assertRaises(s3g.MissingCodeError, self.g.WaitForToolhead, codes, [], '')


  def test_wait_for_toolhead(self):
    tool_index = 2
    timeout = 3
    delay = 100

    codes = {'T':tool_index, 'P':timeout}
    self.g.WaitForToolhead(codes, [], '')

    self.mock.WaitForToolReady.assert_called_once_with(tool_index, delay, timeout)


class gcodeTests(unittest.TestCase):
  def setUp(self):
    self.g = s3g.GcodeParser()
    self.inputstream = io.BytesIO()
    self.writer = s3g.FileWriter(self.inputstream)
    self.r = s3g.s3g()
    self.r.writer = self.writer
    self.g.s3g = self.r
    self.d = s3g.FileReader()
    self.d.file = self.inputstream
 
  def tearDown(self):
    self.g = None
    self.r = None
    self.d = None
    self.inputstream = None
    self.writer = None

  def test_rapid_position_flagged_code(self):
    codes = {'X'  : True}
    self.assertRaises(s3g.CodeValueError, self.g.RapidPositioning, codes, '')
    
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
    self.g.RapidPositioning(codes, '')
    self.inputstream.seek(0)
    expectedPayload = [s3g.host_action_command_dict['QUEUE_EXTENDED_POINT']]
    positionInSteps = [1, 2, 3, 0, 0]
    spmList = [
        self.g.state.xSPM, 
        self.g.state.ySPM, 
        self.g.state.zSPM, 
        self.g.state.aSPM, 
        self.g.state.bSPM
        ]
    for i in range(len(spmList)):
      positionInSteps[i] *= spmList[i]
      positionInSteps[i] = int(positionInSteps[i])
    for pos in positionInSteps:
      expectedPayload.append(pos)
    expectedPayload.append(self.g.state.rapidFeedrate)
    readPayload = self.d.ParseNextPayload()    
    self.assertEqual(expectedPayload, readPayload)
 
  def test_store_offsets_all_codes_accounted_for(self):
    codes = 'XYZP'
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[10][1])

  def test_store_offsets_not_enough_codes(self):
    codes = {
        'X' : 0,
        'Y' : 0,
        'P' : 0,
        }
    self.assertRaises(s3g.MissingCodeError, self.g.StoreOffsets, codes, '')

  def test_store_offsets_no_p(self):
    codes = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        }
    self.assertRaises(s3g.MissingCodeError, self.g.StoreOffsets, codes, '')

  def test_store_offsets_p_is_flag(self):
    codes = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'P' : True,
        }
    self.assertRaises(s3g.CodeValueError, self.g.StoreOffsets, codes, '')

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
    self.g.StoreOffsets(codes, '')
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
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[55][1])

  def test_use_91_offsets(self):
    codes = {}
    self.g.UseP1Offsets(codes, [], '')
    self.assertEqual(1, self.g.state.offset_register)
    self.assertEqual(1, self.g.state.tool_index)

  def test_use_p0_offsets_all_codes_accounted_for(self):
    codes = ''
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[54][1])

  def test_use_90_offsets(self):
    codes = {}
    self.g.UseP0Offsets(codes, [], '')
    self.assertEqual(0, self.g.state.offset_register) 
    self.assertEqual(0, self.g.state.tool_index)

  def test_absolute_programming_all_codes_accounted_for(self):
    codes = ''
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[90][1])

  def test_absolute_programming(self):
    oldState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.tool_index,
        self.g.state.offset_register,
        self.g.state.tool_speed,
        self.g.state.tool_direction,
        self.g.state.tool_enabled,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,
        ]
    newState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.tool_index,
        self.g.state.offset_register,
        self.g.state.tool_speed,
        self.g.state.tool_direction,
        self.g.state.tool_enabled,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,     
        ]
    self.g.AbsoluteProgramming({}, [], "")
    self.assertEqual(oldState, newState)

  def test_milimeter_programming_all_codes_accounted_for(self):
    codes = ''
    self.assertEqual(codes, self.g.GCODE_INSTRUCTIONS[21][1])

  def test_milimeter_programming(self):
    oldState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.tool_index,
        self.g.state.offset_register,
        self.g.state.tool_speed,
        self.g.state.tool_direction,
        self.g.state.tool_enabled,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,
        ]
    newState = [
        self.g.state.position,
        self.g.state.offsetPosition,
        self.g.state.tool_index,
        self.g.state.offset_register,
        self.g.state.tool_speed,
        self.g.state.tool_direction,
        self.g.state.tool_enabled,
        self.g.state.rapidFeedrate,
        self.g.state.findingTimeout,     
        ]
    self.g.MilimeterProgramming({}, [], "")
    self.assertEqual(oldState, newState)   

  def test_set_position_flagged_register(self):
    codes = {'X' : True}
    self.assertRaises(s3g.CodeValueError, self.g.SetPosition, codes, [], "")

  def test_set_position_all_codes_accounted_for(self):
    codes = 'XYZAB'
    self.assertEqual(sorted(codes), sorted(self.g.GCODE_INSTRUCTIONS[92][1]))

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
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    expectedPayload = [s3g.host_action_command_dict['SET_EXTENDED_POSITION']]
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
      expectedPosition[i] = int(expectedPosition[i])
    for pos in expectedPosition:
      expectedPayload.append(pos)
    self.assertEqual(expectedPayload, readPayload)
  
  def test_find_axes_minimum_missing_feedrate(self):
    codes = {'G' : 161}
    self.assertRaises(s3g.MissingCodeError, self.g.FindAxesMinimum, codes, [], '') 

  def test_find_axes_minimum_feedrate_is_flag(self):
    codes = {'G' : 161, 'F' : True}
    self.assertRaises(s3g.CodeValueError, self.g.FindAxesMinimum, codes, [], '')

  def test_g_161_all_registers_accounted_for(self):
    """
    Tests to make sure that throwing all registers in a command doesnt raise an
    extra register error.
    """
    allRegs = 'XYZF'
    self.assertEqual(sorted(allRegs), sorted(self.g.GCODE_INSTRUCTIONS[161][1]))

  def test_find_Axes_maximum_missing_feedrate(self):
    codes = {"G" : 162}
    self.assertRaises(s3g.MissingCodeError, self.g.FindAxesMaximum, codes, [], '')

  def test_find_axes_maximum_feedrate_is_flag(self):
    codes = {"G" : 162, 'F' : True}
    self.assertRaises(s3g.CodeValueError, self.g.FindAxesMaximum, codes, [], '')

  def test_g_162_all_codes_accounted_for(self):
    allRegs = 'XYZF'
    self.assertEqual(sorted(allRegs), sorted(self.g.GCODE_INSTRUCTIONS[162][1]))

  def test_set_potentiometer_values_no_codes(self):
    codes = {'G' : 130}
    self.g.SetPotentiometerValues(codes, [], '')
    self.inputstream.seek(0)
    payloads = self.d.ReadFile()
    self.assertEqual(len(payloads), 0)

  def test_set_potentiometer_values_codes_are_flags(self):
    codes = {'G' : 130, 'X' : True}
    self.assertRaises(s3g.CodeValueError, self.g.SetPotentiometerValues, codes, [], '')

  def test_set_potentiometer_values_one_axis(self):
    codes = {'G' : 130, 'X' : 0}
    cmd = s3g.host_action_command_dict['SET_POT_VALUE']
    encodedAxes = s3g.EncodeAxes(['x'])
    val = 0
    expectedPayload = [cmd, encodedAxes, val]
    self.g.SetPotentiometerValues(codes, [], '')
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    self.assertEqual(expectedPayload, readPayload)

  def test_set_potentiometer_values_all_axes(self):
    codes = {'X' : 0, 'Y' : 1, 'Z' : 2, 'A': 3, 'B' : 4} 
    cmd = s3g.host_action_command_dict['SET_POT_VALUE']
    axes = ['X', 'Y', 'Z', 'A', 'B']
    values = [0, 1 ,2, 3, 4]
    self.g.SetPotentiometerValues(codes, [], '')
    self.inputstream.seek(0)
    readPayloads = self.d.ReadFile() 
    for readPayload, i in zip(readPayloads, range(5)):
      expectedPayload = [cmd, s3g.EncodeAxes(axes[i]), values[i]]
      self.assertEqual(expectedPayload, readPayload)

  def test_set_potentiometer_values_all_codes_same(self):
    codes = {'X' : 0, 'Y' : 0, 'Z' : 0, 'A' : 0, 'B' : 0}
    cmd = s3g.host_action_command_dict['SET_POT_VALUE']
    axes = s3g.EncodeAxes(['x', 'y', 'z', 'a', 'b'])
    expectedPayload = [cmd, axes, 0]
    self.g.SetPotentiometerValues(codes, [], '')
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    self.assertEqual(expectedPayload, readPayload)

  def test_find_axes_minimum(self):
    self.g.state.position = {
          'X' : 0,
          'Y' : 0,
          'Z' : 0,
          'A' : 0,
          'B' : 0,
          }
    codes = {'X':True, 'Y':True, 'Z':True, 'F':0}
    cmd = s3g.host_action_command_dict['FIND_AXES_MINIMUMS']
    encodedAxes = s3g.EncodeAxes(['x', 'y', 'z'])
    feedrate = 0
    timeout = self.g.state.findingTimeout
    expectedPayload = [cmd, encodedAxes, feedrate, timeout]
    self.g.FindAxesMinimum(codes, [], '')
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    self.assertEqual(expectedPayload, readPayload)
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
    encodedAxes = 0
    feedrate = 0
    expectedPayload = [cmd, encodedAxes, feedrate, self.g.state.findingTimeout]
    self.g.FindAxesMinimum(codes, [], '')
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    self.assertEqual(readPayload, expectedPayload)

  def test_find_axes_maximum(self):
    self.g.state.position = {
        'X'   :   1,
        'Y'   :   2,
        'Z'   :   3,
        'A'   :   4,
        'B'   :   5
        }
    codes = {'X':True, 'Y':True, 'Z':True, 'F':0}
    cmd = s3g.host_action_command_dict['FIND_AXES_MAXIMUMS']
    encodedAxes = s3g.EncodeAxes(['x', 'y', 'z'])
    feedrate = 0
    expectedPayload = [cmd ,encodedAxes, feedrate, self.g.state.findingTimeout]
    self.g.FindAxesMaximum(codes, [], '')
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    self.assertEqual(expectedPayload, readPayload)
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
    encodedAxes = 0
    feedrate = 0
    expectedPayload = [cmd ,encodedAxes, feedrate, self.g.state.findingTimeout]
    self.g.FindAxesMaximum(codes, [], '')
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    self.assertEqual(readPayload, expectedPayload)

if __name__ == "__main__":
  unittest.main()
