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


parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
(options, args) = parser.parse_args()


r = s3g.s3g()
r.file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)

print "firmware version: %i"%(r.GetVersion())
print "build name: %s"%(r.GetBuildName())

try:
  print "SD Card name: " + r.GetNextFilename(True)
  while True:
    filename = r.GetNextFilename(False)
    if filename == '\x00':
      break
    print ' ' + filename
except s3g.SDCardError:
  print "SD Card error"

print "Available buffer size=%i"%(r.GetAvailableBufferSize())

print "toolhead_0=%i, toolhead_1=%i, platform=%i"%(
  r.GetToolheadTemperature(0),
  r.GetToolheadTemperature(1),
  r.GetPlatformTemperature(0)
 )
