import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
from s3g import Encoder, errors, constants

class PacketEncodeTests(unittest.TestCase):
  def test_reject_oversize_payload(self):
    payload = bytearray()
    for i in range (0, constants.maximum_payload_length + 1):
      payload.append(i)
    self.assertRaises(errors.PacketLengthError,Encoder.EncodePayload,payload)

  def test_packet_length(self):
    payload = 'abcd'
    packet = Encoder.EncodePayload(payload)
    assert len(packet) == len(payload) + 3

  def test_packet_header(self):
    payload = 'abcd'
    packet = Encoder.EncodePayload(payload)

    assert packet[0] == constants.header

  def test_packet_length_field(self):
    payload = 'abcd'
    packet = Encoder.EncodePayload(payload)
    assert packet[1] == len(payload)

  def test_packet_crc(self):
    payload = 'abcd'
    packet = Encoder.EncodePayload(payload)
    assert packet[6] == Encoder.CalculateCRC(payload);


class PacketDecodeTests(unittest.TestCase):
  def test_undersize_packet(self):
    packet = bytearray('abc')
    self.assertRaises(errors.PacketLengthError,Encoder.DecodePacket,packet)
    
  def test_wrong_header(self):
    packet = bytearray('abcd')
    self.assertRaises(errors.PacketHeaderError,Encoder.DecodePacket,packet)

  def test_bad_packet_length_field(self):
    packet = bytearray()
    packet.append(constants.header)
    packet.append(5)
    packet.extend('ab')
    self.assertRaises(errors.PacketLengthFieldError,Encoder.DecodePacket,packet)

  def test_bad_crc(self):
    packet = bytearray()
    packet.append(constants.header)
    packet.append(1)
    packet.extend('a')
    packet.append(Encoder.CalculateCRC('a')+1)
    self.assertRaises(errors.PacketCRCError,Encoder.DecodePacket,packet)

  def test_got_payload(self):
    expected_payload = bytearray('abcde')

    packet = bytearray()
    packet.append(constants.header)
    packet.append(len(expected_payload))
    packet.extend(expected_payload)
    packet.append(Encoder.CalculateCRC(expected_payload))

    payload = Encoder.DecodePacket(packet)
    assert payload == expected_payload


class PacketStreamDecoderTests(unittest.TestCase):
  def setUp(self):
    self.s = Encoder.PacketStreamDecoder()

  def tearDown(self):
    self.s = None

  def test_starts_in_wait_for_header_mode(self):
    assert self.s.state == 'WAIT_FOR_HEADER'
    assert len(self.s.payload) == 0
    assert self.s.expected_length == 0

  def test_reject_bad_header(self):
    self.assertRaises(errors.PacketHeaderError,self.s.ParseByte,0x00)
    assert self.s.state == 'WAIT_FOR_HEADER'

  def test_accept_header(self):
    self.s.ParseByte(constants.header)
    assert self.s.state == 'WAIT_FOR_LENGTH'

  def test_reject_bad_size(self):
    self.s.ParseByte(constants.header)
    self.assertRaises(errors.PacketLengthFieldError,self.s.ParseByte,constants.maximum_payload_length+1)

  def test_accept_size(self):
    self.s.ParseByte(constants.header)
    self.s.ParseByte(constants.maximum_payload_length)
    assert(self.s.state == 'WAIT_FOR_DATA')
    assert(self.s.expected_length == constants.maximum_payload_length)

  def test_accepts_data(self):
    self.s.ParseByte(constants.header)
    self.s.ParseByte(constants.maximum_payload_length)
    for i in range (0, constants.maximum_payload_length):
      self.s.ParseByte(i)

    assert(self.s.expected_length == constants.maximum_payload_length)
    for i in range (0, constants.maximum_payload_length):
      assert(self.s.payload[i] == i)

  def test_reject_bad_crc(self):
    payload = 'abcde'
    self.s.ParseByte(constants.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(errors.PacketCRCError,self.s.ParseByte,Encoder.CalculateCRC(payload)+1)

  def test_reject_response_generic_error(self):
    cases = [
      ['GENERIC_ERROR',          errors.RetryError],
      ['ACTION_BUFFER_OVERFLOW', errors.BufferOverflowError],
      ['CRC_MISMATCH',           errors.CRCMismatchError],
      ['DOWNSTREAM_TIMEOUT',     errors.DownstreamTimeoutError],
      ['TOOL_LOCK_TIMEOUT',      errors.ToolLockError],
      ['CANCEL_BUILD',           errors.BuildCancelledError],
    ]

    for case in cases:
      self.s = Encoder.PacketStreamDecoder()

      payload = bytearray()
      payload.append(constants.response_code_dict[case[0]])

      self.s.ParseByte(constants.header)
      self.s.ParseByte(len(payload))
      for i in range (0, len(payload)):
        self.s.ParseByte(payload[i])
      self.assertRaises(case[1], Encoder.CheckResponseCode, payload[0])

  def test_reject_response_unknown_error_code(self):
    payload = bytearray()
    payload.append(0xFF)  # Note: We assume that 0xFF is not a valid error code.

    self.s.ParseByte(constants.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(errors.ProtocolError, Encoder.CheckResponseCode, payload[0])

  def test_accept_packet(self):
    payload = bytearray()
    payload.append(constants.response_code_dict['SUCCESS'])
    payload.extend('abcde')
    self.s.ParseByte(constants.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.s.ParseByte(Encoder.CalculateCRC(payload))
    assert(self.s.state == 'PAYLOAD_READY')
    assert(self.s.payload == payload)

  def test_accept_packet_ignore_response_code(self):
    self.s = Encoder.PacketStreamDecoder()

    payload = bytearray()
    payload.extend('abcde')
    self.s.ParseByte(constants.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.s.ParseByte(Encoder.CalculateCRC(payload))
    assert(self.s.state == 'PAYLOAD_READY')
    assert(self.s.payload == payload)

if __name__ == "__main__":
  unittest.main()
