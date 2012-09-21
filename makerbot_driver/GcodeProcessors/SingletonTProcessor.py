from __future__ import absolute_import

import makerbot_driver
from .LineTransformProcessor import LineTransformProcessor 

class SingletonTProcessor(LineTransformProcessor):

  def __init__(self):
    super(SingletonTProcessor, self).__init__()
    self.code_map = { 
        "T[0-9]$" : self._transform_singleton
        }

  def _transform_singleton(self, input_line):
    (codes, flags, comments) = makerbot_driver.Gcode.parse_line(input_line)
    return_line = input_line
    if len(codes) == 1 and 'T' in codes:
      return_line = 'M135 T%i\n' %(codes['T'])
    return return_line
