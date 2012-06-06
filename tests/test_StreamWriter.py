import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import io
import struct
import unittest

import s3g

class StreamWriterTests(unittest.TestCase):
  def setUp(self):
    self.outputstream = io.BytesIO() # Stream that we will send responses on
    self.inputstream = io.BytesIO()  # Stream that we will receive commands on

    file = io.BufferedRWPair(self.outputstream, self.inputstream)
    self.w = s3g.StreamWriter(file)

  def tearDown(self):
    self.w = None

  def test_send_command(self):
    """
    Passing case: Preload the buffer with a correctly formatted expected response, and verigy that it works correctly
    """
    payload = 'abcde'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend('12345')
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertEqual(response_payload, self.w.SendCommand(payload))
    self.assertEqual(s3g.EncodePayload(payload), self.inputstream.getvalue())

  def test_send_packet_timeout(self):
    """
    Time out when no data is received. The input stream should have max_rety_count copies of the
    payload packet in it.
    """
    payload = 'abcde'
    packet = s3g.EncodePayload(payload)
    expected_packet = s3g.EncodePayload(payload)

    self.assertRaises(s3g.TransmissionError,self.w.SendPacket, packet)

    self.inputstream.seek(0)
    for i in range (0, s3g.max_retry_count):
      for byte in expected_packet:
        self.assertEquals(byte, ord(self.inputstream.read(1)))

  def test_send_packet_many_bad_responses(self):
    """
    Passing case: test that the transmission can recover from one less than the alloted
    number of errors.
    """
    payload = 'abcde'
    packet = s3g.EncodePayload(payload)
    expected_packet = s3g.EncodePayload(payload)

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend('12345')

    for i in range (0, s3g.max_retry_count - 1):
      self.outputstream.write('a')
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertEquals(response_payload, self.w.SendPacket(packet))

    self.inputstream.seek(0)
    for i in range (0, s3g.max_retry_count - 1):
      for byte in expected_packet:
        self.assertEquals(byte, ord(self.inputstream.read(1)))

  def test_send_packet(self):
    """
    Passing case: Preload the buffer with a correctly formatted expected response, and
    verify that it works correctly.
    """
    payload = 'abcde'
    packet = s3g.EncodePayload(payload)
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend('12345')
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertEquals(response_payload, self.w.SendPacket(packet))
    self.assertEquals(s3g.EncodePayload(payload), self.inputstream.getvalue())

  # TODO: Test timing based errors- can we send half a response, get it to re-send, then send a regular response?

  def test_build_and_send_action_payload(self):
    command = s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW']
    point = [1, 2, 3, 4, 5]
    duration = 42
    relativeAxes = 0
    expected_payload = struct.pack(
      '<BiiiiiIB',
      command,
      point[0], point[1], point[2], point[3], point[4],
      duration,
      relativeAxes
    )

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    payload = struct.pack(
      '<BiiiiiIB',
      command,
      point[0], point[1], point[2], point[3], point[4],
      duration,
      relativeAxes,
    )
      

    self.w.SendActionPayload(payload)

    self.assertEquals(s3g.EncodePayload(expected_payload), self.inputstream.getvalue())

  def test_build_and_send_query_payload_with_null_terminated_string(self):
    cmd = s3g.host_query_command_dict['GET_NEXT_FILENAME']
    flag = 0x01
    payload = struct.pack(
      '<BB',
      cmd,
      flag
    )
    filename = 'asdf\x00'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(s3g.sd_error_dict['SUCCESS'])
    response_payload.extend(filename)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    payload = struct.pack(
      '<bb',
      cmd,
      flag,
    )
    self.assertEqual(response_payload, self.w.SendQueryPayload(payload))

    self.assertEqual(s3g.EncodePayload(payload), self.inputstream.getvalue())
    

  def test_build_and_send_query_payload(self):
    cmd = s3g.host_query_command_dict['GET_VERSION']
    s3gVersion = 123
    botVersion = 456
    expected_payload = struct.pack(
      '<bH',
      cmd,
      s3gVersion
    )

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint16(botVersion))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    payload = struct.pack(
      '<bH',
      cmd,
      s3gVersion,
    )

    self.assertEquals(response_payload, self.w.SendQueryPayload(payload))
    self.assertEquals(s3g.EncodePayload(expected_payload), self.inputstream.getvalue())
    

if __name__ == "__main__":
  unittest.main()
