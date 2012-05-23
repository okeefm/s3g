import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import struct
import array

import s3g


class s3gStreamDecoderTests(unittest.TestCase):
  def setUp(self):
    self.r = s3g.s3g()
    self.outputstream = io.BytesIO() # Stream that we will send responses on
    self.inputstream = io.BytesIO()
    file = io.BufferedRWPair(self.outputstream, self.inputstream)
    self.r.writer = s3g.StreamWriter(file)

    self.d = s3g.s3gStreamDecoder.s3gStreamDecoder()
    self.d.file = self.inputstream

  def tearDown(self):
    self.r = None
    self.d = None

  def test_PackagePacket(self):
    a = 'a'
    b = 'b'
    l = [1, 2, 3, 4]
    c = 'c'
    expectedPackaged = ['a', 'b', 1, 2, 3, 4, 'c']
    packaged = self.d.PackagePacket('a', 'b', l, 'c')
    self.assertEqual(expectedPackaged, packaged)
  
  def test_GetCommandFormat(self):
    cases = {
        129: ['i', 'i', 'i', 'i'],
        130: ['i', 'i', 'i'],
        131: ['B', 'I', 'H'],
        }
    for case in cases:
      formatString = s3g.commandFormats[case]
      self.assertEqual(formatString, cases[case])

  def test_GetBytes(self):
    val = 42
    encodedVal = s3g.EncodeUint32(val)
    payload = bytearray()
    payload.extend(encodedVal)
    self.inputstream.write(payload)
    self.inputstream.seek(0)
    readVal = self.d.GetBytes('I')
    self.assertEqual(readVal, encodedVal) 

  def test_GetStringBytesPathological(self):
    b = bytearray()
    for i in range(s3g.constants.maximum_payload_length):
      b.append('a')
    b.append('\x00')
    self.inputstream.write(b)
    self.inputstream.seek(0)
    self.assertRaises(s3g.errors.StringTooLongError, self.d.GetStringBytes)

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
    cmd = s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW']
    point = [1, 2, 3, 4, 5]
    duration = 42
    relativeAxes = 0
    expectedPayload = bytearray()
    s3g.coding.AddObjToPayload(expectedPayload, [[s3g.coding.EncodeInt32(cor) for cor in point], s3g.coding.EncodeUint32(duration), relativeAxes])
    self.inputstream.write(expectedPayload)
    self.inputstream.seek(0)
    info = self.d.ParseOutParameters(cmd)
    self.assertEqual(expectedPayload[0:4], s3g.coding.EncodeInt32(info[0]))
    self.assertEqual(expectedPayload[4:8], s3g.coding.EncodeInt32(info[1]))
    self.assertEqual(expectedPayload[8:12], s3g.coding.EncodeInt32(info[2]))
    self.assertEqual(expectedPayload[12:16], s3g.coding.EncodeInt32(info[3]))
    self.assertEqual(expectedPayload[16:20], s3g.coding.EncodeInt32(info[4]))
    self.assertEqual(expectedPayload[20:24], s3g.coding.EncodeUint32(info[5]))
    self.assertEqual(expectedPayload[24], info[6])
 
  def test_ParseOutParametersToolAction(self):
    cmd = s3g.host_action_command_dict['TOOL_ACTION_COMMAND']
    tool_index = 0
    toolCmd = s3g.slave_action_command_dict['SET_SERVO_1_POSITION']
    length = 1
    theta = 10
    payload = bytearray()
    s3g.coding.AddObjToPayload(payload, [cmd, tool_index, toolCmd, length, theta])
    self.inputstream.write(payload)
    self.inputstream.seek(1)
    info = self.d.ParseOutParameters(s3g.host_action_command_dict['TOOL_ACTION_COMMAND'])
    self.assertEqual(info[0], tool_index)
    self.assertEqual(info[1], toolCmd)
    self.assertEqual(info[2], length)
    self.assertEqual(info[3], theta)
    
  def test_ParseParameter(self):
    cases = [
    [256, s3g.EncodeUint32(256), '<i'],
    ['asdf', array.array('B', 'asdf'),  '<4s'],
    ['asdf', array.array('B', 'asdf\x00'), '<5s'],
    ]
    for case in cases:
      self.assertEqual(case[0], self.d.ParseParameter(case[2], case[1]))

  def test_GetNextCommand(self):
    cmd = s3g.host_query_command_dict['INIT']
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.r.Init()
    self.inputstream.seek(2) #Get around first two bytes of the packet, since we only want to check the command
    readCmd = self.d.GetNextCommand()
    self.assertEqual(readCmd, cmd)

  def test_ParseNextPayload(self):
    cmd = s3g.host_action_command_dict['BUILD_START_NOTIFICATION']
    commandCount = 1
    buildName = "test"
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.r.BuildStartNotification(commandCount, buildName)
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
    s3g.coding.AddObjToPayload(payload, [cmd, [s3g.EncodeInt32(cor) for cor in point], s3g.EncodeUint32(duration), relativeAxes])
    crc = s3g.CalculateCRC(payload)
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.r.QueueExtendedPointNew(
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


  def test_ReadStream(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    point = [1, 2, 3, 4, 5]
    duration = 42
    relativeAxes = 0
    self.outputstream.seek(0)
    self.r.QueueExtendedPointNew(point, duration, [])
    self.outputstream.seek(0)
    self.r.SetExtendedPosition(point)
    self.outputstream.seek(0)
    self.r.SetPosition(point[:3])
    self.inputstream.seek(0)
    packets = self.d.ReadStream()
    cmdNumbers = [
        s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW'], 
        s3g.host_action_command_dict['SET_EXTENDED_POSITION'], 
        s3g.host_action_command_dict['SET_POSITION']
        ]
    for readCmd, cmd in zip([packets[0][2], packets[1][2], packets[2][2]], cmdNumbers):
      self.assertEqual(readCmd, cmd)

if __name__ == "__main__":
  unittest.main()
