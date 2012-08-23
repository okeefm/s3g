import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver
import optparse

parser = optparse.OptionParser()
parser.add_option('-i', '--input_file', dest='input_file',
                  help='the file you want to process')
parser.add_option('-o', '--output_file', dest='output_file',
                  help='name of the file after processing')
parser.add_option('-p', '--preprocessor', dest='preprocessor',
                  help='the name of the preprocessor')
parser.add_option('-l', '--list_preprocessors', dest='list',
                  help='If desired, lists preprocessors', 
                  default=False, action='store_true')
(options, args) = parser.parse_args()

prepro_fact = makerbot_driver.Preprocessors.PreprocessorFactory()
if options.list:
  print '-----Here are the preprocessors you can choose from-----' 
  prepros = prepro_fact.list_preprocessors()
  for p in prepros:
    print p
  sys.exit(0)
prepro = prepro_fact.create_preprocessor_from_name(options.preprocessor)

prepro.process_file(options.input_file, options.output_file)
