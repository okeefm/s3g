import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import serial
import optparse

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="port",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="ReplicatorDual")
parser.add_option("-u", "--unload", dest="unload",
									help="unload filament", default=False, action="store_true")
parser.add_option("-t", "--toolhead", dest="toolhead",
									help="toolhead to load/unload", default=0)	

(options, args) = parser.parse_args()

r = makerbot_driver.s3g.from_filename(options.port)
r.clear_buffer()
r.set_toolhead_temperature(options.toolhead, 220)
r.wait_for_tool_ready(options.toolhead, 100, 600)
if options.toolhead == 0:
	toolhead = 'A'
else:
	toolhead = 'B'
speed = 3000
if options.unload:
	r.find_axes_maximums([toolhead], speed, 60)
else:
	r.find_axes_minimums([toolhead], speed, 60)
