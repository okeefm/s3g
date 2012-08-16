from errors import *
from .. import Gcode

class ToolchangePreprocessor(object):

  def __init__(self):
    self.extruders = {
        'A' : 'M135 T0\n',
        'B' : 'M135 T1\n'
        }
    self.current_extruder = 'A'

  def process_file(self, input_path, output_path):
    output = open(output_path, 'w')
    with open(input_path) as f:
      for line in f:
        extruder = self.get_used_extruder(line)
        if extruder is not self.current_extruder and extruder is not None:
          addendum = self.extruders[extruder]
          output.write(addendum)
          self.current_extruder = extruder
        output.write(line)
    output.close()

  def get_used_extruder(self, input_line):
    (codes, flags, comments) = Gcode.parse_line(input_line)
    axis = None
    if codes['G'] is 1:
      extruders = set(self.extruders.keys())
      input_extruders = set(codes)
      used_extruder = extruders.intersection(input_extruders)
      if len(used_extruder) > 1:
        raise Gcode.ConflictingCodesError
      elif len(used_extruder) == 1:
        axis = list(used_extruder)[0]
    return axis
