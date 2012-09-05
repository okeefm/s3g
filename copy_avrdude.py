import platform
import os
import shutil
import optparse
import sys

parser = optparse.OptionParser()
parser.add_option('-p', '--platform', dest='platform',
                  help='The platform you are you', default=None)
(options, args) = parser.parse_args()


tool_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'submodule',
    'conveyor_bins'
    )
path_to_firmware = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'makerbot_driver',
    'Firmware'
    )

#Lets do some os detection!
if not options.platform:
  if platform.system() == "Windows": 
    platform_folder = 'windows'
  elif platform.system() == "Darwin":
    platform_folder = 'mac'
  elif platform.system() == 'Linux':
    print "Nothing to copy; use distribution utility to obtain AVRDude."
    sys.exit(0)
else:
  #Lets use the user specified args!
  acceptable_platforms = ['windows', 'mac']
  if options.platform not in acceptable_platforms:
    print "Please enter a platform as: %s" %(str(acceptable_platforms))
    sys.exit(1)
  platform_folder = options.platform

path_to_avr = os.path.join(
    tool_path,
    platform_folder,
    'avrdude'
    )

if not os.path.isfile(os.path.join(path_to_firmware, 'avrdude')):
  print 'Copying avrdude into %s' %(path_to_firmware)
  shutil.copy(path_to_avr, path_to_firmware)
  sys.exit(0)
else:
  print 'AVRDude detected in %s, exiting' %(path_to_firmware)
  sys.exit(0)
