import Makerbot
import unittest
import optparse
import serial
import io
import struct
from array import array
import time

import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g


extensive = True
port = ''
hasInterface = True

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


  def test_GetVersionPacket(self):
    packet = self.getVersionPacket()
    for i in range(20):
      self.s3g.file.write(packet)
      self.s3g.file.flush()
    self.assertTrue(True)

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

class s3gCanSendCommands(unittest.TestCase):
  def setUp(self):
    self.s3g = s3g.s3g()
    self.s3g.file = serial.Serial(options.serialPort, '115200', timeout=1)

  def tearDown(self):
    self.s3g.file.close()

  def test_InitReply(self):
    self.s3g.Init()
    self.assertTrue(True)

  def test_ToggleValveReply(self):
    self.s3g.ToggleFan(0, False)
    self.assertTrue(True)

  def test_ToggleFanReply(self):
    self.s3g.ToggleFan(0, False)
    self.assertTrue(True)

  def test_IsPlatformReadyReply(self):
    self.s3g.IsPlatformReady(0)
    self.assertTrue(True)

  def test_GetPlatformTargetTemperature(self):
    self.s3g.GetPlatformTargetTemperature(0)
    self.assertTrue(True)

  def test_GetToolheadTargetTemperatureReply(self):
    self.s3g.GetToolheadTargetTemperature(0)
    self.assertTrue(True)

  def test_ReadFromToolheadEEPROM(self):
    self.s3g.ReadFromToolheadEEPROM(0, 0x00, 0)
    self.assertTrue(True)

  def test_IsToolReadyReply(self):
    self.s3g.IsToolReady(0)
    self.assertTrue(True)

  def test_GetToolheadTemperatureReply(self):
    self.s3g.GetToolheadTemperature(0)
    self.assertTrue(True)

  def test_GetToollheadVersionReply(self):
    self.s3g.GetToolheadVersion(0)
    self.assertTrue(True)

  def test_BuildEndNotificationReply(self):
    self.s3g.BuildEndNotification()
    self.assertTrue(True)

  def test_BuildStartNotificationReply(self):
    self.s3g.BuildStartNotification(0, 'aTest')
    self.assertTrue(True)

  def test_DisplayMessageReply(self):
    self.s3g.DisplayMessage(0, 0, "TESTING", .1, False)
    self.assertTrue(True)

  def test_FindAxesMaximumsReply(self):
    self.s3g.FindAxesMaximums(['x', 'y', 'z'], 1, 0)
    self.assertTrue(True)

  def test_FindAxesMinimumsReply(self):
    self.s3g.FindAxesMinimums(['x', 'y', 'z'], 1, 0)
    self.assertTrue(True)

  def test_GetBuildNameReply(self):
    self.s3g.GetBuildName()
    self.assertTrue(True)

  def test_GetNextFilenameReply(self):
    self.s3g.GetNextFilename(False)
    self.assertTrue(True)

  def test_PlaybackCaptureReply(self):
    self.assertRaises(s3g.SDCardError, self.s3g.PlaybackCapture, 'aTest')

  def test_AbortImmediatelyReply(self):
    self.s3g.AbortImmediately()
    self.assertTrue(True)

  def test_GetAvailableBufferSizeReply(self):
    self.s3g.GetAvailableBufferSize()
    self.assertTrue(True)

  def test_ReadFromEEPROMReply(self):
    self.s3g.ReadFromEEPROM(0x00, 0)
    self.assertTrue(True)

  def test_GetVersionReply(self):
    self.s3g.GetVersion()
    self.assertTrue(True)

  def test_SetPlatformTemperatureReply(self):
    temperature = 100
    toolhead = 0
    self.s3g.SetPlatformTemperature(toolhead, temperature)
    self.s3g.SetPlatformTemperature(toolhead, 0)
    self.assertTrue(True)

  def test_SetToolheadTemperatureReply(self):
    temperature = 100
    toolhead = 0
    self.s3g.SetToolheadTemperature(toolhead, temperature)
    self.s3g.SetToolheadTemperature(toolhead, 0)
    self.assertTrue(True)

  def test_ToggleValveReply(self):
    toolhead = 0
    self.s3g.ToggleValve(toolhead, True)
    self.s3g.ToggleValve(toolhead, False)
    self.assertTrue(True)

  def test_ToggleFanReply(self):
    toolhead = 0
    self.s3g.ToggleFan(toolhead, True)
    self.s3g.ToggleFan(toolhead, False)
    self.assertTrue(True)

  def test_GetPositionReply(self):
    self.s3g.GetPosition()[0]
    self.assertTrue(True)

  def test_GetExtendedPositionReply(self):
    self.s3g.GetExtendedPosition()[0]
    self.assertTrue(True)

  def test_QueuePointReply(self):
    position = [0, 0, 0]
    rate = 500
    self.s3g.QueuePoint(position, rate)
    self.assertTrue(True)

  def test_SetPositionReply(self):
    position = [0, 0, 0]
    self.s3g.SetPosition(position)
    self.assertTrue(True)

  def test_QueueExtendedPointReply(self):
    position = [0, 0, 0, 0, 0]
    rate = 500
    self.s3g.QueueExtendedPoint(position, rate)
    self.assertTrue(True)

  def test_SetExtendedPositionReply(self):
    position = [0, 0, 0, 0, 0]
    self.s3g.SetExtendedPosition(position)
    self.assertTrue(True)


