from .. import Gcode
from Preprocessor import *

class SingletonTPreprocessor(Preprocessor):

  def __init__(self):
    pass

  def process_file(self, input_path, output_path):
    self.inputs_are_gcode(input_path, output_path)
    output = open(output_path, 'w')
    with open(input_path) as f:
      for line in f:
        if self.is_singleton_t(line):
          new_line = self.turn_into_toolchange(line)
          output.write(new_line)
        else:
          output.write(line)
    output.close()

  def is_singleton_t(self, input_line):
    (codes, flags, comments) = Gcode.parse_line(input_line)
    return len(flags) is 0 and len(codes) is 1 and 'T' in codes

  def turn_into_toolchange(self, input_line):
    (codes, flags, comments) = Gcode.parse_line(input_line)
    return 'M135 T%i\n' %(codes['T'])
    
