import Makerbot
import unittest
from optparse import OptionParser
import serial

import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g


class s3gPacketTests(unittest.TestCase):
  def setUp(self):
    self.s3g = s3g.s3g()
    self.s3g.file = serial.Serial('/dev/tty.usbmodemfa131', '115200')

  def tearDown(self):
    self.s3g.file.close()

  def test_BadPacket(self):
    payload = bytearray()
    self.s3g.SendCommand(payload)

class s3gEncoderTests(unittest.TestCase):
  def setUp(self):
    self.s3g = s3g.s3g()
    self.s3g.file = serial.Serial('/dev/tty.usbmodemfa131', '115200')
    self.validToolheads = [0, 1]

  def tearDown(self):
    self.s3g.file.close()



  def test_SetPlatformTemp(self):
    self.s3g.SetPlatformTemperature(0, 100)
    self.assertRaises(s3g.PacketResponseCodeError, self.s3g.SetPlatformTemperature, 1, 100)
    self.assertRaises(s3g.ProtocolError, self.s3g.SetPlatformTemperature, -1, 100)
    self.assertRaises(s3g.ProtocolError, self.s3g.SetPlatformTemperature, 0, True)
    self.assertRaises(s3g.ProtocolError, self.s3g.SetPlatformTemperature, 0, 'a')

  def test_SetExtruderTemp(self):
    for tool in self.validToolheads:
      self.s3g.SetExtruderTemperature(0, 200)
      self.s3g.SetExtruderTemperature(0, 0)
    self.assertRaises(s3g.PacketResponseCodeError, self.s3g.SetExtruderTemperature, 2, 200)
    self.assertRaises(s3g.ProtocolError, self.s3g.SetExtruderTemperature, -1, 200)
    self.assertRaises(s3g.ProtocolError, self.s3g.SetExtruderTemperature, 0, True)
    self.assertRaises(s3g.ProtocolError, self.s3g.SetExtruderTemperature, 0, 'a')

  def test_ToggleValve(self):
    for tool in self.validToolheads:
      self.s3g.ToggleValve(tool, True)
      self.s3g.ToggleValve(tool, False)
    self.assertRaises(s3g.PacketResponseCodeError, self.s3g.ToggleValve, 2, True)
    self.assertRaises(s3g.ProtocolResponse, self.s3g.ToggleValve, -1, True)
    self.assertRaises(G

"""def test_ToggleValve(self):
    for toolhead in self.validToolheads:
      try:
        self.s3g.ToggleValve(toolhead, True)
        self.s3g.ToggleValve(toolhead, False)
        assert True
      except s3g.PacketError:
        assert False
    try:
      self.s3g.ToggleValve(-1, True)
      assert False
    except s3g.ProtocolError:
      assert True
    try:
      self.s3g.ToggleValve(2, True)
      assert False
    except s3g.PacketResponseCodeError:
      assert True

  def test_ToggleFan(self):
    for toolhead in self.validToolheads:
      try:
        self.s3g.ToggleFan(toolhead, True)
        self.s3g.ToggleFan(toolhead, False)
        assert True
      except s3g.PacketError:
        assert False
    try:
      self.s3g.ToggleFan(-1, True)
      assert False
    except s3g.ProtocolError:
      assert True
    try:
      self.s3g.ToggleFan(2, True)
      assert False
    except s3g.PacketResponseCodeError:
      assert True
    
  def test_IsPlatformReady(self):
    try:
      self.s3g.IsPlatformReady(0)
      assert True
    except s3g.PacketError:
      assert False
    try:
      self.s3g.IsPlatformReady(-1)
      assert False
    except s3g.ProtocolError:
      assert True
    try:
      self.s3g.IsPlatformReady(1)
      assert False
    except s3g.PacketResponseCodeError:
      assert True
"""
def makeBot():
  return Makerbot.Makerbot('/dev/tty.usbmodemfa131', "115200")

class MakerbotFunctionTests():
  def setUp(self):
    self.m = makeBot()
    self.m.Connect()
    self.s3g = s3g.s3g()
    self.s3g.file = serial.Serial('/dev/tty.usbmodemfa131', '115200', timeout=0)

  def tearDown(self):
    self.m.Disconnect()
    self.s3g.file.close()
    self.m = None

  def test_Send(self):
    s3gVersion = self.s3g.GetVersion()
    mbotVersion = self.m.Send(self.s3g.GetVersion)
    assert s3gVersion == mbotVersion

  def test_HasToolhead(self):
    assert self.m.HasToolhead(0) == True
    assert self.m.HasToolhead(2) == False

  def test_GetVersion(self):
    assert self.s3g.GetVersion() == self.m.GetVersion()

  def test__GetExtruderTemp(self):
    for extruder in self.m.extruders:
      assert self.s3g.GetToolheadTemperature(self.m.extruders[extruder]) == self.m.GetToolheadTemperature(self.m.extruders[extruder])

  def test_GetPlatformTemp(self):
    assert self.s3g.GetPlatformTemperature(0) == self.m.GetPlatformTemperature()
  
  def test_SetExtruderTemp(self):
    temp = 200
    for extruder in self.m.extruders:
      self.m.SetExtruderTemperature(self.m.extruders[extruder], temp)
      assert self.s3g.GetToolheadTargetTemperature(self.m.extruders[extruder]) == temp  
    for extruder in self.m.extruders:
      self.m.SetExtruderTemperature(self.m.extruders[extruder], 0)

  def test_SetPlatformTemp(self):
    temp = 100
    self.m.SetPlatformTemperature(temp)
    assert self.s3g.GetPlatformTargetTemperature(0) == temp
    self.m.SetPlatformTemperature(0)

if __name__ == '__main__':
  unittest.main()
