import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import time
import mock

import s3g

class gcodeTests(unittest.TestCase):
  def setUp(self):
#    self.inputstream = io.BytesIO()
#    self.writer = s3g.FileWriter(self.inputstream)
#    self.r = s3g.s3g()
#    self.r.writer = self.writer
    self.mock = mock.Mock()

    self.g = s3g.GcodeParser()
#    self.g.s3g = self.r
    self.g.s3g = self.mock
   

 
  def tearDown(self):
    self.g = None
    self.r = None
    self.inputstream = None
    self.writer = None

  def test_find_axes_minimum_missing_feedrate(self):
    codes = {'G' : 161}
    self.assertRaises(s3g.MissingCodeError, self.g.FindAxesMinimum, codes, '') 

  def test_g_161_feedrate_is_flag(self):
    codes = {'G' : 161, 'F' : True}
    self.assertRaises(s3g.CodeValueError, self.g.FindAxesMinimum, codes, '')

  def test_g_161_all_registers_accounted_for(self):
    """
    Tests to make sure that throwing all registers in a command doesnt raise an
    extra register error.
    """
    allRegs = 'XYZF'
    self.assertEqual(sorted(allRegs), sorted(self.g.GCODE_INSTRUCTIONS[161][1]))

  def test_g_162_missing_feedrate(self):
    codes = {"G" : 162}
    self.assertRaises(s3g.MissingCodeError, self.g.FindAxesMaximum, codes, '')

  def test_g_162_feedrate_is_flag(self):
    codes = {"G" : 162, 'F' : True}
    self.assertRaises(s3g.CodeValueError, self.g.FindAxesMaximum, codes, '')

  def test_g_162_all_registers_accounted_for(self):
    allRegs = 'XYZF'
    self.assertEqual(sorted(allRegs), sorted(self.g.GCODE_INSTRUCTIONS[162][1]))

  def test_find_axes_minimum(self):
    self.g.states.position = {
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
    timeout = self.g.states.findingTimeout
    expectedPayload = [cmd, encodedAxes, feedrate, timeout]
    self.g.FindAxesMinimum(codes, '')
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
    self.assertEqual(expectedPosition, self.g.states.position)

  def test_find_axes_minimum_no_axes(self):
    codes = {'F':0}
    cmd = s3g.host_action_command_dict['FIND_AXES_MINIMUMS']
    encodedAxes = 0
    feedrate = 0
    expectedPayload = [cmd, encodedAxes, feedrate, self.g.states.findingTimeout]
    self.g.FindAxesMinimum(codes, '')
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    self.assertEqual(readPayload, expectedPayload)

  def test_find_axes_maximum(self):
    self.g.states.position = {
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
    expectedPayload = [cmd ,encodedAxes, feedrate, self.g.states.findingTimeout]
    self.g.FindAxesMaximum(codes, '')
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
    self.assertEqual(expectedPosition, self.g.states.position)

  def test_find_axes_maximum_no_axes(self):
    codes = {'F':0}
    cmd = s3g.host_action_command_dict['WAIT_FOR_TOOL_READY']
    encodedAxes = 0
    feedrate = 0
    expectedPayload = [cmd ,encodedAxes, feedrate, self.g.states.findingTimeout]
    self.g.FindAxesMaximum(codes, '')
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    self.assertEqual(readPayload, expectedPayload)

  def test_wait_for_toolhead(self):
    tool_index = 2
    timeout = 3
    delay = 100

    codes = {'T':tool_index, 'P':timeout}

    self.g.WaitForToolhead(codes, '')

    self.mock.WaitForToolReady.assert_called_once_with(tool_index, delay, timeout)


if __name__ == "__main__":
  unittest.main()
