"""
The Default Preprocessor is a preprocessor
that runs several sub-preprocessors to cover
common problems that most gcode files have.
"""
from __future__ import absolute_import

import makerbot_driver
from .Preprocessor import Preprocessor
from .ToolchangePreprocessor import ToolchangePreprocessor
from .CoordinateRemovalPreprocessor import CoordinateRemovalPreprocessor

class DefaultPreprocessor(Preprocessor):

  def __init__(self):
    pass

  def process_file(self, inlines):
    preprocessors = [
        ToolchangePreprocessor(),
        CoordinateRemovalPreprocessor(),
        ]
    output = []
    for line in inlines:
      tline = [line]
      for prepro in preprocessors:
        tline = prepro.process_file(tline)
      output.extend(tline)
    return output
