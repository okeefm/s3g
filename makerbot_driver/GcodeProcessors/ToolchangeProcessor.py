from __future__ import absolute_import

import re

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
      re.compile("[^;(]*?[gG]1.*?[aAbB]") : self._transform_into_toolchange,
      }
    self.current_extruder = 'A'

  def _transform_into_toolchange(self, input_line):
    return_lines = [input_line]
    #XOR of A in input_line and B in input_line
    if not ("A" in input_line == "B" in input_line):
      extruder_regex = "[aAbB]"
      extruder_match = re.search(extruder_regex, input_line)
      new_extruder = extruder_match.group().upper()
      if not new_extruder == self.current_extruder:
        self.current_extruder = new_extruder
        return_lines.insert(0, self.extruders[self.current_extruder])
    return return_lines
