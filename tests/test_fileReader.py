import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import struct
import array

import s3g

class FileReaderTests_2(unittest.TestCase):
  def setUp(self):
    self.d = s3g.FileReader()

    self.inputstream = io.BytesIO()
    self.d.file = self.inputstream

  def tearDown(self):
    self.r = None
    self.d = None

  def test_ReadBytes_zero_data(self):
    self.d.ReadBytes(0)

  def test_ReadBytes_too_little_data(self):
    self.assertRaises(s3g.EndOfFileError, self.d.ReadBytes, 1)

  def test_ReadBytes_enough_data(self):
    data = '1234567890'
    self.inputstream.write(data)
    self.inputstream.seek(0)
    assert data == self.d.ReadBytes(len(data))

  def test_GetNextCommand_bad_command(self):
    command = 0xFF # Assume that 0xff is not a valid command

    self.inputstream.write(chr(command))
    self.inputstream.seek(0)

    self.assertRaises(s3g.BadCommandError, self.d.GetNextCommand)

  def test_GetNextCommand_host_action_command(self):
    command = s3g.host_action_command_dict['QUEUE_POINT']

    self.inputstream.write(chr(command))
    self.inputstream.seek(0)

    self.assertEquals(command, self.d.GetNextCommand())

  def test_GetNextCommand_slave_action_command(self):
    command = s3g.slave_action_command_dict['SET_TOOLHEAD_TARGET_TEMP']

    self.inputstream.write(chr(command))
    self.inputstream.seek(0)

    self.assertEquals(command, self.d.GetNextCommand())

class FileReaderTests(unittest.TestCase):
  def setUp(self):
    self.r = s3g.s3g()
    self.inputstream = io.BytesIO() # File that we will send responses on

    self.r.writer = s3g.FileWriter(self.inputstream)

    self.d = s3g.FileReader()
    self.d.file = self.inputstream

  def tearDown(self):
    self.r = None
    self.d = None

#  def test_PackagePacket(self):
#    a = 'a'
#    b = 'b'
#    l = [1, 2, 3, 4]
#    c = 'c'
#    expectedPackaged = ['a', 'b', 1, 2, 3, 4, 'c']
#    packaged = self.d.PackagePacket('a', 'b', l, 'c')
#    self.assertEqual(expectedPackaged, packaged)
  
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
    data = 'abcd'

    payload = bytearray()
    payload.extend(data)
    self.inputstream.write(payload)
    self.inputstream.seek(0)

    readVal = self.d.GetBytes('I')
    self.assertEqual(readVal, data)

  def test_GetStringBytesPathological(self):
    b = bytearray()
    for i in range(s3g.constants.maximum_payload_length):
      b.append('a')
    b.append('\x00')
    self.inputstream.write(b)
    self.inputstream.seek(0)
    self.assertRaises(s3g.StringTooLongError, self.d.GetStringBytes)

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

  def test_ParseNextPayload(self):
    cmd = s3g.host_action_command_dict['BUILD_START_NOTIFICATION']
    commandCount = 1
    buildName = "test"

    self.r.BuildStartNotification(commandCount, buildName)
    self.inputstream.seek(0)

    info = self.d.ParseNextPayload()
    self.assertEqual(info[0], cmd)
    self.assertEqual(info[1], commandCount)
    self.assertEqual(info[2], buildName)
    
#  def test_ParseNextPacket(self):
#    cmd = s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW']
#    point = [1, 2, 3, 4, 5]
#    duration = 42
#    relativeAxes = 0x01 + 0x02
#
#    payload = bytearray()
#    s3g.coding.AddObjToPayload(payload, [cmd, [s3g.EncodeInt32(cor) for cor in point], s3g.EncodeUint32(duration), relativeAxes])
#    crc = s3g.CalculateCRC(payload)
#
#    self.r.QueueExtendedPointNew(
#        point, 
#        duration, 
#        ['x', 'y']
#        )
#    self.outputstream.seek(0)
#
#    readPacket = self.d.ParseNextPacket()
#
#    self.assertEqual(readPacket[0], s3g.header)
#    self.assertEqual(readPacket[1], len(payload))
#    self.assertEqual(readPacket[2], s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW'])
#    for i in range(5):
#      self.assertEqual(readPacket[3+i], point[i])
#    self.assertEqual(readPacket[8], duration)
#    self.assertEqual(readPacket[9], relativeAxes)
#    self.assertEqual(readPacket[10], crc)


  def test_ReadFile(self):
    point = [1, 2, 3, 4, 5]
    duration = 42
    relativeAxes = 0

    self.r.QueueExtendedPointNew(point, duration, [])
    self.r.SetExtendedPosition(point)
    self.r.SetPosition(point[:3])
    self.inputstream.seek(0)

    payloads = self.d.ReadFile()
    cmdNumbers = [
        s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW'], 
        s3g.host_action_command_dict['SET_EXTENDED_POSITION'], 
        s3g.host_action_command_dict['SET_POSITION']
        ]

    for readCmd, cmd in zip([payloads[0][0], payloads[1][0], payloads[2][0]], cmdNumbers):
      self.assertEqual(readCmd, cmd)

if __name__ == "__main__":
  unittest.main()
