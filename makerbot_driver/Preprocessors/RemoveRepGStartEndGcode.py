from __future__ import absolute_import

import makerbot_driver
from .Preprocessor import Preprocessor

class RemoveRepGStartEndGcode(Preprocessor):

  def __init__(self):
    pass

  def process_file(self, inlines):
    startgcode = False
    endgcode = False
    output = []

    for line in inlines:
      if startgcode:
        if(self.get_comment_match(line, 'end of start.gcode')):
          startgcode = False
      elif endgcode:
        if(self.get_comment_match(line, 'end End.gcode')):
          endgcode = False
      else:
        if (self.get_comment_match(line, '**** start.gcode')):
          startgcode = True
        elif (self.get_comment_match(line, '**** End.gcode')):
          endgcode = True
        else:
          output.append(line)
    return output

  def get_comment_match(self, input_line, match):
    (codes, flags, comments) = makerbot_driver.Gcode.parse_line(input_line)
    axis = None
    if comments.find(match) is -1:
      return False
    else:
      return True
