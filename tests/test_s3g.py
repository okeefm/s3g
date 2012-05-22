import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io

import s3g


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

  def test_build_payload(self):
    toAdd = ["a", "b", "c", "d", [1, 2, 3], [4, 5, 6]]
    expectedPayload = bytearray()
    for l in [toAdd[0:4],toAdd[-2], toAdd[-1]]:
      expectedPayload.extend(l)
    payload = self.r.BuildPayload(toAdd)
    self.assertEqual(expectedPayload, payload)

  def test_build_payload_empty(self):
    expectedPayload = bytearray()
    payload = self.r.BuildPayload([])
    self.assertEqual(expectedPayload, payload)

  def test_build_and_send_action_payload(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    cmd = s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW']
    point = [1, 2, 3, 4, 5]
    duration = 42
    relativeAxes = 0
    self.r.BuildAndSendActionPayload([cmd, [s3g.EncodeInt32(cor) for cor in point], s3g.EncodeUint32(duration), relativeAxes])
    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], cmd)
    self.assertEqual(payload[1:5], s3g.EncodeInt32(point[0]))
    self.assertEqual(payload[5:9], s3g.EncodeInt32(point[1]))
    self.assertEqual(payload[9:13], s3g.EncodeInt32(point[2]))
    self.assertEqual(payload[13:17], s3g.EncodeInt32(point[3]))
    self.assertEqual(payload[17:21], s3g.EncodeInt32(point[4]))
    self.assertEqual(payload[21:25], s3g.EncodeInt32(duration))
    self.assertEqual(payload[-1], relativeAxes)

  def test_build_and_send_query_payload(self):
    cmd = s3g.host_query_command_dict['GET_VERSION']
    s3gVersion = s3g.s3g_version
    botVersion = 502
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint16(botVersion))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)
    queryResponsePayload = self.r.BuildAndSendQueryPayload([cmd, s3g.EncodeUint16(botVersion)])
    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], cmd)
    self.assertEqual(payload[1:3], s3g.EncodeUint16(botVersion))
    self.assertEqual(queryResponsePayload[0], s3g.response_code_dict['SUCCESS'])
    self.assertEqual(queryResponsePayload[1:3], s3g.EncodeUint16(botVersion))
    
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

  def test_tool_query_negative_tool_index(self):
    self.assertRaises(
        s3g.ToolIndexError, 
        self.r.ToolQuery, 
        -1, 
        s3g.slave_query_command_dict['GET_VERSION']
        )

  def test_tool_query_too_high_tool_index(self):
    self.assertRaises(
        s3g.ToolIndexError, 
        self.r.ToolQuery, 
        s3g.max_tool_index+1, 
        s3g.slave_query_command_dict['GET_VERSION']
        )

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

    self.assertRaises(s3g.EEPROMLengthError,self.r.ReadFromEEPROM,offset, length)

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

    self.assertRaises(s3g.EEPROMLengthError,self.r.WriteToEEPROM, offset, data)

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

    self.assertRaises(s3g.EEPROMMismatchError, self.r.WriteToEEPROM,offset, data)

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

    for error_code in s3g.sd_error_dict:
      if error_code != 'SUCCESS':
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
    for error_code in s3g.sd_error_dict:
      if error_code != 'SUCCESS':
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
    self.assertRaises(s3g.ButtonError, self.r.WaitForButton, button, 0, False, False, False)

  def test_wait_for_button(self):
    button = 0x10
    options = 0x02 + 0x04 # TODO: Explain what these mean
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
    song_id = 1

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.QueueSong(song_id)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['QUEUE_SONG'])
    self.assertEqual(payload[1], song_id)

  def test_reset_to_factory(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.ResetToFactory()

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['RESET_TO_FACTORY'])
    self.assertEqual(payload[1], 0x00) # Reserved byte

  def test_set_build_percent(self):
    percent = 42

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.SetBuildPercent(percent)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['SET_BUILD_PERCENT'])
    self.assertEqual(payload[1], percent)
    self.assertEqual(payload[2], 0x00) # Reserved byte

  def test_display_message(self):
    row = 0x12
    col = 0x34
    timeout = 5
    message = 'abcdefghij'
    clear_existing = True
    last_in_group = True
    wait_for_button = True

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.DisplayMessage(row, col, message, timeout, clear_existing, last_in_group, wait_for_button)
    
    expectedBitfield = 0x01+0x02+0x04 # TODO: Explain this

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    assert payload[0] == s3g.host_action_command_dict['DISPLAY_MESSAGE']
    assert payload[1] == expectedBitfield
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

  def test_queue_point_short_length(self):
    point = [0,1]
    rate = 500
    self.assertRaises(s3g.PointLengthError, self.r.QueuePoint, point, rate)

  def test_queue_point_long_length(self):
    point = [0, 1, 2, 3]
    rate = 500
    self.assertRaises(s3g.PointLengthError, self.r.QueuePoint, point, rate)

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

  def test_set_position_short_length(self):
    self.assertRaises(s3g.PointLengthError, self.r.SetPosition, [1, 2])

  def test_set_position_long_length(self):
    self.assertRaises(s3g.PointLengthError, self.r.SetPosition, [1, 2, 3, 4])

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

  def test_tool_action_command_negative_tool_index(self):
      self.assertRaises(
          s3g.ToolIndexError,
          self.r.ToolActionCommand,
          -1, 
          s3g.slave_action_command_dict['INIT']
          )

  def test_tool_action_command_too_high_tool_index(self):
      self.assertRaises(
          s3g.ToolIndexError,
          self.r.ToolActionCommand,
          s3g.max_tool_index+1,
          s3g.slave_action_command_dict['INIT']
          )
                      

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

  def test_queue_extended_point_long_length(self):
    point = [1, 2, 3, 4, 5, 6]
    rate = 500
    self.assertRaises(s3g.PointLengthError, self.r.QueueExtendedPoint, point, rate)

  def test_queue_extended_point_short_length(self):
    point = [1, 2, 3, 4]
    rate = 500
    self.assertRaises(s3g.PointLengthError, self.r.QueueExtendedPoint, point, rate)

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

  def test_set_extended_position_short_length(self):
    self.assertRaises(s3g.PointLengthError, self.r.SetExtendedPosition, [1, 2, 3, 4])

  def test_set_extended_position_long_length(self):
    self.assertRaises(s3g.PointLengthError, self.r.SetExtendedPosition, [1, 2, 3, 4, 5, 6])

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
    filename = 'test'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(s3g.sd_error_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.CaptureToFile(filename)
    
    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_query_command_dict['CAPTURE_TO_FILE'])
    self.assertEqual(payload[1:-1], filename)
    self.assertEqual(payload[-1], 0x00)

  def test_capture_to_file_errors(self):
    filename = 'test'

    for error_code in s3g.sd_error_dict:
      if error_code != 'SUCCESS':
        response_payload = bytearray()
        response_payload.append(s3g.response_code_dict['SUCCESS'])
        response_payload.append(s3g.sd_error_dict[error_code])
        self.outputstream.write(s3g.EncodePayload(response_payload))
        self.outputstream.seek(0)

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
    axes = ['x','z','b']

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.StoreHomePositions(axes)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['STORE_HOME_POSITIONS'])
    self.assertEqual(payload[1], s3g.EncodeAxes(axes))

  def test_set_beep(self):
    frequency = 1
    duration = 2

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.SetBeep(frequency, duration)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['SET_BEEP'])
    self.assertEqual(payload[1:3], s3g.EncodeUint16(frequency))
    self.assertEqual(payload[3:5], s3g.EncodeUint16(duration))
    self.assertEqual(payload[5], 0x00) # reserved byte

  def test_set_rgb_led(self):
    r = 255
    g = 254
    b = 253
    blink = 252

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.SetRGBLED(r, g, b, blink)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertTrue(payload[0], s3g.host_action_command_dict['SET_POT_VALUE'])
    self.assertEqual(payload[1], r)
    self.assertEqual(payload[2], g)
    self.assertEqual(payload[3], b)
    self.assertEqual(payload[4], blink)
    self.assertEqual(payload[5], 0x00) # reserved byte

  def test_set_potentiometer_value(self):
    axes = ['x', 'y', 'z', 'a', 'b']
    value = 2

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.SetPotentiometerValue(axes, value)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['SET_POT_VALUE'])
    self.assertEqual(payload[1], s3g.EncodeAxes(axes))
    self.assertEqual(payload[2], value)

  def test_recall_home_positions(self):
    axes = ['x','z','b']

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.RecallHomePositions(axes)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['RECALL_HOME_POSITIONS'])
    self.assertEqual(payload[1], s3g.EncodeAxes(axes))

  def test_queue_extended_point_new_short_length(self):
    point = [1, 2, 3, 4]
    duration = 0
    relative_axes = ['x']

    self.assertRaises(s3g.PointLengthError, self.r.QueueExtendedPointNew, point, duration, relative_axes)
  
  def test_queue_extended_point_new_long_length(self):
    point = [1, 2, 3, 4, 5, 6]
    duration = 0
    relative_axes = ['x']

    self.assertRaises(s3g.PointLengthError, self.r.QueueExtendedPointNew, point, duration, relative_axes)
    

  def test_queue_extended_point_new(self):
    point = [1, -2, 3, -4, 5]
    duration = 10
    relative_axes = ['x','z','b']

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.QueueExtendedPointNew(point, duration, relative_axes)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['QUEUE_EXTENDED_POINT_NEW'])
    self.assertEqual(payload[1:5], s3g.EncodeInt32(point[0]))
    self.assertEqual(payload[5:9], s3g.EncodeInt32(point[1]))
    self.assertEqual(payload[9:13], s3g.EncodeInt32(point[2]))
    self.assertEqual(payload[13:17], s3g.EncodeInt32(point[3]))
    self.assertEqual(payload[17:21], s3g.EncodeInt32(point[4]))
    self.assertEqual(payload[21:25], s3g.EncodeUint32(duration))
    self.assertEqual(payload[25], s3g.EncodeAxes(relative_axes))
    

  def test_wait_for_platform_ready(self):
    toolhead = 0
    delay = 100
    timeout = 60

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.WaitForPlatformReady(toolhead, delay, timeout)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['WAIT_FOR_PLATFORM_READY'])
    self.assertEqual(payload[1], toolhead)
    self.assertEqual(payload[2:4], s3g.EncodeUint16(delay))
    self.assertEqual(payload[4:], s3g.EncodeUint16(timeout))

  def test_wait_for_tool_ready(self):
    toolhead = 0
    delay = 100
    timeout = 60

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)


    self.r.WaitForToolReady(toolhead, delay, timeout)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_action_command_dict['WAIT_FOR_TOOL_READY'])
    self.assertEqual(payload[1], toolhead)
    self.assertEqual(payload[2:4], s3g.EncodeUint16(delay))
    self.assertEqual(payload[4:], s3g.EncodeUint16(timeout))
    
  def test_toggle_axes(self):
    axes = ['x','y','b']
    enable_flag = True

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.ToggleAxes(axes, enable_flag)

    bitfield = s3g.EncodeAxes(axes)
    bitfield |= 0x80 # because 'enable_flag is set

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_action_command_dict['ENABLE_AXES'])
    self.assertEqual(payload[1], bitfield)

  def test_delay(self):
    delay = 50

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.r.Delay(delay)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_action_command_dict['DELAY'])
    self.assertEqual(payload[1:], s3g.EncodeUint32(delay))

  def test_get_communication_stats(self):
    stats = {
      'PacketsReceived' : 0,
      'PacketsSent' : 1,
      'NonResponsivePacketsSent' : 2,
      'PacketRetries' : 3,
      'NoiseBytes' : 4,
    }

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend(s3g.EncodeUint32(stats['PacketsReceived']))
    response_payload.extend(s3g.EncodeUint32(stats['PacketsSent']))
    response_payload.extend(s3g.EncodeUint32(stats['NonResponsivePacketsSent']))
    response_payload.extend(s3g.EncodeUint32(stats['PacketRetries']))
    response_payload.extend(s3g.EncodeUint32(stats['NoiseBytes']))

    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    info = self.r.GetCommunicationStats()
    self.assertEqual(info, stats)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_query_command_dict['GET_COMMUNICATION_STATS'])

  def test_get_motherboard_status(self):
    flags = {
      'POWER_ERROR' : 1
    }

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

    self.assertEqual(flags, responseFlags)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)
    self.assertEqual(payload[0], s3g.host_query_command_dict['GET_MOTHERBOARD_STATUS'])    


  def test_extended_stop(self):
    expected_states = [
      [False, False, 0x00],
      [True, False, 0x01],
      [False, True, 0x02],
      [True, True, 0x03],
    ]

    for expected_state in expected_states:
      response_payload = bytearray()
      response_payload.append(s3g.response_code_dict['SUCCESS'])
      response_payload.append(0)
      self.outputstream.write(s3g.EncodePayload(response_payload))
      self.outputstream.seek(0)
      self.inputstream.seek(0)
    
      self.r.ExtendedStop(expected_state[0], expected_state[1])

      packet = bytearray(self.inputstream.getvalue())
      payload = s3g.DecodePacket(packet)

      self.assertEqual(payload[0], s3g.host_query_command_dict['EXTENDED_STOP'])
      self.assertEqual(payload[1], expected_state[2])

  def test_extended_stop_error(self):
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.append(1)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertRaises(s3g.ExtendedStopError, self.r.ExtendedStop, True, True)

  def test_get_pid_state(self):
    expectedDict = {
      "ExtruderError"    : 1,
      "ExtruderDelta"    : 1,
      "exLastTerm"       : 1,
      "PlatformError"    : 1,
      "PlatformDelta"    : 1,
      "PlatformLastTerm" : 1,
    }

    toolIndex = 0
    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    for i in range(6):
      response_payload.extend(s3g.EncodeUint16(1))
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

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
    expectedDict = {
      "ExtruderReady" : True,
      "PlatformError" : True,
      "ExtruderError" : True,
    }

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    returnBitfield = 0xFF

    response_payload.append(returnBitfield)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    self.assertEqual(expectedDict, self.r.GetToolStatus(toolIndex))

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    self.assertEqual(payload[0], s3g.host_query_command_dict['TOOL_QUERY'])
    self.assertEqual(payload[1], toolIndex)
    self.assertEqual(payload[2], s3g.slave_query_command_dict['GET_TOOL_STATUS'])
 

  def test_get_motor_speed(self):
    toolIndex = 0
    speed = 100

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

    self.assertRaises(s3g.HeatElementReadyError, self.r.IsToolReady, tool_index)

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

    self.assertRaises(s3g.EEPROMLengthError,self.r.ReadFromToolheadEEPROM, tool_index, offset, length)

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

    self.assertRaises(s3g.EEPROMLengthError,self.r.WriteToToolheadEEPROM, tool_index, offset, data)

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

    self.assertRaises(s3g.EEPROMMismatchError, self.r.WriteToToolheadEEPROM, tool_index, offset, data)

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

    self.assertRaises(s3g.HeatElementReadyError, self.r.IsPlatformReady, tool_index)

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

    self.r.SetToolheadTemperature(tool_index, temp)

    packet = bytearray(self.inputstream.getvalue())
    payload = s3g.DecodePacket(packet)

    assert payload[0] == s3g.host_action_command_dict['TOOL_ACTION_COMMAND']
    assert payload[1] == tool_index
    assert payload[2] == s3g.slave_action_command_dict['SET_TOOLHEAD_TARGET_TEMP']
    assert payload[3] == 2 #Temp is a byte of len 2
    assert payload[4] == temp
	

  def test_set_platform_temp(self):
    tool_index = 2
    temp = 100

    self.outputstream.seek(0)
    self.outputstream.truncate(0)

    self.outputstream.write(s3g.EncodePayload([s3g.response_code_dict['SUCCESS']]))
    self.outputstream.seek(0)

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
