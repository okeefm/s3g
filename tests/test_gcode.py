import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import glob
import unittest
import io
import time

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


class gcodeStateTests(unittest.TestCase):

  def setUp(self):
    self.g = s3g.GcodeParser()

  def tearDown(self):
    self.g = None

  def test_g_162_state_no_registers(self):
    command = "G192"
    self.g.ExecuteLine(command)
    for key in self.g.states:
      self.assertTrue(self.g.states[key] == 0)

  def test_g_162_state(self):
    """
    Tests to make sure G162 properly looses only those points passed in
    """
    command = "G162 X"
    self.g.ExecuteLine(command)
    for key in self.g.states:
      if key == 'X':
        self.assertTrue(self.g.states[key] == None)
      else:
        self.assertTrue(self.g.states[key] != None)

  def test_g_162_state_overloaded_registers(self):
    command = "G162 X Y Z A"
    self.assertRaises(s3g.ExtraneousCodeError, self.g.ExecuteLine, command)

  def test_g_162_state_all_registers_accounted_for(self):
    """
    Tests to make sure that throwing all registers in a command doesnt raise an
    extra register error.
    """
    allRegs = ['X', 'Y', 'Z']
    self.assertEqual(allRegs, self.g.GCODE_INSTRUCTIONS[162][1])

class gcodeS3gInterfaceTests(unittest.TestCase):

  def setUp(self):
    self.g = s3g.GcodeParser()
    self.r = s3g.s3g()
    self.inputstream = io.BytesIO()
    self.writer = s3g.FileWriter(self.inputstream)
    self.r.writer = self.writer
    self.d = s3g.FileReader()
    self.d.file = self.inputstream
   
  def tearDown(self):
    self.g = None
    self.r = None
    self.inputstream = None
    self.writer = None
    
  def test_find_axes_minimums(self):
    registers = {'X':True, 'Y':True, 'Z':True}
    encodedAxes = s3g.EncodeAxes(['x', 'y', 'z'])
    self.g.FindAxesMinimums(registers, '')
    self.inputstream.seek(0)
    packet = self.d.ParseNextPacket()
    self.assertEqual(packet[0], s3g.host_action_command_dict['FIND_AXES_MINIMUMS'])
    self.assertEqual(packet[1], encodedAxes)

  def test_find_axes_minimums_no_axes(self):
    registers = {}
    encodedAxes = 0
    self.g.FindAxesMinimums(registers, '')
    self.inputstream.seek(0)
    packet = self.d.ParseNextPacket()
    self.assertEqual(packet[0], s3g.host_action_command_dict['FIND_AXES_MINIMUMS'])
    self.assertEqual(packet[1], encodedAxes)

  def test_send_g161_command(self):
    command = "G161"
    

