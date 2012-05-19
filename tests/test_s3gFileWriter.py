import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io

import s3g


class s3gFileWriterTests(unittest.TestCase):
  def setUp(self):
    self.r = s3g.s3gFileWriter()
    self.inputstream = io.BytesIO()
    self.r.file = self.inputstream

  def tearDown(self):
    self.r = None
    self.inputstream = None

  def test_build_and_send_query_packet(self):
    self.assertRaises(s3g.AttemptedQueryCommand, self.r.BuildAndSendQueryPayload, [42])

  def test_send_command(self):
    payload = bytearray()
    payload.append(s3g.header)
    payload.extend('12345')
    payload.append(0x00)
    self.r.SendCommand(payload)
    self.inputstream.seek(0)
    readPayload = self.inputstream.getvalue()
    self.assertEqual(payload, readPayload)

if __name__ == "__main__":
  unittest.main()
