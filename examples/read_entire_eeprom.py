import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import makerbot_driver

import serial
import serial.tools.list_ports
import optparse
parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="ReplicatorDual")
(options, args) = parser.parse_args()

g = makerbot_driver.s3g.from_filename(options.serialportname)
reader = makerbot_driver.EEPROM.eeprom_reader()
reader.s3g  = g
reader.read_entire_eeprom(print_map=True)