class s3gInterfaceTestsDEPRECATED():
  def setUp(self):
    self.sm = s3g.GcodeStateMachine()
    self.inputstream = io.BytesIO()

    self.r = s3g.s3g()
    self.r.writer = s3g.FileWriter(self.inputstream)

    self.d = s3g.s3gStreamDecoder.s3gStreamDecoder()
    self.d.file = self.inputstream
    self.sm.s3g = self.r

  def tearDown(self):
    self.sm = None
    self.r = None
    self.d = None
    self.inputstream = None
    self.outputstream = None

  def test_lose_position(self):
    for key in self.sm.position:
      self.sm.position[key] = 0
    codes = {'X':True, 'Y':True, 'Z':True, 'A':True, 'B':True}
    self.sm.LosePosition(codes)
    for key in self.sm.position:
      self.assertTrue(self.sm.position[key] == None)

  def test_lose_position_no_codes(self):
    for key in self.sm.position:
      self.sm.position[key] = 0
    codes = {}
    self.sm.LosePosition(codes)
    for key in self.sm.position:
      self.assertTrue(self.sm.position[key] == 0)

  def test_lose_position_nonflagged_codes(self):
    for key in self.sm.position:
      self.sm.position[key] = 0
    codes = {'X':1, 'Y':2, 'Z':3, 'A':4, 'B':5}
    self.sm.LosePosition(codes)
    for key in self.sm.position:
      self.assertTrue(self.sm.position[key] == None)
  
  def test_get_point(self):
    self.sm.position={
                      'X' : 1,
                      'Y' : 2,
                      'Z' : 3,
                      }
    self.assertEqual([1, 2, 3], self.sm.GetPoint())

  def test_get_extended_point(self):
    self.sm.position={
                      'X' : 1,
                      'Y' : 2,
                      'Z' : 3,
                      'A' : 4,
                      'B' : 5,
                      }
    self.assertEqual([1, 2, 3, 4, 5], self.sm.GetExtendedPoint())

  def test_MockS3g(self):
    b = bytearray()
    b.append('\x00')
    self.r.SendPacket(b)
    readBytes = bytearray(self.inputstream.getvalue())
    self.assertEqual(b, readBytes)

  def test_rapid_positioning(self):
    command = "G0 X1 Y2 Z3"
    self.toolhead = 0
    self.sm.ExecuteLine(command)
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPacket()
    self.assertEqual(readPayload[2], s3g.host_action_command_dict['QUEUE_POINT'])

  def test_linear_interpolation(self):
    command = 'G1 X1 Y2 Z3 F500'
    self.sm.ExecuteLine(command)
    self.inputstream.seek(0)
    readPayload = self.d.ParseNextPacket()
    self.assertEqual(readPayload[2], s3g.host_action_command_dict['QUEUE_EXTENDED_POINT'])

  def test_dwell_enabled(self):
    self.sm.toolhead_enabled = True
    self.sm.toolhead = 0
    self.sm.toolhead_speed = 50
    command = "G4 P10"
    startTime = time.time()
    self.sm.ExecuteLine(command)
    finalTime = time.time()
    self.assertAlmostEqual(finalTime-startTime, 0)
    self.inputstream.seek(0)
    packets = self.d.ReadStream()
    for packet in packets:
      self.assertEqual(packet[2], s3g.host_action_command_dict['QUEUE_EXTENDED_POINT'])

  def test_dwell_disabled(self):
    self.sm.toolhead_enabled = False
    command = "G4 P10"
    microConstant = 1000000
    miliConstant = 1000
    self.sm.ExecuteLine(command)
    self.inputstream.seek(0)
    readPacket = self.d.ParseNextPacket()
    self.assertEqual(readPacket[2], s3g.host_action_command_dict['DELAY'])

  def test_position_code(self):
    command = "G92 X1 Y2 Z3 A4 B5"
    self.toolhead = 0
    self.sm.ExecuteLine(command)
    self.inputstream.seek(0)
    readPacket = self.d.ParseNextPacket()
    self.assertEqual({"X":1,"Y":2,"Z":3,"A":4,"B":5}, self.sm.position)
    self.assertEqual(readPacket[2], s3g.host_action_command_dict['SET_EXTENDED_POSITION'])
    self.assertEqual(readPacket[3:8], [1, 2, 3, 4, 5])

  def test_set_potentiometer_values(self):
    potVals = "X100 Y99 Z98 A97 B96"
    encodings = {
        s3g.EncodeAxes('x') : 100,
        s3g.EncodeAxes('y') : 99,
        s3g.EncodeAxes('z') : 98,
        s3g.EncodeAxes('a') : 97,
        s3g.EncodeAxes('b') : 96,
        }
    command = 'G130 ' + potVals
    self.sm.ExecuteLine(command)
    self.inputstream.seek(0)
    packets = self.d.ReadStream()
    for packet in packets:
      self.assertEqual(packet[2], s3g.host_action_command_dict['SET_POT_VALUE'])
      self.assertTrue(packet[3] in encodings.keys())
      self.assertEqual(packet[4], encodings[packet[3]])
     
  def test_find_axes_minimums(self):
    feedrate = 500
    axes = ['X', 'Y', 'Z']
    encodedAxes = [axis.lower() for axis in axes]
    command = "G161 X Y Z F500"
    self.sm.ExecuteLine(command)
    self.inputstream.seek(0)
    packet = self.d.ParseNextPacket()
    self.assertEqual(packet[2], s3g.host_action_command_dict['FIND_AXES_MINIMUMS'])
    self.assertEqual(packet[3], encodedAxes)
    self.assertEqual(packet[4], feedrate)
    self.assertEqual(packet[5], self.sm.findingTimeout)
 
