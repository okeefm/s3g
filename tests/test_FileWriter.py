import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io

import s3g


class s3gFileWriterTests(unittest.TestCase):
  def setUp(self):

    self.inputstream = io.BytesIO()
    self.w = s3g.FileWriter(self.inputstream)

  def tearDown(self):
    self.w = None
    self.inputstream = None

  def test_build_and_send_query_packet_not_implemented(self):
    self.assertRaises(NotImplementedError, self.w.BuildAndSendQueryPayload, [42])

  def test_build_and_send_action_payload(self):
    data = 'abcde'
    expected_payload = s3g.BuildPayload(data)

    self.w.BuildAndSendActionPayload(data)

    self.inputstream.seek(0)
    payload = self.inputstream.getvalue()
    assert payload == expected_payload

if __name__ == "__main__":
  unittest.main()
