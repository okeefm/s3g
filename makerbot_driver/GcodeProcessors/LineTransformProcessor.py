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

  def process_gcode(self, gcodes, callback=None):
    output = []
    count_total = len(gcodes)
    count_current = 0
    for code in gcodes:
      tcode = self._transform_code(code)
      count_total += len(tcode) #We can add codes, so we need to adjust for those
      pruned_tcode = self.prune_empty_strings(tcode)
      count_total -= len(pruned_tcode) #We can remove codes, so we need to adjust for those
      with self._condition:
        if self._external_stop:
          raise makerbot_driver.ExternalStopError
        output.extend(pruned_tcode)
      count_current += 1
      percent = self.get_percent(count_current, count_total)
      if callback is not None:
        callback(percent)
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
      match = re.match(key, code)
      if match is not None:
        tcode = self.code_map[key](code)
        break
    #Always use lists so we can extend
    if not isinstance(tcode, list):
      tcode = [tcode]
    return tcode
