import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import makerbot_driver

import serial.tools.list_ports
import optparse
import json

parser = optparse.OptionParser()
parser.add_option("-p", "--port", dest="port",
                  help="The port you want to connect to (OPTIONAL)", default=None)
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="The Replicator")
parser.add_option("-v", "--version", dest="version",
                  help="The version of eeprom you want to read",
                  default="5.6"
                  )
parser.add_option("-o", "--output_file", dest="output_file",
                  help="The file you want to write out to")
(options, args) = parser.parse_args()

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

reader = makerbot_driver.EEPROM.EepromReader()
reader.s3g  = r

with open(os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'makerbot_driver',
            'EEPROM',
            'eeprom_map_%s.json'%(options.version),
            )) as f:
  values = json.load(f)

eeprom_entries = values['eeprom_map']

def read_map(input_map, context=[]):
  for value in input_map:
    if 'sub_map' in input_map[value]:
       read_map(input_map[value]['sub_map'], context=context+[value])
    else:
      input_map[value]['value'] = reader.read_data(value, context)

read_map(eeprom_entries)

dump = json.dumps(eeprom_entries, sort_keys=True, indent=2)
with open(options.output_file, 'w') as f:
  f.write(dump)
