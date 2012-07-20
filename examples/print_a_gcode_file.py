"""
This example shows how we can start a print, and delay
until a Replicator is plugged in, then start the print
"""

import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import s3g

import serial
import serial.tools.list_ports
import optparse
import time

parser = optparse.OptionParser()
parser.add_option("-f", "--filename", dest="filename",
                  help="gcode file to print", default=False)
parser.add_option("-s", "--gcode_start_end_sequences", dest="start_end_sequences",
                  help="run gcode start and end proceeses", default=True)
(options, args) = parser.parse_args()

vid = int('23c1', 16)
pid = int('d314', 16)

ports = list(serial.tools.list_ports.get_ports_by_vid_pid(vid, pid))
while len(ports) == 0:
  time.sleep(3)
  ports = list(serial.tools.list_ports.get_ports_by_vid_pid(vid, pid))
  print "I Think you forgot to plug in your Replicator!  Please plug it in now."

print_delay = 15
print "Super, I've found a replicator!  Give me %i seconds to get everything ready." %(print_delay)
time.sleep(print_delay)

r = s3g.s3g.from_filename(ports[0]['PORT'])

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
