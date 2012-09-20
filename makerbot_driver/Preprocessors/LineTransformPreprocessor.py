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

  def process_file(self, inlines):
    output = []
    for line in inlines:
      tline = self._transform_line(line)
      pruned_tline = self.prune_empty_strings(tline)
      output.extend(pruned_tline)
    return output

  def prune_empty_strings(self, inlines):
    outlines = []
    for line in inlines:
      if not line == "":
        outlines.append(line)
    return outlines

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
