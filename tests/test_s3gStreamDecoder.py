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
    self.file = self.outputstream
    self.d.file = self.file
    self.s = s3g.s3gFileWriter()
    self.s.file = self.file

  def tearDown(self):
    self.d = None

  def test_ReadByte(self):
    payload = bytearray('\x00\x01\x02')
    self.outputstream.write(payload)
    self.outputstream.seek(0)
    readVal = self.d.ReadBytes('BBB')
    self.assertEqual(readVal, struct.unpack('<BBB', array.array('B', payload)))

  def test_GetCommandParameters(self):
    point = (1, 2, 3, 4, 5)
    duration = 42
    relativeAxes = 0
    cmd = s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW']
    payload = bytearray()
    self.s.AddObjToPayload(payload, [cmd, [s3g.EncodeInt32(cor) for cor in point], s3g.EncodeUint32(duration), 0x00])
    self.outputstream.write(payload)
    self.outputstream.seek(0)
    command = self.outputstream.read(1)
    command = struct.unpack('<B', command)[0]
    params = self.d.GetCommandParameters(command)
    self.assertEqual(params[0:5], point)
    self.assertEqual(params[5], duration)
    self.assertEqual(params[6], relativeAxes)

  def test_GetNextCommandQueueExtendedPoint(self):
    point = [1, 2, 3, 4, 5]
    duration = 42
    relativeAxes = 0
    cmd = s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW']
    self.s.QueueExtendedPointNew(point, duration, [])
    self.outputstream.seek(0)
    info = self.d.GetNextCommand()
    self.assertEqual(info[0], cmd)
    self.assertEqual(info[1:6], point)
    self.assertEqual(info[6], duration)
    self.assertEqual(info[7], relativeAxes)

  def test_GetNextCommandBuildStart(self):
    commandCount = 1
    buildName = "test"
    self.s.BuildStartNotification(commandCount, buildName)
    self.outputstream.seek(0)
    info = self.d.GetNextCommand()
    self.assertEqual(info[0], commandCount)
    self.assertEqual(info[1], buildName)
    
    

if __name__ == "__main__":
  unittest.main()
