"""
An interface that all future preprocessors should inherit from
"""

import os
import re

from errors import *
from .. import Gcode

class Preprocessor(object):
  def __init__(self):
    pass

  def process_file(self, input_path, output_path):
    pass

  def inputs_are_gcode(self, input_path, output_path):
    pass

  def _remove_variables(self, input_line):
    variable_regex = "#[^ ^\n^\r]*"
    m = re.search(variable_regex, input_line)
    while m is not None:
      input_line = input_line.replace(m.group(), '0')
      m = re.search(variable_regex, input_line)
    return input_line
