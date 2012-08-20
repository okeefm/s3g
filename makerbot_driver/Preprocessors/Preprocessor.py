"""
An interface that all future preprocessors should inherit from
"""

import os

from errors import *

class Preprocessor(object):

  def __init__(self):
    pass

  def process_file(self, input_path, output_path):
    pass

  def inputs_are_gcode(self, input_path, output_path):
    for path in (input_path, output_path):
      name, ext = os.path.splitext(path)
      if ext != '.gcode':
        raise NotGCodeFileError
