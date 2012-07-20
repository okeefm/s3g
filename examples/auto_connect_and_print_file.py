import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import s3g
lib_path = os.path.abspath('../pyserial')

import serial
import serial.tools.list_ports
import optparse

parser = optparse.OptionParser()
parser.add_option("-f", "--filename", dest="filename",
                  help="gcode file to print", default=False)
parser.add_option("-s", "--gcode_start_end_sequences", dest="start_end_sequences",
                  help="run gcode start and end proceeses", default=True)
(options, args) = parser.parse_args()

vid = int('23c1', 16)
pid = int('d314', 16)

ports = serial.tools.list_ports.get_ports_by_vid_pid(vid, pid)

for port in ports:
  thePort = port['PORT']
  break

r = s3g.s3g.from_filename(thePort)

parser = s3g.Gcode.GcodeParser()
parser.state.values["build_name"] = 'test'
parser.state.profile = s3g.Profile('ReplicatorDual')
parser.s3g = r

if options.start_end_sequences:
  for line in parser.state.profile.values['print_start_sequence']:
    parser.execute_line(line)
with open(options.filename) as f:
  for line in f:
    print line,
    parser.execute_line(line)
if options.start_end_sequences:
  for line in parser.state.profile.values['print_end_sequence']:
    parser.execute_line(line)
