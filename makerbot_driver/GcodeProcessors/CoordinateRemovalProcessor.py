from __future__ import absolute_import

import makerbot_driver
from .LineTransformProcessor import LineTransformProcessor

class CoordinateRemovalProcessor(LineTransformProcessor):

  """
  Remove:
  G10
  G54
  G55
  G21
  G90
  """

  def __init__(self):
    self.code_map = {
        'G10' : self._transform_g10,
        'G54' : self._transform_g54,
        'G55' : self._transform_g55,
        'G21' : self._transform_g21,
        'G90' : self._transform_g90,
        }
    
  def _transform_g10(self, input_line):
    """
    Given a line that has an "G10" command, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = makerbot_driver.Gcode.parse_line(input_line)
    if 'G' in codes and codes['G'] == 10:
      return_line = ''
    else:
      return_line = input_line
    return return_line

  def _transform_g54(self, input_line):
    """
    Given a line that has an "G54" command, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = makerbot_driver.Gcode.parse_line(input_line)
    if 'G' in codes and codes['G'] == 54:
      return_line = ''
    else:
      return_line = input_line
    return return_line

  def _transform_g55(self, input_line):
    """
    Given a line that has an "G55" command, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = makerbot_driver.Gcode.parse_line(input_line)
    if 'G' in codes and codes['G'] == 55:
      return_line = ''
    else:
      return_line = input_line
    return return_line

  def _transform_g21(self, input_line):
    """
    given a line with a G21 command, transforms it into the 
    proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = makerbot_driver.Gcode.parse_line(input_line)
    return_line = input_line
    if codes.get('G', -1) == 21:
      return_line = ''
    return return_line

  def _transform_g90(self, input_line):
    """
    given a line with a G90 command, transforms it into the 
    proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = makerbot_driver.Gcode.parse_line(input_line)
    return_line = input_line
    if codes.get('G', -1) == 90:
      return_line = ''
    return return_line
