import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g
import unittest

class PacketEncodeTests(unittest.TestCase):
  def test_reject_oversize_payload(self):
    payload = bytearray()
    for i in range (0, s3g.maximum_payload_length + 1):
      payload.append(i)
    self.assertRaises(s3g.PacketLengthError,s3g.EncodePayload,payload)

  def test_packet_length(self):
    payload = 'abcd'
    packet = s3g.EncodePayload(payload)
    assert len(packet) == len(payload) + 3

  def test_packet_header(self):
    payload = 'abcd'
    packet = s3g.EncodePayload(payload)

    assert packet[0] == s3g.header

  def test_packet_length_field(self):
    payload = 'abcd'
    packet = s3g.EncodePayload(payload)
    assert packet[1] == len(payload)

  def test_packet_crc(self):
    payload = 'abcd'
    packet = s3g.EncodePayload(payload)
    assert packet[6] == s3g.CalculateCRC(payload);


class PacketDecodeTests(unittest.TestCase):
  def test_undersize_packet(self):
    packet = bytearray('abc')
    self.assertRaises(s3g.PacketLengthError,s3g.DecodePacket,packet)
    
  def test_wrong_header(self):
    packet = bytearray('abcd')
    self.assertRaises(s3g.PacketHeaderError,s3g.DecodePacket,packet)

  def test_bad_packet_length_field(self):
    packet = bytearray()
    packet.append(s3g.header)
    packet.append(5)
    packet.extend('ab')
    self.assertRaises(s3g.PacketLengthFieldError,s3g.DecodePacket,packet)

  def test_bad_crc(self):
    packet = bytearray()
    packet.append(s3g.header)
    packet.append(1)
    packet.extend('a')
    packet.append(s3g.CalculateCRC('a')+1)
    self.assertRaises(s3g.PacketCRCError,s3g.DecodePacket,packet)

  def test_got_payload(self):
    expected_payload = bytearray('abcde')

    packet = bytearray()
    packet.append(s3g.header)
    packet.append(len(expected_payload))
    packet.extend(expected_payload)
    packet.append(s3g.CalculateCRC(expected_payload))

    payload = s3g.DecodePacket(packet)
    assert payload == expected_payload


class PacketStreamDecoderTests(unittest.TestCase):
  def setUp(self):
    self.s = s3g.PacketStreamDecoder()

  def tearDown(self):
    self.s = None

  def test_starts_in_wait_for_header_mode(self):
    assert self.s.state == 'WAIT_FOR_HEADER'
    assert len(self.s.payload) == 0
    assert self.s.expected_length == 0

  def test_reject_bad_header(self):
    self.assertRaises(s3g.PacketHeaderError,self.s.ParseByte,0x00)
    assert self.s.state == 'WAIT_FOR_HEADER'

  def test_accept_header(self):
    self.s.ParseByte(s3g.header)
    assert self.s.state == 'WAIT_FOR_LENGTH'

  def test_reject_bad_size(self):
    self.s.ParseByte(s3g.header)
    self.assertRaises(s3g.PacketLengthFieldError,self.s.ParseByte,s3g.maximum_payload_length+1)

  def test_accept_size(self):
    self.s.ParseByte(s3g.header)
    self.s.ParseByte(s3g.maximum_payload_length)
    assert(self.s.state == 'WAIT_FOR_DATA')
    assert(self.s.expected_length == s3g.maximum_payload_length)

  def test_accepts_data(self):
    self.s.ParseByte(s3g.header)
    self.s.ParseByte(s3g.maximum_payload_length)
    for i in range (0, s3g.maximum_payload_length):
      self.s.ParseByte(i)

    assert(self.s.expected_length == s3g.maximum_payload_length)
    for i in range (0, s3g.maximum_payload_length):
      assert(self.s.payload[i] == i)

  def test_reject_bad_crc(self):
    payload = 'abcde'
    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(s3g.PacketCRCError,self.s.ParseByte,s3g.CalculateCRC(payload)+1)

  def test_reject_response_generic_error(self):
    cases = [
      ['GENERIC_ERROR',          s3g.RetryError],
      ['ACTION_BUFFER_OVERFLOW', s3g.BufferOverflowError],
      ['CRC_MISMATCH',           s3g.RetryError],
      ['DOWNSTREAM_TIMEOUT',     s3g.TransmissionError],
      ['TOOL_LOCK_TIMEOUT',      s3g.TransmissionError],
      ['CANCEL_BUILD',           s3g.BuildCancelledError],
    ]

    for case in cases:
      self.s = s3g.PacketStreamDecoder()

      payload = bytearray()
      payload.append(s3g.response_code_dict[case[0]])

      self.s.ParseByte(s3g.header)
      self.s.ParseByte(len(payload))
      for i in range (0, len(payload)):
        self.s.ParseByte(payload[i])
      self.assertRaises(case[1], s3g.CheckResponseCode, payload[0])

  def test_reject_response_unknown_error_code(self):
    payload = bytearray()
    payload.append(0xFF)  # Note: We assume that 0xFF is not a valid error code.

    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(s3g.ProtocolError, s3g.CheckResponseCode, payload[0])

  def test_accept_packet(self):
    payload = bytearray()
    payload.append(s3g.response_code_dict['SUCCESS'])
    payload.extend('abcde')
    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.s.ParseByte(s3g.CalculateCRC(payload))
    assert(self.s.state == 'PAYLOAD_READY')
    assert(self.s.payload == payload)

  def test_accept_packet_ignore_response_code(self):
    self.s = s3g.PacketStreamDecoder()

    payload = bytearray()
    payload.extend('abcde')
    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.s.ParseByte(s3g.CalculateCRC(payload))
    assert(self.s.state == 'PAYLOAD_READY')
    assert(self.s.payload == payload)

if __name__ == "__main__":
  unittest.main()
