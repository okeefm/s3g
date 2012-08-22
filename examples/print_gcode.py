import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
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
                  help="run gcode start and end proceeses", default=True)
parser.add_option("-a", "--material", dest="material",
                  help="material to print in", default="ABS")
parser.add_option("-r", "--right", dest="right",
                  help="print with right extruder", action="store_true", default=False)
parser.add_option("-l", "--left", dest="left",
                  help="print with left extruder", action="store_true", default=False)
(options, args) = parser.parse_args()


r = makerbot_driver.s3g.from_filename(options.serialportname)

profile = makerbot_driver.Profile(options.machine)

parser = makerbot_driver.Gcode.GcodeParser()
parser.state.values["build_name"] = 'test'
parser.state.profile = profile
parser.s3g = r

assembler = makerbot_driver.GcodeAssembler(profile)
start_recipe, end_recipe, variables = assembler.assemble_recipe(material=options.material, tool_0=options.right, tool_1=options.left)

parser.environment.update(variables)

if options.start_end_sequences:
  for line in assembler.assemble_start_sequence(start_recipe):
    parser.execute_line(line)
with open(options.filename) as f:
  for line in f:
    print line,
    parser.execute_line(line)
if options.start_end_sequences:
  for line in assembler.assemble_end_sequence(end_recipe):
    parser.execute_line(line)
