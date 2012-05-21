import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io

import array

import s3g

class s3gStreamDecoderRawTests(unittest.TestCase):
  def setUp(self):
    self.r = s3g.s3g()
    self.outputstream = io.BytesIO() # Stream that we will send responses on
    self.inputstream = io.BytesIO()  # Stream that we will receive commands on
    self.file = io.BufferedRWPair(self.outputstream, self.inputstream)
    self.r.file = self.file
    self.d = s3g.s3gStreamDecoderRaw()
    self.d.file = self.inputstream

  def tearDown(self):
    self.r = None
    self.d = None
    self.outputstream = None
    self.inputstream = None

  def test_PackagePacket(self):
    a = bytearray()
    a.append('a')
    b = bytearray()
    b.append('b')
    l = bytearray()
    for i in [1, 2, 3, 4]:
      l.append(i)
    c = bytearray()
    c.append('c')
    expectedPackage = bytearray()
    for val in ['a', 'b', 1, 2, 3, 4, 'c']:
      expectedPackage.append(val)
    packaged = self.d.PackagePacket(a, b, l, c)
    self.assertEqual(expectedPackage, packaged)

  def test_GetCommandFormat(self):
    expectedFormatString = ['i', 'i', 'i', 'i']
    cmd = bytearray()
    cmd.append('\x81')
    formatString = self.d.GetCommandFormat(cmd)
    self.assertEqual(expectedFormatString, formatString)

  def test_ParseParameter(self):
    b = bytearray()
    b.extend('asdf')
    b.append('\x00')
    a = array.array('B', b)
    returnBytes = self.d.ParseParameter('<5s', a)
    self.assertEqual(returnBytes, b)

  def test_ParseNextPacket(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.r.QueueExtendedPointNew([1, 2, 3, 4, 5], 42, ['x', 'z'])
    readPacket = self.inputstream.getvalue()
    self.inputstream.seek(0)
    self.assertEqual(readPacket, self.d.ParseNextPacket())
   
  def test_MultiplePackets(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.r.QueueExtendedPointNew([1, 2, 3, 4, 5], 42, ['x', 'y'])
    self.outputstream.seek(0)
    self.r.SetExtendedPosition([1, 2, 3, 4, 5])
    self.outputstream.seek(0)
    self.r.SetPosition([1, 2, 3])
    self.inputstream.seek(0)
    expectedBytes = self.inputstream.getvalue()
    readBytes = self.d.ReadStream()
    collatedBytes = bytearray()
    for r in readBytes:
      collatedBytes.extend(r)
    self.assertEqual(expectedBytes, collatedBytes)

if __name__ == "__main__":
  unittest.main()
