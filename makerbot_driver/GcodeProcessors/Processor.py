"""
An interface that all future preprocessors should inherit from
"""
import os
import re

class Processor(object):
  def __init__(self):
    pass

  def process_gcode(self, gcodes):
    pass

  def _remove_variables(self, gcode):
    variable_regex = "#[^ ^\n^\r]*"
    m = re.search(variable_regex, gcode)
    while m is not None:
      gcode = gcode.replace(m.group(), '0')
      m = re.search(variable_regex, gcode)
    return gcode 
