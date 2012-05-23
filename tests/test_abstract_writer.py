import unittest
import s3g

class AbstractWriterTests(unittest.TestCase):
  """
  Emulate a machine
  """
  def setUp(self):
    self.w = s3g.AbstractWriter()

  def test_build_and_send_action_payload_raises(self):
    self.assertRaises(NotImplementedError,self.w.BuildAndSendActionPayload)

  def test_build_and_send_query_payload_raises(self):
    self.assertRaises(NotImplementedError,self.w.BuildAndSendQueryPayload)

if __name__ == "__main__":
  unittest.main()
