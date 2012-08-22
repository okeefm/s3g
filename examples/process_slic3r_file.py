import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import optparse


parser = optparse.OptionParser()
parser.add_option('-i', '--input_file', dest='input_file',
                  help="the file to process")
parser.add_option('-o', '--output_file', dest='output_file',
                  help="the file to output")
(options, args) = parser.parse_args()
p = makerbot_driver.Preprocessors.SlicerPreprocessor()
p.process_file(options.input_file, options.output_file)
