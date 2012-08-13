import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import makerbot_driver

import serial
import serial.tools.list_ports as lp
import optparse

parser = optparse.OptionParser()
parser.add_option("-f", "--filename", dest="filename",
                  help="gcode file to print", default=False)
parser.add_option("-s", "--gcode_start_end_sequences", dest="start_end_sequences",
                  help="run gcode start and end proceeses", default=True)
parser.add_option("-m", "--machine", dest="machine",
                  help="machine you want to connect to", default="The Replicator Dual")
(options, args) = parser.parse_args()

md = makerbot_driver.MachineDetector()
factory = makerbot_driver.BotFactory()

bot = md.get_first_bot_available(options.machine)
r, prof = factory.build_from_port(bot['port'])

parser = makerbot_driver.Gcode.GcodeParser()
parser.state.values["build_name"] = 'test'
parser.state.profile = prof
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
