import os
import sys
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
parser.add_option("-f", "--filename", dest="filename",
                  help="gcode file to print", default=False)
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="ReplicatorDual")
parser.add_option("-s", "--gcode_start_end_sequences", dest="start_end_sequences",
                  help="run gcode start and end proceeses", default=False)
(options, args) = parser.parse_args()


file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)
r = s3g.s3g()
r.writer = s3g.Writer.StreamWriter(file)

parser = s3g.Gcode.GcodeParser()
parser.state.values["build_name"] = 'test'
parser.state.profile = s3g.Profile(options.machine)
parser.s3g = r
profile = s3g.Profile("ReplicatorSingle")
parser.state.profile = profile

environment = {}

if options.start_end_sequences:
  for line in parser.state.profile.values['print_start_sequence']:
    parser.ExecuteLine(line, environment)
with open(options.filename) as f:
  for line in f:
    print line,
    parser.ExecuteLine(line, environment)
if options.start_end_sequences:
  for line in parser.state.profile.values['print_end_sequence']:
    parser.ExecuteLine(line, environment)
