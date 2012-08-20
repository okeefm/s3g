import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import optparse
import tempfile

parser = optparse.OptionParser()
parser.add_option("-i", "--inputfile", dest="input_file",
                  help="gcode file to read in", default=False)
parser.add_option("-o", "--outputfile", dest="output_file",
                  help="s3g file to write out", default=False)
parser.add_option("-m", "--machine_type", dest="machine",
                  help="machine type", default="ReplicatorDual")
parser.add_option("-s", "--gcode_start_end_sequences", dest="start_end_sequences",
                  help="Disregard the start/end sequences in the stored inside the machine profile.", default=True, action="store_false")
(options, args) = parser.parse_args()


s = makerbot_driver.s3g()
s.writer = makerbot_driver.Writer.FileWriter(open(options.output_file, 'w'))

with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
  default_preprocess = f.name

with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
  preprocessor_output = f.name

with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
  remove_startendgcode = f.name

preprocessor = makerbot_driver.Preprocessors.RemoveStartEndGcode()
preprocessor.process_file(options.input_file, remove_startendgcode)

preprocessor = makerbot_driver.Preprocessors.DefaultPreprocessor()
preprocessor.process_file(remove_startendgcode, default_preprocess)

preprocessor = makerbot_driver.Preprocessors.Skeinforge50Preprocessor()
preprocessor.process_file(default_preprocess, preprocessor_output)

parser = makerbot_driver.Gcode.GcodeParser()
parser.state.values["build_name"] = 'test'
parser.state.profile = makerbot_driver.Profile(options.machine)
parser.s3g = s

if options.start_end_sequences:
  for line in parser.state.profile.values['print_start_sequence']:
    print line
    parser.execute_line(line)

with open(preprocessor_output) as f:
  for line in f:
    parser.execute_line(line)

if options.start_end_sequences:
  for line in parser.state.profile.values['print_end_sequence']:
    parser.execute_line(line)

s.writer.file.close()

finito = makerbot_driver.Gcode.FileComplete()
finito.finish(options.output_file)
