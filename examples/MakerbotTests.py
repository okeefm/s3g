import Makerbot
import unittest
import optparse
import serial
import io
import struct
from array import array
from time import sleep

import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g


heaterTests = True

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
    self.s3g.file = serial.Serial(options.serialPort,'115200', timeout=1)

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
    self.s3g.file = serial.Serial(options.serialPort, '115200', timeout=1)

  def tearDown(self):
    self.s3g.file.close()

  def getToolheadActionPacket(self, tool_index, command, tool_payload):
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
    payload = self.getToolheadActionPacket(toolIndex, s3g.slave_action_command_dict['SET_PLATFORM_TEMP'], tempPayload)
    payload[0] = 255
    self.assertRaises(s3g.TransmissionError, self.s3g.SendCommand, payload)

  def test_badToolIndex(self):
    temperature = 100 
    toolIndex = 2
    tempPayload = bytearray()
    tempPayload.extend(s3g.EncodeUint16(temperature))
    payload = self.getToolheadActionPacket(toolIndex, s3g.slave_action_command_dict['SET_PLATFORM_TEMP'], tempPayload)
    self.assertRaises(s3g.TransmissionError, self.s3g.SendCommand, payload)

  def test_badLength(self):
    temperature = 100
    toolIndex = 2
    tempPayload = bytearray()
    tempPayload.extend(s3g.EncodeUint16(temperature))
    payload = self.getToolheadActionPacket(toolIndex, s3g.slave_action_command_dict['SET_PLATFORM_TEMP'], tempPayload)
    payload[3] = 99
    self.assertRaises(s3g.TransmissionError, self.s3g.SendCommand, payload)

  def test_setPlatformTemperature(self):
    temperature = 100
    toolIndex = 0
    self.assertEqual(self.s3g.SetPlatformTemperature(toolIndex, temperature)[0], s3g.response_code_dict['SUCCESS'])

  def test_setToolheadTemperature(self):
    temperature = 100
    toolhead = 0
    self.assertEqual(self.s3g.SetToolheadTemperature(toolhead, temperature)[0], s3g.response_code_dict['SUCCESS'])

  def test_ToggleValve(self):
    toolhead = 0
    self.assertEqual(self.s3g.ToggleValve(toolhead, True)[0], s3g.response_code_dict['SUCCESS'])

  def test_ToggleFan(self):
    toolhead = 0
    self.assertEqual(self.s3g.ToggleFan(toolhead, True)[0], s3g.response_code_dict['SUCCESS'])

  def test_GetPlatformTemperature(self):
    if heaterTests:
      obsvTemperature = raw_input("\nWhat is the current platform temperature? ")
      self.assertEqual(str(self.s3g.GetPlatformTemperature(0)), str(obsvTemperature))

  def test_GetToolheadTemperature(self):
    if heaterTests:
      obsvTemperature = raw_input("\nWhat is the right extruder's current temperature? ")
      self.assertEqual(str(self.s3g.GetToolheadTemperature(0)), str(obsvTemperature))

  def test_SetPlatformTargetTemperature(self):
    if heaterTests:
      tolerance = 2
      target = 50
      self.s3g.SetPlatformTemperature(0, target)
      minutes = 3
      print "\nWaiting %i mintues to heat the Platform up"%(minutes)
      sleep(60*minutes)
      self.assertTrue(abs(self.s3g.GetPlatformTemperature(0)-target) <= tolerance)
      self.s3g.SetPlatformTemperature(0, 0)

  def test_SetToolheadTemperature(self):
    if heaterTests:
      tolerance = 2
      target = 50
      self.s3g.SetToolheadTemperature(0, target)
      minutes = 3
      print "\nWaiting %i minutes to heat the Toolhead up"%(minutes)
      sleep(60*minutes)
      self.assertTrue(abs(self.s3g.GetToolheadTemperature(0) - target) <= tolerance)
      self.s3g.SetToolheadTemperature(0, 0)
    

  def test_ReadFromEEPROMMighty(self):
    """
    Read the VID/PID settings from the MB and compare against s3g's read from eeprom
    """
    vidPID = self.s3g.ReadFromEEPROM(0x0044, 2)
    vidPID = s3g.DecodeUint16(vidPID)
    mightyVIDPID = [0x23C1, 0xB404]
    self.assertEqual(vidPID, mightyVIDPID[0])

  def test_WriteToEEPROMMighty(self):
    nameOffset = 0x0022
    nameSize = 16
    name = 'ILOVETESTINGALOT'
    self.s3g.WriteToEEPROM(nameOffset, name)
    readName = self.s3g.ReadFromEEPROM(nameOffset, 16)
    self.assertEqual(name, readName)

  def test_ReadFromToolEEPROMMighty(self):
    """
    Read the backoff forward time from the mighty board tool eeprom
    """
    t0Database = 0x0100
    bftOffset = 0x0006
    readBFT = self.s3g.ReadFromToolheadEEPROM(0, bftOffset, 0)
    readBFT = s3g.DecodeUint16(readBFT)
    mightyBFT = 500
    self.assertEqual(mightyBFT, readBFT)

  def test_IsPlatformReady(self):
    """
    Determine if the platform is ready by setting the temperature to its current reading and asking if its ready (should return true, then setting the temperature to double what it is now then querying it agian, expecting a false answer
    """
    curTemp = self.s3g.GetPlatformTemperature(0)
    self.s3g.SetPlatformTemperature(0, curTemp)
    self.assertTrue(self.s3g.IsPlatformReady(0))
    self.s3g.SetPlatformTemperature(0, curTemp+50)
    self.assertEqual(self.s3g.IsPlatformReady(0), False)
    self.s3g.SetPlatformTemperature(0, 0)

  def test_IsToolheadReady(self):
    toolhead = 0
    curTemp = self.s3g.GetToolheadTemperature(toolhead)
    self.s3g.SetToolheadTemperature(toolhead, curTemp)
    self.assertTrue(self.s3g.IsToolReady(toolhead))
    self.s3g.SetToolheadTemperature(toolhead, curTemp + 50)
    self.assertEqual(self.s3g.IsToolReady(toolhead), False)
    self.s3g.SetToolheadTemperature(toolhead, 0)


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-t", "--temperature", dest="heatUp", default="True")
  parser.add_option("-p", "--port", dest="serialPort", default="")
  (options, args) = parser.parse_args()
  if options.heatUp.lower() == "false":
    heaterTests = False
  else:
    print "heatUp flag unrecognized, using default value"
    heaterTests = True
  del sys.argv[1:]
  unittest.main()