class StateMachineTestsDEPRECATED():
  def setUp(self):
    self.sm = s3g.GcodeStateMachine()
    self.r = s3g.s3g()

    self.r.file = io.BytesIO()
    self.sm.s3g = self.r

  def tearDown(self):
    self.sm = None

  def test_parse_out_axes(self):
    codes = {
        "A" : 1,
        "B" : 2,
        "C" : 3,
        "D" : 4,
        "E" : 5,
        "X" : 6,
        "Y" : 7,
        }
    for axis in ['A', 'B', 'X', 'Y']:
      self.assertTrue(axis in self.sm.ParseOutAxes(codes))

  def test_set_position(self):
    for key in self.sm.position:
      self.sm.position[key] = 0
    setPos = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        'A' : 4,
        'B' : 5,
        }
    self.sm.SetPosition(setPos)
    self.assertEqual(setPos, self.sm.position)

  def test_set_position_flagged_reg(self):
    for key in self.sm.position:
      self.sm.position[key] = 0
    setPos = {
        'X' : True,
        'Y' : 2,
        'Z' : 3,
        'A' : 4,
        'B' : 5,
        }
    self.sm.SetPosition(setPos)
    self.assertEqual({'X':0, 'Y':2, 'Z':3, 'A':4, 'B':5}, self.sm.position)

  def test_apply_offset(self):
    self.sm.position = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        'A' : 4,
        'B' : 5,
        }
    self.sm.offsetPosition[0] = {
        'X' : 10,
        'Y' : 11,
        'Z' : 12,
        }
    interpolatedPos = {}
    for key in self.sm.position:
      if key in self.sm.offsetPosition[0]:
        interpolatedPos[key] = self.sm.position[key] + self.sm.offsetPosition[0][key]
      else:
        interpolatedPos[key] = self.sm.position[key]
    self.sm.toolhead = 0
    self.sm.ApplyNeededOffsetsToPosition()
    self.assertEqual(interpolatedPos, self.sm.position)

  def test_apply_needed_offset_no_offset_set(self):
    self.sm.position = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        'A' : 4,
        'B' : 5, 
        }
    self.sm.offsetPosition = {}
    self.sm.toolhead = 0
    self.assertRaises(KeyError, self.sm.ApplyNeededOffsetsToPosition)

  def test_apply_needed_offset_no_toolhead(self):
    self.sm.position = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        'A' : 4,
        'B' : 5,
        }
    self.sm.offsetPosition = {
        'X' : 100,
        'Y' : 200,
        'Z' : 300,
        }
    self.sm.ApplyNeededOffsetsToPosition()
    self.assertEqual({'X':1, 'Y':2, 'Z':3, 'A':4, 'B':5}, self.sm.position)
 
  def test_set_offsets(self):
    codes = {'X':1, 'Y':2, 'Z':3,'P':0}
    self.sm.SetOffsets(codes)
    self.assertTrue(self.sm.offsetPosition[0] != None)
    self.assertEqual(self.sm.offsetPosition[0], {'X':1,'Y':2,'Z':3})

  def test_set_offsets_flagged_p(self):
    codes = {'X':1,'Y':2,'Z':3,'P':True}
    self.assertRaises(s3g.InvalidRegisterError, self.sm.SetOffsets,codes)

  def test_set_offsets_missing_p(self):
    codes = {'X':1, 'Y':2, 'Z':3}
    self.assertRaises(s3g.MissingRegisterError, self.sm.SetOffsets, codes)

  def test_set_offsets_missing_codes(self):
    codes = {'P':1}
    self.sm.SetOffsets(codes)
    self.assertEqual(self.sm.offsetPositions[1], {})
     
  def test_g0_state_no_tool_offset(self):
    command = 'G0 X1 Y2 Z3'
    self.sm.ExecuteLine(command)
    self.assertEqual({'X':1, 'Y':2, 'Z':3, 'A':0, 'B':0}, self.sm.position)

  def test_g0_state_tool_offset(self):
    command = 'G0 X1 Y2 Z3'
    self.sm.toolhead = 0
    self.sm.offsetPosition[0] = {}
    self.sm.offsetPosition[0]['X'] = 1
    self.sm.offsetPosition[0]['Y'] = 2
    self.sm.offsetPosition[0]['Z'] = 3
    self.sm.ExecuteLine(command)
    self.assertEqual({'X':2, 'Y':4, 'Z':6, 'A':0, 'B':0}, self.sm.position)

  def test_g1_state_a_b(self):
    command = 'G1 X1 Y2 Z3 A4 B5'
    self.sm.ExecuteLine(command)
    self.assertEqual({'X':1,'Y':2,'Z':3,'A':4,'B':5}, self.sm.position)

  def test_g1_state_e(self):
    expectedPoint = {'X':1, 'Y':2, 'Z':3}
    command = "G1 X1 Y2 Z3 E42"
    self.sm.ExecuteLine(command)
    self.assertEqual(42, self.sm.toolhead_speed)
    for axis in ['X', 'Y', 'Z']:
      self.assertEqual(expectedPoint[axis], self.sm.position[axis])
 
  def test_g1_state_e_a_b(self):
    command = "G1 E42 A1 B2"
    self.assertRaises(s3g.LinearInterpolationError, self.sm.ExecuteLine, command)

  def test_g1_state_no_a_b_e(self):
    command = "G1 X1 Y2 Z3"
    for key in self.sm.position:
      self.sm.position[key] = 0
    self.sm.ExecuteLine(command)
    self.assertEqual({'X':1, 'Y':2, 'Z':3, 'A':0, 'B':0}, self.sm.position)

  def test_g1_state_no_a_b_e_no_codes_defined(self):
    command = "G1 X1 Y2 Z3"
    for key in self.sm.position:
      self.sm.position[key] = 0
    self.sm.toolhead = 0
    self.assertRaises(KeyError, self.sm.ExecuteLine, command)

  def test_g10_state_state(self):
    command = 'G10 X1 Y2 Z3 P1'
    self.sm.ExecuteLine(command)
    self.assertEqual({'X':1,'Y':2,'Z':3}, self.sm.offsetPosition[1])

  def test_g10_state_no_p(self):
    command = 'G10 X1 Y2 Z3'
    self.assertRaises(s3g.MissingRegisterError, self.sm.ExecuteLine, command)

  def test_g10_state_undefined_p(self):
    command = 'G10 X1 Y2 Z3 P'
    self.assertRaises(s3g.InvalidRegisterError, self.sm.ExecuteLine, command)

  def test_g10_state_only_p(self):
    command = 'G10 P1'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.offsetPosition[1], {})

  def test_g54_state(self):
    command = 'G54'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead, 0)

  def test_g54_state_extra_codes(self):
    command = 'G54 X5 Y1 P51'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead, 0)

  def test_g55_state(self):
    command = 'G55'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead, 1)

  def test_g55_state_extra_codes(self):
    command = 'G55 X5 Y1 P51'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead, 1)

  def test_g161_state(self):
    command = 'G161 Z X Y A B'
    self.sm.ExecuteLine(command)
    for key in self.sm.position:
      self.assertTrue(self.sm.position[key] == None)

  def test_g161_state_no_flags(self):
    command = 'G161'
    for key in self.sm.position:
      self.sm.position[key] = 0
    self.sm.ExecuteLine(command)
    for key in self.sm.position:
      self.assertEqual(0, self.sm.position[key])

  def test_g162_state(self):
    command = 'G162 X Y Z A B'
    self.sm.ExecuteLine(command)
    for key in self.sm.position:
      self.assertTrue(self.sm.position[key] == None)

  def test_g162_state_no_flags(self):
    command = 'G162'
    for key in self.sm.position:
      self.sm.position[key] = 0
    self.sm.ExecuteLine(command)
    for key in self.sm.position:
      self.assertEqual(0, self.sm.position[key])

  def test_m101_state(self):
    command = 'M101'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead_enabled, True)
    self.assertEqual(self.sm.toolhead_direction, True)

  def test_m102_state_extra_codes(self):
    command = 'M101 A12'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead_enabled, True)
    self.assertEqual(self.sm.toolhead_direction, True)

  def test_m102_state(self):
    command = 'M102'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead_enabled, True)
    self.assertEqual(self.sm.toolhead_direction, False)

  def test_m102_state_extra_codes(self):
    command = 'M102 A12'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead_enabled, True)
    self.assertEqual(self.sm.toolhead_direction, False)

  def test_m103_state(self):
    command = 'M103'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead_enabled, False)

  def test_m108_state(self):
    command = 'M108 R42'
    self.sm.ExecuteLine(command)
    self.assertEqual(self.sm.toolhead_speed, 42)

  def test_m108_state_flagged_r(self):
    command = 'M108 R'
    self.assertRaises(s3g.InvalidRegisterError, self.sm.ExecuteLine, command)

  def test_m108_state_missing_r(self): 
    command = 'M108'
    self.assertRaises(s3g.MissingRegisterError, self.sm.ExecuteLine, command)

  def test_m132_state(self):
    for key in self.sm.position:
      self.sm.position[key] = 0
    command = 'M132 X Y Z'
    self.sm.ExecuteLine(command)
    self.assertEqual({'X':None, 'Y':None, 'Z':None, 'A':0, 'B':0}, self.sm.position)

class ParseSampleGcodeFileTests(unittest.TestCase):
  """
  Run the parser across all of the sample gcode files, to verify that no assertions
  are thrown
  """
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
