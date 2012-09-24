"""
The Default Preprocessor is a preprocessor
that runs several sub-preprocessors to cover
common problems that most gcode files have.
"""

import tempfile

from Preprocessor import *
from ToolchangePreprocessor import*
from CoordinateRemovalPreprocessor import *


class DefaultPreprocessor(Preprocessor):

    def __init__(self):
        pass

    def process_file(self, input_path, output_path):
        self.inputs_are_gcode(input_path, output_path)
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
            toolchange_path = f.name
        tool_prepro = ToolchangePreprocessor()
        tool_prepro.process_file(input_path, toolchange_path)
        coordinate_prepro = CoordinateRemovalPreprocessor()
        coordinate_prepro.process_file(toolchange_path, output_path)
