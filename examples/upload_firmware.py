import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver

import optparse
import time

parser = optparse.OptionParser()
parser.add_option("-m", "--machine", dest="machine",
                help="machine to upload to", default="The Replicator")
parser.add_option("-v", "--version", dest="version", 
                help="version to upload", default="5.5")
parser.add_option("-p", "--port", dest="port",
                help="port machine is connected to (OPTIONAL)", default=None)
(options, args) = parser.parse_args()

s = 10

print 'Press the reset button on your machine in %s seconds, if needed' %(s)

if options.port == None:
  md = makerbot_driver.MachineDetector()
  md.scan(options.machine)
  port = md.get_first_machine()
  if port is None:
    print "Cant Find %s" %(options.machine)
    sys.exit()
else:
  port = options.port

machine_name = options.machine.replace(' ', '')

time.sleep(s)

u = makerbot_driver.Firmware.Uploader()
u.upload_firmware(port, machine_name, options.version)
