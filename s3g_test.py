import unittest
import sys
import io
import s3g

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


class EncodeTests(unittest.TestCase):
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

  def test_decode_uint16(self):
    cases = [
      [0,       '\x00\x00'],
      [32767,   '\xFF\x7F'],
      [65535,   '\xFF\xFF'],
    ]
    for case in cases:
      assert s3g.DecodeUint16(case[1]) == case[0]

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
    self.assertRaises(s3g.PacketResponseCodeError,self.s.ParseByte,s3g.CalculateCRC(payload))

  def test_reject_response_action_buffer_overflow(self):
    payload = bytearray()
    payload.append(s3g.response_code_dict['ACTION_BUFFER_OVERFLOW'])

    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(s3g.PacketResponseCodeError,self.s.ParseByte,s3g.CalculateCRC(payload))

  def test_reject_response_crc_mismatch(self):
    payload = bytearray()
    payload.append(s3g.response_code_dict['CRC_MISMATCH'])

    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(s3g.PacketResponseCodeError,self.s.ParseByte,s3g.CalculateCRC(payload))

  def test_reject_response_downstream_timeout(self):
    payload = bytearray()
    payload.append(s3g.response_code_dict['DOWNSTREAM_TIMEOUT'])

    self.s.ParseByte(s3g.header)
    self.s.ParseByte(len(payload))
    for i in range (0, len(payload)):
      self.s.ParseByte(payload[i])
    self.assertRaises(s3g.PacketResponseCodeError,self.s.ParseByte,s3g.CalculateCRC(payload))

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
    self.s = s3g.PacketStreamDecoder(False)

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

  def test_send_command_timeout(self):
    """
    Time out when no data is received. The input stream should have max_rety_count copies of the
    payload packet in it.
    """
    payload = 'abcde'
    expected_packet = s3g.EncodePayload(payload)

    self.assertRaises(s3g.TransmissionError,self.r.SendCommand, payload)

    #TODO: We should use a queue here, it doesn't make sense to shove this in a file buffer?
    self.inputstream.seek(0)

    for i in range (0, s3g.max_retry_count):
      for byte in expected_packet:
        assert(byte == ord(self.inputstream.read(1)))

  def test_send_command_many_bad_responses(self):
    """
    Passing case: test that the transmission can recover from one less than the alloted
    number of errors.
    """
    payload = 'abcde'
    expected_packet = s3g.EncodePayload(payload)

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend('12345')

    for i in range (0, s3g.max_retry_count - 1):
      self.outputstream.write('a')
    self.outputstream.write(s3g.EncodePayload(response_payload))

    #TODO: We should use a queue here, it doesn't make sense to shove this in a file buffer?
    self.outputstream.seek(0)

    assert(response_payload == self.r.SendCommand(payload))
    #TODO: We should use a queue here, it doesn't make sense to shove this in a file buffer?
    self.inputstream.seek(0)
    for i in range (0, s3g.max_retry_count - 1):
      for byte in expected_packet:
        assert byte == ord(self.inputstream.read(1))

  def test_send_command(self):
    """
    Passing case: Preload the buffer with a correctly formatted expected response, and
    verify that it works correctly.
    """
    payload = 'abcde'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend('12345')

    self.outputstream.write(s3g.EncodePayload(response_payload))
    #TODO: We should use a queue here, it doesn't make sense to shove this in a file buffer?
    self.outputstream.seek(0)

    assert response_payload == self.r.SendCommand(payload)
    assert s3g.EncodePayload(payload) == self.inputstream.getvalue()

  # TODO: Test timing based errors- can we send half a response, get it to re-send, then send a regular response?

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

  def test_get_next_filename_error_codes(self):
    error_codes = [
      'NO_CARD_PRESENT',
      'INITIALIZATION_FAILED',
      'PARTITION_TABLE_ERROR',
      'FILESYSTEM_ERROR',
      'DIRECTORY_ERROR',
    ]
    for error_code in error_codes:
      response_payload = bytearray()
      response_payload.append(s3g.response_code_dict['SUCCESS'])
      response_payload.append(s3g.sd_error_dict[error_code])
      response_payload.append('\x00')
      self.outputstream.write(s3g.EncodePayload(response_payload))
      self.outputstream.seek(0)

      self.assertRaises(s3g.SDCardError,self.r.GetNextFilename,False)

  def test_queue_point(self):
    target = [1,2,3]
    velocity = 6

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

    self.r.QueuePoint(target, velocity)

    packet = bytearray(self.inputstream.getvalue())

    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['QUEUE_POINT']
    for i in range(0, 3):
      assert s3g.EncodeInt32(target[i]) == payload[(i*4+1):(i*4+5)]

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
    target = [1,2,3,4,5]
    velocity = 6

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

    self.r.QueueExtendedPoint(target, velocity)

    packet = bytearray(self.inputstream.getvalue())

    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['QUEUE_EXTENDED_POINT']
    for i in range(0, 5):
      assert s3g.EncodeInt32(target[i]) == payload[(i*4+1):(i*4+5)]

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
    assert payload[2] == s3g.slave_query_command_dict['GET_BUILD_PLATFORM_TEMP']

  def test_toggle_fan(self):
    tool_index = 2
    fan_states = [True, False]

    for fan_state in fan_states:
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

if __name__ == "__main__":
  unittest.main()
