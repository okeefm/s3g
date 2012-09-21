from __future__ import absolute_import

import makerbot_driver
from .LineTransformProcessor import LineTransformProcessor

class ToolchangeProcessor(LineTransformProcessor):

  def __init__(self):
    super(ToolchangeProcessor, self).__init__()
    self.extruders = {
        'A' : 'M135 T0\n',
        'B' : 'M135 T1\n'
        }
    self.code_map = {
        "[abAB]" : self.insert_tool_change,
        }
    self.current_extruder = 'A'

  def insert_tool_change(self, input_line):
    (codes, flags, comments) = makerbot_driver.Gcode.parse_line(input_line)
    return_lines = [input_line]
    if 'G' in codes:
      if codes['G'] is 1:
        axis = None
        extruders = set(self.extruders.keys())
        input_extruders = set(codes)
        used_extruder = extruders.intersection(input_extruders)
        #Always default to the A extruder if there are 2 extruders moving
        if len(used_extruder) > 1:
          axis = 'A'
        #Theres only one extruder, get that one
        elif len(used_extruder) == 1:
          axis = list(used_extruder)[0]
        if axis is not None:
          if not axis == self.current_extruder:
            return_lines.insert(0, self.extruders[axis])
            self.current_extruder = axis
    return return_lines
