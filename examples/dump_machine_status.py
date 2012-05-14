"""
Read some statistics from a connected machine, and dump them to the console.

Requires these modules:
* pySerial: http://pypi.python.org/pypi/pyserial
"""
# To use this example without installing s3g, we need this hack:
import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g
import serial
import optparse
import binascii

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
parser.add_option("-t", "--toolheads", dest="toolheads",
                  help="toolhead count", type='int', default=2)
parser.add_option("-d", "--dumpeeprom", dest="dump_eeprom",
                  help="dump eeprom data", default=False)
(options, args) = parser.parse_args()


r = s3g.s3g()
r.file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)

print "firmware version: %i"%(r.GetVersion())
print "build name: %s"%(r.GetBuildName())

try:
  sd_name = r.GetNextFilename(True)
  print "SD Card name: " + sd_name
  while True:
    filename = r.GetNextFilename(False)
    if filename == '\x00':
      break
    print '  ' + filename
except s3g.SDCardError:
  print "SD Card error"

print "Available buffer size=%i"%(r.GetAvailableBufferSize())

print "get_position:", r.GetPosition()
print "get_extended_position:", r.GetExtendedPosition()

for tool_index in range(0, options.toolheads):
  print "Tool %i"%(tool_index)
  print "  Version=%i"%(r.GetToolheadVersion(tool_index))
  print "  Extruder_temp=%i"%(r.GetToolheadTemperature(tool_index))
  print "  Extruder_target=%i"%(r.GetToolheadTargetTemperature(tool_index))
  print "  Extruder_ready?=%s"%(r.IsToolReady(tool_index))
  print "  Platform_temp=%i"%(r.GetPlatformTemperature(tool_index))
  print "  Platform_target=%i"%(r.GetPlatformTargetTemperature(tool_index))
  print "  Platform_ready?=%s"%(r.IsPlatformReady(tool_index))


if options.dump_eeprom:
  print "Host EEPROM memory map:"
  for offset in range(0, 1024, 16):
    data = r.ReadFromEEPROM(offset, 16)
    print '%04x'%(offset), binascii.hexlify(buffer(data))

  for tool_index in range(0, options.toolheads):
    print "Tool %i EEPROM memory map:"%(tool_index)
    for offset in range(0, 1024, 16):
      data = r.ReadFromToolheadEEPROM(tool_index, offset, 16)
      print '%04x'%(offset), binascii.hexlify(buffer(data))

