"""
An abstract preprocessor that scans lines for
certain regexs and executes certain commands
on them.
"""
from __future__ import absolute_import
import re

import makerbot_driver
from . import Processor

class LineTransformProcessor(Processor):

  def __init__(self):
    super(LineTransformProcessor, self).__init__()
    self.code_map = {}

  def process_gcode(self, gcodes):
    output = []
    for code in gcodes:
      tcode = self._transform_code(code)
      pruned_tcode = self.prune_empty_strings(tcode)
      with self._condition:
        if self._external_stop:
          raise makerbot_driver.ExternalStopError
        output.extend(pruned_tcode)
    return output

  def prune_empty_strings(self, gcodes):
    outcodes = []
    for code in gcodes:
      if not code == "":
        outcodes.append(code)
    return outcodes 

  def _transform_code(self, code):
    tcode = code
    for key in self.code_map:
      match = re.search(key, code)
      if match is not None:
        tcode = self.code_map[key](code)
        break
    #Always use lists so we can extend
    if not isinstance(tcode, list):
      tcode = [tcode]
    return tcode
