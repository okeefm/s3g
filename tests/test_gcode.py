import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import time

import s3g

class gcodeTests(unittest.TestCase):

  def setUp(self):
    self.g = s3g.GcodeParser()
    self.r = s3g.s3g()
    self.inputstream = io.BytesIO()
    self.writer = s3g.FileWriter(self.inputstream)
    self.r.writer = self.writer
    self.d = s3g.FileReader()
    self.d.file = self.inputstream
    self.g.s3g = self.r
 
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
    cmd = s3g.host_action_command_dict['FIND_AXES_MAXIMUMS']
    encodedAxes = 0
    feedrate = 0
    expectedPayload = [cmd ,encodedAxes, feedrate, self.g.states.findingTimeout]
    self.g.FindAxesMaximum(codes, '')
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPayload()
    self.assertEqual(readPayload, expectedPayload)

class s3gHelperFunctionTests(unittest.TestCase):
  def setUp(self):
    self.g = s3g.GcodeParser()

  def tearDown(self):
    self.g = None

  def test_lose_position(self):
    self.g.states.position = {
          'X' : 0,
          'Y' : 0,
          'Z' : 0,
          'A' : 0,
          'B' : 0,
          }
    codes = {'X':True, 'Y':True, 'Z':True, 'A':True, 'B':True}
    self.g.LosePosition(codes)
    for key in self.g.states.position:
      self.assertTrue(self.g.states.position[key] == None)

  def test_lose_position_no_codes(self):
    self.g.states.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    codes = {}
    expectedPosition = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2, 
        'A' : 3,
        'B' : 4, 
        }
    self.g.LosePosition(codes)
    self.assertEqual(expectedPosition, self.g.states.position)

  def test_lose_position_minimal_codes(self):
    self.g.states.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    expectedPosition = {
        'X' : None,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    codes = {'X':True}
    self.g.LosePosition(codes)
    self.assertEqual(expectedPosition, self.g.states.position)

  def test_parse_out_axes(self):
    codes = {'X':True, 'Y':True, 'Z':True, 'A':True, 'B':True}
    parsedAxes = self.g.ParseOutAxes(codes)
    self.assertEqual(sorted(['X', 'Y', 'Z', 'A', 'B']), sorted(parsedAxes))

  def test_parse_out_axes_extra_axes(self):
    codes = {'X':True, 'Y':True, 'Z':True, 'A':True, 'B':True, 'Q':True}
    parsedAxes = self.g.ParseOutAxes(codes)
    self.assertEqual(sorted(['X', 'Y', 'Z', 'A', 'B']), sorted(parsedAxes))

  def test_parse_out_axes_no_axes(self):
    codes = {}
    parsedAxes = self.g.ParseOutAxes(codes)
    self.assertEqual([], parsedAxes)

  def test_parse_out_axes_minimal_axes(self):
    codes = {'X':True}
    parsedAxes = self.g.ParseOutAxes(codes)
    self.assertEqual(['X'], parsedAxes)

if __name__ == "__main__":
  unittest.main()
