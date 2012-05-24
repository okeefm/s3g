"""
Decode an s3g file into comamnds and registers.

"""

import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g
import optparse

parser = optparse.OptionParser()
parser.add_option("-f", "--filename", dest="filename",
                  help="File name of the s3g file to parse")
(options, args) = parser.parse_args()

reader = s3g.FileReader()
reader.file = open(options.filename)
payloads = reader.ReadFile()
for payload in payloads:
  print payload
