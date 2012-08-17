"""
The Default Preprocessor is a preprocessor
that runs several sub-preprocessors to cover
common problems that most gcode files have.
"""

import tempfile

import makerbot_driver

class DefaultPreprocessor(object):

  def __init__(self):
    pass

  def process_file(self, input_path, output_path):
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
      toolchange_path = f.name
    tool_prepro = makerbot_driver.Preprocessors.ToolchangePreprocessor()
    tool_prepro.process_file(input_path, toolchange_path)
    coordinate_prepro = makerbot_driver.Preprocessors.CoordinatePreprocessor()
    coordinate_prepro.process_file(toolchange_path, output_path_)
