import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g
import optparse

parser = optparse.OptionParser()
parser.add_option("-i", "--inputline", dest="input_line",
                  help="gcode line to read in", default=False)
parser.add_option("-o", "--outputfile", dest="output_file",
                  help="s3g file to write out", default=False)
parser.add_option("-m", "--machine", dest="machine",
                  help="the type of machine we print to", default="ReplicatorDual")
(options, args) = parser.parse_args()


s = s3g.s3g()
s.writer = s3g.Writer.FileWriter(open(options.output_file, 'w'))

parser = s3g.Gcode.GcodeParser()
parser.state.profile = s3g.Profile(options.machine)
parser.s3g = s

parser.ExecuteLine(options.input_line)
