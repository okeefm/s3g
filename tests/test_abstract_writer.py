import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
from s3g import Writer

class AbstractWriterTests(unittest.TestCase):
  """
  Emulate a machine
  """
  def setUp(self):
    self.w = Writer.AbstractWriter()


  def test_build_and_send_action_payload_raises(self):
    payload = ''
    self.assertRaises(NotImplementedError,self.w.SendActionPayload, payload)

  def test_build_and_send_query_payload_raises(self):
    payload = ''
    self.assertRaises(NotImplementedError,self.w.SendQueryPayload, payload)

if __name__ == "__main__":
  unittest.main()
