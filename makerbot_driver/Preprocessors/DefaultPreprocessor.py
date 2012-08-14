"""
The Default Preprocessor is a preprocessor
that runs several sub-preprocessors to cover
common problems that most gcode files have.
"""

from toolchangeProcessor import *

class DefaultPreprocessor(object):

  def __init__(self):
    pass

  def process_file(self, input_path, output_path):
    toolPrepro = ToolchangePreprocessor()
    toolPrepro.process_file(input_path, output_path)
