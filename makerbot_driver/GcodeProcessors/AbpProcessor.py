from __future__ import absolute_import

import makerbot_driver
from .LineTransformProcessor import LineTransformProcessor

class AbpProcessor(LineTransformProcessor):

  def __init__(self):
    super(AbpProcessor, self).__init__()
    self.code_map = {
        "M106" : self._transform_m106,
        "M107" : self._transform_m107,
        }

  def _transform_m107(self, input_line):
    codes, flags, comments = makerbot_driver.Gcode.parse_line(input_line)
    return_line = input_line
    if codes.get("M", -1) == 107:
      return_line = ""
    return return_line

  def _transform_m106(self, input_line):
    codes, flags, comments = makerbot_driver.Gcode.parse_line(input_line)
    return_line = input_line
    if codes.get("M", -1) == 106:
      return_line = ""
    return return_line
