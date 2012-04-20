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
import time
import math

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
(options, args) = parser.parse_args()


r = s3g.s3g()
r.file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)

print "firmware version: %i"%(r.GetVersion())

r.SetPosition([0,0,0])
base_y = 0

def PlayNote(note,duration,base_y):
  freq = 440 * pow(2, (note-49.0)/12)
  speed = 1 / freq * 100000
  distance = duration/speed * 1000000
  base_y += distance
  r.QueuePoint([0,base_y,0], int(speed))
  return base_y

time = .2

for i in [4,4,5,7,7,5,4,2,0,0,2,4,4,2,2]:
 base_y = PlayNote(i+12, time, base_y)

