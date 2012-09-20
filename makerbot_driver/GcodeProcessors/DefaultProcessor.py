"""
The Default Preprocessor is a preprocessor
that runs several sub-preprocessors to cover
common problems that most gcode files have.
"""
from __future__ import absolute_import

import makerbot_driver
from .Processor import Processor
from .ToolchangeProcessor import ToolchangeProcessor
from .CoordinateRemovalProcessor import CoordinateRemovalProcessor

class DefaultProcessor(Processor):

  def __init__(self):
    pass

  def process_gcode(self, gcodes):
    processors = [
        ToolchangeProcessor(),
        CoordinateRemovalProcessor(),
        ]
    output = []
    for code in gcodes:
      tcode = [code]
      for pro in processors:
        tcode = pro.process_gcode(tcode)
      output.extend(tcode)
    return output
