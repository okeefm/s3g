"""
Decode an s3g file into commands and registers.
"""

import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import optparse

parser = optparse.OptionParser()
parser.add_option("-f", "--filename", dest="filename",
                  help="File name of the s3g file to parse")
(options, args) = parser.parse_args()

reader = makerbot_driver.FileReader.FileReader()
reader.file = open(options.filename)
payloads = reader.ReadFile()
for payload in payloads:
  print payload
