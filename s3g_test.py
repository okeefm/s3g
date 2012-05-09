import unittest
import sys
import io
import s3g
import struct

class CRCTests(unittest.TestCase):
  def test_cases(self):
    # Calculated using the processing tool 'ibutton_crc'
    cases = [
      [b'', 0],
      [b'abcdefghijk', 0xb4],
      [b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f', 0x3c],
    ]
    for case in cases:
      assert s3g.CalculateCRC(case[0]) == case[1]


class EncoderTests(unittest.TestCase):
  def test_decode_bitfield8(self):
    field1 = 0
    vals1 = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]
    for val in vals1:
      field1 |= val
    self.assertTrue(s3g.DecodeBitfield8(field1), [1, 1, 1, 1, 1, 1, 1, 1])
    field2 = 0
    vals2 = [0x01, 0x04, 0x10, 0x40]
    for val in vals2:
      field2 |= val
    self.assertTrue(s3g.DecodeBitfield8(field2), [1, 0, 1, 0, 1, 0, 1, 0])
    field3 = 0
    vals3 = [0x01, 0x02]
    for val in vals3:
      field3 |= val
    self.assertTrue(s3g.DecodeBitfield8(field3), [1, 1, 0, 0, 0, 0, 0, 0, 0])
    self.assertTrue(s3g.DecodeBitfield8(0), [0, 0, 0, 0, 0, 0, 0, 0])

  def test_decode_bitfield8_pathogenic(self):
    field = 0
    field |= 0x80 + 0x80
    self.assertRaises(TypeError, s3g.DecodeBitfield8, field)


  def test_encode_int32(self):
    cases = [
      [0,            '\x00\x00\x00\x00'],
      [-2147483648,  '\x00\x00\x00\x80'],
      [2147483647,   '\xFF\xFF\xFF\x7F'],
    ]
    for case in cases:
      assert s3g.EncodeInt32(case[0]) == case[1]
    
  def test_encode_uint32(self):
    cases = [
      [0,            '\x00\x00\x00\x00'],
      [2147483647,   '\xFF\xFF\xFF\x7F'],
      [4294967295,   '\xFF\xFF\xFF\xFF'],
    ]
    for case in cases:
      assert s3g.EncodeUint32(case[0]) == case[1]

  def test_encode_uint16(self):
    cases = [
      [0,       '\x00\x00'],
      [32767,   '\xFF\x7F'],
      [65535,   '\xFF\xFF'],
    ]
    for case in cases:
      assert s3g.EncodeUint16(case[0]) == case[1]

  def test_decode_int32(self):
    cases = [
      [0,       '\x00\x00\x00\x00'],
      [-65536,  '\x00\x00\xFF\xFF'],
      [16,      '\x10\x00\x00\x00'],
    ]
    for case in cases:
      self.assertEqual(case[0], s3g.DecodeInt32(case[1]))

  def test_decode_int32_bytearray(self):
    cases = [
      [0, bytearray('\x00\x00\x00\x00')],
      [-65536,  '\x00\x00\xFF\xFF'],
      [16,      '\x10\x00\x00\x00'],
    ]
    for case in cases:
      self.assertEqual(case[0], s3g.DecodeInt32(case[1]))

  def test_decode_uint16(self):
    cases = [
      [0,       '\x00\x00'],
      [32767,   '\xFF\x7F'],
      [65535,   '\xFF\xFF'],
    ]
    for case in cases:
      self.assertEqual(s3g.DecodeUint16(case[1]), case[0])

  def test_decode_uint16_bytearray(self):
    byteArrayCases = [
      [0,       bytearray('\x00\x00')],
      [32767,   bytearray('\xff\x7f')],
      [65535,   bytearray('\xff\xff')],
    ]
    for case in byteArrayCases:
      self.assertEqual(s3g.DecodeUint16(case[1]), case[0])

  def test_decode_uint16_pathological_fail(self):
    failCase = [0, bytearray('\x00\x00\x00')]
    self.assertRaises(struct.error, s3g.DecodeUint16, failCase[1])

  def test_encode_axes(self):
    cases = [
      [['x','y','z','a','b'], 0x1F],
      [['x'],                 0x01],
      [['y'],                 0x02],
      [['z'],                 0x04],
      [['a'],                 0x08],
      [['b'],                 0x10],
      [[],                    0x00],
    ]
    for case in cases:
      assert s3g.EncodeAxes(case[0]) == case[1]


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
    payload = bytearray()
    payload.append(s3g.response_code_dict['GENERIC_ERROR'])

    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(s3g.RetryError, s3g.CheckResponseCode, payload[0])

  def test_reject_response_action_buffer_overflow(self):
    payload = bytearray()
    payload.append(s3g.response_code_dict['ACTION_BUFFER_OVERFLOW'])

    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(s3g.BufferOverflowError, s3g.CheckResponseCode, payload[0])

  def test_reject_response_crc_mismatch(self):
    payload = bytearray()
    payload.append(s3g.response_code_dict['CRC_MISMATCH'])

    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(s3g.RetryError, s3g.CheckResponseCode, payload[0])

  def test_reject_response_downstream_timeout(self):
    payload = bytearray()
    payload.append(s3g.response_code_dict['DOWNSTREAM_TIMEOUT'])

    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(s3g.TransmissionError, s3g.CheckResponseCode, payload[0])

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


