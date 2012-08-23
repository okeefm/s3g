import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import makerbot_driver

import serial
import serial.tools.list_ports
import optparse

parser = optparse.OptionParser()
parser.add_option("-p", "--port", dest="port",
                  help="The port you want to connect to (OPTIONAL)", default=None)
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="The Replicator")
parser.add_option("-e", "--eeprom_entry", dest="eeprom_entry",
                  help="eeprom entry to write to")
parser.add_option("-c", "--context", dest="context",
                  help="context for the eeprom_entry, as comma separated values surrounded by quotations.", 
                  default="")
parser.add_option("-v", "--value", dest="value",
                  help="the value you want to write to on the eeprom")
(options, args) = parser.parse_args()

def process_comma_separated_values(string):
  string = string.replace(' ', '')
  string = string.split(',')
  for s in string:
    if s == '':
      string.remove(s)
  return string

context = process_comma_separated_values(options.context)

values = process_comma_separated_values(options.value)

#Try to convert ints to ints, since they are passed 
#in as strings
for i in range(len(values)):
  try:
    values[i] = int(values[i])
  except ValueError:
    pass

if options.port == None:
  md = makerbot_driver.MachineDetector()
  md.scan(options.machine)
  port = md.get_first_machine()
  if port is None:
    print "Cant Find %s" %(options.machine)
    sys.exit()
else:
  port = options.port
factory = makerbot_driver.BotFactory()
r, prof = factory.build_from_port(port)

writer = makerbot_driver.EEPROM.EepromWriter()
writer.s3g  = r

writer.write_data(options.eeprom_entry, values, context, flush=True)
