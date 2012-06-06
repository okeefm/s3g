import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io

import array

import s3g

class fileReaderRawTests(unittest.TestCase):
  def setUp(self):
    self.r = s3g.s3g()
    self.outputstream = io.BytesIO() # Stream that we will send responses on
    self.inputstream = io.BytesIO()  # Stream that we will receive commands on

    file = io.BufferedRWPair(self.outputstream, self.inputstream)
    self.r.writer = s3g.StreamWriter(file)

    self.d = s3g.FileReaderRaw()
    self.d.file = self.inputstream

  def tearDown(self):
    self.r = None
    self.d = None
    self.outputstream = None
    self.inputstream = None


#  def test_ParseNextPacket(self):
#    response_payload = bytearray()
#    response_payload.append(s3g.response_code_dict['SUCCESS'])
#    self.outputstream.write(s3g.EncodePayload(response_payload))
#    self.outputstream.seek(0)
#    self.r.QueueExtendedPointNew([1, 2, 3, 4, 5], 42, ['x', 'z'])
#    readPacket = self.inputstream.getvalue()
#    self.inputstream.seek(0)
#    self.assertEqual(readPacket, self.d.ParseNextPacket())
   
#  def test_MultiplePackets(self):
#    response_payload = bytearray()
#    response_payload.append(s3g.response_code_dict['SUCCESS'])
#    self.outputstream.write(s3g.EncodePayload(response_payload))
#    self.outputstream.seek(0)
#    self.r.QueueExtendedPointNew([1, 2, 3, 4, 5], 42, ['x', 'y'])
#    self.outputstream.seek(0)
#    self.r.SetExtendedPosition([1, 2, 3, 4, 5])
#    self.outputstream.seek(0)
#    self.r.SetPosition([1, 2, 3])
#    self.inputstream.seek(0)
#    expectedBytes = self.inputstream.getvalue()
#    readBytes = self.d.ReadFile()
#    collatedBytes = bytearray()
#    for r in readBytes:
#      collatedBytes.extend(r)
#    self.assertEqual(expectedBytes, collatedBytes)

if __name__ == "__main__":
  unittest.main()
