from __future__ import absolute_import

import makerbot_driver
from .LineTransformProcessor import LineTransformProcessor

class TemperatureProcessor(LineTransformProcessor):

  def __init__(self):
    self.code_map = {
        "M104" : self._transform_m104,
        "M105" : self._transform_m105,
        }

  def _transform_m104(self, input_line):
    codes, flags, comments = makerbot_driver.Gcode.parse_line(input_line)
    return_line = input_line
    if codes.get('M', -1) == 104:
      return_line = ''
    return return_line

  def _transform_m105(self, input_line):
    codes, flags, comments = makerbot_driver.Gcode.parse_line(input_line)
    return_line = input_line
    if codes.get('M', -1) == 105:
      return_line = ''
    return return_line
