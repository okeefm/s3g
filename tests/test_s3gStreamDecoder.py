import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import struct
import array

import s3g


class DecoderTests(unittest.TestCase):
  def setUp(self):
    self.d = s3g.s3gStreamDecoder()
    self.outputstream = io.BytesIO() # Stream that we will send responses on
    self.inputstream = io.BytesIO()
    self.d.file = self.inputstream
    self.file = io.BufferedRWPair(self.outputstream, self.inputstream)
    self.s = s3g.s3g()
    self.s.file = self.file

  def tearDown(self):
    self.d = None

  def test_GetBytes(self):
    val = 42
    encodedVal = s3g.EncodeUint32(val)
    payload = bytearray()
    payload.extend(encodedVal)
    self.inputstream.write(payload)
    self.inputstream.seek(0)
    readVal = self.d.GetBytes('I')
    self.assertEqual(struct.unpack('<I',readVal)[0], val) 

  def test_GetStringBytes(self):
    val = 'asdf'
    payload = bytearray()
    payload.extend(val)
    payload.append('\x00')
    self.inputstream.write(payload)
    self.inputstream.seek(0)
    readVal = self.d.GetStringBytes()
    self.assertEqual(readVal, val+'\x00')
    
  def test_ParseOutParameters(self):
    cmd = s3g.host_action_command_dict['TOOL_ACTION_COMMAND']
    tool_index = 0
    toolCmd = s3g.slave_action_command_dict['SET_SERVO_1_POSITION']
    length = 1
    theta = 10
    payload = bytearray()
    self.s.AddObjToPayload(payload, [cmd, tool_index, toolCmd, length, theta])
    self.inputstream.write(payload)
    self.inputstream.seek(1)
    info = self.d.ParseOutParameters(s3g.host_action_command_dict['TOOL_ACTION_COMMAND'])
    self.assertEqual(info[0], tool_index)
    self.assertEqual(info[1], toolCmd)
    self.assertEqual(info[2], length)
    self.assertEqual(info[3], theta)
    
  def test_returnParam(self):
    cases = [
    [256, s3g.EncodeUint32(256), '<i'],
    ['asdf', array.array('B', 'asdf'),  '<4s']
    ]
    for case in cases:
      self.assertEqual(case[0], self.d.parseParameter(case[2], case[1]))

  def test_GetNextCommand(self):
    cmd = s3g.host_query_command_dict['INIT']
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.s.Init()
    self.inputstream.seek(2, 0) #Get around first two bytes of the packet, since we only want to check the command
    readCmd = self.d.GetNextCommand()
    self.assertEqual(readCmd, cmd)

  def test_ParseNextPayloadBuildStart(self):
    cmd = s3g.host_action_command_dict['BUILD_START_NOTIFICATION']
    commandCount = 1
    buildName = "test"
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.s.BuildStartNotification(commandCount, buildName)
    self.inputstream.seek(2)
    info = self.d.ParseNextPayload()
    self.assertEqual(info[0], cmd)
    self.assertEqual(info[1], commandCount)
    self.assertEqual(info[2], buildName)
    
  def test_ParseNextPacket(self):
    cmd = s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW']
    point = [1, 2, 3, 4, 5]
    duration = 42
    relativeAxes = 0x01 + 0x02
    payload =bytearray()
    self.s.AddObjToPayload(payload, [cmd, [s3g.EncodeInt32(cor) for cor in point], s3g.EncodeUint32(duration), relativeAxes])
    crc = s3g.CalculateCRC(payload)
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.s.QueueExtendedPointNew(
        point, 
        duration, 
        ['x', 'y']
        )
    self.inputstream.seek(0)
    readPacket = self.d.ParseNextPacket()
    self.assertEqual(readPacket[0], s3g.header)
    self.assertEqual(readPacket[1], len(payload))
    self.assertEqual(readPacket[2], s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW'])
    for i in range(5):
      self.assertEqual(readPacket[3+i], point[i])
    self.assertEqual(readPacket[8], duration)
    self.assertEqual(readPacket[9], relativeAxes)
    self.assertEqual(readPacket[10], crc)

    

if __name__ == "__main__":
  unittest.main()