class S3gTests(unittest.TestCase):
  """
  Emulate a machine
  """
  def setUp(self):
    self.r = s3g.s3g()
    self.outputstream = io.BytesIO() # Stream that we will send responses on
    self.inputstream = io.BytesIO()  # Stream that we will receive commands on
    self.file = io.BufferedRWPair(self.outputstream, self.inputstream)
    self.r.file = self.file

  def tearDown(self):
    self.r = None
    self.outputstream = None
    self.inputstream = None
    self.file = None

  def test_send_packet_timeout(self):
    """
    Time out when no data is received. The input stream should have max_rety_count copies of the
    payload packet in it.
    """
    payload = 'abcde'
    packet = s3g.EncodePayload(payload)
    expected_packet = s3g.EncodePayload(payload)

    self.assertRaises(s3g.TransmissionError,self.r.SendPacket, packet)
    self.inputstream.seek(0)

    for i in range (0, s3g.max_retry_count):
      for byte in expected_packet:
        assert byte == ord(self.inputstream.read(1))

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

    assert response_payload == self.r.SendPacket(packet)

    self.inputstream.seek(0)
    for i in range (0, s3g.max_retry_count - 1):
      for byte in expected_packet:
        assert byte == ord(self.inputstream.read(1))

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

    assert response_payload == self.r.SendPacket(packet)
    assert s3g.EncodePayload(payload) == self.inputstream.getvalue()

  # TODO: Test timing based errors- can we send half a response, get it to re-send, then send a regular response?

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

    self.assertEqual(response_payload, self.r.SendCommand(payload))
    self.assertEqual(s3g.EncodePayload(payload), self.inputstream.getvalue())

  def test_unpack_response_no_format(self):
    self.assertRaises(s3g.ProtocolError,self.r.UnpackResponse,'','abcde')

  def test_unpack_response_short_data(self):
    self.assertRaises(s3g.ProtocolError,self.r.UnpackResponse,'<I','abc')

  def test_unpack_response(self):
    expected_data = [1,'a','b','c']
    data = self.r.UnpackResponse('<Iccc','\x01\x00\x00\x00abc')
    for i in range(0, len(expected_data)):
      assert(data[i] == expected_data[i])

  def test_unpack_response_with_string_no_format(self):
    expected_string = 'abcde\x00'
    data = self.r.UnpackResponseWithString('',expected_string)
    assert(len(data) == 1)
    assert data[0] == expected_string

  def test_unpack_response_with_string_missing_string(self):
    self.assertRaises(s3g.ProtocolError,self.r.UnpackResponseWithString,'<I','abcd')

  def test_unpack_response_with_string(self):
    expected_data = [1,'a','b','c','ABCDE\x00']
    data = self.r.UnpackResponseWithString('<Iccc','\x01\x00\x00\x00abcABCDE\x00')
    for i in range(0, len(expected_data)):
      assert(data[i] == expected_data[i])

  def test_get_version(self):
    version = 0x5DD5

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint16(version))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetVersion() == version

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['GET_VERSION']
    assert payload[1:3] == s3g.EncodeUint16(s3g.s3g_version)

  def test_reset(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])

    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.Reset()

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_query_command_dict['RESET'])

  def test_is_finished(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(0)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertEqual(self.r.IsFinished(), 0)

    packet = bytearray(self.inputstream.getvalue())

    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_query_command_dict['IS_FINISHED'])

  def test_clear_buffer(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.ClearBuffer()

    packet = bytearray(self.inputstream.getvalue())

    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_query_command_dict['CLEAR_BUFFER'])

  def test_pause(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.Pause()

    packet = bytearray(self.inputstream.getvalue())

    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_query_command_dict['PAUSE'])

  def test_tool_query_no_payload(self):
    tool_index = 2
    command = 0x12
    response = 'abcdef'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(response)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    
    assert self.r.ToolQuery(tool_index, command) == response_payload

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
    assert payload[1] == tool_index
    assert payload[2] == command

  def test_tool_query_payload(self):
    tool_index = 2
    command = 0x12
    command_payload = 'ABCDEF'
    response = 'abcdef'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(response)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    
    assert self.r.ToolQuery(tool_index, command, command_payload) == response_payload

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
    assert payload[1] == tool_index
    assert payload[2] == command
    assert payload[3:] == command_payload

  def test_read_from_eeprom_bad_length(self):
    offset = 1234
    length = s3g.maximum_payload_length

    self.assertRaises(s3g.ProtocolError,self.r.ReadFromEEPROM,offset, length)

  def test_read_from_eeprom(self):
    offset = 1234
    length = s3g.maximum_payload_length - 1
    data = bytearray()
    for i in range (0, length):
      data.append(i)

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(data)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.ReadFromEEPROM(offset, length) == data

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['READ_FROM_EEPROM']
    assert payload[1:3] == s3g.EncodeUint16(offset)
    assert payload[3] == length

  def test_write_to_eeprom_too_much_data(self):
    offset = 1234
    length = s3g.maximum_payload_length - 3
    data = bytearray()
    for i in range (0, length):
      data.append(i)

    self.assertRaises(s3g.ProtocolError,self.r.WriteToEEPROM, offset, data)

  def test_write_to_eeprom_bad_response_length(self):
    offset = 1234
    length = s3g.maximum_payload_length - 4
    data = bytearray()
    for i in range (0, length):
      data.append(i)

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(length+1)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertRaises(s3g.ProtocolError, self.r.WriteToEEPROM,offset, data)

  def test_write_to_eeprom(self):
    offset = 1234
    length = s3g.maximum_payload_length - 4
    data = bytearray()
    for i in range (0, length):
      data.append(i)

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(length)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.WriteToEEPROM(offset, data)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['WRITE_TO_EEPROM']
    assert payload[1:3] == s3g.EncodeUint16(offset)
    assert payload[3] == length
    assert payload[4:] == data

  def test_get_available_buffer_size(self):
    buffer_size = 0xDEADBEEF

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint32(buffer_size))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetAvailableBufferSize() == buffer_size

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['GET_AVAILABLE_BUFFER_SIZE']

  def test_get_position(self):
    position = [1, -2, 3]
    endstop_states = s3g.EncodeAxes(['x','y'])
    
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeInt32(position[0]))
    response_payload.extend(s3g.EncodeInt32(position[1]))
    response_payload.extend(s3g.EncodeInt32(position[2]))
    response_payload.append(endstop_states)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    [returned_position, returned_endstop_states] = self.r.GetPosition()
    assert returned_position == position
    assert returned_endstop_states == endstop_states

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['GET_POSITION']

  def test_abort_immediately(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.AbortImmediately()

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['ABORT_IMMEDIATELY']

  def test_playback_capture_error_codes(self):
    filename = 'abcdefghijkl'
    error_codes = [
      'NO_CARD_PRESENT',
      'INITIALIZATION_FAILED',
      'PARTITION_TABLE_ERROR',
      'FILESYSTEM_ERROR',
      'DIRECTORY_ERROR',
    ]

    for error_code in error_codes:
      self.outputstream.seek(0)
      self.outputstream.truncate(0)

      response_payload = bytearray()
      response_payload.append(s3g.response_code_dict['SUCCESS'])
      response_payload.append(s3g.sd_error_dict[error_code])
      self.outputstream.write(s3g.EncodePayload(response_payload))
      self.outputstream.seek(0)

      self.assertRaises(s3g.SDCardError,self.r.PlaybackCapture,filename)

  def test_playback_capture(self):
    filename = 'abcdefghijkl'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(s3g.sd_error_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.PlaybackCapture(filename)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['PLAYBACK_CAPTURE']
    assert payload[1:-1] == filename
    assert payload[-1] == 0x00

  def test_get_next_filename_error_codes(self):
    error_codes = [
      'NO_CARD_PRESENT',
      'INITIALIZATION_FAILED',
      'PARTITION_TABLE_ERROR',
      'FILESYSTEM_ERROR',
      'DIRECTORY_ERROR',
    ]
    for error_code in error_codes:
      self.outputstream.seek(0)
      self.outputstream.truncate(0)

      response_payload = bytearray()
      response_payload.append(s3g.response_code_dict['SUCCESS'])
      response_payload.append(s3g.sd_error_dict[error_code])
      response_payload.append('\x00')
      self.outputstream.write(s3g.EncodePayload(response_payload))
      self.outputstream.seek(0)

      self.assertRaises(s3g.SDCardError,self.r.GetNextFilename,False)

  def test_get_next_filename_reset(self):
    filename = 'abcdefghijkl'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(s3g.sd_error_dict['SUCCESS'])
    response_payload.extend(filename)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetNextFilename(True) == filename

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['GET_NEXT_FILENAME']
    assert payload[1] == 1

  def test_get_next_filename_no_reset(self):
    filename = 'abcdefghijkl'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(s3g.sd_error_dict['SUCCESS'])
    response_payload.extend(filename)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetNextFilename(False) == filename

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['GET_NEXT_FILENAME']
    assert payload[1] == 0

  def test_get_build_name(self):
    build_name = 'abcdefghijklmnop'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(build_name)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetBuildName() == build_name

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['GET_BUILD_NAME']

  def test_get_extended_position(self):
    position = [1, -2, 3, -4 , 5]
    endstop_states = 0x1234
    
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeInt32(position[0]))
    response_payload.extend(s3g.EncodeInt32(position[1]))
    response_payload.extend(s3g.EncodeInt32(position[2]))
    response_payload.extend(s3g.EncodeInt32(position[3]))
    response_payload.extend(s3g.EncodeInt32(position[4]))
    response_payload.extend(s3g.EncodeUint16(endstop_states))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    [returned_position, returned_endstop_states] = self.r.GetExtendedPosition()
    assert returned_position == position
    assert returned_endstop_states == endstop_states

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['GET_EXTENDED_POSITION']

  def test_wait_for_button_bad_button(self):
    button = 'bad'
    self.assertRaises(s3g.UnknownButtonError, self.r.WaitForButton, button, 0, False, False, False)

  def test_wait_for_button(self):
    button = 0x10
    options = 0x02 + 0x04
    timeout = 0
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.WaitForButton('up', timeout, False, True, True)
    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['WAIT_FOR_BUTTON'])
    self.assertEqual(payload[1], button)
    self.assertEqual(payload[2:4], s3g.EncodeUint16(timeout))
    self.assertEqual(payload[4], options)

  def test_queue_song(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    songId = 1
    self.r.QueueSong(songId)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['QUEUE_SONG'])
    self.assertEqual(payload[1], songId)

  def test_reset_to_factory(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    options = 0
    self.r.ResetToFactory(options)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['RESET_TO_FACTORY'])
    self.assertEqual(payload[1], options)

  def test_set_build_percent(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    percent = 42
    ignore = 0
    self.r.SetBuildPercent(percent, ignore)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['SET_BUILD_PERCENT'])
    self.assertEqual(payload[1], percent)
    self.assertEqual(payload[2], ignore)

  def test_display_message(self):
    continuation = True
    row = 0x12
    col = 0x34
    timeout = 0x56
    message = 'abcdefghij'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.DisplayMessage(row, col, message, timeout, continuation)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['DISPLAY_MESSAGE']
    assert payload[1] == 1 # continuation == True
    assert payload[2] == col
    assert payload[3] == row
    assert payload[4] == timeout
    assert payload[5:-1] == message
    assert payload[-1] == 0x00

  def test_build_start_notification(self):
    command_count = 1234
    build_name = 'abcdefghijkl'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.BuildStartNotification(command_count, build_name)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['BUILD_START_NOTIFICATION']
    assert payload[1:5] == s3g.EncodeUint32(command_count)
    assert payload[5:-1] == build_name
    assert payload[-1] == 0x00

  def test_build_end_notification(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.BuildEndNotification()

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['BUILD_END_NOTIFICATION']

  def test_queue_point(self):
    target = [1,-2,3]
    velocity = 6

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

    self.r.QueuePoint(target, velocity)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    assert payload[0] == s3g.host_action_command_dict['QUEUE_POINT']
    for i in range(0, 3):
      assert payload[(i*4+1):(i*4+5)] == s3g.EncodeInt32(target[i])
    payload[13:17] == s3g.EncodeInt32(velocity)

  def test_set_position(self):
    target = [1,-2,3]

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

    self.r.SetPosition(target)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    assert payload[0] == s3g.host_action_command_dict['SET_POSITION']
    for i in range(0, 3):
      assert payload[(i*4+1):(i*4+5)] == s3g.EncodeInt32(target[i])

  def test_find_axes_minimums(self):
    axes = ['x', 'y', 'z', 'b']
    rate = 2500
    timeout = 45

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

    self.r.FindAxesMinimums(axes, rate, timeout)

    packet = bytearray(self.inputstream.getvalue())

    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['FIND_AXES_MINIMUMS']
    assert payload[1] == s3g.EncodeAxes(axes)
    assert payload[2:6] == s3g.EncodeUint32(rate)
    assert payload[6:8] == s3g.EncodeUint16(timeout)
  
  def test_find_axes_maximums(self):
    axes = ['x', 'y', 'z', 'b']
    rate = 2500
    timeout = 45

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

    self.r.FindAxesMaximums(axes, rate, timeout)

    packet = bytearray(self.inputstream.getvalue())

    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['FIND_AXES_MAXIMUMS']
    assert payload[1] == s3g.EncodeAxes(axes)
    assert payload[2:6] == s3g.EncodeUint32(rate)
    assert payload[6:8] == s3g.EncodeUint16(timeout)

  def test_tool_action_command_bad_tool_index(self):
    tool_indices = [-1, s3g.max_tool_index + 1]
    command = 0x12
    command_payload = 'abcdefghij'

    for tool_index in tool_indices:
      self.assertRaises(s3g.ProtocolError,
                        self.r.ToolActionCommand,
                        tool_index, command, command_payload)

  def test_tool_action_command(self):
    tool_index = 2
    command = 0x12
    command_payload = 'abcdefghij'

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

    self.r.ToolActionCommand(tool_index, command, command_payload)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    assert payload[0] == s3g.host_action_command_dict['TOOL_ACTION_COMMAND']
    assert payload[1] == tool_index
    assert payload[2] == command
    assert payload[3] == len(command_payload)
    assert payload[4:] == command_payload

  def test_queue_extended_point(self):
    target = [1,-2,3,-4,5]
    velocity = 6

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

    self.r.QueueExtendedPoint(target, velocity)

    packet = bytearray(self.inputstream.getvalue())

    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['QUEUE_EXTENDED_POINT']
    for i in range(0, 5):
      assert payload[(i*4+1):(i*4+5)] == s3g.EncodeInt32(target[i])
    assert payload[21:25] == s3g.EncodeInt32(velocity)

  def test_set_extended_position(self):
    target = [1,-2,3,-4,5]

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

    self.r.SetExtendedPosition(target)

    packet = bytearray(self.inputstream.getvalue())

    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['SET_EXTENDED_POSITION']
    for i in range(0, 5):
      assert s3g.EncodeInt32(target[i]) == payload[(i*4+1):(i*4+5)]

  def test_get_toolhead_version(self):
    tool_index = 2
    version = 0x5DD5

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint16(version))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetToolheadVersion(tool_index) == version

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_query_command_dict['GET_VERSION']
    assert payload[3:5] == s3g.EncodeUint16(s3g.s3g_version)

  def test_capture_to_file(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(s3g.sd_error_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    filename = 'test'
    self.r.CaptureToFile(filename)
    
    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_query_command_dict['CAPTURE_TO_FILE'])
    self.assertEqual(payload[1:-1], filename)
    self.assertEqual(payload[-1], 0x00)

  def test_capture_to_file_errors(self):
    for key in s3g.sd_error_dict:
      if key != 'SUCCESS':
        response_payload = bytearray()
        response_payload.append(s3g.response_code_dict['SUCCESS'])
        response_payload.append(s3g.sd_error_dict[key])
        self.outputstream.write(s3g.EncodePayload(response_payload))
        self.outputstream.seek(0)

        filename = 'test'

        self.assertRaises(s3g.SDCardError, self.r.CaptureToFile, filename)

  def test_end_capture_to_file(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint32(0))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    sdResponse = self.r.EndCaptureToFile()

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_query_command_dict['END_CAPTURE'])

  def test_store_home_positions(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    bitfield = s3g.EncodeAxes(['x', 'y', 'z', 'a', 'b'])
    self.r.StoreHomePositions(True, True, True, True, True)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['STORE_HOME_POSITIONS'])
    self.assertEqual(payload[1], bitfield)

  def test_set_beep(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    frequency = 1
    length = 2
    effect = 3
    self.r.SetBeep(frequency, length, effect)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['SET_BEEP'])
    self.assertEqual(payload[1:3], s3g.EncodeUint16(frequency))
    self.assertEqual(payload[3:5], s3g.EncodeUint16(length))
    self.assertEqual(payload[5], effect)

  def test_set_rgb_led(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    r = 255
    g = 254
    b = 253
    blink = 252
    effect = 0

    self.r.SetRGBLED(r, g, b, blink, effect)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertTrue(payload[0], s3g.host_action_command_dict['SET_POT_VALUE'])
    self.assertEqual(payload[1], r)
    self.assertEqual(payload[2], g)
    self.assertEqual(payload[3], b)
    self.assertEqual(payload[4], blink)
    self.assertEqual(payload[5], effect)

  def test_set_potentiometer_value(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    axesField = 0
    axesField |= 0x01 + 0x02 + 0x04 + 0x08 + 0x10
    value = 0
    self.r.SetPotentiometerValue(True, True, True, True, True, value)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['SET_POT_VALUE'])
    self.assertEqual(payload[1], axesField)
    self.assertEqual(payload[2], value)

  def test_recall_home_positions(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    bitfield = s3g.EncodeAxes(['x', 'y', 'z', 'a', 'b'])
    self.r.RecallHomePositions(True, True, True, True, True)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['RECALL_HOME_POSITIONS'])
    self.assertEqual(payload[1], bitfield)

  def test_queue_extended_point_new(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    point = [1, 2, 3, 4, 5]
    duration = 10
    bitfield = 0
    vals = [0x01, 0x02, 0x04, 0x08, 0x10]
    for val in vals:
      bitfield |= val
    self.r.QueueExtendedPointNew(point, duration, True, True, True, True, True)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW'])
    self.assertEqual(payload[1:5], s3g.EncodeInt32(point[0]))
    self.assertEqual(payload[5:9], s3g.EncodeInt32(point[1]))
    self.assertEqual(payload[9:13], s3g.EncodeInt32(point[2]))
    self.assertEqual(payload[13:17], s3g.EncodeInt32(point[3]))
    self.assertEqual(payload[17:21], s3g.EncodeInt32(point[4]))
    self.assertEqual(payload[21:25], s3g.EncodeUint32(duration))
    self.assertEqual(payload[25], bitfield)
    

  def test_wait_for_platform_ready(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    toolhead = 0
    delay = 100
    timeout = 60

    self.r.WaitForPlatformReady(toolhead, delay, timeout)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['WAIT_FOR_PLATFORM_READY'])
    self.assertEqual(payload[1], toolhead)
    self.assertEqual(payload[2:4], s3g.EncodeUint16(delay))
    self.assertEqual(payload[4:], s3g.EncodeUint16(timeout))

  def test_wait_for_tool_ready(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    toolhead = 0
    delay = 100
    timeout = 60

    self.r.WaitForToolReady(toolhead, delay, timeout)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_action_command_dict['WAIT_FOR_TOOL_READY'])
    self.assertEqual(payload[1], toolhead)
    self.assertEqual(payload[2:4], s3g.EncodeUint16(delay))
    self.assertEqual(payload[4:], s3g.EncodeUint16(timeout))
    
  def test_toggle_enable_axes(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.ToggleEnableAxes(True, True, True, True, True, True)
    bitfield = 0
    bitVals = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]
    for val in bitVals:
      bitfield |= val

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['ENABLE_AXES'])
    self.assertEqual(payload[1], bitfield)

  def test_delay(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    dTime = 50
    self.r.Delay(dTime)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_action_command_dict['DELAY'])
    self.assertEqual(payload[1:], s3g.EncodeUint32(dTime))

  def test_get_communication_stats(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    for i in range(5):
      response_payload.extend(s3g.EncodeUint32(0))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    info = self.r.GetCommunicationStats()
    responseInfo = {
    'PacketsReceived' : 0,
    'PacketsSent' : 0,
    'NonResponsivePacketsSent' : 0,
    'PacketRetries' : 0,
    'NoiseBytes' : 0,
    }
    self.assertEqual(info, responseInfo)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_query_command_dict['GET_COMMUNICATION_STATS'])

  def test_get_motherboard_status(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    flagValues = [0x01 for i in range(8)]
    bitfield = 0
    for i in range(len(flagValues)):
      if flagValues[i]:
        bitfield+=1 << i
    response_payload.append(bitfield)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    responseFlags = self.r.GetMotherboardStatus()

    flags = {
    'POWER_ERROR' : 1
    }

    self.assertEqual(flags, responseFlags)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_query_command_dict['GET_MOTHERBOARD_STATUS'])    


  def test_extended_stop(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(0)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    
    bitfield = 0
    bitfield |= 0x01
    bitfield |= 0x02

    self.r.ExtendedStop(True, True)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_query_command_dict['EXTENDED_STOP'])
    self.assertEqual(payload[1], bitfield)

  def test_extended_stop_error(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(1)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertRaises(s3g.ExtendedStopError, self.r.ExtendedStop, True, True)

  def test_get_pid_state(self):
    toolIndex = 0
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    for i in range(6):
      response_payload.extend(s3g.EncodeUint16(1))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    expectedDict = {
    "ExtruderError"    : 1,
    "ExtruderDelta"    : 1,
    "exLastTerm"       : 1,
    "PlatformError"    : 1,
    "PlatformDelta"    : 1,
    "PlatformLastTerm" : 1,
    }

    self.assertTrue(expectedDict, self.r.GetPIDState(toolIndex))

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_query_command_dict['TOOL_QUERY'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_query_command_dict['GET_PID_STATE'])

  def test_toolhead_init(self):
    toolIndex = 0
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.ToolheadInit(toolIndex)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    expectedPayload = bytearray()
    self.assertEqual(payload[0], s3g.host_action_command_dict['TOOL_ACTION_COMMAND'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_action_command_dict['INIT'])
    self.assertEqual(payload[3], len(expectedPayload))
    self.assertEqual(payload[4:], expectedPayload)

  def test_toolhead_abort(self):
    toolIndex = 0
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.ToolheadAbort(toolIndex)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['TOOL_ACTION_COMMAND'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_action_command_dict['ABORT'])
    self.assertEqual(payload[3], len(bytearray()))
    self.assertEqual(payload[4:], bytearray())

  def test_toolhead_pause(self):
    toolIndex = 0
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.ToolheadPause(toolIndex)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['TOOL_ACTION_COMMAND'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_action_command_dict['PAUSE'])
    self.assertEqual(payload[3], len(bytearray()))
    self.assertEqual(payload[4:], bytearray())

  def test_set_servo_1_position(self):
    toolIndex = 0
    theta = 90
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.r.SetServo1Position(toolIndex, theta)

    expectedPayload = bytearray()
    expectedPayload.append(theta)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['TOOL_ACTION_COMMAND'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_action_command_dict['SET_SERVO_1_POSITION'])
    self.assertEqual(payload[3], len(expectedPayload))
    self.assertEqual(payload[4:], expectedPayload)

  def test_toggle_motor_1(self):
    toolIndex = 0
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.ToggleMotor1(toolIndex, True, True)

    expectedPayload = bytearray()
    bitfield = 0
    bitfield |= 0x01 + 0x02
    expectedPayload.append(bitfield)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['TOOL_ACTION_COMMAND'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_action_command_dict['TOGGLE_MOTOR_1'])
    self.assertEqual(payload[3], len(expectedPayload))
    self.assertEqual(payload[4:], expectedPayload)

  def test_set_motor_1_speed_rpm(self):
    toolIndex = 0
    duration = 50 
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.SetMotor1SpeedRPM(toolIndex, duration)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    expectedPayload = bytearray()
    expectedPayload.extend(s3g.EncodeUint32(duration))

    self.assertEqual(payload[0], s3g.host_action_command_dict['TOOL_ACTION_COMMAND'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_action_command_dict['SET_MOTOR_1_SPEED_RPM'])
    self.assertEqual(payload[3], len(expectedPayload))
    self.assertEqual(payload[4:], expectedPayload)

  def test_get_tool_status(self):
    toolIndex = 0
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    returnBitfield = 0
    values = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]
    for val in values:
      returnBitfield |= val
    response_payload.append(returnBitfield)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)


    expectedDict = {
    "EXTRUDER_READY" : True,
    "PLATFORM_ERROR" : True,
    "EXTRUDER_ERROR" : True,
    }
    self.assertEqual(expectedDict, self.r.GetToolStatus(toolIndex))

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_query_command_dict['TOOL_QUERY'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_query_command_dict['GET_TOOL_STATUS'])
 

  def test_get_motor_speed(self):
    speed = 100
    toolIndex = 0
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint32(speed))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertEqual(speed, self.r.GetMotor1Speed(toolIndex))

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_query_command_dict['TOOL_QUERY'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_query_command_dict['GET_MOTOR_1_SPEED_RPM'])

  def test_init(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.Init()

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['INIT']

  def test_get_toolhead_temperature(self):
    tool_index = 2
    temperature = 1234

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint16(temperature))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetToolheadTemperature(tool_index) == temperature

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_query_command_dict['GET_TOOLHEAD_TEMP']

  # TODO: also test for bad codes, both here and in platform.
  def test_is_tool_ready_bad_response(self):
    tool_index = 2
    ready_state = 2

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(ready_state)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.inputstream.seek(0)

    self.assertRaises(s3g.ProtocolError, self.r.IsToolReady, tool_index)

  # TODO: also test for bad codes, both here and in platform.
  def test_is_tool_ready(self):
    tool_index = 2
    ready_states = [[True, 1],
                    [False,0]]

    for ready_state in ready_states:
      self.outputstream.seek(0)
      self.outputstream.truncate(0)

      response_payload = bytearray()
      response_payload.append(s3g.response_code_dict['SUCCESS'])
      response_payload.append(ready_state[1])
      self.outputstream.write(s3g.EncodePayload(response_payload))
      self.outputstream.seek(0)
      self.inputstream.seek(0)

      assert self.r.IsToolReady(tool_index) == ready_state[0]

      packet = bytearray(self.inputstream.getvalue())
      payload = s3g.DecodePacket(packet)
      assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
      assert payload[1] == tool_index
      assert payload[2] == s3g.slave_query_command_dict['IS_TOOL_READY']
    

  def test_read_from_toolhead_eeprom_bad_length(self):
    tool_index = 2
    offset = 1234
    length = s3g.maximum_payload_length

    self.assertRaises(s3g.ProtocolError,self.r.ReadFromToolheadEEPROM, tool_index, offset, length)

  def test_read_from_toolhead_eeprom(self):
    tool_index = 2
    offset = 1234
    length = s3g.maximum_payload_length - 1
    data = bytearray()
    for i in range (0, length):
      data.append(i)

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(data)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.ReadFromToolheadEEPROM(tool_index, offset, length) == data

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_query_command_dict['READ_FROM_EEPROM']
    assert payload[3:5] == s3g.EncodeUint16(offset)
    assert payload[5] == length

  def test_write_to_toolhead_eeprom_too_much_data(self):
    tool_index = 2
    offset = 1234
    length = s3g.maximum_payload_length - 5
    data = bytearray()
    for i in range (0, length):
      data.append(i)

    self.assertRaises(s3g.ProtocolError,self.r.WriteToToolheadEEPROM, tool_index, offset, data)

  def test_write_to_toolhead_eeprom_bad_response_length(self):
    tool_index = 2
    offset = 1234
    length = s3g.maximum_payload_length - 6
    data = bytearray()
    for i in range (0, length):
      data.append(i)

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(length+1)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertRaises(s3g.ProtocolError, self.r.WriteToToolheadEEPROM, tool_index, offset, data)

  def test_write_to_toolhead_eeprom(self):
    tool_index = 2
    offset = 1234
    length = s3g.maximum_payload_length - 6
    data = bytearray()
    for i in range (0, length):
      data.append(i)

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(length)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.WriteToToolheadEEPROM(tool_index, offset, data)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_query_command_dict['WRITE_TO_EEPROM']
    assert payload[3:5] == s3g.EncodeUint16(offset)
    assert payload[6:] == data

  def test_get_platform_temperature(self):
    tool_index = 2
    temperature = 1234

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint16(temperature))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetPlatformTemperature(tool_index) == temperature

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_query_command_dict['GET_PLATFORM_TEMP']

  def test_get_toolhead_target_temperature(self):
    tool_index = 2
    temperature = 1234

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint16(temperature))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetToolheadTargetTemperature(tool_index) == temperature

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_query_command_dict['GET_TOOLHEAD_TARGET_TEMP']

  def test_get_platform_target_temperature(self):
    tool_index = 2
    temperature = 1234

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint16(temperature))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert self.r.GetPlatformTargetTemperature(tool_index) == temperature

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_query_command_dict['GET_PLATFORM_TARGET_TEMP']

  def test_is_platform_ready_bad_response(self):
    tool_index = 2
    ready_state = 2

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(ready_state)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    self.inputstream.seek(0)

    self.assertRaises(s3g.ProtocolError, self.r.IsPlatformReady, tool_index)

  def test_is_platform_ready(self):
    tool_index = 2
    ready_states = [[True, 1],
                    [False,0]]

    for ready_state in ready_states:
      self.outputstream.seek(0)
      self.outputstream.truncate(0)

      response_payload = bytearray()
      response_payload.append(s3g.response_code_dict['SUCCESS'])
      response_payload.append(ready_state[1])
      self.outputstream.write(s3g.EncodePayload(response_payload))
      self.outputstream.seek(0)
      self.inputstream.seek(0)

      assert self.r.IsPlatformReady(tool_index) == ready_state[0]

      packet = bytearray(self.inputstream.getvalue())
      payload = s3g.DecodePacket(packet)
      assert payload[0] == s3g.host_query_command_dict['TOOL_QUERY']
      assert payload[1] == tool_index
      assert payload[2] == s3g.slave_query_command_dict['IS_PLATFORM_READY']

  def test_toggle_fan(self):
    tool_index = 2
    fan_states = [True, False]

    for fan_state in fan_states:
      self.outputstream.seek(0)
      self.outputstream.truncate(0)

      self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
      self.outputstream.seek(0)
      self.inputstream.seek(0)
 
      self.r.ToggleFan(tool_index, fan_state)
 
      packet = bytearray(self.inputstream.getvalue())
      payload = s3g.DecodePacket(packet)
 
      assert payload[0] == s3g.host_action_command_dict['TOOL_ACTION_COMMAND']
      assert payload[1] == tool_index
      assert payload[2] == s3g.slave_action_command_dict['TOGGLE_FAN']
      assert payload[3] == 1
      assert payload[4] == fan_state

  def test_toggle_valve(self):
    tool_index = 2
    fan_states = [True, False]

    for fan_state in fan_states:
      self.outputstream.seek(0)
      self.outputstream.truncate(0)

      self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
      self.outputstream.seek(0)
      self.inputstream.seek(0)
 
      self.r.ToggleValve(tool_index, fan_state)
 
      packet = bytearray(self.inputstream.getvalue())
      payload = s3g.DecodePacket(packet)
 
      assert payload[0] == s3g.host_action_command_dict['TOOL_ACTION_COMMAND']
      assert payload[1] == tool_index
      assert payload[2] == s3g.slave_action_command_dict['TOGGLE_VALVE']
      assert payload[3] == 1
      assert payload[4] == fan_state

  def test_set_toolhead_temp(self):
    tool_index = 2
    temp = 100

    self.outputstream.seek(0)
    self.outputstream.truncate(0)

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)
    self.inputstream.seek(0)

    self.r.SetToolheadTemperature(tool_index, temp)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    assert payload[0] == s3g.host_action_command_dict['TOOL_ACTION_COMMAND']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_action_command_dict['SET_TOOLHEAD_TARGET_TEMP']
    assert payload[3] == 2 #Temp is a byte of len 2
    assert payload[4] == temp
	

  def test_set_platform_temp(self):
    tool_index = 0
    temp = 100

    self.outputstream.seek(0)
    self.outputstream.truncate(0)

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)
    self.inputstream.seek(0)

    self.r.SetPlatformTemperature(tool_index, temp)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    assert payload[0] == s3g.host_action_command_dict['TOOL_ACTION_COMMAND']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_action_command_dict['SET_PLATFORM_TEMP']
    assert payload[3] == 2 #Temp is a byte of len 2
    assert payload[4] == temp

if __name__ == "__main__":
  unittest.main()
