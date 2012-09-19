"""
An abstract preprocessor that scans lines for
certain regexs and executes certain commands
on them.
"""
from __future__ import absolute_import
import re

import makerbot_driver
from . import Preprocessor

class LineTransformPreprocessor(Preprocessor):

  def __init__(self):
    self.code_map = {}

  def process_file(self, input_file):
    output = []
    for line in input_file:
      tline = self._transform_line(line)
      output.extend(tline)
    return iter(output)

  def _transform_line(self, line):
    tline = line
    for key in self.code_map:
      match = re.search(key, line)
      if match is not None:
        tline = self.code_map[key](line)
        break
    #Always use lists so we can extend
    if not isinstance(tline, list):
      tline = [tline]
    return tline
