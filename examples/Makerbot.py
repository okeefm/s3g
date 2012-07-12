import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import serial
import s3g
from time import sleep


class Makerbot(object):
  def __init__(self, serialportname, baudrate, timeout=0):
    self.s3g = s3g.s3g()
    self.serialportname = serialportname
    self.baudrate = baudrate
    self.timeout = timeout
    self.extruders = {'RIGHT':0, 'LEFT':1}

  def Connect(self):
    self.s3g.file = serial.Serial(self.serialportname, self.baudrate, timeout=self.timeout, dsrdtr=True)

  def Disconnect(self):
    self.s3g.file.close()

  def HasToolhead(self, index):
    return index < len(self.extruders)
	
  def get_toolhead_temperature(self, toolhead):
    if not self.HasToolhead(toolhead):
      raise s3g.ProtocolError('Tool index out of range, got=%i, max=%i'%(tool_index, max_tool_index))
    else:
      return self.s3g.get_toolhead_temperature(toolhead)

  def get_platform_temperature(self):
    return self.s3g.get_platform_temperature(0)

  def SetExtruderTemperature(self, toolhead, target):
    if not self.HasToolhead(toolhead):
      raise s3g.ProtocolError('Tool index out of range, got=%i, max=%i'%(tool_index, max_tool_index))
    return self.s3g.set_toolhead_temperature(toolhead, target)

  def set_platform_temperature(self, target):
    self.s3g.set_platform_temperature(0, target)

  def get_version(self):
    self.s3g.get_version()

  def GetExtruderPID(self):
    pid_offsets = [0, 2, 4]
    length = 2
    pid_base = 0x000A
    vals = []
    for offset in pid_offsets:
      value = self.s3g.read_from_EEPROM(pid_base+offset, length)
      vals.append(s3g.decode_uint16(value))
    return vals

  def SetExtruderPID(self, pid_vals):
    pid_offsets = [0, 2, 4]
    length = 2
    pid_base = 0x000A
    for val, offset in zip(pid_vals, pid_offsets):
      self.s3g.write_to_EEPROM(pid_base+offset, val)

  def GetPlatformPID(self):
    pid_offsets = [0, 2, 4]
    length = 2
    pid_base = 0x0010
    vals = []
    for offset in pid_offsets:
      value = self.s3g.read_from_EEPROM(pid_base+offset, length)
      vals.append(s3g.decode_uint16(value))
    return vals

if __name__ == '__main__':
  m = Makerbot('/dev/tty.usbmodemfa131', '115200')
  m.Connect()
  #print m.get_toolhead_temperature(m.extruders['Right'])
  print m.GetExtruderPID()
  m.Disconnect()