class s3gFunctionTesting(unittest.TestCase):
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

  def test_GetPlatformTemperature(self):
    if extensive:
      obsvTemperature = raw_input("\nWhat is the current platform temperature? ")
      self.assertEqual(str(self.s3g.GetPlatformTemperature(0)), str(obsvTemperature))

  def test_GetToolheadTemperature(self):
    if extensive:
      obsvTemperature = raw_input("\nWhat is the right extruder's current temperature? ")
      self.assertEqual(str(self.s3g.GetToolheadTemperature(0)), str(obsvTemperature))

  def test_SetPlatformTargetTemperature(self):
    if extensive:
      tolerance = 2
      target = 50
      self.s3g.SetPlatformTemperature(0, target)
      minutes = 3
      print "\nWaiting %i mintues to heat the Platform up"%(minutes)
      time.sleep(60*minutes)
      self.assertTrue(abs(self.s3g.GetPlatformTemperature(0)-target) <= tolerance)
      self.s3g.SetPlatformTemperature(0, 0)

  def test_SetToolheadTemperature(self):
    if extensive:
      tolerance = 2
      target = 50
      self.s3g.SetToolheadTemperature(0, target)
      minutes = 3
      print "\nWaiting %i minutes to heat the Toolhead up"%(minutes)
      time.sleep(60*minutes)
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
    readBFT = self.s3g.ReadFromToolheadEEPROM(0, bftOffset, 2)
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

  def test_DisplayMessage(self):
    message = str(time.clock())
    self.s3g.DisplayMessage(0, 0, message, 10, False)
    readMessage = raw_input("\nWhat is the message on the replicator's display? ")
    self.assertEqual(message, readMessage)

  def test_GetPosition(self):
    position = self.s3g.GetPosition()[0]
    self.assertEqual(position, [0, 0, 0])

  def test_GetExtendedPosition(self):
    position = self.s3g.GetExtendedPosition()[0]
    self.assertEqual(position, [0, 0, 0, 0, 0])

  def test_SetPositionCheck(self):
    position = [1, 2, 3]
    self.s3g.SetPosition(position)
    self.assertEqual(position, self.s3g.GetPosition()[0])
    self.s3g.SetPosition([0, 0, 0])

  def test_SetExtendedPositionCheck(self):
    position = [1, 2, 3, 4, 5]
    self.s3g.SetExtendedPosition(position)
    self.assertEqual(position, self.s3g.GetExtendedPosition()[0])
    self.s3g.SetExtendedPosition([0, 0, 0, 0, 0])

  def test_QueuePointCheck(self):
    startPosition = [0, 0, 0]
    newPosition = [1, 2, 3]
    rate = 500
    self.s3g.SetPosition(startPosition)
    self.s3g.QueuePoint(newPosition, rate)
    self.assertEqual(newPosition, self.s3g.GetPosition()[0])
    self.s3g.SetPosition(startPosition)

  def test_QueueExtendedPositionCheck(self):
    startPosition = [0, 0, 0, 0, 0]
    newPosition = [1, 2, 3, 4, 5]
    rate = 500
    self.s3g.SetExtendedPosition(startPosition)
    self.s3g.QueueExtendedPoint(newPosition, rate)
    self.assertEqual(newPosition, self.s3g.GetExtendedPosition()[0])
    self.s3g.SetExtendedPosition(startPosition())

  def test_FindAxesMin(self):
    axes = ['x', 'y', 'z']
    rate = 500
    timeout = 2
    self.s3g.FindAxesMinimums(axes, rate, timeout)
    self.assertTrue(True)

  def test_FindAxesMax(self):
    axes = ['x', 'y', 'z']
    rate = 500
    timeout = 2
    self.s3g.FindAxesMaximums(axes, rate, timeout)
    self.assertTrue(True)

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-e", "--extensive", dest="extensive", default="True")
  parser.add_option("-m", "--mightyboard", dest="isMightyBoard", default="True")
  parser.add_option("-t", "--tom", dest="isTOM", default="False")
  parser.add_option("-i", "--interface", dest="hasInterface", default="True")
  parser.add_option("-p", "--port", dest="serialPort", default="/dev/tty.usbmodemfa131")
  (options, args) = parser.parse_args()
  if options.extensive.lower() == "false":
    print "Forgoing Heater Tests"
    extensive= False
  if options.hasInterface.lower() == "false":
    print "Forgoing Tests requiring Interface Boards"
    hasInterface = False
    
  del sys.argv[1:]
  print "*****To do many of these tests, your printer must be reset immediately prior to execution.  If you haven't, please reset your robot and run these tests again!!!*****"
  print "*****Because We are going to be moving the axes around, you should probably move the gantry to the middle of the build area and the Z platform to about halfway!!!*****"
  unittest.main()
