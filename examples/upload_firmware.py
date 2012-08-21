import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver

import optparse

parser = optparse.OptionParser()
parser.add_option("-m", "--machine", dest="machine",
                help="machine to upload to", default="TheReplicator")
parser.add_option("-v", "--version", dest="version", 
                help="version to upload", default="5.5")
parser.add_option("-p", "--port", dest="port",
                help="port machine is connected to", default="/dev/ttyACM0")
(options, args) = parser.parse_args()

u = makerbot_driver.Firmware.Uploader()
u.upload_firmware(options.port, options.machine, options.version)
