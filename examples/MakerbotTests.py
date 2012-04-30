import Makerbot
import unittest
from optparse import OptionParser
import serial
import io

import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g


class SendPacketTests(unittest.TestCase):
  
  def setUp(self):
    self.s3g = s3g.s3g()
    self.outputstream = io.BytesIO() # Stream that we will send responses on
    self.inputstream = io.BytesIO()  # Stream that we will receive commands on
    self.file = io.BufferedRWPair(self.outputstream, self.inputstream)
    self.s3g.file = self.file

  def tearDown(self):
    self.s3g = None
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

    self.assertRaises(s3g.TransmissionError,self.s3g._SendPacket, packet)
    self.inputstream.seek(0)

    for i in range (0, s3g.max_retry_count):
      for byte in expected_packet:
        assert byte == ord(self.inputstream.read(1))

  def test_send_command_many_bad_responses(self):
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

    assert response_payload == self.s3g._SendPacket(packet)

    self.inputstream.seek(0)
    for i in range (0, s3g.max_retry_count - 1):
      for byte in expected_packet:
        assert byte == ord(self.inputstream.read(1))

  
  def test_sendPacket(self):
    """
    Passing case: Preload the buffer with a correctly formatted expected response, and
    verify that it works correctly.
    """
    payload = 'abcde'

    response_payload = bytearray()
    response_payload.append(s3g.response_code_dict['SUCCESS'])
    response_payload.extend('12345')
    packet = s3g.EncodePayload(payload)
    self.outputstream.write(s3g.EncodePayload(response_payload))
    self.outputstream.seek(0)

    assert response_payload == self.s3g._SendPacket(packet)
    assert s3g.EncodePayload(payload) == self.inputstream.getvalue()


class s3gPacketTests(unittest.TestCase):
  def setUp(self):
    self.s3g = s3g.s3g()
    self.s3g.file = serial.Serial('/dev/tty.usbmodemfa131', '115200', timeout=1)

  def tearDown(self):
    self.s3g.file.close()

  def getVersionPacket(self):
    """
    Helper method to generate a Get Version packet to be modified and sent
    """
    payload = bytearray()
    payload.append(s3g.host_query_command_dict['GET_VERSION'])
    payload.extend(s3g.EncodeUint16(s3g.s3g_version))
    return s3g.EncodePayload(payload)

  """def test_emptyPayload(self):
    payload = bytearray()
    self.assertRaises(s3g.TransmissionError, self.s3g.SendCommand, payload)"""

  def test_emptyPacket(self):
    packet = bytearray()
    self.assertRaises(s3g.TransmissionError, self.s3g._SendPacket, packet)

  def test_trailingPacket(self):
    """
    Test putting bad information right after a packet
    """
    packet = self.getVersionPacket()
    addition = bytearray('\xff\xff')
    packet.extend(addition)
    self.assertRaises(s3g.TransmissionError, self.s3g._SendPacket, packet)

  def test_preceedingPacket(self):
    """
    Test putting bad information right before a packet
    """
    packet = self.getVersionPacket()
    addition = bytearray('\xa4\x5f')
    addition.extend(packet)
    self.assertRaises(s3g.TransmissionError, self.s3g._SendPacket, addition)

  def test_badCRC(self):
    packet = self.getVersionPacket()
    packet[-1] = '\x00' 
    self.assertRaises(s3g.TransmissionError, self.s3g._SendPacket, packet)

  def test_badLength(self):
    packet = self.getVersionPacket()
    packet[1] = '\xff'
    self.assertRaises(s3g.TransmissionError, self.s3g._SendPacket, packet)

  def test_intermittentBadBytes(self):
    """
    Tests putting a random byte into the formed payload
    """
    packet = self.getVersionPacket()
    packet.insert(2, '\x4a')
    self.assertRaises(s3g.TransmissionError, self.s3g.SendCommand, packet)

  def test_badHeader(self):
    packet = self.getVersionPacket()
    packet[0] = 0x00
    self.assertRaises(s3g.TransmissionError, self.s3g._SendPacket, packet)

class ToolheadActionCommands(unittest.TestCase):

  def setUp(self):
    self.s3g = s3g.s3g()
    self.s3g.file = serial.Serial('/dev/tty.usbmodemfa131', '115200', timeout=1)

  def tearDown(self):
    self.s3g.file.close()

  def getToolheadPacket(self, tool_index, command, tool_payload):
    payload = bytearray()
    payload.append(s3g.host_action_command_dict['TOOL_ACTION_COMMAND'])
    payload.append(tool_index)
    payload.append(command)
    payload.append(len(tool_payload))
    payload.extend(tool_payload)
    return payload
  

  def test_badHeader(self):
    temperature = 100
    toolIndex = 0
    tempPayload = bytearray()
    tempPayload.extend(s3g.EncodeUint16(temperature))
    payload = self.getToolheadPacket(toolIndex, s3g.slave_action_command_dict['SET_PLATFORM_TEMP'], tempPayload)
    payload[0] = 255
    self.assertRaises(s3g.TransmissionError, self.s3g.SendCommand, payload)

  def test_badToolIndex(self):
    temperature = 100 
    toolIndex = 2
    tempPayload = bytearray()
    tempPayload.extend(s3g.EncodeUint16(temperature))
    payload = self.getToolheadPacket(toolIndex, s3g.slave_action_command_dict['SET_PLATFORM_TEMP'], tempPayload)
    self.assertRaises(s3g.TransmissionError, self.s3g.SendCommand, payload)

  def test_badLength(self):
    temperature = 100
    toolIndex = 2
    tempPayload = bytearray()
    tempPayload.extend(s3g.EncodeUint16(temperature))
    payload = self.getToolheadPacket(toolIndex, s3g.slave_action_command_dict['SET_PLATFORM_TEMP'], tempPayload)
    payload[3] = 99
    self.assertRaises(s3g.TransmissionError, self.s3g.SendCommand, payload)

  def test_setPlatformTemp(self):
    temperature = 100
    toolIndex = 0
    self.assertEqual(self.s3g.SetPlatformTemperature(toolIndex, temperature)[0], s3g.response_code_dict['SUCCESS'])

  def test_setToolheadTemperature(self):
    temperature = 100
    for toolhead in [0, 1]:
      self.assertEqual(self.s3g.SetToolheadTemperature(toolhead, temperature)[0], s3g.response_code_dict['SUCCESS'])

  def test_ToggleValve(self):
    toolhead = 0
    self.assertEqual(self.s3g.ToggleValve(toolhead, True)[0], s3g.response_code_dict['SUCCESS'])


if __name__ == '__main__':
  unittest.main()
